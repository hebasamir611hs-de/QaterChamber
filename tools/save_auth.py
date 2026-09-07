#!/usr/bin/env python3
"""
save_auth.py — capture a Playwright storageState ONCE, so every locator extraction and
every test run reuses the authenticated session instead of logging in each time
(see automation-standards.md -> "Auth reuse"). Logging in on every call is the most
expensive "reach a state" path; this removes it.

Run once (creds from .env), then reuse the saved state:
    python tools/save_auth.py
    python tools/extract_locators.py --url <authed-page> --storage-state .auth/state.json
    # and the browser/context fixture loads it automatically when AUTH_STATE_PATH is set.

Re-run only when the session expires. `.auth/` is git-ignored — it holds live session
tokens; never commit it.
"""
import argparse
import os
import sys
from pathlib import Path

# Run as a script (`python tools/save_auth.py`), so sys.path[0] is tools/ and
# the project root is not importable. Add it, then import config.settings —
# importing it is what loads .env, which the env() reads below depend on.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import ENV_FILE, auth_state_path  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright not installed. Run: pip install playwright && playwright install chromium")


def env(key, default=None):
    return os.environ.get(key, default)


def login(page):
    """
    Standard username/password login driven by env selectors. ADAPT this function for
    the project's real flow (multi-step, OTP, SSO) — it is the one project-specific piece.
    Selectors default to common ids; override via LOGIN_*_SELECTOR env vars.
    """
    base = (env("WEB_BASE_URL", "") or "").rstrip("/")
    page.goto(base + env("LOGIN_PATH", "/login"), wait_until="domcontentloaded")
    page.fill(env("LOGIN_USER_SELECTOR", "#username"), env("TEST_USER", ""))
    page.fill(env("LOGIN_PASS_SELECTOR", "#password"), env("TEST_PASSWORD", ""))
    page.click(env("LOGIN_SUBMIT_SELECTOR", "button[type=submit]"))
    success = env("LOGIN_SUCCESS_SELECTOR")   # a selector visible ONLY after a real login
    if success:
        page.wait_for_selector(success, timeout=int(env("LOGIN_TIMEOUT", "15000")))
    else:
        page.wait_for_load_state("networkidle")


def main():
    ap = argparse.ArgumentParser(description="Capture Playwright storageState for reuse")
    ap.add_argument("--out", default=str(auth_state_path()))
    ap.add_argument("--viewport", default="1920x1080")
    ap.add_argument("--headed", action="store_true", help="watch the login (useful when adapting login())")
    args = ap.parse_args()

    if not env("TEST_USER") or not env("TEST_PASSWORD") or not env("WEB_BASE_URL"):
        sys.exit(f"Set WEB_BASE_URL / TEST_USER / TEST_PASSWORD in {ENV_FILE} "
                 "before capturing auth.")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    w, h = (int(x) for x in args.viewport.lower().split("x"))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        ctx = browser.new_context(viewport={"width": w, "height": h})
        page = ctx.new_page()
        try:
            login(page)
        except Exception as e:
            browser.close()
            sys.exit(f"Login failed: {e}\n"
                     "Adapt login() in tools/save_auth.py for this app's flow "
                     "(LOGIN_*_SELECTOR env, or multi-step/OTP logic).")
        ctx.storage_state(path=args.out)
        browser.close()

    print(f"Saved auth storageState -> {args.out}")
    print(f"Reuse: python tools/extract_locators.py --url <page> --storage-state {args.out}")


if __name__ == "__main__":
    main()
