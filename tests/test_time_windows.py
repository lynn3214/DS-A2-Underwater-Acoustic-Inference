"""Synthetic-only tests for clock windows and date-run behavior."""

import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from time_windows import (contiguous_run_lengths, eligible_window_counts,
                          interval_start, local_hour_index, window_hours)
from audit_noaa import coverage_diagnostics


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

    def test_start_end_and_center_labels_assign_expected_bin(self):
        stamp = datetime(2020, 1, 1, 10, tzinfo=timezone.utc)
        self.assertEqual(interval_start(stamp, "start"), stamp)
        self.assertEqual(interval_start(stamp, "end"), datetime(2020, 1, 1, 9, tzinfo=timezone.utc))
        self.assertEqual(interval_start(stamp, "center"), datetime(2020, 1, 1, 9, 30, tzinfo=timezone.utc))

    def test_local_hour_conversion_uses_dst_aware_zone(self):
        stamp = datetime(2021, 1, 2, 14, tzinfo=timezone.utc)
        self.assertEqual(local_hour_index(stamp, "America/New_York", "start"),
                         datetime(2021, 1, 2, 9))
        summer_stamp = datetime(2021, 7, 2, 13, tzinfo=timezone.utc)
        self.assertEqual(local_hour_index(summer_stamp, "America/New_York", "start"),
                         datetime(2021, 7, 2, 9))

    def test_night_window_bins_convert_from_utc_and_keep_start_date(self):
        local_zone = ZoneInfo("America/New_York")
        night_local = window_hours(date(2020, 11, 23), "night")
        utc_values = {slot.replace(tzinfo=local_zone).astimezone(timezone.utc): 100.0
                      for slot in night_local}
        counts = eligible_window_counts(utc_values, date(2020, 11, 23),
                                        "America/New_York", "start")
        self.assertEqual(counts["night"], 8)
        self.assertEqual(min(night_local).date(), date(2020, 11, 23))
        self.assertEqual(max(night_local).date(), date(2020, 11, 24))

    def test_spring_dst_boundary_skips_local_hour_two(self):
        zone = ZoneInfo("America/New_York")
        before = datetime(2021, 3, 14, 6, tzinfo=timezone.utc).astimezone(zone)
        after = datetime(2021, 3, 14, 7, tzinfo=timezone.utc).astimezone(zone)
        self.assertEqual((before.hour, before.utcoffset()), (1, timedelta(hours=-5)))
        self.assertEqual((after.hour, after.utcoffset()), (3, timedelta(hours=-4)))
        self.assertEqual(local_hour_index(datetime(2021, 3, 14, 7, tzinfo=timezone.utc),
                                          "America/New_York", "start").hour, 3)

    def test_fall_dst_boundary_retains_both_aware_occurrences(self):
        zone = ZoneInfo("America/New_York")
        first = datetime(2020, 11, 1, 5, tzinfo=timezone.utc).astimezone(zone)
        second = datetime(2020, 11, 1, 6, tzinfo=timezone.utc).astimezone(zone)
        self.assertEqual(first.hour, 1)
        self.assertEqual(second.hour, 1)
        self.assertEqual((first.fold, second.fold), (0, 1))
        self.assertNotEqual(first.utcoffset(), second.utcoffset())
        self.assertEqual(local_hour_index(datetime(2020, 11, 1, 5, tzinfo=timezone.utc),
                                          "America/New_York", "start").hour, 1)
        self.assertEqual(local_hour_index(datetime(2020, 11, 1, 6, tzinfo=timezone.utc),
                                          "America/New_York", "start").hour, 1)

    def test_coverage_diagnostics_report_rules_and_missing_local_hour(self):
        first_day = date(2020, 11, 23)
        zone = ZoneInfo("America/New_York")
        rows = []
        for offset in range(4):
            current = first_day + timedelta(days=offset)
            for slot in window_hours(current, "day") + window_hours(current, "night"):
                rows.append((slot.replace(tzinfo=zone).astimezone(timezone.utc), 100.0))
        missing_internal_hour = (window_hours(first_day + timedelta(days=1), "day")[0]
                                 .replace(tzinfo=zone).astimezone(timezone.utc), 100.0)
        rows.remove(missing_internal_hour)
        result = coverage_diagnostics(rows, "America/New_York", "start")
        self.assertEqual(result["eligible_date_count_6_of_8"], 4)
        self.assertEqual(result["eligible_date_count_8_of_8"], 3)
        self.assertEqual(result["eligible_6_of_8_run_lengths"], [4])
        self.assertEqual(result["local_hour_missingness"]["09"]["missing_or_invalid_bins"], 1)

    def test_contiguous_runs_break_at_missing_dates(self):
        dates = [date(2020, 1, day) for day in (1, 2, 4, 7, 8, 9)]
        self.assertEqual(contiguous_run_lengths(dates), [2, 1, 3])


if __name__ == "__main__":
    unittest.main()
