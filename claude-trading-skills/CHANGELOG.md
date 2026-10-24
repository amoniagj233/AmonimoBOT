# Changelog

All notable changes to this repository are recorded here in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. Repository releases use stable [Semantic Versioning](https://semver.org/) tags (`vMAJOR.MINOR.PATCH`). A `.skill` package does not have an independent version.

## [Unreleased]

### Skills

- Prepare verified `.skill` assets and SHA-256 checksums from a tagged repository revision.
- Migrate the Batch A FMP callers (earnings-calendar, economic-calendar-fetcher, institutional-flow-tracker, cot-contrarian-detector) from hand-rolled HTTP/retry code to the generated vendored `fmp_client.py` (Issue #495 batch A). Deliberate change: the FMP API key is now sent as an `apikey` header (never in a URL) for these four skills; the economic-calendar 402/404 and COT `(data, error)` redaction contracts are preserved. Note: 5xx no longer gets the COT-specific multi-attempt backoff (single 429 retry from the shared client, which fails closed otherwise), and earnings-calendar's former distinct `Request timeout` / `Connection error` wordings now collapse into the shared client's transport-error wording. Also, a 200 COT payload that parses to a non-list now degrades to `([], error=None)` instead of returning the raw value, and non-429 transport failures do not retry under the shared client.

### Workflows

- Add a tag-driven release process. No GitHub Release has been published by this change.

### Breaking metadata

- None.
