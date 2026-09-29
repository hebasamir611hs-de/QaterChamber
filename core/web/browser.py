"""
core/web/browser.py — Playwright launch/context/page factory. The only file
(besides base_page.py) that touches raw Playwright directly.

Auth reuse (automation-standards.md -> "Auth reuse"): when AUTH_STATE_PATH is
set and the file exists, the context loads that storageState so every test
starts already logged in — no per-test login. Capture it once via
tools/save_auth.py.

PER-XDIST-WORKER SESSION ISOLATION — HEALED 2026-09-14 (triage of
tc_135009/135016/135017/135022/135023/134336). Root cause (confirmed via
trace network logs + byte-identical screenshots across different worker
threads): pytest.ini's `-n 3 --dist loadgroup` runs 3 xdist WORKER
PROCESSES, each with its own Playwright Browser/contexts, but every worker
was loading the SAME AUTH_STATE_PATH file — the same JSESSIONID cookie
baked into storageState — into every context it created. All 3 workers
therefore shared ONE authenticated Liferay session server-side. The Object
Authoring "manage-<slug>" surface keeps session-scoped server-side render
state, so when two workers hit the same object type concurrently under that
one shared session, one worker's "open new entry"/"select image" action
could resolve against a different, already-published entry another worker
was mid-editing — landing on an "Editing <GUID> (approved) ... Cancel and
add a new entry instead" banner instead of the expected blank form/picker.

Fix chosen: option (a), a SEPARATE storage_state file per xdist worker id
(`state_gw0.json`, `state_gw1.json`, ...), generated once per worker via a
real login (the same CmsLoginPage flow tools/save_auth.py itself uses) the
first time that worker needs it, then reused for the rest of that worker's
tests exactly like the single shared file was before. Chosen over option
(b) (no storage_state at all, fresh login every test) because it keeps the
"no per-test login" cost win described above while still giving each
worker its own real, independent session — the narrower, smaller-blast-
-radius fix for a collision that is specifically about SHARING one session,
not about caching one at all. Single-process runs (no xdist, e.g. `-n0` or
a bare `pytest <path>`) are UNCHANGED — PYTEST_XDIST_WORKER is unset there,
so this falls straight back to the original single shared AUTH_STATE_PATH
file with the same exists-or-skip behavior as before this fix.
"""

import os
from pathlib import Path

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


def launch_firefox_browser(playwright):
    """Real Gecko-engine (Firefox) launch — added 2026-09-23 for PBI 131054
    (ADO-141813, "keyboard navigation works consistently on Desktop
    Firefox"). Same disclosed-addition shape as launch_webkit_browser()
    above: an explicit second engine for the one case whose own subject is
    cross-browser behaviour, never a default-browser change. Confirmed live
    this session that `playwright.firefox` launches here (Firefox 119.0),
    so that case does NOT need an engine-missing skip."""
    return playwright.firefox.launch(headless=settings.headless)


def launch_edge_browser(playwright):
    """Real Microsoft Edge launch — added 2026-09-23 for PBI 131054
    (ADO-141832, "keyboard navigation works consistently on Desktop Edge").
    Edge is Chromium-based, so Playwright drives it through the chromium
    engine with `channel="msedge"`, which binds to the locally INSTALLED
    Edge build rather than Playwright's bundled Chromium — that channel
    argument is the whole point: plain `chromium.launch()` would be
    Chromium, not Edge, and reporting it as Edge would be a faked result.
    Confirmed live this session (msedge 153.0.4234.48 launches), so that
    case does NOT need an Edge-missing skip."""
    return playwright.chromium.launch(headless=settings.headless, channel="msedge")


# Engine key (as passed through the `page` fixture's param dict) -> factory.
# Keeps engine selection declarative in one place instead of a branch inside
# conftest, and keeps raw Playwright confined to this module.
ENGINE_LAUNCHERS = {
    "chromium": launch_browser,
    "firefox": launch_firefox_browser,
    "msedge": launch_edge_browser,
    "webkit": launch_webkit_browser,
}


def launch_browser_for_engine(playwright, engine: str):
    """Launch the named engine. Raises on an unknown key rather than
    silently falling back to chromium — a cross-browser case that quietly
    ran on the wrong engine would be a faked result (automation-standards.md
    -> "Result integrity")."""
    try:
        launcher = ENGINE_LAUNCHERS[engine]
    except KeyError:
        raise RuntimeError(
            f"Unknown browser engine {engine!r}. Known engines: {sorted(ENGINE_LAUNCHERS)}."
        ) from None
    return launcher(playwright)


def _xdist_worker_id() -> str | None:
    """pytest-xdist sets PYTEST_XDIST_WORKER (e.g. "gw0", "gw1") inside each
    worker process's own environment. Unset (None) outside xdist — plain
    `-n0` or a bare `pytest <path>` invocation — so callers can tell "one of
    N parallel workers" apart from "the only process running the suite"."""
    return os.environ.get("PYTEST_XDIST_WORKER")


def _worker_auth_state_path(worker: str) -> Path:
    """This worker's own storageState file path, e.g. `.auth/state_gw0.json`
    for AUTH_STATE_PATH=.auth/state.json — sibling of the shared file, never
    shared across workers."""
    base = auth_state_path()
    return base.with_name(f"{base.stem}_{worker}{base.suffix}")


def _capture_worker_auth_state(browser, path: Path) -> None:
    """Logs in ONCE (real Liferay login via CmsLoginPage — the same Page
    Object flow tools/save_auth.py's own capture already relies on
    project-wide) and saves the resulting storageState to `path`. Runs in a
    throwaway context (no storage_state loaded) that is closed immediately
    after capture — the real, per-test contexts are created separately by
    the caller once this file exists. Local import (mirrors the existing
    local-import convention in core/web/session_guard.py) so importing
    browser.py does not pull in the whole cms Page-Object tree for every
    test collection, only the first time a worker actually needs to log in.
    A no-op (nothing captured, caller falls back to no auth state — same as
    a missing/unset AUTH_STATE_PATH today) if TEST_USER/TEST_PASSWORD are
    not configured, so a misconfigured env fails the same visible way it
    already did before this change rather than hanging on a login attempt
    with blank credentials."""
    if not settings.test_user or not settings.test_password:
        return
    from cms.pages.control_panel.login_page import CmsLoginPage

    context = browser.new_context(
        viewport={"width": settings.viewport_width, "height": settings.viewport_height}
    )
    page = context.new_page()
    try:
        CmsLoginPage(page).open_login().login(settings.test_user, settings.test_password)
        path.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(path))
    finally:
        context.close()


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
        worker = _xdist_worker_id()
        if worker:
            # Under xdist: this worker's OWN session, never the shared file —
            # see module docstring's PER-XDIST-WORKER SESSION ISOLATION note.
            # Generated lazily, once per worker, the first time it's missing.
            state_file = _worker_auth_state_path(worker)
            if not state_file.exists():
                _capture_worker_auth_state(browser, state_file)
        else:
            # Single-process run (no xdist) — unchanged from before this fix:
            # the one shared file, loaded if present, silently skipped if not.
            state_file = auth_state_path()
        if state_file.exists():
            kwargs["storage_state"] = str(state_file)

    context = browser.new_context(**kwargs)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    return context


def new_api_context(
    playwright,
    user_agent: str = None,
    extra_http_headers: dict = None,
    timeout: int = None,
):
    """Playwright **APIRequestContext** factory — a browserless HTTP client.

    Added 2026-09-23 for the PBI 131053 sitemap.xml batch: those cases are
    protocol assertions (HTTP status, content-type, XML well-formedness,
    namespace) with no DOM in them, so launching a full browser context per
    test would be pure waste. This is the raw-Playwright entry point for
    that, kept here in `core/web/` alongside `new_context()` rather than in
    a test or Page Object (automation-standards.md: raw Playwright lives in
    `core/` only).

    Deliberately loads **no** storageState: an APIRequestContext created here
    is genuinely anonymous/logged-out, which is what the "public visitor /
    crawler" cases require (standards.md's "Draft/Unpublish Public-Visibility
    Checks — Mandatory Logged-Out Context" rule, applied to a protocol-level
    request). Callers that need an authenticated API context must pass
    `storage_state` explicitly via a future parameter rather than having one
    silently auto-loaded.

    Kwargs mirror `playwright.request.new_context()` exactly (verified
    against playwright.dev/python's APIRequest docs 2026-09-23); dispose with
    `context.dispose()`.
    """
    kwargs = {}
    if user_agent:
        kwargs["user_agent"] = user_agent
    if extra_http_headers:
        kwargs["extra_http_headers"] = extra_http_headers
    if timeout is not None:
        kwargs["timeout"] = timeout
    return playwright.request.new_context(**kwargs)
