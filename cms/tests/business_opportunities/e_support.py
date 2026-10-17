"""
cms/tests/business_opportunities/e_support.py — Agent E test support for PBI
130697 (Business Opportunities, Control_Panel). Agent E took over A's
test_bizopp_auth_a / test_bizopp_page_a modules; this file re-points A's
helpers at the E_PREFIX namespace (now `QCTEST-130697-G-<tc>-<stamp>`, Agent G):

  - page objects are built with the E prefix (they refuse any other record);
  - `disposable_e` registers ONLY captured E records (title + entry id + code)
    and deletes them in teardown through the guarded single-record delete,
    signed in as the Site Content Editor — parents first, never the Recycle Bin;
  - role logins retry (the Editor / Author accounts are shared with other
    agents running in parallel) and pin the signed-in userId.

The generic helpers (create, pinned, has, history, anon_pages) are reused
from a_support unchanged.
"""

from __future__ import annotations

from datetime import datetime

import allure
import pytest

from cms.pages.business_opportunities.opportunity_admin_page import (
    BIZOPP_SLUG,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    BizOppEntry,
    BizOppObjectPage,
    OpportunityAdminPage,
    OpportunityChildAdminPage,
    OpportunityListingPageAdminPage,
    LISTING_PAGE_SLUG,
)
from cms.tests.business_opportunities.a_support import (  # noqa: F401 — re-exported fixtures/helpers
    AUTH_FREE_PAGE,
    EPIC,
    anon_pages,
    create,
    has,
    history,
    pinned,
    role_pages,
)
from config.settings import PROJECT_ROOT
from core.web.browser import new_context

E_PREFIX = "QCTEST-130697-G-"  # Agent G owns E's files (review-fix run)
E_STAMP = datetime.now().strftime("%m%d%H%M%S")
E_EVIDENCE_DIR = str(PROJECT_ROOT / "reports" / "evidence" / "130697_G")
E_GROUP = pytest.mark.xdist_group("bizopp_cms_e")
LOGIN_ATTEMPTS = 3

ROLE_ADMINISTRATOR = "Administrator"      # = TEST_USER (user decision 2026-10-07)
ROLE_QC_ADMIN_REVIEWER = "Form Manager"   # "QC Admin Reviewer" in the cases = Form Manager (user decision)


def e_name(tc_id: str, suffix: str = "") -> str:
    return f"{E_PREFIX}{tc_id}-{E_STAMP}" + (f" {suffix}" if suffix else "")


def page_for(slug: str, page) -> BizOppObjectPage:
    if slug == BIZOPP_SLUG:
        return OpportunityAdminPage(page, E_PREFIX, E_EVIDENCE_DIR)
    if slug == LISTING_PAGE_SLUG:
        return OpportunityListingPageAdminPage(page, E_PREFIX, E_EVIDENCE_DIR)
    return OpportunityChildAdminPage.for_slug(slug, page, E_PREFIX, E_EVIDENCE_DIR)


def _sign_in(admin: BizOppObjectPage, role: str) -> tuple[str, str]:
    """login_as_role with retries; returns (outcome, signed-in userId)."""
    outcome, user_id = "", ""
    for _ in range(LOGIN_ATTEMPTS):
        outcome = admin.login_as_role(role)
        if outcome == "auth_failed":
            admin.page.wait_for_timeout(4000)
            continue
        try:
            admin.open_list_all()
        except Exception:  # noqa: BLE001 — a role without list access (Form Manager) sees Access Denied
            admin.page.wait_for_load_state("load")
        user_id, _ = admin.signed_in_user()
        if user_id:
            break
        admin.page.wait_for_timeout(4000)
    return outcome, user_id


def e_login(page, role: str, slug: str = BIZOPP_SLUG) -> BizOppObjectPage:
    """Signs in as `role` (pinned userId) in this auth-free context; skips when
    the account cannot sign in, never falls back to another account."""
    admin = page_for(slug, page)
    outcome, user_id = _sign_in(admin, role)
    if outcome == "auth_failed" and not user_id:
        pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for '{role}' ({LOGIN_ATTEMPTS} attempts)")
    if not user_id:
        pytest.fail(f"login as '{role}' neither succeeded nor showed Liferay's refusal banner")
    expected = ROLE_USER_IDS.get(role)
    if expected and user_id != expected:
        pytest.skip(f"PRECONDITION: '{role}' signs in as userId {user_id!r}, not the pinned {expected}")
    admin._pinned_user_id = user_id
    allure.attach(f"{role} -> userId {user_id}", name="signed-in account")
    return admin


class ERegistry:
    """Records this test created (captured E identity), in creation order."""

    def __init__(self):
        self.entries: list[BizOppEntry] = []

    def track(self, entry: BizOppEntry) -> BizOppEntry:
        if not entry.in_namespace() or entry.prefix != E_PREFIX:
            raise ValueError(f"{entry} is not a captured {E_PREFIX} record")
        if all(e.entry_id != entry.entry_id for e in self.entries):
            self.entries.append(entry)
        return entry


@pytest.fixture
def disposable_e(browser):
    """Deletes ONLY the E records the test registered at creation, signed in as
    the Site Content Editor, through the guarded delete (id + code + title
    re-read on the opened form). Parents first; never purges the Recycle Bin."""
    registry = ERegistry()
    yield registry
    if not registry.entries:
        return
    ctx = new_context(browser, use_auth_state=False)
    outcome, failures = [], []
    try:
        page = ctx.new_page()
        signer = page_for(BIZOPP_SLUG, page)
        _, user_id = _sign_in(signer, ROLE_EDITOR)
        if user_id != ROLE_USER_IDS[ROLE_EDITOR]:
            failures.append(f"teardown could not sign in as the Editor (userId {user_id!r})")
        ordered = ([e for e in reversed(registry.entries) if e.slug == BIZOPP_SLUG]
                   + [e for e in reversed(registry.entries) if e.slug != BIZOPP_SLUG])
        for entry in ([] if failures else ordered):
            label = f"{entry.slug} {entry.title!r} (id {entry.entry_id}, code {entry.code})"
            cleaner = page_for(entry.slug, page)
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


def create_opportunity_e(admin: OpportunityAdminPage, disposable: ERegistry, data: dict, publish: bool,
                         role: str = ROLE_EDITOR):
    return create(admin, disposable, data["opportunityTitle"], lambda a: a.fill_opportunity(data), publish, role)
