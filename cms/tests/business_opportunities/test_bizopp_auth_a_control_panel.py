"""
cms/tests/business_opportunities/test_bizopp_auth_a_control_panel.py —
P1 role / auth cases for PBI 130697 (Business Opportunities), Azure suite
140361 in plan 137724, on `manage-business-opportunity` (Agent A).

Accounts: Site Content Editor (156488), Site Content Author (156492), a
logged-out context, and "QC Admin Reviewer" = the Form Manager role (user
decision 2026-10-07).

Live facts this module asserts against (recon 2026-10-07):
  - Editor form buttons "Save as Draft" / "Publish" (publishes directly);
    Author form buttons "Save as Draft" / "Submit for Review".
  - Logged-out `manage-*` URLs answer 404 with the "Coming Soon" page — no
    redirect to the login page (OBJECT-AUTHORING-GUIDE §1 documents the 404).
"""

from __future__ import annotations

import allure
import pytest

from cms.pages.business_opportunities.opportunity_admin_page import (
    K_SUB_SECTOR,
    MSG_DRAFT_SAVED,
    MSG_SAVED_AND_PUBLISHED,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    OpportunityAdminPage,
)
from cms.tests.business_opportunities.a_support import (  # noqa: F401 — fixtures (143276 stays A's)
    A_GROUP,
    disposable,
    login,
)
from cms.tests.business_opportunities.e_support import (  # noqa: F401 — fixtures
    AUTH_FREE_PAGE,
    E_EVIDENCE_DIR,
    E_GROUP,
    E_PREFIX,
    EPIC,
    ROLE_QC_ADMIN_REVIEWER,
    anon_pages,
    create_opportunity_e,
    disposable_e,
    e_login,
    e_name,
    has,
    history,
    pinned,
)
from cms.tests.business_opportunities.a_support import a_name, create_opportunity  # noqa: E402 — 143276
from core.web.base_page import BasePage
from config.settings import control_panel_url

FEATURE = "Business Opportunities — Control Panel (auth / roles)"
MANAGE_PATHS = {
    "Business Opportunity Management": "/web/qatar-chamber/manage-business-opportunity",
    "Inquiry review": "/web/qatar-chamber/manage-opportunity-inquiry",
    "Submission review": "/web/qatar-chamber/manage-opportunity-submission",
}


def _markers(*tcs, group=E_GROUP):
    def deco(fn):
        for m in (pytest.mark.control_panel, pytest.mark.invest, pytest.mark.auth, pytest.mark.pbi_130697, group):
            fn = m(fn)
        for tc in tcs:
            fn = getattr(pytest.mark, f"tc_{tc}")(fn)
        return fn
    return deco


# ===========================================================================
# 143275 — logged-out forced browsing to the CMS management URLs
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / forced browsing")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A logged-out user forced-browsing to the CMS Opportunity Management URLs is redirected to login")
@_markers("143275")
def test_logged_out_forced_browsing_redirects_to_login(anon_pages):
    # Azure TC 143275 | PBI 130697 | logged-out context (no CMS user).
    results = {}
    for name, path in MANAGE_PATHS.items():
        page = anon_pages()
        response = page.goto(control_panel_url(path), wait_until="load", timeout=60000)
        BasePage(page).page.wait_for_timeout(2500)
        view = OpportunityAdminPage(page, E_PREFIX, E_EVIDENCE_DIR)
        results[name] = {
            "status": response.status if response else None,
            "final_url": page.url,
            "title": page.title(),
            "login_form": page.locator("#_com_liferay_login_web_portlet_LoginPortlet_login").count() > 0,
            "on_login_url": "login" in page.url.lower(),
            "records_or_controls": page.locator('[data-qc-oel-delete], [data-qc-oel-view], [name^="ObjectField_"], '
                                                'button:has-text("Save as Draft"), button:has-text("Publish")').count(),
        }
        view.evidence(f"143275 logged-out {name}")
    allure.attach("\n".join(f"{k}: {v}" for k, v in results.items()), name="logged-out responses")

    # Step 2 — no records or admin controls exposed (the security outcome).
    exposed = {k: v for k, v in results.items() if v["records_or_controls"]}
    assert not exposed, f"PRODUCT: logged-out requests exposed records/admin controls: {exposed}"
    # Steps 1, 3, 4 — the case expects a redirect to the CMS login page.
    not_redirected = {k: f"HTTP {v['status']} at {v['final_url']} ({v['title']!r}), login form: {v['login_form']}"
                      for k, v in results.items() if not (v["login_form"] or v["on_login_url"])}
    assert not not_redirected, (
        "PRODUCT (behaviour differs, access is still blocked): logged-out management URLs are NOT redirected to the "
        f"CMS login page — {not_redirected}")


# ===========================================================================
# 143276 — Site Content Editor manages records (create, edit, Save Draft, Publish)
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Editor can log in and manage Business Opportunity records")
@_markers("143276", group=A_GROUP)
def test_editor_manages_business_opportunity_records(page, disposable):
    # Azure TC 143276 | PBI 130697 | account: Site Content Editor (156488).
    # Steps 1-2 — login + management list with existing records.
    editor = login(page, ROLE_EDITOR)
    rows = editor.list_rows()
    allure.attach("\n".join(f"{r['code']} {r['status']}" for r in rows), name="management list rows")
    assert rows, "the Editor's Business Opportunity Management list shows no records"

    # Step 3 — create a record (Save Draft), then edit it and Save Draft again.
    title = a_name("143276", "Editor managed")
    # Active Status ticked: with it off a published record reads "(Inactive)", not "(Published)"
    data = OpportunityAdminPage.default_data(title)
    entry = create_opportunity(editor, disposable, data, publish=False)
    assert has(editor.create_banners, MSG_DRAFT_SAVED), f"no {MSG_DRAFT_SAVED!r}: {editor.create_banners}"
    editor.open_list_all()
    assert editor.row_status_of(entry) == "Draft", f"new record status {editor.row_status_raw(entry)!r}"
    edited = "QCTEST Solar (edited by the Editor)"
    editor.open_entry_en(entry.code)
    editor.fill_en(K_SUB_SECTOR, edited)
    pinned(editor, ROLE_EDITOR)
    editor.click_save_as_draft()
    banners = editor.success_messages(MSG_DRAFT_SAVED) if editor.save_went_through() else editor.editbar_texts()
    editor.evidence("143276 editor edit saved as draft")
    assert editor.save_went_through(), f"the Editor's edit + Save Draft did not go through: {editor.save_outcome()}"
    assert has(banners, MSG_DRAFT_SAVED), f"edit + Save Draft showed {banners}"
    editor.open_entry_en(entry.code)
    assert editor.text_value(K_SUB_SECTOR) == edited, f"the edit did not persist: {editor.text_value(K_SUB_SECTOR)!r}"

    # Step 4 — Publish -> Published.
    pinned(editor, ROLE_EDITOR)
    editor.click_publish()
    banners = editor.success_messages(MSG_SAVED_AND_PUBLISHED) if editor.save_went_through() else editor.editbar_texts()
    editor.evidence("143276 editor published")
    assert editor.save_went_through(), f"the Editor's Publish did not go through: {editor.save_outcome()}"
    assert has(banners, MSG_SAVED_AND_PUBLISHED), f"Publish showed {banners}"
    badge = editor.wait_status(entry, ("Published", "Inactive"))
    editor.open_entry_en(entry.code)
    status = editor.current_status()
    allure.attach(f"list badge {badge!r}\nediting bar {editor.editbar_texts()}", name="status after Publish")
    assert status == "Published", f"after Publish the record status is {status!r} (badge {badge!r}), not Published"
    trail = history(editor, entry)
    assert trail, "the published record has no History trail"


# ===========================================================================
# 143278 — Site Content Author creates a Draft
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Author can log in and create a Draft Business Opportunity record")
@_markers("143278")
def test_author_creates_draft_record(page, disposable_e):
    # Azure TC 143278 | PBI 130697 | account: Site Content Author (156492).
    author = e_login(page, ROLE_AUTHOR)
    assert author.total_entry_count() is not None, "the Author's Opportunity Management screen shows no entry list"
    author.open_create_form_en()
    buttons = author.form_buttons() if hasattr(author, "form_buttons") else []
    title = e_name("143278", "Author draft")
    data = OpportunityAdminPage.default_data(title, active_status=False)
    entry = create_opportunity_e(author, disposable_e, data, publish=False, role=ROLE_AUTHOR)
    assert has(author.create_banners, MSG_DRAFT_SAVED), f"no {MSG_DRAFT_SAVED!r}: {author.create_banners}"
    author.open_list_all()
    status = author.row_status_of(entry)
    allure.attach(f"buttons {buttons}\nstatus {author.row_status_raw(entry)!r}", name="Author create outcome")
    assert status == "Draft", f"the Author's saved record shows status {author.row_status_raw(entry)!r}, not Draft"


# ===========================================================================
# 143279 — Site Content Author cannot directly Publish
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Author is denied the ability to directly Publish a Business Opportunity record")
@_markers("143279")
def test_author_cannot_publish_directly(page, disposable_e):
    # Azure TC 143279 | PBI 130697 | account: Site Content Author (156492).
    author = e_login(page, ROLE_AUTHOR)
    title = e_name("143279", "Author no publish")
    data = OpportunityAdminPage.default_data(title, active_status=False)
    entry = create_opportunity_e(author, disposable_e, data, publish=False, role=ROLE_AUTHOR)

    # Step 2 — open the Draft record.
    author.open_entry_en(entry.code)
    assert author.current_status() == "Draft", f"editing bar: {author.editbar_texts()}"
    # Step 3 — the Publish action is not available to the Author.
    form_buttons = _form_button_labels(author)
    author.open_list_all()
    row_actions = author.row_actions(entry)
    author.evidence("143279 author draft list")
    allure.attach(f"form buttons {form_buttons}\nrow actions {row_actions}", name="Author's publish controls")
    assert "Publish" not in form_buttons, f"PRODUCT: the Author's form offers 'Publish': {form_buttons}"
    assert "publish" not in row_actions and "approve" not in row_actions, (
        f"PRODUCT: the Author's row offers a publish/approve action: {row_actions}")
    # Step 4 — status remains Draft.
    assert author.row_status_of(entry) == "Draft", f"status is {author.row_status_raw(entry)!r}, not Draft"


def _form_button_labels(admin) -> list[str]:
    names = []
    for button in admin._form().locator("button").all():
        try:
            if button.is_visible():
                label = button.inner_text().strip()
                if label:
                    names.append(label + ("" if button.is_enabled() else " [disabled]"))
        except Exception:  # noqa: BLE001 — detached node
            continue
    return names


# ===========================================================================
# 143281 — QC Admin Reviewer (= Form Manager) denied content authoring
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A QC Admin Reviewer is denied access to Business Opportunity content authoring")
@_markers("143281")
def test_qc_admin_reviewer_denied_authoring(page):
    # Azure TC 143281 | "QC Admin Reviewer" = the Form Manager role (user decision 2026-10-07).
    # Step 1 — login succeeds.
    admin = e_login(page, ROLE_QC_ADMIN_REVIEWER)
    user_id = admin._pinned_user_id
    # Step 2 — the Object Authoring index must not offer Business Opportunity authoring.
    admin.open(control_panel_url("/en/web/qatar-chamber/object-authoring"))
    admin.page.wait_for_load_state("load")
    admin.page.wait_for_timeout(5000)
    menu = admin.page.locator('a[href$="/manage-business-opportunity"], a[href*="/manage-business-opportunity?"]')
    menu_visible = menu.count() > 0 and menu.first.is_visible()
    index_row_text = menu.first.locator("xpath=..").inner_text() if menu.count() else ""
    admin.evidence("143281 form manager object-authoring index")
    # Step 3 — direct navigation to the content creation URL.
    response = admin.page.goto(control_panel_url("/en/web/qatar-chamber/manage-business-opportunity"),
                               wait_until="load", timeout=90000)
    admin.page.wait_for_timeout(6000)
    def _visible(selector: str) -> int:  # a hidden template node is not an exposed control
        return sum(1 for n in admin.page.locator(selector).all() if n.is_visible())

    controls = {
        "form_fields": _visible('[name^="ObjectField_"]:not([type="hidden"])'),
        "save_or_publish": _visible('button:has-text("Save as Draft"), button:has-text("Publish"), '
                                    'button:has-text("Submit for Review")'),
        "add_new": _visible('text="+ Add New"'),
        "row_edit_links": _visible('a[href*="editEntry="]'),
        "row_delete": _visible("[data-qc-oel-delete]"),
    }
    body = " ".join(admin.page.locator("body").inner_text().split())
    denied_text = "Access Denied" in body or "not have permission" in body
    admin.evidence("143281 form manager direct manage URL")
    evidence = {"userId": user_id, "menu_visible": menu_visible, "index_row": index_row_text,
                "status": response.status if response else None, "url": admin.page.url, "controls": controls,
                "denied_text": denied_text, "body_head": body[:600]}
    allure.attach(repr(evidence), name="Form Manager access evidence")
    # Step 4 — no content creation / edit controls exposed.
    exposed = {k: v for k, v in controls.items() if v}
    assert not exposed, f"PRODUCT: the QC Admin Reviewer (Form Manager) sees authoring controls: {exposed}; {evidence}"
    problems = []
    if menu_visible:
        problems.append(f"the Object Authoring index shows a Business Opportunity entry ({index_row_text!r})")
    if not (denied_text or (response and response.status in (403, 404))):
        problems.append(f"direct URL shows no access-denied/forbidden page (HTTP {evidence['status']})")
    assert not problems, "PRODUCT (no controls exposed, but): " + "; ".join(problems)
