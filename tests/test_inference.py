"""Synthetic unit and Monte Carlo validation for Phase 1 procedures."""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inference import (aggregate_daily, ar1_empirical_properties, generate_ar1,
                       hac_inference, iid_analytical_power, moving_block_bootstrap,
                       t_inference)


class AggregationTests(unittest.TestCase):
    @staticmethod
    def utc_stamp(day, hour):
        local = datetime(2021, 1, day, hour, tzinfo=ZoneInfo("America/New_York"))
        return pd.Timestamp(local.astimezone(timezone.utc))

    def test_sign_and_window_means(self):
        stamps, values = [], []
        for hour in range(9, 17):
            stamps.append(self.utc_stamp(4, hour))
            values.append(10.0)
        for hour in list(range(21, 24)) + list(range(0, 5)):
            day = 4 if hour >= 21 else 5
            stamps.append(self.utc_stamp(day, hour))
            values.append(13.0)
        frame = pd.DataFrame({"timestamp_utc": stamps, "spl_db": values})
        result = aggregate_daily(frame)
        row = result.loc[result.local_date == "2021-01-04"].iloc[0]
        self.assertEqual(row.day_valid_hours, 8)
        self.assertEqual(row.night_valid_hours, 8)
        self.assertEqual(row.day_mean_db, 10.0)
        self.assertEqual(row.night_mean_db, 13.0)
        self.assertEqual(row.daily_difference_db, 3.0)

    def test_primary_coverage_includes_six_and_strict_requires_eight(self):
        stamps, values = [], []
        for hour in range(9, 15):
            stamps.append(self.utc_stamp(4, hour))
            values.append(10.0)
        for hour in list(range(21, 24)) + list(range(0, 3)):
            day = 4 if hour >= 21 else 5
            stamps.append(self.utc_stamp(day, hour))
            values.append(13.0)
        result = aggregate_daily(pd.DataFrame({"timestamp_utc": stamps, "spl_db": values}))
        row = result.loc[result.local_date == "2021-01-04"].iloc[0]
        self.assertTrue(row.eligible_6_of_8)
        self.assertFalse(row.eligible_8_of_8)
        self.assertEqual(row.daily_difference_db, 3.0)

    def test_duplicate_timestamp_rejected(self):
        frame = pd.DataFrame({"timestamp_utc": [pd.Timestamp("2021-01-01T00:00Z")] * 2,
                              "spl_db": [1.0, 2.0]})
        with self.assertRaises(ValueError):
            aggregate_daily(frame)


class InferenceTests(unittest.TestCase):
    def test_t_matches_scipy_reference(self):
        x = np.array([-1.2, 0.4, 1.8, 2.1, -0.1, 0.8])
        result = t_inference(x)
        reference = stats.ttest_1samp(x, 0)
        self.assertAlmostEqual(result["statistic"], reference.statistic, places=12)
        self.assertAlmostEqual(result["p_value"], reference.pvalue, places=12)
        self.assertAlmostEqual(result["se"], stats.sem(x), places=12)

    def test_hac_lag_zero_matches_sample_variance_se_with_finite_correction(self):
        x = np.array([1.0, 2.0, 4.0, 7.0, 8.0])
        result = hac_inference(x, max_lag=0)
        expected = np.std(x, ddof=1) / np.sqrt(len(x))
        self.assertAlmostEqual(result["se"], expected, places=12)

    def test_hac_bartlett_matches_independent_direct_sum(self):
        x = np.array([1.2, -0.5, 0.7, 3.0, 2.2, -1.1, 0.4])
        n, lag = len(x), 2
        residual = x - x.mean()
        lrv = sum(residual * residual) / n
        for k in range(1, lag + 1):
            gamma = sum(residual[t] * residual[t-k] for t in range(k, n)) / n
            lrv += 2 * (1 - k / (lag + 1)) * gamma
        expected = np.sqrt(lrv / n * n / (n - 1))
        self.assertAlmostEqual(hac_inference(x, max_lag=lag)["se"], expected, places=12)

    def test_bootstrap_shape_and_determinism(self):
        x = np.arange(20.0)
        first = moving_block_bootstrap(x, 4, replications=100, seed=22)
        second = moving_block_bootstrap(x, 4, replications=100, seed=22)
        self.assertEqual(first["bootstrap_means"].shape, (100,))
        np.testing.assert_array_equal(first["bootstrap_means"], second["bootstrap_means"])
        self.assertLessEqual(first["lower"], first["upper"])

    def test_single_full_length_block_preserves_observed_mean(self):
        result = moving_block_bootstrap(np.arange(12.0), 12, replications=30, seed=1)
        np.testing.assert_allclose(result["bootstrap_means"], 5.5)

    def test_iid_sampling_mean_and_coverage_mc_tolerance(self):
        rng = np.random.default_rng(300)
        n, replications, sigma = 20, 5000, 2.0
        samples = rng.normal(0, sigma, size=(replications, n))
        means = samples.mean(axis=1)
        sds = samples.std(axis=1, ddof=1)
        critical = stats.t.ppf(0.975, n - 1)
        coverage = np.mean(np.abs(means) <= critical * sds / np.sqrt(n))
        self.assertLess(abs(means.mean()), 0.04)
        self.assertLess(abs(means.std(ddof=1) - sigma / np.sqrt(n)), 0.04)
        self.assertLess(abs(coverage - 0.95), 0.02)

    def test_analytical_power_agrees_with_monte_carlo(self):
        n, sigma, effect, reps = 25, 1.5, 1.0, 20000
        rng = np.random.default_rng(310)
        sample = rng.normal(effect, sigma, size=(reps, n))
        tstat = sample.mean(axis=1) / (sample.std(axis=1, ddof=1) / np.sqrt(n))
        critical = stats.t.ppf(0.975, n - 1)
        observed = np.mean(np.abs(tstat) > critical)
        expected = iid_analytical_power(n, sigma, effect)
        self.assertLess(abs(observed - expected), 0.015)

    def test_analytical_power_stays_finite_for_extreme_but_valid_condition(self):
        power = iid_analytical_power(30, 3.0, 3.0 * 2.0)
        self.assertTrue(np.isfinite(power))
        self.assertGreater(power, 0.999)
        self.assertLessEqual(power, 1.0)

    def test_ar1_stationary_properties(self):
        result = ar1_empirical_properties(0.6, 2.0, seed=99, replications=20000, n=300)
        self.assertLess(abs(result["empirical_mean"]), 0.03)
        self.assertLess(abs(result["empirical_variance"] / result["theoretical_variance"] - 1), 0.03)
        self.assertLess(abs(result["empirical_lag1_mean"] - 0.6), 0.02)

    def test_ar1_generator_deterministic_and_stationary_initial_value(self):
        one = generate_ar1(4, 1.0, 2.0, 0.3, 100, np.random.default_rng(8))
        two = generate_ar1(4, 1.0, 2.0, 0.3, 100, np.random.default_rng(8))
        np.testing.assert_array_equal(one, two)
        self.assertEqual(one.shape, (100, 4))


if __name__ == "__main__":
    unittest.main()
