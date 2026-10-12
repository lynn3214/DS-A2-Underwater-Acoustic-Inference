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

Use the existing Conda environment `nussem1`; Python 3.10.18 was used for the recorded run. The repository does not include an environment lock file. The verified environment includes NumPy 2.2.6, SciPy 1.15.2, pandas 2.3.1, Matplotlib 3.10.5, PyYAML 6.0.2, Jupyter 1.1.1, and nbconvert 7.16.6. Tests also use the standard library and installed pandas/SciPy packages. No packages were installed for this project. Do not install or upgrade packages without reviewing the environment and obtaining authorization.

From the repository root, activate and verify the environment:

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate nussem1
which python
python -c "import sys; print(sys.executable); print(sys.version)"
```

## Reproduction

Run the tests, regenerate derived results/figures/PDF, rebuild the notebook, then execute it in a fresh Jupyter kernel:

```bash
python -m unittest discover -s tests -v
python src/run_phase1.py
python src/build_notebook.py
jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=1200 \
  notebook/DS_A2_inference_uncertainty.ipynb \
  --output /tmp/DS_A2_inference_uncertainty_executed.ipynb
```

`run_phase1.py` verifies the source SHA-256 against the frozen protocol before analysis. It writes `data/processed/`, `results/raw/`, `results/figures/`, and the PDF. The notebook's pipeline cell also calls the same runner. The PDF uses Matplotlib's PDF backend; Ghostscript can be used for text extraction and page rendering when available.

## Design and interpretation limits

The frozen windows are local `[09:00,17:00)` and `[21:00,05:00)` with the night assigned to its starting date. A date requires at least six valid hours in each window; 8/8 is reported as a coverage sensitivity. Hourly values are published dB indicators and are averaged arithmetically on the dB scale. See `config/experiment_protocol.yaml` and `docs/analysis_plan.md` for the estimand and methods.

The sample contains 64 eligible dates from one short deployment. Missing row-level QC, the unresolved frequency-edge discrepancy, temporal dependence, and possible nonstationarity limit inference. The 3 dB threshold is an operational interpretation threshold, not a universal ecological standard. Controlled simulation results apply only to their stated models; neither simulations nor observational intervals support causation. Phase 0.5's historical feasibility status remains CONDITIONAL PASS. Independent human review is pending; no course-platform submission or final tag has been made.

## Key documents

- Frozen analysis: `config/experiment_protocol.yaml`, `docs/analysis_plan.md`.
- Source/YAML parameter mapping and output consistency scope: `docs/phase1_parameter_mapping.md`.
- Phase 0/0.5 audit: `docs/audit_report.md`, `docs/metadata_resolution.md`.
- Methods and observed/simulation results: `docs/method_notes.md`, `docs/phase1_results.md`.
- Human-review summary draft: `docs/course_summary.md` (not submitted).
- Reproducibility QA: `docs/final_qa_report.md` (added during Phase 2).
- AI-use and execution history: `docs/ai_use_log.md`, `docs/experiment_log.md`.
