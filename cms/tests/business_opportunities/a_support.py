"""
cms/tests/business_opportunities/a_support.py — Agent A test support for PBI
130697 (Business Opportunities, Control_Panel). Own file: fixtures and helpers
shared by the four test_bizopp_*_a_control_panel.py modules.

Pattern (Tenders PBI 130952 workflow tests, commit 1c88750):
  - every case runs as the account it names, in an auth-free context, with the
    signed-in userId re-checked before each save; Administrator-worded cases
    run as the Site Content Editor (closest real role, brief "Accounts");
  - records are disposable `QCTEST-130697-G-<tc>-<stamp>` records (A_PREFIX; was -A- before
    Agent G took the files over); identity
    (title + entry id + code) is captured right after creation by diffing the
    list ids and reading the new record back by code; teardown deletes ONLY
    those captured records, newest first (children before parents), through the
    guarded single-record delete, signed in as the Editor;
  - public checks verify the STORED Active Status first, then read the page
    from a fresh logged-out context.
"""

from __future__ import annotations

import os as _os
from datetime import datetime
from time import monotonic

import allure
import pytest

from cms.pages.business_opportunities.opportunity_admin_page import (
    BIZOPP_SLUG,
    MSG_DRAFT_SAVED,
    MSG_SAVED_AND_PUBLISHED,
    MSG_SUBMITTED_FOR_REVIEW,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    BizOppEntry,
    BizOppObjectPage,
    BizOppPublicView,
    OpportunityAdminPage,
    OpportunityChildAdminPage,
)
from cms.pages.components.object_authoring_page import shows_message
from config.settings import PROJECT_ROOT
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

# Agent G owns A's files (review-fix run); a retest may override via env (e.g. QCTEST-R30-A-).
A_PREFIX = _os.environ.get("BIZOPP_A_PREFIX", "QCTEST-130697-G-")
STAMP = datetime.now().strftime("%m%d%H%M%S")
EVIDENCE_DIR = _os.environ.get("BIZOPP_A_EVIDENCE_DIR", str(PROJECT_ROOT / "reports" / "evidence" / "130697_G"))
AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
A_GROUP = pytest.mark.xdist_group("bizopp_cms_a")
EPIC = "Business Gateway"
PUBLIC_REFLECT_TIMEOUT = 45.0


def a_name(tc_id: str, suffix: str = "") -> str:
    return f"{A_PREFIX}{tc_id}-{STAMP}" + (f" {suffix}" if suffix else "")


FIXTURES_DIR = PROJECT_ROOT / "cms" / "tests" / "business_opportunities" / "fixtures"
BMP_FIXTURE = str(FIXTURES_DIR / "a_qctest_hero-banner.bmp")
# Distinct EXISTING Documents & Media root images (picked, never uploaded).
EXISTING_ROOT_IMAGES = ("6th-World-Conference-Arbitration-Eng.png", "a_er_thumb_40kb (1).png",
                        "a_er_thumb_40kb (2).png", "a_er_thumb_40kb (3).png", "a_er_thumb_40kb (4).png",
                        "a_er_thumb_40kb (5).png", "a_er_thumb_40kb (10).png", "a_er_thumb_40kb (11).png")


def make_pdf(name: str, size_bytes: int) -> str:
    """A valid PDF of exactly `size_bytes`, written to a temp folder (large
    files are generated per run instead of being committed)."""
    import tempfile
    from pathlib import Path
    folder = Path(tempfile.gettempdir()) / "qctest_130697_a"
    folder.mkdir(exist_ok=True)
    head = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
            b"trailer<</Root 1 0 R>>\n")
    tail = b"\n%%EOF\n"
    filler = b"%" + b"Q" * (size_bytes - len(head) - len(tail) - 2) + b"\n"
    path = folder / name
    path.write_bytes(head + filler + tail)
    assert path.stat().st_size == size_bytes
    return str(path)


def today_ddmmyyyy(delta_days: int = 0) -> str:
    from datetime import timedelta
    return (datetime.now() + timedelta(days=delta_days)).strftime("%d/%m/%Y")


# ===========================================================================
# Fixtures
# ===========================================================================
class Registry:
    """Records this test created (captured identity), in creation order."""

    def __init__(self):
        self.entries: list[BizOppEntry] = []

    def track(self, entry: BizOppEntry) -> BizOppEntry:
        if not entry.in_namespace() or entry.prefix != A_PREFIX:
            raise ValueError(f"{entry} is not a captured {A_PREFIX} record")
        if all(e.entry_id != entry.entry_id for e in self.entries):
            self.entries.append(entry)
        return entry


def _page_for(slug: str, page) -> BizOppObjectPage:
    if slug == BIZOPP_SLUG:
        return OpportunityAdminPage(page, A_PREFIX, EVIDENCE_DIR)
    return OpportunityChildAdminPage.for_slug(slug, page, A_PREFIX, EVIDENCE_DIR)


@pytest.fixture
def disposable(browser):
    """Deletes ONLY the records the test registered at creation (newest first),
    signed in as the Site Content Editor, through the guarded delete."""
    registry = Registry()
    yield registry
    if not registry.entries:
        return
    ctx = new_context(browser, use_auth_state=False)
    outcome, failures = [], []
    try:
        page = ctx.new_page()
        login = OpportunityAdminPage(page, A_PREFIX, EVIDENCE_DIR)
        if login.login_as_role(ROLE_EDITOR) == "auth_failed":
            failures.append("teardown could not sign in as the Editor")
        # Parents FIRST, while their children are still live: deleting a parent
        # cascades to its children, whereas a parent whose children were already
        # deleted (Recycle Bin) is refused with HTTP 400 (live 2026-10-07).
        # Children of a deleted parent then read "already gone".
        ordered = ([e for e in reversed(registry.entries) if e.slug == BIZOPP_SLUG]
                   + [e for e in reversed(registry.entries) if e.slug != BIZOPP_SLUG])
        for entry in ordered:
            label = f"{entry.slug} {entry.title!r} (id {entry.entry_id}, code {entry.code})"
            cleaner = _page_for(entry.slug, page)
            if hasattr(cleaner, "owned_parent_ids"):
                cleaner.owned_parent_ids = {e.entry_id for e in registry.entries if e.slug == BIZOPP_SLUG}
            try:
                cleaner.open_list_all()
                if not any(r["entry_id"] == entry.entry_id for r in cleaner.list_rows()):
                    if cleaner.is_list_fully_expanded():
                        outcome.append(f"already gone: {label}")
                    else:
                        failures.append(f"{label}: not found and the list is NOT fully expanded")
                    continue
                cleaner.adopt_entry(entry)
                if cleaner.delete_own_entry(entry):
                    outcome.append(f"removed {label}")
                else:
                    failures.append(f"NOT removed {label}: guarded delete refused/failed (see log)")
            except Exception as exc:  # noqa: BLE001 — collected and raised below
                failures.append(f"{label}: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(outcome + failures) or "nothing to remove", name="QCTEST teardown")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


def _contexts(browser):
    contexts = []

    def _make():
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return ctx.new_page()

    return contexts, _make


@pytest.fixture
def anon_pages(browser):
    """Fresh logged-out contexts for every public read."""
    contexts, make = _contexts(browser)
    yield make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


@pytest.fixture
def role_pages(browser):
    """Extra auth-free pages for a second account in the same test."""
    contexts, make = _contexts(browser)
    yield make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# Helpers (test layer — no raw Playwright)
# ===========================================================================
def login(page, role: str, slug: str = BIZOPP_SLUG) -> BizOppObjectPage:
    """Signs in as `role` in this auth-free context; skips (never falls back)
    when the account cannot sign in or is not the pinned one."""
    admin = _page_for(slug, page)
    outcome = admin.login_as_role(role)
    if outcome == "auth_failed":
        pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for '{role}'")
    admin.open_list_all()
    user_id, _ = admin.signed_in_user()
    if not user_id:
        pytest.fail(f"login as '{role}' neither succeeded nor showed Liferay's refusal banner")
    if user_id != ROLE_USER_IDS[role]:
        pytest.skip(f"PRECONDITION: '{role}' signs in as userId {user_id!r}, not the pinned {ROLE_USER_IDS[role]}")
    return admin


ROLE_ADMINISTRATOR = "Administrator"      # = TEST_USER (super-admin), confirmed by the user 2026-10-07
ROLE_QC_ADMIN_REVIEWER = "Form Manager"   # "QC Admin Reviewer" in the cases = the Form Manager role


def login_any(page, role: str, slug: str = BIZOPP_SLUG) -> tuple[BizOppObjectPage, str]:
    """Signs in as `role` ("Administrator" -> TEST_USER, or any cms_role_credentials
    role) WITHOUT pinning a userId; returns (page object, signed-in userId).
    Never prints credentials."""
    from cms.pages.control_panel.login_page import CmsLoginPage  # noqa: PLC0415
    from config.settings import settings  # noqa: PLC0415
    admin = _page_for(slug, page)
    if role == ROLE_ADMINISTRATOR:
        try:
            CmsLoginPage(page).open_login().login(settings.test_user, settings.test_password)
        except Exception:  # noqa: BLE001 — sign-in is checked below
            pass
    else:
        if admin.login_as_role(role) == "auth_failed":
            pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for '{role}'")
    admin.open(admin._manage_url(locale="en"))
    admin.page.wait_for_load_state("load")
    user_id, _ = admin.signed_in_user()
    if not user_id:
        pytest.fail(f"login as '{role}' did not produce a signed-in session")
    allure.attach(f"{role} -> userId {user_id}", name="signed-in account")
    admin._pinned_user_id = user_id
    return admin, user_id


def same_session(admin: BizOppObjectPage, slug: str) -> BizOppObjectPage:
    """Another object's page object on the SAME signed-in page."""
    return _page_for(slug, admin.page)


def pinned(admin: BizOppObjectPage, role: str) -> None:
    user_id, _ = admin.signed_in_user()
    expected = ROLE_USER_IDS.get(role) or getattr(admin, "_pinned_user_id", "")
    assert expected and user_id == expected, (
        f"the session is now userId {user_id!r}, not the pinned {role} ({expected})")


def has(banners: list[str], expected: str) -> bool:
    return any(shows_message(b, expected) for b in banners)


def expected_banner(publish: bool, role: str) -> str:
    if not publish:
        return MSG_DRAFT_SAVED
    return MSG_SUBMITTED_FOR_REVIEW if role == ROLE_AUTHOR else MSG_SAVED_AND_PUBLISHED


def create(admin: BizOppObjectPage, disposable: Registry, identity: str, fill, publish: bool,
           role: str = ROLE_EDITOR, wait_arabic: bool = True) -> BizOppEntry:
    """Creates one record: `fill(admin)` fills the open create form, then Save as
    Draft (publish=False) or the role's submit button. Registers whatever got
    created for teardown, THEN asserts. `admin.create_banners` holds the
    edit-bar messages shown after the save."""
    ids_before = admin.snapshot_ids()
    went_through, diagnostics, banners, arabic = False, {}, [], ""
    try:
        admin.open_create_form_en()
        fill(admin)
        pinned(admin, role)
        admin.click_publish() if publish else admin.click_save_as_draft()
        went_through = admin.save_went_through()
        diagnostics = admin.refusal_evidence()
        if went_through:
            banners = admin.success_messages(expected_banner(publish, role), timeout=15.0)
            if wait_arabic:
                arabic = admin.wait_arabic_saved()
            admin.evidence(f"{identity} after {'submit' if publish else 'draft'}")
        else:
            admin.evidence(f"{identity} save not through")
    finally:
        entry = None
        try:
            entry = admin.identify_created_entry(identity, ids_before)
            if entry:
                disposable.track(entry)
        except Exception as exc:  # noqa: BLE001 — registration must not mask the result
            allure.attach(repr(exc), name=f"registration of {identity!r} failed")
    admin.create_banners = banners
    allure.attach("\n".join(banners) or "(none)", name=f"edit-bar after creating {identity}")
    allure.attach(arabic or "(no Arabic-save message)", name="Arabic content save")
    assert went_through, f"creating {identity!r} as {role} did not go through: {diagnostics}"
    assert entry is not None, f"{identity!r} went through but is not identifiable as exactly one NEW record"
    return entry


def create_opportunity(admin: OpportunityAdminPage, disposable: Registry, data: dict, publish: bool,
                       role: str = ROLE_EDITOR) -> BizOppEntry:
    return create(admin, disposable, data["opportunityTitle"], lambda a: a.fill_opportunity(data), publish, role)


def create_child(parent_admin: BizOppObjectPage, disposable: Registry, slug: str, parent: BizOppEntry,
                 data: dict, identity: str, publish: bool = True) -> tuple[BizOppEntry, BizOppObjectPage]:
    """Creates one child record of `parent` on the SAME signed-in page."""
    child = same_session(parent_admin, slug)
    child.owned_parent_ids.add(parent.entry_id)
    data = dict(data, parent=parent.code)
    wait_ar = any(k.endswith("_ar") for k in data)
    entry = create(child, disposable, identity, lambda a: a.fill_child(data), publish, wait_arabic=wait_ar)
    return entry, child


def history(admin: BizOppObjectPage, entry: BizOppEntry) -> list[dict]:
    trail = admin.history(entry)
    allure.attach("\n".join(repr(h) for h in trail) or "(empty)", name=f"History of {entry.code}")
    return trail


def require_active_status(admin: BizOppObjectPage, entry: BizOppEntry) -> None:
    """Brief rule 4: the STORED Active Status must be ticked before any public check."""
    admin.open_entry_en(entry.code)
    stored = admin.active_status_stored()
    allure.attach(f"stored Active Status: {stored!r}", name="public-visibility precondition")
    if stored != "true":
        pytest.fail(f"PRECONDITION NOT MET — PRODUCT: {entry.title!r} stores Active Status {stored!r}; "
                    f"the public step was not run")


def public_until(anon_pages, predicate, message: str, locale: str = "en", tab: str = "active",
                 timeout: float = PUBLIC_REFLECT_TIMEOUT) -> tuple[BizOppPublicView, float]:
    """Poll the logged-out listing until `predicate(view)`; returns view + latency."""
    view = BizOppPublicView(anon_pages())
    started = monotonic()

    def _check() -> bool:
        view.open_listing(locale, tab)
        return bool(predicate(view))

    try:
        wait_until(_check, timeout=timeout, poll=2.0, message=message)
    except WaitTimeoutError:
        view.screenshot(f"public listing at timeout ({tab}, {locale})")
        pytest.fail(f"{message} within {timeout:.0f}s (tabs {view.tabs()}, cards {[c['title'] for c in view.cards()]})")
    latency = monotonic() - started
    allure.attach(f"{latency:.1f}s", name="observed public-listing latency")
    return view, latency


def assert_not_public(anon_pages, entry: BizOppEntry, title_text: str) -> dict:
    """Absence on BOTH tabs (EN), the detail URL and the search, that cannot pass
    vacuously: the Active tab must render real cards first. Returns evidence."""
    evidence = {}
    for tab in ("active", "archive"):
        view = BizOppPublicView(anon_pages()).open_listing("en", tab)
        cards = view.cards()
        evidence[tab] = {"tabs": view.tabs(), "cards": [c["title"] for c in cards]}
        if tab == "active":
            assert cards, f"cannot prove {entry.code} is absent: the logged-out Active tab shows no cards"
        assert not view.card_for(entry.code), f"{entry.title!r} ({entry.code}) is on the public {tab} tab"
        assert title_text not in [c["title"] for c in cards], f"a card titled {title_text!r} is on the {tab} tab"
    detail = BizOppPublicView(anon_pages()).open_detail(entry.code)
    body = detail.detail()["body"]
    evidence["detail_url_shows_title"] = title_text in body
    allure.attach(repr(evidence), name="logged-out absence evidence")
    assert title_text not in body, f"the logged-out detail URL for {entry.code} renders {title_text!r}"
    return evidence
