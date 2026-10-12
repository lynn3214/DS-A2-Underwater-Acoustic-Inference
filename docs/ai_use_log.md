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

## ChatGPT research assistance and AI-assisted review

- Tool: OpenAI ChatGPT.
- Model and effort: GPT-6; the student reports the interface label **Luna** and **Medium** thinking effort for this conversation. These UI labels are recorded as student-reported configuration, not independently verified model metadata.
- Scope: research planning, methodology discussion, Codex task specification, critique of reported and available source-code results, deliverable review, and submission guidance. ChatGPT did not implement or execute the full experiment in the student's local environment.

### Assignment interpretation and research planning

- Task: Interpret the DS-A2 requirements and compare candidate research settings, including the previous robotics dataset and real underwater-acoustics observations.
- Accepted advice: use NOAA SanctSound SB02_13 as the candidate for a real-data scientific question; pair day and night windows by local date; separate the observational sound-level contrast from controlled simulation and methodological validation.
- Rejected/deferred alternative: reusing the DS-A1 robotics dataset solely for project continuity.
- Methodological clarification: the estimand concerns arithmetic means of published hourly dB indicators, not linear acoustic-energy means; the observational comparison does not establish causal effects.

### Analysis design and methodological choices

- Task: Help define the research question, daily paired-difference estimand, null and alternative hypotheses, operational meaningful-effect thresholds, sampling-distribution simulation, power analysis, and the AR(1) assumption-violation counterexample.
- Accepted advice: prespecify selection and analysis rules; preserve meaningful failures and negative findings; compare IID t inference against HAC and moving block bootstrap (MBB); overlay analytical and Monte Carlo power under an IID Gaussian model; examine real-data ACF without treating estimated correlation as a known parameter.
- Modified advice: use 3 dB as a *prespecified operational* meaningful-effect threshold, with 1 dB as a sensitivity reference, rather than claiming a universal NOAA or ecological threshold. Treat MBB block length and HAC bandwidth as specified methods with finite-sample limitations, not guaranteed corrections.
- Rejected/deferred suggestions: additional empirical-residual resampling and unrestricted sign-flip permutation (extra complexity and dependence assumptions); astronomical sunrise/sunset sensitivity analysis (outside the fixed-clock-time primary estimand; discussed as a limitation).

### Phase 0 / 0.5 guidance and review

- Task: Draft instructions for the Codex feasibility audit, review the reported data-source and timestamp ambiguities, and request targeted additional metadata checks before scientific analysis.
- Accepted advice: stop outcome-dependent analysis until the hourly time-bin semantics could be justified; distinguish product-specific NOAA netCDF evidence from indirect evidence from related products; retain the 10-versus-20 Hz frequency-edge discrepancy and missing per-record QC as limitations.
- Review scope: ChatGPT considered audit reports and, in subsequent repository review, source-code and saved-result consistency. Codex, not ChatGPT, executed the NOAA audit and synthetic tests.

### Phase 1 / 2 review and final-deliverable checks

- Task: Review the reported NOAA inference, power and AR(1) counterexample, examine relevant implementation and saved results, identify maintainability and interpretation issues, and propose a narrow final QA scope.
- Numerical cross-check: the reported standard deviation (approximately 3.123 dB) and sample size (64) imply an IID standard error of approximately 0.390 dB, consistent with the reported IID interval and p-value.
- Interpretation advice: a confidence interval containing zero does not prove zero effect; inflated AR(1) rejection under a true null reflects Type I error, not superior power; HAC and MBB may still under-cover in dependent finite samples.
- Accepted/retained limitation: document duplicate YAML/source parameter values and test consistency rather than refactoring validated scientific computation late in the project.
- PDF review: ChatGPT visually inspected the supplied ten-page Phase 1 PDF, including the effect/CI, sampling-distribution, power and counterexample figures, and found no obvious page clipping, overlapping elements, or missing figures. This was AI-assisted inspection, not independent human visual sign-off.
- Documentation advice: make the notebook introduction portable by referencing a Python environment with documented dependencies rather than requiring the reader's environment to have the student's local name; synchronize the introduction with the notebook-generation template, while preserving the actual `nussem1` environment in execution/provenance records.

### Verification boundary

- ChatGPT provided methodological reasoning, selected hand calculations, repository/source review, document feedback, and AI-assisted PDF inspection. It did not independently run the complete notebook, test suite, NOAA retrieval, or Monte Carlo study in the student's `nussem1` environment.
- Codex implementation and internal checks are recorded in the phase-specific entries above; the student's separate clean-kernel execution is recorded in the **Independent student verification** section.
- The source review and PDF assessment are not a guarantee of correctness. Responsibility for approving the final interpretation and submission remains with the student.

## Verification status at final-log preparation

- The earlier phase-specific statements of **human review pending** are historical status statements recorded when those phases finished; they should not be retroactively rewritten.
- On 2026-10-12, the student reported a successful personal clean-kernel run of all 11 code cells and matching outputs. This is the scope of the student verification presently documented.
- Codex subsequently compared the notebook outputs with the committed version; ChatGPT provided separate AI-assisted design, source/result, and PDF review. Neither is represented as an instructor's or a separate human expert's endorsement.
- Remaining scientific limitations are documented elsewhere in the repository, including the frequency-edge metadata conflict, absent row-level QC, a single short deployment, and method limitations under temporal dependence.
