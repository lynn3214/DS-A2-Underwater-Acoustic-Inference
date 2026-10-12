# DS-A2 — Inference and Uncertainty Notebook

This repository contains the NOAA SanctSound SB02_13 feasibility audit and Phase 1 analysis.

## Status

Phase 0.5 remains historically **CONDITIONAL PASS**: timestamp semantics and coverage are resolved, while the 10 Hz versus 20 Hz metadata discrepancy and missing row-level QC remain limitations. Phase 1 results are documented in [`docs/phase1_results.md`](docs/phase1_results.md); its design was frozen before calculating paired outcomes in [`config/experiment_protocol.yaml`](config/experiment_protocol.yaml). The contrast is observational and scoped to one deployment. Independent human review is pending, and no platform submission has been made.

## Reproduce

Use the existing Conda environment `nussem1`:

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate nussem1
python -c "import sys; print(sys.executable)"
python -m unittest discover -s tests -v
python src/run_phase1.py
python src/build_notebook.py
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebook/DS_A2_inference_uncertainty.ipynb
```

No dependencies were installed. The analysis validates the official source CSV SHA-256 against the frozen protocol before computing results. Environment versions and random seed root are recorded in `results/raw/phase1_run_manifest.json`. Original NOAA files are preserved under `data/raw/`; daily aggregates and numerical results are under `data/processed/` and `results/raw/`.

## Key artifacts

- Executable notebook: [`notebook/DS_A2_inference_uncertainty.ipynb`](notebook/DS_A2_inference_uncertainty.ipynb)
- PDF report: [`results/DS_A2_phase1_report.pdf`](results/DS_A2_phase1_report.pdf)
- Frozen analysis plan: [`docs/analysis_plan.md`](docs/analysis_plan.md)
- Statistical method notes: [`docs/method_notes.md`](docs/method_notes.md)
- Verified results and reproduction record: [`docs/phase1_results.md`](docs/phase1_results.md)
- English course-summary draft: [`docs/course_summary.md`](docs/course_summary.md)
- NOAA provenance: [`results/audit/provenance.json`](results/audit/provenance.json)
- AI-use and verification record: [`docs/ai_use_log.md`](docs/ai_use_log.md)
