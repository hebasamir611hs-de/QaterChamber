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

import allure
import pytest

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
    assert footer.current_url().rstrip("/").endswith("/web/qatar-chamber/home"), (
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
    assert result["url"].rstrip("/").endswith("/web/qatar-chamber/about-us"), (
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
@pytest.mark.skip(
    reason=(
        "Requires a CMS precondition (zero active Quick Links configured) that this "
        "session cannot arrange — TEST_USER/TEST_PASSWORD are blank in .env (see "
        "footer_admin_component.py's docstring) and no Playwright MCP fallback is "
        "available either. FooterComponent.is_quick_links_column_visible() is real "
        "and ready to assert against once a real zero-active-links state exists; "
        "only the CMS-side setup step is gated, per this task's own instruction."
    )
)
def test_quick_links_column_hidden_when_no_active_quick_links(page):
    # ADO-130966 | PBI 129366 — see skip reason above.
    # Arrange
    footer = FooterComponent(page)

    # Act — TODO(CMS precondition): configure zero active quick links as a
    # Site Content Editor before this line, once real credentials exist.
    footer.open_home()
    footer.scroll_to_footer()
    column_visible = footer.is_quick_links_column_visible()

    # Assert
    assert not column_visible, "expected the Quick Links column hidden when no quick links are active"


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
    assert result["url"].rstrip("/").endswith("/web/qatar-chamber/contact-us"), (
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
@pytest.mark.skip(
    reason=(
        "Requires a CMS precondition (a footer field, e.g. a nav link title, "
        "configured with no Arabic translation) that this session cannot arrange — "
        "no Site Content Editor credentials available (see footer_admin_component.py's "
        "docstring). Real, live finding: every footer field/label/link on the current "
        "AR homepage IS genuinely translated (confirmed via a full text dump — see "
        "footer_component.py's docstring), so there is no reachable missing-translation "
        "state to honestly assert against this session; only the CMS-side setup step is "
        "gated, per this task's own instruction."
    )
)
def test_footer_falls_back_to_default_language_when_translation_missing(page):
    # ADO-130975 | PBI 129366 — see skip reason above; intentionally no
    # assertion is executed (never fabricate a pass against a fully
    # translated footer, which would not honestly exercise this case).
    pass


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
@pytest.mark.skip(
    reason=(
        "Requires a CMS precondition (setting one nav link, one quick link, one "
        "social icon, the copyright text, and one bottom bar link inactive and "
        "publishing) that this session cannot arrange — no Site Content Editor "
        "credentials available (see footer_admin_component.py's docstring). "
        "FooterComponent.is_nav_link_present() / is_social_icon_present() / "
        "is_legal_link_present() / is_copyright_text_present() are real and ready to "
        "assert with once a real disabled-element state exists; only the CMS-side "
        "toggle step is gated, per this task's own instruction."
    )
)
def test_disabling_individual_footer_element_hides_only_that_element(page):
    # ADO-130976 | PBI 129366 — see skip reason above.
    # Arrange
    footer = FooterComponent(page)

    # Act — TODO(CMS precondition): disable one nav link, one quick link, one
    # social icon, the copyright text, and one bottom bar link as a Site
    # Content Editor before this line, once real credentials exist.
    footer.open_home()
    footer.scroll_to_footer()

    # Assert — each disabled element hidden, all other active elements remain
    # visible/functional (concrete element names filled in once the CMS-side
    # setup step names which ones were disabled).
    assert not footer.is_nav_link_present("About Qatar Chamber", "About Us")
    assert footer.is_quick_links_column_visible(), "expected other active elements to remain visible"


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
@pytest.mark.skip(
    reason=(
        "Arabic duplicate of ADO-130975 — same unreachable CMS precondition (see that "
        "test's skip reason above and footer_component.py's docstring for the live "
        "AR-translation-completeness finding)."
    )
)
def test_footer_displays_default_language_when_no_arabic_translation_available(page):
    # ADO-130992 | PBI 129366 — see skip reason above.
    pass


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
