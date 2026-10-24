"""Offline replay contract for the strategy research pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_replay import execute_replay  # noqa: E402

SPEC = ROOT / "examples/workflows/strategy-research-pipeline/replay.yaml"


def test_replay_binds_tickets_hints_metrics_and_preserves_human_gate(tmp_path: Path) -> None:
    output = tmp_path / "replay"
    report = execute_replay(ROOT, SPEC, "required-only", output)

    assert report["status"] == "completed"
    assert [step["executor_mode"] for step in report["steps"]] == [
        "native_cli",
        "native_cli",
        "native_cli",
        "manual_contract",
    ]
    hints = yaml.safe_load((output / "02_edge_hints.yaml").read_text())
    tickets = json.loads((output / "03_final_research_tickets.json").read_text())
    assessment = json.loads((output / "04_backtest_quality_assessment.json").read_text())
    assert hints["as_of"] == tickets["as_of"] == assessment["provenance"]["as_of"]
    assert tickets["tickets"]
    assert assessment["provenance"]["ticket_id"] in {ticket["id"] for ticket in tickets["tickets"]}
    assert assessment["status"] == "HOLD"
    assert assessment["evaluation_invoked"] is False
    assert "verdict" not in assessment
    assert any("period differs" in reason for reason in assessment["reasons"])
    assert any("look-ahead" in reason for reason in assessment["reasons"])


def test_replay_holds_metrics_from_another_ticket(tmp_path: Path) -> None:
    source = SPEC.parent / "replay-inputs/backtest_metrics.json"
    metrics = json.loads(source.read_text())
    metrics["ticket_id"] = "different-ticket"
    bad = tmp_path / "inputs" / "bad-metrics.json"
    bad.parent.mkdir()
    bad.write_text(json.dumps(metrics) + "\n")

    execute_replay(
        ROOT,
        SPEC,
        "required-only",
        tmp_path / "replay",
        input_overrides={"backtest_metrics": bad},
    )
    result = json.loads((tmp_path / "replay/04_backtest_quality_assessment.json").read_text())
    assert result["status"] == "HOLD"
    assert result["evaluation_invoked"] is False
    assert "verdict" not in result
    assert any("ticket ID is absent" in reason for reason in result["reasons"])
