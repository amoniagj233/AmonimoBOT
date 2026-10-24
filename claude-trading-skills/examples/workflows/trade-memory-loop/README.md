# Example: `trade-memory-loop`

Executable required-only and full-path replays for the canonical
[`trade-memory-loop`](../../../workflows/trade-memory-loop.yaml) workflow.

> Illustrative only—not investment advice. `EXMPL`, its thesis, outcome, and
> aggregate backtest metrics are fictional. The replay never calls a broker or
> changes a user's Trader Memory state.

## Variants

| Variant | Executed steps | Optional steps |
|---|---|---|
| [`sample-run/`](sample-run/) | close → postmortem → lessons journal | coaching and metric evaluation skipped |
| [`sample-run-full-path/`](sample-run-full-path/) | close → postmortem → coaching → metric evaluation → lessons journal | all included |

The replay starts from a schema-valid fictional `ACTIVE` thesis, closes it with
the real `trader-memory-core` CLI in disposable state, and passes the resulting
`CLOSED` artifact to downstream steps. The required-only path proves that the
workflow completes when both optional steps are absent.

## Evidence classification

The manifest does not collapse native execution and human decisions:

| Step | Evidence |
|---|---|
| 1 | `native_cli`: Trader Memory `close` against temporary state |
| 2 | `composite`: native `signal-postmortem.create_postmortem_record` classification plus a human-approved root-cause fixture |
| 3 | `composite`: native Trade Performance Coach CLI plus human-approved operating rules |
| 4 | `native_cli`: Backtest Expert evaluates supplied aggregate metrics |
| 5 | `composite`: native Trader Memory update/postmortem APIs plus a human-approved lesson |

Root-cause and lesson decisions include the exact SHA-256 values of their
normalized source artifacts. The lessons step rebuilds disposable Trader Memory
state from the verified closed-thesis snapshot carried by the declared
postmortem artifact; it does not trust hidden state from the close step. A stale decision, wrong variant, missing optional
source, malformed thesis, corrupt handoff, or injected journal failure stops the
replay without replacing the published golden tree.

Step 4 is deliberately narrow: it proves that the native evaluator can assess
the bundled fictional metrics and hand off a structured result. It does **not**
claim that a strategy was re-run, that the evaluator consumed the postmortem,
or that the illustrative result is live trading evidence.

## State and publication boundary

- subprocess environments remove API-key, token, secret, password, and proxy variables;
- the replay invokes the installed Python interpreter directly and never launches `uv`;
- Trader Memory writes occur only under a disposable replay directory;
- Trader Memory atomically replaces each state file, but does not provide a
  multi-file transaction across thesis, index, and journal;
- the harness publishes the complete generated tree transactionally, so a late
  failure leaves an existing destination unchanged.

Run from the repository root:

```bash
python3 scripts/workflow_replay.py run \
  --spec examples/workflows/trade-memory-loop/replay.yaml \
  --variant required-only \
  --output-dir /tmp/trade-memory-required
python3 scripts/workflow_replay.py check
```

`sample-run/` and `sample-run-full-path/` are generated outputs. Edit
`replay.yaml` or `replay-inputs/`, then run `python3 scripts/workflow_replay.py
generate`; do not hand-edit the golden trees.
