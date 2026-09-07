"""
core/utils/logger.py — shared logger + secret masking. Passwords, OTPs, and
card numbers must never appear in plain text in logs or Allure attachments
(automation-standards.md, wrapper hard rules).
"""

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

_SECRET_KEYS = ("password", "pwd", "otp", "token", "card", "cvv", "pin")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def mask(text: str) -> str:
    """Masking for values known to be secret-shaped. Callers that know a
    value is secret should still avoid logging it at all — this is a safety
    net, not a substitute for not logging secrets.

    FULL mask, always. The earlier digits-only rule (re.fullmatch(r"\\d{4,}"))
    silently returned any alphanumeric password verbatim, so every
    type(PASSWORD_INPUT, ...) logged the real credential to stdout and the
    Allure attachments. A fixed token leaks nothing — not even length. Partial
    reveal (first2/last2) is deliberately NOT used: for short passwords that
    discloses most of the secret."""
    if text is None:
        return text
    return "***MASKED***"


def log_action(logger: logging.Logger, action: str, locator: str, value: str = None) -> None:
    if value is not None and any(k in locator.lower() for k in _SECRET_KEYS):
        value = mask(value)
    if value is not None:
        logger.info("%s locator=%r value=%r", action, locator, value)
    else:
        logger.info("%s locator=%r", action, locator)
