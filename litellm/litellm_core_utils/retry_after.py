import math
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Final


def _nonnegative_seconds(value: str, divisor: int = 1) -> int | None:
    try:
        seconds: Final = float(value) / divisor
    except ValueError:
        return None
    return math.ceil(seconds) if math.isfinite(seconds) and seconds >= 0 else None


def rate_limit_retry_after(message: str, provider: str, headers: Mapping[str, str]) -> int | None:
    milliseconds: Final = headers.get("retry-after-ms")
    millisecond_delay: Final = _nonnegative_seconds(milliseconds, 1000) if milliseconds is not None else None
    if millisecond_delay is not None:
        return millisecond_delay
    retry_header: Final = headers.get("retry-after")
    if retry_header is not None:
        numeric_delay: Final = _nonnegative_seconds(retry_header)
        if numeric_delay is not None:
            return numeric_delay
        try:
            retry_date: Final = parsedate_to_datetime(retry_header)
            aware_date: Final = retry_date.replace(tzinfo=timezone.utc) if retry_date.tzinfo is None else retry_date
            return max(0, math.ceil((aware_date - datetime.now(timezone.utc)).total_seconds()))
        except (ValueError, TypeError, OverflowError):
            pass
    if provider in {"vertex_ai", "vertex_ai_beta", "gemini"}:
        delay_match: Final = re.search(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"', message)
        return _nonnegative_seconds(delay_match[1]) if delay_match is not None else None
    if provider == "groq":
        groq_match: Final = re.search(r"try again in (?:(\d+)m)?(\d+(?:\.\d+)?)s", message, re.IGNORECASE)
        if groq_match is not None:
            second_delay: Final = _nonnegative_seconds(groq_match[2])
            return int(groq_match[1] or 0) * 60 + second_delay if second_delay is not None else None
    return None
