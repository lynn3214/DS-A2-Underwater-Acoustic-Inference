"""Execute the frozen Phase 1 analysis and write reproducible artifacts."""

from __future__ import annotations

import json
import math
import os
import platform
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".cache/matplotlib"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
import scipy
import yaml

from audit_noaa import sha256
from inference import (aggregate_daily, ar1_empirical_properties, ar1_method_comparison,
                       hac_inference, iid_analytical_power, moving_block_bootstrap,
                       read_source, sample_acf, simulate_iid_condition, t_inference,
                       wilson_interval)
from time_windows import contiguous_run_lengths

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "config/experiment_protocol.yaml"


def json_dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def run_all() -> dict:
    protocol = yaml.safe_load(PROTOCOL.read_text(encoding="utf-8"))
    raw_path = ROOT / protocol["data"]["input"]
    expected_hash = protocol["data"]["source_checksum_sha256"]
    actual_hash = sha256(raw_path)
    if actual_hash != expected_hash:
        raise RuntimeError(f"Source checksum mismatch: {actual_hash} != {expected_hash}")

    for folder in ("data/processed", "results/raw", "results/figures", "docs"):
        (ROOT / folder).mkdir(parents=True, exist_ok=True)

    hourly = read_source(raw_path)
    daily = aggregate_daily(hourly, protocol["data"]["analysis_timezone"], min_hours=6)
    audit = json.loads((ROOT / "results/audit/noaa_audit.json").read_text(encoding="utf-8"))
    audit_coverage = audit["coverage"]
    eligible = daily.loc[daily["eligible_6_of_8"]].copy().reset_index(drop=True)
    strict = daily.loc[daily["eligible_8_of_8"]]
    if len(eligible) != audit_coverage["eligible_date_count_6_of_8"]:
        raise RuntimeError("Primary eligibility count differs from Phase 0.5 audit")
    if len(strict) != audit_coverage["eligible_date_count_8_of_8"]:
        raise RuntimeError("Strict eligibility count differs from Phase 0.5 audit")
    dates = pd.to_datetime(eligible["local_date"])
    if not dates.diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise RuntimeError("Primary eligible sequence has a date gap; do not bridge it")
    daily_path = ROOT / "data/processed/daily_analysis.csv"
    daily.to_csv(daily_path, index=False, float_format="%.12g")
    differences = eligible["daily_difference_db"].to_numpy(float)
    n = len(differences)
    sigma0 = float(np.std(differences, ddof=1))
    descriptive = {
        "eligible_primary_dates": n, "eligible_strict_dates": len(strict),
        "eligible_date_range": [eligible.local_date.iloc[0], eligible.local_date.iloc[-1]],
        "contiguous_runs": contiguous_run_lengths([pd.Timestamp(day).date() for day in eligible.local_date]),
        "mean_difference_db": float(np.mean(differences)),
        "median_difference_db": float(np.median(differences)),
        "sample_sd_ddof1_db": sigma0,
        "standard_error_db": sigma0 / math.sqrt(n),
        "minimum_difference_db": float(np.min(differences)),
        "maximum_difference_db": float(np.max(differences)),
        "minimum_meaningful_threshold_db": 3.0,
        "secondary_interpretation_threshold_db": 1.0,
    }
    methods = []
    iid = t_inference(differences)
    methods.append({"method": "IID one-sample t", **iid})
    hac = hac_inference(differences)
    methods.append({"method": "Newey-West HAC", **hac})
    for block_length in (2, 4, 8):
        result = moving_block_bootstrap(differences, block_length, 1999,
                                        seed=20261012 + block_length)
        methods.append({"method": f"Moving block bootstrap L={block_length}",
                        "n": n, "mean": result["mean"], "lower": result["lower"],
                        "upper": result["upper"], "block_length": block_length,
                        "replications": result["replications"], "p_value": None,
                        "reject_zero_by_interval": result["lower"] > 0 or result["upper"] < 0})
    json_dump(ROOT / "results/raw/real_data_inference.json", {
        "source_sha256": actual_hash, "descriptive": descriptive, "methods": methods,
        "interpretation": "The MBB uses percentile intervals; no bootstrap p-value was calculated."})

    lags = [1, 2, 3, 7, 14]
    acf = sample_acf(differences, lags)
    acf_rows = [{"lag_days": lag, "acf": acf[lag], "n_pairs": n - lag,
                 "approx_white_noise_bound": 1.96 / math.sqrt(n)} for lag in lags]
    pd.DataFrame(acf_rows).to_csv(ROOT / "results/raw/daily_difference_acf.csv", index=False)

    seed_root = protocol["simulations"]["seed_root"]
    sampling_conditions = []
    sampling_values = []
    seed_id = 0
    for sample_n in (20, 30, 64):
        for effect in (0.0, 3.0):
            seed = seed_root + seed_id
            seed_id += 1
            row = simulate_iid_condition(sample_n, effect, sigma0, 5000, seed)
            row["seed"] = seed
            sampling_conditions.append(row)
            rng = np.random.default_rng(seed)
            draws = rng.normal(effect, sigma0, size=(5000, sample_n)).mean(axis=1)
            sampling_values.extend({"n": sample_n, "effect_db": effect, "replicate": i,
                                    "sample_mean_db": float(value)} for i, value in enumerate(draws))
    pd.DataFrame(sampling_conditions).to_csv(ROOT / "results/raw/sampling_distribution_summary.csv", index=False)
    pd.DataFrame(sampling_values).to_csv(ROOT / "results/raw/sampling_distribution_draws.csv", index=False)

    power_rows = []
    index = 0
    conditions = []
    conditions.extend((value, sigma0, 3.0, "sample_size", value) for value in (10, 20, 30, 40, 60))
    conditions.extend((30, sigma0 * multiplier, 3.0, "noise", multiplier) for multiplier in (.5, 1, 1.5, 2))
    conditions.extend((30, sigma0, effect, "effect", effect) for effect in (0, 1, 2, 3, 4, 5))
    for sample_n, sigma, effect, factor, x_value in conditions:
        seed = seed_root + 100 + index
        index += 1
        row = simulate_iid_condition(sample_n, effect, sigma, 5000, seed)
        low, high = row["rejection_ci_low"], row["rejection_ci_high"]
        power_rows.append({"factor": factor, "x": x_value, "n": sample_n,
                           "sigma_db": sigma, "effect_db": effect,
                           "analytical_power": iid_analytical_power(sample_n, sigma, effect),
                           "monte_carlo_rejection_rate": row["rejection_rate"],
                           "mc_ci_low": low, "mc_ci_high": high,
                           "replications": 5000, "seed": seed,
                           "interpretation": "empirical Type I error" if effect == 0 else "rejection rate"})
    pd.DataFrame(power_rows).to_csv(ROOT / "results/raw/iid_power.csv", index=False)

    ar_rows = []
    ar_properties = []
    ar_seed = seed_root + 1000
    replications = 2000
    bootstrap_reps = 999
    for rho_index, rho in enumerate((0.0, 0.3, 0.6, 0.9)):
        ar_properties.append(ar1_empirical_properties(rho, sigma0, ar_seed + rho_index))
        for effect_index, effect in enumerate((0.0, 3.0)):
            print(f"AR(1) comparison rho={rho}, effect={effect}", flush=True)
            ar_rows.extend(ar1_method_comparison(64, effect, sigma0, rho, replications,
                                                 bootstrap_reps,
                                                 ar_seed + 100 + 10 * rho_index + effect_index))
    ar_frame = pd.DataFrame(ar_rows)
    ar_frame.to_csv(ROOT / "results/raw/ar1_counterexample_replicates.csv", index=False)
    ar_summaries = []
    for keys, frame in ar_frame.groupby(["rho", "effect_db", "method"], sort=True):
        rho, effect, method = keys
        rejected = int(frame["reject_zero"].sum())
        rate = rejected / len(frame)
        ci_low, ci_high = wilson_interval(rejected, len(frame))
        covered = int(frame["covered"].sum())
        cover_low, cover_high = wilson_interval(covered, len(frame))
        ar_summaries.append({"rho": float(rho), "effect_db": float(effect), "method": method,
                             "replications": len(frame), "rejection_rate": rate,
                             "rejection_ci_low": ci_low, "rejection_ci_high": ci_high,
                             "coverage": covered / len(frame), "coverage_ci_low": cover_low,
                             "coverage_ci_high": cover_high,
                             "mean_interval_width_db": float(frame.interval_width.mean()),
                             "median_interval_width_db": float(frame.interval_width.median())})
    pd.DataFrame(ar_summaries).to_csv(ROOT / "results/raw/ar1_counterexample_summary.csv", index=False)
    json_dump(ROOT / "results/raw/ar1_stationarity_checks.json", ar_properties)

    write_figures(eligible, differences, descriptive, methods, acf_rows, sampling_conditions,
                  sampling_values, power_rows, ar_summaries)
    runtime = {
        "python": sys.version,
        "python_executable": "Python interpreter from the active nussem1 Conda environment",
        "conda": subprocess.run(["conda", "--version"], check=True, capture_output=True, text=True).stdout.strip(),
        "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__,
        "scipy": scipy.__version__, "matplotlib": matplotlib.__version__,
        "pyyaml": yaml.__version__, "jupyter": "1.1.1", "nbconvert": "7.16.6",
        "rng": "numpy.random.default_rng", "seed_root": seed_root,
    }
    json_dump(ROOT / "results/raw/phase1_run_manifest.json", {
        "source_sha256": actual_hash, "protocol": "config/experiment_protocol.yaml",
        "protocol_commit": "33261148bbcfb2a4f6e9ff27286c5f962e323138",
        "runtime": runtime,
        "artifacts": ["data/processed/daily_analysis.csv", "results/raw/real_data_inference.json",
                      "results/raw/daily_difference_acf.csv", "results/raw/sampling_distribution_summary.csv",
                      "results/raw/sampling_distribution_draws.csv", "results/raw/iid_power.csv",
                      "results/raw/ar1_counterexample_replicates.csv",
                      "results/raw/ar1_counterexample_summary.csv",
                      "results/raw/ar1_stationarity_checks.json", "results/figures/",
                      "results/DS_A2_phase1_report.pdf",
                      "notebook/DS_A2_inference_uncertainty.ipynb"],
    })
    return {"descriptive": descriptive, "methods": methods, "acf": acf_rows,
            "sampling": sampling_conditions, "power": power_rows,
            "ar1": ar_summaries, "runtime": runtime}


def write_figures(eligible, differences, descriptive, methods, acf_rows, sampling_summary,
                  sampling_values, power_rows, ar_summaries) -> None:
    out = ROOT / "results/figures"
    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(pd.to_datetime(eligible.local_date), differences, color="#176b87", linewidth=1.4)
    ax.axhline(0, color="black", linewidth=.8)
    ax.set(title="Observed NOAA daily paired differences", ylabel="Night minus day (dB)", xlabel="Local date")
    fig.tight_layout(); fig.savefig(out / "daily_difference_timeseries.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(differences, bins="auto", color="#319795", edgecolor="white")
    ax.axvline(0, color="black", linewidth=.8)
    ax.set(title="Observed NOAA daily paired-difference distribution", xlabel="Night minus day (dB)", ylabel="Dates")
    fig.tight_layout(); fig.savefig(out / "daily_difference_distribution.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([row["lag_days"] for row in acf_rows], [row["acf"] for row in acf_rows], color="#805ad5")
    ax.axhline(1.96 / math.sqrt(64), color="gray", linestyle="--", label="Approx. white-noise band")
    ax.axhline(-1.96 / math.sqrt(64), color="gray", linestyle="--")
    ax.set(title="Observed NOAA daily-difference sample ACF", xlabel="Lag (days)", ylabel="Autocorrelation")
    ax.legend(); fig.tight_layout(); fig.savefig(out / "daily_difference_acf.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    names = [item["method"] for item in methods]
    means = [item.get("mean", np.nan) for item in methods]
    lows = [item["lower"] for item in methods]; highs = [item["upper"] for item in methods]
    y = np.arange(len(names))
    ax.errorbar(means, y, xerr=[np.array(means)-lows, np.array(highs)-means], fmt="o", capsize=4)
    ax.axvline(0, color="black", linewidth=.8); ax.axvline(1, color="#d69e2e", linestyle=":", label="1 dB threshold")
    ax.axvline(3, color="#c53030", linestyle="--", label="3 dB threshold")
    ax.set_yticks(y, names); ax.set(title="Observed NOAA estimate and 95% intervals", xlabel="Night minus day (dB)")
    ax.legend(); fig.tight_layout(); fig.savefig(out / "inference_intervals.png", dpi=180); plt.close(fig)

    draw_frame = pd.DataFrame(sampling_values)
    fig, axes = plt.subplots(2, 3, figsize=(12, 7), sharex=False)
    for ax, item in zip(axes.flat, sampling_summary):
        vals = draw_frame[(draw_frame.n == item["n"]) & (draw_frame.effect_db == item["effect_db"])].sample_mean_db
        ax.hist(vals, bins=35, density=True, alpha=.7, color="#3182ce")
        ax.axvline(item["theoretical_mean"], color="#c53030", linestyle="--")
        ax.set(title=f"n={item['n']}, Δ={item['effect_db']:g} dB", xlabel="Simulated sample mean", ylabel="Density")
    fig.suptitle("IID Gaussian sampling distributions (simulation)"); fig.tight_layout()
    fig.savefig(out / "sampling_distributions.png", dpi=180); plt.close(fig)

    for factor, filename, xlabel, order in (
        ("sample_size", "power_vs_sample_size.png", "Sample size n", [10,20,30,40,60]),
        ("noise", "power_vs_noise.png", "Noise SD multiplier", [.5,1,1.5,2]),
        ("effect", "power_vs_effect.png", "True effect Δ (dB)", [0,1,2,3,4,5]),
    ):
        subset = sorted([row for row in power_rows if row["factor"] == factor], key=lambda row: row["x"])
        fig, ax = plt.subplots(figsize=(7, 4.5))
        xs = [row["x"] for row in subset]
        sim = np.array([row["monte_carlo_rejection_rate"] for row in subset])
        analytical = [row["analytical_power"] for row in subset]
        lower = np.array([row["mc_ci_low"] for row in subset]); upper = np.array([row["mc_ci_high"] for row in subset])
        ax.errorbar(xs, sim, yerr=[sim-lower, upper-sim], fmt="o-", capsize=3, label="Monte Carlo t-test")
        ax.plot(xs, analytical, "s--", label="Noncentral-t analytical")
        ax.axhline(.05, color="gray", linestyle=":", label="α = 0.05")
        ax.set(title=f"IID Gaussian power: varying {factor.replace('_',' ')}", xlabel=xlabel, ylabel="Rejection probability", ylim=(-.02,1.02))
        ax.legend(); fig.tight_layout(); fig.savefig(out / filename, dpi=180); plt.close(fig)

    summary = pd.DataFrame(ar_summaries)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    null = summary[summary.effect_db == 0]
    for method, group in null.groupby("method"):
        group = group.sort_values("rho")
        axes[0].plot(group.rho, group.rejection_rate, "o-", label=method)
        axes[1].plot(group.rho, group.coverage, "o-", label=method)
    axes[0].axhline(.05, color="black", linestyle=":")
    axes[1].axhline(.95, color="black", linestyle=":")
    axes[0].set(title="AR(1) null rejection rates", xlabel="Known simulated rho", ylabel="Type I error")
    axes[1].set(title="AR(1) null interval coverage", xlabel="Known simulated rho", ylabel="Coverage")
    axes[0].legend(fontsize=8); fig.suptitle("Controlled dependence counterexample (simulation)")
    fig.tight_layout(); fig.savefig(out / "counterexample_type1_coverage.png", dpi=180); plt.close(fig)

    with PdfPages(ROOT / "results/DS_A2_phase1_report.pdf") as pdf:
        iid_null = next(row for row in ar_summaries
                        if row["rho"] == 0.6 and row["effect_db"] == 0
                        and row["method"] == "iid_t")
        hac_null = next(row for row in ar_summaries
                        if row["rho"] == 0.6 and row["effect_db"] == 0
                        and row["method"] == "hac")
        mbb_null = next(row for row in ar_summaries
                        if row["rho"] == 0.6 and row["effect_db"] == 0
                        and row["method"] == "moving_block_bootstrap")
        baseline_power = next(row for row in power_rows
                              if row["factor"] == "sample_size" and row["n"] == 30)
        noisy_power = next(row for row in power_rows
                           if row["factor"] == "noise" and row["x"] == 2.0)
        iid_row = methods[0]
        fig, ax = plt.subplots(figsize=(8.27, 11.69)); ax.axis("off")
        text = (
            "DS-A2 Phase 1\nStatistical Inference and Uncertainty\n\n"
            "NOAA SanctSound SB02_13 | Observed deployment\n\n"
            "Research question\nIs the average clock-defined nighttime published hourly dB indicator different from the daytime indicator, and how uncertain is that difference? This is an observational contrast, not a causal effect.\n\n"
            "Estimand\nMean across eligible local dates of (night mean hourly dB − day mean hourly dB). Arithmetic means of dB indicators are not linear-energy means.\n\n"
            "Design\nAmerica/New_York; day 09:00–17:00; night 21:00–05:00 next date; >=6/8 valid hours in both windows. Two-sided alpha=.05. Operational interpretation thresholds: 1 and 3 dB.\n\n"
            f"Observed result\nn=64; mean difference={descriptive['mean_difference_db']:.3f} dB (median {descriptive['median_difference_db']:.3f}); IID t 95% CI [{iid_row['lower']:.3f}, {iid_row['upper']:.3f}] dB, p={iid_row['p_value']:.3f}. HAC and all MBB sensitivity intervals also include zero. The estimate and interval do not establish a day–night difference; the interval remains compatible with small positive and negative values.\n\n"
            f"IID power simulation\nAt n=30, sigma=sigma0={descriptive['sample_sd_ddof1_db']:.3f} dB, effect=3 dB, analytical power={baseline_power['analytical_power']:.3f} and Monte Carlo rejection={baseline_power['monte_carlo_rejection_rate']:.3f} (5,000 replications). At twice sigma0, rejection={noisy_power['monte_carlo_rejection_rate']:.3f}. These are conditional IID model results.\n\n"
            f"AR(1) counterexample\nAt rho=.6 and true effect 0, rejection/coverage were IID t {iid_null['rejection_rate']:.3f}/{iid_null['coverage']:.3f}, HAC {hac_null['rejection_rate']:.3f}/{hac_null['coverage']:.3f}, and MBB {mbb_null['rejection_rate']:.3f}/{mbb_null['coverage']:.3f} across 2,000 simulated series. HAC and MBB reduce, but do not eliminate, size distortion in this design.\n\n"
            "Methods\nIID one-sample t baseline; Newey–West Bartlett HAC with frozen bandwidth; overlapping non-circular moving block bootstrap. IID Gaussian sampling/power simulations use empirical marginal SD. Stationary Gaussian AR(1) simulations challenge independence.\n\n"
            "Limitations\n64 eligible dates from one short deployment; row-level QC flags absent; lower frequency edge conflicts between the brief JSON (20 Hz) and netCDF/NCEI (10 Hz). Dependence and nonstationarity remain important.\n\n"
            "Automated execution record\nSee the executable notebook, machine-readable results, environment manifest, tests, and AI-use log. No independent human verification is claimed."
        )
        ax.text(.08, .95, text, va="top", fontsize=12, linespacing=1.45, wrap=True)
        pdf.savefig(fig); plt.close(fig)
        for filename in ("daily_difference_timeseries.png", "daily_difference_distribution.png",
                         "daily_difference_acf.png", "inference_intervals.png",
                         "sampling_distributions.png", "power_vs_effect.png",
                         "power_vs_sample_size.png", "power_vs_noise.png",
                         "counterexample_type1_coverage.png"):
            image = plt.imread(out / filename)
            fig, ax = plt.subplots(figsize=(11.69, 8.27)); ax.imshow(image); ax.axis("off")
            fig.tight_layout(); pdf.savefig(fig); plt.close(fig)


if __name__ == "__main__":
    result = run_all()
    print(json.dumps({"descriptive": result["descriptive"], "methods": result["methods"],
                      "runtime": result["runtime"]}, indent=2))
