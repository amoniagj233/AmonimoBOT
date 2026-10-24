"""Executable replay coverage for stockbee-20pct-study-daily (Issue #294)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import workflow_replay as replay_module  # noqa: E402
from workflow_replay import (  # noqa: E402
    EXECUTORS,
    ReplayError,
    compare_trees,
    execute_replay,
    generate_goldens,
    load_yaml,
)

SPEC = ROOT / "examples" / "workflows" / "stockbee-20pct-study-daily" / "replay.yaml"
COVERAGE = ROOT / "examples" / "workflows" / "replay-coverage.yaml"


def test_twenty_pct_spec_runs_four_native_steps_and_one_manual_contract() -> None:
    summary = replay_module.validate_spec(ROOT, SPEC)

    assert summary["workflow_id"] == "stockbee-20pct-study-daily"
    assert summary["native_steps"] == [1, 2, 3, 4]
    assert summary["manual_contract_steps"] == [5]


def test_required_only_replays_non_empty_matured_cohort(tmp_path: Path) -> None:
    output = tmp_path / "required"
    report = execute_replay(ROOT, SPEC, "required-only", output)

    assert report["status"] == "completed"
    assert report["network_policy"] == "offline-input-required"
    assert [step["executor_mode"] for step in report["steps"]] == ["native_cli"] * 4
    assert [step["gate_policy"] for step in report["steps"]] == [
        "continue",
        "continue",
        "continue",
        "record_only",
    ]

    scanned = json.loads((output / "01_twenty_pct_mover_events.json").read_text())
    enriched = json.loads((output / "02_classified_event_study.json").read_text())
    matured = json.loads((output / "03_matured_event_outcomes.json").read_text())
    summary = json.loads((output / "04_twenty_pct_cohort_summary.json").read_text())
    hints = json.loads((output / "04_edge_hints.yaml").read_text())

    assert [event["symbol"] for event in scanned["events"]] == ["FICT20"]
    assert enriched["events"][0]["catalyst"]["label"] == "EARNINGS_REVALUATION"
    assert matured["metadata"]["counts"]["matured"] == 1
    assert matured["records"][0]["outcomes"]["5d"]["status"] == "MATURED"
    assert summary["records_matured"] == 1
    assert len(summary["cohorts"]) == 1
    assert len(summary["rule_candidates"]) == 1
    assert hints["edge_hints"] == summary["rule_candidates"]

    manifest = load_yaml(output / "manifest.yaml")
    assert manifest["completed_steps"] == [1, 2, 3, 4]
    assert manifest["optional_steps_skipped"] == [
        {
            "step": 5,
            "skill": "trader-memory-core",
            "reason": "required-only executable replay",
        }
    ]
    assert not (output / "05_accepted_lessons_log.yaml").exists()


def test_full_path_binds_manual_lessons_to_step_four_evidence(tmp_path: Path) -> None:
    output = tmp_path / "full"
    report = execute_replay(ROOT, SPEC, "full-path", output)

    assert [step["executor_mode"] for step in report["steps"]] == [
        "native_cli",
        "native_cli",
        "native_cli",
        "native_cli",
        "manual_contract",
    ]
    assert [step["gate_policy"] for step in report["steps"][-2:]] == [
        "record_only",
        "record_only",
    ]
    lessons = load_yaml(output / "05_accepted_lessons_log.yaml")
    assert lessons["source_artifacts"] == ["twenty_pct_cohort_summary", "edge_hints_yaml"]
    assert lessons["lessons"][0]["decision"] == "journal_only"
    assert lessons["lessons"][0]["changes_trading_rules"] is False
    assert lessons["provenance"]["execution_mode"] == "manual_contract"
    assert lessons["provenance"]["native_trader_memory_validated"] is False
    assert set(lessons["provenance"]["source_sha256"]) == {
        "twenty_pct_cohort_summary",
        "edge_hints_yaml",
    }


@pytest.mark.parametrize(
    ("input_name", "payload", "completed_steps"),
    [
        ("prices", "{not json\n", []),
        ("news", "{not json\n", [1]),
    ],
)
def test_invalid_offline_input_fails_without_partial_publication(
    input_name: str,
    payload: str,
    completed_steps: list[int],
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    invalid = input_dir / f"invalid-{input_name}.json"
    invalid.write_text(payload, encoding="utf-8")
    output = tmp_path / "published"
    output.mkdir()
    sentinel = output / "existing.txt"
    sentinel.write_bytes(b"unchanged\n")

    with pytest.raises(ReplayError) as exc_info:
        execute_replay(
            ROOT,
            SPEC,
            "required-only",
            output,
            input_overrides={input_name: invalid},
        )

    assert exc_info.value.completed_steps == completed_steps
    assert sentinel.read_bytes() == b"unchanged\n"
    assert {path.name for path in output.iterdir()} == {"existing.txt"}


def test_corrupt_state_handoff_stops_before_downstream_and_preserves_output(
    tmp_path: Path,
) -> None:
    output = tmp_path / "published"
    output.mkdir()
    sentinel = output / "existing.txt"
    sentinel.write_bytes(b"unchanged\n")

    def corrupt_after_scan(step: int, artifacts: dict[str, dict]) -> None:
        if step == 1:
            state = Path(artifacts["twenty_pct_mover_events"]["files"]["state"])
            state.write_text("not-jsonl\n", encoding="utf-8")

    with pytest.raises(ReplayError) as exc_info:
        execute_replay(
            ROOT,
            SPEC,
            "required-only",
            output,
            after_step=corrupt_after_scan,
        )

    assert exc_info.value.completed_steps == [1]
    assert sentinel.read_bytes() == b"unchanged\n"
    assert {path.name for path in output.iterdir()} == {"existing.txt"}


def test_stale_manual_approval_digest_is_rejected(tmp_path: Path) -> None:
    approval = load_yaml(SPEC.parent / "replay-inputs" / "accepted_lessons.yaml")
    approval["source_sha256"]["edge_hints_yaml"] = "0" * 64
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    approval_path = input_dir / "stale-approval.yaml"
    approval_path.write_text(yaml.safe_dump(approval, sort_keys=False), encoding="utf-8")

    with pytest.raises(ReplayError, match="source_sha256") as exc_info:
        execute_replay(
            ROOT,
            SPEC,
            "full-path",
            tmp_path / "published",
            input_overrides={"accepted_lessons": approval_path},
        )

    assert exc_info.value.completed_steps == [1, 2, 3, 4]
    assert not (tmp_path / "published").exists()


def test_non_operating_lesson_cannot_claim_rule_changes_on_input(tmp_path: Path) -> None:
    approval = load_yaml(SPEC.parent / "replay-inputs" / "accepted_lessons.yaml")
    approval["lessons"][0]["changes_trading_rules"] = True
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    approval_path = input_dir / "contradictory-approval.yaml"
    approval_path.write_text(yaml.safe_dump(approval, sort_keys=False), encoding="utf-8")

    with pytest.raises(ReplayError, match="twenty-percent lessons input schema") as exc_info:
        execute_replay(
            ROOT,
            SPEC,
            "full-path",
            tmp_path / "published",
            input_overrides={"accepted_lessons": approval_path},
        )

    assert exc_info.value.completed_steps == [1, 2, 3, 4]
    assert not (tmp_path / "published").exists()


def test_non_operating_lesson_cannot_claim_rule_changes_on_output() -> None:
    payload = load_yaml(SPEC.parent / "sample-run-full-path/05_accepted_lessons_log.yaml")
    payload["lessons"][0]["decision"] = "rejected"
    payload["lessons"][0]["changes_trading_rules"] = True

    with pytest.raises(ReplayError, match="twenty-percent lessons output schema"):
        replay_module._validate_twenty_pct_manual_contract(payload, "output")


def test_manual_contract_write_failure_rolls_back_candidate_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "published"
    output.mkdir()
    sentinel = output / "existing-lessons.yaml"
    sentinel.write_bytes(b"lessons: []\n")
    registration = EXECUTORS["manual_twenty_pct_lessons"]

    def fail_after_write(*args, **kwargs):
        registration.run(*args, **kwargs)
        raise OSError("injected manual contract write failure")

    monkeypatch.setitem(
        EXECUTORS,
        "manual_twenty_pct_lessons",
        replay_module.ExecutorRegistration(mode="manual_contract", run=fail_after_write),
    )

    with pytest.raises(ReplayError, match="manual contract write failure") as exc_info:
        execute_replay(ROOT, SPEC, "full-path", output)

    assert exc_info.value.completed_steps == [1, 2, 3, 4]
    assert sentinel.read_bytes() == b"lessons: []\n"
    assert {path.name for path in output.iterdir()} == {"existing-lessons.yaml"}


def test_native_commands_use_only_offline_inputs_and_scrub_sensitive_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[list[str], dict[str, str]]] = []
    real_run = replay_module.subprocess.run
    monkeypatch.setenv("REPLAY_API_KEY", "secret-value")
    monkeypatch.setenv("REPLAY_PROXY", "http://proxy.invalid")

    def capture_run(command, *args, **kwargs):
        captured.append((list(command), dict(kwargs["env"])))
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(replay_module.subprocess, "run", capture_run)
    execute_replay(ROOT, SPEC, "required-only", tmp_path / "published")

    assert [command[2] for command, _env in captured] == [
        "scan",
        "enrich",
        "update-outcomes",
        "summarize",
    ]
    assert "--prices-json" in captured[0][0]
    assert "--news-json" in captured[1][0]
    assert "--prices-json" in captured[2][0]
    for command, env in captured:
        assert not {"--symbols", "--fmp-universe", "--api-key"} & set(command)
        assert "REPLAY_API_KEY" not in env
        assert "REPLAY_PROXY" not in env


@pytest.mark.parametrize(
    "output_dir",
    [
        ROOT,
        SPEC,
        SPEC.parent,
        SPEC.parent / "replay-inputs",
        SPEC.parent / "sample-run",
        SPEC.parent / "sample-run-full-path",
    ],
)
def test_runtime_output_cannot_overlap_repo_sources_or_goldens(output_dir: Path) -> None:
    protected_files = [
        SPEC,
        SPEC.parent / "replay-inputs/prices.json",
        SPEC.parent / "sample-run/manifest.yaml",
        SPEC.parent / "sample-run-full-path/manifest.yaml",
    ]
    before = {path: path.read_bytes() for path in protected_files}

    with pytest.raises(ReplayError, match="output_dir (?:overlaps protected|must be a directory)"):
        execute_replay(ROOT, SPEC, "required-only", output_dir)

    assert {path: path.read_bytes() for path in protected_files} == before


def test_runtime_output_protects_override_input_parent(tmp_path: Path) -> None:
    override_dir = tmp_path / "override-input"
    override_dir.mkdir()
    prices = override_dir / "prices.json"
    prices.write_bytes((SPEC.parent / "replay-inputs/prices.json").read_bytes())

    with pytest.raises(ReplayError, match="inputs.prices parent"):
        execute_replay(
            ROOT,
            SPEC,
            "required-only",
            override_dir,
            input_overrides={"prices": prices},
        )

    assert prices.exists()


def test_runtime_output_rejects_existing_file_without_replacing_it(tmp_path: Path) -> None:
    output = tmp_path / "existing-output.txt"
    output.write_bytes(b"keep this file\n")

    with pytest.raises(ReplayError, match="output_dir must be a directory"):
        execute_replay(ROOT, SPEC, "required-only", output)

    assert output.is_file()
    assert output.read_bytes() == b"keep this file\n"


def test_generate_stages_every_variant_before_publishing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    golden_dirs = [
        ROOT / "examples/workflows/stockbee-20pct-study-daily/sample-run",
        ROOT / "examples/workflows/stockbee-20pct-study-daily/sample-run-full-path",
        ROOT / "examples/workflows/stockbee-fluency-loop/sample-run",
        ROOT / "examples/workflows/stockbee-fluency-loop/sample-run-full-path",
    ]
    before = {
        path.relative_to(ROOT): path.read_bytes()
        for directory in golden_dirs
        for path in directory.rglob("*")
        if path.is_file()
    }
    real_execute = replay_module.execute_replay
    calls = 0

    def fail_last_variant(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 4:
            raise ReplayError("injected late replay failure", [1, 2, 3])
        return real_execute(*args, **kwargs)

    monkeypatch.setattr(replay_module, "execute_replay", fail_last_variant)

    with pytest.raises(ReplayError, match="late replay failure"):
        generate_goldens(ROOT, COVERAGE)

    after = {
        path.relative_to(ROOT): path.read_bytes()
        for directory in golden_dirs
        for path in directory.rglob("*")
        if path.is_file()
    }
    assert calls == 4
    assert after == before


def test_multi_tree_publication_rolls_back_an_earlier_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stage_one = tmp_path / "stage-one"
    stage_two = tmp_path / "stage-two"
    destination_one = tmp_path / "destination-one"
    destination_two = tmp_path / "destination-two"
    for path, content in (
        (stage_one, b"new-one\n"),
        (stage_two, b"new-two\n"),
        (destination_one, b"old-one\n"),
        (destination_two, b"old-two\n"),
    ):
        path.mkdir()
        (path / "value.txt").write_bytes(content)
    real_replace = replay_module.os.replace

    def fail_second_candidate(source, target):
        source_path = Path(source)
        target_path = Path(target)
        if ".destination-two.candidate-" in source_path.name and target_path == destination_two:
            raise OSError("injected second commit failure")
        return real_replace(source, target)

    monkeypatch.setattr(replay_module.os, "replace", fail_second_candidate)

    with pytest.raises(OSError, match="second commit failure"):
        replay_module._publish_trees_transactionally(
            [(stage_one, destination_one), (stage_two, destination_two)]
        )

    assert (destination_one / "value.txt").read_bytes() == b"old-one\n"
    assert (destination_two / "value.txt").read_bytes() == b"old-two\n"


def test_digest_allowlist_is_explicit_and_golden_outputs_are_marked() -> None:
    digest = "a" * 64
    rendered = replay_module._dump_yaml_with_digest_allowlist(
        {
            "source_sha256": {
                **{key: digest for key in replay_module.DIGEST_ALLOWLIST_KEYS},
                "unrelated_digest": digest,
            }
        }
    )

    for key in replay_module.DIGEST_ALLOWLIST_KEYS:
        assert f"{key}: {digest}  # pragma: allowlist secret" in rendered
    assert f"unrelated_digest: {digest}\n" in rendered
    assert f"unrelated_digest: {digest}  # pragma: allowlist secret" not in rendered

    existing = (
        ROOT
        / "examples/workflows/stockbee-fluency-loop/sample-run-full-path/04_accepted_lessons_log.yaml"
    ).read_text(encoding="utf-8")
    new = (SPEC.parent / "sample-run-full-path/05_accepted_lessons_log.yaml").read_text(
        encoding="utf-8"
    )
    approval = (SPEC.parent / "replay-inputs/accepted_lessons.yaml").read_text(encoding="utf-8")
    assert existing.count("# pragma: allowlist secret") == 2
    assert new.count("# pragma: allowlist secret") == 2
    assert approval.count("# pragma: allowlist secret") == 2


@pytest.mark.parametrize(
    ("variant", "golden_dir"),
    (("required-only", "sample-run"), ("full-path", "sample-run-full-path")),
)
def test_twenty_pct_goldens_are_byte_reproducible(
    variant: str,
    golden_dir: str,
    tmp_path: Path,
) -> None:
    generated = tmp_path / "generated"
    execute_replay(ROOT, SPEC, variant, generated)
    assert compare_trees(generated, SPEC.parent / golden_dir) == []

    altered = tmp_path / "altered"
    shutil.copytree(SPEC.parent / golden_dir, altered)
    candidate = next(altered.glob("0*_*.json"))
    candidate.write_text("{}\n", encoding="utf-8")
    assert compare_trees(generated, altered)
