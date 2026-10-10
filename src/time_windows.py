"""Clock-window helpers for the Phase 0 audit and synthetic tests."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def interval_start(timestamp: datetime, semantics: str) -> datetime:
    """Return the represented interval start for an explicitly chosen label rule."""
    if semantics == "start":
        return timestamp
    if semantics == "end":
        return timestamp - timedelta(hours=1)
    if semantics == "center":
        return timestamp - timedelta(minutes=30)
    raise ValueError("Timestamp semantics must be explicitly start, end, or center")


def window_hours(start_date: date, kind: str) -> list[datetime]:
    """Return the eight local wall-clock hour starts in a half-open design window."""
    if kind == "day":
        start = datetime.combine(start_date, time(9))
    elif kind == "night":
        start = datetime.combine(start_date, time(21))
    else:
        raise ValueError("kind must be 'day' or 'night'")
    return [start + timedelta(hours=hour) for hour in range(8)]


def local_hour_index(timestamp: datetime, timezone: str, semantics: str) -> datetime:
    """Convert a timezone-aware timestamp to the local start of its represented bin."""
    if timestamp.tzinfo is None:
        raise ValueError("Source timestamps must be timezone-aware")
    local = interval_start(timestamp, semantics).astimezone(ZoneInfo(timezone))
    return local.replace(minute=0, second=0, microsecond=0, tzinfo=None)


def eligible_window_counts(hourly_values: dict[datetime, float], start_date: date,
                           timezone: str, semantics: str) -> dict[str, int]:
    """Count valid hourly bins in each predeclared window without comparing values."""
    indexed = {
        local_hour_index(timestamp, timezone, semantics)
        for timestamp in hourly_values
        if hourly_values[timestamp] is not None
    }
    counts = {}
    for kind in ("day", "night"):
        requested = window_hours(start_date, kind)
        counts[kind] = sum(hour in indexed for hour in requested)
    return counts


def contiguous_run_lengths(dates: list[date]) -> list[int]:
    """Return consecutive calendar-date run lengths; missing dates split runs."""
    ordered = sorted(set(dates))
    if not ordered:
        return []
    runs = []
    current = 1
    for previous, current_date in zip(ordered, ordered[1:]):
        if current_date - previous == timedelta(days=1):
            current += 1
        else:
            runs.append(current)
            current = 1
    runs.append(current)
    return runs
