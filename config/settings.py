"""
config/settings.py — typed configuration loaded from environment / .env.
NEVER hard-code URLs, capabilities, or credentials here — every value comes
from the environment so the same framework runs against dev/staging/uat/prod
without a code change.

Env-file resolution is EXPLICIT and anchored to the project root, never
discovered by walking parent directories. `load_dotenv()` with no argument
searches upward from this file, which silently resolved to whichever .env it
happened to find first and left every setting below on its empty default
while the framework kept running. One file, one absolute path, no search.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# config/settings.py -> config/ -> project root. The framework lives AT the
# project root (no automation/ subfolder), so this is exactly one level up.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# The single source of configuration for both the QA Engine MCP and this
# framework. Absolute path — the result does not depend on the working
# directory pytest was invoked from.
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    return int(val) if val else default


@dataclass(frozen=True)
class Settings:
    project_name: str = os.getenv("PROJECT_NAME", "PROJECT")
    env: str = os.getenv("ENV", "uat")
    test_user: str = os.getenv("TEST_USER", "")
    test_password: str = os.getenv("TEST_PASSWORD", "")

    # Reports root — holds allure-results/ and allure-report/ (Allure's own,
    # GUID/hash filenames) alongside screenshots/, videos/, traces/ (the
    # readable-named archive of every evidence file — see
    # core/utils/reporting.py). Anchored to PROJECT_ROOT for the same reason
    # ENV_FILE and auth_state_path() are: the archive must land in one
    # predictable place regardless of which directory pytest was invoked from.
    reports_dir: str = os.getenv("REPORTS_DIR", str(PROJECT_ROOT / "reports"))

    # Web
    web_base_url: str = os.getenv("WEB_BASE_URL", "")
    control_panel_url: str = os.getenv("CONTROL_PANEL_URL", "")
    arabic_path_prefix: str = os.getenv("ARABIC_PATH_PREFIX", "/ar")
    viewport_width: int = _env_int("VIEWPORT_WIDTH", 1920)
    viewport_height: int = _env_int("VIEWPORT_HEIGHT", 1080)
    headless: bool = _env_bool("HEADLESS", True)

    # Mobile
    appium_server_url: str = os.getenv("APPIUM_SERVER_URL", "http://127.0.0.1:4723")
    device_name: str = os.getenv("DEVICE_NAME", "")
    platform_name: str = os.getenv("PLATFORM_NAME", "Android")
    platform_version: str = os.getenv("PLATFORM_VERSION", "")
    app_path: str = os.getenv("APP_PATH", "")


settings = Settings()


def auth_state_path() -> Path:
    """Absolute path to the saved Playwright storageState.

    AUTH_STATE_PATH is written relative in .env for readability; resolving it
    here against PROJECT_ROOT means every entry point — pytest, the extractor,
    tools/save_auth.py — reads and writes the SAME file regardless of which
    directory it was invoked from, instead of creating a separate auth store
    per working directory.
    """
    raw = os.getenv("AUTH_STATE_PATH", ".auth/state.json")
    path = Path(raw)
    return path if path.is_absolute() else (PROJECT_ROOT / path)


def web_url(path: str = "/", locale: str = "en") -> str:
    """Join a site-relative path onto WEB_BASE_URL.

    `locale="ar"` applies ARABIC_PATH_PREFIX, because this site carries the
    active language in the URL path (`/ar/home` vs `/home`) rather than a
    readable cookie — see web/pages/header/language_switcher_page.py.

    Raises rather than returning a bare path when WEB_BASE_URL is unset: a
    missing base URL is a configuration error and must fail loudly at the
    first navigation, not silently send the browser to "about:blank".
    """
    base = settings.web_base_url.rstrip("/")
    if not base:
        raise RuntimeError(
            f"WEB_BASE_URL is not set. Add it to {ENV_FILE} "
            "(see README.md for the full key list)."
        )
    suffix = "/" + path.lstrip("/") if path.strip("/") else ""
    if locale == "ar":
        return f"{base}{settings.arabic_path_prefix.rstrip('/')}{suffix}"
    return f"{base}{suffix}"


def control_panel_url(path: str = "/") -> str:
    """Join a path onto CONTROL_PANEL_URL (the Liferay Control Panel base)."""
    base = settings.control_panel_url.rstrip("/")
    if not base:
        raise RuntimeError(
            f"CONTROL_PANEL_URL is not set. Add it to {ENV_FILE} — the "
            "control-panel tests cannot run without it."
        )
    suffix = "/" + path.lstrip("/") if path.strip("/") else ""
    return f"{base}{suffix}"
