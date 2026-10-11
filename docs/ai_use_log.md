# AI Use Log

## Phase 0 protocol preparation

- Tool: OpenAI Codex.
- Task: Read repository instructions, create the pre-data audit record, then execute only the NOAA feasibility audit.
- Accepted recommendations: protocol/config structure, outcome-blind audit boundary, staged fallback requiring approval.
- Rejected recommendations: none recorded at protocol freeze.
- Human review: pending; this log does not claim independent human verification.
- Independent verification: pending actual audit review.

## Phase 0 audit execution

- Tool: OpenAI Codex.
- Task: Acquire official NOAA processed hourly data after the protocol commit, implement the outcome-blind audit, run synthetic-only tests, and document the gate.
- Accepted recommendations: preserve conflicting and missing metadata as uncertainty; do not compute window eligibility when timestamps are not interpretable.
- Rejected recommendations: none recorded.
- Human review: pending; no independent reviewer has verified the audit yet.
- Independent verification: eight synthetic tests passed on the final run; they verify implementation behavior only and are not independent validation of NOAA metadata or the analysis design.

## Phase 0.5 metadata resolution

- Tool: OpenAI Codex.
- Task: Inspect direct product metadata and user-specified related NOAA records; complete coverage under the newly justified timestamp convention.
- Accepted recommendation: the exact SB02_13 netCDF coordinate comment is direct product-specific evidence for bin starts; related products are labelled indirect.
- Accepted recommendation: preserve frequency conflict and report conditional feasibility pending clarification.
- Rejected recommendations: none recorded.
- Human review: pending independent review; no human verification is claimed.
- Independent verification: pending. Synthetic tests validate implementation behavior but do not independently verify the NOAA source record.
