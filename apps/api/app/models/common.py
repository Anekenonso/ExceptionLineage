from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def ensure_timezone_aware(dt: datetime | None) -> datetime | None:
    """Ensure that a datetime is timezone-aware.

    Raises ValueError if a naive datetime is encountered.
    """
    if dt is None:
        return None
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError("Datetime must be timezone-aware (e.g. UTC)")
    return dt


def validate_non_empty(value: str, field_name: str = "field") -> str:
    """Validate that a string value is not empty or pure whitespace."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must not be empty or whitespace")
    return value.strip()


def validate_date_range(
    effective_from: datetime | None,
    effective_until: datetime | None,
) -> None:
    """Validate that effective_until is on or after effective_from."""
    if effective_from is not None and effective_until is not None:
        if effective_until < effective_from:
            raise ValueError(
                f"effective_until ({effective_until.isoformat()}) must be on or after "
                f"effective_from ({effective_from.isoformat()})"
            )
