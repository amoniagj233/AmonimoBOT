# Example: `stockbee-20pct-study-daily`

Executable required-only and full-path replays for the canonical
[`stockbee-20pct-study-daily`](../../../workflows/stockbee-20pct-study-daily.yaml)
workflow.

> Illustrative only — not investment advice. `FICT20`, its prices, and its
> earnings headline are fictional. Nothing here submits or schedules an order.

Both variants run the real offline `run_20pct_study.py` CLI through scan,
news enrichment, five-day outcome maturation, and cohort summarization. The
fixture deliberately produces one mover, one matched news catalyst, one
matured outcome, and one research candidate so an empty pipeline cannot pass.

| Variant | Native steps | Optional step 5 |
|---|---|---|
| `sample-run/` | scan → enrich → update-outcomes → summarize | skipped |
| `sample-run-full-path/` | same | human-approved `manual_contract` |

The full-path lesson remains `journal_only` because one fictional observation
cannot justify a trading-rule change. Its source hashes bind the lesson to the
generated cohort summary and edge hints. Provenance explicitly records that no
native trader-memory-core append API was executed.

Run from the repository root:

```bash
python3 scripts/workflow_replay.py run \
  --spec examples/workflows/stockbee-20pct-study-daily/replay.yaml \
  --variant required-only \
  --output-dir /tmp/stockbee-20pct-required
python3 scripts/workflow_replay.py check
```

Every native command receives bundled `--prices-json` or `--news-json` input;
none receives a live-universe or API-key flag. Sensitive environment variables
are removed before subprocess execution. This is an offline-input policy, not
an operating-system network sandbox.
