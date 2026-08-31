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

# Same site-wide announcement-overlay guard BasePage.open() applies (see
# core/web/overlays.py). This script drives raw Playwright (it runs BEFORE
# any authenticated Page Object exists to wrap it), so it has to dismiss the
# overlay itself — found live 2026-08-31 automating PBI 129392: the
# anonymous /c/portal/login page sits on the same host as CONTROL_PANEL_URL,
# so #qc-announcement-popup-root mounts there too and intercepts the Sign In
# click without this.
from core.web.overlays import dismiss_overlays, MOUNT_GRACE_MS  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright not installed. Run: pip install playwright && playwright install chromium")


def env(key, default=None):
    return os.environ.get(key, default)


def login(page):
    """
    Liferay CMS login — the project-specific piece, adapted from the generic
    template default. Selectors match web/pages/components/cms_login_page.py
    (CmsLoginPage), CLI-confirmed live against qcdev.ihorizons.com/c/portal/login
    (commit 2cbbb4c, re-confirmed 2026-08-24/2026-08-31). Override any of them
    via the matching LOGIN_*_SELECTOR / LOGIN_PATH env var if the CMS login
    flow ever changes.
    """
    base = (env("WEB_BASE_URL", "") or "").rstrip("/")
    page.goto(base + env("LOGIN_PATH", "/c/portal/login"), wait_until="domcontentloaded")
    dismiss_overlays(page, grace_ms=MOUNT_GRACE_MS)
    page.fill(
        env("LOGIN_USER_SELECTOR", "#_com_liferay_login_web_portlet_LoginPortlet_login"),
        env("TEST_USER", ""),
    )
    page.fill(
        env("LOGIN_PASS_SELECTOR", "#_com_liferay_login_web_portlet_LoginPortlet_password"),
        env("TEST_PASSWORD", ""),
    )
    submit_selector = env(
        "LOGIN_SUBMIT_SELECTOR",
        '#_com_liferay_login_web_portlet_LoginPortlet_loginForm button[type="submit"]',
    )
    dismiss_overlays(page)  # re-check: the overlay can (re)mount after fill() triggers JS
    try:
        page.click(submit_selector)
    except Exception:
        # Same retry-once-after-dismiss pattern as BasePage.click(): the
        # overlay can remount again in the gap between the check above and
        # the click actually landing (client-rendered, not on a fixed timer).
        if not dismiss_overlays(page):
            raise
        page.click(submit_selector)
    success = env("LOGIN_SUCCESS_SELECTOR", 'nav[aria-label="Control Menu"]')
    if success:
        page.wait_for_selector(success, timeout=int(env("LOGIN_TIMEOUT", "20000")))
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
