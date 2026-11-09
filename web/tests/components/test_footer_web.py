"""
web/tests/components/test_footer_web.py — Site Footer & Social Media Icons
(PBI 129366 / QC-GBL-004), Web platform.

Source: 18 approved, Automation-tagged, Web-platform cases handed off for
this PBI (ADO 130961-130976, 130992-130994). The 13 Control_Panel-tagged
cases for this same PBI are scripted separately in the sibling
test_footer_control_panel.py.

See web/pages/components/footer_component.py's docstring for the full
CLI-first extraction log and every real, live finding referenced below (each
honestly asserted per its case's exact stated wording, never silently
adjusted). Headline findings that shape the tests here:
  - The footer logo, ALL 18 nav-column links, and all 3 legal/bottom-bar
    links are same-tab/internal on this dev instance — ZERO are configured
    external (`target="_blank"`). ADO 130964 has no live element to exercise
    this session; it is `skip`-marked at runtime (via a dynamic count check,
    not a hardcoded assumption) rather than faking a pass against an
    internal link.
  - ADO 130966 (Quick Links column hidden when zero active links), 130975/
    130992 (default-language fallback for a missing translation), and
    130976 (disabling one element hides only that element) each require a
    CMS-side precondition (toggling content inactive / removing a
    translation) that this session cannot arrange — TEST_USER/TEST_PASSWORD
    are blank in .env (see footer_admin_component.py's docstring) and no
    Playwright MCP fallback is available either. Each is `skip`-marked with
    a concrete reason per automation-standards.md's Result-integrity rule
    (only the CMS-side SETUP step is gated, per the task's own instruction —
    the frontend read methods these would use are real, not TODO).
    UPDATE 2026-10-21 (QA lead decision): 130975/130992/130976 now run on
    disposable QCTEST records (web/tests/conftest.py `qctest_records`).
    130976 runs fully (copyright excepted, see its docstring); 130975/130992
    skip at runtime with the observed reason when the CMS cannot store a
    missing Arabic translation; 130966 stays skipped (needs real records).
  - ADO 130971/130994 (newsletter backend-error message) found the LIVE
    error text reads "Service temporarily unavailable. Please try again
    later." (EN) / "الخدمة غير متاحة مؤقتاً. يرجى المحاولة لاحقاً." (AR) — NOT
    the case's stated "Unable to process your subscription. Please try
    again later." Scripted per the case's exact stated EN wording regardless
    (a real, disclosed mismatch that will honestly fail, not silently
    corrected) — see web/pages/components/newsletter_subscription_component.py's
    docstring for the full finding.
  - The newsletter section INSIDE the footer (ADO 130969, 130970, 130971,
    130993, 130994) is the exact same live DOM node already owned by
    NewsletterSubscriptionComponent (PBI 129566) — composed directly here
    rather than duplicating its locators in footer_component.py, per
    automation-standards.md's redundancy rule.
"""

import json
import uuid

import allure
import pytest

from cms.pages.components.qctest_record_admin import (
    PNG_FIXTURE as QCTEST_PNG,
    BottomBarLinkQctest,
    FooterNavLinkQctest,
    QuickLinkQctest,
    SocialIconQctest,
)
from web.pages.components.footer_component import FooterComponent
from web.pages.components.newsletter_subscription_component import NewsletterSubscriptionComponent

PBI = "129366"


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Footer renders all sections on every page")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The footer renders all sections on every page")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130961")
def test_footer_renders_all_sections_on_every_page(page):
    # ADO-130961 | PBI 129366
    # Arrange
    footer = FooterComponent(page)

    # Act
    with allure.step("Navigate to a page of the Qatar Chamber website"):
        footer.open_home()

    with allure.step("Scroll to the bottom of the page"):
        footer.scroll_to_footer()
        sections = footer.rendered_sections()

    # Assert
    assert footer.is_footer_visible()
    assert sections["logo"], "expected the Qatar Chamber logo in the footer"
    assert sections["about_text"], "expected the footer description text"
    assert sections["social_label"], "expected the Social Media Label"
    assert sections["social_icons"], "expected at least one social icon"
    assert sections["nav_columns"], "expected at least one navigation column"
    assert sections["quick_links_column"], "expected the Quick Links column"
    assert sections["newsletter_section"], "expected the newsletter section"
    assert sections["copyright_bar"], "expected the copyright bar"


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Footer logo redirects to Home")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking the footer logo redirects to the Home Page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130962")
def test_footer_logo_click_redirects_to_home_page(page):
    # ADO-130962 | PBI 129366
    # Arrange
    footer = FooterComponent(page)

    # Act
    with allure.step("Scroll to the footer on a non-home page (Contact Us)"):
        footer.open_contact_us()
        footer.scroll_to_footer()
        logo_visible = footer.is_logo_visible()

    with allure.step("Click the Qatar Chamber footer logo"):
        footer.click_logo()

    # Assert
    assert logo_visible, "expected the footer logo visible on a non-home page"
    assert footer.current_url().rstrip("/").endswith("/home"), (
        f"expected redirect to the Home Page, got {footer.current_url()}"
    )


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Internal footer nav link opens in same tab")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An internal footer navigation link opens in the same tab")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130963")
def test_internal_footer_nav_link_opens_in_same_tab(page):
    # ADO-130963 | PBI 129366
    # Arrange
    footer = FooterComponent(page)

    # Act
    with allure.step("Scroll to the footer navigation column"):
        footer.open_home()
        footer.scroll_to_footer()

    with allure.step("Click the internal 'About Us' link in the About Qatar Chamber column"):
        result = footer.click_nav_link("About Qatar Chamber", "About Us")

    # Assert
    assert not result["opened_new_tab"], "expected the internal link to open in the SAME tab"
    assert result["url"].rstrip("/").endswith("/about-us"), (
        f"expected navigation to the configured target, got {result['url']}"
    )


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("External footer nav link opens in new tab")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An external footer navigation link opens the configured target URL in a new browser tab")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130964")
def test_external_footer_nav_link_opens_in_new_tab(page):
    # ADO-130964 | PBI 129366
    # Arrange
    footer = FooterComponent(page)

    # Act
    with allure.step("Scroll to the footer navigation column"):
        footer.open_home()
        footer.scroll_to_footer()
        external_count = footer.external_nav_link_count()

    if external_count == 0:
        pytest.skip(
            "No footer navigation link is currently configured as external "
            "(target=\"_blank\") on this dev instance — confirmed live via a full "
            "attribute dump of all 18 nav-column links (see footer_component.py's "
            "docstring). A real content-configuration gap, not a locator problem; "
            "nothing to honestly exercise this case against right now."
        )

    with allure.step("Click an external footer navigation link"):
        popup_url = footer.click_first_external_nav_link_and_capture_popup_url()

    # Assert
    assert popup_url, "expected the external link to open a new tab with a real URL"


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Quick Links column renders heading and active links")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Quick Links column renders its heading and active quick links")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130965")
def test_quick_links_column_renders_heading_and_active_links(page):
    # ADO-130965 | PBI 129366
    # Arrange
    footer = FooterComponent(page)

    # Act
    with allure.step("Scroll to the footer with active quick links configured"):
        footer.open_home()
        footer.scroll_to_footer()

    with allure.step("Observe the Quick Links column"):
        column_visible = footer.is_quick_links_column_visible()
        heading = footer.quick_links_heading_text()
        labels = footer.quick_link_labels()

    # Assert
    assert column_visible, "expected the Quick Links column visible"
    assert heading == "Quick Links"
    assert labels, "expected at least one active quick link listed"
    assert all(label.strip() for label in labels), "a quick link had a blank label"


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Quick Links column hidden when no active quick links")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Quick Links column is hidden when no quick links are active")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130966")
@pytest.mark.tc_130966
@pytest.mark.xdist_group("quick_link_real_rows")
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_quick_links_column_hidden_when_no_active_quick_links(page, real_records):
    """ADO-130966 | PBI 129366.

    Precondition (QA lead instruction 2026-10-21, reversible real writes):
    zero ACTIVE Quick Links cannot be reached with a QCTEST record (it can
    only add one), so EVERY Quick Link record that is Active right now (read
    off the stored list at run time -- 8 on 2026-10-21: QC-QL-1, -2, -7..-11
    and "Partners") gets Active Status unticked and is submitted in place on
    the saved TEST_USER session (admin; the Editor login was locked that
    day; a content precondition, not a workflow case). Each record is
    snapshotted (JSON + form screenshot) first; `real_records` re-ticks and
    verifies every one in teardown. Public reads: fresh logged-out `page`."""
    footer = FooterComponent(page)
    ql = {"slug": "quick-link", "plural": "quicklinks", "label": "Active Status", "api_field": "activeStatus"}

    with allure.step("Baseline (logged out): the Quick Links column renders"):
        footer.open_home_settled_anonymous()
        assert footer.is_quick_links_column_visible(), "baseline: Quick Links column not rendered before the change"

    with allure.step("CMS: set Active Status = False on every active Quick Link and publish"):
        active = real_records.codes_where(ql["slug"], ql["plural"], "activeStatus", True, status="approved")
        allure.attach(json.dumps(active), name="active quick links before", attachment_type=allure.attachment_type.JSON)
        assert active, "precondition: no active Quick Link to deactivate"
        for code in active:
            real_records.change(code=code, value=False, **ql)
        still = real_records.codes_where(ql["slug"], ql["plural"], "activeStatus", True, status="approved")
        assert still == [], f"precondition not reached: still active {still}"

    with allure.step("Load any public page and inspect the footer (logged out, polled up to 3 min)"):
        def _hidden() -> bool:
            footer.open_home_settled_anonymous()
            return not footer.is_quick_links_column_visible()

        hidden = _poll_public(_hidden)
        allure.attach(page.screenshot(full_page=True), name="public footer, zero active quick links",
                      attachment_type=allure.attachment_type.PNG)

    # Assert
    assert hidden, "expected the Quick Links column hidden when no quick links are active (3 min poll)"


def _poll_public(predicate, timeout: float = 180.0, poll: float = 10.0) -> bool:
    """Public propagation poll (QA lead: a change landing within 3 min is fine)."""
    from core.utils.waits import WaitTimeoutError, wait_until

    try:
        wait_until(predicate, timeout=timeout, poll=poll)
        return True
    except WaitTimeoutError:
        return False


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Clicking a quick link redirects to its configured URL")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking a quick link redirects to its configured URL")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130967")
def test_clicking_quick_link_redirects_to_configured_url(page):
    # ADO-130967 | PBI 129366
    # Arrange
    footer = FooterComponent(page)

    # Act
    with allure.step("Scroll to the footer Quick Links column"):
        footer.open_home()
        footer.scroll_to_footer()

    with allure.step("Click the active 'Contact Us' quick link"):
        result = footer.click_quick_link("Contact Us")

    # Assert
    assert not result["opened_new_tab"], "expected this quick link configured to open in the same tab"
    assert result["url"].rstrip("/").endswith("/contact-us"), (
        f"expected redirect to the configured URL, got {result['url']}"
    )


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Social media icon opens official channel in new tab")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking a social media icon opens the official Qatar Chamber channel in a new tab")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130968")
def test_clicking_social_icon_opens_official_channel_in_new_tab(page):
    # ADO-130968 | PBI 129366
    # Arrange
    footer = FooterComponent(page)

    # Act
    with allure.step("Scroll to the footer social icons row"):
        footer.open_home()
        footer.scroll_to_footer()
        social_label_visible = footer.is_social_label_visible()

    with allure.step("Click the Facebook social media icon"):
        popup_url = footer.click_social_icon_and_capture_popup_url("Facebook")

    # Assert
    assert social_label_visible, "expected the 'Follow us on Social Media' label above the icons"
    assert "facebook.com/qatarchamber" in popup_url.lower(), (
        f"expected the official Qatar Chamber Facebook channel, got {popup_url}"
    )


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Newsletter subscription success confirmation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Subscribing with a valid email shows a success confirmation")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.newsletter
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130969")
def test_newsletter_valid_email_shows_success_confirmation(page):
    # ADO-130969 | PBI 129366
    # Arrange — composes NewsletterSubscriptionComponent (see module docstring).
    newsletter = NewsletterSubscriptionComponent(page)
    test_email = "footer.valid.subscriber@example.com"

    # Act
    with allure.step("Scroll to the footer newsletter section"):
        newsletter.open_home()
        newsletter.scroll_to_widget()
        heading_visible = newsletter.is_widget_visible()
        email_visible = newsletter.is_email_input_visible()
        subscribe_visible = newsletter.is_subscribe_button_visible()

    with allure.step(f"Enter a valid email ('{test_email}') and click Subscribe"):
        newsletter.fill_email(test_email)
        newsletter.click_subscribe()
        newsletter.wait_for_message()

    # Assert
    assert heading_visible and email_visible and subscribe_visible, (
        "expected the newsletter section's heading, email input, and Subscribe button visible"
    )
    assert not newsletter.is_message_error_state()
    assert newsletter.message_text() == "You have successfully subscribed to our newsletter."


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Newsletter empty/invalid email inline validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Submitting an empty or invalid email shows an inline validation error")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.newsletter
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130970")
def test_newsletter_invalid_email_shows_inline_validation_error(page):
    # ADO-130970 | PBI 129366
    # Arrange
    newsletter = NewsletterSubscriptionComponent(page)
    invalid_email = "not-an-email"

    # Act
    with allure.step("Scroll to the newsletter section"):
        newsletter.open_home()
        newsletter.scroll_to_widget()

    with allure.step(f"Enter an invalid email ('{invalid_email}') and click Subscribe"):
        newsletter.fill_email(invalid_email)
        newsletter.click_subscribe()
        newsletter.wait_for_message()

    # Assert
    assert newsletter.is_message_error_state()
    assert newsletter.message_text() == "Please enter a valid email address."


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Newsletter backend error message")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A newsletter backend error displays the appropriate error message")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.newsletter
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130971")
def test_newsletter_backend_error_displays_error_message(page):
    # ADO-130971 | PBI 129366
    # Real finding (see NewsletterSubscriptionComponent's docstring): the live
    # error text reads "Service temporarily unavailable. Please try again
    # later.", not this case's stated wording — asserted per the case's exact
    # stated wording regardless (a real, disclosed mismatch, not silently
    # corrected).
    # Arrange
    newsletter = NewsletterSubscriptionComponent(page)
    test_email = "footer.backend.failure@example.com"

    # Act
    with allure.step("Scroll to the newsletter section"):
        newsletter.open_home()
        newsletter.scroll_to_widget()

    with allure.step("Force the subscribe backend call to fail"):
        newsletter.simulate_subscribe_backend_failure()

    with allure.step(f"Enter a valid email ('{test_email}') and click Subscribe"):
        newsletter.fill_email(test_email)
        newsletter.click_subscribe()
        newsletter.wait_for_message()

    # Assert
    assert newsletter.is_message_error_state()
    assert newsletter.message_text() == "Unable to process your subscription. Please try again later."


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Copyright bar text and bottom bar links")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The copyright bar displays copyright text and bottom bar links correctly")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130972")
def test_copyright_bar_displays_text_and_links_correctly(page):
    # ADO-130972 | PBI 129366
    # Arrange
    footer = FooterComponent(page)

    # Act
    with allure.step("Scroll to the very bottom of the footer"):
        footer.open_home()
        footer.scroll_to_footer()

    with allure.step("Observe the copyright bar"):
        copyright_text = footer.copyright_text()
        legal_labels = footer.legal_link_labels()
        positions = footer.copyright_and_legal_positions()

    # Assert
    assert footer.is_copyright_bar_visible()
    assert "Qatar Chamber" in copyright_text and "All Rights Reserved" in copyright_text
    assert legal_labels == ["Accessibility", "Privacy Policy", "Terms of Service"]
    assert positions, "expected both copyright text and legal links to have a measurable position"
    assert positions["copyright_x"] < positions["legal_x"], (
        "expected copyright text on the left and the legal links to its right"
    )


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Back to Top scrolls the page to the top")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking the Back to Top icon scrolls the page to the top")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130973")
def test_back_to_top_scrolls_page_to_the_top(page):
    # ADO-130973 | PBI 129366
    # Arrange
    footer = FooterComponent(page)

    # Act
    with allure.step("Scroll to the bottom of the page"):
        footer.open_home()
        footer.scroll_to_bottom()
        scroll_before = footer.scroll_position()

    with allure.step("Click the Back to Top icon"):
        footer.click_back_to_top()
        footer.wait_for_scroll_top()
        scroll_after = footer.scroll_position()

    # Assert
    assert scroll_before > 0, "expected the page scrolled down before clicking Back to Top"
    assert scroll_after == 0, "expected the page scrolled back to the very top"


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Default-language fallback for a missing translation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The footer falls back to the default language when a translation is missing")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130975")
@pytest.mark.tc_130975
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_footer_falls_back_to_default_language_when_translation_missing(page, qctest_records):
    """ADO-130975 | PBI 129366.

    Precondition (QA lead decision 2026-10-21): a disposable QCTEST footer
    record Published + Active through Object Authoring as TEST_USER (admin;
    Publish goes live directly -- the Editor login was refused that day),
    deleted in teardown. The case's own example -- a nav-link title with no
    Arabic -- is tried first; when the CMS refuses it (every footer TITLE's
    Arabic twin is required), the bottom-bar link URL, the one footer field
    whose Arabic is optional, carries the missing translation instead.
    Public reads: fresh logged-out `page`, EN then AR."""
    footer = FooterComponent(page)

    with allure.step("Configure a footer field with no Arabic translation while other fields are translated"):
        ev = _missing_translation_evidence(footer, qctest_records, "130975", with_en=True)
    with allure.step("Switch the site language to Arabic and scroll to the footer"):
        allure.attach(json.dumps(ev, ensure_ascii=False, indent=1), name="130975 evidence",
                      attachment_type=allure.attachment_type.JSON)

    # Assert
    if ev["route"].startswith("nav-link"):
        assert ev["en"] and ev["en"][0][0] == ev["expected_text"], f"EN footer: {ev.get('en')}"
        assert ev["ar"], "the nav link with no Arabic title did not render on the AR footer (3 min)"
        assert ev["ar"][0][0] == ev["expected_text"], (
            f"AR footer shows {ev['ar'][0][0]!r} for a title with no Arabic; expected the default "
            f"(English) text {ev['expected_text']!r}")
    else:
        _skip_unless_arabic_missing(ev)
        assert ev["en"] and ev["en"][0][1] == ev["expected_href_part"], f"EN footer link: {ev.get('en')}"
        assert ev["ar"], "the QCTEST bottom-bar link did not render on the AR footer (3 min)"
        assert ev["ar"][0][1] == ev["expected_href_part"], (
            f"AR footer link href is {ev['ar'][0][1]!r}; expected the default-language URL "
            f"{ev['expected_href_part']!r} instead of a blank or broken value")


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Disabling an individual footer element hides only that element")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Disabling an individual footer element hides only that element")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130976")
@pytest.mark.tc_130976
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_disabling_individual_footer_element_hides_only_that_element(page, qctest_records):
    """ADO-130976 | PBI 129366.

    Precondition (QA lead decision 2026-10-21): ONE disposable QCTEST record
    per footer element type -- nav link (About Qatar Chamber column), quick
    link (carrying the real column heading), social icon (Show on Home off)
    and bottom-bar link -- Published + Active through Object Authoring as
    TEST_USER (admin; Publish goes live directly), deleted in teardown. Each
    carries one shared href marker. POSITIVE CONTROL: all four must first
    render for a logged-out visitor; then each is set inactive and published,
    and the whole rest of the footer must be unchanged.
    NOT EXERCISED: the copyright text. CopyrightBar holds ONE real record
    (QC-CR-1); a second QCTEST copyright record could displace the real text
    on the live footer, and the real one may not be touched -- only its
    continued presence is asserted."""
    tag = uuid.uuid4().hex[:6]
    shared = f"qctest-130976-{tag}"
    ledger = qctest_records
    footer = FooterComponent(page)
    nav = FooterNavLinkQctest(ledger.page)
    quick = QuickLinkQctest(ledger.page)
    social = SocialIconQctest(ledger.page)
    bottom = BottomBarLinkQctest(ledger.page)
    created = []

    def _mk(kind: str) -> str:
        return f"QCTEST-130976-{kind}-{tag}"

    with allure.step("In the CMS, create one QCTEST nav link, quick link, social icon and bottom bar link (Active)"):
        for admin, kind, values in (
            (nav, "nav", {"title": (_mk("nav"), f"{_mk('nav')} عربي"), "url": (f"https://example.com/{shared}-nav",) * 2,
                          "column": "About Qatar Chamber", "column_number": "1", "order": "9900",
                          "active": True}),
            (quick, "quick", {"heading": QuickLinkQctest.REAL_HEADING,
                              "title": (_mk("quick"), f"{_mk('quick')} عربي"),
                              "url": (f"https://example.com/{shared}-quick",) * 2, "order": "9900", "active": True}),
            (bottom, "bottom", {"title": (_mk("bottom"), f"{_mk('bottom')} عربي"),
                                "url": (f"https://example.com/{shared}-bottom",) * 2, "order": "9900", "active": True}),
            (social, "social", {"platform": "Flickr", "image": QCTEST_PNG,
                                "alt": (_mk("social"), f"{_mk('social')} عربي"),
                                "url": (f"https://example.com/{shared}-social",) * 2, "new_tab": True,
                                # Home Display Order must be >= 1 even with Show on Home off
                                # (live refusal 2026-10-21 when left blank).
                                "order": "9900", "show_on_home": False, "home_order": "9900", "active": True,
                                "platform_name": ("QCTEST Flickr", "QCTEST فليكر")}),
        ):
            created.append((admin, ledger.create(admin, values, _mk(kind)), _mk(kind)))

    with allure.step("Positive control: all four QCTEST elements render for a logged-out visitor"):
        shown_all, snap_on = footer.poll_public("en", lambda s: len(footer.links_with_marker(s, shared)) == 4)
        shown = footer.links_with_marker(snap_on, shared)
        baseline = footer.without_marker(snap_on, shared)

    with allure.step("Set each QCTEST element to inactive and publish"):
        for admin, code, marker in created:
            ledger.set_active(admin, code, marker, False)

    with allure.step("Load any page and scroll to the footer"):
        hidden_all, snap_off = footer.poll_public("en", lambda s: not footer.links_with_marker(s, shared))
        still = footer.links_with_marker(snap_off, shared)
        rest = footer.without_marker(snap_off, shared)

    allure.attach(json.dumps({"shown": shown, "still_shown_after_inactive": still, "baseline": baseline,
                              "after": rest}, ensure_ascii=False, indent=1),
                  name="130976 evidence", attachment_type=allure.attachment_type.JSON)

    # Assert
    assert shown_all, f"positive control: not all 4 QCTEST elements rendered while Active (3 min): {shown}"
    assert hidden_all, f"disabled QCTEST elements still shown on the footer: {still}"
    assert rest == baseline, "other (active) footer elements changed after disabling the QCTEST ones"
    assert rest["copyright"], "the copyright text is no longer shown"


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Default-language fallback for a missing translation (Arabic)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The footer displays the default language when no Arabic translation is available")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130992")
@pytest.mark.tc_130992
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_footer_displays_default_language_when_no_arabic_translation_available(page, qctest_records):
    """ADO-130992 | PBI 129366 -- Arabic duplicate of ADO-130975, its own
    QCTEST record, same precondition route and account (see 130975)."""
    footer = FooterComponent(page)

    with allure.step("إعداد أحد حقول التذييل بدون ترجمة عربية (QCTEST)"):
        ev = _missing_translation_evidence(footer, qctest_records, "130992", with_en=False)
    with allure.step("تبديل لغة الموقع إلى العربية والتمرير إلى التذييل"):
        allure.attach(json.dumps(ev, ensure_ascii=False, indent=1), name="130992 evidence",
                      attachment_type=allure.attachment_type.JSON)

    # Assert
    assert ev["ar_dir"] == "rtl", f"expected the Arabic site (RTL), html dir={ev['ar_dir']!r}"
    assert ev["ar"], "the QCTEST footer element did not render on the AR footer (3 min)"
    if ev["route"].startswith("nav-link"):
        assert ev["ar"][0][0] == ev["expected_text"], (
            f"AR footer shows {ev['ar'][0][0]!r}; expected the default (English) text {ev['expected_text']!r}")
    else:
        _skip_unless_arabic_missing(ev)
        assert ev["ar"][0][1] == ev["expected_href_part"], (
            f"AR footer link href is {ev['ar'][0][1]!r}; expected the default-language URL "
            f"{ev['expected_href_part']!r} instead of a blank or broken value")


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Newsletter empty/invalid email validation (Arabic)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A validation message appears for an empty/invalid email in the newsletter section (Arabic)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.newsletter
@pytest.mark.bilingual
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130993")
def test_newsletter_invalid_email_shows_validation_message_in_arabic(page):
    # ADO-130993 | PBI 129366 — Arabic duplicate of ADO-130970: same flow,
    # Arabic UI language active first. Real, CLI-confirmed live message text
    # (see module docstring): "يرجى إدخال عنوان بريد إلكتروني صالح." — genuinely
    # localized, not the English string re-rendered.
    # Arrange
    newsletter = NewsletterSubscriptionComponent(page)
    invalid_email = "not-an-email"

    # Act
    with allure.step("Activate Arabic UI language and scroll to the newsletter section"):
        newsletter.open_home_arabic()
        newsletter.scroll_to_widget()
        direction = newsletter.page_direction()

    with allure.step(f"Enter an invalid email ('{invalid_email}') and click Subscribe"):
        newsletter.fill_email(invalid_email)
        newsletter.click_subscribe()
        newsletter.wait_for_message()

    # Assert
    assert direction == "rtl", "expected the Arabic UI language active"
    assert newsletter.is_message_error_state()
    assert newsletter.message_text() == "يرجى إدخال عنوان بريد إلكتروني صالح."


@allure.epic("GLOBAL")
@allure.feature("Site Footer & Social Media Icons")
@allure.story("Newsletter backend error message (Arabic)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An error message appears when the newsletter subscription backend fails (Arabic)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.newsletter
@pytest.mark.bilingual
@pytest.mark.pbi_129366
@pytest.mark.traceability("ADO-130994")
def test_newsletter_backend_error_displays_error_message_in_arabic(page):
    # ADO-130994 | PBI 129366 — Arabic duplicate of ADO-130971: same flow,
    # Arabic UI language active first. Real, CLI-confirmed live message text
    # (see NewsletterSubscriptionComponent's docstring): "الخدمة غير متاحة
    # مؤقتاً. يرجى المحاولة لاحقاً." — genuinely localized. The case gives no
    # official Arabic wording to assert against, so this asserts the real,
    # confirmed live string rather than inventing one.
    # Arrange
    newsletter = NewsletterSubscriptionComponent(page)
    test_email = "footer.backend.failure.ar@example.com"

    # Act
    with allure.step("Activate Arabic UI language and scroll to the newsletter section"):
        newsletter.open_home_arabic()
        newsletter.scroll_to_widget()
        direction = newsletter.page_direction()

    with allure.step("Force the subscribe backend call to fail"):
        newsletter.simulate_subscribe_backend_failure()

    with allure.step(f"Enter a valid email ('{test_email}') and click Subscribe"):
        newsletter.fill_email(test_email)
        newsletter.click_subscribe()
        newsletter.wait_for_message()

    # Assert
    assert direction == "rtl", "expected the Arabic UI language active"
    assert newsletter.is_message_error_state()
    assert newsletter.message_text() == "الخدمة غير متاحة مؤقتاً. يرجى المحاولة لاحقاً."


# ── Disposable-record helpers for ADO 130975 / 130992 (QA lead, 2026-10-21) ──
# Footer link URLs must start with https:// or / (live refusal 2026-10-21:
# "Bottom Link URL is not a valid URL — start it with https:// for another
# site, or with / for a page on this one."), so QCTEST links point at
# https://example.com/qctest-<tc>-<tag>-<kind>, which also serves as the marker.
def _nav_link_without_arabic(ledger, tc: str, tag: str) -> dict:
    """Try the case's own example first: a QCTEST footer nav link whose
    Arabic title is left empty, Published (TEST_USER) and Active. Returns
    {"code", "marker", "href", "blocked", "messages"}; "code" is "" when the
    CMS refused the save."""
    admin = FooterNavLinkQctest(ledger.page)
    marker = f"QCTEST-{tc}-nav-noar-{tag}"
    href = f"https://example.com/qctest-{tc}-{tag}-nav"
    before = set(admin.codes_listed())
    admin.open_create_form()
    admin.fill_values({"title": (marker, None), "url": (href, href), "column": "About Qatar Chamber",
                       "column_number": "1", "order": "9900", "active": True})
    ledger.log_attempt(admin, marker, "nav link with EMPTY Arabic title -- Publish may be refused")
    blocked = admin.publish_reading_validity()
    messages = list(getattr(admin, "last_click_messages", []))
    code = admin.resolve_new_code(before, marker, timeout=20)
    if code:
        ledger.register(admin, code, marker)
    return {"code": code, "marker": marker, "href": href, "blocked": blocked, "messages": messages}


def _bottom_link_without_arabic_url(ledger, tc: str, tag: str) -> dict:
    """The one footer field whose Arabic twin the CMS does not require
    ("Bottom Link URL — العربية", read live 2026-10-21): a QCTEST bottom-bar
    link with EN + AR titles, the EN URL only, Published + Active."""
    admin = BottomBarLinkQctest(ledger.page)
    marker = f"QCTEST-{tc}-bottom-noar-{tag}"
    title_ar = f"QCTEST-{tc} رابط سفلي {tag}"
    href = f"https://example.com/qctest-{tc}-{tag}-bottom"
    code = ledger.create(admin, {"title": (marker, title_ar), "url": (href, None), "order": "9900",
                                 "active": True}, marker)
    admin.open_code(code)
    return {"code": code, "marker": marker, "title_ar": title_ar, "href": href,
            "form_url_ar": admin.value("url", locale="ar"),
            "stored_url_i18n": admin.stored_i18n(code, "url")}


def _legal_link(snapshot: dict, text: str) -> list:
    return [link for link in snapshot.get("legal", []) if link[0] == text]


def _missing_translation_evidence(footer, ledger, tc: str, with_en: bool) -> dict:
    """Builds the case's precondition on disposable data and reads the public
    footer (logged out). Route 1 is the case's own example (a nav-link title
    left without Arabic); when the CMS refuses that save, route 2 uses the
    only footer field whose Arabic is optional (the bottom-bar link URL).
    Returns everything the test asserts on; asserts nothing itself."""
    tag = uuid.uuid4().hex[:6]
    ev = {"tc": tc}
    attempt = _nav_link_without_arabic(ledger, tc, tag)
    ev["nav_attempt"] = {k: attempt[k] for k in ("code", "marker", "blocked", "messages")}
    if attempt["code"]:
        ev["route"] = "nav-link title (no Arabic)"
        ev["expected_text"] = attempt["marker"]
        ev["expected_href_part"] = attempt["href"]
        find = lambda snap: footer.links_with_marker(snap, attempt["href"])  # noqa: E731
        if with_en:
            ok, snap = footer.poll_public("en", lambda s: bool(find(s)))
            ev["en"] = [link[1:] for link in find(snap)]
        ok, snap = footer.poll_public("ar", lambda s: bool(find(s)))
        ev["ar"] = [link[1:] for link in find(snap)]
        ev["ar_dir"] = snap.get("dir", "")
        return ev
    bottom = _bottom_link_without_arabic_url(ledger, tc, tag)
    ev["route"] = "bottom-bar link URL (no Arabic) -- the nav-link title route was refused by the CMS"
    ev["record"] = bottom
    ev["expected_href_part"] = bottom["href"]
    if with_en:
        ok, snap = footer.poll_public("en", lambda s: bool(_legal_link(s, bottom["marker"])))
        ev["en"] = _legal_link(snap, bottom["marker"])
    ok, snap = footer.poll_public("ar", lambda s: bool(_legal_link(s, bottom["title_ar"])))
    ev["ar"] = _legal_link(snap, bottom["title_ar"])
    ev["ar_dir"] = snap.get("dir", "")
    return ev


def _skip_unless_arabic_missing(ev: dict) -> None:
    """The precondition "a footer field missing its Arabic translation" holds
    only if the STORED record has no Arabic value for it. When the CMS stored
    one anyway, the case cannot be set up with test data: skip, quoting what
    was stored and what the public footer showed."""
    stored = ev["record"].get("stored_url_i18n") or {}
    if stored.get("ar_SA"):
        pytest.skip(
            "Precondition not achievable through Object Authoring (2026-10-21): the nav-link "
            f"title route is refused ({ev['nav_attempt']['messages'] or ev['nav_attempt']['blocked']}); "
            "the only optional Arabic footer field (Bottom Link URL) was saved EMPTY but the CMS "
            f"stored an Arabic value anyway (url_i18n={stored}). Public footer read for the record: "
            f"EN={ev.get('en')} AR={ev.get('ar')}."
        )
    assert stored, f"could not read the stored record to confirm the missing translation: {ev['record']}"
