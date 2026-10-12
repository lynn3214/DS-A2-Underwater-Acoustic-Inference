"""Check that saved Phase 1 outputs reflect the frozen YAML parameter grids."""

import json
import re
import unittest
from pathlib import Path

import pandas as pd
import yaml
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]


class FrozenProtocolConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = yaml.safe_load((ROOT / "config/experiment_protocol.yaml").read_text())
        cls.inference = json.loads((ROOT / "results/raw/real_data_inference.json").read_text())
        cls.manifest = json.loads((ROOT / "results/raw/phase1_run_manifest.json").read_text())
        cls.sampling = pd.read_csv(ROOT / "results/raw/sampling_distribution_summary.csv")
        cls.power = pd.read_csv(ROOT / "results/raw/iid_power.csv")
        cls.ar = pd.read_csv(ROOT / "results/raw/ar1_counterexample_summary.csv")

    def test_source_and_seed_manifest_match_frozen_protocol(self):
        self.assertEqual(self.inference["source_sha256"], self.protocol["data"]["source_checksum_sha256"])
        self.assertEqual(self.manifest["source_sha256"], self.protocol["data"]["source_checksum_sha256"])
        self.assertEqual(self.manifest["runtime"]["seed_root"], self.protocol["simulations"]["seed_root"])

    def test_audit_runtime_record_does_not_publish_local_interpreter_path(self):
        audit = json.loads((ROOT / "results/audit/noaa_audit.json").read_text())
        executable = audit["runtime"]["executable"]
        self.assertEqual(executable, "Python interpreter from the active nussem1 Conda environment")
        self.assertFalse(executable.startswith("/"))

    def test_observed_results_match_source_rows_and_frozen_mbb_settings(self):
        daily = pd.read_csv(ROOT / "data/processed/daily_analysis.csv")
        differences = daily.loc[daily.eligible_6_of_8, "daily_difference_db"]
        descriptive = self.inference["descriptive"]
        audit = json.loads((ROOT / "results/audit/noaa_audit.json").read_text())
        audited_count = audit["coverage"]["eligible_date_count_6_of_8"]
        self.assertEqual(len(differences), audited_count)
        self.assertEqual(descriptive["eligible_primary_dates"], len(differences))
        self.assertAlmostEqual(descriptive["mean_difference_db"], differences.mean(), places=10)

        settings = self.protocol["analysis"]["moving_block_bootstrap"]
        mbb = [row for row in self.inference["methods"] if row["method"].startswith("Moving block")]
        self.assertEqual([row["block_length"] for row in mbb], settings["sensitivity_block_lengths"])
        self.assertTrue(all(row["replications"] == settings["replications"] for row in mbb))

    def test_sampling_distribution_grid_matches_yaml(self):
        settings = self.protocol["simulations"]["iid_sampling_distribution"]
        self.assertEqual(sorted(self.sampling.n.unique()), sorted(settings["n_values"]))
        self.assertEqual(sorted(self.sampling.effect_db.unique()), sorted(settings["effects_db"]))
        self.assertEqual(set(self.sampling.replications), {settings["replications_per_condition"]})
        self.assertEqual(len(self.sampling), len(settings["n_values"]) * len(settings["effects_db"]))

    def test_power_grid_matches_yaml(self):
        settings = self.protocol["simulations"]["iid_power"]
        baseline_n = int(re.search(r"\bn=(\d+)", settings["design"]).group(1))
        baseline_effect = self.protocol["research"]["operational_minimum_meaningful_effect_db"]
        expected = {
            "sample_size": settings["n_values"],
            "noise": settings["sigma_multipliers"],
            "effect": settings["effect_values_db"],
        }
        for factor, values in expected.items():
            rows = self.power.loc[self.power.factor == factor]
            self.assertEqual(sorted(rows.x.tolist()), sorted(values))
            self.assertEqual(set(rows.replications), {settings["replications_per_scenario"]})
            self.assertEqual(set(rows.n), {baseline_n} if factor != "sample_size" else set(values))
        self.assertEqual(set(self.power.effect_db[self.power.factor != "effect"]), {baseline_effect})
        self.assertEqual(set(self.power.effect_db[self.power.factor == "effect"]), set(settings["effect_values_db"]))

    def test_ar1_conditions_and_saved_replicates_match_yaml(self):
        settings = self.protocol["simulations"]["ar1_counterexample"]
        self.assertEqual(sorted(self.ar.rho.unique()), sorted(settings["rho_values"]))
        self.assertEqual(sorted(self.ar.effect_db.unique()), sorted(settings["effects_db"]))
        self.assertEqual(set(self.ar.replications), {settings["replications_per_condition"]})
        replicates = pd.read_csv(ROOT / "results/raw/ar1_counterexample_replicates.csv")
        expected_rows = (len(settings["rho_values"]) * len(settings["effects_db"])
                         * settings["replications_per_condition"] * len(settings["methods"]))
        self.assertEqual(len(replicates), expected_rows)

    def test_iid_interval_and_p_value_recalculate_from_saved_daily_data(self):
        daily = pd.read_csv(ROOT / "data/processed/daily_analysis.csv")
        values = daily.loc[daily.eligible_6_of_8, "daily_difference_db"].to_numpy()
        alpha = self.protocol["hypotheses"]["two_sided_alpha"] if "hypotheses" in self.protocol else self.protocol["research"]["hypotheses"]["two_sided_alpha"]
        result = next(row for row in self.inference["methods"] if row["method"] == "IID one-sample t")
        reference = stats.ttest_1samp(values, 0.0)
        critical = stats.t.ppf(1 - alpha / 2, len(values) - 1)
        se = values.std(ddof=1) / len(values) ** 0.5
        self.assertAlmostEqual(result["p_value"], reference.pvalue, places=12)
        self.assertAlmostEqual(result["lower"], values.mean() - critical * se, places=12)
        self.assertAlmostEqual(result["upper"], values.mean() + critical * se, places=12)


if __name__ == "__main__":
    unittest.main()
