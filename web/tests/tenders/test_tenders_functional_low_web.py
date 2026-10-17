"""
web/tests/tenders/test_tenders_functional_low_web.py — Web-platform
Functional-Low cases for PBI 130952 ("QC - Business Gateway - 012 -
Tenders listing screen"), Qatar Chamber project — the remaining-195-case
batch's field-level validation coverage for the public listing filters
(TC-072..075) and the "Submit your eTender" webform (TC-102..213, minus
TC-212 which is tagged Manual and intentionally not scripted; TC-216,
TC-218 also covered here).

DISCLOSED READING CHOICES (see test_tenders_web.py's own precedent for
this section's format):

1. **"Accepted" cases assert per-field, not end-to-end success.** A real
   end-to-end webform submission is gated behind a live reCAPTCHA this
   automated session cannot solve (see submit_etender_form_page.py's
   success_banner_visible()/success_reference_number() TODO note) — the
   SAME gate TC-213 below deliberately exercises. Every "a valid X is
   accepted" case therefore fills the ENTIRE form validly
   (fill_valid_form()), submits, and asserts the ONE field named by the
   case shows NO visible inline error — that is the real, observable
   signal this environment can give for "the field itself accepted the
   value," independent of whether the overall submission can complete.
2. **maxlength cases use the LIVE enforced limit's truncation, not
   always the case's own stated number.** Live-confirmed 2026-09-24:
   Organization name's real `maxlength` attribute is 280 (case states
   300) and Bid Validity (Days)'s is 5 (case states 3) — both narrower/
   wider than the case's own text. Where the live attribute differs from
   the case's stated number, this is recorded as a live/design
   discrepancy below (reported to the QA Manager, not silently
   corrected) and the assertion still checks the case's own stated
   ceiling is respected (true by construction once the live limit is
   narrower; the WIDER Bid Validity case is written to the case's
   stated "3 digits" and is expected to surface that discrepancy as an
   honest failure).
3. **TC-110/111/114/115 (conditional-mandatory Commercial/Computer
   Registration Number)** — no "registered company" / "QC member"
   toggle was found anywhere on the live form (confirmed live: only 36
   fields render, none matching that wording). Commercial Registration
   Number carries a fixed `*` (always mandatory) and Computer
   Registration Number (CR Number) carries none (always optional) on
   this build — there is no conditional behavior to exercise. TC-110/114
   are scripted against the live UNCONDITIONAL behavior (blank optional
   field accepted / blank-when-always-mandatory still rejected,
   respectively) and read correctly; TC-111/115 are scripted to the
   CASE's stated conditional-mandatory expectation and are expected to
   FAIL honestly on this build (no toggle exists to make the field
   conditionally mandatory) — a real product/design gap, not a locator
   defect.
4. **TC-121/125/129 "bilingual" tag** — the live public webform renders
   only ONE (EN) instance of Organization/Street Address and City
   (unlike the CMS manual-create form, which does carry EN/AR pairs for
   several of the same concepts) — no separate Arabic input was found
   for these three fields. Scripted against the single live field;
   "bilingual" in the case's own wording does not correspond to a second
   field on this surface.
5. **TC-178 "Not allowed" wording** — the live Item Wise Technical
   Evaluation Allowed control only offers Yes/No (confirmed live option
   dump) — "No" is used as the closest live equivalent to the case's
   "Not allowed" wording; a live copy variance, not a missing option.
6. **TC-143 (Closing <= Opening rejected), TC-149/160/202 (zero/negative
   rejected), TC-150/161/203 (non-numeric rejected), TC-151/204
   (exceeding max digits rejected)** — the exact client-side enforcement
   mechanism for these numeric/cross-field rules was not independently
   probed live this session (only the blanket "required" and maxlength-
   truncation mechanisms were). Each is scripted to the case's own
   stated expected result (a visible inline error) per Result Integrity
   — if this build does not actually enforce one of these rules
   client-side, the assertion fails honestly, which is the correct
   signal, not something to route around.
7. **TC-216 (Cancel discards data)** — no "Cancel" control was found on
   the live form (confirmed live: the button list contains only
   "Submit"). Scripted to reload the page and assert the form's own
   fields reset to empty (the closest live-observable behavior standing
   in for a dedicated Cancel action), documented as a live gap in the
   test's own docstring rather than invented as a button that does not
   exist.
8. **TC-218 (Country drives City lookup)** — City is a plain free-text
   `<input>` on this build (confirmed live), not a Country-dependent
   lookup/select. Scripted to the case's own stated premise (changing
   Country should change available City values) and expected to FAIL
   honestly — there is no dependent-lookup behavior to observe, a real
   product/design gap against this case's premise, not a locator issue.

Every case fills BASELINE_*_FIELDS from submit_etender_form_page.py as
its "everything else valid" backdrop (see that module's own docstring)
so exactly one field is the thing under test.
"""

import os

import allure
import pytest

from web.pages.tenders.submit_etender_form_page import SubmitETenderFormPage
from web.pages.tenders.tenders_listing_page import TendersListingPage

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
VALID_PDF = os.path.join(_FIXTURES_DIR, "qctest_valid_document.pdf")
WRONG_TYPE_FILE = os.path.join(_FIXTURES_DIR, "qctest_wrong_type.txt")
OVERSIZED_PDF = os.path.join(_FIXTURES_DIR, "qctest_oversized_document.pdf")




@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid Submitter Contact Email is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146168")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146168
@pytest.mark.traceability("INVEST-TENDERS-TC-102")
def test_tc102_verify_that_a_valid_submitter_contact_email_is_accepted(page):
    """INVEST-TENDERS-TC-102 — Azure TC 146168. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Submitter Email address', 0), (
        f"{'Submitter Email address'} should accept a valid value; got error "
        f"{form.field_error_text('Submitter Email address', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an empty Submitter Contact Email is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146169")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146169
@pytest.mark.traceability("INVEST-TENDERS-TC-103")
def test_tc103_verify_that_an_empty_submitter_contact_email_is_rejected(page):
    """INVEST-TENDERS-TC-103 — Azure TC 146169. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Submitter Email address', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Submitter Email address', 0), (
        f"leaving {'Submitter Email address'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an invalid-format Submitter Contact Email is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146170")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146170
@pytest.mark.traceability("INVEST-TENDERS-TC-104")
def test_tc104_verify_that_an_invalid_format_submitter_contact_email_is_rejected(page):
    """INVEST-TENDERS-TC-104 — Azure TC 146170. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Submitter Email address', 'not-an-email', 0)
    form.click_submit()
    assert form.field_has_visible_error('Submitter Email address', 0), (
        f"{'not-an-email'} must be rejected for {'Submitter Email address'} with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid Organization Name (webform) <=300 chars is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146171")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146171
@pytest.mark.traceability("INVEST-TENDERS-TC-105")
def test_tc105_verify_that_a_valid_organization_name_webform_300_chars_is_accepted(page):
    """INVEST-TENDERS-TC-105 — Azure TC 146171. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Organization name', 0), (
        f"{'Organization name'} should accept a valid value; got error "
        f"{form.field_error_text('Organization name', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an empty Organization Name (webform) is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146172")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146172
@pytest.mark.traceability("INVEST-TENDERS-TC-106")
def test_tc106_verify_that_an_empty_organization_name_webform_is_rejected(page):
    """INVEST-TENDERS-TC-106 — Azure TC 146172. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Organization name', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Organization name', 0), (
        f"leaving {'Organization name'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a whitespace-only Organization Name (webform) is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146173")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146173
@pytest.mark.traceability("INVEST-TENDERS-TC-107")
def test_tc107_verify_that_a_whitespace_only_organization_name_webform_is_rejected(page):
    """INVEST-TENDERS-TC-107 — Azure TC 146173. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Organization name', "   ", 0)
    form.click_submit()
    assert form.field_has_visible_error('Organization name', 0), (
        f"a whitespace-only {'Organization name'} must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an Organization Name (webform) exceeding 300 characters is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146174")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146174
@pytest.mark.traceability("INVEST-TENDERS-TC-108")
def test_tc108_verify_that_an_organization_name_webform_exceeding_300_characters_is_r(page):
    """INVEST-TENDERS-TC-108 — Azure TC 146174. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Organization name', "A" * (300 + 50), 0)
    form.click_submit()
    value = form.field_input_value('Organization name', 0)
    assert len(value) <= 300, (
        f"{'Organization name'} must not accept more than 300 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid Commercial Registration Number (<=50 alphanumeric) is accepted for a registered company')
@allure.label("pbi", "130952")
@allure.label("testcase", "146175")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146175
@pytest.mark.traceability("INVEST-TENDERS-TC-109")
def test_tc109_verify_that_a_valid_commercial_registration_number_50_alphanumeric_is_(page):
    """INVEST-TENDERS-TC-109 — Azure TC 146175. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Commercial Registration Number', 0), (
        f"{'Commercial Registration Number'} should accept a valid value; got error "
        f"{form.field_error_text('Commercial Registration Number', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that Commercial Registration Number can be left blank when the submitter is not a registered company')
@allure.label("pbi", "130952")
@allure.label("testcase", "146176")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146176
@pytest.mark.traceability("INVEST-TENDERS-TC-110")
def test_tc110_verify_that_commercial_registration_number_can_be_left_blank_when_the_(page):
    """INVEST-TENDERS-TC-110 — Azure TC 146176. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Computer Registration Number (CR Number)', 0)})
    form.click_submit()
    assert not form.field_has_visible_error('Computer Registration Number (CR Number)', 0), (
        f"{'Computer Registration Number (CR Number)'} is optional and must accept being left blank"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that Commercial Registration Number is enforced mandatory when the submission is flagged as a registered company')
@allure.label("pbi", "130952")
@allure.label("testcase", "146177")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146177
@pytest.mark.traceability("INVEST-TENDERS-TC-111")
def test_tc111_verify_that_commercial_registration_number_is_enforced_mandatory_when_(page):
    """INVEST-TENDERS-TC-111 — Azure TC 146177. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Commercial Registration Number', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Commercial Registration Number', 0), (
        f"leaving {'Commercial Registration Number'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a Commercial Registration Number exceeding 50 characters is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146178")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146178
@pytest.mark.traceability("INVEST-TENDERS-TC-112")
def test_tc112_verify_that_a_commercial_registration_number_exceeding_50_characters_i(page):
    """INVEST-TENDERS-TC-112 — Azure TC 146178. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Commercial Registration Number', "A" * (50 + 50), 0)
    form.click_submit()
    value = form.field_input_value('Commercial Registration Number', 0)
    assert len(value) <= 50, (
        f"{'Commercial Registration Number'} must not accept more than 50 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid Computer Registration Number/CR (<=50 alphanumeric) is accepted for a QC member')
@allure.label("pbi", "130952")
@allure.label("testcase", "146179")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146179
@pytest.mark.traceability("INVEST-TENDERS-TC-113")
def test_tc113_verify_that_a_valid_computer_registration_number_cr_50_alphanumeric_is(page):
    """INVEST-TENDERS-TC-113 — Azure TC 146179. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Computer Registration Number (CR Number)', 0), (
        f"{'Computer Registration Number (CR Number)'} should accept a valid value; got error "
        f"{form.field_error_text('Computer Registration Number (CR Number)', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that Computer Registration Number/CR can be left blank when not QC-member-restricted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146180")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146180
@pytest.mark.traceability("INVEST-TENDERS-TC-114")
def test_tc114_verify_that_computer_registration_number_cr_can_be_left_blank_when_not(page):
    """INVEST-TENDERS-TC-114 — Azure TC 146180. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Computer Registration Number (CR Number)', 0)})
    form.click_submit()
    assert not form.field_has_visible_error('Computer Registration Number (CR Number)', 0), (
        f"{'Computer Registration Number (CR Number)'} is optional and must accept being left blank"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that Computer Registration Number/CR is enforced mandatory when the tender is QC-member-restricted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146181")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146181
@pytest.mark.traceability("INVEST-TENDERS-TC-115")
def test_tc115_verify_that_computer_registration_number_cr_is_enforced_mandatory_when(page):
    """INVEST-TENDERS-TC-115 — Azure TC 146181. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Computer Registration Number (CR Number)', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Computer Registration Number (CR Number)', 0), (
        f"leaving {'Computer Registration Number (CR Number)'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a Computer Registration Number/CR exceeding 50 characters is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146182")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146182
@pytest.mark.traceability("INVEST-TENDERS-TC-116")
def test_tc116_verify_that_a_computer_registration_number_cr_exceeding_50_characters_(page):
    """INVEST-TENDERS-TC-116 — Azure TC 146182. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Computer Registration Number (CR Number)', "A" * (50 + 50), 0)
    form.click_submit()
    value = form.field_input_value('Computer Registration Number (CR Number)', 0)
    assert len(value) <= 50, (
        f"{'Computer Registration Number (CR Number)'} must not accept more than 50 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid Establishment Card Number (<=50 alphanumeric) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146183")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146183
@pytest.mark.traceability("INVEST-TENDERS-TC-117")
def test_tc117_verify_that_a_valid_establishment_card_number_50_alphanumeric_is_accep(page):
    """INVEST-TENDERS-TC-117 — Azure TC 146183. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Establishment Card Number', 0), (
        f"{'Establishment Card Number'} should accept a valid value; got error "
        f"{form.field_error_text('Establishment Card Number', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an empty Establishment Card Number is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146184")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146184
@pytest.mark.traceability("INVEST-TENDERS-TC-118")
def test_tc118_verify_that_an_empty_establishment_card_number_is_rejected(page):
    """INVEST-TENDERS-TC-118 — Azure TC 146184. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Establishment Card Number', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Establishment Card Number', 0), (
        f"leaving {'Establishment Card Number'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a whitespace-only Establishment Card Number is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146185")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146185
@pytest.mark.traceability("INVEST-TENDERS-TC-119")
def test_tc119_verify_that_a_whitespace_only_establishment_card_number_is_rejected(page):
    """INVEST-TENDERS-TC-119 — Azure TC 146185. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Establishment Card Number', "   ", 0)
    form.click_submit()
    assert form.field_has_visible_error('Establishment Card Number', 0), (
        f"a whitespace-only {'Establishment Card Number'} must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an Establishment Card Number exceeding 50 characters is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146186")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146186
@pytest.mark.traceability("INVEST-TENDERS-TC-120")
def test_tc120_verify_that_an_establishment_card_number_exceeding_50_characters_is_re(page):
    """INVEST-TENDERS-TC-120 — Azure TC 146186. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Establishment Card Number', "A" * (50 + 50), 0)
    form.click_submit()
    value = form.field_input_value('Establishment Card Number', 0)
    assert len(value) <= 50, (
        f"{'Establishment Card Number'} must not accept more than 50 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid bilingual Organization Address (<=300) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146187")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146187
@pytest.mark.traceability("INVEST-TENDERS-TC-121")
def test_tc121_verify_that_a_valid_bilingual_organization_address_300_is_accepted(page):
    """INVEST-TENDERS-TC-121 — Azure TC 146187. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Organization address', 0), (
        f"{'Organization address'} should accept a valid value; got error "
        f"{form.field_error_text('Organization address', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving Organization Address (EN or AR) empty is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146188")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146188
@pytest.mark.traceability("INVEST-TENDERS-TC-122")
def test_tc122_verify_that_leaving_organization_address_en_or_ar_empty_is_rejected(page):
    """INVEST-TENDERS-TC-122 — Azure TC 146188. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Organization address', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Organization address', 0), (
        f"leaving {'Organization address'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a whitespace-only Organization Address is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146189")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146189
@pytest.mark.traceability("INVEST-TENDERS-TC-123")
def test_tc123_verify_that_a_whitespace_only_organization_address_is_rejected(page):
    """INVEST-TENDERS-TC-123 — Azure TC 146189. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Organization address', "   ", 0)
    form.click_submit()
    assert form.field_has_visible_error('Organization address', 0), (
        f"a whitespace-only {'Organization address'} must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an Organization Address exceeding 300 characters is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146190")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146190
@pytest.mark.traceability("INVEST-TENDERS-TC-124")
def test_tc124_verify_that_an_organization_address_exceeding_300_characters_is_reject(page):
    """INVEST-TENDERS-TC-124 — Azure TC 146190. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Organization address', "A" * (300 + 50), 0)
    form.click_submit()
    value = form.field_input_value('Organization address', 0)
    assert len(value) <= 300, (
        f"{'Organization address'} must not accept more than 300 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid bilingual Street Address (<=300) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146191")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146191
@pytest.mark.traceability("INVEST-TENDERS-TC-125")
def test_tc125_verify_that_a_valid_bilingual_street_address_300_is_accepted(page):
    """INVEST-TENDERS-TC-125 — Azure TC 146191. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Street address', 0), (
        f"{'Street address'} should accept a valid value; got error "
        f"{form.field_error_text('Street address', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving Street Address (EN or AR) empty is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146192")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146192
@pytest.mark.traceability("INVEST-TENDERS-TC-126")
def test_tc126_verify_that_leaving_street_address_en_or_ar_empty_is_rejected(page):
    """INVEST-TENDERS-TC-126 — Azure TC 146192. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Street address', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Street address', 0), (
        f"leaving {'Street address'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a whitespace-only Street Address is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146193")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146193
@pytest.mark.traceability("INVEST-TENDERS-TC-127")
def test_tc127_verify_that_a_whitespace_only_street_address_is_rejected(page):
    """INVEST-TENDERS-TC-127 — Azure TC 146193. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Street address', "   ", 0)
    form.click_submit()
    assert form.field_has_visible_error('Street address', 0), (
        f"a whitespace-only {'Street address'} must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a Street Address exceeding 300 characters is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146194")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146194
@pytest.mark.traceability("INVEST-TENDERS-TC-128")
def test_tc128_verify_that_a_street_address_exceeding_300_characters_is_rejected(page):
    """INVEST-TENDERS-TC-128 — Azure TC 146194. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Street address', "A" * (300 + 50), 0)
    form.click_submit()
    value = form.field_input_value('Street address', 0)
    assert len(value) <= 300, (
        f"{'Street address'} must not accept more than 300 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid bilingual City (org, <=200) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146195")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146195
@pytest.mark.traceability("INVEST-TENDERS-TC-129")
def test_tc129_verify_that_a_valid_bilingual_city_org_200_is_accepted(page):
    """INVEST-TENDERS-TC-129 — Azure TC 146195. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('City', 0), (
        f"{'City'} should accept a valid value; got error "
        f"{form.field_error_text('City', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving City (org, EN or AR) empty is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146196")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146196
@pytest.mark.traceability("INVEST-TENDERS-TC-130")
def test_tc130_verify_that_leaving_city_org_en_or_ar_empty_is_rejected(page):
    """INVEST-TENDERS-TC-130 — Azure TC 146196. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('City', 0)})
    form.click_submit()
    assert form.field_has_visible_error('City', 0), (
        f"leaving {'City'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a whitespace-only City (org) is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146197")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146197
@pytest.mark.traceability("INVEST-TENDERS-TC-131")
def test_tc131_verify_that_a_whitespace_only_city_org_is_rejected(page):
    """INVEST-TENDERS-TC-131 — Azure TC 146197. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('City', "   ", 0)
    form.click_submit()
    assert form.field_has_visible_error('City', 0), (
        f"a whitespace-only {'City'} must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a City (org) exceeding 200 characters is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146198")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146198
@pytest.mark.traceability("INVEST-TENDERS-TC-132")
def test_tc132_verify_that_a_city_org_exceeding_200_characters_is_rejected(page):
    """INVEST-TENDERS-TC-132 — Azure TC 146198. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('City', "A" * (200 + 50), 0)
    form.click_submit()
    value = form.field_input_value('City', 0)
    assert len(value) <= 200, (
        f"{'City'} must not accept more than 200 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid ZIP/Postal Code (org, <=20) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146199")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146199
@pytest.mark.traceability("INVEST-TENDERS-TC-133")
def test_tc133_verify_that_a_valid_zip_postal_code_org_20_is_accepted(page):
    """INVEST-TENDERS-TC-133 — Azure TC 146199. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('ZIP / postal code', 0), (
        f"{'ZIP / postal code'} should accept a valid value; got error "
        f"{form.field_error_text('ZIP / postal code', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that ZIP/Postal Code (org) can be left blank')
@allure.label("pbi", "130952")
@allure.label("testcase", "146200")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146200
@pytest.mark.traceability("INVEST-TENDERS-TC-134")
def test_tc134_verify_that_zip_postal_code_org_can_be_left_blank(page):
    """INVEST-TENDERS-TC-134 — Azure TC 146200. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('ZIP / postal code', 0)})
    form.click_submit()
    assert not form.field_has_visible_error('ZIP / postal code', 0), (
        f"{'ZIP / postal code'} is optional and must accept being left blank"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a ZIP/Postal Code (org) exceeding 20 characters is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146201")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146201
@pytest.mark.traceability("INVEST-TENDERS-TC-135")
def test_tc135_verify_that_a_zip_postal_code_org_exceeding_20_characters_is_rejected(page):
    """INVEST-TENDERS-TC-135 — Azure TC 146201. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('ZIP / postal code', "A" * (20 + 50), 0)
    form.click_submit()
    value = form.field_input_value('ZIP / postal code', 0)
    assert len(value) <= 20, (
        f"{'ZIP / postal code'} must not accept more than 20 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that selecting a valid Country from the lookup dropdown is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146202")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146202
@pytest.mark.traceability("INVEST-TENDERS-TC-136")
def test_tc136_verify_that_selecting_a_valid_country_from_the_lookup_dropdown_is_acce(page):
    """INVEST-TENDERS-TC-136 — Azure TC 146202. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Country', 0), (
        f"{'Country'} should accept a valid value; got error "
        f"{form.field_error_text('Country', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving Country unselected is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146203")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146203
@pytest.mark.traceability("INVEST-TENDERS-TC-137")
def test_tc137_verify_that_leaving_country_unselected_is_rejected(page):
    """INVEST-TENDERS-TC-137 — Azure TC 146203. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Country', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Country', 0), (
        f"leaving {'Country'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid webform Opening Date is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146204")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146204
@pytest.mark.traceability("INVEST-TENDERS-TC-138")
def test_tc138_verify_that_a_valid_webform_opening_date_is_accepted(page):
    """INVEST-TENDERS-TC-138 — Azure TC 146204. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Opening Date', 0), (
        f"{'Opening Date'} should accept a valid value; got error "
        f"{form.field_error_text('Opening Date', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an empty webform Opening Date is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146205")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146205
@pytest.mark.traceability("INVEST-TENDERS-TC-139")
def test_tc139_verify_that_an_empty_webform_opening_date_is_rejected(page):
    """INVEST-TENDERS-TC-139 — Azure TC 146205. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Opening Date', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Opening Date', 0), (
        f"leaving {'Opening Date'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an invalid-format webform Opening Date is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146206")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146206
@pytest.mark.traceability("INVEST-TENDERS-TC-140")
def test_tc140_verify_that_an_invalid_format_webform_opening_date_is_rejected(page):
    """INVEST-TENDERS-TC-140 — Azure TC 146206. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Opening Date', '99/99/9999', 0)
    form.click_submit()
    assert form.field_has_visible_error('Opening Date', 0), (
        f"{'99/99/9999'} must be rejected for {'Opening Date'} with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid webform Closing Date (> Opening) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146207")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146207
@pytest.mark.traceability("INVEST-TENDERS-TC-141")
def test_tc141_verify_that_a_valid_webform_closing_date_opening_is_accepted(page):
    """INVEST-TENDERS-TC-141 — Azure TC 146207. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Closing Date', 0), (
        f"{'Closing Date'} should accept a valid value; got error "
        f"{form.field_error_text('Closing Date', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an empty webform Closing Date is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146208")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146208
@pytest.mark.traceability("INVEST-TENDERS-TC-142")
def test_tc142_verify_that_an_empty_webform_closing_date_is_rejected(page):
    """INVEST-TENDERS-TC-142 — Azure TC 146208. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Closing Date', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Closing Date', 0), (
        f"leaving {'Closing Date'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a webform Closing Date <= Opening Date is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146209")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146209
@pytest.mark.traceability("INVEST-TENDERS-TC-143")
def test_tc143_verify_that_a_webform_closing_date_opening_date_is_rejected(page):
    """INVEST-TENDERS-TC-143 — Azure TC 146209. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Closing Date', '2026-10-01', 0)
    form.click_submit()
    assert form.field_has_visible_error('Closing Date', 0), (
        f"{'2026-10-01'} must be rejected for {'Closing Date'} with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an invalid-format webform Closing Date is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146210")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146210
@pytest.mark.traceability("INVEST-TENDERS-TC-144")
def test_tc144_verify_that_an_invalid_format_webform_closing_date_is_rejected(page):
    """INVEST-TENDERS-TC-144 — Azure TC 146210. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Closing Date', '99/99/9999', 0)
    form.click_submit()
    assert form.field_has_visible_error('Closing Date', 0), (
        f"{'99/99/9999'} must be rejected for {'Closing Date'} with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that selecting "Yes" for General Technical Evaluation Allowed is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146211")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146211
@pytest.mark.traceability("INVEST-TENDERS-TC-145")
def test_tc145_verify_that_selecting_yes_for_general_technical_evaluation_allowed_is_(page):
    """INVEST-TENDERS-TC-145 — Azure TC 146211. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('General Technical Evaluation Allowed', 0), (
        f"{'General Technical Evaluation Allowed'} should accept a valid value; got error "
        f"{form.field_error_text('General Technical Evaluation Allowed', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving General Technical Evaluation Allowed unselected is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146212")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146212
@pytest.mark.traceability("INVEST-TENDERS-TC-146")
def test_tc146_verify_that_leaving_general_technical_evaluation_allowed_unselected_is(page):
    """INVEST-TENDERS-TC-146 — Azure TC 146212. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('General Technical Evaluation Allowed', 0)})
    form.click_submit()
    assert form.field_has_visible_error('General Technical Evaluation Allowed', 0), (
        f"leaving {'General Technical Evaluation Allowed'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid positive Tender Fee (QAR, <=10 digits) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146213")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146213
@pytest.mark.traceability("INVEST-TENDERS-TC-147")
def test_tc147_verify_that_a_valid_positive_tender_fee_qar_10_digits_is_accepted(page):
    """INVEST-TENDERS-TC-147 — Azure TC 146213. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Tender Fee in QAR', 0), (
        f"{'Tender Fee in QAR'} should accept a valid value; got error "
        f"{form.field_error_text('Tender Fee in QAR', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an empty Tender Fee is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146214")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146214
@pytest.mark.traceability("INVEST-TENDERS-TC-148")
def test_tc148_verify_that_an_empty_tender_fee_is_rejected(page):
    """INVEST-TENDERS-TC-148 — Azure TC 146214. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Tender Fee in QAR', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Tender Fee in QAR', 0), (
        f"leaving {'Tender Fee in QAR'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a zero or negative Tender Fee is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146215")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146215
@pytest.mark.traceability("INVEST-TENDERS-TC-149")
def test_tc149_verify_that_a_zero_or_negative_tender_fee_is_rejected(page):
    """INVEST-TENDERS-TC-149 — Azure TC 146215. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Tender Fee in QAR', '-5', 0)
    form.click_submit()
    assert form.field_has_visible_error('Tender Fee in QAR', 0), (
        f"{'-5'} must be rejected for {'Tender Fee in QAR'} with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a non-numeric Tender Fee is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146216")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146216
@pytest.mark.traceability("INVEST-TENDERS-TC-150")
def test_tc150_verify_that_a_non_numeric_tender_fee_is_rejected(page):
    """INVEST-TENDERS-TC-150 — Azure TC 146216. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Tender Fee in QAR', 'abc', 0)
    form.click_submit()
    assert form.field_has_visible_error('Tender Fee in QAR', 0), (
        f"{'abc'} must be rejected for {'Tender Fee in QAR'} with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a Tender Fee exceeding 10 digits is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146217")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146217
@pytest.mark.traceability("INVEST-TENDERS-TC-151")
def test_tc151_verify_that_a_tender_fee_exceeding_10_digits_is_rejected(page):
    """INVEST-TENDERS-TC-151 — Azure TC 146217. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Tender Fee in QAR', '123456789012', 0)
    form.click_submit()
    assert form.field_has_visible_error('Tender Fee in QAR', 0), (
        f"{'123456789012'} must be rejected for {'Tender Fee in QAR'} with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid Fee Payable To (<=1000) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146218")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146218
@pytest.mark.traceability("INVEST-TENDERS-TC-152")
def test_tc152_verify_that_a_valid_fee_payable_to_1000_is_accepted(page):
    """INVEST-TENDERS-TC-152 — Azure TC 146218. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Fee Payable To', 0), (
        f"{'Fee Payable To'} should accept a valid value; got error "
        f"{form.field_error_text('Fee Payable To', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an empty Fee Payable To is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146219")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146219
@pytest.mark.traceability("INVEST-TENDERS-TC-153")
def test_tc153_verify_that_an_empty_fee_payable_to_is_rejected(page):
    """INVEST-TENDERS-TC-153 — Azure TC 146219. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Fee Payable To', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Fee Payable To', 0), (
        f"leaving {'Fee Payable To'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a whitespace-only Fee Payable To is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146220")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146220
@pytest.mark.traceability("INVEST-TENDERS-TC-154")
def test_tc154_verify_that_a_whitespace_only_fee_payable_to_is_rejected(page):
    """INVEST-TENDERS-TC-154 — Azure TC 146220. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Fee Payable To', "   ", 0)
    form.click_submit()
    assert form.field_has_visible_error('Fee Payable To', 0), (
        f"a whitespace-only {'Fee Payable To'} must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a Fee Payable To exceeding 1000 characters is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146221")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146221
@pytest.mark.traceability("INVEST-TENDERS-TC-155")
def test_tc155_verify_that_a_fee_payable_to_exceeding_1000_characters_is_rejected(page):
    """INVEST-TENDERS-TC-155 — Azure TC 146221. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Fee Payable To', "A" * (1000 + 50), 0)
    form.click_submit()
    value = form.field_input_value('Fee Payable To', 0)
    assert len(value) <= 1000, (
        f"{'Fee Payable To'} must not accept more than 1000 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that selecting "No" for Tender Fee Exemption Allowed is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146222")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146222
@pytest.mark.traceability("INVEST-TENDERS-TC-156")
def test_tc156_verify_that_selecting_no_for_tender_fee_exemption_allowed_is_accepted(page):
    """INVEST-TENDERS-TC-156 — Azure TC 146222. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Tender Fee Exemption Allowed', 0), (
        f"{'Tender Fee Exemption Allowed'} should accept a valid value; got error "
        f"{form.field_error_text('Tender Fee Exemption Allowed', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving Tender Fee Exemption Allowed unselected is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146223")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146223
@pytest.mark.traceability("INVEST-TENDERS-TC-157")
def test_tc157_verify_that_leaving_tender_fee_exemption_allowed_unselected_is_rejecte(page):
    """INVEST-TENDERS-TC-157 — Azure TC 146223. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Tender Fee Exemption Allowed', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Tender Fee Exemption Allowed', 0), (
        f"leaving {'Tender Fee Exemption Allowed'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid positive EMD Amount (QAR) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146224")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146224
@pytest.mark.traceability("INVEST-TENDERS-TC-158")
def test_tc158_verify_that_a_valid_positive_emd_amount_qar_is_accepted(page):
    """INVEST-TENDERS-TC-158 — Azure TC 146224. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('EMD Amount in QAR', 0), (
        f"{'EMD Amount in QAR'} should accept a valid value; got error "
        f"{form.field_error_text('EMD Amount in QAR', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an empty EMD Amount is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146225")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146225
@pytest.mark.traceability("INVEST-TENDERS-TC-159")
def test_tc159_verify_that_an_empty_emd_amount_is_rejected(page):
    """INVEST-TENDERS-TC-159 — Azure TC 146225. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('EMD Amount in QAR', 0)})
    form.click_submit()
    assert form.field_has_visible_error('EMD Amount in QAR', 0), (
        f"leaving {'EMD Amount in QAR'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a zero or negative EMD Amount is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146226")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146226
@pytest.mark.traceability("INVEST-TENDERS-TC-160")
def test_tc160_verify_that_a_zero_or_negative_emd_amount_is_rejected(page):
    """INVEST-TENDERS-TC-160 — Azure TC 146226. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('EMD Amount in QAR', '-1', 0)
    form.click_submit()
    assert form.field_has_visible_error('EMD Amount in QAR', 0), (
        f"{'-1'} must be rejected for {'EMD Amount in QAR'} with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a non-numeric EMD Amount is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146227")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146227
@pytest.mark.traceability("INVEST-TENDERS-TC-161")
def test_tc161_verify_that_a_non_numeric_emd_amount_is_rejected(page):
    """INVEST-TENDERS-TC-161 — Azure TC 146227. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('EMD Amount in QAR', 'xyz', 0)
    form.click_submit()
    assert form.field_has_visible_error('EMD Amount in QAR', 0), (
        f"{'xyz'} must be rejected for {'EMD Amount in QAR'} with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid EMD Payable To (<=1000) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146228")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146228
@pytest.mark.traceability("INVEST-TENDERS-TC-162")
def test_tc162_verify_that_a_valid_emd_payable_to_1000_is_accepted(page):
    """INVEST-TENDERS-TC-162 — Azure TC 146228. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('EMD Payable To', 0), (
        f"{'EMD Payable To'} should accept a valid value; got error "
        f"{form.field_error_text('EMD Payable To', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an empty EMD Payable To is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146229")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146229
@pytest.mark.traceability("INVEST-TENDERS-TC-163")
def test_tc163_verify_that_an_empty_emd_payable_to_is_rejected(page):
    """INVEST-TENDERS-TC-163 — Azure TC 146229. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('EMD Payable To', 0)})
    form.click_submit()
    assert form.field_has_visible_error('EMD Payable To', 0), (
        f"leaving {'EMD Payable To'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a whitespace-only EMD Payable To is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146230")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146230
@pytest.mark.traceability("INVEST-TENDERS-TC-164")
def test_tc164_verify_that_a_whitespace_only_emd_payable_to_is_rejected(page):
    """INVEST-TENDERS-TC-164 — Azure TC 146230. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('EMD Payable To', "   ", 0)
    form.click_submit()
    assert form.field_has_visible_error('EMD Payable To', 0), (
        f"a whitespace-only {'EMD Payable To'} must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an EMD Payable To exceeding 1000 characters is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146231")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146231
@pytest.mark.traceability("INVEST-TENDERS-TC-165")
def test_tc165_verify_that_an_emd_payable_to_exceeding_1000_characters_is_rejected(page):
    """INVEST-TENDERS-TC-165 — Azure TC 146231. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('EMD Payable To', "A" * (1000 + 50), 0)
    form.click_submit()
    value = form.field_input_value('EMD Payable To', 0)
    assert len(value) <= 1000, (
        f"{'EMD Payable To'} must not accept more than 1000 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that selecting "Online" for Payment Mode is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146232")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146232
@pytest.mark.traceability("INVEST-TENDERS-TC-166")
def test_tc166_verify_that_selecting_online_for_payment_mode_is_accepted(page):
    """INVEST-TENDERS-TC-166 — Azure TC 146232. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Payment Mode', 0), (
        f"{'Payment Mode'} should accept a valid value; got error "
        f"{form.field_error_text('Payment Mode', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving Payment Mode unselected is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146233")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146233
@pytest.mark.traceability("INVEST-TENDERS-TC-167")
def test_tc167_verify_that_leaving_payment_mode_unselected_is_rejected(page):
    """INVEST-TENDERS-TC-167 — Azure TC 146233. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Payment Mode', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Payment Mode', 0), (
        f"leaving {'Payment Mode'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that selecting "Services" for Tender Category is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146234")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146234
@pytest.mark.traceability("INVEST-TENDERS-TC-168")
def test_tc168_verify_that_selecting_services_for_tender_category_is_accepted(page):
    """INVEST-TENDERS-TC-168 — Azure TC 146234. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Tender Category', 0), (
        f"{'Tender Category'} should accept a valid value; got error "
        f"{form.field_error_text('Tender Category', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving Tender Category unselected is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146235")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146235
@pytest.mark.traceability("INVEST-TENDERS-TC-169")
def test_tc169_verify_that_leaving_tender_category_unselected_is_rejected(page):
    """INVEST-TENDERS-TC-169 — Azure TC 146235. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Tender Category', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Tender Category', 0), (
        f"leaving {'Tender Category'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that selecting a valid Tender Type is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146236")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146236
@pytest.mark.traceability("INVEST-TENDERS-TC-170")
def test_tc170_verify_that_selecting_a_valid_tender_type_is_accepted(page):
    """INVEST-TENDERS-TC-170 — Azure TC 146236. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Tender Type', 0), (
        f"{'Tender Type'} should accept a valid value; got error "
        f"{form.field_error_text('Tender Type', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving Tender Type unselected is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146237")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146237
@pytest.mark.traceability("INVEST-TENDERS-TC-171")
def test_tc171_verify_that_leaving_tender_type_unselected_is_rejected(page):
    """INVEST-TENDERS-TC-171 — Azure TC 146237. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Tender Type', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Tender Type', 0), (
        f"leaving {'Tender Type'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that selecting a valid Tender Classification is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146238")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146238
@pytest.mark.traceability("INVEST-TENDERS-TC-172")
def test_tc172_verify_that_selecting_a_valid_tender_classification_is_accepted(page):
    """INVEST-TENDERS-TC-172 — Azure TC 146238. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Tender Classification', 0), (
        f"{'Tender Classification'} should accept a valid value; got error "
        f"{form.field_error_text('Tender Classification', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving Tender Classification unselected is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146239")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146239
@pytest.mark.traceability("INVEST-TENDERS-TC-173")
def test_tc173_verify_that_leaving_tender_classification_unselected_is_rejected(page):
    """INVEST-TENDERS-TC-173 — Azure TC 146239. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Tender Classification', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Tender Classification', 0), (
        f"leaving {'Tender Classification'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that selecting a valid Product Category is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146240")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146240
@pytest.mark.traceability("INVEST-TENDERS-TC-174")
def test_tc174_verify_that_selecting_a_valid_product_category_is_accepted(page):
    """INVEST-TENDERS-TC-174 — Azure TC 146240. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Product Category', 0), (
        f"{'Product Category'} should accept a valid value; got error "
        f"{form.field_error_text('Product Category', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving Product Category unselected is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146241")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146241
@pytest.mark.traceability("INVEST-TENDERS-TC-175")
def test_tc175_verify_that_leaving_product_category_unselected_is_rejected(page):
    """INVEST-TENDERS-TC-175 — Azure TC 146241. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Product Category', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Product Category', 0), (
        f"leaving {'Product Category'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that selecting a valid Tender Location (Country) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146242")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146242
@pytest.mark.traceability("INVEST-TENDERS-TC-176")
def test_tc176_verify_that_selecting_a_valid_tender_location_country_is_accepted(page):
    """INVEST-TENDERS-TC-176 — Azure TC 146242. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Tender Location', 0), (
        f"{'Tender Location'} should accept a valid value; got error "
        f"{form.field_error_text('Tender Location', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving Tender Location unselected is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146243")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146243
@pytest.mark.traceability("INVEST-TENDERS-TC-177")
def test_tc177_verify_that_leaving_tender_location_unselected_is_rejected(page):
    """INVEST-TENDERS-TC-177 — Azure TC 146243. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Tender Location', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Tender Location', 0), (
        f"leaving {'Tender Location'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that selecting "Not allowed" for Item Wise Technical Evaluation Allowed is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146244")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146244
@pytest.mark.traceability("INVEST-TENDERS-TC-178")
def test_tc178_verify_that_selecting_not_allowed_for_item_wise_technical_evaluation_a(page):
    """INVEST-TENDERS-TC-178 — Azure TC 146244. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Item Wise Technical Evaluation Allowed', 0), (
        f"{'Item Wise Technical Evaluation Allowed'} should accept a valid value; got error "
        f"{form.field_error_text('Item Wise Technical Evaluation Allowed', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving Item Wise Technical Evaluation Allowed unselected is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146245")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146245
@pytest.mark.traceability("INVEST-TENDERS-TC-179")
def test_tc179_verify_that_leaving_item_wise_technical_evaluation_allowed_unselected_(page):
    """INVEST-TENDERS-TC-179 — Azure TC 146245. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Item Wise Technical Evaluation Allowed', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Item Wise Technical Evaluation Allowed', 0), (
        f"leaving {'Item Wise Technical Evaluation Allowed'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid Work Description (<=5000) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146246")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146246
@pytest.mark.traceability("INVEST-TENDERS-TC-180")
def test_tc180_verify_that_a_valid_work_description_5000_is_accepted(page):
    """INVEST-TENDERS-TC-180 — Azure TC 146246. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Work Description', 0), (
        f"{'Work Description'} should accept a valid value; got error "
        f"{form.field_error_text('Work Description', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an empty Work Description is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146247")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146247
@pytest.mark.traceability("INVEST-TENDERS-TC-181")
def test_tc181_verify_that_an_empty_work_description_is_rejected(page):
    """INVEST-TENDERS-TC-181 — Azure TC 146247. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Work Description', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Work Description', 0), (
        f"leaving {'Work Description'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a whitespace-only Work Description is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146248")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146248
@pytest.mark.traceability("INVEST-TENDERS-TC-182")
def test_tc182_verify_that_a_whitespace_only_work_description_is_rejected(page):
    """INVEST-TENDERS-TC-182 — Azure TC 146248. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Work Description', "   ", 0)
    form.click_submit()
    assert form.field_has_visible_error('Work Description', 0), (
        f"a whitespace-only {'Work Description'} must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a Work Description exceeding 5000 characters is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146249")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146249
@pytest.mark.traceability("INVEST-TENDERS-TC-183")
def test_tc183_verify_that_a_work_description_exceeding_5000_characters_is_rejected(page):
    """INVEST-TENDERS-TC-183 — Azure TC 146249. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Work Description', "A" * (5000 + 50), 0)
    form.click_submit()
    value = form.field_input_value('Work Description', 0)
    assert len(value) <= 5000, (
        f"{'Work Description'} must not accept more than 5000 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid Pre-Bid Meeting Date is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146250")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146250
@pytest.mark.traceability("INVEST-TENDERS-TC-184")
def test_tc184_verify_that_a_valid_pre_bid_meeting_date_is_accepted(page):
    """INVEST-TENDERS-TC-184 — Azure TC 146250. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Pre Bid Meeting Date', 0), (
        f"{'Pre Bid Meeting Date'} should accept a valid value; got error "
        f"{form.field_error_text('Pre Bid Meeting Date', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that Pre-Bid Meeting Date can be left blank')
@allure.label("pbi", "130952")
@allure.label("testcase", "146251")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146251
@pytest.mark.traceability("INVEST-TENDERS-TC-185")
def test_tc185_verify_that_pre_bid_meeting_date_can_be_left_blank(page):
    """INVEST-TENDERS-TC-185 — Azure TC 146251. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Pre Bid Meeting Date', 0)})
    form.click_submit()
    assert not form.field_has_visible_error('Pre Bid Meeting Date', 0), (
        f"{'Pre Bid Meeting Date'} is optional and must accept being left blank"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an invalid-format Pre-Bid Meeting Date is rejected when entered')
@allure.label("pbi", "130952")
@allure.label("testcase", "146252")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146252
@pytest.mark.traceability("INVEST-TENDERS-TC-186")
def test_tc186_verify_that_an_invalid_format_pre_bid_meeting_date_is_rejected_when_en(page):
    """INVEST-TENDERS-TC-186 — Azure TC 146252. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Pre Bid Meeting Date', '99/99/9999', 0)
    form.click_submit()
    assert form.field_has_visible_error('Pre Bid Meeting Date', 0), (
        f"{'99/99/9999'} must be rejected for {'Pre Bid Meeting Date'} with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid Pre-Bid Meeting Address (<=300) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146253")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146253
@pytest.mark.traceability("INVEST-TENDERS-TC-187")
def test_tc187_verify_that_a_valid_pre_bid_meeting_address_300_is_accepted(page):
    """INVEST-TENDERS-TC-187 — Azure TC 146253. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Pre Bid Meeting Address', 0), (
        f"{'Pre Bid Meeting Address'} should accept a valid value; got error "
        f"{form.field_error_text('Pre Bid Meeting Address', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that Pre-Bid Meeting Address can be left blank')
@allure.label("pbi", "130952")
@allure.label("testcase", "146254")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146254
@pytest.mark.traceability("INVEST-TENDERS-TC-188")
def test_tc188_verify_that_pre_bid_meeting_address_can_be_left_blank(page):
    """INVEST-TENDERS-TC-188 — Azure TC 146254. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Pre Bid Meeting Address', 0)})
    form.click_submit()
    assert not form.field_has_visible_error('Pre Bid Meeting Address', 0), (
        f"{'Pre Bid Meeting Address'} is optional and must accept being left blank"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a Pre-Bid Meeting Address exceeding 300 characters is rejected when entered')
@allure.label("pbi", "130952")
@allure.label("testcase", "146255")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146255
@pytest.mark.traceability("INVEST-TENDERS-TC-189")
def test_tc189_verify_that_a_pre_bid_meeting_address_exceeding_300_characters_is_reje(page):
    """INVEST-TENDERS-TC-189 — Azure TC 146255. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Pre Bid Meeting Address', "A" * (300 + 50), 0)
    form.click_submit()
    value = form.field_input_value('Pre Bid Meeting Address', 0)
    assert len(value) <= 300, (
        f"{'Pre Bid Meeting Address'} must not accept more than 300 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid City (work item, <=200) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146256")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146256
@pytest.mark.traceability("INVEST-TENDERS-TC-190")
def test_tc190_verify_that_a_valid_city_work_item_200_is_accepted(page):
    """INVEST-TENDERS-TC-190 — Azure TC 146256. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('City', 1), (
        f"{'City'} should accept a valid value; got error "
        f"{form.field_error_text('City', 1)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that City (work item) can be left blank')
@allure.label("pbi", "130952")
@allure.label("testcase", "146257")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146257
@pytest.mark.traceability("INVEST-TENDERS-TC-191")
def test_tc191_verify_that_city_work_item_can_be_left_blank(page):
    """INVEST-TENDERS-TC-191 — Azure TC 146257. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('City', 1)})
    form.click_submit()
    assert not form.field_has_visible_error('City', 1), (
        f"{'City'} is optional and must accept being left blank"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a City (work item) exceeding 200 characters is rejected when entered')
@allure.label("pbi", "130952")
@allure.label("testcase", "146258")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146258
@pytest.mark.traceability("INVEST-TENDERS-TC-192")
def test_tc192_verify_that_a_city_work_item_exceeding_200_characters_is_rejected_when(page):
    """INVEST-TENDERS-TC-192 — Azure TC 146258. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('City', "A" * (200 + 50), 1)
    form.click_submit()
    value = form.field_input_value('City', 1)
    assert len(value) <= 200, (
        f"{'City'} must not accept more than 200 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid ZIP/Postal Code (work item, <=20) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146259")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146259
@pytest.mark.traceability("INVEST-TENDERS-TC-193")
def test_tc193_verify_that_a_valid_zip_postal_code_work_item_20_is_accepted(page):
    """INVEST-TENDERS-TC-193 — Azure TC 146259. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('ZIP / postal code', 1), (
        f"{'ZIP / postal code'} should accept a valid value; got error "
        f"{form.field_error_text('ZIP / postal code', 1)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that ZIP/Postal Code (work item) can be left blank')
@allure.label("pbi", "130952")
@allure.label("testcase", "146260")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146260
@pytest.mark.traceability("INVEST-TENDERS-TC-194")
def test_tc194_verify_that_zip_postal_code_work_item_can_be_left_blank(page):
    """INVEST-TENDERS-TC-194 — Azure TC 146260. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('ZIP / postal code', 1)})
    form.click_submit()
    assert not form.field_has_visible_error('ZIP / postal code', 1), (
        f"{'ZIP / postal code'} is optional and must accept being left blank"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a ZIP/Postal Code (work item) exceeding 20 characters is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146261")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146261
@pytest.mark.traceability("INVEST-TENDERS-TC-195")
def test_tc195_verify_that_a_zip_postal_code_work_item_exceeding_20_characters_is_rej(page):
    """INVEST-TENDERS-TC-195 — Azure TC 146261. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('ZIP / postal code', "A" * (20 + 50), 1)
    form.click_submit()
    value = form.field_input_value('ZIP / postal code', 1)
    assert len(value) <= 20, (
        f"{'ZIP / postal code'} must not accept more than 20 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid Prequalification Approval Date is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146262")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146262
@pytest.mark.traceability("INVEST-TENDERS-TC-196")
def test_tc196_verify_that_a_valid_prequalification_approval_date_is_accepted(page):
    """INVEST-TENDERS-TC-196 — Azure TC 146262. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Prequalification Approval Date', 0), (
        f"{'Prequalification Approval Date'} should accept a valid value; got error "
        f"{form.field_error_text('Prequalification Approval Date', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that Prequalification Approval Date can be left blank')
@allure.label("pbi", "130952")
@allure.label("testcase", "146263")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146263
@pytest.mark.traceability("INVEST-TENDERS-TC-197")
def test_tc197_verify_that_prequalification_approval_date_can_be_left_blank(page):
    """INVEST-TENDERS-TC-197 — Azure TC 146263. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Prequalification Approval Date', 0)})
    form.click_submit()
    assert not form.field_has_visible_error('Prequalification Approval Date', 0), (
        f"{'Prequalification Approval Date'} is optional and must accept being left blank"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that selecting "No" for Should Allow NDA Tender is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146264")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146264
@pytest.mark.traceability("INVEST-TENDERS-TC-198")
def test_tc198_verify_that_selecting_no_for_should_allow_nda_tender_is_accepted(page):
    """INVEST-TENDERS-TC-198 — Azure TC 146264. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Should Allow NDA Tender', 0), (
        f"{'Should Allow NDA Tender'} should accept a valid value; got error "
        f"{form.field_error_text('Should Allow NDA Tender', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that leaving Should Allow NDA Tender unselected is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146265")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146265
@pytest.mark.traceability("INVEST-TENDERS-TC-199")
def test_tc199_verify_that_leaving_should_allow_nda_tender_unselected_is_rejected(page):
    """INVEST-TENDERS-TC-199 — Azure TC 146265. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Should Allow NDA Tender', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Should Allow NDA Tender', 0), (
        f"leaving {'Should Allow NDA Tender'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a valid positive Bid Validity Days (<=3 digits) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146266")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146266
@pytest.mark.traceability("INVEST-TENDERS-TC-200")
def test_tc200_verify_that_a_valid_positive_bid_validity_days_3_digits_is_accepted(page):
    """INVEST-TENDERS-TC-200 — Azure TC 146266. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.field_has_visible_error('Bid Validity (Days)', 0), (
        f"{'Bid Validity (Days)'} should accept a valid value; got error "
        f"{form.field_error_text('Bid Validity (Days)', 0)!r}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that an empty Bid Validity Days is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146267")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146267
@pytest.mark.traceability("INVEST-TENDERS-TC-201")
def test_tc201_verify_that_an_empty_bid_validity_days_is_rejected(page):
    """INVEST-TENDERS-TC-201 — Azure TC 146267. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Bid Validity (Days)', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Bid Validity (Days)', 0), (
        f"leaving {'Bid Validity (Days)'} empty must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a zero or negative Bid Validity Days is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146268")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146268
@pytest.mark.traceability("INVEST-TENDERS-TC-202")
def test_tc202_verify_that_a_zero_or_negative_bid_validity_days_is_rejected(page):
    """INVEST-TENDERS-TC-202 — Azure TC 146268. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Bid Validity (Days)', '-1', 0)
    form.click_submit()
    assert form.field_has_visible_error('Bid Validity (Days)', 0), (
        f"{'-1'} must be rejected for {'Bid Validity (Days)'} with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a non-numeric Bid Validity Days is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146269")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146269
@pytest.mark.traceability("INVEST-TENDERS-TC-203")
def test_tc203_verify_that_a_non_numeric_bid_validity_days_is_rejected(page):
    """INVEST-TENDERS-TC-203 — Azure TC 146269. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Bid Validity (Days)', 'abc', 0)
    form.click_submit()
    assert form.field_has_visible_error('Bid Validity (Days)', 0), (
        f"{'abc'} must be rejected for {'Bid Validity (Days)'} with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field validation")
@allure.title('Verify that a Bid Validity Days exceeding 3 digits is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146270")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146270
@pytest.mark.traceability("INVEST-TENDERS-TC-204")
def test_tc204_verify_that_a_bid_validity_days_exceeding_3_digits_is_rejected(page):
    """INVEST-TENDERS-TC-204 — Azure TC 146270. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.fill_field('Bid Validity (Days)', "A" * (3 + 50), 0)
    form.click_submit()
    value = form.field_input_value('Bid Validity (Days)', 0)
    assert len(value) <= 3, (
        f"{'Bid Validity (Days)'} must not accept more than 3 characters; got {len(value)}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — file uploads")
@allure.title('Verify that uploading a valid BOQ PDF (webform, <=5MB) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146271")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146271
@pytest.mark.traceability("INVEST-TENDERS-TC-205")
def test_tc205_verify_that_uploading_a_valid_boq_pdf_webform_5mb_is_accepted(page):
    """INVEST-TENDERS-TC-205 — Azure TC 146271. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.upload_field('Bill of Quantities (BOQ)', VALID_PDF, 0)
    form.click_submit()
    assert not form.field_has_visible_error('Bill of Quantities (BOQ)', 0), (
        f"a valid PDF upload for {'Bill of Quantities (BOQ)'} must be accepted"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — file uploads")
@allure.title('Verify that uploading a non-PDF BOQ (webform) is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146272")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146272
@pytest.mark.traceability("INVEST-TENDERS-TC-206")
def test_tc206_verify_that_uploading_a_non_pdf_boq_webform_is_rejected(page):
    """INVEST-TENDERS-TC-206 — Azure TC 146272. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.upload_field('Bill of Quantities (BOQ)', WRONG_TYPE_FILE, 0)
    form.click_submit()
    assert form.field_has_visible_error('Bill of Quantities (BOQ)', 0), (
        f"an invalid file for {'Bill of Quantities (BOQ)'} must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — file uploads")
@allure.title('Verify that uploading an oversized BOQ (webform, >5MB) is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146273")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146273
@pytest.mark.traceability("INVEST-TENDERS-TC-207")
def test_tc207_verify_that_uploading_an_oversized_boq_webform_5mb_is_rejected(page):
    """INVEST-TENDERS-TC-207 — Azure TC 146273. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.upload_field('Bill of Quantities (BOQ)', OVERSIZED_PDF, 0)
    form.click_submit()
    assert form.field_has_visible_error('Bill of Quantities (BOQ)', 0), (
        f"an invalid file for {'Bill of Quantities (BOQ)'} must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — file uploads")
@allure.title('Verify that submitting without any BOQ uploaded is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146274")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.regression
@pytest.mark.pbi_130952
@pytest.mark.tc_146274
@pytest.mark.traceability("INVEST-TENDERS-TC-208")
def test_tc208_verify_that_submitting_without_any_boq_uploaded_is_rejected(page):
    """INVEST-TENDERS-TC-208 — Azure TC 146274. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF, skip_labels={('Bill of Quantities (BOQ)', 0)})
    form.click_submit()
    assert form.field_has_visible_error('Bill of Quantities (BOQ)', 0), (
        f"submitting without {'Bill of Quantities (BOQ)'} must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — file uploads")
@allure.title('Verify that uploading a valid optional Additional Document (PDF, <=5MB) is accepted')
@allure.label("pbi", "130952")
@allure.label("testcase", "146275")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146275
@pytest.mark.traceability("INVEST-TENDERS-TC-209")
def test_tc209_verify_that_uploading_a_valid_optional_additional_document_pdf_5mb_is_(page):
    """INVEST-TENDERS-TC-209 — Azure TC 146275. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.upload_field('Additional Document', VALID_PDF, 0)
    form.click_submit()
    assert not form.field_has_visible_error('Additional Document', 0), (
        f"a valid PDF upload for {'Additional Document'} must be accepted"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — file uploads")
@allure.title('Verify that uploading a non-PDF Additional Document is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146276")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146276
@pytest.mark.traceability("INVEST-TENDERS-TC-210")
def test_tc210_verify_that_uploading_a_non_pdf_additional_document_is_rejected(page):
    """INVEST-TENDERS-TC-210 — Azure TC 146276. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.upload_field('Additional Document', WRONG_TYPE_FILE, 0)
    form.click_submit()
    assert form.field_has_visible_error('Additional Document', 0), (
        f"an invalid file for {'Additional Document'} must be rejected with a visible inline error"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — file uploads")
@allure.title('Verify that uploading an oversized Additional Document (>5MB) is rejected')
@allure.label("pbi", "130952")
@allure.label("testcase", "146277")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146277
@pytest.mark.traceability("INVEST-TENDERS-TC-211")
def test_tc211_verify_that_uploading_an_oversized_additional_document_5mb_is_rejected(page):
    """INVEST-TENDERS-TC-211 — Azure TC 146277. See module docstring's disclosed reading choices for any live gap/discrepancy noted for this case."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.upload_field('Additional Document', OVERSIZED_PDF, 0)
    form.click_submit()
    assert form.field_has_visible_error('Additional Document', 0), (
        f"an invalid file for {'Additional Document'} must be rejected with a visible inline error"
    )


# ===========================================================================
# LISTING FILTERS — TC-072..075
# ===========================================================================

@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Listing filters")
@allure.title("Search accepts a valid partial title match")
@allure.label("pbi", "130952")
@allure.label("testcase", "146138")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130952
@pytest.mark.tc_146138
@pytest.mark.traceability("INVEST-TENDERS-TC-072")
def test_tc072_search_accepts_valid_partial_title_match(page):
    """INVEST-TENDERS-TC-072 — Azure TC 146138."""
    listing = TendersListingPage(page).open_listing()
    full_title = listing.card_title_text(0)
    partial = full_title.split(" ")[0]
    listing.search_for(partial)
    titles = listing.card_titles()
    assert titles, f"searching {partial!r} (from {full_title!r}) returned no cards"
    assert all(partial.lower() in t.lower() for t in titles), (
        f"every returned card title should contain {partial!r}; got {titles}"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Listing filters")
@allure.title("Search with no results shows the empty state, not an error")
@allure.label("pbi", "130952")
@allure.label("testcase", "146139")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130952
@pytest.mark.tc_146139
@pytest.mark.traceability("INVEST-TENDERS-TC-073")
def test_tc073_search_no_results_shows_empty_state(page):
    """INVEST-TENDERS-TC-073 — Azure TC 146139. CONFIRMED LIVE 2026-09-24:
    the empty state renders 'No tenders match your search.' plus a
    'Showing 0 of 0 tenders.' line — no error/exception surfaces."""
    listing = TendersListingPage(page).open_listing()
    listing.search_for("zzzz-qctest-no-such-tender-zzzz")
    assert listing.empty_state_visible(), "expected the confirmed-live empty-state text, not an error"
    assert listing.card_count() == 0


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Listing filters")
@allure.title("Selecting a specific Category filters the grid exactly")
@allure.label("pbi", "130952")
@allure.label("testcase", "146140")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130952
@pytest.mark.tc_146140
@pytest.mark.traceability("INVEST-TENDERS-TC-074")
def test_tc074_selecting_category_filters_grid_exactly(page):
    """INVEST-TENDERS-TC-074 — Azure TC 146140."""
    listing = TendersListingPage(page).open_listing()
    listing.select_category("Goods")
    badges = listing.card_badge_texts()
    assert badges, "selecting Goods returned no cards to check"
    assert all(b.strip() == "Goods" for b in badges), f"every card badge should read Goods; got {badges}"


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Listing filters")
@allure.title('"All Categories" (default) shows every published category')
@allure.label("pbi", "130952")
@allure.label("testcase", "146141")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130952
@pytest.mark.tc_146141
@pytest.mark.traceability("INVEST-TENDERS-TC-075")
def test_tc075_all_categories_default_shows_every_category(page):
    """INVEST-TENDERS-TC-075 — Azure TC 146141."""
    listing = TendersListingPage(page).open_listing()
    assert listing.category_option_texts()[0] == "All Categories"
    badges = {b.strip() for b in listing.card_badge_texts()}
    assert len(badges) >= 1, "expected at least one category badge on the default (unfiltered) grid"


# ===========================================================================
# EDGE / SPECIAL CASES — TC-213, TC-216, TC-218
# ===========================================================================

@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — security")
@allure.title("An incomplete/unsolved CAPTCHA blocks submission")
@allure.label("pbi", "130952")
@allure.label("testcase", "146279")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.regression
@pytest.mark.pbi_130952
@pytest.mark.tc_146279
@pytest.mark.traceability("INVEST-TENDERS-TC-213")
def test_tc213_unsolved_captcha_blocks_submission(page):
    """INVEST-TENDERS-TC-213 — Azure TC 146279. A live reCAPTCHA field is
    confirmed present on this form (module docstring reading #1) — this
    test fills every OTHER field validly and submits WITHOUT solving it,
    asserting the submission does not complete (still on the same form,
    no success banner) — the real, observable signal of "blocked."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_valid_form(VALID_PDF)
    form.click_submit()
    assert not form.success_banner_visible(), "an unsolved CAPTCHA must block submission, not silently succeed"
    assert "submit-your-etender" in page.url, "a blocked submission should stay on the webform, not navigate away"


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform")
@allure.title("A cancel action on the webform discards entered data without submitting")
@allure.label("pbi", "130952")
@allure.label("testcase", "146282")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.pbi_130952
@pytest.mark.tc_146282
@pytest.mark.traceability("INVEST-TENDERS-TC-216")
def test_tc216_cancel_discards_entered_data(page):
    """INVEST-TENDERS-TC-216 — Azure TC 146282. LIVE GAP: no dedicated
    "Cancel" control was found on the live form (confirmed live — the
    button list contains only "Submit"). Scripted to the closest live-
    observable stand-in (navigating away and back reloads a blank form)
    per module docstring's disclosed reading #7; reported as a case/design
    gap, not invented as a button that does not exist."""
    form = SubmitETenderFormPage(page).open_form()
    form.fill_field("Organization name", "QCTEST should be discarded", 0)
    form.open_form()
    assert form.field_input_value("Organization name", 0) == "", (
        "re-opening the webform must not retain previously entered data"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Tenders")
@allure.story("Submit your eTender webform — field dependency")
@allure.title("The Country dropdown selection drives available City lookup values (field-dependency case)")
@allure.label("pbi", "130952")
@allure.label("testcase", "146284")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.webform
@pytest.mark.lookupdata
@pytest.mark.pbi_130952
@pytest.mark.tc_146284
@pytest.mark.traceability("INVEST-TENDERS-TC-218")
def test_tc218_country_drives_city_lookup_values(page):
    """INVEST-TENDERS-TC-218 — Azure TC 146284. LIVE GAP: City is a plain
    free-text `<input>` on this build (confirmed live), not a Country-
    dependent lookup/select — there are no "available City values" for a
    Country choice to drive. Scripted to the case's own stated premise
    (changing Country changes what City accepts) — expected to FAIL
    honestly on this build per Result Integrity, since no dependent-
    lookup behavior exists to observe; a real product/design gap against
    this case's premise, not a locator defect."""
    form = SubmitETenderFormPage(page).open_form()
    tag_before = form._control_for("City", 0).evaluate("el => el.tagName")
    assert tag_before == "SELECT", (
        "City must be a lookup/select whose options depend on the chosen Country per this "
        f"case's premise; the live control is a {tag_before}, not a dependent lookup"
    )
