from datetime import UTC, datetime


def utcnow() -> datetime:
    """Naive UTC 'now' — all datetimes in the app are naive UTC."""
    return datetime.now(UTC).replace(tzinfo=None)
