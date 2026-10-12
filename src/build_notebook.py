"""Create the documented, executable Phase 1 notebook source."""

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
notebook = nbf.v4.new_notebook()
notebook.metadata = {
    "kernelspec": {"display_name": "Python (nussem1)", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.10.18"},
}
cells = []


def markdown(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    cells.append(nbf.v4.new_code_cell(text))


markdown("""# DS-A2 — Statistical Inference and Uncertainty

**Day–Night Variability in Underwater Sound Levels: Statistical Inference, Power, and Temporal Dependence**

This notebook analyzes the NOAA SanctSound SB02_13 hourly broadband sound-level indicator. It separates observed data from controlled simulations and makes no causal claim about night, vessels, animals, or other sources. Run every cell from top to bottom in the existing `nussem1` environment. The frozen design is in `config/experiment_protocol.yaml`; implementation functions are in `src/inference.py` and orchestration is in `src/run_phase1.py`.
""")

markdown("""## 1. Research question and estimand

For eligible dates in this deployment, is the average nighttime underwater sound indicator different from the daytime indicator, and how uncertain is that difference? The sampling unit is a local calendar date.

For each date, `D_d = mean(night published hourly dB) − mean(day published hourly dB)`. The estimand is the expected `D_d` under the eligible observation process at this one station and deployment; the estimator is the mean of observed eligible differences. These arithmetic means of dB indicators are **not** means of linear acoustic energy. Generalization beyond this deployment needs additional assumptions.

The hypotheses are `H0: Delta = 0` versus two-sided `H1: Delta != 0`, alpha 0.05, with 95% intervals. The 3 dB primary and 1 dB secondary values are pre-specified operational interpretation thresholds, not universal acoustic/ecological standards and not null hypotheses. Statistical significance and practical importance are distinct.
""")

markdown("""## 2. Data provenance and measurement

The source is NOAA SanctSound SB02_13_BB_1h, DOI [10.25921/yyt5-g930](https://doi.org/10.25921/yyt5-g930), retrieved from the official NOAA public bucket. The original CSV checksum and provenance are recorded in `results/audit/provenance.json`; the protocol also pins its SHA-256. Direct netCDF attributes identify UTC labels as the start of each one-hour bin. `America/New_York` is used for local-clock windows. The data span November 2020 to January 2021 and do not contain a daylight-saving transition.

The primary band label is 10–24,000 Hz based on netCDF/NCEI/field-name evidence; the exact product's brief JSON says 20–24,000 Hz, which remains unresolved. The file has no row-level QC flag, so no undocumented filtering is applied. The exact product's netCDF license permits free redistribution with disclaimers; no raw audio is included.
""")

markdown("""## 3. Frozen analysis and execution

Day is local `[09:00, 17:00)` and night is `[21:00, 05:00)` on the next local date, assigned to the night start date. Include at least six valid hours in each eight-hour window; 8/8 is a coverage sensitivity. Missing values are not interpolated.

The IID baseline is a one-sample t procedure. HAC uses an intercept-only Newey–West estimate with Bartlett weights, `floor(4*(n/100)^(2/9))` lags, `n/(n−1)` correction and a t reference with `n−1` degrees of freedom. MBB samples overlapping non-circular blocks, concatenates then truncates to n, and uses bootstrap-mean percentile intervals. Its primary block length is `ceil(n^(1/3))`, with lengths 2, 4, 8 as sensitivity. The confidence-interval decision is used for MBB; no bootstrap p-value is manufactured.

The following run cell validates the pinned source hash, checks paired-date eligibility against the Phase 0.5 audit, and computes the frozen observed-data and simulation analyses. All pseudo-random draws use explicit `numpy.random.default_rng` seeds from root 20261012.
""")
code("""from pathlib import Path
import json, sys
ROOT = Path.cwd()
if ROOT.name == "notebook":
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
from run_phase1 import run_all
results = run_all()
print("Pipeline completed with pinned source data and frozen protocol.")
""")

markdown("## 4. Data preparation and eligibility")
code("""import pandas as pd
daily = pd.read_csv(ROOT / "data/processed/daily_analysis.csv")
eligible = daily.loc[daily.eligible_6_of_8].copy()
eligible_summary = {
    "all_dates_screened": len(daily),
    "eligible_6_of_8": int(daily.eligible_6_of_8.sum()),
    "eligible_8_of_8": int(daily.eligible_8_of_8.sum()),
    "first_eligible_date": eligible.local_date.iloc[0],
    "last_eligible_date": eligible.local_date.iloc[-1],
}
pd.Series(eligible_summary, name="value").to_frame()
""")

markdown("## 5. Observed-data inference")
markdown("The three families target the same mean paired difference but encode different dependence assumptions. HAC intervals at n=64 are approximate, not guaranteed calibrated; MBB sensitivity to block size is shown explicitly.")
code("""from IPython.display import display
display(pd.DataFrame([results["descriptive"]]).T.rename(columns={0: "observed value"}))
display(pd.DataFrame(results["methods"])[["method", "mean", "lower", "upper", "p_value"]])
""")
code("""from IPython.display import Image, display
display(Image(filename=str(ROOT / "results/figures/daily_difference_timeseries.png")))
display(Image(filename=str(ROOT / "results/figures/daily_difference_distribution.png")))
display(Image(filename=str(ROOT / "results/figures/inference_intervals.png")))
""")

markdown("## 6. Sampling-distribution simulation")
markdown("A controlled IID Gaussian model uses the observed daily-difference sample SD as a marginal scale calibration. This calibration does not assert that NOAA daily differences are IID Gaussian. For each n/effect condition, Monte Carlo means are compared with the theoretical mean and standard error.")
code("""sampling = pd.read_csv(ROOT / "results/raw/sampling_distribution_summary.csv")
sampling[["n", "effect_db", "sigma_db", "theoretical_mean", "empirical_mean",
          "theoretical_se", "empirical_se", "estimated_bias"]]
""")
code("""display(Image(filename=str(ROOT / "results/figures/sampling_distributions.png")))
""")

markdown("## 7. Statistical power")
markdown("The same two-sided t-test is used for every IID Monte Carlo scenario and for noncentral-t analytical power. At zero effect, the rejection rate estimates Type I error. Error bars show Wilson Monte Carlo intervals; analytical values apply only to the matching IID Gaussian model.")
code("""power = pd.read_csv(ROOT / "results/raw/iid_power.csv")
display(power)
""")
code("""for figure in ("power_vs_sample_size.png", "power_vs_noise.png", "power_vs_effect.png"):
    display(Image(filename=str(ROOT / "results/figures" / figure)))
""")

markdown("## 8. Temporal-dependence counterexample")
markdown("Stationary Gaussian AR(1) series use known simulation `rho` values 0, 0.3, 0.6 and 0.9, stationary initialization, n=64, and effects 0 and 3 dB. The rho values are controlled truth in simulation. They are not inferred from the NOAA sample ACF. Compare Type I error, coverage, interval width and rejection under the alternative without presuming any method always performs best.")
code("""counterexample = pd.read_csv(ROOT / "results/raw/ar1_counterexample_summary.csv")
display(counterexample)
display(pd.read_json(ROOT / "results/raw/ar1_stationarity_checks.json"))
""")
code("""display(Image(filename=str(ROOT / "results/figures/counterexample_type1_coverage.png")))
""")

markdown("## 9. Observed temporal dependence diagnostics")
markdown("The daily ACF is exploratory and estimated from only 64 dates. The displayed approximate white-noise bands are descriptive reference bands, not universal coefficient-wise confidence intervals. No eligible-date gaps are bridged.")
code("""acf = pd.read_csv(ROOT / "results/raw/daily_difference_acf.csv")
display(acf)
display(Image(filename=str(ROOT / "results/figures/daily_difference_acf.png")))
""")

markdown("""## 10. Interpretation, limitations, and reproducibility

The real-data estimate describes this one deployment and the chosen published hourly indicator. The dataset's lower band edge remains conflicted (10 vs 20 Hz), and row-level QC is unavailable. Missingness, temporal dependence, possible nonstationarity, the brief deployment, and arithmetic averaging on the dB scale limit interpretation. Neither a p-value nor power simulation supplies causal evidence. Controlled simulations validate behavior under their stated data-generating processes only.

Reproduce in `nussem1` with `python src/run_phase1.py`, then execute this notebook from a clean kernel with `jupyter nbconvert --to notebook --execute notebook/DS_A2_inference_uncertainty.ipynb --output /tmp/DS_A2_executed.ipynb`. Run tests with `python -m unittest discover -s tests -v`. The resulting PDF, code, raw numerical outputs, source checksums, tests, protocol and AI-use log are versioned. Codex's automated checks are not independent student or reviewer verification. No course platform submission was made.
""")

notebook.cells = cells
notebook.metadata["kernelspec"]["name"] = "python3"
output = ROOT / "notebook/DS_A2_inference_uncertainty.ipynb"
output.parent.mkdir(parents=True, exist_ok=True)
nbf.write(notebook, output)
print(f"Wrote {output.relative_to(ROOT)}")
