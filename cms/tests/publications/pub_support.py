"""
cms/tests/publications/pub_support.py — shared test-layer helpers for the PBI
130711 Publication Control_Panel module (Engineer A lifecycle cases and
Engineer B field cases). Role pinning, disposable-record creation, logged-out
public reads. No raw Playwright here — everything goes through Page Objects.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

import allure
import pytest

from cms.pages.publications.publication_admin_page import (
    QCTEST_PREFIX,
    ROLE_USER_IDS,
    STATUS_INACTIVE,
    CreatedEntry,
    PublicationAdminPage,
)
from core.utils.waits import WaitTimeoutError, wait_until
from web.pages.publications.publications_page import PublicationsPage

PBI = "130711"
AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
PUBLISH_CONFIRM_TIMEOUT = 90.0
PUBLIC_REFLECT_TIMEOUT = 60.0
PUBLIC_POLL = 3.0
HISTORY_CLOCK_TOLERANCE = timedelta(minutes=5)
ARABIC = re.compile(r"[؀-ۿ]")
LATIN = re.compile(r"[A-Za-z]")


def title_for(tc_id: str, name: str) -> str:
    """`QCTEST-130711-<tc>-<name>` — the only namespace any delete accepts."""
    return f"{QCTEST_PREFIX}{tc_id}-{name}"


def pinned_login(admin: PublicationAdminPage, role: str) -> str:
    """Signs in as `role` in this auth-free context; returns the display name.
    Skips (never falls back) when the account cannot sign in or is not pinned."""
    outcome = admin.login_as_role(role)
    if outcome == "auth_failed":
        pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for '{role}'")
    if outcome != "ok":
        pytest.fail(f"login as '{role}' neither succeeded nor showed Liferay's refusal banner")
    admin.open_entries_list()
    user_id, name = admin.signed_in_user()
    if user_id != ROLE_USER_IDS[role]:
        pytest.skip(f"PRECONDITION: '{role}' credentials sign in as userId {user_id!r}, "
                    f"not the pinned {ROLE_USER_IDS[role]}")
    return name


def assert_still_pinned(admin: PublicationAdminPage, role: str) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == ROLE_USER_IDS[role], (
        f"the session is now userId {user_id!r}, not the pinned {role} ({ROLE_USER_IDS[role]}) — "
        f"it dropped and was re-authenticated as another account"
    )


def require_no_leftovers(admin: PublicationAdminPage, *titles: str) -> None:
    admin.open_entries_list()
    for title in titles:
        rows = admin.rows_with_exact_title(title)
        if rows:
            pytest.fail(
                f"PRECONDITION: {len(rows)} leftover row(s) titled {title!r} "
                f"(ids {[r['entry_id'] for r in rows]}) exist from an earlier run; they are not "
                f"deleted automatically. Remove them by hand, then rerun."
            )


def snapshot_ids(admin: PublicationAdminPage) -> set:
    """Every entry id on the fully expanded list (read-only) — the pre-action
    snapshot a creation is diffed against (review M2)."""
    admin.open_entries_list()
    if not admin.is_list_fully_expanded():
        pytest.fail("PRECONDITION: the Publication list did not expand to show every row; "
                    "cannot snapshot entry ids safely")
    return {r["entry_id"] for r in admin.list_rows()}


def register_if_created(admin: PublicationAdminPage, disposable, title: str, ids_before: set) -> CreatedEntry | None:
    """Registers for teardown the ONE row titled exactly `title` whose id was
    NOT in `ids_before` (the snapshot taken before the create attempt) —
    never a pre-existing row (review M2). Never raises: anything unexpected
    is logged and attached, and None is returned (review m5)."""
    try:
        admin.open_entries_list()
        rows = [r for r in admin.rows_with_exact_title(title) if r["entry_id"] not in ids_before]
        if len(rows) != 1:
            if rows:
                allure.attach(repr(rows), name=f"NOT registered: {len(rows)} new rows titled {title!r}")
            return None
        entry = CreatedEntry(title=title, entry_id=rows[0]["entry_id"])
        admin.adopt(entry)
        return disposable.track(entry)
    except Exception as exc:  # noqa: BLE001 — registration must never mask the test result
        allure.attach(repr(exc), name=f"registration of {title!r} failed (logged only)")
        return None


def create(admin: PublicationAdminPage, disposable, data: dict, publish: bool) -> CreatedEntry:
    """Creates one entry (Publish = the role's submit, else Save as Draft).
    Takes its OWN pre-action id snapshot, registers only a NEW row with the
    exact title (in `finally`, so even a crashed save is cleaned up), THEN
    asserts."""
    ids_before = snapshot_ids(admin)
    went_through, diagnostics, entry = False, "", None
    try:
        admin.open_new_entry_form()
        admin.fill_publication(data)
        admin.publish() if publish else admin.save_as_draft()
        went_through = admin.save_redirected()
        diagnostics = f"field errors {admin.field_errors()}, banners {admin.feedback_banners()}"
    finally:
        entry = register_if_created(admin, disposable, data["title"], ids_before)
    assert went_through, f"creating {data['title']!r} did not go through: {diagnostics}"
    assert entry is not None, f"{data['title']!r} went through but is not listed exactly once as a NEW row"
    return entry


def wait_row_status(admin: PublicationAdminPage, entry: CreatedEntry, expected: str,
                    timeout: float = PUBLISH_CONFIRM_TIMEOUT) -> str:
    seen = {"status": ""}

    def _reached() -> bool:
        admin.open_entries_list()
        seen["status"] = admin.row_status(entry)
        return seen["status"] == expected

    try:
        wait_until(_reached, timeout=timeout, poll=3.0)
    except WaitTimeoutError:
        pass
    return seen["status"]


def public_titles(anon_pages, search: str | None = None) -> list[str]:
    """Card titles a logged-out visitor sees (optionally after the page's own
    search box). Always a fresh logged-out context."""
    public = PublicationsPage(anon_pages()).open_publications().wait_for_results()
    if search:
        public.search(search)
        public.wait_for_results()
    return public.card_titles()


def public_until(anon_pages, predicate, message: str) -> PublicationsPage:
    """Publish-then-poll: reloads the public page in ONE logged-out context
    until `predicate(page)` holds (grid rendered first) or the budget ends."""
    public = PublicationsPage(anon_pages())

    def _check() -> bool:
        public.open_publications().wait_for_results()
        return bool(predicate(public))

    try:
        wait_until(_check, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL, message=message)
    except WaitTimeoutError:
        pytest.fail(f"{message} within {PUBLIC_REFLECT_TIMEOUT:.0f}s (logged-out cards: {public.card_titles()})")
    return public


def assert_not_public(anon_pages, title: str, control_title: str | None = None) -> None:
    """Absence check that cannot pass vacuously (review M5). In ONE fresh
    logged-out context: the grid must render; a POSITIVE control — a record a
    visitor can see (`control_title`, else the first visible card) — must be
    found through the same search box; only then is `title` searched and
    required to be absent."""
    public = PublicationsPage(anon_pages()).open_publications().wait_for_results()
    visible = public.card_titles()
    control = control_title or (visible[0] if visible else "")
    if not control:
        pytest.fail(f"cannot prove {title!r} is absent publicly: the logged-out page shows no publications at all "
                    f"(positive control unavailable)")
    public.search(control)
    public.wait_for_results()
    if control not in public.card_titles():
        pytest.fail(f"positive control failed: the visible publication {control!r} is not found through the public "
                    f"search box, so an absence result would mean nothing")
    public.search(title)
    public.wait_for_results()
    titles = public.card_titles()
    assert title not in titles, (
        f"{title!r} is visible to a logged-out visitor on the public Publications page (cards: {titles})"
    )


def assert_publicly_visible(anon_pages, title: str) -> PublicationsPage:
    """Positive control for a published record (review M5): publish-then-poll,
    logged-out; fails with the delivery reason if it never appears."""
    def _found(p) -> bool:
        # HEALED 2026-10-02: with the 12 restored real records the grid pages
        # at 8 cards, so a new card can sit behind "Load More" — look it up
        # through the public search box (the page fetches every item).
        p.search(title)
        p.wait_for_results()
        return title in p.card_titles()

    return public_until(
        anon_pages, _found,
        f"DELIVERY: {title!r} is Published with Active Status ticked in the CMS but never became visible to a "
        f"logged-out visitor",
    )


def parse_when(when: str) -> datetime | None:
    for fmt in ("%m/%d/%Y, %I:%M:%S %p", "%m/%d/%Y, %I:%M %p"):
        try:
            return datetime.strptime(when.strip(), fmt)
        except ValueError:
            continue
    return None


def attach_banners(admin: PublicationAdminPage, context: str, timeout: float = 15.0) -> list[str]:
    banners = admin.success_banners(timeout)
    allure.attach("\n".join(admin.feedback_banners()) or "(no banner)", name=f"feedback after {context}")
    return banners


__all__ = [
    "PBI", "AUTH_FREE_PAGE", "ARABIC", "LATIN", "HISTORY_CLOCK_TOLERANCE", "STATUS_INACTIVE",
    "title_for", "pinned_login", "assert_still_pinned", "require_no_leftovers", "register_if_created",
    "create", "snapshot_ids", "wait_row_status", "public_titles", "public_until", "assert_not_public",
    "assert_publicly_visible", "parse_when", "attach_banners",
]
