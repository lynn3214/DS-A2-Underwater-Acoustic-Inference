# Experiment Log

## Phase 0 initialization

- Date: 2026-10-10 (client date; exact retrieval times will be recorded in UTC).
- Status: protocol setup only; no NOAA dataset has been accessed or examined.
- Planned audit command and outcomes: pending actual execution.
- Failures and negative evidence: pending; record actual errors and limitations here without fabricating results.
- No inferential analysis, power analysis, paired differences, or counterexample simulation is authorized in Phase 0.

## 2026-10-10 — NOAA source audit

- Initial source access followed protocol commit `aa4394b8474e24798096592870d0c22a1e52e00c`.
- Retrieved the 57,449-byte processed CSV and two official metadata objects; see `results/audit/provenance.json` for URLs, retrieval time, generations, and SHA-256 hashes.
- Executed `python -m unittest discover -s tests -v` in `nussem1`. First run: 7 passed, 1 failed because the synthetic UTC fixture did not map to the expected local clock windows; this was a fixture construction error. Corrected fixture and reran: all 8 passed.
- Executed `python src/audit_noaa.py` in `nussem1`; outcome-blind metrics are in `results/audit/noaa_audit.json`.
- Negative/unresolved evidence: hourly bin-label semantics absent; local time zone absent from source metadata; frequency lower bound differs in companion brief JSON; no explicit open redistribution license found; no row-level QC flags. Per protocol, window eligibility and date counts were not computed.
- No effect, inferential interval/test, power, or counterexample experiment was run.

## 2026-10-12 — Phase 0.5 metadata and coverage follow-up

- Environment: existing `nussem1`, Python 3.10.18, Conda 25.9.1, h5py 3.14.0, PyYAML 6.0.2.
- Retrieved the exact SB02_13 netCDF from the same NOAA object prefix; size 132,286 bytes, SHA-256 `6f9f0211a98f415cd2c26526ec7bae9788bc3401b5ad707b7a9a7882609fba03`.
- Direct netCDF attribute inspection verified both time coordinate comments identify one-hour-bin starts and the exact product global license permits free redistribution with disclaimers. Prior licensing uncertainty is resolved for repository inclusion.
- Tried exact SB02_13 ERDDAP `.das`; NOAA returned HTTP 403 stating this request IP is on its blacklist. This failed access is preserved in `results/audit/metadata_evidence.json`.
- The two related NOAA ERDDAP products independently say their time coordinates are bin starts; logged as indirect corroboration only.
- Under `America/New_York` with start-label semantics, the audit found 64 eligible dates under both 6/8 and 8/8 rules, in one uninterrupted run; the 30-date screen is met. Local date/hour missingness has no internal gaps.
- Unresolved negative finding: exact SB02_13 brief JSON reports 20–24,000 Hz, while its netCDF abstract/history, NCEI processing record, and CSV variable label report 10–24,000 Hz. No frequency/outcome values were used to choose a preferred timestamp convention.
- No observed day–night contrasts, intervals, tests, power, or simulations were computed.

## 2026-10-12 — Phase 1 protocol freeze and execution

- Frozen prospective design in `config/experiment_protocol.yaml` and `docs/analysis_plan.md`; commit `33261148bbcfb2a4f6e9ff27286c5f962e323138` precedes outcome computation. Source SHA-256 was checked against the frozen protocol before creating daily differences.
- Environment verified: Python interpreter from the active `nussem1` Conda environment, Python 3.10.18, Conda 25.9.1, macOS 15.5 arm64. Runtime packages were NumPy 2.2.6, SciPy 1.15.2, pandas 2.3.1, matplotlib 3.10.5, PyYAML 6.0.2, Jupyter 1.1.1, nbconvert 7.16.6. Statsmodels and PDF inspection utilities `pdfinfo`/`pdftotext` are absent; no package was installed. HAC uses its explicitly stated formula.

  Reproduce the environment activation from repository root:

  ```bash
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate nussem1
  python -c "import sys; print(sys.executable); print(sys.version)"
  ```
- Initial Phase 1 unit run: 23 tests, 1 failure. The finite-series ACF validation tolerance was too tight for n=80 due to expected demeaning bias; revised fixture length to 300. Subsequent suite: 24 tests passed.
- First analysis launch failed before reading data because of a smart-quote syntax typo in the plotting title. Corrected it. The next launch identified whitespace around the CSV's second header and a non-writable default Matplotlib cache; the reader now trims header fields and cache is repository-local/ignored.
- First full numerical run revealed SciPy returned NaN for one lower-tail noncentral-t CDF at a valid high-noncentrality power setting (sigma multiplier .5). Preserved this negative finding in development history and implemented a stable exact chi-square-mixture tail integral for non-finite direct results; the regression test now verifies finite power in that regime.
- An ensuing full run calculated all results but PDF text construction raised `NameError` because the descriptive result object was not passed into the report writer. Corrected the function interface; final full pipeline subsequently completed, exit 0.
- First clean-kernel attempt was blocked by sandbox socket binding (`PermissionError`). After approved escalated execution, the notebook pipeline completed but a figure display cell had a `Path`/string precedence error. Fixed the notebook builder, then re-executed from a clean kernel successfully. A final clean-kernel run remains part of release verification after final edits.
- Observed verified coverage matched Phase 0.5 exactly: 64 primary and 64 strict dates in one contiguous segment. Final observed estimates, simulations, checks and artifacts are detailed in `docs/phase1_results.md` and machine-readable files under `results/raw/`.
- PDF inspection utilities were unavailable. The final PDF is Matplotlib-generated and will be checked for signature, EOF, and page-object structure; visual review by a human remains outstanding.
- No methods or parameters were changed in response to the observed effect. Failure corrections are code/verification fixes, not outcome-driven design changes.
- Final release verification: 26 tests passed; `python src/run_phase1.py` exited 0; the rebuilt notebook executed from a clean `nussem1` kernel with zero error outputs. `file` identified the generated PDF as PDF 1.4 with 10 pages; signature and EOF checks passed. `pdfinfo`/`pdftotext` were unavailable, so text extraction/visual review was not claimed.
- Reproducibility refinement: per-condition and per-series RNG seeds were added to machine-readable simulation outputs; seeds derive deterministically from root 20261012 as specified in the runner and protocol.
- First Phase 0.5 test run: 12 passed, 1 failed because the synthetic missing-hour fixture removed the earliest timestamp, outside the audit's source-span missingness denominator. Moved the synthetic omission to an interior date; the final rerun passed all 13 tests.

## 2026-10-12 — Phase 2 final quality assurance

- Reviewed the Phase 1 implementation and existing deliverables at commit `c45a0f3d8a6c8f0ec48257adb7ac04406d2533be` before Phase 2 edits.
- Added six frozen-protocol/result consistency tests. The full suite in `nussem1` passed: 32 tests, 0 failures. Checks include YAML grid values against saved simulation summaries, replicate counts, source/seed manifest, observed sample mean, and an independent SciPy recalculation of the IID t interval and p-value.
- Notebook execution attempt in the restricted sandbox failed before kernel startup because Jupyter could not bind a local port (`PermissionError: [Errno 1] Operation not permitted`). The same clean-kernel command then completed with explicit approval: exit 0, 11 of 11 code cells executed, no error outputs. Execution counts and notebook SHA-256 are preserved in `results/qa/notebook_execution.json`.
- Notebook execution regenerated all tracked numerical data and figures with no numerical diffs from the prior committed outputs. It regenerated the PDF as well; the PDF bytes changed, but all ten page renders were pixel-identical to the pre-run PDF at the recorded 110 dpi render settings.
- Ghostscript extracted PDF text and rendered all 10 pages. Each page was visually reviewed; readability, clipping, overlaps, symbols, labels/units, ordering, page integrity and displayed result consistency were checked. No formatting correction was needed. This was automated/AI-assisted inspection, not independent human verification.
- `docs/course_summary.md` contains 244 whitespace-delimited words. No package was installed. No research definition, simulation parameter, statistical method, or scientific conclusion was changed.
- Phase 2 portability cleanup generalized the machine-specific interpreter path in historical Phase 0 audit evidence while retaining its environment/version record. README reproduction and repository-map guidance were completed. The runner's remaining source-fixed parameter duplication is disclosed and checked against saved artifacts; no numerical-code refactor was made.
- A final source review found that rerunning the Phase 0 audit writer would reintroduce its absolute `sys.executable` value. The writer now emits the same portable environment description as the preserved audit record; an additional regression test covers this. Final suite rerun: 33 tests passed, 0 failed.
- Final interpretation clarification: the methods note, Phase 1 results, and notebook now state that a confidence interval is not a posterior probability statement and that inclusion of zero does not establish a zero contrast. This changes explanatory text only. Rebuilt and clean-kernel executed the final notebook again: exit 0, 11 code cells executed, zero errors; the 33-test suite passed again.
- One initial local-path/credential scan helper failed while parsing a nested rich-text notebook output (`TypeError`); no repository files were changed by that failed scan. The helper was corrected to scan notebook source and text outputs while excluding encoded image payloads; the completed scan found no credential-pattern or machine-specific path matches.
- No external submission or final Git tag was created. Independent student/reviewer verification remains outstanding.
