# Phase 2 Final Quality Assurance Report

## Decision

**Recommendation: CONDITIONAL PASS for independent review.** The Phase 1 deliverables passed the automated verification performed here, and the clean-kernel notebook run succeeded. The frozen protocol, analysis methods, parameter values, and scientific conclusions were not changed. Conditional items are scientific/metadata limitations already disclosed in the project and the still-pending independent human review; this report does not represent that review as complete.

The exact reviewed base commit was `c45a0f3d8a6c8f0ec48257adb7ac04406d2533be`. Phase 2 changes are subsequent, additive commits; prior commits were not rewritten.

## Materials reviewed

Read before changes: `AGENTS.md`, `CODEX_AUDIT_PROMPT.md`, `config/experiment_protocol.yaml`, all three audit protocol YAML files, `docs/analysis_plan.md`, `docs/audit_report.md`, `docs/metadata_resolution.md`, `docs/phase1_results.md`, `docs/method_notes.md`, `docs/experiment_log.md`, `docs/decision_log.md`, `docs/ai_use_log.md`, `docs/course_summary.md`, `README.md`, all Python modules under `src/`, and all tests under `tests/`.

The review also parsed the frozen protocols, provenance and audit JSON, Phase 1 JSON/CSV results, and notebook structure and outputs. The notebook's full markdown/code content was reviewed and then executed in a fresh kernel. The report PDF and all nine embedded diagnostic figures were checked on each of its ten rendered pages. Source CSV/NetCDF checksums remain pinned by the protocol and provenance records.

## Findings and actions

| Severity | Finding | Action and status |
|---|---|---|
| Medium, non-blocking | Several effective settings are duplicated as literals in `src/run_phase1.py` rather than loaded dynamically from YAML. | Left analysis code and frozen configuration unchanged. Added `docs/phase1_parameter_mapping.md` identifying YAML-controlled values, source-fixed values, and limits of future YAML edits; added automated checks that saved outputs match the frozen grids and counts. |
| Low | Historical Phase 0 report/JSON exposed an absolute local interpreter path, and the audit writer would reintroduce it on rerun. | Replaced the recorded path with a portable `nussem1` interpreter description and updated the writer. Python version, Conda version, package versions, and platform records remain. |
| Low | README did not fully explain repository layout and the full reproduction flow. | Expanded it with dataset/provenance, directories, dependencies, exact environment activation, tests, analysis/notebook execution, PDF/figure regeneration, artifact locations, and limitations. |
| None found | Output consistency, notebook execution errors, PDF layout faults, credentials, local paths, and oversized files. | Verification details follow. |

No method, estimand, inclusion rule, simulation condition, random seed, numerical conclusion, or historical commit was changed. No new statistical experiment was conducted. Re-running the pre-existing pipeline was part of the requested reproducibility check.

## Configuration and numerical consistency

The new `tests/test_protocol_consistency.py` compares saved result grids and replication counts with `config/experiment_protocol.yaml`, verifies the manifest's source checksum and seed root, checks the observed-data mean against the saved eligible daily rows, and independently recalculates the IID t interval and p-value with SciPy. It also covers the MBB settings and AR(1) replicate totals. The complete mapping and source-fixed values are listed in `docs/phase1_parameter_mapping.md`.

Verified consistency checks:

- Eligibility: 64 dates under 6/8 and 64 under 8/8, matching Phase 0.5; one uninterrupted eligible run.
- Observed estimate: mean night-minus-day `+0.352137 dB` (reported rounded to `+0.352 dB`), n=64.
- IID t: 95% CI `[-0.428004, 1.132278] dB`, p=`0.370490`.
- HAC: 95% CI `[-0.563540, 1.267814] dB`, p=`0.445066`.
- MBB percentile intervals: block 2 `[-0.499504, 1.136729]`, block 4 `[-0.541927, 1.227979]`, block 8 `[-0.431345, 1.245774] dB`.
- IID power at n=30/effect 3 dB: analytical `0.999097`, Monte Carlo `0.9990`; at twice the noise SD, Monte Carlo `0.7134`. Null rejection estimate: `0.0514`.
- AR(1), rho=.6 and true effect zero: IID t/HAC/MBB rejection rates `0.3265/0.1555/0.1745`; coverage `0.6735/0.8445/0.8255`.
- The 3 dB value remains a prespecified operational interpretation threshold, not an established ecological criterion. A CI including zero is not evidence that the true contrast is zero; the estimate and uncertainty remain scoped to this observational deployment.

The full numerical results remain in `results/raw/` and are summarized in `docs/phase1_results.md`. Re-execution produced no changed numerical data tables or figures relative to the reviewed commit. The PDF file was regenerated; although the file bytes changed, the ten rendered page images were pixel-identical to the prior version at 110 dpi.

## Automated verification

Environment: existing Conda environment `nussem1`; Python 3.10.18, Conda 25.9.1, NumPy 2.2.6, SciPy 1.15.2, pandas 2.3.1, Matplotlib 3.10.5, PyYAML 6.0.2, Jupyter 1.1.1, and nbconvert 7.16.6. No package was installed or upgraded.

Final test command, after activating the environment:

```bash
python -m unittest discover -s tests -v
```

**Result: 33 tests passed, 0 failed.** This includes the original synthetic parsing, timezone/DST, window eligibility, HAC/t/MBB, simulation, and AR(1) tests plus seven protocol/output consistency and path-portability checks.

The first clean-kernel command in the sandbox failed before starting a kernel because Jupyter could not bind a local temporary port (`PermissionError: [Errno 1] Operation not permitted`). The same command was rerun with the necessary approved local-kernel permission and exited 0:

```bash
jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=1200 \
  notebook/DS_A2_inference_uncertainty.ipynb \
  --output /tmp/DS_A2_inference_uncertainty_executed.ipynb
```

All 11 of 11 code cells executed; there were no error outputs. The fresh execution is saved in the delivered notebook, and exact execution counts, command, reviewed base commit, status, and notebook SHA-256 are in `results/qa/notebook_execution.json`. The failure and successful retry are preserved in `docs/experiment_log.md`.

Machine-readable validation parsed 9 JSON files, 3 YAML files, 8 CSV files, and the 27-cell notebook successfully. `git diff --check` passed. The course summary is 244 whitespace-delimited English words, within the required 150–300 range. The notebook contains 11 executed code cells and no error outputs.

## PDF inspection

Ghostscript extracted the PDF text and rendered **10 pages**. Each page was visually inspected from its rendered image. No clipped text, page overflow, missing/corrupt page, unreadable figure or legend, incorrect unit, or overlap was found. All page text and figures were checked against the saved results; the render-by-render comparison after regeneration was exact.

| Page | Contents | Review result |
|---|---|---|
| 1 | Research question, estimand, design, results, simulation and limitations | Text fits the page; equations/symbols and result statements are readable; no clipping. |
| 2 | Observed daily difference time series | Axes, date labels, dB units, and trace are legible; no clipping. |
| 3 | Observed difference distribution | Histogram and labels are legible; no overflow. |
| 4 | Observed daily ACF | Lags, axis, and reference-band legend are legible. |
| 5 | Estimate and interval comparison | Method labels, interval bars, zero line, and 1/3 dB thresholds are legible and correctly placed. |
| 6 | IID sampling distributions | All six panels, sample sizes, effects, axes, and density labels are legible. |
| 7 | IID power by effect | Analytical and Monte Carlo series, uncertainty bars, alpha reference, and legend are legible. |
| 8 | IID power by sample size | Series and sample-size labels are legible; legend is inside the plot area but does not obscure plotted data. |
| 9 | IID power by noise level | Series and noise multipliers are legible; legend does not obscure plotted data. |
| 10 | AR(1) rejection and coverage counterexample | Both panels, method labels, known-rho axis, and reference lines are legible. |

This was automated Ghostscript inspection plus AI-assisted visual review. **No independent human visual review is claimed.**

## Documentation and integrity checks

- `README.md` now describes the scientific objective, NOAA DOI, structure, environment/dependency assumptions, exact activation/reproduction commands, notebook execution, figure/PDF regeneration, result locations, and limitations.
- The 244-word English summary covers question, sample, methods, observed results, power, dependence counterexample, interpretation, and limitations. It was not submitted.
- AI-use and experiment logs record the Phase 2 role, decisions, failed sandbox attempt, successful execution, automated checks, and outstanding human review. No student or outside review is claimed.
- Scan of readable tracked/untracked text files and notebook cell source/text outputs found zero matches for common credential formats, credential assignments, personal home-directory paths, or machine-specific OS temporary paths. Encoded PNG notebook payloads were excluded from path scanning to avoid binary/base64 false matches. The `/tmp` locations in reproduction commands are intentional portable temporary-output targets. The original sanctioned NOAA source is present; raw audio is not. No tracked file exceeds 50 MiB. Largest tracked file is the 6.14 MB AR(1) replicate CSV; this is a documented machine-readable result, not a cache or raw audio artifact.
- The exact dataset license and provenance are recorded in Phase 0.5. The lower frequency-edge conflict (10 vs 20 Hz) and absence of per-record QC remain explicit; no inference was made about which metadata field NOAA intended.

## Remaining independent-review checklist

- Confirm the scientific question, operational 3 dB threshold, estimand scope, and use of arithmetic means on the published dB scale.
- Review whether IID, HAC bandwidth/reference, and MBB choices are appropriately limited and explained for this short series.
- Resolve with NOAA the 10 Hz versus 20 Hz lower frequency-edge discrepancy if possible; assess the lack of record-level QC information.
- Independently inspect the notebook, code, PDF, and reproduction steps; automated checks are not independent scientific validation.
- Approve the English course summary and decide whether/when to create the final Git tag and submit through the course platform.

No platform submission or final tag was created. Stop here for independent review.
