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
SUBSCRIBE_BUTTON_TEXT = "Subscribe"
SUCCESS_MESSAGE_TEXT = "You have successfully subscribed to our newsletter."


class NewsletterSubscriptionComponent(BasePage):
    def open_home(self) -> "NewsletterSubscriptionComponent":
        self.open(web_url("/home"))
        return self

    # ---- Locators (as Locator objects — this field has no stable id/name,
    # see module docstring) -------------------------------------------------
    def _email_input(self):
        return self.page.get_by_placeholder(EMAIL_INPUT_PLACEHOLDER)

    def _subscribe_button(self):
        return self.page.get_by_role("button", name=SUBSCRIBE_BUTTON_TEXT, exact=True)

    # ---- Actions ------------------------------------------------------
    def enter_email(self, value: str) -> "NewsletterSubscriptionComponent":
        field = self._email_input()
        field.scroll_into_view_if_needed()
        field.fill(value)
        return self

    def click_subscribe(self) -> "NewsletterSubscriptionComponent":
        self._subscribe_button().click()
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
