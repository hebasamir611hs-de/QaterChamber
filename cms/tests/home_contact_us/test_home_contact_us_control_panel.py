"""
cms/tests/home_contact_us/test_home_contact_us_control_panel.py —
Control_Panel-tagged cases for PBI 129390, backing the Home Page "Contact
Us" section (public fragment "QC Home Contact Us").

PBI resolution note: no azure-devops MCP tool was available in this
session's toolset. `129390` is read directly, live, off the
externalReferenceCode of the "Inquiry Categories" Object Definition rows
this section's Category dropdown is sourced from
(`QCDEMO-129390-INQCAT-01` .. `-11`, confirmed live, 11 rows, "Showing 1 to
11 of 11 entries") — real evidence, the same seed-naming convention already
relied on verbatim elsewhere in this suite (pbi_129389/About Us,
pbi_129397/GM's Message, etc.). The other content surface behind this same
feature — the "Contact Us Section" Journal (Web Content) article, articleId
53012 — exposes NO externalReferenceCode anywhere in its own edit-form UI
(confirmed live: `input[name*="externalReferenceCode"]` had zero matches),
so there is no independently-confirmed PBI number for that half of the
feature. This module uses `pbi_129390` for BOTH halves as the best-available
same-feature inference, disclosed explicitly here rather than silently
presented as separately confirmed for the article — see
HomeContactUsAdminPage's module docstring for the full trail.

LIVE BLOCKER — 11 of these 14 cases are SKIPPED, not faked. The "Contact Us
Section" article's Fields panel (where Section Tag/Heading/Email Support/
Telephone/Location/Recipient Emails/Send Message Button Label live) fails to
render its field inputs in both en-US and ar-SA locales — confirmed live,
reproducible, `aria-expanded` verified `true` on the panel toggle with the
mount point (`.ddm-form-builder-app`) still empty afterward, alongside
`asset-taglib` React errors (`X.map is not a function`) and two `403`s on
`/api/jsonws/invoke` in the browser console on every load of this screen.
Per this suite's own rule ("never invent selectors as real"), the 11 tests
below that would exercise this form are `@pytest.mark.skip`, carrying their
full intended AAA body in a docstring/comment plus their real traceability
markers, so Azure selection (`-m tc_XXXXXX`) still finds them — they are
simply not executable until the product-side rendering issue is confirmed
fixed (or a different edit path into this article's fields is found) and
this module is revisited to fill in real locators.

The remaining 3 cases (136534, 136538, 136569) target the OTHER surface —
the Inquiry Categories Object Definition's row 01 (ERC
QCDEMO-129390-INQCAT-01, record 52706) — which DOES render correctly live,
and are fully scripted with real, confirmed locators.

Shared-record safety: all 14 tests are pinned to `xdist_group` so
pytest-xdist (run with `--dist loadgroup`) serializes each group onto one
worker while still running in parallel against unrelated modules — the
Inquiry Category tests share row 52706 (a live, seeded, shared singleton
per this project's Test-Data Policy: TEST_OWNED, baseline captured/restored,
never left mutated), and the (currently-skipped) article tests share
articleId 53012.
"""

import allure
import pytest

from cms.pages.home_contact_us.home_contact_us_admin_page import (
    HomeContactUsAdminPage,
)
from core.web.browser import new_context
from web.pages.home_contact_us.home_contact_us_page import HomeContactUsPage

INQUIRY_CATEGORY_XDIST_GROUP = "home_contact_us_inquiry_category_52706"
CONTACT_US_SECTION_XDIST_GROUP = "home_contact_us_section_article_53012"

FIELDS_PANEL_BLOCKED_REASON = (
    "BLOCKED (live, 2026-09-06): the 'Contact Us Section' article's (id "
    "53012) Fields panel does not render its field inputs in either en-US "
    "or ar-SA — aria-expanded confirmed true, .ddm-form-builder-app mount "
    "confirmed empty, asset-taglib React errors + 403s on "
    "/api/jsonws/invoke in console. See HomeContactUsAdminPage's module "
    "docstring for the full reproduction. Real locators cannot be captured "
    "until this clears; not worked around with invented selectors."
)


# ---------------------------------------------------------------------------
# Inquiry Categories (row 01, ERC QCDEMO-129390-INQCAT-01) — LIVE, SCRIPTED
# ---------------------------------------------------------------------------

@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Inquiry Category fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Inquiry Category Label (EN) valid value saves (ADO-136534)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136534
@pytest.mark.xdist_group(INQUIRY_CATEGORY_XDIST_GROUP)
def test_inquiry_category_label_en_valid_value_saves_136534(page):
    """ADO-136534. Enter Category Label (EN)='General Inquiry' on the live
    Inquiry Category row 01 -> Save -> value persists on reload. The shared
    row's baseline is captured first and restored in `finally`."""
    admin = HomeContactUsAdminPage(page)
    qctest_label_en = "General Inquiry"  # case's own literal value; also this row's current seed value

    with allure.step("Open Inquiry Category row 01's edit form"):
        admin.open_inquiry_category_01_edit_form()

    with allure.step("Capture the current (baseline) Category Label (EN) for teardown"):
        baseline_label_en = admin.field_value(admin.CATEGORY_LABEL_EN)

    try:
        with allure.step("Enter Category Label (EN)"):
            admin.fill_text_field(admin.CATEGORY_LABEL_EN, qctest_label_en)

        # Assert: field accepts the input before Save.
        assert admin.field_value(admin.CATEGORY_LABEL_EN) == qctest_label_en

        with allure.step("Click Save"):
            admin.save_category()

        # Assert: Save succeeds — no validation error surfaced.
        assert not admin.is_save_error_shown(), admin.save_error_text()

        with allure.step("Reopen the record and confirm the value persisted"):
            admin.open_inquiry_category_01_edit_form()
            reloaded_label_en = admin.field_value(admin.CATEGORY_LABEL_EN)

        assert reloaded_label_en == qctest_label_en, (
            f"Category Label (EN) reads {reloaded_label_en!r} after reload, "
            f"expected {qctest_label_en!r}."
        )
    finally:
        with allure.step("Teardown: restore the baseline Category Label (EN)"):
            admin.open_inquiry_category_01_edit_form()
            admin.fill_text_field(admin.CATEGORY_LABEL_EN, baseline_label_en)
            admin.save_category()
            assert not admin.is_save_error_shown(), (
                "Teardown restore failed validation: " + admin.save_error_text()
            )


@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Inquiry Category fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Inquiry Category Display Order valid value saves (ADO-136538)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136538
@pytest.mark.xdist_group(INQUIRY_CATEGORY_XDIST_GROUP)
def test_inquiry_category_display_order_valid_value_saves_136538(page):
    """ADO-136538. Enter Display Order=1 (the case's literal value; the
    live seeded rows actually use a 100/200/... convention — disclosed, not
    silently normalized) -> Save -> value persists on reload."""
    admin = HomeContactUsAdminPage(page)
    qctest_display_order = "1"

    with allure.step("Open Inquiry Category row 01's edit form"):
        admin.open_inquiry_category_01_edit_form()

    with allure.step("Capture the current (baseline) Display Order for teardown"):
        baseline_display_order = admin.field_value(admin.CATEGORY_DISPLAY_ORDER)

    try:
        with allure.step("Enter Display Order"):
            admin.fill_text_field(admin.CATEGORY_DISPLAY_ORDER, qctest_display_order)

        assert admin.field_value(admin.CATEGORY_DISPLAY_ORDER) == qctest_display_order

        with allure.step("Click Save"):
            admin.save_category()

        assert not admin.is_save_error_shown(), admin.save_error_text()

        with allure.step("Reopen the record and confirm the value persisted"):
            admin.open_inquiry_category_01_edit_form()
            reloaded_display_order = admin.field_value(admin.CATEGORY_DISPLAY_ORDER)

        assert reloaded_display_order == qctest_display_order, (
            f"Display Order reads {reloaded_display_order!r} after reload, "
            f"expected {qctest_display_order!r}."
        )
    finally:
        with allure.step("Teardown: restore the baseline Display Order"):
            admin.open_inquiry_category_01_edit_form()
            admin.fill_text_field(admin.CATEGORY_DISPLAY_ORDER, baseline_display_order)
            admin.save_category()
            assert not admin.is_save_error_shown(), (
                "Teardown restore failed validation: " + admin.save_error_text()
            )


@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Inquiry Category fields (Arabic)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("التحقق من أنه يتم حفظ قيمة صحيحة لتصنيف فئة الاستفسار (بالعربية) (ADO-136569)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136569
@pytest.mark.xdist_group(INQUIRY_CATEGORY_XDIST_GROUP)
def test_inquiry_category_label_ar_valid_value_saves_136569(page):
    """ADO-136569 (Bilingual/AR variant). Enter Category Label (AR)='استفسار
    عام' via the field's own per-field locale toggle -> Save -> value
    persists on reload, RTL stored correctly."""
    admin = HomeContactUsAdminPage(page)
    qctest_label_ar = "استفسار عام"

    with allure.step("Open Inquiry Category row 01's edit form"):
        admin.open_inquiry_category_01_edit_form()

    with allure.step("Switch the Category Label field to Arabic"):
        admin.switch_category_label_locale_to_arabic()

    with allure.step("Capture the current (baseline) Category Label (AR) for teardown"):
        baseline_label_ar = admin.field_value(admin.CATEGORY_LABEL_EN)

    try:
        with allure.step("Enter Category Label (AR)"):
            admin.fill_text_field(admin.CATEGORY_LABEL_EN, qctest_label_ar)

        assert admin.field_value(admin.CATEGORY_LABEL_EN) == qctest_label_ar

        with allure.step("Click Save"):
            admin.save_category()

        assert not admin.is_save_error_shown(), admin.save_error_text()

        with allure.step("Reopen the record, switch to Arabic, and confirm the value persisted"):
            admin.open_inquiry_category_01_edit_form()
            admin.switch_category_label_locale_to_arabic()
            reloaded_label_ar = admin.field_value(admin.CATEGORY_LABEL_EN)

        assert reloaded_label_ar == qctest_label_ar, (
            f"Category Label (AR) reads {reloaded_label_ar!r} after reload, "
            f"expected {qctest_label_ar!r}."
        )
    finally:
        with allure.step("Teardown: restore the baseline Category Label (AR)"):
            admin.open_inquiry_category_01_edit_form()
            admin.switch_category_label_locale_to_arabic()
            admin.fill_text_field(admin.CATEGORY_LABEL_EN, baseline_label_ar)
            admin.save_category()
            assert not admin.is_save_error_shown(), (
                "Teardown restore failed validation: " + admin.save_error_text()
            )


# ---------------------------------------------------------------------------
# Contact Us Section article (id 53012) — SKIPPED, blocked live (see module
# docstring). Each carries its full intended AAA body in a docstring so the
# batch is not a dead end once the Fields panel blocker clears.
# ---------------------------------------------------------------------------

@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Section Tag / Heading")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section Tag (EN) valid value saves (ADO-136508)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136508
@pytest.mark.xdist_group(CONTACT_US_SECTION_XDIST_GROUP)
@pytest.mark.skip(reason=FIELDS_PANEL_BLOCKED_REASON)
def test_section_tag_en_valid_value_saves_136508(page):
    """ADO-136508. Intended body once unblocked: open the Contact Us
    Section article -> capture baseline SECTION_TAG_EN -> fill 'Get in
    touch' (12 chars) -> Save as Draft -> assert no validation error ->
    reopen and reread to confirm authoring-side persistence (the case's
    "renders on Home Page" expectation is not assertable from a Draft save
    — see module docstring's draft-vs-public note) -> restore baseline in
    `finally`."""
    admin = HomeContactUsAdminPage(page)
    admin.open_contact_us_section_article()
    baseline = admin.field_value(admin.SECTION_TAG_EN)
    try:
        admin.fill_text_field(admin.SECTION_TAG_EN, "Get in touch")
        admin.save_article_as_draft()
        assert not admin.is_save_error_shown(), admin.save_error_text()
    finally:
        admin.fill_text_field(admin.SECTION_TAG_EN, baseline)
        admin.save_article_as_draft()


@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Section Tag / Heading")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section Heading (EN) valid value saves (ADO-136512)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136512
@pytest.mark.xdist_group(CONTACT_US_SECTION_XDIST_GROUP)
@pytest.mark.skip(reason=FIELDS_PANEL_BLOCKED_REASON)
def test_section_heading_en_valid_value_saves_136512(page):
    """ADO-136512. Intended body: fill SECTION_HEADING_EN with 'Connect
    with Qatar Chamber to Move Your Business Forward' (58 chars — this is
    also the section's CURRENT live public heading) -> Save as Draft ->
    assert no validation error -> reopen/reread -> restore baseline."""
    admin = HomeContactUsAdminPage(page)
    admin.open_contact_us_section_article()
    baseline = admin.field_value(admin.SECTION_HEADING_EN)
    try:
        admin.fill_text_field(
            admin.SECTION_HEADING_EN,
            "Connect with Qatar Chamber to Move Your Business Forward",
        )
        admin.save_article_as_draft()
        assert not admin.is_save_error_shown(), admin.save_error_text()
    finally:
        admin.fill_text_field(admin.SECTION_HEADING_EN, baseline)
        admin.save_article_as_draft()


@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Contact details")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Email Support Address valid value saves (ADO-136518)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136518
@pytest.mark.xdist_group(CONTACT_US_SECTION_XDIST_GROUP)
@pytest.mark.skip(reason=FIELDS_PANEL_BLOCKED_REASON)
def test_email_support_address_valid_value_saves_136518(page):
    """ADO-136518 (Priority 1). Intended body: fill
    EMAIL_SUPPORT_ADDRESS='support@qcci.org' -> Save as Draft -> assert no
    validation error -> reopen/reread -> restore baseline. Public-section
    reflection would additionally be checked in a fresh, logged-out
    context per this project's public-page-visibility convention, once the
    Draft-vs-Publish contradiction is resolved for this case (see module
    docstring)."""
    admin = HomeContactUsAdminPage(page)
    admin.open_contact_us_section_article()
    baseline = admin.field_value(admin.EMAIL_SUPPORT_ADDRESS)
    try:
        admin.fill_text_field(admin.EMAIL_SUPPORT_ADDRESS, "support@qcci.org")
        admin.save_article_as_draft()
        assert not admin.is_save_error_shown(), admin.save_error_text()
    finally:
        admin.fill_text_field(admin.EMAIL_SUPPORT_ADDRESS, baseline)
        admin.save_article_as_draft()


@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Contact details")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Telephone Number valid value saves (ADO-136523)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136523
@pytest.mark.xdist_group(CONTACT_US_SECTION_XDIST_GROUP)
@pytest.mark.skip(reason=FIELDS_PANEL_BLOCKED_REASON)
def test_telephone_number_valid_value_saves_136523(page):
    """ADO-136523. Intended body: fill TELEPHONE_NUMBER='+974 44559111'
    (also the section's CURRENT live public telephone) -> Save as Draft ->
    assert no validation error -> reopen/reread -> restore baseline."""
    admin = HomeContactUsAdminPage(page)
    admin.open_contact_us_section_article()
    baseline = admin.field_value(admin.TELEPHONE_NUMBER)
    try:
        admin.fill_text_field(admin.TELEPHONE_NUMBER, "+974 44559111")
        admin.save_article_as_draft()
        assert not admin.is_save_error_shown(), admin.save_error_text()
    finally:
        admin.fill_text_field(admin.TELEPHONE_NUMBER, baseline)
        admin.save_article_as_draft()


@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Contact details")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Location Address (EN) valid value saves (ADO-136527)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136527
@pytest.mark.xdist_group(CONTACT_US_SECTION_XDIST_GROUP)
@pytest.mark.skip(reason=FIELDS_PANEL_BLOCKED_REASON)
def test_location_address_en_valid_value_saves_136527(page):
    """ADO-136527. Intended body: fill LOCATION_ADDRESS_EN='Lusail
    Boulevard 69, Al Kharayej - Street 169, Doha, Qatar' -> Save as Draft ->
    assert no validation error -> reopen/reread -> restore baseline."""
    admin = HomeContactUsAdminPage(page)
    admin.open_contact_us_section_article()
    baseline = admin.field_value(admin.LOCATION_ADDRESS_EN)
    try:
        admin.fill_text_field(
            admin.LOCATION_ADDRESS_EN,
            "Lusail Boulevard 69, Al Kharayej - Street 169, Doha, Qatar",
        )
        admin.save_article_as_draft()
        assert not admin.is_save_error_shown(), admin.save_error_text()
    finally:
        admin.fill_text_field(admin.LOCATION_ADDRESS_EN, baseline)
        admin.save_article_as_draft()


@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Form routing")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Form Recipient Email(s) valid multi-value saves (ADO-136541)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136541
@pytest.mark.xdist_group(CONTACT_US_SECTION_XDIST_GROUP)
@pytest.mark.skip(reason=FIELDS_PANEL_BLOCKED_REASON)
def test_form_recipient_emails_valid_multi_value_saves_136541(page):
    """ADO-136541 (Priority 1). Intended body: fill
    FORM_RECIPIENT_EMAILS='contact@qcci.org;info@qcci.org' -> Save as Draft
    -> assert no validation error -> reopen/reread -> restore baseline."""
    admin = HomeContactUsAdminPage(page)
    admin.open_contact_us_section_article()
    baseline = admin.field_value(admin.FORM_RECIPIENT_EMAILS)
    try:
        admin.fill_text_field(
            admin.FORM_RECIPIENT_EMAILS, "contact@qcci.org;info@qcci.org"
        )
        admin.save_article_as_draft()
        assert not admin.is_save_error_shown(), admin.save_error_text()
    finally:
        admin.fill_text_field(admin.FORM_RECIPIENT_EMAILS, baseline)
        admin.save_article_as_draft()


@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Call-to-action label")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Send Message Button Label (EN) valid value saves and publishes (ADO-136546)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136546
@pytest.mark.xdist_group(CONTACT_US_SECTION_XDIST_GROUP)
@pytest.mark.skip(reason=FIELDS_PANEL_BLOCKED_REASON)
def test_send_message_button_label_en_valid_value_saves_and_publishes_136546(page):
    """ADO-136546 (Bilingual — the one of the two cases whose steps say
    "Save as Draft, then Publish"). Intended body: fill
    SEND_MESSAGE_BUTTON_LABEL_EN='Send Message' -> Save as Draft -> Publish
    -> assert no validation error -> open a FRESH, logged-out browser
    context (never the CMS-authenticated `page` fixture, per this
    project's public-page-visibility convention) against the public Home
    page and assert the CTA renders 'Send Message' -> restore baseline and
    republish in `finally` (a Draft-only restore would leave the record
    published with the mutated value still live)."""
    admin = HomeContactUsAdminPage(page)
    admin.open_contact_us_section_article()
    baseline = admin.field_value(admin.SEND_MESSAGE_BUTTON_LABEL_EN)
    try:
        admin.fill_text_field(admin.SEND_MESSAGE_BUTTON_LABEL_EN, "Send Message")
        admin.save_article_as_draft()
        admin.publish_article()
        assert not admin.is_save_error_shown(), admin.save_error_text()
        # TODO(public-assert): fresh logged-out context against the public
        # Home page, assert CTA text == "Send Message".
    finally:
        admin.fill_text_field(admin.SEND_MESSAGE_BUTTON_LABEL_EN, baseline)
        admin.save_article_as_draft()
        admin.publish_article()


@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Section Tag / Heading (Arabic)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("التحقق من أنه يتم حفظ قيمة صحيحة لعلامة القسم (بالعربية) (ADO-136555)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136555
@pytest.mark.xdist_group(CONTACT_US_SECTION_XDIST_GROUP)
@pytest.mark.skip(reason=FIELDS_PANEL_BLOCKED_REASON)
def test_section_tag_ar_valid_value_saves_136555(page):
    """ADO-136555 (Bilingual/AR variant). Intended body: switch to ar-SA
    via the toolbar locale switcher -> fill SECTION_TAG_AR='تواصل معنا' ->
    Save as Draft -> assert no validation error -> reopen/reread (RTL
    stored correctly) -> restore baseline."""
    admin = HomeContactUsAdminPage(page)
    admin.open_contact_us_section_article()
    baseline = admin.field_value(admin.SECTION_TAG_AR)
    try:
        admin.fill_text_field(admin.SECTION_TAG_AR, "تواصل معنا")
        admin.save_article_as_draft()
        assert not admin.is_save_error_shown(), admin.save_error_text()
    finally:
        admin.fill_text_field(admin.SECTION_TAG_AR, baseline)
        admin.save_article_as_draft()


@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Section Tag / Heading (Arabic)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("التحقق من أنه يتم حفظ قيمة صحيحة لعنوان القسم (بالعربية) (ADO-136559)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136559
@pytest.mark.xdist_group(CONTACT_US_SECTION_XDIST_GROUP)
@pytest.mark.skip(reason=FIELDS_PANEL_BLOCKED_REASON)
def test_section_heading_ar_valid_value_saves_136559(page):
    """ADO-136559 (Bilingual/AR variant). Intended body: fill
    SECTION_HEADING_AR='تواصل مع قطر لدفع أعمالك إلى الأمام' -> Save as
    Draft -> assert no validation error -> reopen/reread -> restore
    baseline."""
    admin = HomeContactUsAdminPage(page)
    admin.open_contact_us_section_article()
    baseline = admin.field_value(admin.SECTION_HEADING_AR)
    try:
        admin.fill_text_field(
            admin.SECTION_HEADING_AR, "تواصل مع قطر لدفع أعمالك إلى الأمام"
        )
        admin.save_article_as_draft()
        assert not admin.is_save_error_shown(), admin.save_error_text()
    finally:
        admin.fill_text_field(admin.SECTION_HEADING_AR, baseline)
        admin.save_article_as_draft()


@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Contact details (Arabic)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("التحقق من أنه يتم حفظ قيمة صحيحة لعنوان الموقع (بالعربية) (ADO-136565)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136565
@pytest.mark.xdist_group(CONTACT_US_SECTION_XDIST_GROUP)
@pytest.mark.skip(reason=FIELDS_PANEL_BLOCKED_REASON)
def test_location_address_ar_valid_value_saves_136565(page):
    """ADO-136565 (Bilingual/AR variant). Intended body: fill
    LOCATION_ADDRESS_AR with a valid Arabic address string -> Save as Draft
    -> assert no validation error -> reopen/reread -> restore baseline."""
    admin = HomeContactUsAdminPage(page)
    admin.open_contact_us_section_article()
    baseline = admin.field_value(admin.LOCATION_ADDRESS_AR)
    try:
        admin.fill_text_field(
            admin.LOCATION_ADDRESS_AR,
            "شارع لوسيل بوليفارد 69، الخرائج - شارع 169، الدوحة، قطر",
        )
        admin.save_article_as_draft()
        assert not admin.is_save_error_shown(), admin.save_error_text()
    finally:
        admin.fill_text_field(admin.LOCATION_ADDRESS_AR, baseline)
        admin.save_article_as_draft()


@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Call-to-action label (Arabic)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("التحقق من أنه يتم حفظ قيمة صحيحة لنص زر إرسال الرسالة (بالعربية) (ADO-136572)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_129390
@pytest.mark.tc_136572
@pytest.mark.xdist_group(CONTACT_US_SECTION_XDIST_GROUP)
@pytest.mark.skip(reason=FIELDS_PANEL_BLOCKED_REASON)
def test_send_message_button_label_ar_valid_value_saves_and_publishes_136572(page):
    """ADO-136572 (Bilingual/AR variant — the second of the two cases whose
    steps say "Save as Draft, then Publish"). Intended body: fill
    SEND_MESSAGE_BUTTON_LABEL_AR='إرسال الرسالة' -> Save as Draft ->
    Publish -> assert no validation error -> fresh, logged-out browser
    context against the public Home page, assert the CTA renders 'إرسال
    الرسالة' right-aligned (RTL) -> restore baseline and republish in
    `finally`."""
    admin = HomeContactUsAdminPage(page)
    admin.open_contact_us_section_article()
    baseline = admin.field_value(admin.SEND_MESSAGE_BUTTON_LABEL_AR)
    try:
        admin.fill_text_field(admin.SEND_MESSAGE_BUTTON_LABEL_AR, "إرسال الرسالة")
        admin.save_article_as_draft()
        admin.publish_article()
        assert not admin.is_save_error_shown(), admin.save_error_text()
        # TODO(public-assert): fresh logged-out context against the public
        # Home page, assert CTA text == "إرسال الرسالة", right-aligned (RTL).
    finally:
        admin.fill_text_field(admin.SEND_MESSAGE_BUTTON_LABEL_AR, baseline)
        admin.save_article_as_draft()
        admin.publish_article()


# ---------------------------------------------------------------------------
# TC 136498 — full end-to-end configuration flow (PBI 129390). RE-VERIFIED
# LIVE 2026-09-07 (this session, disposable Python/Playwright probe, existing
# .auth/state.json, 1920x1080) rather than inherited from the 2026-09-06
# finding above, per standards.md's "re-verify any finding reached via
# Content & Data instead of Object Authoring" instruction:
#
#   1. Confirmed NO Object Authoring (`/web/qatar-chamber/manage-<slug>`)
#      surface exists for this section — tried `contact-us-section`,
#      `quick-contact-us`, `quick-contact`, `contact-us`,
#      `home-quick-contact-us`, `contact-us-quick-section`, every one
#      rendered the site's "Coming Soon" 404-equivalent page. Independently
#      cross-checked against the full live Content & Data object-definition
#      menu (`Open Applications Menu` -> menu-item dump, ~170 objects listed)
#      — no "Contact Us Section"/"Quick Contact" object definition exists
#      anywhere in it (only "Inquiry Categories", already covered by
#      136534/136538/136569 above). This section is confirmed NOT
#      Object-Definition-backed; the standards.md "Object Authoring Is the
#      Only Path" rule does not apply to it (see that section's own carve-out
#      for surfaces that were never a Content & Data-vs-Object-Authoring
#      choice) — it is a Liferay Journal (Web Content) article, matching the
#      2026-09-06 finding.
#   2. Re-opened the real article edit screen (articleId 53012) live this
#      session and re-clicked "Fields" myself: the SAME blocker reproduces
#      today — `.ddm-form-builder-app` mount renders with empty innerHTML,
#      and the console fires the identical `TypeError: B.map is not a
#      function` / `TypeError: O.map is not a function` traces inside
#      `asset-taglib`'s bundle on every load. This is a confirmed-live,
#      reproducible, still-open PRODUCT DEFECT (not a stale/superseded
#      finding) — Site Content Editors cannot enter ANY of this article's
#      Section Tag / Heading / Email Support / Telephone / Location /
#      Recipient Emails / Send Message Button Label fields in either
#      locale, via any in-product path, as of this session.
#
# TC 136498 ("Verify that the CMS end-to-end configuration flow saves and
# publishes correctly") Step 2 ("Enter all fields (EN+AR) with test data")
# is exactly the step this blocker prevents — it is SKIPPED for the same
# reason and using the same shared xdist_group (articleId 53012) as the 11
# field-level cases above, not scripted as a hollow pass. Save as Draft (Step
# 3) and Publish (Step 5) buttons themselves DO render and are independently
# clickable (see HomeContactUsAdminPage's ARTICLE_SAVE_AS_DRAFT_BUTTON /
# ARTICLE_PUBLISH_BUTTON, both CONFIRMED LIVE) — only the field-entry step is
# blocked — but a "Save as Draft" with no fields actually enterable cannot
# fulfil the case's own Step 2, so the whole flow is disclosed as blocked
# rather than split into a partial/misleading pass.
# ---------------------------------------------------------------------------

@allure.epic("Home Page")
@allure.feature("Contact Us Section")
@allure.story("Full admin configuration flow, end to end")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("CMS end-to-end configuration flow saves and publishes correctly (ADO-136498)")
@pytest.mark.control_panel
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.bilingual
@pytest.mark.pbi_129390
@pytest.mark.tc_136498
@pytest.mark.xdist_group(CONTACT_US_SECTION_XDIST_GROUP)
@pytest.mark.skip(reason=FIELDS_PANEL_BLOCKED_REASON)
def test_contact_us_section_full_admin_configuration_flow_136498(page, browser):
    """ADO-136498. Intended body once the Fields-panel blocker clears:

    Step 1: admin.open_contact_us_section_article() -> screen opens (article
        edit form renders, Save as Draft / Publish visible).
    Step 2: fill every EN field (SECTION_TAG_EN, SECTION_HEADING_EN,
        EMAIL_SUPPORT_ADDRESS, TELEPHONE_NUMBER, LOCATION_ADDRESS_EN,
        FORM_RECIPIENT_EMAILS, SEND_MESSAGE_BUTTON_LABEL_EN) with QCTEST-
        prefixed values, switch the toolbar locale to ar-SA via
        ARTICLE_LOCALE_TOGGLE and fill every AR counterpart
        (SECTION_TAG_AR, SECTION_HEADING_AR, LOCATION_ADDRESS_AR,
        SEND_MESSAGE_BUTTON_LABEL_AR) -> assert every field_value() read-back
        equals what was entered (bilingual pairs populated).
    Step 3: admin.save_article_as_draft() -> assert not
        is_save_error_shown() and a success toast is visible.
    Step 4: admin.preview_article() (or equivalent Preview control once
        confirmed) -> assert the preview surface renders the same values
        just entered.
    Step 5: admin.publish_article() -> assert not is_save_error_shown();
        then, per standards.md's mandatory logged-out-context rule, open a
        FRESH `new_context(browser, use_auth_state=False)` page against the
        public Home page and poll/reload until the "QC Home Contact Us"
        fragment reflects the new Heading/Telephone text, asserting the
        anon read (never the CMS-authenticated `page`) matches.
    Teardown (`finally`): restore every field to its captured baseline via
        fill_text_field() + save_article_as_draft() + publish_article(), and
        reopen-reread to confirm the restore persisted.

    None of the above can be exercised today — Step 2's "Enter all fields"
    is blocked by the live, reproducible Fields-panel rendering defect
    documented in the module docstring and re-confirmed at the top of this
    section 2026-09-07 (same asset-taglib `X.map is not a function` errors,
    empty `.ddm-form-builder-app` mount). Reported as a PRODUCT-DEFECT
    suspicion against TC 136498 — not an automation gap to route around with
    an invented selector.
    """
    admin = HomeContactUsAdminPage(page)
    admin.open_contact_us_section_article()
    baseline = {
        "section_tag_en": admin.field_value(admin.SECTION_TAG_EN),
        "section_heading_en": admin.field_value(admin.SECTION_HEADING_EN),
        "email_support_address": admin.field_value(admin.EMAIL_SUPPORT_ADDRESS),
        "telephone_number": admin.field_value(admin.TELEPHONE_NUMBER),
        "location_address_en": admin.field_value(admin.LOCATION_ADDRESS_EN),
        "form_recipient_emails": admin.field_value(admin.FORM_RECIPIENT_EMAILS),
        "send_message_button_label_en": admin.field_value(admin.SEND_MESSAGE_BUTTON_LABEL_EN),
    }
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    try:
        with allure.step("Step 1: Open Contact Us Section Management — screen opens"):
            admin.open_contact_us_section_article()

        with allure.step("Step 2: Enter all fields (EN+AR) with test data"):
            admin.fill_text_field(admin.SECTION_TAG_EN, "QCTEST-136498 Get in touch")
            admin.fill_text_field(admin.SECTION_HEADING_EN, "QCTEST-136498 Connect with Qatar Chamber")
            admin.fill_text_field(admin.EMAIL_SUPPORT_ADDRESS, "qctest-136498@example.com")
            admin.fill_text_field(admin.TELEPHONE_NUMBER, "+974 4000 0000")
            admin.fill_text_field(admin.LOCATION_ADDRESS_EN, "QCTEST-136498 Doha, Qatar")
            admin.fill_text_field(admin.FORM_RECIPIENT_EMAILS, "qctest-136498@example.com")
            admin.fill_text_field(admin.SEND_MESSAGE_BUTTON_LABEL_EN, "QCTEST-136498 Send")
            assert admin.field_value(admin.SECTION_HEADING_EN) == "QCTEST-136498 Connect with Qatar Chamber"

        with allure.step("Step 3: Click Save as Draft — draft saved, success toast shown"):
            admin.save_article_as_draft()
            assert not admin.is_save_error_shown(), admin.save_error_text()

        with allure.step("Step 4: Click Preview — preview renders matching entered values"):
            admin.preview_article()

        with allure.step("Step 5: Click Publish — section published; Home Page reflects new content"):
            admin.publish_article()
            assert not admin.is_save_error_shown(), admin.save_error_text()
            home = HomeContactUsPage(anon_page)
            reflected = home.reload_until_heading_matches("QCTEST-136498 Connect with Qatar Chamber")
            assert reflected, "Updated Contact Us heading did not reflect on the public Home Page within the poll budget"
    finally:
        admin.open_contact_us_section_article()
        admin.fill_text_field(admin.SECTION_TAG_EN, baseline["section_tag_en"])
        admin.fill_text_field(admin.SECTION_HEADING_EN, baseline["section_heading_en"])
        admin.fill_text_field(admin.EMAIL_SUPPORT_ADDRESS, baseline["email_support_address"])
        admin.fill_text_field(admin.TELEPHONE_NUMBER, baseline["telephone_number"])
        admin.fill_text_field(admin.LOCATION_ADDRESS_EN, baseline["location_address_en"])
        admin.fill_text_field(admin.FORM_RECIPIENT_EMAILS, baseline["form_recipient_emails"])
        admin.fill_text_field(admin.SEND_MESSAGE_BUTTON_LABEL_EN, baseline["send_message_button_label_en"])
        admin.save_article_as_draft()
        admin.publish_article()
        anon_context.close()
