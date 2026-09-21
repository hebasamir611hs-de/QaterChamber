"""
web/tests/mediation/test_mediation_web.py — Web-platform cases for PBI 129405
(QC-SVC-007 — Mediation), sourced from Azure DevOps test suite 138836 (plan
137724), filtered to the 13 cases that carry no Control_Panel tag (live-read
2026-09-20 via `get_test_cases_from_suite` — `review_test_coverage(parent_id=
129405)` 404s; it resolves via PBI relations, and this suite's link only
surfaces through the suite itself, not the PBI's own relation graph).

Scope note: this PBI's suite is ENTIRELY Functional-Low (no UI-tagged case
exists in it at all — 200/200 cases are Functional-Low; see the QA Manager's
2026-09-20 finding). These 13 are the "no Control_Panel" slice of that set —
all "empty required field blocks Next" checks on the 2-step Mediation Request
wizard (Step 01 Applicant, Step 02 Respondent). All 13 shown here.

Scripted as ONE parametrized test per step (9 Step-01 cases + 4 Step-02
cases) rather than 13 near-identical bodies — the case set IS a parametrized
family (same shape, different field), and automation-standards.md's
one-file-per-case prohibition applies with equal force to 13 copy-pasted
bodies. Each parametrize case still carries its own tc_<azure_id> marker
and traceability id, so `pytest -m tc_138660` still selects exactly one.

Locators — INTENTIONALLY NOT EXTRACTED (explicit QA Manager instruction,
2026-09-20 session). Every MediationPage locator constant is a TODO(locator)
placeholder; these tests will fail at the first Page Object call until
`extract-locators` fills them in.
"""

import allure
import pytest

from web.pages.mediation.mediation_page import MediationPage

# ---------------------------------------------------------------------------
# (field_key, field_label, azure_tc_id, extra_marks) — mirrors each case's
# own EXPECTED text ("'<Label> is required' appears under the field").
# ---------------------------------------------------------------------------
def _marks(tc_id: int, uat: bool) -> tuple:
    marks = [getattr(pytest.mark, f"tc_{tc_id}"), pytest.mark.traceability(str(tc_id))]
    if uat:
        marks.append(pytest.mark.uat)
    return tuple(marks)


STEP1_CASES = [
    pytest.param("company_name", "Company Name", 138660, True, id="138660-company-name", marks=_marks(138660, True)),
    pytest.param("commercial_registration_no", "Commercial Registration No.", 138665, False, id="138665-cr-no", marks=_marks(138665, False)),
    pytest.param("chamber_membership_number", "Chamber Membership Number", 138669, False, id="138669-membership-no", marks=_marks(138669, False)),
    pytest.param("contact_person_name", "Contact Person Name", 138672, True, id="138672-contact-person", marks=_marks(138672, True)),
    pytest.param("job_title", "Job Title", 138676, True, id="138676-job-title", marks=_marks(138676, True)),
    pytest.param("email_address", "Email Address", 138680, False, id="138680-email", marks=_marks(138680, False)),
    pytest.param("mobile_number", "Mobile Number", 138684, False, id="138684-mobile", marks=_marks(138684, False)),
    pytest.param("company_address", "Company Address", 138691, True, id="138691-company-address", marks=_marks(138691, True)),
    pytest.param("country", "Country", 138694, False, id="138694-country", marks=_marks(138694, False)),
]

# NOTE (arbitrated against the live page, 2026-09-20): only the company-name
# field in Step 02 carries the "Respondent " prefix. The contact-person, email
# and mobile fields render as plain "Contact Person", "Email Address" and
# "Mobile Number" — identical to their Step 01 counterparts — and their inline
# errors use those same labels. The case text assumed a "Respondent " prefix on
# all four. Expectations below mirror what the page actually renders; PENDING
# PBI 129405 design confirmation on whether Step 02 labels should be prefixed
# for consistency (if the design changes, these three strings change with it).
STEP2_CASES = [
    pytest.param("respondent_company_name", "Respondent Company Name", 138699, True, id="138699-resp-company-name", marks=_marks(138699, True)),
    pytest.param("respondent_contact_person", "Contact Person", 138703, True, id="138703-resp-contact-person", marks=_marks(138703, True)),
    pytest.param("respondent_email_address", "Email Address", 138707, False, id="138707-resp-email", marks=_marks(138707, False)),
    pytest.param("respondent_mobile_number", "Mobile Number", 138711, False, id="138711-resp-mobile", marks=_marks(138711, False)),
]

_STEP1_KEYS = [c.values[0] for c in STEP1_CASES]
_STEP2_KEYS = [c.values[0] for c in STEP2_CASES]


# ===========================================================================
# Step 01 (Applicant) — 9 cases: empty required field blocks Next
# ===========================================================================
@allure.epic("Services")
@allure.feature("Mediation")
@allure.story("Request wizard — Step 01 required-field validation")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129405
@pytest.mark.parametrize("field_key,field_label,tc_id,is_uat", STEP1_CASES)
def test_mediation_step1_empty_required_field_blocks_next(page, field_key, field_label, tc_id, is_uat):
    allure.dynamic.title(f"Clicking Next with an empty {field_label} shows the inline required message and blocks the step")
    allure.dynamic.label("testcase", str(tc_id))
    allure.dynamic.label("pbi", "129405")

    mp = MediationPage(page)

    with allure.step("Open the Mediation Request wizard as a public visitor via the Submit New Request CTA"):
        mp.open_mediation_wizard(locale="en")

    # Step 1 — Next button enabled by default
    assert mp.next_button_is_enabled()

    # Step 2 — every mandatory field filled except field_key
    with allure.step(f"Complete every mandatory field in Step 01 except {field_label}"):
        mp.fill_step1(skip=field_key)

    # Step 3 — Next blocked, inline required message appears
    with allure.step("Click Next"):
        other_values_before = {k: mp.field_value(k) for k in _STEP1_KEYS if k != field_key}
        mp.click_next()
        # The live wizard renders the inline error WITH a trailing period
        # ("<Label> is required."), as documented in the MediationPage module
        # docstring; the case text omitted it. Arbitrated against the live page.
        assert mp.field_error_text(field_key) == f"{field_label} is required."

    # Step 4 — still on Step 01, every other field retains its value
    with allure.step("Inspect the form and the step indicator"):
        assert "01" in mp.current_step_text()
        for key, value in other_values_before.items():
            assert mp.field_value(key) == value


# ===========================================================================
# Step 02 (Respondent) — 4 cases: empty required field blocks Next
# ===========================================================================
@allure.epic("Services")
@allure.feature("Mediation")
@allure.story("Request wizard — Step 02 required-field validation")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.pbi_129405
@pytest.mark.parametrize("field_key,field_label,tc_id,is_uat", STEP2_CASES)
def test_mediation_step2_empty_required_field_blocks_next(page, field_key, field_label, tc_id, is_uat):
    allure.dynamic.title(f"Clicking Next with an empty {field_label} shows the inline required message and blocks the step")
    allure.dynamic.label("testcase", str(tc_id))
    allure.dynamic.label("pbi", "129405")

    mp = MediationPage(page)

    with allure.step("Open the Mediation Request wizard and advance to Step 02"):
        mp.open_mediation_wizard(locale="en")
        mp.advance_to_step2()

    # Step 1 — Next button enabled by default
    assert mp.next_button_is_enabled()

    # Step 2 — every mandatory field filled except field_key
    with allure.step(f"Complete every mandatory field in Step 02 except {field_label}"):
        mp.fill_step2(skip=field_key)

    # Step 3 — Next blocked, inline required message appears
    with allure.step("Click Next"):
        other_values_before = {k: mp.field_value(k) for k in _STEP2_KEYS if k != field_key}
        mp.click_next()
        # The live wizard renders the inline error WITH a trailing period
        # ("<Label> is required."), as documented in the MediationPage module
        # docstring; the case text omitted it. Arbitrated against the live page.
        assert mp.field_error_text(field_key) == f"{field_label} is required."

    # Step 4 — still on Step 02, every other field retains its value
    with allure.step("Inspect the form and the step indicator"):
        assert "02" in mp.current_step_text()
        for key, value in other_values_before.items():
            assert mp.field_value(key) == value
