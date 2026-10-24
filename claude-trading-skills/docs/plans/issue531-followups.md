# Issue 531 implementation plan

Selected after live GitHub queue verification: PRs 561, 563, 568 are CLEAN,
89 passing checks each, one scheduled-link skip, no requested changes or inline
comments. Their files do not overlap the following scope. Root branch is left
untouched; this run uses a fresh origin/main worktree.

Candidate exclusions: 332, 496, 495, 298, 297, 523 already have local/remote
branches (496 also has a worktree; 332 and 495 have registered worktrees).
524 requires a maintainer ruleset; 515 requires point-in-time evaluation data
for its calibration acceptance. 531 has no preexisting branch/worktree.

1. Pair historical run IDs and aggregate percentages correctly in the policy doc.
2. Render expiry day 0 as expires today, day 1 in singular, other days in plural;
   test the emitted warning text and preserve inclusive expiry policy.
3. Preserve the already-fixed all(expiries) regression pin: empty waiver lists
   are valid after retirement, and no min(empty) operation remains on main.
4. Mark REIT basis FFO_UNAVAILABLE until a usable FFO payout assessment exists,
   including missing cashflows and missing/zero dividend early returns. Set FFO
   only when calculate_ffo_payout_ratio returns a ratio; preserve scoring.
5. Distinguish derived nonfinite FCF from missing inputs using NON_FINITE for
   amount/coverage status, preserve null amounts and JSON finiteness, preserve
   NO_DIVIDEND precedence, and explicitly describe unavailable coverage in the
   non-REIT note (never the successful-coverage note).
6. Add targeted regression tests, regenerate the value-dividend-screener bundle.
   Run skill and matrix pytest, ruff, required generator/metadata/snapshot checks,
   pre-commit all files and diff check. Shared matrix changes warrant full suite.
7. Obtain objective code review (maximum three rounds), fix all findings, commit,
   push and open one draft PR. Use Closes #531 only with all acceptance points
   satisfied, including the pin already satisfied on main. Verify closing refs,
   draft state and CI. Do not merge.

Plan review round 1: reviewer identified overflow note fallthrough and requested
an explicit definition of FFO basis on early returns. Both are incorporated
above; the reviewer confirmed no additional findings before implementation.

Implementation review round 1: no actionable findings; reviewer independently
ran 114 related tests successfully. Historical evidence pairing follows the
Issue's verified run-to-percentage mapping. Targeted Python 3.9 tests: 146 skill
tests and 69 matrix tests pass. Ruff and all required drift/metadata checks pass;
pre-commit --all-files passes. Full suite initially failed due to sandbox access
to ~/.cache/uv and was restarted outside that restriction.

Full suite final result: 75/75 matrix rows passed, exit 0; repo-scripts
2189 passed / 1 skipped. Known skips remain skips, not individual test passes.
