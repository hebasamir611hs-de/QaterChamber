"""
core/utils/waits.py — explicit-wait helpers. `time.sleep()` is forbidden
everywhere in this framework (automation-standards.md, wrapper hard rules).
Playwright/Appium have their own built-in auto-waiting for actionability;
wait_until() below is the generic polling fallback for arbitrary predicates
(e.g. "wait until this Page-Object state query returns True") that the
built-in waits don't cover.
"""

import time
from typing import Callable


class WaitTimeoutError(TimeoutError):
    pass


def wait_until(predicate: Callable[[], bool], timeout: float = 10.0, poll: float = 0.25, message: str = "") -> None:
    deadline = time.monotonic() + timeout
    last_exc = None
    while time.monotonic() < deadline:
        try:
            if predicate():
                return
        except Exception as exc:  # noqa: BLE001 — deliberately broad: keep polling
            last_exc = exc
        time.sleep(poll)
    detail = message or (str(last_exc) if last_exc else "condition never became true")
    raise WaitTimeoutError(f"wait_until timed out after {timeout}s: {detail}")
