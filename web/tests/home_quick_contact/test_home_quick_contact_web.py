"""
web/tests/home_quick_contact/test_home_quick_contact_web.py — Quick Contact
Us Section (PBI 129390 / QC-HOME-014), Web platform.

Source: 8 approved, Automation-tagged, UI-category, Web-platform cases
handed off for this PBI (ADO TC 136473, 136474, 136475, 136476, 136477,
136478, 136479, 136550). TC 136480/136551 are Control_Panel-tagged and
scripted separately in the sibling test_home_quick_contact_control_panel.py.
TC 136472/136481/136482 are Manual-tagged and explicitly OUT of this run's
scope (not authored here).

Per active/standards.md's Tag-Taxonomy mapping, every case here carries
`GLOBAL` (Service axis -> @pytest.mark.global_) and `UI` (Category axis ->
@pytest.mark.ui) — mirroring the sibling GLOBAL-tagged
test_newsletter_subscription_web.py's marker choice and its `ADO-<id>`
traceability convention (this PBI's cases carry no project-specific
Service/Module code beyond GLOBAL, unlike EVENT/B2B-tagged PBIs). TC 136550
additionally carries `Bilingual`/`Regression` (Axis 5 -> @pytest.mark.bilingual,
Axis 1 -> @pytest.mark.regression) — the only Regression-tagged case in this
batch.

See the sibling home_quick_contact_page.py's docstring for the full
CLI-first extraction log and every real, live finding surfaced while
scripting these (each honestly asserted per its case's exact stated
wording, never silently adjusted) — not repeated in full here.
"""

import allure
import pytest

PBI = "129390"

from web.pages.home_quick_contact.home_quick_contact_page import HomeQuickContactPage


@allure.epic("GLOBAL")
@allure.feature("Quick Contact Us Section")
@allure.story("Responsive at mobile viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Contact Us section is responsive at a 375px mobile viewport (EN)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129390
@pytest.mark.traceability("ADO-136473")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_contact_us_responsive_at_mobile_375(page):
    # ADO-136473 | PBI 129390
    # Arrange
    contact = HomeQuickContactPage(page)

    # Act
    with allure.step("Load the Home Page at 375px viewport"):
        contact.open_home()

    with allure.step("Scroll to the Contact Us section"):
        contact.scroll_to_section()
        single_column = contact.is_single_column_layout()
        has_overflow = contact.has_page_horizontal_overflow()
        map_box = contact.map_container_box()

    with allure.step("Measure the touch targets of every interactive control in the section"):
        name_ok = contact.is_touch_target_ok(contact.NAME_INPUT)
        email_ok = contact.is_touch_target_ok(contact.EMAIL_INPUT)
        category_ok = contact.is_touch_target_ok(contact.CATEGORY_SELECT)
        message_ok = contact.is_touch_target_ok(contact.MESSAGE_TEXTAREA)
        submit_ok = contact.is_touch_target_ok(contact.SUBMIT_BUTTON)
        directions_ok = contact.is_touch_target_ok(contact.DIRECTIONS_LINK)

    # Assert
    assert contact.is_section_visible()
    assert single_column, "expected the section to stack to a single column at 375px"
    assert not has_overflow, "expected no horizontal overflow at 375px"
    assert map_box and map_box["width"] >= 300, "expected the map to render at (near) full section width"
    assert name_ok and email_ok and category_ok and message_ok and submit_ok, (
        "expected every form control's touch target to be >=44px"
    )
    assert directions_ok, (
        "expected the 'Open location in Google Maps' touch target to be >=44px — "
        "live product value is a 38x38px icon-link (see Page-Object docstring)"
    )


@allure.epic("GLOBAL")
@allure.feature("Quick Contact Us Section")
@allure.story("Responsive at tablet viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Contact Us section is responsive at a 768px tablet viewport (EN)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129390
@pytest.mark.traceability("ADO-136474")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_contact_us_responsive_at_tablet_768(page):
    # ADO-136474 | PBI 129390
    # Arrange
    contact = HomeQuickContactPage(page)

    # Act
    with allure.step("Load the Home Page at 768px viewport"):
        contact.open_home()

    with allure.step("Scroll to the Contact Us section"):
        contact.scroll_to_section()
        has_overflow = contact.has_page_horizontal_overflow()
        heading_text = contact.heading_text()

    # Assert
    assert contact.is_section_visible()
    assert not has_overflow, "expected no overlap/truncation/horizontal scroll at 768px"
    assert heading_text.strip(), "expected the section heading to remain legible (non-empty) at 768px"


@allure.epic("GLOBAL")
@allure.feature("Quick Contact Us Section")
@allure.story("Inquiry Category dropdown")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Inquiry Category dropdown shows the correct placeholder and full option list")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129390
@pytest.mark.traceability("ADO-136475")
def test_inquiry_category_dropdown_placeholder_and_options(page):
    # ADO-136475 | PBI 129390
    expected_categories = [
        "Select",
        "General Inquiry",
        "Membership Services",
        "Legal Services",
        "Commercial Directory",
        "Events",
        "B2B Platform",
        "Publications & Research",
        "Tender Submission",
        "Technical Support",
        "Suggestions & Feedback",
        "Other",
    ]
    # Arrange
    contact = HomeQuickContactPage(page)

    # Act
    with allure.step("Load the Home Page and scroll to the Contact Us section"):
        contact.open_home()
        contact.scroll_to_section()

    with allure.step("Read the Inquiry Category dropdown's placeholder and full option list"):
        labels = contact.category_option_labels()

    # Assert
    assert labels == expected_categories, f"expected the exact 11-entry option list, got {labels!r}"


@allure.epic("GLOBAL")
@allure.feature("Quick Contact Us Section")
@allure.story("Form field focus states")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Each form field shows the correct focus state")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129390
@pytest.mark.traceability("ADO-136476")
def test_form_fields_show_visible_focus_state(page):
    # ADO-136476 | PBI 129390
    # See Page-Object docstring: a real, focusable cross-origin map iframe
    # sits between the info column and the form in tab order, so a genuine
    # keyboard Tab walk from page load can't deterministically reach the
    # form. `.focus()` is used as the confirmed equivalent — this project's
    # CSS applies the focus ring via a plain `:focus` selector, verified
    # identical whether reached by a real Tab keypress or by `.focus()`.
    # Arrange
    contact = HomeQuickContactPage(page)

    # Act
    with allure.step("Load the Home Page and scroll to the Contact Us section"):
        contact.open_home()
        contact.scroll_to_section()

    with allure.step("Tab into the Full Name field"):
        contact.focus_field(contact.NAME_INPUT)
        name_outline = contact.field_outline(contact.NAME_INPUT)

    with allure.step("Tab into the Email field"):
        contact.focus_field(contact.EMAIL_INPUT)
        email_outline = contact.field_outline(contact.EMAIL_INPUT)

    with allure.step("Tab into the Message field"):
        contact.focus_field(contact.MESSAGE_TEXTAREA)
        message_outline = contact.field_outline(contact.MESSAGE_TEXTAREA)

    # Assert
    assert name_outline == "rgb(145, 23, 49) solid 2px", f"expected a visible focus outline, got {name_outline!r}"
    assert email_outline == "rgb(145, 23, 49) solid 2px", f"expected a visible focus outline, got {email_outline!r}"
    assert message_outline == "rgb(145, 23, 49) solid 2px", f"expected a visible focus outline, got {message_outline!r}"


@allure.epic("GLOBAL")
@allure.feature("Quick Contact Us Section")
@allure.story("Inline validation error state")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Inline validation error state is visually distinct on empty required fields")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129390
@pytest.mark.traceability("ADO-136477")
def test_empty_required_fields_show_distinct_error_state(page):
    # ADO-136477 | PBI 129390
    # Arrange
    contact = HomeQuickContactPage(page)

    # Act
    with allure.step("Load the Home Page and scroll to the Contact Us section"):
        contact.open_home()
        contact.scroll_to_section()

    with allure.step("Click Send Message with all fields empty"):
        contact.click_submit()

    with allure.step("Inspect the border color and inline error message on each required field"):
        name_border = contact.field_border_color_hex(contact.NAME_INPUT)
        email_border = contact.field_border_color_hex(contact.EMAIL_INPUT)
        category_border = contact.field_border_color_hex(contact.CATEGORY_SELECT)
        message_border = contact.field_border_color_hex(contact.MESSAGE_TEXTAREA)
        name_error = contact.field_error_text(contact.NAME_INPUT)
        email_error = contact.field_error_text(contact.EMAIL_INPUT)
        category_error = contact.field_error_text(contact.CATEGORY_SELECT)
        message_error = contact.field_error_text(contact.MESSAGE_TEXTAREA)

    # Assert
    error_red = "#C0271D"
    assert name_border == error_red and name_error == "Please enter your full name."
    assert email_border == error_red and email_error == "Please enter a valid email address."
    assert category_border == error_red and category_error == "Please select a category."
    assert message_border == error_red and message_error == "Please enter your message."


@allure.epic("GLOBAL")
@allure.feature("Quick Contact Us Section")
@allure.story("Send Message button submission state")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Send Message button shows a disabled/loading state during submission")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129390
@pytest.mark.traceability("ADO-136478")
def test_send_message_button_disabled_during_submission(page):
    # ADO-136478 | PBI 129390
    # Arrange
    contact = HomeQuickContactPage(page)

    # Act
    with allure.step("Load the Home Page and scroll to the Contact Us section"):
        contact.open_home()
        contact.scroll_to_section()

    with allure.step("Fill the form with valid, concrete data"):
        contact.fill_valid_form(
            full_name="QA Automation Test",
            email="qa.automation@example.com",
            category_value="52706",  # General Inquiry
            message="This is an automated QA test message for ADO-136478.",
        )

    with allure.step("Click Send Message and observe the button during the network call"):
        contact.click_submit()
        disabled_during_call = contact.is_submit_disabled()
        has_spinner = contact.has_loading_spinner()
        contact.page.wait_for_function(
            "el => !el.disabled",
            arg=contact.page.locator(contact.SUBMIT_BUTTON).element_handle(),
            timeout=15000,
        )
        status_text = contact.status_text()

    # Assert
    assert disabled_during_call, "expected the Send Message button to be disabled during the network call"
    assert has_spinner, (
        "expected a loading spinner on the Send Message button during submission — none exists in the "
        "live markup (button icon/label are unchanged while disabled; see Page-Object docstring)"
    )
    assert status_text.strip(), "expected a non-empty status message once the response returns"


@allure.epic("GLOBAL")
@allure.feature("Quick Contact Us Section")
@allure.story("Embedded map pin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The embedded map renders the Qatar Chamber location pin correctly")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129390
@pytest.mark.traceability("ADO-136479")
def test_embedded_map_renders_location_pin(page):
    # ADO-136479 | PBI 129390
    # Arrange
    contact = HomeQuickContactPage(page)

    # Act
    with allure.step("Load the Home Page and scroll to the Contact Us section"):
        contact.open_home()
        contact.scroll_to_section()

    with allure.step("Inspect the embedded map and the Location Address text"):
        map_visible = contact.is_map_iframe_visible()
        fallback_visible = contact.is_map_fallback_visible()
        map_src = contact.map_iframe_src()
        location_text = contact.location_text()

    # Assert
    assert map_visible, "expected the embedded map iframe to be visible"
    assert not fallback_visible, "expected the map fallback state NOT to be showing when the map loads"
    assert "Lusail" in map_src and "Doha" in map_src, f"expected the map query to match the configured address, got {map_src!r}"
    assert "Lusail Boulevard 69" in location_text, f"expected the Location Address text to match the map, got {location_text!r}"


@allure.epic("GLOBAL")
@allure.feature("Quick Contact Us Section")
@allure.story("Arabic (RTL) rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Contact Us section renders correctly in Arabic on desktop (RTL)")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.pbi_129390
@pytest.mark.traceability("ADO-136550")
def test_contact_us_renders_correctly_in_arabic_rtl_desktop(page):
    # ADO-136550 | PBI 129390
    # Arrange
    contact = HomeQuickContactPage(page)

    # Act
    with allure.step("Switch the site language to Arabic and reload the Home Page"):
        contact.open_home_arabic()

    with allure.step("Scroll to the Contact Us section"):
        contact.scroll_to_section()
        page_dir = contact.page_direction()
        section_dir = contact.section_direction()
        info_x = contact.info_x()
        form_x = contact.form_x()
        heading_text = contact.heading_text()
        submit_label = contact.text(contact.SUBMIT_LABEL)

    # Assert
    assert page_dir == "rtl"
    assert section_dir == "rtl"
    assert contact.is_section_visible()
    assert info_x is not None and form_x is not None
    assert info_x > form_x, "expected the contact-info column to mirror to the RIGHT of the form under RTL"
    assert heading_text == "تواصل مع غرفة قطر لدفع أعمالك نحو الأمام"
    assert submit_label == "إرسال الرسالة"
