"""
web/pages/business_opportunities/detail_page.py — BusinessOpportunityDetailPage.

Public-frontend Page Object for PBI 130697 (INVEST — Business Opportunities),
covering the Opportunity Detail page (header, sticky section index, the
01 Overview / 02 Investment Details / 03 Gallery & Supporting Documents
sections) AND the "Express Your Interest" inquiry modal that opens from this
page's "Submit Inquiry" CTA — the modal is specific to this page (not reused
elsewhere in the feature), so it is kept here rather than split into
`pages/components/`, mirroring how `legal_consultation_page.py` keeps its
request-form modal on the same Page Object as the page it opens from.

LOCATOR EXTRACTION ATTEMPTED, BLOCKED BY AN ENVIRONMENT GAP — disclosed
------------------------------------------------------------------
Unlike listing_page.py and submit_opportunity_page.py (both resolved live
this pass), this page's real route was reached but does NOT render
opportunity-specific detail content on qcdev as of 2026-09-22:
`https://qcdev.ihorizons.com/web/qatar-chamber/business-opportunity?opportunity=<id>`
resolves (its `<title>` is "Business Opportunity Details - Qatar Chamber"),
clicking a listing card's "View Details" link navigates there for real, and
the URL param IS present — but the rendered fragment is the SAME
`qc-business-opportunities-listing` widget as the listing page itself (same
`h1.qc-bol-title` = "Global Business Opportunities", same generic hero
description, no `qc-bod-*`/detail-specific markup anywhere in the DOM). This
was confirmed twice: once navigating the URL directly, once via a real
`.qc-bol-card` click from the listing page — both landed on the listing
widget, not a detail template. Read as the dedicated detail-page fragment
not yet being deployed/wired to this route on qcdev, not a script/wait
timing issue (`networkidle` + an extra fixed wait were both tried). Every
locator constant below is therefore left as a `TODO(locator)` placeholder,
per instruction — do not invent them. Flag to devs: confirm whether the
Business Opportunity Detail page fragment exists in this environment at
all before re-attempting this extraction.
"""

from config.settings import web_url
from core.web.base_page import BasePage

# TODO(locator): the live route IS confirmed —
# /web/qatar-chamber/business-opportunity?opportunity=<id> (see module
# docstring) — but it does not render detail content to extract a real
# section/field layout from yet.
PATH_TEMPLATE = "/web/qatar-chamber/business-opportunity?opportunity={slug}"

INQUIRY_FIELD_KEYS = ("your_name", "email", "mobile", "company", "inquiry_type", "message")


class BusinessOpportunityDetailPage(BasePage):
    # ---- Header / breadcrumb ------------------------------------------------
    BREADCRUMB = "nav.qc-bod-crumbs"  # TODO: locator - breadcrumb navigation
    BREADCRUMB_LINK = ".qc-bod-crumb"  # TODO: locator - one breadcrumb link
    HEADER_TITLE = "h1.qc-bod-title"  # TODO: locator - opportunity title
    HEADER_SUMMARY = ".qc-bod-summary"  # TODO: locator - hero summary rich text
    SECTOR_TAG = ".qc-bod-tag-sector"  # TODO: locator - derived Sector tag
    COUNTRY_TAG = ".qc-bod-tag-country"  # TODO: locator - derived Country tag

    # ---- Sticky section index ------------------------------------------------
    SECTION_INDEX = "nav.qc-bod-index"  # TODO: locator - sticky section index nav
    SECTION_INDEX_ITEM = ".qc-bod-index-item"  # TODO: locator - one section index entry
    SECTION_INDEX_ACTIVE_ITEM = ".qc-bod-index-item.is-active"  # TODO: locator - currently-highlighted index entry

    SECTION_OVERVIEW = "#qc-bod-overview"  # TODO: locator - 01 Overview section
    SECTION_INVESTMENT_DETAILS = "#qc-bod-investment-details"  # TODO: locator - 02 Investment Details section
    SECTION_GALLERY_DOCS = "#qc-bod-gallery-docs"  # TODO: locator - 03 Gallery & Supporting Documents section

    # ---- 01 Overview ----------------------------------------------------------
    OVERVIEW_BODY = ".qc-bod-overview-body"  # TODO: locator - Overview Body rich text
    INVESTMENT_BRIEF = ".qc-bod-investment-brief"  # TODO: locator - Investment Brief text
    KEY_HIGHLIGHT_ITEM = ".qc-bod-key-highlight"  # TODO: locator - one Key Highlight list item

    # ---- 02 Investment Details ------------------------------------------------
    SUBMITTED_BY_NAME = ".qc-bod-submitter-name"  # TODO: locator - Submitted By: submitter name
    SUBMITTED_BY_ENTITY_TYPE = ".qc-bod-submitter-entity"  # TODO: locator - Submitted By: entity type
    SUBMITTED_BY_LOCATION = ".qc-bod-submitter-location"  # TODO: locator - Submitted By: location
    SUBMITTED_BY_LOGO = ".qc-bod-submitter-logo img"  # TODO: locator - Submitted By: logo image
    INVESTMENT_AMOUNT = ".qc-bod-investment-amount"  # TODO: locator - Investment Amount value
    MINIMUM_TICKET = ".qc-bod-minimum-ticket"  # TODO: locator - Minimum Ticket value
    CO_INVESTMENT_ROW = ".qc-bod-co-investment-row"  # TODO: locator - one Co-Investment row

    # ---- 03 Gallery & Supporting Documents -------------------------------
    GALLERY_IMAGE = ".qc-bod-gallery-image"  # TODO: locator - one gallery image
    RESOURCE_ROW = ".qc-bod-resource-row"  # TODO: locator - one downloadable-resource row
    RESOURCE_TITLE = ".qc-bod-resource-title"  # TODO: locator - resource row title
    RESOURCE_SIZE = ".qc-bod-resource-size"  # TODO: locator - resource row file size
    RESOURCE_DOWNLOAD_BUTTON = ".qc-bod-resource-download"  # TODO: locator - resource row "Download" button
    RESOURCE_UNAVAILABLE_MESSAGE = ".qc-bod-resource-unavailable"  # TODO: locator - "file no longer available" message

    # ---- Submit Inquiry CTA -------------------------------------------------
    SUBMIT_INQUIRY_CTA = ".qc-bod-submit-inquiry-cta"  # TODO: locator - "Submit Inquiry" CTA button

    # ---- Express Your Interest modal ----------------------------------------
    INQUIRY_MODAL = ".qc-boi-modal"  # TODO: locator - inquiry modal container
    INQUIRY_DIALOG = ".qc-boi-dialog"  # TODO: locator - inquiry modal dialog
    INQUIRY_CLOSE_BUTTON = ".qc-boi-dialog-x"  # TODO: locator - inquiry modal close icon
    INQUIRY_SUBMIT_BUTTON = ".qc-boi-submit"  # TODO: locator - inquiry modal "Submit Inquiry" button
    INQUIRY_CAPTCHA_MOUNT = ".qc-boi-captcha"  # TODO: locator - inquiry modal CAPTCHA mount node
    INQUIRY_SUCCESS_MESSAGE = ".qc-boi-success"  # TODO: locator - inquiry modal success/confirmation message
    INQUIRY_GENERIC_ERROR = ".qc-boi-error"  # TODO: locator - inquiry modal generic/top-level error banner

    INQUIRY_FIELD_LOCATORS = {
        "your_name": "input[name='inquiryYourName']",  # TODO: locator - Inquiry "Your Name" input
        "email": "input[name='inquiryEmail']",  # TODO: locator - Inquiry "Email Address" input
        "mobile": "input[name='inquiryMobile']",  # TODO: locator - Inquiry "Mobile Number" input
        "company": "input[name='inquiryCompany']",  # TODO: locator - Inquiry "Company" input
        "inquiry_type": "select[name='inquiryType']",  # TODO: locator - Inquiry "Inquiry Type" dropdown (optional)
        "message": "textarea[name='inquiryMessage']",  # TODO: locator - Inquiry "Message" textarea
    }
    INQUIRY_FIELD_ERROR_LOCATORS = {
        key: f".qc-boi-field[data-field='{key}'] .qc-boi-error"  # TODO: locator - inline error under this field
        for key in INQUIRY_FIELD_KEYS
    }

    # ---- Navigation -----------------------------------------------------------
    def open_detail(self, slug: str, locale: str = "en") -> "BusinessOpportunityDetailPage":
        self.open(web_url(PATH_TEMPLATE.format(slug=slug), locale=locale))
        self.wait_for(self.HEADER_TITLE, state="visible", timeout=30000)
        return self

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    # ---- Header / breadcrumb ------------------------------------------------
    def title_text(self) -> str:
        return self.text(self.HEADER_TITLE).strip()

    def summary_text(self) -> str:
        return self.text(self.HEADER_SUMMARY).strip()

    def breadcrumb_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.BREADCRUMB_LINK).all_inner_texts()]

    def click_breadcrumb(self, label: str) -> None:
        self.click(f"{self.BREADCRUMB_LINK}:has-text('{label}')")

    def sector_tag_text(self) -> str:
        return self.text(self.SECTOR_TAG).strip()

    def country_tag_text(self) -> str:
        return self.text(self.COUNTRY_TAG).strip()

    # ---- Section index -----------------------------------------------------
    def section_index_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.SECTION_INDEX_ITEM).all_inner_texts()]

    def click_section_index_item(self, label: str) -> None:
        self.click(f"{self.SECTION_INDEX_ITEM}:has-text('{label}')")

    def active_section_index_label(self) -> str:
        return self.text(self.SECTION_INDEX_ACTIVE_ITEM).strip()

    # ---- 01 Overview ----------------------------------------------------------
    def overview_body_text(self) -> str:
        return self.text(self.OVERVIEW_BODY).strip()

    def investment_brief_text(self) -> str:
        return self.text(self.INVESTMENT_BRIEF).strip()

    def key_highlight_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.KEY_HIGHLIGHT_ITEM).all_inner_texts()]

    # ---- 02 Investment Details ------------------------------------------------
    def submitted_by(self) -> dict:
        return {
            "name": self.text(self.SUBMITTED_BY_NAME).strip(),
            "entity_type": self.text(self.SUBMITTED_BY_ENTITY_TYPE).strip(),
            "location": self.text(self.SUBMITTED_BY_LOCATION).strip(),
            "logo_visible": self.is_visible(self.SUBMITTED_BY_LOGO),
        }

    def investment_amount_text(self) -> str:
        return self.text(self.INVESTMENT_AMOUNT).strip()

    def minimum_ticket_text(self) -> str:
        return self.text(self.MINIMUM_TICKET).strip()

    def co_investment_row_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.CO_INVESTMENT_ROW).all_inner_texts()]

    # ---- 03 Gallery & Supporting Documents -------------------------------
    def gallery_image_count(self) -> int:
        return self.page.locator(self.GALLERY_IMAGE).count()

    def resource_title_text(self, index: int = 0) -> str:
        return self.page.locator(self.RESOURCE_TITLE).nth(index).inner_text().strip()

    def resource_size_text(self, index: int = 0) -> str:
        return self.page.locator(self.RESOURCE_SIZE).nth(index).inner_text().strip()

    def click_download_resource(self, index: int = 0):
        """Returns the Playwright download object for the file the click
        triggers; the test asserts on its suggested_filename/path."""
        with self.page.expect_download() as download_info:
            self.page.locator(self.RESOURCE_DOWNLOAD_BUTTON).nth(index).click()
        return download_info.value

    def is_resource_unavailable_message_visible(self) -> bool:
        return self.is_visible(self.RESOURCE_UNAVAILABLE_MESSAGE)

    def click_download_button(self, index: int = 0) -> None:
        """Clicks Download WITHOUT waiting for a download event — for the
        "file was deactivated after render" case, where no download is
        expected to actually start."""
        self.page.locator(self.RESOURCE_DOWNLOAD_BUTTON).nth(index).click()

    def is_submit_inquiry_cta_keyboard_reachable(self, max_presses: int = 25) -> bool:
        return self.press_tab_until_focused(self.SUBMIT_INQUIRY_CTA, max_presses=max_presses)

    # ---- Submit Inquiry CTA -------------------------------------------------
    def is_submit_inquiry_cta_visible(self) -> bool:
        return self.is_visible(self.SUBMIT_INQUIRY_CTA)

    def is_submit_inquiry_cta_enabled(self) -> bool:
        disabled = self.get_attribute(self.SUBMIT_INQUIRY_CTA, "disabled")
        return self.is_submit_inquiry_cta_visible() and disabled is None

    def click_submit_inquiry(self) -> "BusinessOpportunityDetailPage":
        self.click(self.SUBMIT_INQUIRY_CTA)
        self.wait_for(self.INQUIRY_DIALOG, state="visible", timeout=15000)
        return self

    # ---- Express Your Interest modal ----------------------------------------
    def is_inquiry_modal_open(self) -> bool:
        return self.is_visible(self.INQUIRY_DIALOG)

    def close_inquiry_modal(self) -> None:
        self.click(self.INQUIRY_CLOSE_BUTTON)

    def visible_inquiry_field_keys(self) -> list:
        return [key for key in INQUIRY_FIELD_KEYS if self.is_visible(self.INQUIRY_FIELD_LOCATORS[key])]

    def fill_inquiry_field(self, field_key: str, value: str) -> None:
        locator = self.INQUIRY_FIELD_LOCATORS[field_key]
        if field_key == "inquiry_type":
            self.select_option(locator, label=value)
        else:
            self.type(locator, value)

    def fill_inquiry_form(self, values: dict) -> "BusinessOpportunityDetailPage":
        for key, value in values.items():
            self.fill_inquiry_field(key, value)
        return self

    def inquiry_field_value(self, field_key: str) -> str:
        return self.get_attribute(self.INQUIRY_FIELD_LOCATORS[field_key], "value") or ""

    def inquiry_field_error_text(self, field_key: str) -> str:
        return self.text(self.INQUIRY_FIELD_ERROR_LOCATORS[field_key]).strip()

    def is_inquiry_field_error_visible(self, field_key: str) -> bool:
        return self.is_visible(self.INQUIRY_FIELD_ERROR_LOCATORS[field_key])

    def is_inquiry_captcha_present(self) -> bool:
        return self.is_visible(self.INQUIRY_CAPTCHA_MOUNT) or self.page.locator(self.INQUIRY_CAPTCHA_MOUNT).count() > 0

    def click_submit_inquiry_button(self) -> None:
        self.click(self.INQUIRY_SUBMIT_BUTTON)

    def is_inquiry_submit_button_disabled(self) -> bool:
        return self.get_attribute(self.INQUIRY_SUBMIT_BUTTON, "disabled") is not None

    def inquiry_success_message_text(self) -> str:
        return self.text(self.INQUIRY_SUCCESS_MESSAGE).strip()

    def is_inquiry_success_visible(self) -> bool:
        return self.is_visible(self.INQUIRY_SUCCESS_MESSAGE)

    def inquiry_generic_error_text(self) -> str:
        return self.text(self.INQUIRY_GENERIC_ERROR).strip()
