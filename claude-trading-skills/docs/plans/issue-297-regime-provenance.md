# Issue #297: market-regime-daily provenance handoff

## Selection and boundaries

P1 #297 has an owner-approved bounded end-to-end slice. Current main is b29c6df.
Open PRs #571–#575 and existing worktrees were checked. Avoid their FMP clients,
market-top implementation/03 golden, packaging infrastructure and CI hooks.
This implements required breadth/uptrend handoffs, not all FMP producers; #297 remains open.
No trading execution or live writes.

## Implementation

1. Vendor one identical stdlib-only provenance_contract.py in breadth, uptrend and
   exposure scripts. Test byte parity and compatibility with the shared schema validator.
   Helpers construct schema 1.0 with honest false quality flags and validate run/time semantics.
2. Real breadth/uptrend mains accept --run-id (unique default), capture UTC retrieval
   after successful fetch, and use actual last primary-data date, never the report clock,
   as as_of. Record actual dataset sources and identify auxiliary sources whose dates
   are unverified. Reject missing/invalid primary dates. Do not change financial scoring.
3. Exposure adds opt-in --require-provenance with mandatory --run-id and --as-of
   (aware evaluation timestamp), plus --max-age-days (default 3, finite nonnegative integer).
   Require breadth/uptrend and validate schema, expected run, valid timezone, UTC retrieval,
   as_of <= retrieval <= evaluation, data age <= configured calendar days. Compare business
   dates in the declared reporting timezone; datetime as_of uses actual instant. Reject
   invalid inputs before output creation; preserve existing output. Legacy CLI stays compatible.
   Emit accepted input lineage and explicit boundaries: quality flags remain unknown,
   auxiliary-source dates and optional top-risk/other inputs are outside this strict gate.
   Same-run ID is a caller-provided consistency marker, not authenticated provenance or PIT proof.
4. Enable required_provenance for replay breadth/uptrend. Its existing component fixtures
   remain honestly fictional: fixture provider, fixed retrieval, fixture as_of, false flags,
   explicit common run ID. Exercise strict consumer CLI and compare native recomputation.
   Regenerate only 01/02/04 and manifests in both variants; leave 03 byte-identical.
5. Document actual invocation with shared run ID and strict evaluation time, rollout scope,
   conservative freshness policy and replay boundaries. Refresh the three skill packages.

## Verification

- Mock-fetch tests of both real producer mains establish source/date/retrieval/run fields.
- Consumer tests: valid input, missing block/field, schema mismatch, invalid date/timezone,
  wrong run, stale/future timestamps, exact freshness boundaries, absent required input,
  output preservation and legacy compatibility. Verify packaged standalone imports.
- Replay tests: missing provenance and shifted as_of/run at producer/consumer boundaries,
  preserve old publication on failure; both variants deterministic golden check.
- Run each affected skill suite independently; shared provenance and replay tests; lint,
  metadata/docs/package gates and required full pre-push matrix.

## Independent reviews

Plan and code each receive an independent sub-agent review, up to three rounds.
Resolve all material findings before committing and creating a PR. Record results here.

Plan review round 1: independent reviewer approved without required changes. Final plan.

## Results

- Plan review: round 1 approved; no required changes.
- Code review: round 1 found a missing mkdir in the documented invocation; fixed.
  Round 2 approved with no remaining findings. Independent 42 tests and three
  extracted standalone package CLI checks passed.
- Official skill suites: breadth 170 passed (95.21%), uptrend 233 passed (91.64%),
  exposure 138 passed (87.38%); each vendored helper covered 100%.
- Provenance/replay targeted suite: 136 passed. Both replay variants match goldens;
  03 top-risk golden is byte-identical to base. Financial scores stay unchanged.
- Pre-commit all-files checks passed. Full pre-push matrix is a separate final gate.
