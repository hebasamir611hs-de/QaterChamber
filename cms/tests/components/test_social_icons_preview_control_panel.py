"""
cms/tests/components/test_social_icons_preview_control_panel.py — PBI 129373
(QC-HOME-004B — Social Media Icons), TC 131148, added 2026-10-15 (Phase 3).

Read-only: the Editor opens the staff Preview of a real, published Social Media
Icon row and compares the social links it renders with the links a logged-out
visitor sees on the live Home Page. Nothing is saved.
"""

from __future__ import annotations

import allure
import pytest

from cms.pages.components.object_authoring_page import ObjectAuthoringPage, STATUS_PUBLISHED
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.tests import authoring_checks as ac
from config.settings import cms_role_credentials, control_panel_url

pytestmark = [pytest.mark.control_panel, pytest.mark.pbi_129373]

SOCIAL_HOSTS = ("facebook", "instagram", "linkedin", "youtube", "x.com", "twitter", "tiktok", "snapchat", "flickr")


def _social_hrefs(page) -> set[str]:
    hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    return {h.rstrip("/") for h in hrefs if any(s in h.lower() for s in SOCIAL_HOSTS)}


@allure.title("CMS preview of the Social Media Icons section matches the published Home Page render")
@pytest.mark.ui
@pytest.mark.tc_131148
def test_social_icons_preview_matches_published(page, browser):
    email, password = cms_role_credentials("Site Content Editor")
    CmsLoginPage(page).ensure_signed_in_as(email, password, control_panel_url("/en/home"))
    oa = ObjectAuthoringPage(page, "social-media-icon")
    oa.open_entries_list()
    rows = page.locator(oa.ENTRIES_TABLE_ROW)
    code = next(
        (rows.nth(i).locator("td").first.inner_text().strip() for i in range(rows.count())
         if oa.row_status_text_by_code(rows.nth(i).locator("td").first.inner_text().strip()) == STATUS_PUBLISHED),
        "",
    )
    assert code, "no Published Social Media Icon row to preview"
    url = oa.row_preview_url_by_code(code)
    assert url, f"row {code} offers no Preview link"
    oa.open(url)
    page.wait_for_load_state("domcontentloaded")
    preview = _social_hrefs(page)
    ctx, anon = ac._anon_page(browser)
    try:
        anon.goto(control_panel_url("/en/home"), wait_until="domcontentloaded")
        anon.wait_for_load_state("load")
        live = _social_hrefs(anon)
    finally:
        ac._close(ctx)
    allure.attach(f"preview={sorted(preview)}\nlive={sorted(live)}", name="social links",
                  attachment_type=allure.attachment_type.TEXT)
    assert preview, "the Preview renders no social links"
    assert live <= preview or preview <= live, (
        f"Preview and the live Home Page render different social links:\n"
        f"only in preview: {sorted(preview - live)}\nonly live: {sorted(live - preview)}"
    )


@allure.title("Leaving the icon form without saving discards the entered values")
@pytest.mark.tc_131174
def test_social_icon_unsaved_changes_discarded(page):
    """TC 131174 (P4). The live form has no Cancel button (read live
    2026-10-15: Save as Draft / Publish only), so the discard is leaving the
    form: values typed into a new entry, page left without saving, the form
    reopens empty and no entry with that alt text exists. Nothing is saved."""
    from cms.pages.components.footer_admin_component import SocialMediaIconAdminPage

    email, password = cms_role_credentials("Site Content Editor")
    CmsLoginPage(page).ensure_signed_in_as(email, password, control_panel_url("/en/home"))
    admin = SocialMediaIconAdminPage(page)
    admin.open_new_entry_form()
    alt = f"QCTEST-131174-discard-{ac._RUN_UID}"
    admin.fill_icon_form(platform="Facebook", alt_text_en=alt, alt_text_ar="تجاهل")
    page.once("dialog", lambda d: d.accept())
    admin.open_new_entry_form()
    assert page.locator('input[name="ObjectField_altText"]').input_value() == "", "the unsaved alt text came back"
    assert page.get_by_role("combobox", name="Platform", exact=True).input_value() == "", "the unsaved Platform came back"
    admin.open_entries_list()
    box = page.locator('input[placeholder^="Search entries"]')
    box.fill(alt)
    box.press("Enter")
    page.wait_for_timeout(4000)
    assert page.locator(f'table tbody tr:has-text("{alt}")').count() == 0, "an entry was created without saving"
