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
from config.settings import ENV_FILE, auth_state_path, control_panel_url  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright not installed. Run: pip install playwright && playwright install chromium")


def env(key, default=None):
    return os.environ.get(key, default)


def login(page):
    """
    Qatar Chamber / Liferay DXP login — CORRECTED 2026-09-20 (live incident this
    session, PBI 129566 Draft-vs-Publish correction batch): the PRIOR version of
    this function (role-based "Email Address"/"Password"/"Sign In" lookup against
    WEB_BASE_URL) does NOT raise, prints "Saved auth storageState" successfully,
    but produces a session that cannot actually reach any Control_Panel/Object
    Authoring surface — `manage-<slug>` and `object-authoring` both render a
    generic "Coming Soon" fallback page with that state.json (confirmed live:
    `manage-newsletter` returned title "Coming Soon..." with the prior flow's
    captured state, and title "Manage: Newsletter..." after re-capturing via
    THIS corrected flow — same account, same run). Root cause: WEB_BASE_URL's
    login page also renders a public-member "Sign In" control (matched by the
    old role-based lookup) that is a DIFFERENT auth path from the real Liferay
    LoginPortlet the admin/Control_Panel surfaces require — exactly the gap
    `cms/pages/control_panel/login_page.py`'s own docstring already disclosed
    ("tools/save_auth.py's login() is still the generic scaffold... was never
    adapted for this project's real flow, and points at the PUBLIC site, not
    CONTROL_PANEL_URL"). This was a silent false-green in the auth tool itself:
    a broken session reported as a successful capture.

    Fixed by driving the SAME real LoginPortlet flow
    `cms/pages/control_panel/login_page.py`'s CmsLoginPage and
    `core/web/session_guard.py`'s reauthenticate() already use — stable ID
    selectors scoped to the LoginPortlet form (not accessible-role names, which
    this login page's account-type ambiguity makes unsafe here), against
    CONTROL_PANEL_URL, then forcing the account's persisted UI language back to
    English via the same `update_language` endpoint (see session_guard.py's own
    HEALED note on why this step is not optional — a stale Arabic preference on
    the shared TEST_USER account silently breaks every English-text locator
    project-wide). LOGIN_*_SELECTOR env overrides are still honored for a future
    login-form change, but now default to these confirmed-live, real selectors
    instead of the broken role-based ones.
    """
    base = control_panel_url("")
    page.goto(base + env("LOGIN_PATH", "/c/portal/login"), wait_until="domcontentloaded")

    user_selector = env(
        "LOGIN_USER_SELECTOR", "#_com_liferay_login_web_portlet_LoginPortlet_login"
    )
    pass_selector = env(
        "LOGIN_PASS_SELECTOR", "#_com_liferay_login_web_portlet_LoginPortlet_password"
    )
    submit_selector = env(
        "LOGIN_SUBMIT_SELECTOR",
        '#_com_liferay_login_web_portlet_LoginPortlet_loginForm button[type="submit"]',
    )
    success_selector = env(
        "LOGIN_SUCCESS_SELECTOR",
        'nav[aria-label="Control Menu"], [data-qa-id="productMenu"]',
    )

    page.fill(user_selector, env("TEST_USER", ""))
    page.fill(pass_selector, env("TEST_PASSWORD", ""))
    page.click(submit_selector)

    # .first: this selector legitimately matches BOTH the Control Menu nav AND
    # the Product Menu toggle once logged in (see CmsLoginPage.login()) —
    # Playwright strict mode rejects a bare 2-element wait_for_selector.
    page.locator(success_selector).first.wait_for(
        state="visible", timeout=int(env("LOGIN_TIMEOUT", "15000"))
    )

    # Force (and persist) English — mirrors CmsLoginPage._force_english_locale()
    # exactly; a stale account-level Arabic preference otherwise silently
    # breaks every English-text locator on the admin surfaces later.
    from urllib.parse import quote

    redirect_url = quote("/home", safe="")
    # domcontentloaded, not the default "load" — this portal's network rarely
    # idles/finishes-loading cleanly (site-wide chatbot widget polling, same
    # finding already documented project-wide, e.g. base_page.py/
    # object_authoring_page.py's own settle notes); "load" timed out here live
    # this session even though the navigation itself completes well within it.
    page.goto(
        control_panel_url(f"/c/portal/update_language?languageId=en_US&redirect={redirect_url}"),
        wait_until="domcontentloaded",
        timeout=int(env("LOGIN_TIMEOUT", "15000")),
    )
    page.locator(success_selector).first.wait_for(
        state="visible", timeout=int(env("LOGIN_TIMEOUT", "15000"))
    )


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
