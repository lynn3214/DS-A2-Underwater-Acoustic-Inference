"""Reproducible Phase 1 data preparation and statistical procedures."""

from __future__ import annotations

import csv
import math
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy import stats
from scipy.integrate import quad

from time_windows import window_hours


def read_source(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame.columns = [str(column).strip() for column in frame.columns]
    if list(frame.columns) != ["yyyy-mm-ddTHH:MM:SSZ", "BB_10-24000"]:
        raise ValueError(f"Unexpected source schema: {list(frame.columns)!r}")
    frame = frame.rename(columns={"yyyy-mm-ddTHH:MM:SSZ": "timestamp_utc", "BB_10-24000": "spl_db"})
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    frame["spl_db"] = pd.to_numeric(frame["spl_db"], errors="coerce")
    return frame.sort_values("timestamp_utc", kind="stable").reset_index(drop=True)


def aggregate_daily(frame: pd.DataFrame, timezone_name: str = "America/New_York",
                    min_hours: int = 6) -> pd.DataFrame:
    """Aggregate published dB indicators to date-level day/night summaries."""
    if frame["timestamp_utc"].duplicated().any():
        raise ValueError("Duplicate source timestamp labels are not eligible for aggregation")
    zone = ZoneInfo(timezone_name)
    data = frame.copy()
    data["local_start"] = data["timestamp_utc"].dt.tz_convert(zone)
    data["local_date"] = data["local_start"].dt.date
    data["local_hour"] = data["local_start"].dt.hour
    data["local_fold"] = data["local_start"].map(lambda value: value.to_pydatetime().fold)
    data["valid"] = np.isfinite(data["spl_db"])
    all_dates = sorted(data["local_date"].unique())
    output = []
    for day in all_dates:
        day_hours = set(range(9, 17))
        day_mask = (data["local_date"] == day) & data["local_hour"].isin(day_hours)
        night_date = day + timedelta(days=1)
        night_mask = (((data["local_date"] == day) & data["local_hour"].between(21, 23)) |
                      ((data["local_date"] == night_date) & data["local_hour"].between(0, 4)))
        day_values = data.loc[day_mask & data["valid"], "spl_db"]
        night_values = data.loc[night_mask & data["valid"], "spl_db"]
        day_n, night_n = len(day_values), len(night_values)
        eligible = day_n >= min_hours and night_n >= min_hours
        full = day_n == 8 and night_n == 8
        output.append({
            "local_date": day.isoformat(),
            "day_valid_hours": day_n,
            "night_valid_hours": night_n,
            "day_mean_db": float(day_values.mean()) if day_n else np.nan,
            "night_mean_db": float(night_values.mean()) if night_n else np.nan,
            "daily_difference_db": (float(night_values.mean() - day_values.mean()) if eligible else np.nan),
            "eligible_6_of_8": bool(eligible),
            "eligible_8_of_8": bool(full),
        })
    return pd.DataFrame(output)


def t_inference(values: np.ndarray, alpha: float = 0.05) -> dict:
    x = np.asarray(values, dtype=float)
    n = len(x)
    mean = float(np.mean(x))
    sd = float(np.std(x, ddof=1))
    se = sd / math.sqrt(n)
    critical = stats.t.ppf(1 - alpha / 2, n - 1)
    statistic = mean / se
    return {"n": n, "mean": mean, "sd": sd, "se": se,
            "lower": mean - critical * se, "upper": mean + critical * se,
            "statistic": statistic, "p_value": float(2 * stats.t.sf(abs(statistic), n - 1)),
            "df": n - 1}


def hac_inference(values: np.ndarray, alpha: float = 0.05, max_lag: int | None = None) -> dict:
    """Intercept-only Newey-West variance, Bartlett weights and n/(n-1) correction."""
    x = np.asarray(values, dtype=float)
    n = len(x)
    if max_lag is None:
        max_lag = math.floor(4 * (n / 100) ** (2 / 9))
    lag = min(max_lag, n - 1)
    residual = x - np.mean(x)
    long_run = float(np.dot(residual, residual) / n)
    for k in range(1, lag + 1):
        gamma = float(np.dot(residual[k:], residual[:-k]) / n)
        weight = 1 - k / (lag + 1)
        long_run += 2 * weight * gamma
    variance_mean = max(0.0, long_run / n * n / (n - 1))
    se = math.sqrt(variance_mean)
    mean = float(np.mean(x))
    df = n - 1
    critical = stats.t.ppf(1 - alpha / 2, df)
    statistic = mean / se if se else math.copysign(math.inf, mean)
    return {"n": n, "mean": mean, "se": se, "lower": mean - critical * se,
            "upper": mean + critical * se, "statistic": statistic,
            "p_value": float(2 * stats.t.sf(abs(statistic), df)), "df": df,
            "max_lag": lag, "kernel": "Bartlett", "finite_sample_factor": n / (n - 1)}


def moving_block_bootstrap(values: np.ndarray, block_length: int, replications: int = 1999,
                           seed: int = 0, chunk_size: int = 128) -> dict:
    """Non-circular overlapping-block bootstrap; percentile interval for sample mean."""
    x = np.asarray(values, dtype=float)
    n = len(x)
    if not 1 <= block_length <= n:
        raise ValueError("block_length must be between 1 and sample size")
    rng = np.random.default_rng(seed)
    starts = np.arange(n - block_length + 1)
    blocks_per_sample = math.ceil(n / block_length)
    means = np.empty(replications, dtype=float)
    for lo in range(0, replications, chunk_size):
        count = min(chunk_size, replications - lo)
        chosen = rng.choice(starts, size=(count, blocks_per_sample), replace=True)
        offsets = np.arange(block_length)
        indices = (chosen[:, :, None] + offsets).reshape(count, -1)[:, :n]
        means[lo:lo + count] = x[indices].mean(axis=1)
    low, high = np.quantile(means, [alpha := 0.025, 1 - alpha])
    return {"mean": float(x.mean()), "lower": float(low), "upper": float(high),
            "block_length": block_length, "replications": replications,
            "bootstrap_means": means}


def wilson_interval(successes: int, trials: int, alpha: float = 0.05) -> tuple[float, float]:
    z = stats.norm.ppf(1 - alpha / 2)
    p = successes / trials
    den = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / den
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials**2)) / den
    return center - half, center + half


def iid_analytical_power(n: int, sigma: float, effect: float, alpha: float = 0.05) -> float:
    df = n - 1
    critical = stats.t.ppf(1 - alpha / 2, df)
    ncp = effect * math.sqrt(n) / sigma
    lower = stats.nct.cdf(-critical, df, ncp)
    upper = stats.nct.sf(critical, df, ncp)
    if np.isfinite(lower) and np.isfinite(upper):
        return float(lower + upper)
    # Stable exact noncentral-t tail integration when SciPy's direct CDF underflows.
    def integrand(value: float) -> float:
        root = critical * math.sqrt(value / df)
        tails = stats.norm.sf(root - ncp) + stats.norm.cdf(-root - ncp)
        return tails * stats.chi2.pdf(value, df)
    probability, _ = quad(integrand, 0, np.inf, epsabs=1e-11, epsrel=1e-10, limit=200)
    return float(probability)


def simulate_iid_condition(n: int, effect: float, sigma: float, replications: int,
                           seed: int, alpha: float = 0.05, batch: int = 5000) -> dict:
    rng = np.random.default_rng(seed)
    means, sds = [], []
    rejected = 0
    done = 0
    critical = stats.t.ppf(1 - alpha / 2, n - 1)
    while done < replications:
        size = min(batch, replications - done)
        sample = rng.normal(effect, sigma, size=(size, n))
        mean = sample.mean(axis=1)
        sd = sample.std(axis=1, ddof=1)
        tstat = mean / (sd / math.sqrt(n))
        rejected += int(np.count_nonzero(np.abs(tstat) > critical))
        means.append(mean)
        sds.append(sd)
        done += size
    all_means, all_sds = np.concatenate(means), np.concatenate(sds)
    low, high = wilson_interval(rejected, replications, alpha)
    return {"n": n, "effect_db": effect, "sigma_db": sigma, "replications": replications,
            "empirical_mean": float(all_means.mean()), "theoretical_mean": effect,
            "empirical_se": float(all_means.std(ddof=1)), "theoretical_se": sigma / math.sqrt(n),
            "estimated_bias": float(all_means.mean() - effect), "empirical_sd_mean": float(all_sds.mean()),
            "mc_se_empirical_mean": float(all_means.std(ddof=1) / math.sqrt(replications)),
            "mc_se_empirical_sampling_sd": float(all_means.std(ddof=1) / math.sqrt(2 * (replications - 1))),
            "rejections": rejected, "rejection_rate": rejected / replications,
            "rejection_ci_low": low, "rejection_ci_high": high}


def generate_ar1(n: int, effect: float, sigma: float, rho: float, replications: int,
                 rng: np.random.Generator) -> np.ndarray:
    innovations = rng.normal(0, sigma * math.sqrt(1 - rho**2), size=(replications, n))
    values = np.empty_like(innovations)
    values[:, 0] = rng.normal(0, sigma, size=replications)
    for t in range(1, n):
        values[:, t] = rho * values[:, t - 1] + innovations[:, t]
    return values + effect


def ar1_empirical_properties(rho: float, sigma: float, seed: int = 1,
                             replications: int = 30000, n: int = 100) -> dict:
    series = generate_ar1(n, 0.0, sigma, rho, replications, np.random.default_rng(seed))
    centered = series - series.mean(axis=1, keepdims=True)
    lag1 = np.sum(centered[:, 1:] * centered[:, :-1], axis=1) / np.sqrt(
        np.sum(centered[:, 1:]**2, axis=1) * np.sum(centered[:, :-1]**2, axis=1))
    return {"rho": rho, "theoretical_mean": 0.0, "empirical_mean": float(series.mean()),
            "theoretical_variance": sigma**2, "empirical_variance": float(series.var()),
            "theoretical_lag1": rho, "empirical_lag1_mean": float(lag1.mean()),
            "replications": replications, "series_length": n, "seed": seed}


def ar1_method_comparison(n: int, effect: float, sigma: float, rho: float,
                          replications: int, bootstrap_replications: int,
                          seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    samples = generate_ar1(n, effect, sigma, rho, replications, rng)
    records = []
    block_length = math.ceil(n ** (1 / 3))
    for index, values in enumerate(samples):
        iid = t_inference(values)
        hac = hac_inference(values)
        mbb = moving_block_bootstrap(values, block_length, bootstrap_replications,
                                     seed=seed + index + 1, chunk_size=128)
        for name, result in (("iid_t", iid), ("hac", hac), ("moving_block_bootstrap", mbb)):
            records.append({"rho": rho, "effect_db": effect, "series_id": index,
                            "series_seed": seed, "bootstrap_seed": seed + index + 1,
                            "method": name, "estimate": float(np.mean(values)),
                            "lower": result["lower"], "upper": result["upper"],
                            "covered": result["lower"] <= effect <= result["upper"],
                            "reject_zero": result["lower"] > 0 or result["upper"] < 0,
                            "interval_width": result["upper"] - result["lower"]})
    return records


def sample_acf(values: np.ndarray, lags: list[int]) -> dict[int, float]:
    x = np.asarray(values, dtype=float)
    x = x - x.mean()
    denominator = float(np.dot(x, x))
    return {lag: float(np.dot(x[lag:], x[:-lag]) / denominator) for lag in lags}
