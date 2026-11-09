"""
web/pages/components/newsletter_subscription_component.py —
NewsletterSubscriptionComponent.

Public-site footer "Stay Updated with Qatar Chamber" newsletter-subscription
widget — PBI 129566 (QC-GBL-005 — Newsletter Subscription Management), the
`Web`-platform half of this batch (see
cms/pages/components/newsletter_subscription_admin_component.py for the
Control_Panel "compose a newsletter issue" half — a separate object/surface
under the same PBI). This is a global, cross-cutting footer component
(rendered on every page, not just Home) — lives under `pages/components/`
per the plugin's own flat shared-component exception, and per this
project's pre-existing skeleton at this exact path (see that file's own
placeholder before this batch).

CONFIRMED LIVE 2026-09-19/20 (scripted Playwright probe against qcdev's
`/en/home`, ANONYMOUS/unauthenticated context — this is a genuinely public,
unauthenticated widget, never behind login, confirmed by never loading
`.auth/state.json` for this class's own tests):

  - Email field: a native `<input type="email" required>` with placeholder
    "Enter your email address" — resolved via
    `get_by_placeholder("Enter your email address")`. `get_by_role`/
    `get_by_label` were tried first per locator-priority and do not resolve
    (this field carries no `<label for>`/`aria-label` wiring an accessible
    name to); the placeholder is the only stable, unique text. Its `id`
    carries a randomized per-render suffix (confirmed live twice,
    "qc-footer-email-eggv" one render, a different suffix the next) — never
    hardcode it, the placeholder-based locator is the stable one.
  - Subscribe button: `get_by_role("button", name="Subscribe", exact=True)`.
  - Validation is 100% native HTML5 constraint validation
    (`type="email"` + `required`) — NO custom JS validator on this widget,
    a real, confirmed contrast with the CMS Newsletter Management form's
    own custom, partially-cosmetic validation (see NewsletterAdminPage's
    own module docstring):
      * Empty submit: the browser's own `validationMessage` reads "Please
        fill out this field." and the click's underlying form submission is
        blocked entirely — confirmed live via `element.checkValidity()`
        immediately reporting `false` and zero matching network requests
        firing.
      * Whitespace-only submit: a `type="email"` input strips leading/
        trailing whitespace as part of the browser's OWN value-sanitization
        algorithm before constraint validation ever runs — confirmed live
        that `fill("   ")` leaves `element.value === ""` — so this produces
        the IDENTICAL blocked-submit / "Please fill out this field."
        behavior as the empty case above, not a distinct code path.
      * Invalid format (no "@", e.g. "not-an-email"): native message
        "Please include an '@' in the email address. '<value>' is missing
        an '@'." — this exact wording is the browser engine's OWN built-in
        text (Chromium here), not this project's copy, and will differ by
        browser/locale; this class's `email_validation_message()` exposes
        the raw message for a caller to assert non-emptiness/an "@"-related
        hint on, never the literal Chromium string.
      * Valid submit: fires a real `GET /o/qc-newsletter/subscribe?
        email=<addr>&languageId=en_US&recaptchaToken=...` request (a real
        JAX-RS endpoint backing the "Newsletter Subscriber" Object
        Definition — confirmed present, `(view only)` in Object Authoring's
        own index, so it has no admin create/edit/delete UI) and the footer
        section replaces the form with the confirmation text "You have
        successfully subscribed to our newsletter." — confirmed live
        end-to-end with a disposable `qctest-<uuid>@example.com` address.

  - NO SAFE TEARDOWN PATH — disclosed, not routed around (see
    cms-profile.md's Test-Data Policy and cms-testing.md §9 "no
    programmatic way to delete created content"): "Newsletter Subscriber"
    is `(view only)` in Object Authoring (no manage-<slug> form exists for
    it to delete through), and the site's own self-service unsubscribe page
    (`/en/newsletter-unsubscribe`) requires a per-subscriber token only
    ever delivered by a real confirmation email this suite has no inbox
    access to read — confirmed live: visiting that page with no token
    renders "This unsubscribe link is invalid or has expired." Accepted
    here as a standing, disclosed limitation (not escalated per
    cms-testing.md §9) because every test uses a disposable
    `qctest-<uuid>@example.com` address on the reserved RFC 2606
    `example.com` domain — an inert row behind a view-only admin surface,
    not a real mailbox, receives no mail, and cannot be spammed. Escalate
    for a real teardown path (an Administrator-only delete surface, or a
    documented Headless Delivery API write) before this suite scales beyond
    a handful of disposable rows.
"""

from core.web.base_page import BasePage
from config.settings import web_url

EMAIL_INPUT_PLACEHOLDER = "Enter your email address"
SUCCESS_MESSAGE_TEXT = "You have successfully subscribed to our newsletter."


class NewsletterSubscriptionComponent(BasePage):
    # ── Widget-scoped structural locators (PBI 129366 footer cases) ──────
    # Re-verified live 2026-10-21 (anonymous /en/home, 1920x1080):
    # `tools/extract_locators.py --scope div.qc-footer-newsletter` resolves
    # the input/button by role ("Email address" / "Subscribe"), but those
    # accessible names are English text and the footer cases also run on
    # /ar/home (ADO 130993/130994). The structural classes below are
    # locale-agnostic and were confirmed present in the live widget DOM by a
    # one-off scripted probe (div.qc-footer-newsletter > form.qc-footer-form >
    # div.qc-footer-input-wrap > input.qc-footer-input[type=email] +
    # button.qc-footer-subscribe; p.qc-footer-newsletter-message, which gets
    # `qc-footer-newsletter-message--error` on an invalid submit — the form
    # is `novalidate`, so the message is the site's own JS text, e.g.
    # "Please enter a valid email address.").
    WIDGET = "div.qc-footer-newsletter"
    EMAIL_INPUT = f"{WIDGET} >> input.qc-footer-input"
    SUBSCRIBE_BUTTON = f"{WIDGET} >> button.qc-footer-subscribe"
    MESSAGE = f"{WIDGET} >> p.qc-footer-newsletter-message"
    MESSAGE_ERROR_CLASS = "qc-footer-newsletter-message--error"
    SUBSCRIBE_ENDPOINT_GLOB = "**/o/qc-newsletter/subscribe**"
    HTML_ROOT = "html"

    def open_home(self) -> "NewsletterSubscriptionComponent":
        self.open(web_url("/home"))
        return self

    def open_home_arabic(self) -> "NewsletterSubscriptionComponent":
        """Loads the homepage directly on the Arabic locale (`/ar/home`) and
        waits for the footer widget to render — same pattern as the other
        GLOBAL components' Arabic entry points."""
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.WIDGET, state="attached")
        return self

    def scroll_to_widget(self) -> "NewsletterSubscriptionComponent":
        """The footer widget is attached on load but off-screen at the bottom
        of the page; wait for it to attach (condition, not a sleep), then
        scroll it into view."""
        self.wait_for(self.WIDGET, state="attached")
        self.page.locator(self.WIDGET).scroll_into_view_if_needed()
        self.wait_for(self.WIDGET)
        return self

    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir") or ""

    # ── Widget presence ──────────────────────────────────────────────────
    def is_widget_visible(self) -> bool:
        return self.is_visible(self.WIDGET)

    def is_email_input_visible(self) -> bool:
        return self.is_visible(self.EMAIL_INPUT)

    def is_subscribe_button_visible(self) -> bool:
        return self.is_visible(self.SUBSCRIBE_BUTTON)

    # ── Footer subscribe flow (ADO 130969-130971, 130993, 130994) ────────
    def fill_email(self, email: str) -> "NewsletterSubscriptionComponent":
        self.type(self.EMAIL_INPUT, email)
        return self

    def simulate_subscribe_backend_failure(self) -> "NewsletterSubscriptionComponent":
        """Intercepts the real subscribe call and answers HTTP 500, so the
        client's backend-failure state is tested without a real outage and
        without writing a subscriber row."""
        self.page.route(
            self.SUBSCRIBE_ENDPOINT_GLOB,
            lambda route: route.fulfill(
                status=500, content_type="application/json",
                body='{"error":"simulated failure"}',
            ),
        )
        return self

    def wait_for_message(self, timeout: int = 15000) -> "NewsletterSubscriptionComponent":
        """Waits until the message <p> is visible AND carries non-empty text —
        a visible-but-empty node would otherwise let message_text() read ""."""
        self.wait_for(self.MESSAGE, timeout=timeout)
        self.page.wait_for_function(
            "sel => { const m = document.querySelector(sel);"
            " return !!m && m.innerText.trim().length > 0; }",
            arg="div.qc-footer-newsletter p.qc-footer-newsletter-message",
            timeout=timeout,
        )
        return self

    def message_text(self) -> str:
        return self.page.locator(self.MESSAGE).inner_text().strip()

    def is_message_error_state(self) -> bool:
        classes = self.page.locator(self.MESSAGE).get_attribute("class") or ""
        return self.MESSAGE_ERROR_CLASS in classes

    # ---- Locators (as Locator objects — this field has no stable id/name,
    # see module docstring) -------------------------------------------------
    def _email_input(self):
        return self.page.get_by_placeholder(EMAIL_INPUT_PLACEHOLDER)

    # ---- Actions ------------------------------------------------------
    def enter_email(self, value: str) -> "NewsletterSubscriptionComponent":
        field = self._email_input()
        field.scroll_into_view_if_needed()
        field.fill(value)
        return self

    def click_subscribe(self) -> "NewsletterSubscriptionComponent":
        # Structural, widget-scoped locator (not the English role name) so the
        # same click works on /ar/home — see the class-level locator note.
        self.click(self.SUBSCRIBE_BUTTON)
        return self

    # ---- State queries --------------------------------------------------
    def email_value(self) -> str:
        return self._email_input().input_value()

    def is_email_field_valid(self) -> bool:
        return bool(self._email_input().evaluate("el => el.checkValidity()"))

    def email_validation_message(self) -> str:
        return self._email_input().evaluate("el => el.validationMessage") or ""

    def success_message_visible(self, timeout: int = 10000) -> bool:
        """Waits (bounded, never a blind sleep) for the confirmation text to
        render before answering — the real Subscribe click fires a
        recaptchaToken-bearing XHR (see module docstring) that is not
        synchronous with the click itself; an immediate, unwaited visibility
        check race-loses against that round trip live (confirmed:
        the very first version of this method used a bare `is_visible()`
        with no wait and intermittently reported the success text absent
        even on a real, valid subscribe)."""
        try:
            self.wait_for(f"text={SUCCESS_MESSAGE_TEXT}", timeout=timeout)
            return True
        except Exception:  # noqa: BLE001 — mirrors is_visible()'s never-throws contract
            return False
