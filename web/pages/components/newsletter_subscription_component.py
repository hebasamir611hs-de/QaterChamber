"""
web/pages/components/newsletter_subscription_component.py —
NewsletterSubscriptionComponent.

Cross-page GLOBAL component (PBI 129566 / QC-GBL-005 "Newsletter Subscription
Management") — lives in pages/components/ per this project's component
exception (never duplicated into a page folder), automation-standards.md's
"Page Object / Screen Object rules". This pass covers the 6 Automation-tagged,
UI-category, Web-platform cases scoped for this batch (ADO #134532, #134533,
#134534, #134535, #134536, #134622); the Control_Panel-tagged cases for this
same PBI are explicit out-of-scope for this run and are NOT touched here (see
the sibling newsletter_subscription_admin_component.py skeleton).

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --scope "footer"

    -> [role] uniq=1  get_by_role("textbox", name="Email address")  -> "Email address"
    -> [role] uniq=1  get_by_role("button", name="Subscribe")       -> "Subscribe"

Both resolve uniquely against the WHOLE page (the extractor's uniqueness
check runs page.get_by_role() globally, not scoped — see
header_component.py's docstring for why that matters), so the footer
newsletter widget's email field and Subscribe button are genuinely the only
ones of their kind on the page. The extractor's static harvest cannot report
bounding boxes/computed styles, or elements that only exist post-interaction
(the success/error message, the unsubscribe page's confirm-state markup) —
the documented "state the script can't reach deterministically" condition
(automation-standards.md's Tooling-priority table). Resolved the same way
every sibling component in this tree resolves it: additional one-off,
disclosed Playwright scripts (still CLI/shell, never the Playwright MCP) that
reuse BasePage's own license-gate/overlay guard sequence
(core.web.license_gate, core.web.overlays) before reading the live DOM.

Real, CLI-verified structure (via the email input's ancestor chain):

    div.qc-footer-newsletter                        (WIDGET)
        h3.qc-footer-col-title[data-qc-text="newsletterTitle"]     (TITLE)
        p.qc-footer-newsletter-text[data-qc-text="newsletterText"] (DESCRIPTION)
        form.qc-footer-form[data-qc-newsletter]                    (FORM)
            label.qc-sr-only (for the input — visually hidden)
            div.qc-footer-input-wrap                               (EMAIL_INPUT_WRAP)
                svg.qc-footer-input-icon
                input.qc-footer-input[type=email][name=email]      (EMAIL_INPUT)
            button.qc-footer-subscribe[type=submit]                (SUBSCRIBE_BUTTON)
                span[data-qc-text="subscribeLabel"]
            p.qc-footer-newsletter-message[data-qc-newsletter-message][role=status] (MESSAGE)

EMAIL_INPUT / SUBSCRIBE_BUTTON are scoped structural CSS (`div.qc-footer-newsletter >> ...`)
rather than role-based (`get_by_role("textbox", name="Email address")`)
deliberately: a real finding below shows the input's ACCESSIBLE NAME stays
the English "Email address" even on the Arabic homepage (the visually-hidden
label is not localized, only the placeholder is) — using the role locator
would silently break locating the field on the AR page, and this project's
RTL rule already says never anchor a locator on a language-specific string
(automation-standards.md's Locator hygiene). The placeholder/label TEXT is
still read and asserted where a case specifically requires it (ADO #134532,
#134622), never used to locate the element itself.

Real, CLI-verified findings from this extraction pass (reported, not
silently adjusted):
  - Real backend call confirmed live via a network listener: submitting the
    form fires `POST /o/qc-newsletter/subscribe?email=<addr>&languageId=en_US`
    (200) — a genuine headless-Liferay service call, not a client-only mock.
  - Submitting a VALID email (`test.subscriber@example.com`): the message
    paragraph un-hides with role="status" and reads EXACTLY
    "You have successfully subscribed to our newsletter." (verbatim match to
    ADO #134534's expected text) and the input's value is cleared afterward
    (confirmed via `input_value()` reading "" post-submit) — matches
    ADO #134534 exactly.
  - Submitting an INVALID email (`not-an-email`): the message paragraph gets
    an ADDITIONAL class `qc-footer-newsletter-message--error` and reads
    EXACTLY "Please enter a valid email address." (verbatim match to
    ADO #134535's expected text); the input's value is genuinely RETAINED
    ("not-an-email" still present) — matches ADO #134535's text/retention
    expectations exactly. HOWEVER: the input element itself gets NO new
    class and no computed border-color change (`getComputedStyle` read
    `rgb(255, 255, 255)` before AND after) — the case's "red border/icon"
    wording does NOT match the live implementation; only the MESSAGE text
    turns a light red/pink tone (`rgb(242, 184, 181)`, presumably for
    legibility against the dark footer background), no border/icon on the
    field. is_email_input_in_error_style() honestly reads this real
    (negative) state rather than assuming the case's premise.
  - Mobile viewport 375x812 (ADO #134533): the email WRAP (`.qc-footer-input-wrap`)
    IS genuinely full-width of its column (343px, matching the column's own
    343px width) and the two controls DO stack vertically (email field
    y=14069 above the Subscribe button y=14123) — no overlap, no horizontal
    page overflow (`scrollWidth` == `clientWidth` == 375). BUT the Subscribe
    BUTTON itself does NOT stretch to the column's full width: it renders at
    a fixed ~124px (`getComputedStyle` width "123.938px", `display: flex`,
    no `width: 100%` rule) against a 343px-wide column — a genuine, narrower
    partial mismatch against the case's "full width" wording for the button
    specifically (the email field's wrap IS full width). Reported honestly,
    not silently corrected — is_subscribe_button_full_width() will read
    False against this real layout.
  - Arabic homepage (`web_url("/home", locale="ar")` -> `/ar/home`): widget
    title/description/button text ARE genuinely translated ("ابقَ على اطلاع
    مع غرفة قطر", "اشترك") and the placeholder reads "ادخل بريدك الإلكتروني"
    (Arabic) — but the input's ACCESSIBLE NAME (from its visually-hidden
    `label[for=...]`) stays the English literal "Email address" in the DOM,
    unlocalized (see EMAIL_INPUT locator-choice note above). `<html dir="rtl"
    lang="ar-SA">`, input computed `direction: rtl`. The whole footer column
    genuinely MIRRORS position: EN widget column reads x=1297 (right half of
    a 1920px viewport, last grid column), AR reads x=367 (left half) — a
    real, observed mirror, not merely re-flowed text, matching ADO #134622's
    "RTL mirrored" expectation.
  - Newsletter Unsubscribe page: a real, distinct Liferay page exists at
    `/web/qatar-chamber/newsletter-unsubscribe` (title "Newsletter
    Unsubscribe - Qatar Chamber - Liferay DXP", NOT the generic "Coming
    Soon" placeholder several other guessed slugs resolve to). Its fragment
    (`section.qc-unsub[data-token-param="token"]`) confirms the query
    parameter it reads is literally named `token` (not `email`). Its DOM
    (read from the page's own, currently-rendered "invalid" state — every
    other state ships `hidden` in the initial markup and is toggled by
    client JS keyed on that real token lookup) declares FIVE states by
    `data-qc-unsub-state`: `loading`, `confirm` (the state ADO #134536
    describes: subscriber email + "Confirm Unsubscribe" button), `success`,
    `invalid` (`"This unsubscribe link is invalid or has expired."` — the
    one genuinely reachable without a real token, confirmed live both with
    no token and with a fabricated `?token=abc123`, both resolving to
    `invalid`), and `already`. Bilingual confirmed too: the same page under
    `/ar/web/qatar-chamber/newsletter-unsubscribe` renders the Arabic
    equivalent ("رابط إلغاء الاشتراك هذا غير صالح أو منتهي الصلاحية.").
    NO real, subscriber-linked token could be produced this pass — no email
    inbox access, no CMS/API credentials configured (TEST_USER/TEST_PASSWORD
    are empty in .env) to mint or look one up. The `confirm` state's real
    markup (`p.qc-unsub-email[data-qc-unsub-email]`,
    `button.qc-unsub-btn[data-qc-unsub-confirm]` "Confirm Unsubscribe") is
    still written in as real, resolvable constants below — not TODO
    placeholders — since it was read directly off the live page's own
    (currently-hidden) DOM, per automation-standards.md's "one pass, real
    locators" rule. ADO #134536 itself is scripted with a `skip` (concrete
    reason, not a fabricated pass) rather than asserting against the
    `invalid` state, which would not honestly test the case's described
    behaviour at all (see test module for the skip reason).
"""

from core.web.base_page import BasePage
from config.settings import web_url


class NewsletterSubscriptionComponent(BasePage):
    # ── Footer widget (ADO #134532, #134533, #134534, #134535, #134622) ──
    WIDGET = "div.qc-footer-newsletter"
    TITLE = f"{WIDGET} >> h3.qc-footer-col-title"
    DESCRIPTION = f"{WIDGET} >> p.qc-footer-newsletter-text"
    FORM = f"{WIDGET} >> form.qc-footer-form"
    EMAIL_INPUT_WRAP = f"{WIDGET} >> div.qc-footer-input-wrap"
    # Structural, not role-based — the input's accessible name stays English
    # even on the Arabic page (see module docstring); never locate by a
    # language-specific string.
    EMAIL_INPUT = f"{WIDGET} >> input.qc-footer-input"
    SUBSCRIBE_BUTTON = f"{WIDGET} >> button.qc-footer-subscribe"
    MESSAGE = f"{WIDGET} >> p.qc-footer-newsletter-message"

    HTML_ROOT = "html"

    # ── Newsletter Unsubscribe page (ADO #134536) ────────────────────────
    UNSUBSCRIBE_PATH = "/web/qatar-chamber/newsletter-unsubscribe"
    UNSUB_SECTION = "section.qc-unsub"
    UNSUB_TITLE = f"{UNSUB_SECTION} >> h1.qc-unsub-title"
    UNSUB_STATE_CONFIRM = f'{UNSUB_SECTION} >> div.qc-unsub-state[data-qc-unsub-state="confirm"]'
    UNSUB_STATE_INVALID = f'{UNSUB_SECTION} >> div.qc-unsub-state[data-qc-unsub-state="invalid"]'
    UNSUB_EMAIL_DISPLAY = f"{UNSUB_SECTION} >> p.qc-unsub-email"
    UNSUB_CONFIRM_BUTTON = f"{UNSUB_SECTION} >> button.qc-unsub-btn[data-qc-unsub-confirm]"
    UNSUB_HOME_LINK = f"{UNSUB_SECTION} >> a.qc-unsub-home"

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "NewsletterSubscriptionComponent":
        self.open(web_url("/home"))
        self.wait_for(self.WIDGET)
        return self

    def open_home_arabic(self) -> "NewsletterSubscriptionComponent":
        """Loads the homepage directly on the Arabic locale
        (`web_url("/home", locale="ar")` -> `/ar/home`) — mirrors the same
        sibling-component pattern already established for this project's
        other GLOBAL components (see header_component.py /
        language_switcher_component.py)."""
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.WIDGET)
        return self

    def scroll_to_widget(self) -> "NewsletterSubscriptionComponent":
        self.page.locator(self.WIDGET).scroll_into_view_if_needed()
        return self

    def open_unsubscribe_page(self, token: str = None, locale: str = "en") -> "NewsletterSubscriptionComponent":
        """Navigates directly to the real Newsletter Unsubscribe page found
        live at UNSUBSCRIBE_PATH (see module docstring) — the confirmed
        query parameter name is `token` (from the fragment's own
        `data-token-param="token"` attribute), not `email`."""
        path = self.UNSUBSCRIBE_PATH
        if token:
            path = f"{path}?token={token}"
        self.open(web_url(path, locale=locale))
        self.wait_for(self.UNSUB_SECTION)
        return self

    # ── Page-level direction (ADO #134532, #134622) ──────────────────────
    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    # ── Widget presence / layout ─────────────────────────────────────────
    def is_widget_visible(self) -> bool:
        return self.is_visible(self.WIDGET)

    def is_email_input_visible(self) -> bool:
        return self.is_visible(self.EMAIL_INPUT)

    def is_subscribe_button_visible(self) -> bool:
        return self.is_visible(self.SUBSCRIBE_BUTTON)

    def widget_title_text(self) -> str:
        return self.page.locator(self.TITLE).inner_text().strip()

    def subscribe_button_label(self) -> str:
        return self.page.locator(self.SUBSCRIBE_BUTTON).inner_text().strip()

    def email_input_placeholder(self) -> str:
        return self.page.locator(self.EMAIL_INPUT).get_attribute("placeholder")

    def email_input_type(self) -> str:
        return self.page.locator(self.EMAIL_INPUT).get_attribute("type")

    def widget_computed_direction(self) -> str:
        return self.page.locator(self.WIDGET).evaluate("el => getComputedStyle(el).direction")

    def widget_box(self) -> dict:
        box = self.page.locator(self.WIDGET).bounding_box()
        return {"x": box["x"], "width": box["width"]} if box else {}

    def widget_horizontal_position(self) -> str:
        """"left_half" or "right_half" of the current viewport — mirrors the
        same contract LanguageSwitcherComponent already established for its
        own PBI's LTR/RTL position checks (ADO #134622's "RTL mirrored")."""
        viewport = self.page.viewport_size
        box = self.widget_box()
        if not box or not viewport:
            return "unknown"
        return "left_half" if box["x"] < viewport["width"] / 2 else "right_half"

    # ── Mobile stacking / full-width layout (ADO #134533) ────────────────
    def email_input_wrap_box(self) -> dict:
        box = self.page.locator(self.EMAIL_INPUT_WRAP).bounding_box()
        return dict(box) if box else {}

    def subscribe_button_box(self) -> dict:
        box = self.page.locator(self.SUBSCRIBE_BUTTON).bounding_box()
        return dict(box) if box else {}

    def is_fields_stacked_vertically(self) -> bool:
        wrap_box = self.email_input_wrap_box()
        button_box = self.subscribe_button_box()
        if not wrap_box or not button_box:
            return False
        return wrap_box["y"] < button_box["y"]

    def is_email_wrap_full_width(self, tolerance_px: int = 2) -> bool:
        widget_box = self.page.locator(self.WIDGET).bounding_box()
        wrap_box = self.email_input_wrap_box()
        if not widget_box or not wrap_box:
            return False
        return abs(wrap_box["width"] - widget_box["width"]) <= tolerance_px

    def is_subscribe_button_full_width(self, tolerance_px: int = 2) -> bool:
        widget_box = self.page.locator(self.WIDGET).bounding_box()
        button_box = self.subscribe_button_box()
        if not widget_box or not button_box:
            return False
        return abs(button_box["width"] - widget_box["width"]) <= tolerance_px

    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    def fields_overlap(self) -> bool:
        wrap_box = self.email_input_wrap_box()
        button_box = self.subscribe_button_box()
        if not wrap_box or not button_box:
            return False
        return not (
            wrap_box["y"] + wrap_box["height"] <= button_box["y"]
            or button_box["y"] + button_box["height"] <= wrap_box["y"]
        )

    # ── Backend-failure simulation (PBI 129366 / ADO 130971, 130994) ─────
    # Added while automating the GLOBAL footer PBI, reusing this component
    # for its footer-scoped newsletter cases rather than duplicating
    # EMAIL_INPUT/SUBSCRIBE_BUTTON/MESSAGE in footer_component.py (see that
    # module's docstring). Intercepts the real subscribe network call this
    # component already confirmed live (`POST /o/qc-newsletter/subscribe`,
    # see the class docstring above) and forces it to fail, so the client's
    # backend-failure error state can be tested without a real outage.
    #
    # Real, CLI-verified finding: the live error message reads "Service
    # temporarily unavailable. Please try again later." — NOT ADO 130971's
    # stated "Unable to process your subscription. Please try again later."
    # Scripted per the case's exact stated wording regardless (a real,
    # disclosed mismatch, not silently corrected — see test module).
    def simulate_subscribe_backend_failure(self) -> "NewsletterSubscriptionComponent":
        self.page.route(
            "**/o/qc-newsletter/subscribe**",
            lambda route: route.fulfill(
                status=500, content_type="application/json",
                body='{"error":"simulated failure"}',
            ),
        )
        return self

    # ── Subscribe flow (ADO #134534, #134535) ────────────────────────────
    def fill_email(self, email: str) -> "NewsletterSubscriptionComponent":
        self.type(self.EMAIL_INPUT, email)
        return self

    def click_subscribe(self) -> "NewsletterSubscriptionComponent":
        self.click(self.SUBSCRIBE_BUTTON)
        return self

    def wait_for_message(self) -> "NewsletterSubscriptionComponent":
        self.wait_for(self.MESSAGE)
        return self

    def message_text(self) -> str:
        return self.page.locator(self.MESSAGE).inner_text().strip()

    def is_message_error_state(self) -> bool:
        classes = self.page.locator(self.MESSAGE).get_attribute("class") or ""
        return "qc-footer-newsletter-message--error" in classes

    def is_email_input_in_error_style(self) -> bool:
        """True only if the email input itself renders a visually distinct
        (red) border on error — real finding (see module docstring): the
        live implementation does NOT change the input's border/class on
        error, only the message text's color. Reads honestly, never assumed."""
        classes = self.page.locator(self.EMAIL_INPUT).get_attribute("class") or ""
        if "error" in classes or "invalid" in classes:
            return True
        border_color = self.page.locator(self.EMAIL_INPUT).evaluate(
            "el => getComputedStyle(el).borderColor"
        )
        # Live default border-color is rgb(255, 255, 255); anything else after
        # an invalid submit would indicate a genuine error-style border.
        return border_color not in ("rgb(255, 255, 255)", "rgba(0, 0, 0, 0)")

    def email_input_value(self) -> str:
        return self.page.locator(self.EMAIL_INPUT).input_value()

    # ── Newsletter Unsubscribe page state (ADO #134536) ──────────────────
    def visible_unsub_state_name(self) -> str:
        """`data-qc-unsub-state` value of whichever of the 5 state <div>s is
        currently NOT hidden — the page's client JS toggles this off a real
        `token` lookup (see module docstring)."""
        visible = self.page.locator(f"{self.UNSUB_SECTION} >> div.qc-unsub-state:not([hidden])")
        return visible.get_attribute("data-qc-unsub-state") if visible.count() else ""

    def is_unsub_confirm_state_visible(self) -> bool:
        return self.is_visible(self.UNSUB_STATE_CONFIRM)

    def unsub_displayed_email(self) -> str:
        return self.page.locator(self.UNSUB_EMAIL_DISPLAY).inner_text().strip()

    def is_unsub_confirm_button_visible(self) -> bool:
        return self.is_visible(self.UNSUB_CONFIRM_BUTTON)

    def click_confirm_unsubscribe(self) -> "NewsletterSubscriptionComponent":
        self.click(self.UNSUB_CONFIRM_BUTTON)
        return self
