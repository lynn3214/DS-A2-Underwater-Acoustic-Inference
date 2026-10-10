"""Synthetic fixtures for CSV validity and predeclared coverage rules."""

import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_noaa import load_observations
from time_windows import eligible_window_counts


class ParsingTests(unittest.TestCase):
    def test_duplicates_invalid_timestamp_and_nonfinite_value_are_reported(self):
        content = (
            "yyyy-mm-ddTHH:MM:SSZ, BB_10-24000\n"
            "2020-01-01T09:00:00.000Z, 90\n"
            "2020-01-01T09:00:00.000Z, NaN\n"
            "not-a-time, 91\n"
            "2020-01-01T10:00:00.000Z, 92\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.csv"
            path.write_text(content, encoding="utf-8")
            rows, summary = load_observations(path)
        self.assertEqual(summary["rows_read"], 4)
        self.assertEqual(summary["rows_parsed"], 3)
        self.assertEqual(summary["duplicate_timestamp_rows"], 1)
        self.assertEqual(summary["parse_error_line_numbers"], [4])
        self.assertEqual(summary["value_status_counts"],
                         {"present": 2, "missing_or_nonfinite": 1})

    def test_six_of_eight_and_eight_of_eight_are_separate(self):
        start = datetime(2020, 1, 1, 9, tzinfo=timezone.utc)
        six_valid = {start.replace(hour=hour): 1.0 for hour in range(9, 15)}
        full = {start.replace(hour=hour): 1.0 for hour in range(9, 17)}
        six_count = eligible_window_counts(six_valid, date(2020, 1, 1), "UTC", "start")["day"]
        full_count = eligible_window_counts(full, date(2020, 1, 1), "UTC", "start")["day"]
        self.assertGreaterEqual(six_count, 6)
        self.assertLess(six_count, 8)
        self.assertEqual(full_count, 8)


if __name__ == "__main__":
    unittest.main()
