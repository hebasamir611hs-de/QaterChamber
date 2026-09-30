"""
cms/tests/laws_regulations/lawreg_support.py — shared test-layer helpers for
the PBI 130699 Law Regulation modules:

  test_laws_regulations_control_panel.py      (Engineer A — lifecycle/auth/edge)
  test_laws_regulations_field_validation.py   (Engineer B — field validation)

Moved out of test_laws_regulations_control_panel.py unchanged so both modules
share one copy (fixtures live in this folder's conftest.py). Test-layer only:
role pinning, disposable-record creation, publish-then-poll on the public
page. No raw Playwright here — everything goes through the Page Objects.
"""

from __future__ import annotations

import pytest

from cms.pages.laws_regulations.laws_regulations_admin_page import (
    QCTEST_PREFIX,
    ROLE_USER_IDS,
    CreatedEntry,
    LawsRegulationsAdminPage,
)
from core.utils.waits import WaitTimeoutError, wait_until
from web.pages.laws_regulations.laws_regulations_page import LawsRegulationsPage

PBI = "130699"

# Role tests sign in themselves: the `page` fixture must NOT preload the
# cached TEST_USER storageState (conftest's `"auth": False`).
AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)

# ---- Wait budgets ------------------------------------------------------------
# A publish was measured at 27-30 s to reach Published on the sibling
# law-entry object (chambers_law suite); 120 s leaves headroom without turning
# a non-commit into a pass.
PUBLISH_CONFIRM_TIMEOUT = 120.0
# Public reflection AFTER the CMS already reports the new state. cms-profile
# measured ~0 s delivery; the grid re-fetches on every load, so 60 s of
# polling is generous, and a miss is a FAIL, never retried beyond this.
PUBLIC_REFLECT_TIMEOUT = 60.0
PUBLIC_POLL = 3.0

# standards.md "Named CMS User Roles" — used only to word a skip reason.
_ROLE_ENV = {
    "Site Content Editor": ("Editor", "CMS_SITE_CONTENT_EDITOR_*", "qc.editor.test@qatarchamber.local"),
    "Site Content Author": ("Author", "CMS_SITE_CONTENT_AUTHOR_*", "qc.author.test@qatarchamber.local"),
}


def _title(tc_id: str, case_title: str) -> str:
    return f"{QCTEST_PREFIX}{tc_id}-{case_title}"


def _chip(law_number: str, year: str) -> str:
    """The chip text the CASES expect: 'Law No. <n> · <year>' (U+00B7)."""
    return f"Law No. {law_number} · {year}"


def _pinned_login(admin: LawsRegulationsAdminPage, role: str) -> str:
    """Signs in as the pinned role in this auth-free context and returns the
    account's display name. Skips (never falls back) when the account cannot
    sign in or is not the pinned one."""
    outcome = admin.login_as_role(role)
    if outcome == "auth_failed":
        short, env_keys, email = _ROLE_ENV.get(role, (role, "?", "?"))
        pytest.skip(
            f"{short} login refused — .env {env_keys} stale (standards.md: {email}). "
            f"PRECONDITION: Liferay refused the credentials configured in .env for the pinned "
            f"'{role}' account ('Authentication failed due to incorrect credentials or account "
            f"lockout'); standards.md pins this role to userId {ROLE_USER_IDS[role]}."
        )
    if outcome != "ok":
        pytest.fail(f"login as '{role}' neither succeeded nor showed Liferay's refusal banner")
    admin.open_list()
    user_id, name = admin.signed_in_user()
    if user_id != ROLE_USER_IDS[role]:
        pytest.skip(
            f"PRECONDITION: the .env credentials for '{role}' sign in as userId {user_id!r}, "
            f"not the pinned account userId {ROLE_USER_IDS[role]}."
        )
    return name


def _assert_still_pinned(admin: LawsRegulationsAdminPage, role: str) -> None:
    """Engineer A's variant: a dropped/re-authenticated session FAILS the test."""
    user_id, _ = admin.signed_in_user()
    assert user_id == ROLE_USER_IDS[role], (
        f"the session is now userId {user_id!r}, not the pinned {role} "
        f"({ROLE_USER_IDS[role]}) — the qcdev session dropped and was silently re-authenticated "
        f"as another account, so no lifecycle outcome from here on is attributable to {role}"
    )


def _skip_unless_still_pinned(admin: LawsRegulationsAdminPage, role: str) -> None:
    """Field-validation variant: a session that core/web/session_guard
    silently re-signed in as another account (TEST_USER, 20132) SKIPS — no
    assertion is ever made on another account's behalf."""
    user_id, _ = admin.signed_in_user()
    if user_id != ROLE_USER_IDS[role]:
        pytest.skip(
            f"SESSION: the browser is now signed in as userId {user_id!r}, not the pinned {role} "
            f"({ROLE_USER_IDS[role]}) — core/web/session_guard.reauthenticate() silently re-signed "
            f"in as another account, so no outcome from here on is attributable to {role}. "
            f"Disposable records created so far are still torn down."
        )


def _require_no_leftovers(admin: LawsRegulationsAdminPage, *titles: str) -> None:
    admin.open_list()
    for title in titles:
        rows = admin.rows_with_exact_title(title)
        if rows:
            pytest.fail(
                f"PRECONDITION: {len(rows)} leftover row(s) titled {title!r} (entry ids "
                f"{[r['entry_id'] for r in rows]}) exist from an earlier run. They are NOT deleted "
                f"automatically (delete-safety rule: only records the same test captured). Remove "
                f"them by hand, then rerun."
            )


def _register_if_created(admin, disposable, title: str) -> CreatedEntry | None:
    """Call after ANY create attempt, whether or not it reported success:
    reopens the list and, if exactly one row carries the pre-checked unique
    exact title, registers it for teardown. Register first, assert after."""
    admin.open_list()
    rows = admin.rows_with_exact_title(title)
    if len(rows) != 1:
        return None
    return disposable.track(CreatedEntry(title=title, entry_id=rows[0]["entry_id"]))


def _create(admin, disposable, data: dict, publish: bool) -> CreatedEntry:
    """Creates one entry with `data`, submitting (publish=True) or saving as a
    draft, registers whatever got created for teardown, THEN asserts."""
    admin.open_new_form()
    admin.fill_law(data)
    if publish:
        admin.submit()
    else:
        admin.save_draft()
    went_through = admin.save_redirected()
    diagnostics = f"field errors {admin.field_errors()}, refusal bar {admin.refusal_bar_text()!r}"
    entry = _register_if_created(admin, disposable, data["law_title"])
    assert went_through, f"creating {data['law_title']!r} did not go through: {diagnostics}"
    assert entry is not None, (
        f"creating {data['law_title']!r} went through but exactly one row with that title is not listed"
    )
    return entry


def _wait_row_status(admin, entry: CreatedEntry, expected: str, timeout: float) -> str:
    seen = {"status": ""}

    def _reached() -> bool:
        admin.open_list()
        seen["status"] = admin.row_status(entry)
        return seen["status"] == expected

    try:
        wait_until(_reached, timeout=timeout, poll=3.0)
    except WaitTimeoutError:
        pass
    return seen["status"]


def _public(anon_pages, locale: str = "en") -> LawsRegulationsPage:
    page = LawsRegulationsPage(anon_pages()).open_page(locale)
    page.load_all()
    return page


def _public_until(anon_pages, predicate, message: str, locale: str = "en") -> LawsRegulationsPage:
    """Publish-then-poll on the delivery surface: reloads the public page in
    ONE logged-out context until `predicate(page)` holds or the budget ends
    (then fails)."""
    public = LawsRegulationsPage(anon_pages())

    def _check() -> bool:
        public.open_page(locale)
        public.load_all()
        return bool(predicate(public))

    wait_until(_check, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL, message=message)
    return public


def _typography_mismatches(actual: dict, family: str, weight: str, size: str,
                           line_height: str, align: tuple, color: str) -> list[str]:
    problems = []
    if family.lower() not in actual.get("font_family", "").lower():
        problems.append(f"font-family {actual.get('font_family')!r} (want {family})")
    for key, want in (("font_weight", weight), ("font_size", size),
                      ("line_height", line_height), ("color", color)):
        if want is None:
            continue
        if actual.get(key) != want:
            problems.append(f"{key} {actual.get(key)!r} (want {want!r})")
    if align and actual.get("text_align") not in align:
        problems.append(f"text-align {actual.get('text_align')!r} (want one of {align})")
    return problems
