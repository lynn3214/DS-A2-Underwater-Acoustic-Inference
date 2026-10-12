# Phase 1 Results and Verification

## Scope and provenance

Analysis followed the protocol frozen before observed paired differences were calculated: commit `33261148bbcfb2a4f6e9ff27286c5f962e323138`. The NOAA CSV SHA-256 was verified against the protocol and provenance manifest: `678ccabf720dfb1880b2d5975dee417dda118c66929f0e8d000dc9043c4d1cb2`. Exact-product reuse terms and acquisition provenance remain documented in the Phase 0.5 record. No raw audio is included.

The primary analysis includes 64 eligible dates, 2020-11-23 through 2021-01-25, in one contiguous run. All 64 also satisfy strict 8/8 coverage. Daily rows, including window counts, means, differences, and both eligibility flags, are in `data/processed/daily_analysis.csv`. No interpolation or undocumented value filtering was applied.

## Observed NOAA contrast

The statistic is the arithmetic mean of each date's night-minus-day means of published hourly dB indicators. The observed estimate is **+0.352 dB**, median +0.635 dB, sample SD 3.123 dB, and standard error 0.390 dB (n=64).

| Method | 95% interval (dB) | Two-sided p | Rule |
|---|---:|---:|---|
| IID one-sample t | [−0.428, 1.132] | 0.370 | t test, df=63 |
| Newey–West HAC | [−0.564, 1.268] | 0.445 | Bartlett, lag 3, finite-sample factor 64/63, t reference df=63 |
| MBB, block 2 | [−0.500, 1.137] | Not calculated | 1,999 moving-block replicates, percentile interval |
| MBB, block 4 | [−0.542, 1.228] | Not calculated | Primary `ceil(64^(1/3))` heuristic |
| MBB, block 8 | [−0.431, 1.246] | Not calculated | Block-length sensitivity |

All intervals include zero and 1 dB, and all exclude +3 dB. The parametric p-values do not show a statistically significant average contrast at alpha=.05. The estimate is below both operational thresholds. An interval containing zero does not establish that the true contrast is zero; the interval remains compatible with positive and negative values. A 95% confidence interval describes long-run coverage under its method assumptions, not a 95% probability statement about the fixed contrast. These statements are conditional on the metric, inclusion rule, and inference assumptions; the contrast is not causal. The thresholds are not universal NOAA or ecological standards.

## Real-data temporal dependence

Daily ACF values are lag 1 = 0.138, lag 2 = 0.110, lag 3 = 0.121, lag 7 = 0.003, and lag 14 = −0.034. All lie within the approximate ±0.245 white-noise reference band for n=64. These estimates are uncertain and the reference band is not a universal set of coefficient-wise confidence intervals. Lack of large ACF spikes does not establish independence or stationarity.

## Controlled sampling and power simulations

The observed sample SD `sigma0=3.123 dB` was used only as a marginal calibration. Across 5,000 IID Gaussian replications per scenario, at n=30 and effect=3 dB, analytical noncentral-t power was 0.9991 and Monte Carlo rejection was 0.9990 (Wilson 95% interval 0.9977–0.9996). With noise `2*sigma0`, n=30 and effect=3 dB, analytical power was 0.7200 and rejection was 0.7134 (0.7007–0.7258). At zero effect for n=30, Type I error was 0.0514 (0.0456–0.0579), consistent with .05. Larger n increased simulated power and larger noise reduced it. These high 3 dB power figures are specific to the IID Gaussian simulation and are not transferable to dependent observations.

Sampling-distribution results for n=20, 30, 64 and effects 0/3 dB are in `results/raw/sampling_distribution_summary.csv`; all 30,000 simulated means are in `results/raw/sampling_distribution_draws.csv`. Every point on the plotted power curves and its analytical counterpart is in `results/raw/iid_power.csv`.

## AR(1) counterexample

Stationary-generator checks used 30,000 length-100 sequences per rho. Empirical marginal means were between −0.0064 and +0.0014; pooled variances were within 0.07% of their theoretical value. Mean per-series lag-one correlation ranged from −0.011 at rho=0 to 0.860 at rho=.9; finite-length demeaning produces a downward bias.

At n=64, with 2,000 series per rho/effect condition, true Delta=0 and rho=.6, null rejection and coverage were:

| Method | Type I error (Wilson 95% CI) | Coverage (Wilson 95% CI) | Mean interval width (dB) |
|---|---:|---:|---:|
| IID t | 0.3265 (0.3063–0.3474) | 0.6735 (0.6526–0.6937) | 1.507 |
| HAC | 0.1555 (0.1403–0.1720) | 0.8445 (0.8280–0.8597) | 2.231 |
| MBB, block 4 | 0.1745 (0.1585–0.1918) | 0.8255 (0.8082–0.8415) | 2.166 |

HAC and MBB reduced IID size distortion but neither reached nominal calibration in this design. At rho=.9, Type I errors were 0.679, 0.471, and 0.491; coverage was 0.321, 0.529, and 0.509. The dependence-aware procedures did not solve the severe-dependence case. With true effect 3 dB and rho=.6, rejection rates were 0.9975 (IID), 0.9920 (HAC), and 0.9925 (MBB), but 95% interval coverage of the nonzero truth was only 0.681, 0.857, and 0.834. Full rates, Monte Carlo intervals, all rho/effect settings, and widths are in `results/raw/ar1_counterexample_summary.csv`; replicate records are in `results/raw/ar1_counterexample_replicates.csv`.

## Limitations and decision

Phase 0.5 remains historically **CONDITIONAL PASS**. Direct netCDF/NCEI evidence favors 10–24,000 Hz, while the exact product brief JSON reports 20–24,000 Hz; this discrepancy remains unresolved. There are no row-level QC flags or quantitative exclusions. The record covers one short deployment at one station. HAC and MBB were imperfect under controlled dependence, and a modest observed ACF cannot prove IID behavior. Arithmetic averaging of the published dB indicator is distinct from energy averaging. No causal or beyond-deployment generalization is warranted.

## Execution evidence

- Environment: Python interpreter from the active `nussem1` Conda environment, Python 3.10.18, Conda 25.9.1, macOS 15.5 arm64; NumPy 2.2.6, SciPy 1.15.2, pandas 2.3.1, matplotlib 3.10.5, PyYAML 6.0.2, Jupyter 1.1.1, nbconvert 7.16.6. No dependencies were installed.
- Tests: `python -m unittest discover -s tests -v` — final suite 26 passed.
- Pipeline: `python src/run_phase1.py` — completed, exit 0; it generated data, tables, figures and the PDF after the analytical-tail correction.
- Notebook: `jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebook/DS_A2_inference_uncertainty.ipynb` — clean-kernel execution succeeded and saved outputs. Permission to bind local kernel sockets was required. Final executed notebook contains no error outputs.
- PDF: generated by Matplotlib as a 10-page PDF. `pdfinfo` and `pdftotext` are not installed; a structural check uses the PDF header/EOF and page markers.
- Failures and corrections are retained in `docs/experiment_log.md`. Automated verification is not independent human review.

## Independent reproduction

From repository root, activate the existing environment with the exact commands below, then run `python -m unittest discover -s tests -v`, `python src/run_phase1.py`, `python src/build_notebook.py`, and the `jupyter nbconvert` command listed above. Full grids, seeds, and method definitions are frozen in `config/experiment_protocol.yaml`. Review `docs/ai_use_log.md` and `docs/decision_log.md` before changing methods.

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate nussem1
python -c "import sys; print(sys.executable); print(sys.version)"
```
