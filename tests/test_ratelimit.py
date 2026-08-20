import pytest

from app.utils.ratelimit import SlidingWindowRateLimiter


def test_rate_limiter_allows_within_window():
    rl = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    assert all(rl.allow("ip-1") for _ in range(3))
    assert rl.allow("ip-1") is False


def test_rate_limiter_allows_other_ip():
    rl = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)
    assert rl.allow("ip-a") is True
    assert rl.allow("ip-b") is True