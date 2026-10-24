"""Strict canonical handoffs use real consumer policy and preserve publications."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import workflow_replay as replay

SPEC = ROOT / "examples/workflows/market-regime-daily/replay.yaml"
CLI = ROOT / "skills/exposure-coach/scripts/calculate_exposure.py"


def _block():
    return {
        "schema_version": "1.0",
        "provider": "fictional-fixture",
        "endpoint": "test",
        "retrieved_at": "2026-01-15T12:00:00Z",
        "as_of": "2026-01-14",
        "timezone": "America/New_York",
        "run_id": "same-run",
        "adjusted": False,
        "point_in_time": False,
        "survivorship_free": False,
        "corporate_actions_handled": False,
    }


@pytest.mark.parametrize("failure", ["missing", "run", "stale", "future", "timezone", "schema"])
def test_strict_cli_preserves_output_on_rejected_input(tmp_path, failure):
    block = _block()
    if failure == "run":
        block["run_id"] = "other-run"
    elif failure == "stale":
        block["as_of"] = "2025-12-01"
    elif failure == "future":
        block["retrieved_at"] = "2026-01-16T12:00:00Z"
    elif failure == "timezone":
        block["timezone"] = "not-a-zone"
    elif failure == "schema":
        block["schema_version"] = "future"
    payload = {"breadth_score": 80, "uptrend_score": 80, "data_provenance": block}
    if failure == "missing":
        del payload["data_provenance"]
    source = tmp_path / "source.json"
    source.write_text(json.dumps(payload))
    output = tmp_path / "published"
    output.mkdir()
    marker = output / "old.json"
    marker.write_text("old")
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--breadth",
            str(source),
            "--uptrend",
            str(source),
            "--require-provenance",
            "--run-id",
            "same-run",
            "--as-of",
            "2026-01-15T13:00:00Z",
            "--output-dir",
            str(output),
            "--json-only",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "error:" in result.stderr
    assert list(output.iterdir()) == [marker]
    assert marker.read_text() == "old"


def test_strict_cli_success_and_legacy_schema(tmp_path):
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps({"breadth_score": 80, "uptrend_score": 70, "data_provenance": _block()})
    )
    base = [
        sys.executable,
        str(CLI),
        "--breadth",
        str(source),
        "--uptrend",
        str(source),
        "--json-only",
    ]
    decisions = []
    for strict in [False, True]:
        output = tmp_path / str(strict)
        command = base + ["--output-dir", str(output)]
        if strict:
            command += [
                "--require-provenance",
                "--run-id",
                "same-run",
                "--as-of",
                "2026-01-15T13:00:00Z",
            ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        decision = json.loads(next(output.glob("*.json")).read_text())
        assert ("input_lineage" in decision) == strict
        decisions.append(decision)
    for key in ["composite_score", "exposure_ceiling_pct", "recommendation", "component_scores"]:
        assert decisions[0][key] == decisions[1][key]


@pytest.mark.parametrize("mutation", ["missing", "run", "stale"])
def test_replay_rejects_invalid_producer_semantics_and_keeps_publication(
    tmp_path,
    monkeypatch,
    mutation,
):
    original = replay._market_analysis

    def altered(*args, **kwargs):
        payload = original(*args, **kwargs)
        block = payload.get("data_provenance")
        if block:
            if mutation == "missing":
                del payload["data_provenance"]
            elif mutation == "run":
                block["run_id"] = "unrelated-run"
            else:
                block["as_of"] = "2025-01-01"
        return payload

    monkeypatch.setattr(replay, "_market_analysis", altered)
    published = tmp_path / "published"
    published.mkdir()
    marker = published / "old.json"
    marker.write_text("unchanged")
    with pytest.raises(replay.ReplayError):
        replay.execute_replay(ROOT, SPEC, "required-only", published)
    assert list(published.iterdir()) == [marker]
    assert marker.read_text() == "unchanged"


def test_required_handoff_declarations():
    spec = replay.load_yaml(SPEC)
    assert spec["steps"][0]["required_provenance"] == ["market_breadth_report"]
    assert spec["steps"][1]["required_provenance"] == ["uptrend_report"]
    assert "required_provenance" not in spec["steps"][2]
