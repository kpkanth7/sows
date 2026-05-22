from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def parse_timestamp(value: str | int | float | None) -> datetime:
    if value is None:
        return utc_now()
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, tz=UTC)
    if value.isdigit() and len(value) == 14:
        return datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    if value.isdigit() and len(value) == 8:
        return datetime.strptime(value, "%Y%m%d").replace(tzinfo=UTC)
    cleaned = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def start_of_day(value: datetime) -> datetime:
    value = value.astimezone(UTC)
    return value.replace(hour=0, minute=0, second=0, microsecond=0)
