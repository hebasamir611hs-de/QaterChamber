"""
core/web/browser.py — Playwright launch/context/page factory. The only file
(besides base_page.py) that touches raw Playwright directly.

Auth reuse (automation-standards.md -> "Auth reuse"): when AUTH_STATE_PATH is
set and the file exists, the context loads that storageState so every test
starts already logged in — no per-test login. Capture it once via
tools/save_auth.py.
"""

from config.settings import auth_state_path, settings


def launch_browser(playwright):
    return playwright.chromium.launch(headless=settings.headless)


def launch_webkit_browser(playwright):
    """Real Safari-engine (WebKit) launch — added for PBI 129373 batch 4
    (ADO-131150, "renders correctly in Safari on desktop"). Confirmed live
    this session that `playwright.webkit` launches successfully in this
    environment (`playwright install` already provisioned it), unlike the
    rest of this project which only ever launches `chromium` via
    `launch_browser()` above — this is an explicit, disclosed ADDITION for
    the one case whose own subject is cross-engine rendering, not a
    default-browser change. No branded "Safari.app" exists on non-macOS
    CI/dev machines; WebKit is the real, correct open-source rendering
    engine Safari itself is built on, and is the closest genuine
    (non-faked) equivalent achievable via Playwright here."""
    return playwright.webkit.launch(headless=settings.headless)


def new_context(
    browser,
    viewport: tuple = None,
    record_video_dir: str = None,
    locale: str = None,
    timezone_id: str = None,
    use_auth_state: bool = True,
):
    """`locale`/`timezone_id` map straight onto Playwright's
    `browser.new_context(locale=..., timezone_id=...)` — used by browser
    "primary language" / fresh-session cases (e.g. Chrome-with-ar-QA,
    Safari-with-en-US) that need a real locale-flavoured context rather than
    a second real browser (automation-standards.md: no `time.sleep()`, no
    unnecessary heavyweight fixtures — one Chromium context per locale is
    the correct, cheap equivalent)."""
    vw = viewport or (settings.viewport_width, settings.viewport_height)
    kwargs = {"viewport": {"width": vw[0], "height": vw[1]}}
    if record_video_dir:
        kwargs["record_video_dir"] = record_video_dir
    if locale:
        kwargs["locale"] = locale
    if timezone_id:
        kwargs["timezone_id"] = timezone_id

    # `use_auth_state=False` is MANDATORY for any test whose subject is the
    # login/permission flow itself (e.g. RBAC denial, ADO TC-134658). With the
    # default auto-load, a cached admin storageState silently pre-authenticates
    # the context — an RBAC test would then assert "denied" against an ADMIN
    # session and could false-PASS (or false-fail) the permission check.
    if use_auth_state:
        state_file = auth_state_path()
        if state_file.exists():
            kwargs["storage_state"] = str(state_file)

    context = browser.new_context(**kwargs)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    return context
