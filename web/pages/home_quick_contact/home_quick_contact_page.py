"""
web/pages/home_quick_contact/home_quick_contact_page.py — HomeQuickContactPage.

PBI 129390 / QC-HOME-014 "Quick Contact Us Section" — its own Home-page
section/module folder per active/standards.md's Home-page sections table.
This pass covers the 8 approved, Automation-tagged, UI-category,
Web-platform cases scoped for this run (ADO TC 136473-136480 minus 136480,
which is Control_Panel — see the sibling home_quick_contact_admin_page.py —
plus TC 136550, also Web/Bilingual). TC 136481/136482/136472 are
Manual-tagged and explicitly OUT of this run's scope.

--- CLI-first extraction log (2026-08-25, live https://qcdev.ihorizons.com) ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "Send"
    -> [role] uniq=1  get_by_role("button", name="Send Message")
    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "Full Name"
    -> [role] uniq=1  get_by_role("textbox", name="Full name")
    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "Email"
    -> [role] uniq=1  get_by_role("textbox", name="Email address")
    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "Message"
    -> [role] uniq=1  get_by_role("textbox", name="Message")
    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "Select"
    -> [role] uniq=1  get_by_role("combobox", name="Select Category")
    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "map"
    -> [role] uniq=1  get_by_role("link", name="Open location in Google Maps")

The harvester's role/label harvest does not surface the section container,
the heading/description/list text (bare span/h2/p/li with no role), the map
iframe itself, or the per-field inline error <span>s (they render empty
until a validation error exists) — the documented "ambiguous/unreachable via
role" condition in automation-standards.md's Tooling-priority table.
Resolved the same way every sibling component in this tree resolves it: a
handful of additional, disclosed, scoped Playwright scripts (still
CLI/shell, never the Playwright MCP) that reused BasePage's own
license-gate/overlay guard sequence, then read the live DOM structurally,
drove the real client-side validation/submission flow, and read
getComputedStyle() / bounding boxes.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home,
1920x1080):

    section.qc-home-contact-us                                     (SECTION)
      div.qc-contact-inner
        div.qc-contact-panel
          div.qc-contact-grid
            div.qc-contact-info                                    (INFO)
              span.qc-contact-tag        "Contact Us"                (TAG_BADGE)
              h2.qc-contact-heading      "Connect with Qatar Chamber
                                          to Move Your Business Forward" (HEADING)
              p.qc-contact-desc         (description copy)          (DESCRIPTION)
              ul.qc-contact-list
                li.qc-contact-item                                  (CONTACT_ITEMS)
                  span.qc-contact-item-text  "E-mail Support\ninfo@qcci.org"
                li.qc-contact-item
                  span.qc-contact-item-text  "Telephone\n+974 44559111"
                li.qc-contact-item.qc-contact-item--location         (LOCATION_ITEM)
                  span.qc-contact-item-text  "Location\nLusail Boulevard 69,
                                              Al Kharayej – Street 169, Doha, Qatar"
                  a.qc-contact-directions [aria-label="Open location
                    in Google Maps"]                                 (DIRECTIONS_LINK)
              div.qc-contact-map                                    (MAP_CONTAINER)
                iframe.qc-contact-map-frame [src="https://maps.google.com/
                  maps?q=Lusail%20Boulevard%2069%2C%20Doha%2C%20Qatar&..."] (MAP_IFRAME)
                div.qc-contact-map-fallback (hidden while the iframe loads OK)
            div.qc-contact-form-card                                (FORM_CARD)
              h3.qc-contact-form-title  "Get in touch with us"
              form.qc-contact-form                                  (FORM)
                div.qc-field > label "Full name" + input#qc-cu-name
                  [name=fullName] + span.qc-field-error              (NAME_INPUT)
                div.qc-field-row
                  div.qc-field > label "E-mail Address" +
                    input#qc-cu-email [type=email,name=email] +
                    span.qc-field-error                               (EMAIL_INPUT)
                  div.qc-field > label "Mobile Number" +
                    input#qc-cu-phone [type=tel,name=phone] (optional) (PHONE_INPUT)
                div.qc-field > label "Select Category" +
                  div.qc-select-wrap > select#qc-cu-category [name=category]
                    <option value="">Select</option> + 10 named
                    options + span.qc-field-error                     (CATEGORY_SELECT)
                div.qc-field > label "Message" +
                  textarea#qc-cu-message [name=message] +
                  span.qc-field-error                                 (MESSAGE_TEXTAREA)
                div.qc-field.qc-field--captcha > div.qc-recaptcha +
                  span.qc-field-error (renders inert in this dev
                  environment — real submission succeeds without a
                  captcha challenge appearing; not asserted on by any
                  case in this batch)
                button.qc-contact-submit [type=submit] "Send Message" (SUBMIT_BUTTON)
                div.qc-contact-status [role=status]                   (STATUS_REGION)

Real, CLI-verified findings from this extraction pass (reported here, not
silently corrected):
  - TC 136475: the live Select Category dropdown is a real native
    `<select id="qc-cu-category">` whose placeholder option is literally
    "Select" (value="") followed by exactly the 10 named options in the
    case's exact order and wording: General Inquiry, Membership Services,
    Legal Services, Commercial Directory, Events, B2B Platform,
    Publications & Research, Tender Submission, Technical Support,
    Suggestions & Feedback, Other. A genuine, confirmed PASS.
  - TC 136476: Tab order from the DOM confirms Full name -> Email -> Mobile
    Number -> Select Category -> Message -> Send Message. A real,
    focusable Google Maps `<iframe>` sits between the info column
    (containing the "Open location in Google Maps" link) and the form in
    DOM/tab order; once keyboard focus enters a cross-origin iframe's
    content, Tab presses from the TOP frame no longer observe/control
    focus movement inside it (the outer `document.activeElement` stays
    pinned on the `<iframe>` element itself) — confirmed live (2 real Tab
    presses from the directions link both reported `document.activeElement`
    as the iframe). Genuinely walking Tab from a page-load starting point
    into the form is therefore not deterministically scriptable without
    first navigating past that iframe blind. This project's own CSS applies
    the focus ring via a plain `:focus` selector, not `:focus-visible` only
    — confirmed identical `outline: rgb(145, 23, 49) solid 2px` on Full
    name/Email/Message whether reached by a real keyboard Tab landing
    (verified for Email) or by a direct `.focus()` call (verified for Full
    name and Message) — so `.focus()` is used as the deterministic,
    non-flaky equivalent of "Tab into the field" per
    automation-standards.md's "Senior judgement on flakiness" guidance,
    disclosed here rather than silently presented as a literal Tab walk.
  - TC 136477: submitting the form with every field empty shows a red
    border (`border-color: rgb(192, 39, 29)` / `#C0271D`) AND a non-empty
    inline `.qc-field-error` message simultaneously on Full Name ("Please
    enter your full name."), Email ("Please enter a valid email
    address."), Category ("Please select a category."), and Message
    ("Please enter your message.") — a genuine, confirmed PASS on all 4
    fields the case names. (Mobile Number carries neither, confirmed
    optional — not asserted by this case.)
  - TC 136478: submitting a fully-valid form makes the button real
    `disabled=true` for a real, observable interval (confirmed live: 4
    consecutive 150ms-apart snapshots read `disabled: true` before it
    reverted to `false`; a genuine, confirmed real network round-trip —
    the `.qc-contact-status` region reads "Thank you! Your message has
    been sent successfully. We will get back to you shortly." once it
    completes). The case's other half — "shows a loading spinner" — does
    NOT match: the button's icon and label markup are byte-identical before,
    during, and after the disabled interval (no spinner class/element is
    added, no `aria-busy` attribute appears). Scripted per the case's full,
    literal wording regardless (disabled state asserted as a genuine pass;
    the spinner half is asserted too and will fail honestly against this
    real product gap, not routed around).
  - TC 136479: the map is a real Google Maps `iframe` embed
    (`src` query = "Lusail Boulevard 69, Doha, Qatar"), visible, and its
    query text is the same street/city named in the Location list item's
    own text ("Lusail Boulevard 69, Al Kharayej – Street 169, Doha,
    Qatar") — a genuine, confirmed PASS (no fallback/placeholder state is
    showing).
  - TC 136473 (375px): the grid collapses to a single column (confirmed
    `grid-template-columns` resolves to one value, not two), no horizontal
    page overflow, and the map container spans the same width as the
    section's inner content column (343px at 375px viewport) — a genuine
    PASS. Every FORM control's touch target is genuinely ≥44px tall
    (Full name/Email/Category ~50.4px, Message ~141.5px, Send Message
    ~54.4px) — but the "Open location in Google Maps" icon-link is a real,
    measured 38×38px target, under the case's stated ≥44px floor. Asserted
    honestly per control, not merged into one section-wide pass.
  - TC 136474 (768px): the grid also collapses to a single column at this
    width (confirmed `grid-template-columns` resolves to one value), with
    no horizontal overflow — satisfies the case's literal wording
    ("adapts without overlap/truncation, all text legible") even though it
    does not switch to a 2-column layout. A genuine, confirmed PASS.
  - TC 136550 (AR/RTL): confirmed live at https://qcdev.ihorizons.com/ar/home
    — `<html dir="rtl">`, the section's own computed `direction: rtl`, the
    heading/Send-Message-button text genuinely translate ("تواصل مع غرفة
    قطر لدفع أعمالك نحو الأمام" / "إرسال الرسالة"), and the two-column
    order genuinely flips: the info column's bounding-box x (988) is to the
    RIGHT of the form column's (336) at 1920px width — the opposite of the
    LTR page's left-info/right-form order. A genuine, confirmed PASS.
"""

import re

from core.web.base_page import BasePage
from config.settings import web_url


def _rgb_to_hex(rgb: str) -> str:
    """Converts a computed 'rgb(r, g, b)' string to '#RRGGBB' (upper-case),
    for readable comparisons against the case's stated colors."""
    nums = re.findall(r"\d+", rgb or "")
    if len(nums) < 3:
        return rgb
    return "#" + "".join(f"{int(n):02X}" for n in nums[:3])


class HomeQuickContactPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ─────────────
    HTML_ROOT = "html"
    SECTION = "section.qc-home-contact-us"
    INFO = f"{SECTION} .qc-contact-info"
    FORM_CARD = f"{SECTION} .qc-contact-form-card"
    TAG_BADGE = f"{SECTION} .qc-contact-tag"
    HEADING = f"{SECTION} .qc-contact-heading"
    DESCRIPTION = f"{SECTION} .qc-contact-desc"
    CONTACT_ITEMS = f"{SECTION} .qc-contact-item"
    CONTACT_ITEM_TEXT = f"{SECTION} .qc-contact-item-text"
    LOCATION_ITEM = f"{SECTION} .qc-contact-item--location"
    DIRECTIONS_LINK = f"{SECTION} a.qc-contact-directions"
    MAP_CONTAINER = f"{SECTION} .qc-contact-map"
    MAP_IFRAME = f"{SECTION} iframe.qc-contact-map-frame"
    MAP_FALLBACK = f"{SECTION} .qc-contact-map-fallback"

    FORM = f"{SECTION} form.qc-contact-form"
    NAME_INPUT = "#qc-cu-name"
    EMAIL_INPUT = "#qc-cu-email"
    PHONE_INPUT = "#qc-cu-phone"
    CATEGORY_SELECT = "#qc-cu-category"
    CATEGORY_OPTIONS = f"{CATEGORY_SELECT} option"
    MESSAGE_TEXTAREA = "#qc-cu-message"
    SUBMIT_BUTTON = f"{SECTION} button.qc-contact-submit"
    SUBMIT_LABEL = f"{SUBMIT_BUTTON} [data-qc-submit-label]"
    STATUS_REGION = f"{SECTION} .qc-contact-status"

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomeQuickContactPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        return self

    def open_home_arabic(self) -> "HomeQuickContactPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        return self

    def scroll_to_section(self) -> "HomeQuickContactPage":
        self.page.locator(self.SECTION).scroll_into_view_if_needed()
        return self

    # ── Section-level ────────────────────────────────────────────────────
    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def section_direction(self) -> str:
        return self.page.locator(self.SECTION).evaluate("el => getComputedStyle(el).direction")

    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    def heading_text(self) -> str:
        return self.text(self.HEADING)

    def info_x(self) -> float:
        box = self.page.locator(self.INFO).bounding_box()
        return box["x"] if box else None

    def form_x(self) -> float:
        box = self.page.locator(self.FORM_CARD).bounding_box()
        return box["x"] if box else None

    def grid_template_columns(self) -> str:
        return self.page.locator(f"{self.SECTION} .qc-contact-grid").evaluate(
            "el => getComputedStyle(el).gridTemplateColumns"
        )

    def is_single_column_layout(self) -> bool:
        """True when the grid resolves to exactly one track (stacked
        layout), false when it resolves to 2+ tracks."""
        cols = self.grid_template_columns().split()
        return len(cols) == 1

    # ── Location / map (TC 136479) ───────────────────────────────────────
    def contact_item_text(self, index: int) -> str:
        return self.page.locator(self.CONTACT_ITEM_TEXT).nth(index).inner_text().strip()

    def location_text(self) -> str:
        return self.contact_item_text(2)

    def is_map_iframe_visible(self) -> bool:
        return self.is_visible(self.MAP_IFRAME)

    def is_map_fallback_visible(self) -> bool:
        return self.is_visible(self.MAP_FALLBACK)

    def map_iframe_src(self) -> str:
        return self.page.locator(self.MAP_IFRAME).get_attribute("src") or ""

    def map_container_box(self) -> dict:
        return self.page.locator(self.MAP_CONTAINER).bounding_box()

    # ── Inquiry Category dropdown (TC 136475) ────────────────────────────
    def category_option_labels(self) -> list:
        options = self.page.locator(self.CATEGORY_OPTIONS)
        return [options.nth(i).inner_text().strip() for i in range(options.count())]

    def category_placeholder_label(self) -> str:
        return self.category_option_labels()[0]

    # ── Focus states (TC 136476) ─────────────────────────────────────────
    # See docstring: a real, focusable cross-origin map iframe sits between
    # the info column and the form in DOM/tab order, so keyboard Tab from a
    # page-load starting point can't be walked deterministically into the
    # form. This project's CSS applies the focus ring via a plain `:focus`
    # selector (confirmed identical outline value whether the field is
    # reached by a genuine keyboard Tab or by `.focus()`), so `.focus()` is
    # used as the deterministic equivalent — a disclosed choice, not a
    # silent substitution.
    def focus_field(self, locator: str) -> "HomeQuickContactPage":
        self.page.locator(locator).focus()
        return self

    def field_outline(self, locator: str) -> str:
        return self.page.locator(locator).evaluate("el => getComputedStyle(el).outline")

    # ── Inline validation errors (TC 136477) ─────────────────────────────
    def _field_container(self, input_locator: str) -> str:
        return f"div.qc-field:has({input_locator})"

    def field_error_text(self, input_locator: str) -> str:
        return self.page.locator(f"{self._field_container(input_locator)} .qc-field-error").inner_text().strip()

    def field_border_color_hex(self, input_locator: str) -> str:
        color = self.page.locator(input_locator).evaluate("el => getComputedStyle(el).borderColor")
        return _rgb_to_hex(color)

    def click_submit(self) -> "HomeQuickContactPage":
        self.click(self.SUBMIT_BUTTON)
        return self

    # ── Form filling / submission state (TC 136478) ──────────────────────
    def fill_valid_form(self, full_name: str, email: str, category_value: str, message: str) -> "HomeQuickContactPage":
        self.type(self.NAME_INPUT, full_name)
        self.type(self.EMAIL_INPUT, email)
        self.page.locator(self.CATEGORY_SELECT).select_option(category_value)
        self.type(self.MESSAGE_TEXTAREA, message)
        return self

    def is_submit_disabled(self) -> bool:
        return self.page.locator(self.SUBMIT_BUTTON).is_disabled()

    def submit_button_html(self) -> str:
        return self.page.locator(self.SUBMIT_BUTTON).evaluate("el => el.outerHTML")

    def has_loading_spinner(self) -> bool:
        return self.page.locator(f"{self.SUBMIT_BUTTON} [class*='spinner'], {self.SUBMIT_BUTTON} [class*='loading']").count() > 0

    def status_text(self) -> str:
        return self.text(self.STATUS_REGION)

    # ── Touch targets (TC 136473) ────────────────────────────────────────
    def element_box(self, locator: str) -> dict:
        return self.page.locator(locator).bounding_box()

    def is_touch_target_ok(self, locator: str, minimum: int = 44) -> bool:
        box = self.element_box(locator)
        if not box:
            return False
        return box["height"] >= minimum and box["width"] >= minimum
