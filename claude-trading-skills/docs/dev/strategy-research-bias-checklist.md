# Strategy Research Bias Checklist

> Source: GitHub issue #297 (mandatory checklist referenced by `backtest-expert`,
> the `edge-*` pipeline, `residual-edge-analyzer`, and
> `edge-strategy-reviewer`).
> Canonical data: [skills/edge-strategy-reviewer/assets/bias_checklist.yaml](https://github.com/tradermonty/claude-trading-skills/blob/main/skills/edge-strategy-reviewer/assets/bias_checklist.yaml)

## Purpose

Backtest and strategy-research results are only as trustworthy as the biases
they fail to control for. This checklist enumerates the bias and realism concerns
a strategy draft must address before it is considered fit for further work. It is
**mandatory**, not advisory: the reviewer downgrades a draft that leaves a
required concern unaddressed.

## Checklist items

Every item is `required`. An item is **addressed** only when the draft declares
it in its `bias_checklist` block with a truthy value (a string note, `true`, or a
dict with `addressed: true`).

| ID | Concern | Coverage hint (draft text signal) |
|----|---------|-----------------------------------|
| `look_ahead` | Look-ahead bias | `point-in-time`, `as-of`, `future data` |
| `survivorship` | Survivorship bias | `survivorship`, `delisted`, `non-surviving` |
| `universe_selection` | Universe selection | `universe`, `selection criteria`, `constituents` |
| `delisted_securities` | Delisted securities | `delist`, `trading suspended`, `halted` |
| `earnings_announcement_timing` | Earnings announcement timing | `earnings announce/report/date/timing` |
| `split_dividend_adjustment` | Split & dividend adjustment | `split`, `dividend`, `adjusted`, `corporate action` |
| `transaction_costs_slippage` | Transaction costs & slippage | `transaction cost`, `commission`, `slippage`, `after costs` |
| `short_borrow_availability` | Short borrow availability | `short borrow`, `borrow fee`, `locate`, `HTB` |
| `liquidity_capacity` | Liquidity & capacity | `liquidity`, `capacity`, `ADV`, `market impact` |
| `parameter_multiplicity` | Parameter multiplicity | `parameter grid/count`, `overfit`, multiple configs |
| `walk_forward_out_of_sample` | Walk-forward & OOS | `walk-forward`, `out-of-sample`, `OOS`, `hold-out` |
| `benchmark_attribution` | Benchmark attribution | `benchmark`, `attribution`, `relative to (index)` |
| `regime_dependence` | Regime dependence | `regime`, `across regimes`, `risk-on/off`, `stress` |

## Declaring coverage in a draft

A strategy draft declares which concerns it has already addressed in an optional
`bias_checklist` block:

```yaml
bias_checklist:
  look_ahead: "Uses point-in-time snapshots; no look-ahead"
  survivorship: "Universe includes delisted names"
  universe_selection: "S&P 500 constituents at each rebalance"
  # ... any other addressed items ...
```

Values may be:

- a non-empty string note,
- `true`,
- a dict `{addressed: true, note: "..."}` for explicit control.

An item is **unaddressed** when its key is absent, `false`, an empty string, or a
dict with `addressed: false`.

## Enforcement in `edge-strategy-reviewer`

The reviewer scores every draft against the checklist when run with the bias flag:

```bash
# Use the bundled checklist
python3 skills/edge-strategy-reviewer/scripts/review_strategy_drafts.py \
  --drafts-dir reports/edge_strategy_drafts/ \
  --bias-checklist \
  --output-dir reports/

# Any required item left unaddressed downgrades PASS -> REVISE and clears
# export eligibility (never raises a REJECT).
```

- **Non-scoring:** the bias gate never changes the confidence score or the
  C1–C8 weights.
- **Attached output:** each reviewed draft gets a `bias_review` array (one entry
  per checklist item with `item_id`, `title`, `required`, `addressed`,
  `noted_in_draft`, `note`).
- **Informational `noted_in_draft`:** a heuristic that reports whether a concern's
  concept text appears anywhere in the draft, so an author can see that a rule is
  discussed in prose but not yet declared. Escalation is driven only by
  `addressed`.

## Drift / consistency

The checklist function is loaded from the YAML in assets, and the semantic table
here mirrors it. When items change, update both the YAML and this table together.
A drift test enforces that the reviewer loads a non-empty, fully-required
checklist so a rule can never be silently dropped.
