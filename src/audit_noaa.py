"""Outcome-blind Phase 0 NOAA hourly data feasibility audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
import h5py

from time_windows import contiguous_run_lengths, eligible_window_counts, local_hour_index, window_hours


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def load_observations(path: Path) -> tuple[list[tuple[datetime, float | None]], dict]:
    rows = []
    parse_errors = []
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.reader(source)
        header = [field.strip() for field in next(reader)]
        if header != ["yyyy-mm-ddTHH:MM:SSZ", "BB_10-24000"]:
            raise ValueError(f"Unexpected source schema: {header!r}")
        for line_number, fields in enumerate(reader, start=2):
            if len(fields) != 2:
                parse_errors.append(line_number)
                continue
            try:
                timestamp = datetime.fromisoformat(fields[0].strip().replace("Z", "+00:00"))
                if timestamp.tzinfo is None:
                    raise ValueError("timestamp is not timezone-aware")
                raw_value = fields[1].strip()
                value = float(raw_value) if raw_value else None
                if value is not None and not math.isfinite(value):
                    value = None
            except ValueError:
                parse_errors.append(line_number)
                continue
            rows.append((timestamp.astimezone(timezone.utc), value))
    timestamps = [item[0] for item in rows]
    duplicates = len(timestamps) - len(set(timestamps))
    nonmonotonic = sum(right <= left for left, right in zip(timestamps, timestamps[1:]))
    value_counts = Counter("missing_or_nonfinite" if value is None else "present" for _, value in rows)
    return rows, {
        "header": header,
        "rows_read": len(rows) + len(parse_errors),
        "rows_parsed": len(rows),
        "parse_error_line_numbers": parse_errors,
        "duplicate_timestamp_rows": duplicates,
        "nonmonotonic_adjacent_pairs": nonmonotonic,
        "value_status_counts": dict(value_counts),
    }


def correlation(pairs: list[tuple[float, float]]) -> float | None:
    if len(pairs) < 2:
        return None
    x_values, y_values = zip(*pairs)
    x_mean, y_mean = statistics.mean(x_values), statistics.mean(y_values)
    denominator = math.sqrt(sum((x - x_mean) ** 2 for x in x_values) *
                            sum((y - y_mean) ** 2 for y in y_values))
    return sum((x - x_mean) * (y - y_mean) for x, y in pairs) / denominator if denominator else None


def audit(path: Path, config_path: Path, netcdf_path: Path | None = None) -> dict:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    rows, schema = load_observations(path)
    ordered = sorted(rows, key=lambda row: row[0])
    timestamps = [timestamp for timestamp, _ in ordered]
    valid_values = [value for _, value in ordered if value is not None]
    deltas = [(right - left).total_seconds() / 3600 for left, right in zip(timestamps, timestamps[1:])]
    adjacent_hour_pairs = [
        (left_value, right_value)
        for (left_time, left_value), (right_time, right_value) in zip(ordered, ordered[1:])
        if right_time - left_time == timedelta(hours=1)
        and left_value is not None and right_value is not None
    ]
    q1, q3 = quantile(valid_values, .25), quantile(valid_values, .75)
    iqr = q3 - q1 if q1 is not None and q3 is not None else None
    outlier_candidates = ([value for value in valid_values
                           if value < q1 - 1.5 * iqr or value > q3 + 1.5 * iqr]
                          if iqr is not None else [])
    semantics = config["windows"]["timestamp_semantics"]
    semantics_confirmed = semantics in {"start", "end", "center"}
    coverage = coverage_diagnostics(ordered, config["windows"]["timezone"], semantics) if semantics_confirmed else None
    local_zone = ZoneInfo(config["windows"]["timezone"])
    local_offsets = [timestamp.astimezone(local_zone).utcoffset().total_seconds() / 3600
                     for timestamp in timestamps]
    dst_active = [timestamp.astimezone(local_zone).dst() != timedelta(0) for timestamp in timestamps]
    netcdf_path = netcdf_path or ROOT / "data/raw/SanctSound_SB02_13_BB_1h.nc"
    netcdf_attributes = read_netcdf_metadata(netcdf_path)
    output = {
        "phase": 0.5,
        "audit_status": "completed_non_outcome_diagnostics",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": {
            "station_deployment": config["candidate"]["station_deployment"],
            "timestamp_semantics_confirmed": semantics_confirmed,
            "timestamp_semantics": semantics if semantics_confirmed else None,
            "timestamp_semantics_confidence": config["windows"].get("timestamp_semantics_confidence"),
            "timezone": config["windows"].get("timezone"),
            "window_eligibility_computed": coverage is not None,
            "window_eligibility_reason": None if coverage is not None else "Timestamp interval semantics are not resolved in the supplied phase configuration.",
        },
        "input": {
            "relative_path": str(path.relative_to(ROOT)),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        },
        "direct_product_metadata": netcdf_attributes,
        "schema_and_time": {
            **schema,
            "first_timestamp_utc": timestamps[0].isoformat() if timestamps else None,
            "last_timestamp_utc": timestamps[-1].isoformat() if timestamps else None,
            "cadence_hours_counts": dict(Counter(deltas)),
            "unique_timestamp_count": len(set(timestamps)),
            "utc_hour_of_day_counts": dict(Counter(timestamp.hour for timestamp in timestamps)),
            "utc_calendar_date_row_counts": dict(Counter(timestamp.date().isoformat() for timestamp in timestamps)),
            "non_hour_aligned_timestamps": sum(t.minute != 0 or t.second != 0 or t.microsecond != 0 for t in timestamps),
            "local_timezone_utc_offsets_hours": sorted(set(local_offsets)),
            "local_timezone_offset_transitions": sum(left != right for left, right in zip(local_offsets, local_offsets[1:])),
            "observations_during_daylight_time": sum(dst_active),
            "hourly_gaps": sum(delta > 1 for delta in deltas),
            "longest_consecutive_hourly_run": _longest_hourly_run(ordered),
            "hourly_lag1_correlation_within_adjacent_rows_only": correlation(adjacent_hour_pairs),
            "lag1_pair_count": len(adjacent_hour_pairs),
        },
        "marginal_values_only": {
            "valid_value_count": len(valid_values),
            "minimum": min(valid_values) if valid_values else None,
            "q1": q1,
            "median": quantile(valid_values, .5),
            "mean": statistics.mean(valid_values) if valid_values else None,
            "q3": q3,
            "maximum": max(valid_values) if valid_values else None,
            "iqr_outlier_candidate_count_for_review_only": len(outlier_candidates),
        },
        "quality_flags": {
            "source_qc_columns_present": False,
            "official_metadata_has_quantitative_qc_rule": False,
            "metadata_description": "Quality described as assessed by visual analysis and acoustic levels over time; no row-level QC flags or quantitative filtering rule documented.",
        },
        "coverage": coverage,
        "prohibited_analysis_check": {
            "paired_date_eligibility_screened": coverage is not None,
            "paired_outcome_values_created": False,
            "day_night_values_compared": False,
            "effect_or_interval_or_p_value_or_power_computed": False,
        },
        "runtime": {
            "python": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
            "conda": subprocess.run(["conda", "--version"], check=True, capture_output=True, text=True).stdout.strip(),
            "pyyaml": yaml.__version__,
            "h5py": h5py.__version__,
        },
    }
    return output


def read_netcdf_metadata(path: Path) -> dict:
    """Read direct product attributes only; do not load the measurement array."""
    if not path.exists():
        return {"available": False, "path": str(path)}
    with h5py.File(path, "r") as dataset:
        attrs = dataset.attrs
        time_attrs = dataset["time"].attrs
        timestamp_attrs = dataset["time_stamp"].attrs
        levels_attrs = dataset["sound_pressure_levels"].attrs

        def value(item):
            if isinstance(item, bytes):
                return item.decode("utf-8", errors="replace")
            if hasattr(item, "tolist"):
                item = item.tolist()
                return value(item)
            if isinstance(item, (list, tuple)):
                return [value(element) for element in item]
            return item

        return {
            "available": True,
            "relative_path": str(path.relative_to(ROOT)),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "global_doi": value(attrs.get("id")),
            "global_title": value(attrs.get("title")),
            "global_license": value(attrs.get("license")),
            "global_abstract": value(attrs.get("abstract")),
            "time_attributes": {key: value(time_attrs[key]) for key in ("comment", "units", "actual_range") if key in time_attrs},
            "time_stamp_attributes": {key: value(timestamp_attrs[key]) for key in ("comment", "units", "actual_range") if key in timestamp_attrs},
            "sound_pressure_levels_attributes": {key: value(levels_attrs[key]) for key in ("units", "comment", "actual_range") if key in levels_attrs},
        }


def coverage_diagnostics(rows: list[tuple[datetime, float | None]], timezone_name: str,
                         semantics: str) -> dict:
    """Compute clock-window completeness counts only; never compare SPL magnitudes."""
    if not rows:
        return {"status": "no_rows", "eligible_date_count_6_of_8": 0,
                "eligible_date_count_8_of_8": 0, "dates": []}

    timestamp_multiplicity = Counter(timestamp for timestamp, _ in rows)
    local_counts = Counter()
    local_valid_counts = Counter()
    local_collisions = Counter()
    for timestamp, value in rows:
        local_hour = local_hour_index(timestamp, timezone_name, semantics)
        local_counts[local_hour] += 1
        if value is not None and timestamp_multiplicity[timestamp] == 1:
            local_valid_counts[local_hour] += 1
        if local_counts[local_hour] > 1:
            local_collisions[local_hour] += 1

    first_utc, last_utc = min(timestamp for timestamp, _ in rows), max(timestamp for timestamp, _ in rows)
    expected_local_counts = Counter()
    cursor = first_utc
    while cursor <= last_utc:
        expected_local_counts[local_hour_index(cursor, timezone_name, semantics)] += 1
        cursor += timedelta(hours=1)

    local_dates = [local_hour.date() for local_hour, _ in rows]
    first_date, last_date = min(local_dates), max(local_dates)
    per_date = []
    cursor_date = first_date
    main_eligible_dates = []
    strict_eligible_dates = []
    while cursor_date <= last_date:
        day_slots = window_hours(cursor_date, "day")
        night_slots = window_hours(cursor_date, "night")
        day_valid = sum(local_valid_counts[slot] >= 1 for slot in day_slots)
        night_valid = sum(local_valid_counts[slot] >= 1 for slot in night_slots)
        main_eligible = day_valid >= 6 and night_valid >= 6
        strict_eligible = day_valid == 8 and night_valid == 8
        if main_eligible:
            main_eligible_dates.append(cursor_date)
        if strict_eligible:
            strict_eligible_dates.append(cursor_date)
        observed_hours = [hour for hour in local_counts if hour.date() == cursor_date]
        expected_hours = [hour for hour in expected_local_counts if hour.date() == cursor_date]
        valid_observed = sum(local_valid_counts[hour] >= 1 for hour in observed_hours)
        missing_observed = sum(max(0, expected_local_counts[hour] - local_valid_counts[hour])
                               for hour in expected_hours)
        per_date.append({
            "local_date": cursor_date.isoformat(),
            "expected_hour_bins_within_source_span": len(expected_hours),
            "valid_hour_bins_within_source_span": valid_observed,
            "missing_or_invalid_hour_bins_within_source_span": missing_observed,
            "day_window_valid_hours": day_valid,
            "night_window_valid_hours": night_valid,
            "eligible_6_of_8": main_eligible,
            "eligible_8_of_8": strict_eligible,
            "deployment_boundary_date": cursor_date in {first_date, last_date},
        })
        cursor_date += timedelta(days=1)

    expected_by_hour = Counter()
    for hour, count in expected_local_counts.items():
        expected_by_hour[hour.hour] += count
    local_hour_missingness = {
        f"{hour:02d}": {
            "expected_bins_in_source_span": expected_by_hour[hour],
            "valid_bins": sum(value for dt, value in local_valid_counts.items() if dt.hour == hour),
            "missing_or_invalid_bins": sum(
                max(0, count - local_valid_counts[dt])
                for dt, count in expected_local_counts.items() if dt.hour == hour
            ),
        }
        for hour in range(24)
    }

    return {
        "timezone": timezone_name,
        "timestamp_semantics": semantics,
        "validity_rule": "Finite values at unique timestamp labels; no undocumented numeric or QC filter applied.",
        "date_count_screened": len(per_date),
        "eligible_date_count_6_of_8": len(main_eligible_dates),
        "eligible_date_count_8_of_8": len(strict_eligible_dates),
        "target_minimum_dates": 30,
        "target_met_6_of_8": len(main_eligible_dates) >= 30,
        "target_met_8_of_8": len(strict_eligible_dates) >= 30,
        "eligible_6_of_8_dates": [day.isoformat() for day in main_eligible_dates],
        "eligible_6_of_8_run_lengths": contiguous_run_lengths(main_eligible_dates),
        "eligible_6_of_8_longest_run": max(contiguous_run_lengths(main_eligible_dates), default=0),
        "eligible_8_of_8_dates": [day.isoformat() for day in strict_eligible_dates],
        "eligible_8_of_8_run_lengths": contiguous_run_lengths(strict_eligible_dates),
        "eligible_8_of_8_longest_run": max(contiguous_run_lengths(strict_eligible_dates), default=0),
        "local_hour_missingness": local_hour_missingness,
        "local_date_coverage": per_date,
        "duplicate_or_dst_fold_local_hour_collision_count": sum(local_collisions.values()),
    }


def _longest_hourly_run(rows: list[tuple[datetime, float | None]]) -> int:
    if not rows:
        return 0
    longest = current = 1
    for (previous, _), (current_time, _) in zip(rows, rows[1:]):
        if current_time - previous == timedelta(hours=1):
            current += 1
        else:
            longest = max(longest, current)
            current = 1
    return max(longest, current)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "data/raw/SanctSound_SB02_13_BB_1h.csv")
    parser.add_argument("--config", type=Path, default=ROOT / "config/audit_protocol_phase0_5.yaml")
    parser.add_argument("--netcdf", type=Path, default=ROOT / "data/raw/SanctSound_SB02_13_BB_1h.nc")
    parser.add_argument("--output", type=Path, default=ROOT / "results/audit/noaa_audit.json")
    arguments = parser.parse_args()
    result = audit(arguments.input, arguments.config, arguments.netcdf)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {arguments.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
