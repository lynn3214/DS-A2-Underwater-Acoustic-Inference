# DS-A2 — Inference and Uncertainty Notebook

This repository audits and analyzes NOAA SanctSound hourly broadband sound-level indicators for Stellwagen Bank station SB02_13. The Phase 1 question is whether the average night-minus-day indicator differs within eligible local dates during this one deployment, and how uncertain that contrast is. The analysis is observational and makes no causal claim.

## Dataset

The processed hourly product is NOAA SanctSound SB02_13_BB_1h ([DOI 10.25921/yyt5-g930](https://doi.org/10.25921/yyt5-g930)). Source links, retrieval details, license evidence, and checksums are in `results/audit/provenance.json`; metadata evidence and the historical feasibility decisions are in `results/audit/` and `docs/audit_report.md`. Exact-product metadata permit redistribution of the processed file. Raw acoustic audio is out of scope. A conflict remains between 10 Hz and 20 Hz lower band-edge metadata, and the source has no row-level QC flags.

## Repository map

- `config/`: frozen Phase 0 and Phase 1 protocols.
- `data/raw/`: original processed NOAA source and metadata snapshots; no raw audio.
- `data/processed/`: derived daily windows and eligibility records.
- `src/`: audit, time-window, statistical, pipeline, and notebook-builder code.
- `tests/`: synthetic unit tests and frozen-protocol/result consistency checks.
- `notebook/`: executable DS-A2 notebook.
- `results/audit/`: audit outputs, provenance, and metadata evidence.
- `results/raw/`: machine-readable Phase 1 results, simulation records, and run manifest.
- `results/figures/` and `results/DS_A2_phase1_report.pdf`: generated figures and report.
- `docs/`: design, methods, audit, results, decisions, execution history, AI-use log, and course summary.

## Environment and dependencies

Use the existing Conda environment `nussem1`; the recorded Phase 1 run used Python 3.10.18, NumPy 2.2.6, SciPy 1.15.2, pandas 2.3.1, Matplotlib 3.10.5, PyYAML 6.0.2, Jupyter 1.1.1, and nbconvert 7.16.6. The audit environment record also lists h5py 3.14.0. On 2026-10-14, the active environment reported nbformat 5.10.4, ipykernel 6.30.1, IPython 8.37.0, and tzdata 2025.2; those versions were not recorded as part of the original Phase 1 run. The repository does not include an environment lock file.

Direct tool requirements include PyYAML and h5py for NOAA metadata auditing, nbformat for rebuilding the Notebook, and Jupyter, nbconvert, and an ipykernel for clean-kernel execution. Python's standard-library `zoneinfo` uses the IANA time-zone database; Conda's `tzdata` package supplies that database where the operating system does not. The tests import the audit code and therefore also require its h5py dependency. No packages were installed for this project. Do not install or upgrade packages without reviewing the environment and obtaining authorization.

From the repository root, activate and verify the environment:

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate nussem1
which python
python -c "import sys; print(sys.executable); print(sys.version)"
```

## Reproduction

The following is a **deliverable-generation workflow**, not a read-only verification run. `python src/run_phase1.py` rewrites the processed daily table, raw result tables, figures, and PDF. `python src/build_notebook.py` overwrites the submitted Notebook. Executing the Notebook also runs its pipeline cell, which rewrites generated results and the PDF, even though the `nbconvert` command below saves the executed Notebook to `/tmp` rather than using `--inplace`. Use a disposable working copy if you need to preserve the committed deliverables while checking reproducibility.

From the repository root, the generation commands are:

```bash
python -m unittest discover -s tests -v
python src/run_phase1.py
python src/build_notebook.py
jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=1200 \
  notebook/DS_A2_inference_uncertainty.ipynb \
  --output /tmp/DS_A2_inference_uncertainty_executed.ipynb
```

`run_phase1.py` verifies the source SHA-256 against the frozen protocol before analysis. It writes `data/processed/`, `results/raw/`, `results/figures/`, and the PDF. The notebook's pipeline cell calls the same runner. The PDF uses Matplotlib's PDF backend; Ghostscript can be used for text extraction and page rendering when available.

## Design and interpretation limits

The frozen windows are local `[09:00,17:00)` and `[21:00,05:00)` with the night assigned to its starting date. A date requires at least six valid hours in each window; 8/8 is reported as a coverage sensitivity. Hourly values are published dB indicators and are averaged arithmetically on the dB scale. See `config/experiment_protocol.yaml` and `docs/analysis_plan.md` for the estimand and methods.

The sample contains 64 eligible dates from one short deployment. Missing row-level QC, the unresolved frequency-edge discrepancy, temporal dependence, and possible nonstationarity limit inference. The 3 dB threshold is an operational interpretation threshold, not a universal ecological standard. Controlled simulation results apply only to their stated models; neither simulations nor observational intervals support causation. Phase 0.5's historical feasibility status remains CONDITIONAL PASS. Independent scientific review and course-platform submission remain pending. The annotated Git tag `ds-a2-submission-v1` points to commit `7202de916f78aeb01b944ce2410c5b1a2e58693d`.

## Key documents

- Frozen analysis: `config/experiment_protocol.yaml`, `docs/analysis_plan.md`.
- Source/YAML parameter mapping and output consistency scope: `docs/phase1_parameter_mapping.md`.
- Phase 0/0.5 audit: `docs/audit_report.md`, `docs/metadata_resolution.md`.
- Methods and observed/simulation results: `docs/method_notes.md`, `docs/phase1_results.md`.
- Human-review summary draft: `docs/course_summary.md` (not submitted).
- Reproducibility QA: `docs/final_qa_report.md` (added during Phase 2).
- AI-use and execution history: `docs/ai_use_log.md`, `docs/experiment_log.md`.
