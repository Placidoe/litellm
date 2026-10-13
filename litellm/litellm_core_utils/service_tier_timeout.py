from collections.abc import Mapping
from typing import Annotated, Final, TypeAlias

from pydantic import Field, TypeAdapter

ServiceTierTimeoutSeconds: TypeAlias = Annotated[float, Field(strict=True, gt=0, allow_inf_nan=False)]
_TIMEOUTS: Final = TypeAdapter(Mapping[str, ServiceTierTimeoutSeconds])


def resolve_service_tier_timeout(request: Mapping[str, object], deployment: Mapping[str, object]) -> float | None:
    tier: Final = request.get("service_tier", deployment.get("service_tier"))
    if not isinstance(tier, str):
        return None
    stream_timeouts: Final = deployment.get("stream_timeout_by_service_tier") if request.get("stream") else None
    stream_timeout: Final = (
        _TIMEOUTS.validate_python(stream_timeouts).get(tier) if stream_timeouts is not None else None
    )
    if stream_timeout is not None:
        return stream_timeout
    timeouts: Final = deployment.get("timeout_by_service_tier")
    return _TIMEOUTS.validate_python(timeouts).get(tier) if timeouts is not None else None
