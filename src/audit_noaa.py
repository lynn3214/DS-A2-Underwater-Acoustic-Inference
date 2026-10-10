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
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml


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


def audit(path: Path, config_path: Path) -> dict:
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
    semantics_confirmed = config["windows"]["timestamp_semantics"] not in {
        "confirm_interval_start_end_or_center_before_windowing", None, ""
    }
    output = {
        "audit_status": "completed_non_outcome_diagnostics",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": {
            "station_deployment": config["candidate"]["station_deployment"],
            "timestamp_semantics_confirmed": semantics_confirmed,
            "window_eligibility_computed": False,
            "window_eligibility_reason": "Timestamp labels are whole-hour UTC timestamps, but the official metadata does not define whether they label interval starts, ends, or centers." if not semantics_confirmed else None,
        },
        "input": {
            "relative_path": str(path.relative_to(ROOT)),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        },
        "schema_and_time": {
            **schema,
            "first_timestamp_utc": timestamps[0].isoformat() if timestamps else None,
            "last_timestamp_utc": timestamps[-1].isoformat() if timestamps else None,
            "cadence_hours_counts": dict(Counter(deltas)),
            "unique_timestamp_count": len(set(timestamps)),
            "utc_hour_of_day_counts": dict(Counter(timestamp.hour for timestamp in timestamps)),
            "utc_calendar_date_row_counts": dict(Counter(timestamp.date().isoformat() for timestamp in timestamps)),
            "non_hour_aligned_timestamps": sum(t.minute != 0 or t.second != 0 or t.microsecond != 0 for t in timestamps),
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
        "prohibited_analysis_check": {
            "daily_pairs_created": False,
            "day_night_values_compared": False,
            "effect_or_interval_or_p_value_or_power_computed": False,
        },
        "runtime": {
            "python": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
            "conda": subprocess.run(["conda", "--version"], check=True, capture_output=True, text=True).stdout.strip(),
            "pyyaml": yaml.__version__,
        },
    }
    return output


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
    parser.add_argument("--config", type=Path, default=ROOT / "config/audit_protocol.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "results/audit/noaa_audit.json")
    arguments = parser.parse_args()
    result = audit(arguments.input, arguments.config)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {arguments.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
