"""
core/utils/logger.py — shared logger + secret masking. Passwords, OTPs, and
card numbers must never appear in plain text in logs or Allure attachments
(automation-standards.md, wrapper hard rules).
"""

import logging
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

_SECRET_KEYS = ("password", "pwd", "otp", "token", "card", "cvv", "pin")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def mask(text: str) -> str:
    """Best-effort masking for values known to be secret-shaped. Callers that
    know a value is secret should still avoid logging it at all — this is a
    safety net, not a substitute for not logging secrets."""
    if text is None:
        return text
    if re.fullmatch(r"\d{4,}", text):
        return text[:2] + "*" * max(0, len(text) - 4) + text[-2:]
    return text


def log_action(logger: logging.Logger, action: str, locator: str, value: str = None) -> None:
    if value is not None and any(k in locator.lower() for k in _SECRET_KEYS):
        value = mask(value)
    if value is not None:
        logger.info("%s locator=%r value=%r", action, locator, value)
    else:
        logger.info("%s locator=%r", action, locator)
