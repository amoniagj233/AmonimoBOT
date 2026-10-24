---
layout: default
title: "Edge Signal Aggregator"
grand_parent: English
parent: Skill Guides
nav_order: 11
lang_peer: /ja/skills/edge-signal-aggregator/
permalink: /en/skills/edge-signal-aggregator/
---

# Edge Signal Aggregator
{: .no_toc }

Aggregate and rank signals from multiple edge-finding skills (edge-candidate-agent, theme-detector, sector-analyst, institutional-flow-tracker) into a prioritized conviction dashboard with weighted scoring, deduplication, and contradiction detection.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[Download Skill Package (.skill)](https://github.com/tradermonty/claude-trading-skills/raw/main/skill-packages/edge-signal-aggregator.skill){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/edge-signal-aggregator){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

Combine outputs from multiple upstream edge-finding skills into a single weighted conviction dashboard. This skill applies configurable signal weights, deduplicates overlapping themes, flags contradictions between skills, and ranks composite edge ideas by aggregate confidence score. The result is a prioritized edge shortlist with provenance links to each contributing skill.

---

## 2. When to Use

- After running multiple edge-finding skills and wanting a unified view
- When consolidating signals from edge-candidate-agent, theme-detector, sector-analyst, and institutional-flow-tracker
- Before making portfolio allocation decisions based on multiple signal sources
- To identify contradictions between different analysis approaches
- When prioritizing which edge ideas deserve deeper research

---

## 3. Prerequisites

- Python 3.9+
- No API keys required (processes local JSON/YAML files from other skills)
- Dependencies: `pyyaml` (standard in most environments)

---

## 4. Quick Start

```bash
python3 skills/edge-signal-aggregator/scripts/aggregate_signals.py \
  --edge-candidates reports/edge_candidate_agent_*.json \
  --edge-concepts reports/edge_concepts_*.yaml \
  --themes reports/theme_detector_*.json \
  --sectors reports/sector_analyst_*.json \
  --institutional reports/institutional_flow_*.json \
  --hints reports/edge_hints_*.yaml \
  --output-dir reports/
```

---

## 5. Workflow

### Step 1: Gather Upstream Skill Outputs

Collect output files from the upstream skills you want to aggregate:
- `reports/edge_candidate_*.json` from edge-candidate-agent
- `reports/edge_concepts_*.yaml` from edge-concept-synthesizer
- `reports/theme_detector_*.json` from theme-detector
- `reports/sector_analyst_*.json` from sector-analyst
- `reports/institutional_flow_*.json` from institutional-flow-tracker
- `reports/edge_hints_*.yaml` from edge-hint-extractor

### Step 2: Run Signal Aggregation

Execute the aggregator script with paths to upstream outputs:

```bash
python3 skills/edge-signal-aggregator/scripts/aggregate_signals.py \
  --edge-candidates reports/edge_candidate_agent_*.json \
  --edge-concepts reports/edge_concepts_*.yaml \
  --themes reports/theme_detector_*.json \
  --sectors reports/sector_analyst_*.json \
  --institutional reports/institutional_flow_*.json \
  --hints reports/edge_hints_*.yaml \
  --output-dir reports/
```

Optional: Use a custom weights configuration:

```bash
python3 skills/edge-signal-aggregator/scripts/aggregate_signals.py \
  --edge-candidates reports/edge_candidate_agent_*.json \
  --weights-config skills/edge-signal-aggregator/assets/custom_weights.yaml \
  --output-dir reports/
```

### Step 3: Review Aggregated Dashboard

Open the generated report to review:
1. **Ranked Edge Ideas** - Sorted by composite conviction score
2. **Signal Provenance** - Which skills contributed to each idea (with `evidence_id` per contributor)
3. **Contradictions** - Conflicting signals flagged for manual review
4. **Deduplication Log** - Merged overlapping themes (verbatim re-ingested duplicates get no bonus)
5. **Invalid Signals** - Scores that are NaN/infinite, negative, or out of declared range are dropped and reported, never converted into confidence

### Step 4: Act on High-Conviction Signals

Filter the shortlist by minimum conviction threshold:

```bash
python3 skills/edge-signal-aggregator/scripts/aggregate_signals.py \
  --edge-candidates reports/edge_candidate_agent_*.json \
  --min-conviction 0.7 \
  --output-dir reports/
```

---

## 6. Resources

**References:**

- `skills/edge-signal-aggregator/references/signal-weighting-framework.md`

**Scripts:**

- `skills/edge-signal-aggregator/scripts/aggregate_signals.py`

---

## 7. Producer Contract and Scoring Rules (schema 1.1)

Since schema 1.1, aggregation is idempotent and strict about score validity (Issue #510):

- **`evidence_id`** (optional, per item): stable evidence identity. Re-ingesting the same
  evidence (same skill + `evidence_id`) never adds a bonus. Without it a
  deterministic fallback is derived from skill, signal reference, title, tickers, and direction
  (timestamps excluded, so refreshed timestamps cannot forge a new identity). When copies
  differ, the newest observation wins: the latest parsed timezone-aware timestamp (date-only
  and naive values read as UTC) supplies the retained score. Equal, missing, or unparsable
  timestamps keep the highest raw score, then a stable key, so ingestion order cannot change
  the result. Only ISO-8601 strings (or `YYYY-MM-DD`) are ordered; epoch numbers and compact forms such as `20261010` count as missing timestamps. A newer, lower score replaces an older, higher one, and discarded copies are
  listed in `deduplication_log[].discarded_copies`.
- **`score_scale`** (optional, per item or per document: `"0-1"` / `"0-100"`): declared scales
  are enforced strictly. NaN/infinity, negative, and out-of-range values are rejected into
  `invalid_signals`; a present-but-unparsable declaration (`""`, `"foo"`) is rejected as
  `missing_scale`. When the key is absent, values in (1, 100] are assumed 0-100 and flagged
  (`score_scale_assumed: true` + `scale_assumptions_report` with the original `value` and the
  `normalized_value`); values > 100 are rejected.
- **Agreement rule**: bonuses fire on `agreement_tier = min(distinct evidence ids, distinct
  event fingerprints, distinct skills)`. Verbatim cross-skill restatements (identical normalized
  title + tickers) count once and cannot self-confirm; re-ingested duplicates earn nothing.
  Known limitation: event fingerprints are vocabulary-based, so paraphrased cross-skill
  restatements with disjoint word sets still earn the agreement bonus.
- **`merge_bonus_per_duplicate`** (in custom weights YAML) is deprecated and ignored.
