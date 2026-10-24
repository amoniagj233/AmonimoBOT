import json
import shlex
import shutil
import subprocess
from datetime import date

import pytest
import yaml

from scripts import check_coverage_waiver_expiry as monitor


def write_policy(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    policy = {
        "schema_version": 1,
        "aggregate_coverage": {"target": 75, "waiver": None},
        "coverage": {
            "default_target": 70,
            "tiers": {},
            "waivers": {
                "sample": {
                    "floor": 40,
                    "target": 70,
                    "expires_on": "2027-01-31",
                    "issue": 293,
                    "reason": "Coverage backlog",
                }
            },
        },
        "allowed_failures": {},
        "matrix": {},
    }
    path = config / "ci-test-policy.yaml"
    path.write_text(yaml.safe_dump(policy))
    return path, policy


@pytest.mark.parametrize(
    "day,status", [(16, "active"), (17, "warning"), (24, "urgent"), (31, "urgent")]
)
def test_warning_boundaries(tmp_path, day, status):
    write_policy(tmp_path)
    row = monitor.build_report(tmp_path, date(2027, 1, day))["exceptions"][0]
    assert row["status"] == status
    assert row["days_remaining"] == 31 - day


def test_expired_is_reported_not_rejected(tmp_path):
    path, policy = write_policy(tmp_path)
    exception = {"expires_on": "2027-01-31", "issue": 293, "reason": "Backlog"}
    policy["allowed_failures"] = {"sample": exception}
    policy["aggregate_coverage"]["waiver"] = {**exception, "floor": 50, "target": 75}
    path.write_text(yaml.safe_dump(policy))
    rows = monitor.build_report(tmp_path, date(2027, 2, 1))["exceptions"]
    assert len(rows) == 3
    assert all(row["status"] == "expired" and row["days_remaining"] == -1 for row in rows)


@pytest.mark.parametrize("mutation", ["missing", "target", "bool", "date", "duplicate"])
def test_malformed_policy_fails(tmp_path, mutation):
    path, policy = write_policy(tmp_path)
    if mutation == "missing":
        del policy["coverage"]
    elif mutation == "target":
        policy["coverage"]["waivers"]["sample"]["target"] = 71
    elif mutation == "bool":
        policy["coverage"]["waivers"]["sample"]["issue"] = True
    elif mutation == "date":
        policy["coverage"]["waivers"]["sample"]["expires_on"] = "invalid"
    path.write_text(yaml.safe_dump(policy))
    if mutation == "duplicate":
        path.write_text(path.read_text() + "schema_version: 1\n")
    with pytest.raises(monitor.MatrixError):
        monitor.build_report(tmp_path, date(2027, 1, 1))


def report(status="warning", days=14):
    return {
        "exceptions": [
            {
                "kind": "coverage_waiver",
                "id": "sample",
                "expires_on": "2027-01-31",
                "issue": 293,
                "status": status,
                "days_remaining": days,
            }
        ]
    }


def fake_api(monkeypatch, pages):
    calls = []

    def api(endpoint, **kwargs):
        calls.append((endpoint, kwargs))
        return pages if kwargs.get("paginate") else {}

    monkeypatch.setattr(monitor, "gh_api", api)
    return calls


def test_create_ignores_human_marker_and_paginates(monkeypatch):
    calls = fake_api(monkeypatch, [[{"user": {"login": "human"}, "body": monitor.MARKER}], []])
    assert monitor.notify(report(), "owner/repo") == "created"
    assert calls[0][1] == {"paginate": True}
    assert calls[1][1]["method"] == "POST"
    assert "@owner" in calls[1][1]["body"]


def test_unchanged_countdown_suppressed(monkeypatch):
    body = monitor.alert_body(report(), "owner")
    calls = fake_api(monkeypatch, [[], [{"id": 42, "user": {"login": monitor.BOT}, "body": body}]])
    assert monitor.notify(report("urgent", 0), "owner/repo") == "unchanged"
    assert len(calls) == 1


def test_recovery_update(monkeypatch):
    status = "active"
    body = monitor.alert_body(report(), "owner")
    calls = fake_api(monkeypatch, [[{"id": 42, "user": {"login": monitor.BOT}, "body": body}]])
    assert monitor.notify(report(status), "owner/repo") == "updated"
    assert calls[1][0].endswith("/issues/comments/42")
    assert calls[1][1]["method"] == "PATCH"
    assert ("EXPIRED" if status == "expired" else "No exceptions") in calls[1][1]["body"]


def test_no_alert_no_comment(monkeypatch):
    calls = fake_api(monkeypatch, [[]])
    assert monitor.notify(report("active"), "owner/repo") == "no-alert"
    assert len(calls) == 1


def test_duplicate_managed_comments_fail(monkeypatch):
    comment = {"id": 42, "user": {"login": monitor.BOT}, "body": monitor.MARKER}
    calls = fake_api(monkeypatch, [[comment, comment]])
    with pytest.raises(ValueError, match="multiple managed"):
        monitor.notify(report(), "owner/repo")
    assert len(calls) == 1


def test_api_failure_cli_fails_and_keeps_report(tmp_path, monkeypatch, capsys):
    write_policy(tmp_path)

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["gh"])

    monkeypatch.setattr(monitor, "gh_api", fail)
    output = tmp_path / "report.json"
    assert (
        monitor.main(["--root", str(tmp_path), "--output", str(output), "--notify", "owner/repo"])
        == 2
    )
    assert json.loads(output.read_text())["exceptions"]
    assert "ERROR" in capsys.readouterr().err


def test_offline_cli_never_calls_github(tmp_path, monkeypatch):
    write_policy(tmp_path)
    monkeypatch.setattr(monitor, "gh_api", lambda *a, **kw: pytest.fail("offline GitHub call"))
    assert monitor.main(["--root", str(tmp_path), "--output", str(tmp_path / "report.json")]) == 0


def test_workflow_scope_and_permissions():
    workflow = yaml.safe_load(
        (monitor.ROOT / ".github/workflows/coverage-waiver-expiry.yml").read_text()
    )
    # PyYAML's YAML 1.1 resolver interprets the key 'on' as True.
    triggers = workflow[True]
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    job = workflow["jobs"]["notify"]
    assert job["permissions"] == {"contents": "read", "issues": "write"}
    assert "refs/heads/main" in job["if"]
    assert "tradermonty/claude-trading-skills" in job["if"]
    assert workflow["concurrency"]["cancel-in-progress"] is False
    assert any("--notify" in step.get("run", "") for step in job["steps"])


def _workflow_uv_commands():
    workflow = yaml.safe_load(
        (monitor.ROOT / ".github/workflows/coverage-waiver-expiry.yml").read_text()
    )
    runs = [step["run"] for step in workflow["jobs"]["notify"]["steps"] if "run" in step]
    return [shlex.split(run) for run in runs if run.lstrip().startswith("uv ")]


def test_workflow_syncs_then_runs_without_resync():
    commands = _workflow_uv_commands()
    assert [argv[1] for argv in commands] == ["sync", "run"]
    sync, run = commands
    assert {"--locked", "--no-install-project", "--extra", "dev"} <= set(sync)
    assert {"--locked", "--no-sync"} <= set(run)
    assert "--no-install-project" not in run
    script = run[run.index("python") : run.index("python") + 2]
    assert script == ["python", "scripts/check_coverage_waiver_expiry.py"]


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv CLI not installed")
def test_workflow_uv_options_are_accepted_by_uv():
    # uv validates every option before handling --help, so an option that belongs to
    # another subcommand (e.g. `uv run --no-install-project`) fails here, offline.
    for argv in _workflow_uv_commands():
        options = argv[: argv.index("python")] if "python" in argv else argv
        result = subprocess.run([*options, "--help"], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("change", ["expired", "new", "renewed"])
def test_escalation_creates_fresh_mention(monkeypatch, change):
    old = monitor.alert_body(report(), "owner")
    current = report("expired") if change == "expired" else report()
    if change == "new":
        current["exceptions"].append({**current["exceptions"][0], "id": "other"})
    elif change == "renewed":
        current["exceptions"][0]["expires_on"] = "2027-02-01"
    calls = fake_api(monkeypatch, [[{"id": 42, "user": {"login": monitor.BOT}, "body": old}]])
    assert monitor.notify(current, "owner/repo") == "created"
    assert [call[1].get("method") for call in calls] == [None, "PATCH", "POST"]
    assert calls[1][1]["body"].startswith(monitor.SUPERSEDED_MARKER)
    assert not calls[1][1]["body"].startswith(monitor.MARKER)
    assert "@owner" not in calls[1][1]["body"]
    assert "@owner" in calls[2][1]["body"]


def test_prose_and_row_order_do_not_realert(monkeypatch):
    current = report()
    current["exceptions"].append({**current["exceptions"][0], "id": "other"})
    old = monitor.alert_body(current, "owner").replace("require action", "need attention")
    current["exceptions"].reverse()
    calls = fake_api(monkeypatch, [[{"id": 42, "user": {"login": monitor.BOT}, "body": old}]])
    assert monitor.notify(current, "owner/repo") == "updated"
    assert calls[1][1]["method"] == "PATCH"


@pytest.mark.parametrize("failed_method", ["PATCH", "POST"])
def test_escalation_failure_retries_without_duplicate(monkeypatch, failed_method):
    comments = [
        {"id": 42, "user": {"login": monitor.BOT}, "body": monitor.alert_body(report(), "owner")}
    ]
    methods = []
    fail_once = True

    def api(endpoint, **kwargs):
        nonlocal fail_once
        if kwargs.get("paginate"):
            return [[dict(comment) for comment in comments]]
        method = kwargs["method"]
        methods.append(method)
        if method == failed_method and fail_once:
            fail_once = False
            raise subprocess.CalledProcessError(1, ["gh"])
        if method == "PATCH":
            comments[0]["body"] = kwargs["body"]
        else:
            comments.append({"id": 43, "user": {"login": monitor.BOT}, "body": kwargs["body"]})
        return {}

    monkeypatch.setattr(monitor, "gh_api", api)
    with pytest.raises(subprocess.CalledProcessError):
        monitor.notify(report("expired"), "owner/repo")
    if failed_method == "PATCH":
        assert methods == ["PATCH"]
        assert comments[0]["body"].startswith(monitor.MARKER)
    else:
        assert comments[0]["body"].startswith(monitor.SUPERSEDED_MARKER)
    assert monitor.notify(report("expired"), "owner/repo") == "created"
    assert sum(c["body"].startswith(monitor.MARKER) for c in comments) == 1
    assert monitor.notify(report("expired"), "owner/repo") == "unchanged"
