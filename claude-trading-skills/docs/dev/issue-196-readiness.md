# Learning-loop readiness: numeric evidence

Issue: #196 (remains open). Both learning-loop skills remain beta.

## Scope and evidence

Assessed base: `40ae281` (2026-09-27 UTC). The deterministic reviewer scored
trade-performance-coach 100/100 and stockbee-setup-fluency-trainer 96/100,
with nine tests per skill. The improvement-loop threshold is 90. These are
automated-axis scores, not independent financial or security approval.

Inspection found that NaN risk could yield a within-limit finding, an invalid
maximum could silently fall back to planned risk, and huge integers could raise
conversion overflow. The coach now validates its six consumed numeric fields
before analysis and before any CLI report writes. Zero and numeric strings remain
supported; missing/null values keep existing semantics. Loss counts must be whole
numbers. Invalid numeric evidence returns CLI exit code 2, including multi-input
sources. Existing output files are preserved on this rejection path.

Regressions cover all six fields, nonfinite and negative values, booleans, bad
strings, conversion overflow, fractional loss counts, valid boundaries, null
fallback, extreme finite risk, JSON/YAML input, and existing/new output directories.

## Remaining promotion work

- Report IDs and explicit output names still need a path-safety assessment.
- Multiple source records still use the documented shallow wrapper; validation
  of each source does not implement aggregation.
- Other input structures, boolean semantics, and malformed-file handling need
  a complete instruction/error-contract assessment.
- The trainer has not received a full independent financial/security audit in
  this slice. Its automated score alone does not establish readiness.
- Establish the applicable eight-axis evidence and live high-severity Issue gate
  described in `production-verification.md` before deciding promotion.

No lifecycle or verification metadata is promoted by this change. Use `Refs #196`
until both skills meet the complete acceptance criteria.

## Review disposition

Plan round 1 rejected score-only promotion and required distinguishing invalid
limits from missing values. Round 2 approved this bounded numeric fix, source-level
validation, output-preservation tests, and explicit remaining gaps. Implementation
review and final command results are recorded in the draft PR.
