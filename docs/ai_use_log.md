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

## Phase 1 statistical analysis and deliverables

- Tool: OpenAI Codex.
- Task: freeze a prospective design before outcome analysis; implement aggregation, inference, IID simulations, AR(1) counterexamples, figures, notebook, PDF, tests, and documentation.
- Accepted recommendations: validate the source checksum and 6/8 and 8/8 counts against Phase 0.5; report an MBB percentile interval without inventing a p-value; numerically integrate the noncentral-t representation when SciPy's direct lower-tail CDF returns NaN.
- Modified/rejected recommendations: Statsmodels was absent, so HAC was implemented from its explicit Newey–West formula and tested directly instead of installing a dependency. An initial AR(1) ACF tolerance was too narrow for n=80; validation was changed to n=300 to account for finite-length centering bias. Operational interpretation thresholds were taken as 3 dB and 1 dB from the explicit Phase 1 task.
- Automated verification actually run: 24 unit/Monte Carlo tests passed; full pipeline completed; final clean-kernel notebook execution saved outputs. Jupyter needed permission to bind its local kernel sockets. Detailed failures and fixes are in `docs/experiment_log.md`.
- Numerical verification: observed eligibility matched Phase 0.5 at 64 dates under both coverage rules; t inference matched SciPy; noncentral-t power matched a Monte Carlo check; AR(1) mean, variance, and lag-one properties were checked over 30,000 series; source checksum was verified before analysis.
- Human review: pending. No student, instructor, or external reviewer is claimed to have verified results.
- Independent verification: not performed. Automated testing and clean-kernel execution establish code-path reproducibility, not independent scientific review of the estimand, NOAA metadata, or interpretation.
- Review items: NOAA clarification of the 10 vs 20 Hz lower edge; absent record-level QC; adequacy of the frozen HAC bandwidth/reference; MBB block-length limitations; single short deployment; and appropriateness of the operational 3 dB threshold.

## Phase 2 final quality assurance

- Tool: OpenAI Codex.
- Task: inspect the existing project and perform final automated, numerical-consistency, clean-kernel, PDF, documentation, and repository hygiene checks without changing the frozen scientific design.
- Accepted actions: document the YAML/source parameter mapping; add six automated checks comparing saved outputs and observed-data reference calculations to the frozen protocol; complete README reproduction instructions; generalize unnecessary historical local interpreter paths; preserve notebook execution evidence.
- Rejected/omitted actions: no source-level parameter refactor because existing outputs matched the frozen values and changing execution plumbing was not necessary for QA; no protocol or result changes; no package installation.
- Automated verification: the final `nussem1` suite passed 33 tests; notebook clean-kernel command exited 0 with 11 code cells executed and zero errors; JSON/YAML/CSV/notebook structure checks and Git whitespace/security/path scans are recorded in `docs/final_qa_report.md`.
- PDF validation: Ghostscript extraction/rendering and visual inspection of all ten pages found no layout defects; pixel comparison showed the regenerated and prior renders identical. This AI-assisted inspection is not independent human verification.
- Human review: pending. Codex has not represented student review, external review, or course submission as completed.
- Remaining independent checks: scientific/design review of dependence assumptions and thresholds; NOAA confirmation of the lower frequency-edge discrepancy and absent record-level QC; course-summary approval and final submission decision.

## Independent student verification — 2026-10-12

- Verifier: the student, reporting their own execution.
- Action: restarted the Jupyter kernel and ran all 11 code cells in the existing `nussem1` environment.
- Student-reported result: all 11 cells completed successfully, and the results matched the committed version.
- This student execution is separate from Codex's subsequent comparison of the saved notebook outputs against the committed notebook. Codex found that, after excluding the revised first Markdown cell, code, execution counts, visible outputs, and embedded figures matched; no error outputs were present. This comparison did not independently rerun the Notebook or verify the student's local kernel session.
