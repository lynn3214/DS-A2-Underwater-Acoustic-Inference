"""Synthetic-only tests for clock windows and date-run behavior."""

import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from time_windows import (contiguous_run_lengths, eligible_window_counts,
                          interval_start, local_hour_index, window_hours)


class WindowTests(unittest.TestCase):
    def test_day_window_half_open_boundaries(self):
        hours = window_hours(date(2020, 1, 2), "day")
        self.assertEqual(len(hours), 8)
        self.assertEqual(hours[0].hour, 9)
        self.assertEqual(hours[-1].hour, 16)
        self.assertNotIn(datetime(2020, 1, 2, 17), hours)

    def test_night_is_assigned_to_starting_date_across_midnight(self):
        hours = window_hours(date(2020, 1, 2), "night")
        self.assertEqual(hours[0], datetime(2020, 1, 2, 21))
        self.assertEqual(hours[-1], datetime(2020, 1, 3, 4))
        self.assertEqual(hours[-1].date(), date(2020, 1, 3))

    def test_hour_counts_use_valid_presence_not_magnitude(self):
        day = date(2020, 1, 2)
        stamps = ([datetime(2020, 1, 2, hour, tzinfo=timezone.utc)
                   for hour in list(range(9, 17)) + list(range(21, 24))]
                  + [datetime(2020, 1, 3, hour, tzinfo=timezone.utc)
                     for hour in range(5)])
        values = {stamp: -float(index) for index, stamp in enumerate(stamps)}
        counts = eligible_window_counts(values, day, "UTC", "start")
        self.assertEqual(counts, {"day": 8, "night": 8})

    def test_semantics_are_mandatory(self):
        with self.assertRaises(ValueError):
            interval_start(datetime(2020, 1, 1), "unknown")

    def test_local_hour_conversion_uses_dst_aware_zone(self):
        stamp = datetime(2021, 1, 2, 14, tzinfo=timezone.utc)
        self.assertEqual(local_hour_index(stamp, "America/New_York", "start"),
                         datetime(2021, 1, 2, 9))

    def test_contiguous_runs_break_at_missing_dates(self):
        dates = [date(2020, 1, day) for day in (1, 2, 4, 7, 8, 9)]
        self.assertEqual(contiguous_run_lengths(dates), [2, 1, 3])


if __name__ == "__main__":
    unittest.main()
