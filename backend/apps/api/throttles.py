import re

from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle

_RATE = re.compile(r"^(\d+)/(\d*)(s|sec|m|min|h|hour|d|day)$")
_UNITS = {"s": 1, "sec": 1, "m": 60, "min": 60, "h": 3600, "hour": 3600, "d": 86400, "day": 86400}


class FlexibleRateMixin:
    """Allows rates such as '3/15min' in addition to DRF's '3/min'."""

    def parse_rate(self, rate):
        if rate is None:
            return (None, None)
        m = _RATE.match(rate)
        if not m:
            return super().parse_rate(rate)
        num, mult, unit = m.groups()
        return int(num), int(mult or 1) * _UNITS[unit]


class ScopedThrottle(FlexibleRateMixin, ScopedRateThrottle):
    pass


class EmailThrottle(FlexibleRateMixin, SimpleRateThrottle):
    scope = "magic_link_email"

    def get_cache_key(self, request, view):
        email = str(request.data.get("email", "")).strip().lower()
        if not email:
            return None
        return self.cache_format % {"scope": self.scope, "ident": email}


class IpThrottle(FlexibleRateMixin, SimpleRateThrottle):
    scope = "magic_link_ip"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
