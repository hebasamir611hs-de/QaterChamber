"""
web/tests/components/test_newsletter_subscription_web.py

Web-platform cases for ADO parent PBI 129566 (QC-GBL-005 — Newsletter
Subscription Management), FLD-1 (public footer Email field) — 4 cases from
suite 134470 / plan 133534, all tagged Automation, Functional-Low. Source:
the approved, injected batch handed down for this PBI (task description);
full field behavior was independently investigated live against qcdev
rather than assumed from the case titles alone — see
web/pages/components/newsletter_subscription_component.py's module
docstring for the complete evidence trail this module's assertions rely on.

TEST-DATA POLICY: every subscribe attempt uses a fresh, disposable
`qctest-<uuid>@example.com` address (RFC 2606 reserved domain — not a real
mailbox). No teardown is performed — see the Page Object's own module
docstring for why no safe programmatic teardown path exists on this
environment (the backing "Newsletter Subscriber" object is `(view only)` in
Object Authoring, and the site's own unsubscribe flow requires a
real-email-delivered token this suite cannot read) and why this is accepted
as a disclosed, standing limitation rather than blocking this batch.

Validation on this widget is 100% native HTML5 constraint validation (no
custom JS layer) — confirmed live, see the Page Object's docstring. Assertions
below check `checkValidity()` / `validationMessage` on the real `<input
type="email">` element rather than a hardcoded browser-engine message
string, since the exact wording is Chromium's own built-in text, not this
project's copy.
"""

import uuid

import allure
import pytest

from web.pages.components.newsletter_subscription_component import NewsletterSubscriptionComponent


def _widget(page) -> NewsletterSubscriptionComponent:
    return NewsletterSubscriptionComponent(page)


def _disposable_email() -> str:
    return f"qctest-{uuid.uuid4().hex[:10]}@example.com"


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134546")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Footer Email field accepts a valid subscription email (ADO-134546)")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134546
def test_valid_email_subscribes_successfully(page):
    """ADO 134546. Steps: enter a valid subscriber email in the footer
    Email field -> value entered; click Subscribe -> value accepted, format
    validated as valid, subscription proceeds and a success message
    displays. CONFIRMED LIVE: fires a real
    GET /o/qc-newsletter/subscribe?email=...&languageId=en_US&... request
    and the footer form is replaced with "You have successfully subscribed
    to our newsletter." — see module docstring for the live evidence."""
    widget = _widget(page)
    email = _disposable_email()

    with allure.step(f"Enter a valid, disposable subscription email ({email})"):
        widget.open_home()
        widget.enter_email(email)
        assert widget.email_value() == email
        assert widget.is_email_field_valid(), (
            f"valid email {email!r} unexpectedly failed native constraint validation: "
            f"{widget.email_validation_message()!r}"
        )

    with allure.step("Click Subscribe — success message displays"):
        widget.click_subscribe()
        assert widget.success_message_visible(), (
            "expected the confirmation text "
            "'You have successfully subscribed to our newsletter.' after a valid "
            "Subscribe submission, but it was not visible"
        )


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134547")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Submitting an empty Email field is rejected (ADO-134547)")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134547
def test_empty_email_is_rejected(page):
    """ADO 134547 (mandatory-field check). CONFIRMED LIVE: the field is a
    native `<input type="email" required>` — an empty submit is blocked by
    the browser's own constraint validation
    (validationMessage = "Please fill out this field.") before any request
    fires; no success message ever appears."""
    widget = _widget(page)

    with allure.step("Leave the Email field empty and click Subscribe"):
        widget.open_home()
        widget.enter_email("")
        widget.click_subscribe()

    with allure.step("Submission is rejected client-side — no success message"):
        assert not widget.is_email_field_valid(), (
            "expected the empty, required email field to fail native constraint "
            "validation, but checkValidity() reported true"
        )
        assert widget.email_validation_message() != "", (
            "expected a real browser validation message on the empty required field"
        )
        assert not widget.success_message_visible(), (
            "an empty Email submission unexpectedly showed the subscribe success message"
        )


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134548")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Submitting a whitespace-only Email field is rejected (ADO-134548)")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134548
def test_whitespace_only_email_is_rejected(page):
    """ADO 134548. CONFIRMED LIVE: a `type="email"` input strips leading/
    trailing whitespace as part of the browser's OWN value-sanitization
    step BEFORE constraint validation runs — `fill("   ")` leaves
    `element.value === ""` — so this produces the IDENTICAL blocked-submit
    behavior as test_empty_email_is_rejected above, not a distinct code
    path; asserted the same way, disclosed as a real, confirmed mechanism
    (not assumed)."""
    widget = _widget(page)

    with allure.step("Enter a whitespace-only value and click Subscribe"):
        widget.open_home()
        widget.enter_email("   ")
        assert widget.email_value() == "", (
            "expected the browser's own type=email value-sanitization to strip "
            "whitespace-only input to an empty value before this assertion"
        )
        widget.click_subscribe()

    with allure.step("Submission is rejected client-side — no success message"):
        assert not widget.is_email_field_valid(), (
            "expected the whitespace-trimmed-to-empty required email field to fail "
            "native constraint validation"
        )
        assert not widget.success_message_visible(), (
            "a whitespace-only Email submission unexpectedly showed the subscribe "
            "success message"
        )


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134549")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An invalid-format Email is rejected with a real validation message (ADO-134549)")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134549
def test_invalid_format_email_is_rejected(page):
    """ADO 134549. CONFIRMED LIVE: an "@"-less value (e.g. "not-an-email")
    fails native constraint validation with a real, browser-engine-specific
    message (Chromium: "Please include an '@' in the email address.
    '<value>' is missing an '@'."). This suite asserts the message is
    non-empty and real (checkValidity() false), not the literal Chromium
    wording, since that wording is browser copy, not this project's own —
    see module docstring."""
    widget = _widget(page)
    invalid_value = "not-an-email"

    with allure.step(f"Enter an invalid-format email ({invalid_value!r}) and click Subscribe"):
        widget.open_home()
        widget.enter_email(invalid_value)
        widget.click_subscribe()

    with allure.step("Submission is rejected client-side with a real validation message"):
        assert not widget.is_email_field_valid(), (
            f"expected {invalid_value!r} to fail native email-format constraint "
            "validation, but checkValidity() reported true"
        )
        message = widget.email_validation_message()
        assert message != "", "expected a real browser validation message for the invalid-format email"
        assert not widget.success_message_visible(), (
            "an invalid-format Email submission unexpectedly showed the subscribe "
            "success message"
        )
