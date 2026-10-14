"""
web/tests/qafl_membership/test_qafl_membership_step1_web.py — Step 1
(Company Identity) field cases for PBI 130718: names, Company Registered Under
and its MOCI / QFC / QFZ / Other conditional fields, Company Size, Company
Type, Market Presence and their conditional fields.

SCRIPTED OFFLINE 2026-10-07, NOT EXECUTED. Character-limit cases are skipped
N/A (team decision 2026-10-03). The shared AAA bodies and the baseline data
are in qafl_data.py (its docstring explains why the filler differs from the
undefined "A-2").
"""

import allure
import pytest

from web.pages.qafl_membership.qafl_membership_page import QaflMembershipPage
from web.tests.qafl_membership.qafl_data import (
    CHAR_LIMIT_SKIP,
    COMPANY_TYPE_LABELS,
    CRU_LABELS,
    KB,
    MB,
    FileMaker,
    anon,
    build,
    open_page,
    run_accepts,
    run_blocked,
    run_char_limit,
    run_file_size,
    run_file_type_rejected,
    run_non_numeric,
    run_required,
    run_whitespace,
)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Company English Name accepts the valid value 'Gulf Freight Logistics WLL'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146566
@pytest.mark.traceability("146566")
@allure.label("pbi", "130718")
@allure.label("testcase", "146566")
@anon()
def test_146566_company_english_name_accepts_the_valid_value_gulf_freight_lo(page, tmp_path):
    """Verify that Company English Name accepts the valid value 'Gulf Freight Logistics WLL'

    Steps (case is the oracle):
    1. Open Step 1 (EN) -> Step 1 displayed
    2. Enter 'Gulf Freight Logistics WLL' in Company English Name -> Value shown with no inline error
    3. Click Next -> Wizard advances to Step 2 and value is retained when returning with Previous
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146566, 1, 'companyEnglishName', 'Gulf Freight Logistics WLL', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that leaving Company English Name empty blocks progress with an inline required error')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146567
@pytest.mark.traceability("146567")
@allure.label("pbi", "130718")
@allure.label("testcase", "146567")
@anon()
def test_146567_leaving_company_english_name_empty_blocks_progress_with_an_i(page, tmp_path):
    """Verify that leaving Company English Name empty blocks progress with an inline required error

    Steps (case is the oracle):
    1. Open Step 1 and leave Company English Name empty -> Step 1 displayed
    2. Fill other fields with baseline data -> Other fields accepted
    3. Click Next -> Inline required error under Company English Name; user stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146567, 1, 'companyEnglishName', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Company English Name enforces the 200-character limit (200 accepted, 201 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146568
@pytest.mark.traceability("146568")
@allure.label("pbi", "130718")
@allure.label("testcase", "146568")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146568_company_english_name_enforces_the_200_character_limit_200_ac(page, tmp_path):
    """Verify that Company English Name enforces the 200-character limit (200 accepted, 201 rejected)

    Steps (case is the oracle):
    1. Open Step 1 -> Step 1 displayed
    2. Enter 200 x 'A' and click Next -> 200 characters accepted, no error, wizard advances
    3. Return and enter 201 x 'A' -> Input capped at 200 or inline length error; 201-character value
       never accepted or stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146568, 1, 'companyEnglishName', 200, char='A', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Company English Name is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146569
@pytest.mark.traceability("146569")
@allure.label("pbi", "130718")
@allure.label("testcase", "146569")
@anon()
def test_146569_a_whitespace_only_company_english_name_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Company English Name is rejected as empty

    Steps (case is the oracle):
    1. Open Step 1 -> Step 1 displayed
    2. Enter '   ' (3 spaces) in Company English Name -> Field holds spaces
    3. Click Next -> Inline required error shown; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146569, 1, 'companyEnglishName', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Company Arabic Name accepts the valid value 'الخليج للشحن واللوجستيات ذ.م.م'")
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146570
@pytest.mark.traceability("146570")
@allure.label("pbi", "130718")
@allure.label("testcase", "146570")
@anon()
def test_146570_company_arabic_name_accepts_the_valid_value(page, tmp_path):
    """Verify that Company Arabic Name accepts the valid value 'الخليج للشحن واللوجستيات ذ.م.م'

    Steps (case is the oracle):
    1. Open Step 1 -> Step 1 displayed
    2. Enter 'الخليج للشحن واللوجستيات ذ.م.م' in Company Arabic Name -> Arabic text shown correctly, no
       error
    3. Click Next -> Wizard advances; value retained on Previous
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146570, 1, 'companyArabicName', 'الخليج للشحن واللوجستيات ذ.م.م', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that leaving Company Arabic Name empty blocks progress with an inline required error')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146571
@pytest.mark.traceability("146571")
@allure.label("pbi", "130718")
@allure.label("testcase", "146571")
@anon()
def test_146571_leaving_company_arabic_name_empty_blocks_progress_with_an_in(page, tmp_path):
    """Verify that leaving Company Arabic Name empty blocks progress with an inline required error

    Steps (case is the oracle):
    1. Open Step 1 and leave Company Arabic Name empty -> Step 1 displayed
    2. Fill other fields with baseline data -> Other fields accepted
    3. Click Next -> Inline required error under Company Arabic Name; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146571, 1, 'companyArabicName', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Company Arabic Name enforces the 200-character limit (200 accepted, 201 rejected)')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146572
@pytest.mark.traceability("146572")
@allure.label("pbi", "130718")
@allure.label("testcase", "146572")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146572_company_arabic_name_enforces_the_200_character_limit_200_acc(page, tmp_path):
    """Verify that Company Arabic Name enforces the 200-character limit (200 accepted, 201 rejected)

    Steps (case is the oracle):
    1. Open Step 1 -> Step 1 displayed
    2. Enter 200 x 'ش' and click Next -> 200 characters accepted, wizard advances
    3. Return and enter 201 x 'ش' -> Input capped at 200 or inline length error; 201 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146572, 1, 'companyArabicName', 200, char='ش', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Company Arabic Name is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146573
@pytest.mark.traceability("146573")
@allure.label("pbi", "130718")
@allure.label("testcase", "146573")
@anon()
def test_146573_a_whitespace_only_company_arabic_name_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Company Arabic Name is rejected as empty

    Steps (case is the oracle):
    1. Open Step 1 -> Step 1 displayed
    2. Enter '   ' in Company Arabic Name -> Field holds spaces
    3. Click Next -> Inline required error shown; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146573, 1, 'companyArabicName', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Company Registered Under accepts the selection 'Qatar Ministry of Commerce and Industry (MOCI)'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.lookupdata
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146575
@pytest.mark.traceability("146575")
@allure.label("pbi", "130718")
@allure.label("testcase", "146575")
@anon()
def test_146575_company_registered_under_accepts_the_selection_qatar_ministr(page, tmp_path):
    """Verify that Company Registered Under accepts the selection 'Qatar Ministry of Commerce and Industry (MOCI)'

    Steps (case is the oracle):
    1. Open Step 1 and open the Company Registered Under dropdown -> Dropdown lists exactly MOCI, QFC,
       QFZ, Other from the lookup
    2. Select 'Qatar Ministry of Commerce and Industry (MOCI)' -> MOCI shown as the selected value and
       the MOCI block appears below
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    with allure.step("Open Company Registered Under: exactly MOCI, QFC, QFZ, Other from the lookup"):
        qp.wait_for_options_loaded("companyRegisteredUnder")
        assert qp.option_texts("companyRegisteredUnder") == CRU_LABELS, qp.option_texts("companyRegisteredUnder")
    with allure.step("Select MOCI: shown as the selected value and the MOCI block appears"):
        qp.select("companyRegisteredUnder", label=CRU_LABELS[0])
        assert qp.selected_option_text("companyRegisteredUnder") == CRU_LABELS[0]
        assert qp.is_shown(qp.COND_GROUP_N.format(group="moci")), "MOCI block did not appear"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that leaving Company Registered Under unselected blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146576
@pytest.mark.traceability("146576")
@allure.label("pbi", "130718")
@allure.label("testcase", "146576")
@anon()
def test_146576_leaving_company_registered_under_unselected_blocks_progress(page, tmp_path):
    """Verify that leaving Company Registered Under unselected blocks progress

    Steps (case is the oracle):
    1. Open Step 1 and leave Company Registered Under on its placeholder -> Placeholder 'Select
       registration authority' shown
    2. Fill the other fields with baseline data -> Other fields accepted
    3. Click Next -> Inline required error under the dropdown; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    with allure.step("Leave Company Registered Under on its placeholder"):
        qp.wait_for_options_loaded("companyRegisteredUnder")
        assert qp.selected_option_text("companyRegisteredUnder") == "Select registration authority"
    with allure.step("Fill the other Step 1 fields with baseline data and click Next"):
        qp.fill(build(1, files, 146576, exclude=("companyRegisteredUnder",)))
        qp.click_next()
    with allure.step("Inline required error under the dropdown; stays on Step 1"):
        assert qp.has_field_error("companyRegisteredUnder"), "no inline required error under Company Registered Under"
        assert qp.current_step() == 1


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Company Size accepts the selection 'Medium (51-500)'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146577
@pytest.mark.traceability("146577")
@allure.label("pbi", "130718")
@allure.label("testcase", "146577")
@anon()
def test_146577_company_size_accepts_the_selection_medium_51_500(page, tmp_path):
    """Verify that Company Size accepts the selection 'Medium (51-500)'

    Steps (case is the oracle):
    1. Open Step 1 -> Four cards displayed
    2. Click the 'Medium' card ('51–500 employees') -> Only 'Medium' is selected (single-select)
    3. Click Next -> Wizard advances; 'Medium' stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    with allure.step("Four Company Size cards displayed"):
        assert qp.count(qp.RADIO_CARD_ANY.format(name="companySize")) == 4
    with allure.step("Click the Medium card: only Medium is selected"):
        qp.click(qp.RADIO_CARD.format(name="companySize", value="medium"))
        assert qp.field_value("companySize") == "medium"
        checked = qp.page.locator('input[name="companySize"]:checked').count()
        assert checked == 1, f"{checked} Company Size cards selected"
    with allure.step("Click Next: wizard advances; Medium retained"):
        qp.fill(build(1, files, 146577, exclude=("companySize",)))
        qp.click_next()
        assert qp.wait_for_step(2)
        qp.click_previous()
        assert qp.wait_for_step(1)
        assert qp.field_value("companySize") == "medium"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that leaving Company Size unselected blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146578
@pytest.mark.traceability("146578")
@allure.label("pbi", "130718")
@allure.label("testcase", "146578")
@anon()
def test_146578_leaving_company_size_unselected_blocks_progress(page, tmp_path):
    """Verify that leaving Company Size unselected blocks progress

    Steps (case is the oracle):
    1. Open Step 1 with no Company Size selected -> No card selected
    2. Fill other fields with baseline data -> Other fields accepted
    3. Click Next -> Inline required error under Company Size; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146578, 1, 'companySize', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Company Size (Other) accepts the valid number 750')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146579
@pytest.mark.traceability("146579")
@allure.label("pbi", "130718")
@allure.label("testcase", "146579")
@anon()
def test_146579_company_size_other_accepts_the_valid_number_750(page, tmp_path):
    """Verify that Company Size (Other) accepts the valid number 750

    Steps (case is the oracle):
    1. Select Company Size 'Other' -> Numeric field appears
    2. Enter 750 in the revealed count field -> 750 accepted with no error
    3. Click Next -> Wizard advances; 750 stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146579, 1, 'companySizeOther', '750', cru='qfc', extra={'companySize': 'other'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Company Size (Other) blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146580
@pytest.mark.traceability("146580")
@allure.label("pbi", "130718")
@allure.label("testcase", "146580")
@anon()
def test_146580_an_empty_company_size_other_blocks_progress(page, tmp_path):
    """Verify that an empty Company Size (Other) blocks progress

    Steps (case is the oracle):
    1. Select Company Size 'Other' and leave the count empty -> Count field shown
    2. Observe the count field -> Empty
    3. Click Next -> Inline required error under the count field; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_blocked(qp, files, 146580, 1, 'companySizeOther', cru='qfc', override={'companySize': 'other'}, exclude=('companySizeOther',))


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that non-numeric 'abc' is rejected in Company Size (Other)")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146581
@pytest.mark.traceability("146581")
@allure.label("pbi", "130718")
@allure.label("testcase", "146581")
@anon()
def test_146581_non_numeric_abc_is_rejected_in_company_size_other(page, tmp_path):
    """Verify that non-numeric 'abc' is rejected in Company Size (Other)

    Steps (case is the oracle):
    1. Select Company Size 'Other' -> Count field shown
    2. Type 'abc' in the count field -> Letters not accepted or flagged
    3. Click Next -> Inline format error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_non_numeric(qp, files, 146581, 1, 'companySizeOther', 'abc', extra={'companySize': 'other'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Company Size (Other) enforces the 10-character limit (10 accepted, 11 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146582
@pytest.mark.traceability("146582")
@allure.label("pbi", "130718")
@allure.label("testcase", "146582")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146582_company_size_other_enforces_the_10_character_limit_10_accept(page, tmp_path):
    """Verify that Company Size (Other) enforces the 10-character limit (10 accepted, 11 rejected)

    Steps (case is the oracle):
    1. Select Company Size 'Other' -> Count field shown
    2. Enter 1234567890 and click Next -> 10 digits accepted
    3. Return and enter 12345678901 -> Input capped at 10 or inline error; 11 digits never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146582, 1, 'companySizeOther', 10, char='1', cru='qfc', extra={'companySize': 'other'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Company Size (Other) is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146583
@pytest.mark.traceability("146583")
@allure.label("pbi", "130718")
@allure.label("testcase", "146583")
@anon()
def test_146583_a_whitespace_only_company_size_other_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Company Size (Other) is rejected as empty

    Steps (case is the oracle):
    1. Select Company Size 'Other' -> Count field shown
    2. Enter '   ' -> Spaces entered
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146583, 1, 'companySizeOther', cru='qfc', value='   ', extra={'companySize': 'other'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Company Type accepts the selection 'LLC'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.lookupdata
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146584
@pytest.mark.traceability("146584")
@allure.label("pbi", "130718")
@allure.label("testcase", "146584")
@anon()
def test_146584_company_type_accepts_the_selection_llc(page, tmp_path):
    """Verify that Company Type accepts the selection 'LLC'

    Steps (case is the oracle):
    1. Open Step 1 and open Company Type -> Dropdown lists the lookup values (Public, Private, LLC, Non-
       profit, Other) with placeholder 'Select company type'
    2. Select 'LLC' -> 'LLC' selected and shown
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    with allure.step("Open Company Type: lookup values with placeholder 'Select company type'"):
        qp.wait_for_options_loaded("companyType")
        assert qp.option_texts("companyType", include_placeholder=True)[0] == "Select company type"
        assert qp.option_texts("companyType") == COMPANY_TYPE_LABELS, qp.option_texts("companyType")
    with allure.step("Select LLC: shown as selected"):
        qp.select("companyType", label="LLC")
        assert qp.selected_option_text("companyType") == "LLC"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that leaving Company Type unselected blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146585
@pytest.mark.traceability("146585")
@allure.label("pbi", "130718")
@allure.label("testcase", "146585")
@anon()
def test_146585_leaving_company_type_unselected_blocks_progress(page, tmp_path):
    """Verify that leaving Company Type unselected blocks progress

    Steps (case is the oracle):
    1. Open Step 1 leaving Company Type unselected -> Placeholder shown
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error under Company Type; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146585, 1, 'companyType', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Company Type (Other) accepts the valid value 'Cooperative Society'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146586
@pytest.mark.traceability("146586")
@allure.label("pbi", "130718")
@allure.label("testcase", "146586")
@anon()
def test_146586_company_type_other_accepts_the_valid_value_cooperative_socie(page, tmp_path):
    """Verify that Company Type (Other) accepts the valid value 'Cooperative Society'

    Steps (case is the oracle):
    1. Select Company Type 'Other' -> Text field appears
    2. Enter 'Cooperative Society' -> Value accepted
    3. Click Next -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146586, 1, 'companyTypeOther', 'Cooperative Society', cru='qfc', extra={'companyType': {'label': 'Other'}})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Company Type (Other) blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146587
@pytest.mark.traceability("146587")
@allure.label("pbi", "130718")
@allure.label("testcase", "146587")
@anon()
def test_146587_an_empty_company_type_other_blocks_progress(page, tmp_path):
    """Verify that an empty Company Type (Other) blocks progress

    Steps (case is the oracle):
    1. Select Company Type 'Other' leaving the text empty -> Text field shown
    2. Observe the text field -> Empty
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_blocked(qp, files, 146587, 1, 'companyTypeOther', cru='qfc', override={'companyType': {'label': 'Other'}}, exclude=('companyTypeOther',))


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Company Type (Other) enforces the 100-character limit (100 accepted, 101 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146588
@pytest.mark.traceability("146588")
@allure.label("pbi", "130718")
@allure.label("testcase", "146588")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146588_company_type_other_enforces_the_100_character_limit_100_acce(page, tmp_path):
    """Verify that Company Type (Other) enforces the 100-character limit (100 accepted, 101 rejected)

    Steps (case is the oracle):
    1. Select Company Type 'Other' -> Text field shown
    2. Enter 100 x 'A' and click Next -> 100 accepted
    3. Return and enter 101 x 'A' -> Input capped at 100 or inline error; 101 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146588, 1, 'companyTypeOther', 100, char='A', cru='qfc', extra={'companyType': {'label': 'Other'}})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Company Type (Other) is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146589
@pytest.mark.traceability("146589")
@allure.label("pbi", "130718")
@allure.label("testcase", "146589")
@anon()
def test_146589_a_whitespace_only_company_type_other_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Company Type (Other) is rejected as empty

    Steps (case is the oracle):
    1. Select Company Type 'Other' -> Text field shown
    2. Enter '   ' -> Spaces entered
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146589, 1, 'companyTypeOther', cru='qfc', value='   ', extra={'companyType': {'label': 'Other'}})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Market Presence accepts 'Local' and reveals no conditional field")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146590
@pytest.mark.traceability("146590")
@allure.label("pbi", "130718")
@allure.label("testcase", "146590")
@anon()
def test_146590_market_presence_accepts_local_and_reveals_no_conditional_fie(page, tmp_path):
    """Verify that Market Presence accepts 'Local' and reveals no conditional field

    Steps (case is the oracle):
    1. Open Step 1 -> Four cards shown
    2. Click the 'Local' card -> 'Local' selected; no extra field appears
    3. Click Next -> Wizard advances; 'Local' stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    with allure.step("Four Market Presence cards shown"):
        assert qp.count(qp.RADIO_CARD_ANY.format(name="marketPresence")) == 4
    with allure.step("Click Local: selected, no extra field appears"):
        qp.click(qp.RADIO_CARD.format(name="marketPresence", value="local"))
        assert qp.field_value("marketPresence") == "local"
        for cond in ("regionalMarkets", "internationalMarkets", "marketPresenceOther"):
            assert not qp.is_field_visible(cond), f"{cond} appeared for Local"
    with allure.step("Click Next: wizard advances; Local retained"):
        qp.fill(build(1, files, 146590))
        qp.click_next()
        assert qp.wait_for_step(2)
        qp.click_previous()
        assert qp.wait_for_step(1)
        assert qp.field_value("marketPresence") == "local"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that leaving Market Presence unselected blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146591
@pytest.mark.traceability("146591")
@allure.label("pbi", "130718")
@allure.label("testcase", "146591")
@anon()
def test_146591_leaving_market_presence_unselected_blocks_progress(page, tmp_path):
    """Verify that leaving Market Presence unselected blocks progress

    Steps (case is the oracle):
    1. Open Step 1 with no Market Presence selected -> No card selected
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error under Market Presence; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146591, 1, 'marketPresence', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Regional Markets accepts 'Kuwait, Saudi Arabia, Bahrain'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146592
@pytest.mark.traceability("146592")
@allure.label("pbi", "130718")
@allure.label("testcase", "146592")
@anon()
def test_146592_regional_markets_accepts_kuwait_saudi_arabia_bahrain(page, tmp_path):
    """Verify that Regional Markets accepts 'Kuwait, Saudi Arabia, Bahrain'

    Steps (case is the oracle):
    1. Select Market Presence 'Regional' -> Text area appears
    2. Enter 'Kuwait, Saudi Arabia, Bahrain' in Regional Markets -> Value accepted
    3. Click Next -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146592, 1, 'regionalMarkets', 'Kuwait, Saudi Arabia, Bahrain', cru='qfc', extra={'marketPresence': 'regional'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Regional Markets blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146593
@pytest.mark.traceability("146593")
@allure.label("pbi", "130718")
@allure.label("testcase", "146593")
@anon()
def test_146593_an_empty_regional_markets_blocks_progress(page, tmp_path):
    """Verify that an empty Regional Markets blocks progress

    Steps (case is the oracle):
    1. Select Market Presence 'Regional' leaving the text area empty -> Text area shown
    2. Observe the text area -> Empty
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_blocked(qp, files, 146593, 1, 'regionalMarkets', cru='qfc', override={'marketPresence': 'regional'}, exclude=('regionalMarkets',))


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Regional Markets is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146594
@pytest.mark.traceability("146594")
@allure.label("pbi", "130718")
@allure.label("testcase", "146594")
@anon()
def test_146594_a_whitespace_only_regional_markets_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Regional Markets is rejected as empty

    Steps (case is the oracle):
    1. Select 'Regional' -> Text area shown
    2. Enter '   ' then a newline -> Whitespace held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146594, 1, 'regionalMarkets', cru='qfc', value='   \n', extra={'marketPresence': 'regional'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that International Markets accepts 'Germany, India, China'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146595
@pytest.mark.traceability("146595")
@allure.label("pbi", "130718")
@allure.label("testcase", "146595")
@anon()
def test_146595_international_markets_accepts_germany_india_china(page, tmp_path):
    """Verify that International Markets accepts 'Germany, India, China'

    Steps (case is the oracle):
    1. Select Market Presence 'International' -> Text area appears
    2. Enter 'Germany, India, China' -> Value accepted
    3. Click Next -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146595, 1, 'internationalMarkets', 'Germany, India, China', cru='qfc', extra={'marketPresence': 'international'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty International Markets blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146596
@pytest.mark.traceability("146596")
@allure.label("pbi", "130718")
@allure.label("testcase", "146596")
@anon()
def test_146596_an_empty_international_markets_blocks_progress(page, tmp_path):
    """Verify that an empty International Markets blocks progress

    Steps (case is the oracle):
    1. Select 'International' leaving the text area empty -> Text area shown
    2. Observe the text area -> Empty
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_blocked(qp, files, 146596, 1, 'internationalMarkets', cru='qfc', override={'marketPresence': 'international'}, exclude=('internationalMarkets',))


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only International Markets is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146597
@pytest.mark.traceability("146597")
@allure.label("pbi", "130718")
@allure.label("testcase", "146597")
@anon()
def test_146597_a_whitespace_only_international_markets_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only International Markets is rejected as empty

    Steps (case is the oracle):
    1. Select 'International' -> Text area shown
    2. Enter '   ' -> Whitespace held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146597, 1, 'internationalMarkets', cru='qfc', value='   ', extra={'marketPresence': 'international'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Market Presence (Other) accepts 'Africa and Central Asia'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146598
@pytest.mark.traceability("146598")
@allure.label("pbi", "130718")
@allure.label("testcase", "146598")
@anon()
def test_146598_market_presence_other_accepts_africa_and_central_asia(page, tmp_path):
    """Verify that Market Presence (Other) accepts 'Africa and Central Asia'

    Steps (case is the oracle):
    1. Select Market Presence 'Other' -> Text field appears
    2. Enter 'Africa and Central Asia' -> Value accepted
    3. Click Next -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146598, 1, 'marketPresenceOther', 'Africa and Central Asia', cru='qfc', extra={'marketPresence': 'other'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Market Presence (Other) blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146599
@pytest.mark.traceability("146599")
@allure.label("pbi", "130718")
@allure.label("testcase", "146599")
@anon()
def test_146599_an_empty_market_presence_other_blocks_progress(page, tmp_path):
    """Verify that an empty Market Presence (Other) blocks progress

    Steps (case is the oracle):
    1. Select 'Other' leaving the text empty -> Text field shown
    2. Observe the text field -> Empty
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_blocked(qp, files, 146599, 1, 'marketPresenceOther', cru='qfc', override={'marketPresence': 'other'}, exclude=('marketPresenceOther',))


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Market Presence (Other) enforces the 150-character limit (150 accepted, 151 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146600
@pytest.mark.traceability("146600")
@allure.label("pbi", "130718")
@allure.label("testcase", "146600")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146600_market_presence_other_enforces_the_150_character_limit_150_a(page, tmp_path):
    """Verify that Market Presence (Other) enforces the 150-character limit (150 accepted, 151 rejected)

    Steps (case is the oracle):
    1. Select 'Other' -> Text field shown
    2. Enter 150 x 'A' and click Next -> 150 accepted
    3. Return and enter 151 x 'A' -> Input capped at 150 or inline error; 151 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146600, 1, 'marketPresenceOther', 150, char='A', cru='qfc', extra={'marketPresence': 'other'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Market Presence (Other) is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146601
@pytest.mark.traceability("146601")
@allure.label("pbi", "130718")
@allure.label("testcase", "146601")
@anon()
def test_146601_a_whitespace_only_market_presence_other_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Market Presence (Other) is rejected as empty

    Steps (case is the oracle):
    1. Select 'Other' -> Text field shown
    2. Enter '   ' -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146601, 1, 'marketPresenceOther', cru='qfc', value='   ', extra={'marketPresence': 'other'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that CR Number accepts the valid value 'CR-1234567'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146602
@pytest.mark.traceability("146602")
@allure.label("pbi", "130718")
@allure.label("testcase", "146602")
@anon()
def test_146602_cr_number_accepts_the_valid_value_cr_1234567(page, tmp_path):
    """Verify that CR Number accepts the valid value 'CR-1234567'

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Enter 'CR-1234567' in CR Number -> Value accepted
    3. Click Next with other fields baseline -> Wizard advances; CR-1234567 stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146602, 1, 'crNumber', 'CR-1234567', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty CR Number blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146603
@pytest.mark.traceability("146603")
@allure.label("pbi", "130718")
@allure.label("testcase", "146603")
@anon()
def test_146603_an_empty_cr_number_blocks_progress(page, tmp_path):
    """Verify that an empty CR Number blocks progress

    Steps (case is the oracle):
    1. Select MOCI leaving CR Number empty -> MOCI block shown
    2. Fill other fields with baseline -> Others accepted
    3. Click Next -> Inline required error under CR Number; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146603, 1, 'crNumber', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that CR Number enforces the 50-character limit (50 accepted, 51 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146604
@pytest.mark.traceability("146604")
@allure.label("pbi", "130718")
@allure.label("testcase", "146604")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146604_cr_number_enforces_the_50_character_limit_50_accepted_51_rej(page, tmp_path):
    """Verify that CR Number enforces the 50-character limit (50 accepted, 51 rejected)

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Enter 50 x 'A' and click Next -> 50 accepted
    3. Return and enter 51 x 'A' -> Input capped at 50 or inline error; 51 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146604, 1, 'crNumber', 50, char='A', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only CR Number is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146605
@pytest.mark.traceability("146605")
@allure.label("pbi", "130718")
@allure.label("testcase", "146605")
@anon()
def test_146605_a_whitespace_only_cr_number_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only CR Number is rejected as empty

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Enter '   ' in CR Number -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146605, 1, 'crNumber', cru='moci', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Upload CR Copy accepts 'cr-copy.pdf' (1.2 MB)")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146606
@pytest.mark.traceability("146606")
@allure.label("pbi", "130718")
@allure.label("testcase", "146606")
@anon()
def test_146606_upload_cr_copy_accepts_cr_copy_pdf_1_2_mb(page, tmp_path):
    """Verify that Upload CR Copy accepts 'cr-copy.pdf' (1.2 MB)

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Upload cr-copy.pdf (1.2 MB) in Upload CR Copy -> File name shown as attached with no error
    3. Click Next with other fields baseline -> Wizard advances; file stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146606, 1, 'uploadCrCopy', files.make('cr-copy.pdf', 1.2 * MB), cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that a missing CR Copy blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146607
@pytest.mark.traceability("146607")
@allure.label("pbi", "130718")
@allure.label("testcase", "146607")
@anon()
def test_146607_a_missing_cr_copy_blocks_progress(page, tmp_path):
    """Verify that a missing CR Copy blocks progress

    Steps (case is the oracle):
    1. Select MOCI and attach no CR copy -> MOCI block shown
    2. Fill others with baseline -> No file attached
    3. Click Next -> Inline required error under Upload CR Copy; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146607, 1, 'uploadCrCopy', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that Upload CR Copy rejects an unsupported type 'cr-copy.png'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146608
@pytest.mark.traceability("146608")
@allure.label("pbi", "130718")
@allure.label("testcase", "146608")
@anon()
def test_146608_upload_cr_copy_rejects_an_unsupported_type_cr_copy_png(page, tmp_path):
    """Verify that Upload CR Copy rejects an unsupported type 'cr-copy.png'

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Upload cr-copy.png in Upload CR Copy -> Inline file-type error shown; file not attached
    3. Click Next -> Next blocked while the field has no valid file
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_type_rejected(qp, files, 146608, 1, 'uploadCrCopy', 'cr-copy.png', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Upload CR Copy enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146609
@pytest.mark.traceability("146609")
@allure.label("pbi", "130718")
@allure.label("testcase", "146609")
@anon()
def test_146609_upload_cr_copy_enforces_the_5_mb_limit_4_99_mb_accepted_5_01(page, tmp_path):
    """Verify that Upload CR Copy enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Upload cr-4_99mb.pdf (4.99 MB) -> 4.99 MB accepted with no error
    3. Replace it with cr-5_01mb.pdf (5.01 MB) -> 5.01 MB rejected with inline size error; not attached
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_size(qp, files, 146609, 1, 'uploadCrCopy', 'cr-4_99mb.pdf', 'cr-5_01mb.pdf', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Qatar Chamber Membership Number accepts 'QCM-7654321'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146610
@pytest.mark.traceability("146610")
@allure.label("pbi", "130718")
@allure.label("testcase", "146610")
@anon()
def test_146610_qatar_chamber_membership_number_accepts_qcm_7654321(page, tmp_path):
    """Verify that Qatar Chamber Membership Number accepts 'QCM-7654321'

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Enter 'QCM-7654321' in Qatar Chamber Membership Number -> Value accepted
    3. Click Next with others baseline -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146610, 1, 'qatarChamberMembershipNumber', 'QCM-7654321', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Qatar Chamber Membership Number blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146611
@pytest.mark.traceability("146611")
@allure.label("pbi", "130718")
@allure.label("testcase", "146611")
@anon()
def test_146611_an_empty_qatar_chamber_membership_number_blocks_progress(page, tmp_path):
    """Verify that an empty Qatar Chamber Membership Number blocks progress

    Steps (case is the oracle):
    1. Select MOCI leaving Qatar Chamber Membership Number empty -> MOCI block shown
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146611, 1, 'qatarChamberMembershipNumber', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Qatar Chamber Membership Number enforces the 50-character limit (50 accepted, 51 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146612
@pytest.mark.traceability("146612")
@allure.label("pbi", "130718")
@allure.label("testcase", "146612")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146612_qatar_chamber_membership_number_enforces_the_50_character_li(page, tmp_path):
    """Verify that Qatar Chamber Membership Number enforces the 50-character limit (50 accepted, 51 rejected)

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Enter 50 x 'A' and click Next -> 50 accepted
    3. Return and enter 51 x 'A' -> Input capped at 50 or inline error; 51 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146612, 1, 'qatarChamberMembershipNumber', 50, char='A', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Qatar Chamber Membership Number is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146613
@pytest.mark.traceability("146613")
@allure.label("pbi", "130718")
@allure.label("testcase", "146613")
@anon()
def test_146613_a_whitespace_only_qatar_chamber_membership_number_is_rejecte(page, tmp_path):
    """Verify that a whitespace-only Qatar Chamber Membership Number is rejected as empty

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Enter '   ' -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146613, 1, 'qatarChamberMembershipNumber', cru='moci', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Upload Qatar Chamber Membership Copy accepts 'qcm-copy.pdf' (1 MB)")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146614
@pytest.mark.traceability("146614")
@allure.label("pbi", "130718")
@allure.label("testcase", "146614")
@anon()
def test_146614_upload_qatar_chamber_membership_copy_accepts_qcm_copy_pdf_1(page, tmp_path):
    """Verify that Upload Qatar Chamber Membership Copy accepts 'qcm-copy.pdf' (1 MB)

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Upload qcm-copy.pdf (1 MB) -> File attached, no error
    3. Click Next with others baseline -> Wizard advances; file stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146614, 1, 'uploadQatarChamberMembershipCopy', files.make('qcm-copy.pdf', 1 * MB), cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that a missing Qatar Chamber Membership Copy blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146615
@pytest.mark.traceability("146615")
@allure.label("pbi", "130718")
@allure.label("testcase", "146615")
@anon()
def test_146615_a_missing_qatar_chamber_membership_copy_blocks_progress(page, tmp_path):
    """Verify that a missing Qatar Chamber Membership Copy blocks progress

    Steps (case is the oracle):
    1. Select MOCI attaching no membership copy -> MOCI block shown
    2. Fill others with baseline -> No file
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146615, 1, 'uploadQatarChamberMembershipCopy', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that Upload Qatar Chamber Membership Copy rejects an unsupported type 'qcm-copy.png'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146616
@pytest.mark.traceability("146616")
@allure.label("pbi", "130718")
@allure.label("testcase", "146616")
@anon()
def test_146616_upload_qatar_chamber_membership_copy_rejects_an_unsupported(page, tmp_path):
    """Verify that Upload Qatar Chamber Membership Copy rejects an unsupported type 'qcm-copy.png'

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Upload qcm-copy.png -> Inline file-type error; file not attached
    3. Click Next -> Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_type_rejected(qp, files, 146616, 1, 'uploadQatarChamberMembershipCopy', 'qcm-copy.png', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Upload Qatar Chamber Membership Copy enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146617
@pytest.mark.traceability("146617")
@allure.label("pbi", "130718")
@allure.label("testcase", "146617")
@anon()
def test_146617_upload_qatar_chamber_membership_copy_enforces_the_5_mb_limit(page, tmp_path):
    """Verify that Upload Qatar Chamber Membership Copy enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Upload qcm-4_99mb.pdf (4.99 MB) -> 4.99 MB accepted
    3. Replace with qcm-5_01mb.pdf (5.01 MB) -> 5.01 MB rejected with inline size error
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_size(qp, files, 146617, 1, 'uploadQatarChamberMembershipCopy', 'qcm-4_99mb.pdf', 'qcm-5_01mb.pdf', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Verified on Qatar Commercial Directory? accepts the selection 'Yes'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146618
@pytest.mark.traceability("146618")
@allure.label("pbi", "130718")
@allure.label("testcase", "146618")
@anon()
def test_146618_verified_on_qatar_commercial_directory_accepts_the_selection(page, tmp_path):
    """Verify that Verified on Qatar Commercial Directory? accepts the selection 'Yes'

    Steps (case is the oracle):
    1. Select MOCI -> MOCI block shown
    2. Choose 'Yes' in Verified on Qatar Commercial Directory? -> 'Yes' selected
    3. Click Next with others baseline -> Wizard advances; 'Yes' stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146618, 1, 'verifiedOnQatarCommercialDirectory', 'yes', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that leaving Verified on Qatar Commercial Directory? unselected blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146619
@pytest.mark.traceability("146619")
@allure.label("pbi", "130718")
@allure.label("testcase", "146619")
@anon()
def test_146619_leaving_verified_on_qatar_commercial_directory_unselected_bl(page, tmp_path):
    """Verify that leaving Verified on Qatar Commercial Directory? unselected blocks progress

    Steps (case is the oracle):
    1. Select MOCI leaving the control untouched -> MOCI block shown
    2. Fill others with baseline -> No value selected
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146619, 1, 'verifiedOnQatarCommercialDirectory', cru='moci')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that QFC Number accepts 'QFC-00123'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146620
@pytest.mark.traceability("146620")
@allure.label("pbi", "130718")
@allure.label("testcase", "146620")
@anon()
def test_146620_qfc_number_accepts_qfc_00123(page, tmp_path):
    """Verify that QFC Number accepts 'QFC-00123'

    Steps (case is the oracle):
    1. Select QFC -> QFC block shown
    2. Enter 'QFC-00123' -> Value accepted
    3. Click Next with others baseline -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146620, 1, 'qfcNumber', 'QFC-00123', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty QFC Number blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146621
@pytest.mark.traceability("146621")
@allure.label("pbi", "130718")
@allure.label("testcase", "146621")
@anon()
def test_146621_an_empty_qfc_number_blocks_progress(page, tmp_path):
    """Verify that an empty QFC Number blocks progress

    Steps (case is the oracle):
    1. Select QFC leaving QFC Number empty -> QFC block shown
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146621, 1, 'qfcNumber', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that QFC Number enforces the 50-character limit (50 accepted, 51 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146622
@pytest.mark.traceability("146622")
@allure.label("pbi", "130718")
@allure.label("testcase", "146622")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146622_qfc_number_enforces_the_50_character_limit_50_accepted_51_re(page, tmp_path):
    """Verify that QFC Number enforces the 50-character limit (50 accepted, 51 rejected)

    Steps (case is the oracle):
    1. Select QFC -> QFC block shown
    2. Enter 50 x 'A' and click Next -> 50 accepted
    3. Return and enter 51 x 'A' -> Input capped at 50 or inline error; 51 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146622, 1, 'qfcNumber', 50, char='A', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only QFC Number is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146623
@pytest.mark.traceability("146623")
@allure.label("pbi", "130718")
@allure.label("testcase", "146623")
@anon()
def test_146623_a_whitespace_only_qfc_number_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only QFC Number is rejected as empty

    Steps (case is the oracle):
    1. Select QFC -> QFC block shown
    2. Enter '   ' -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146623, 1, 'qfcNumber', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that QFC Membership Copy accepts 'qfc-membership.pdf' (1 MB)")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146624
@pytest.mark.traceability("146624")
@allure.label("pbi", "130718")
@allure.label("testcase", "146624")
@anon()
def test_146624_qfc_membership_copy_accepts_qfc_membership_pdf_1_mb(page, tmp_path):
    """Verify that QFC Membership Copy accepts 'qfc-membership.pdf' (1 MB)

    Steps (case is the oracle):
    1. Select QFC -> QFC block shown
    2. Upload qfc-membership.pdf (1 MB) -> File attached, no error
    3. Click Next with others baseline -> Wizard advances; file stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146624, 1, 'qfcMembershipCopy', files.make('qfc-membership.pdf', 1 * MB), cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that a missing QFC Membership Copy blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146625
@pytest.mark.traceability("146625")
@allure.label("pbi", "130718")
@allure.label("testcase", "146625")
@anon()
def test_146625_a_missing_qfc_membership_copy_blocks_progress(page, tmp_path):
    """Verify that a missing QFC Membership Copy blocks progress

    Steps (case is the oracle):
    1. Select QFC attaching no copy -> QFC block shown
    2. Fill others with baseline -> No file
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146625, 1, 'qfcMembershipCopy', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that QFC Membership Copy rejects an unsupported type 'qfc-membership.png'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146626
@pytest.mark.traceability("146626")
@allure.label("pbi", "130718")
@allure.label("testcase", "146626")
@anon()
def test_146626_qfc_membership_copy_rejects_an_unsupported_type_qfc_membersh(page, tmp_path):
    """Verify that QFC Membership Copy rejects an unsupported type 'qfc-membership.png'

    Steps (case is the oracle):
    1. Select QFC -> QFC block shown
    2. Upload qfc-membership.png -> Inline file-type error; file not attached
    3. Click Next -> Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_type_rejected(qp, files, 146626, 1, 'qfcMembershipCopy', 'qfc-membership.png', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that QFC Membership Copy enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146627
@pytest.mark.traceability("146627")
@allure.label("pbi", "130718")
@allure.label("testcase", "146627")
@anon()
def test_146627_qfc_membership_copy_enforces_the_5_mb_limit_4_99_mb_accepted(page, tmp_path):
    """Verify that QFC Membership Copy enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)

    Steps (case is the oracle):
    1. Select QFC -> QFC block shown
    2. Upload qfc-4_99mb.pdf (4.99 MB) -> 4.99 MB accepted
    3. Replace with qfc-5_01mb.pdf (5.01 MB) -> 5.01 MB rejected with inline size error
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_size(qp, files, 146627, 1, 'qfcMembershipCopy', 'qfc-4_99mb.pdf', 'qfc-5_01mb.pdf', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that QFZ Number accepts 'QFZ-00456'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146628
@pytest.mark.traceability("146628")
@allure.label("pbi", "130718")
@allure.label("testcase", "146628")
@anon()
def test_146628_qfz_number_accepts_qfz_00456(page, tmp_path):
    """Verify that QFZ Number accepts 'QFZ-00456'

    Steps (case is the oracle):
    1. Select QFZ -> QFZ block shown
    2. Enter 'QFZ-00456' -> Value accepted
    3. Click Next with others baseline -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146628, 1, 'qfzNumber', 'QFZ-00456', cru='qfz')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty QFZ Number blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146629
@pytest.mark.traceability("146629")
@allure.label("pbi", "130718")
@allure.label("testcase", "146629")
@anon()
def test_146629_an_empty_qfz_number_blocks_progress(page, tmp_path):
    """Verify that an empty QFZ Number blocks progress

    Steps (case is the oracle):
    1. Select QFZ leaving QFZ Number empty -> QFZ block shown
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146629, 1, 'qfzNumber', cru='qfz')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that QFZ Number enforces the 50-character limit (50 accepted, 51 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146630
@pytest.mark.traceability("146630")
@allure.label("pbi", "130718")
@allure.label("testcase", "146630")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146630_qfz_number_enforces_the_50_character_limit_50_accepted_51_re(page, tmp_path):
    """Verify that QFZ Number enforces the 50-character limit (50 accepted, 51 rejected)

    Steps (case is the oracle):
    1. Select QFZ -> QFZ block shown
    2. Enter 50 x 'A' and click Next -> 50 accepted
    3. Return and enter 51 x 'A' -> Input capped at 50 or inline error; 51 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146630, 1, 'qfzNumber', 50, char='A', cru='qfz')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only QFZ Number is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146631
@pytest.mark.traceability("146631")
@allure.label("pbi", "130718")
@allure.label("testcase", "146631")
@anon()
def test_146631_a_whitespace_only_qfz_number_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only QFZ Number is rejected as empty

    Steps (case is the oracle):
    1. Select QFZ -> QFZ block shown
    2. Enter '   ' -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146631, 1, 'qfzNumber', cru='qfz', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that QFZ Membership Copy accepts 'qfz-membership.pdf' (1 MB)")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146632
@pytest.mark.traceability("146632")
@allure.label("pbi", "130718")
@allure.label("testcase", "146632")
@anon()
def test_146632_qfz_membership_copy_accepts_qfz_membership_pdf_1_mb(page, tmp_path):
    """Verify that QFZ Membership Copy accepts 'qfz-membership.pdf' (1 MB)

    Steps (case is the oracle):
    1. Select QFZ -> QFZ block shown
    2. Upload qfz-membership.pdf (1 MB) -> File attached, no error
    3. Click Next with others baseline -> Wizard advances; file stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146632, 1, 'qfzMembershipCopy', files.make('qfz-membership.pdf', 1 * MB), cru='qfz')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that a missing QFZ Membership Copy blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146633
@pytest.mark.traceability("146633")
@allure.label("pbi", "130718")
@allure.label("testcase", "146633")
@anon()
def test_146633_a_missing_qfz_membership_copy_blocks_progress(page, tmp_path):
    """Verify that a missing QFZ Membership Copy blocks progress

    Steps (case is the oracle):
    1. Select QFZ attaching no copy -> QFZ block shown
    2. Fill others with baseline -> No file
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146633, 1, 'qfzMembershipCopy', cru='qfz')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that QFZ Membership Copy rejects an unsupported type 'qfz-membership.png'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146634
@pytest.mark.traceability("146634")
@allure.label("pbi", "130718")
@allure.label("testcase", "146634")
@anon()
def test_146634_qfz_membership_copy_rejects_an_unsupported_type_qfz_membersh(page, tmp_path):
    """Verify that QFZ Membership Copy rejects an unsupported type 'qfz-membership.png'

    Steps (case is the oracle):
    1. Select QFZ -> QFZ block shown
    2. Upload qfz-membership.png -> Inline file-type error; file not attached
    3. Click Next -> Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_type_rejected(qp, files, 146634, 1, 'qfzMembershipCopy', 'qfz-membership.png', cru='qfz')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that QFZ Membership Copy enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146635
@pytest.mark.traceability("146635")
@allure.label("pbi", "130718")
@allure.label("testcase", "146635")
@anon()
def test_146635_qfz_membership_copy_enforces_the_5_mb_limit_4_99_mb_accepted(page, tmp_path):
    """Verify that QFZ Membership Copy enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)

    Steps (case is the oracle):
    1. Select QFZ -> QFZ block shown
    2. Upload qfz-4_99mb.pdf (4.99 MB) -> 4.99 MB accepted
    3. Replace with qfz-5_01mb.pdf (5.01 MB) -> 5.01 MB rejected with inline size error
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_size(qp, files, 146635, 1, 'qfzMembershipCopy', 'qfz-4_99mb.pdf', 'qfz-5_01mb.pdf', cru='qfz')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Company Registered Under (Other) accepts 'Dubai Multi Commodities Centre'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146636
@pytest.mark.traceability("146636")
@allure.label("pbi", "130718")
@allure.label("testcase", "146636")
@anon()
def test_146636_company_registered_under_other_accepts_dubai_multi_commoditi(page, tmp_path):
    """Verify that Company Registered Under (Other) accepts 'Dubai Multi Commodities Centre'

    Steps (case is the oracle):
    1. Select Other -> Other block shown
    2. Enter 'Dubai Multi Commodities Centre' -> Value accepted
    3. Click Next with others baseline -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146636, 1, 'companyRegisteredUnderOther', 'Dubai Multi Commodities Centre', cru='other')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Company Registered Under (Other) blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146637
@pytest.mark.traceability("146637")
@allure.label("pbi", "130718")
@allure.label("testcase", "146637")
@anon()
def test_146637_an_empty_company_registered_under_other_blocks_progress(page, tmp_path):
    """Verify that an empty Company Registered Under (Other) blocks progress

    Steps (case is the oracle):
    1. Select Other leaving the authority name empty -> Other block shown
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146637, 1, 'companyRegisteredUnderOther', cru='other')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Company Registered Under (Other) enforces the 100-character limit (100 accepted, 101 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146638
@pytest.mark.traceability("146638")
@allure.label("pbi", "130718")
@allure.label("testcase", "146638")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146638_company_registered_under_other_enforces_the_100_character_li(page, tmp_path):
    """Verify that Company Registered Under (Other) enforces the 100-character limit (100 accepted, 101 rejected)

    Steps (case is the oracle):
    1. Select Other -> Other block shown
    2. Enter 100 x 'A' and click Next -> 100 accepted
    3. Return and enter 101 x 'A' -> Input capped at 100 or inline error; 101 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146638, 1, 'companyRegisteredUnderOther', 100, char='A', cru='other')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Company Registered Under (Other) is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146639
@pytest.mark.traceability("146639")
@allure.label("pbi", "130718")
@allure.label("testcase", "146639")
@anon()
def test_146639_a_whitespace_only_company_registered_under_other_is_rejected(page, tmp_path):
    """Verify that a whitespace-only Company Registered Under (Other) is rejected as empty

    Steps (case is the oracle):
    1. Select Other -> Other block shown
    2. Enter '   ' -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146639, 1, 'companyRegisteredUnderOther', cru='other', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Other Membership Copy accepts 'other-authority.pdf' (1 MB)")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146640
@pytest.mark.traceability("146640")
@allure.label("pbi", "130718")
@allure.label("testcase", "146640")
@anon()
def test_146640_other_membership_copy_accepts_other_authority_pdf_1_mb(page, tmp_path):
    """Verify that the Other Membership Copy accepts 'other-authority.pdf' (1 MB)

    Steps (case is the oracle):
    1. Select Other -> Other block shown
    2. Upload other-authority.pdf (1 MB) -> File attached, no error
    3. Click Next with others baseline -> Wizard advances; file stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146640, 1, 'companyRegisteredUnderOtherMembershipCopy', files.make('other-authority.pdf', 1 * MB), cru='other')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that a missing Other Membership Copy blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146641
@pytest.mark.traceability("146641")
@allure.label("pbi", "130718")
@allure.label("testcase", "146641")
@anon()
def test_146641_a_missing_other_membership_copy_blocks_progress(page, tmp_path):
    """Verify that a missing Other Membership Copy blocks progress

    Steps (case is the oracle):
    1. Select Other attaching no copy -> Other block shown
    2. Fill others with baseline -> No file
    3. Click Next -> Inline required error; stays on Step 1
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146641, 1, 'companyRegisteredUnderOtherMembershipCopy', cru='other')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the Other Membership Copy rejects an unsupported type 'other-authority.png'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146642
@pytest.mark.traceability("146642")
@allure.label("pbi", "130718")
@allure.label("testcase", "146642")
@anon()
def test_146642_other_membership_copy_rejects_an_unsupported_type_other_auth(page, tmp_path):
    """Verify that the Other Membership Copy rejects an unsupported type 'other-authority.png'

    Steps (case is the oracle):
    1. Select Other -> Other block shown
    2. Upload other-authority.png -> Inline file-type error; file not attached
    3. Click Next -> Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_type_rejected(qp, files, 146642, 1, 'companyRegisteredUnderOtherMembershipCopy', 'other-authority.png', cru='other')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the Other Membership Copy enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146643
@pytest.mark.traceability("146643")
@allure.label("pbi", "130718")
@allure.label("testcase", "146643")
@anon()
def test_146643_other_membership_copy_enforces_the_5_mb_limit_4_99_mb_accept(page, tmp_path):
    """Verify that the Other Membership Copy enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)

    Steps (case is the oracle):
    1. Select Other -> Other block shown
    2. Upload other-4_99mb.pdf (4.99 MB) -> 4.99 MB accepted
    3. Replace with other-5_01mb.pdf (5.01 MB) -> 5.01 MB rejected with inline size error
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_size(qp, files, 146643, 1, 'companyRegisteredUnderOtherMembershipCopy', 'other-4_99mb.pdf', 'other-5_01mb.pdf', cru='other')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that selecting MOCI reveals exactly the 5 MOCI fields, each required')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146644
@pytest.mark.traceability("146644")
@allure.label("pbi", "130718")
@allure.label("testcase", "146644")
@anon()
def test_146644_selecting_moci_reveals_exactly_the_5_moci_fields_each_requir(page, tmp_path):
    """Verify that selecting MOCI reveals exactly the 5 MOCI fields, each required

    Steps (case is the oracle):
    1. Open Step 1 and select MOCI -> Fields appear immediately below with no page reload
    2. Count and read the fields revealed below the dropdown -> Exactly 5: CR Number, Upload CR Copy,
       Qatar Chamber Membership Number, Upload Qatar Chamber Membership Copy, Verified on Qatar
       Commercial Directory?, each with required marker
    3. Click Next leaving them empty -> Next blocked with inline required errors on all 5
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    before = set(qp.visible_field_names(1))
    with allure.step("Select MOCI: fields appear immediately with no page reload"):
        url = qp.page.url
        qp.select("companyRegisteredUnder", value='moci')
        assert qp.page.url == url
    with allure.step("Read the fields revealed below the dropdown"):
        revealed = [n for n in qp.visible_field_names(1) if n not in before]
        assert revealed == ['crNumber', 'uploadCrCopy', 'qatarChamberMembershipNumber', 'uploadQatarChamberMembershipCopy', 'verifiedOnQatarCommercialDirectory'], f"revealed fields: {revealed}"
        assert [qp.label_text(n) for n in revealed] == ['CR Number', 'Upload CR Copy', 'Qatar Chamber Membership Number', 'Upload Qatar Chamber Membership Copy', 'Verified on Qatar Commercial Directory?']
        for n in revealed:
            assert qp.has_required_marker(n), f"{n} has no required marker"
        for g in ['qfc', 'qfz', 'other']:
            assert not qp.is_shown(qp.COND_GROUP_N.format(group=g)), f"{g} block visible while MOCI selected"
    with allure.step("Click Next leaving them empty: blocked with inline required errors on each"):
        qp.click_next()
        assert qp.current_step() == 1
        for n in ['crNumber', 'uploadCrCopy', 'qatarChamberMembershipNumber', 'uploadQatarChamberMembershipCopy', 'verifiedOnQatarCommercialDirectory']:
            assert qp.has_field_error(n), f"no inline required error on {n}"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that selecting QFC reveals exactly the 2 QFC fields, each required')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146645
@pytest.mark.traceability("146645")
@allure.label("pbi", "130718")
@allure.label("testcase", "146645")
@anon()
def test_146645_selecting_qfc_reveals_exactly_the_2_qfc_fields_each_required(page, tmp_path):
    """Verify that selecting QFC reveals exactly the 2 QFC fields, each required

    Steps (case is the oracle):
    1. Select QFC -> Fields appear immediately
    2. Read the revealed fields -> Exactly 2: QFC Number, QFC Membership Copy, each required-marked; no
       MOCI fields visible
    3. Click Next leaving them empty -> Next blocked with inline required errors on both
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    before = set(qp.visible_field_names(1))
    with allure.step("Select QFC: fields appear immediately with no page reload"):
        url = qp.page.url
        qp.select("companyRegisteredUnder", value='qfc')
        assert qp.page.url == url
    with allure.step("Read the fields revealed below the dropdown"):
        revealed = [n for n in qp.visible_field_names(1) if n not in before]
        assert revealed == ['qfcNumber', 'qfcMembershipCopy'], f"revealed fields: {revealed}"
        assert [qp.label_text(n) for n in revealed] == ['QFC Number', 'QFC Membership Copy']
        for n in revealed:
            assert qp.has_required_marker(n), f"{n} has no required marker"
        for g in ['moci', 'qfz', 'other']:
            assert not qp.is_shown(qp.COND_GROUP_N.format(group=g)), f"{g} block visible while QFC selected"
    with allure.step("Click Next leaving them empty: blocked with inline required errors on each"):
        qp.click_next()
        assert qp.current_step() == 1
        for n in ['qfcNumber', 'qfcMembershipCopy']:
            assert qp.has_field_error(n), f"no inline required error on {n}"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that selecting QFZ reveals exactly the 2 QFZ fields, each required')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146646
@pytest.mark.traceability("146646")
@allure.label("pbi", "130718")
@allure.label("testcase", "146646")
@anon()
def test_146646_selecting_qfz_reveals_exactly_the_2_qfz_fields_each_required(page, tmp_path):
    """Verify that selecting QFZ reveals exactly the 2 QFZ fields, each required

    Steps (case is the oracle):
    1. Select QFZ -> Fields appear immediately
    2. Read the revealed fields -> Exactly 2: QFZ Number, QFZ Membership Copy, each required-marked
    3. Click Next leaving them empty -> Next blocked with inline required errors on both
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    before = set(qp.visible_field_names(1))
    with allure.step("Select QFZ: fields appear immediately with no page reload"):
        url = qp.page.url
        qp.select("companyRegisteredUnder", value='qfz')
        assert qp.page.url == url
    with allure.step("Read the fields revealed below the dropdown"):
        revealed = [n for n in qp.visible_field_names(1) if n not in before]
        assert revealed == ['qfzNumber', 'qfzMembershipCopy'], f"revealed fields: {revealed}"
        assert [qp.label_text(n) for n in revealed] == ['QFZ Number', 'QFZ Membership Copy']
        for n in revealed:
            assert qp.has_required_marker(n), f"{n} has no required marker"
        for g in ['moci', 'qfc', 'other']:
            assert not qp.is_shown(qp.COND_GROUP_N.format(group=g)), f"{g} block visible while QFZ selected"
    with allure.step("Click Next leaving them empty: blocked with inline required errors on each"):
        qp.click_next()
        assert qp.current_step() == 1
        for n in ['qfzNumber', 'qfzMembershipCopy']:
            assert qp.has_field_error(n), f"no inline required error on {n}"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that selecting Other reveals exactly the 2 Other fields, each required')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146647
@pytest.mark.traceability("146647")
@allure.label("pbi", "130718")
@allure.label("testcase", "146647")
@anon()
def test_146647_selecting_other_reveals_exactly_the_2_other_fields_each_requ(page, tmp_path):
    """Verify that selecting Other reveals exactly the 2 Other fields, each required

    Steps (case is the oracle):
    1. Select Other -> Fields appear immediately
    2. Read the revealed fields -> Exactly 2: Company Registered Under (Other) and Company Registered
       Under (Other) Membership Copy, each required-marked
    3. Click Next leaving them empty -> Next blocked with inline required errors on both
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    before = set(qp.visible_field_names(1))
    with allure.step("Select OTHER: fields appear immediately with no page reload"):
        url = qp.page.url
        qp.select("companyRegisteredUnder", value='other')
        assert qp.page.url == url
    with allure.step("Read the fields revealed below the dropdown"):
        revealed = [n for n in qp.visible_field_names(1) if n not in before]
        assert revealed == ['companyRegisteredUnderOther', 'companyRegisteredUnderOtherMembershipCopy'], f"revealed fields: {revealed}"
        assert [qp.label_text(n) for n in revealed] == ['Company Registered Under (Other)', 'Company Registered Under (Other) Membership Copy']
        for n in revealed:
            assert qp.has_required_marker(n), f"{n} has no required marker"
        for g in ['moci', 'qfc', 'qfz']:
            assert not qp.is_shown(qp.COND_GROUP_N.format(group=g)), f"{g} block visible while OTHER selected"
    with allure.step("Click Next leaving them empty: blocked with inline required errors on each"):
        qp.click_next()
        assert qp.current_step() == 1
        for n in ['companyRegisteredUnderOther', 'companyRegisteredUnderOtherMembershipCopy']:
            assert qp.has_field_error(n), f"no inline required error on {n}"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Company Size = Other reveals the required count field')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146648
@pytest.mark.traceability("146648")
@allure.label("pbi", "130718")
@allure.label("testcase", "146648")
@anon()
def test_146648_company_size_other_reveals_the_required_count_field(page, tmp_path):
    """Verify that Company Size = Other reveals the required count field

    Steps (case is the oracle):
    1. Select Company Size 'Other' -> Count field (max 10) appears and is required-marked
    2. Observe the form -> Field visible under/in the Other card
    3. Switch to 'Small' -> Count field hides and is no longer required
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    with allure.step("Select other: companySizeOther appears, required-marked"):
        qp.click(qp.RADIO_CARD.format(name='companySize', value='other'))
        assert qp.is_field_visible('companySizeOther'), "companySizeOther did not appear"
        assert qp.has_required_marker('companySizeOther'), "companySizeOther has no required marker"
        assert qp.is_control_required('companySizeOther'), "companySizeOther is not required"
    with allure.step("Only that conditional field is revealed"):
        for other in []:
            assert not qp.is_field_visible(other), f"{other} is also visible"
    with allure.step("Switch to small: the field hides and is no longer required"):
        qp.click(qp.RADIO_CARD.format(name='companySize', value='small'))
        assert not qp.is_field_visible('companySizeOther'), "companySizeOther still visible"
        assert not qp.is_control_required('companySizeOther'), "companySizeOther still required"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Company Type = Other reveals the required text field')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146649
@pytest.mark.traceability("146649")
@allure.label("pbi", "130718")
@allure.label("testcase", "146649")
@anon()
def test_146649_company_type_other_reveals_the_required_text_field(page, tmp_path):
    """Verify that Company Type = Other reveals the required text field

    Steps (case is the oracle):
    1. Select Company Type 'Other' -> Text field (max 100) appears required-marked
    2. Observe the form -> Field visible below the dropdown
    3. Switch to 'LLC' -> Field hides and is no longer required
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    with allure.step("Select Other: companyTypeOther appears, required-marked"):
        qp.select('companyType', label='Other')
        assert qp.is_field_visible('companyTypeOther'), "companyTypeOther did not appear"
        assert qp.has_required_marker('companyTypeOther'), "companyTypeOther has no required marker"
        assert qp.is_control_required('companyTypeOther'), "companyTypeOther is not required"
    with allure.step("Only that conditional field is revealed"):
        for other in []:
            assert not qp.is_field_visible(other), f"{other} is also visible"
    with allure.step("Switch to LLC: the field hides and is no longer required"):
        qp.select('companyType', label='LLC')
        assert not qp.is_field_visible('companyTypeOther'), "companyTypeOther still visible"
        assert not qp.is_control_required('companyTypeOther'), "companyTypeOther still required"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Market Presence = Regional reveals the required Regional Markets text area')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146650
@pytest.mark.traceability("146650")
@allure.label("pbi", "130718")
@allure.label("testcase", "146650")
@anon()
def test_146650_market_presence_regional_reveals_the_required_regional_marke(page, tmp_path):
    """Verify that Market Presence = Regional reveals the required Regional Markets text area

    Steps (case is the oracle):
    1. Select Market Presence 'Regional' -> Regional Markets text area appears required-marked
    2. Observe the form -> Only that field revealed (no International/Other field)
    3. Switch to 'Local' -> Text area hides and is no longer required
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    with allure.step("Select regional: regionalMarkets appears, required-marked"):
        qp.click(qp.RADIO_CARD.format(name='marketPresence', value='regional'))
        assert qp.is_field_visible('regionalMarkets'), "regionalMarkets did not appear"
        assert qp.has_required_marker('regionalMarkets'), "regionalMarkets has no required marker"
        assert qp.is_control_required('regionalMarkets'), "regionalMarkets is not required"
    with allure.step("Only that conditional field is revealed"):
        for other in ['internationalMarkets', 'marketPresenceOther']:
            assert not qp.is_field_visible(other), f"{other} is also visible"
    with allure.step("Switch to local: the field hides and is no longer required"):
        qp.click(qp.RADIO_CARD.format(name='marketPresence', value='local'))
        assert not qp.is_field_visible('regionalMarkets'), "regionalMarkets still visible"
        assert not qp.is_control_required('regionalMarkets'), "regionalMarkets still required"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Market Presence = International reveals the required International Markets text area')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146651
@pytest.mark.traceability("146651")
@allure.label("pbi", "130718")
@allure.label("testcase", "146651")
@anon()
def test_146651_market_presence_international_reveals_the_required_internati(page, tmp_path):
    """Verify that Market Presence = International reveals the required International Markets text area

    Steps (case is the oracle):
    1. Select Market Presence 'International' -> International Markets text area appears required-marked
    2. Observe the form -> Only that field revealed
    3. Switch to 'Local' -> Text area hides and is no longer required
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    with allure.step("Select international: internationalMarkets appears, required-marked"):
        qp.click(qp.RADIO_CARD.format(name='marketPresence', value='international'))
        assert qp.is_field_visible('internationalMarkets'), "internationalMarkets did not appear"
        assert qp.has_required_marker('internationalMarkets'), "internationalMarkets has no required marker"
        assert qp.is_control_required('internationalMarkets'), "internationalMarkets is not required"
    with allure.step("Only that conditional field is revealed"):
        for other in ['regionalMarkets', 'marketPresenceOther']:
            assert not qp.is_field_visible(other), f"{other} is also visible"
    with allure.step("Switch to local: the field hides and is no longer required"):
        qp.click(qp.RADIO_CARD.format(name='marketPresence', value='local'))
        assert not qp.is_field_visible('internationalMarkets'), "internationalMarkets still visible"
        assert not qp.is_control_required('internationalMarkets'), "internationalMarkets still required"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Market Presence = Other reveals the required Market Presence (Other) field')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146652
@pytest.mark.traceability("146652")
@allure.label("pbi", "130718")
@allure.label("testcase", "146652")
@anon()
def test_146652_market_presence_other_reveals_the_required_market_presence_o(page, tmp_path):
    """Verify that Market Presence = Other reveals the required Market Presence (Other) field

    Steps (case is the oracle):
    1. Select Market Presence 'Other' -> Text field (max 150) appears required-marked
    2. Observe the form -> Only that field revealed
    3. Switch to 'Local' -> Field hides and is no longer required
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    with allure.step("Select other: marketPresenceOther appears, required-marked"):
        qp.click(qp.RADIO_CARD.format(name='marketPresence', value='other'))
        assert qp.is_field_visible('marketPresenceOther'), "marketPresenceOther did not appear"
        assert qp.has_required_marker('marketPresenceOther'), "marketPresenceOther has no required marker"
        assert qp.is_control_required('marketPresenceOther'), "marketPresenceOther is not required"
    with allure.step("Only that conditional field is revealed"):
        for other in ['regionalMarkets', 'internationalMarkets']:
            assert not qp.is_field_visible(other), f"{other} is also visible"
    with allure.step("Switch to local: the field hides and is no longer required"):
        qp.click(qp.RADIO_CARD.format(name='marketPresence', value='local'))
        assert not qp.is_field_visible('marketPresenceOther'), "marketPresenceOther still visible"
        assert not qp.is_control_required('marketPresenceOther'), "marketPresenceOther still required"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that changing Company Registered Under clears and un-requires the previous selection's fields")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146653
@pytest.mark.traceability("146653")
@allure.label("pbi", "130718")
@allure.label("testcase", "146653")
@anon()
def test_146653_changing_company_registered_under_clears_and_un_requires_the(page, tmp_path):
    """Verify that changing Company Registered Under clears and un-requires the previous selection's fields

    Steps (case is the oracle):
    1. Select MOCI, enter CR Number 'CR-1234567' and attach cr-copy.pdf -> MOCI fields filled
    2. Switch the dropdown to QFC -> MOCI block removed; only QFC Number and QFC Membership Copy shown
    3. Check the visible fields, then fill QFC Number 'QFC-00123' + copy and click Next -> Next is not
       blocked by any MOCI field, so previous values are discarded and no longer required; step advances
    4. Switch back to MOCI -> MOCI fields reappear empty (CR-1234567 and cr-copy.pdf gone)
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    with allure.step("Select MOCI, enter CR Number 'CR-1234567' and attach cr-copy.pdf"):
        qp.select("companyRegisteredUnder", value="moci")
        qp.type_into("crNumber", "CR-1234567")
        qp.attach("uploadCrCopy", files.make("cr-copy.pdf", 100 * KB))
    with allure.step("Switch to QFC: MOCI block removed; only QFC Number and QFC Membership Copy shown"):
        qp.select("companyRegisteredUnder", value="qfc")
        assert not qp.is_shown(qp.COND_GROUP_N.format(group="moci")), "MOCI block still shown"
        assert qp.visible_cond_field_names() == ["qfcNumber", "qfcMembershipCopy"], qp.visible_cond_field_names()
    with allure.step("Fill QFC Number 'QFC-00123' + copy and click Next: not blocked by any MOCI field"):
        qp.fill(build(1, files, 146653, cru="qfc"))
        qp.click_next()
        assert qp.wait_for_step(2), "Next blocked after switching away from MOCI"
    with allure.step("Switch back to MOCI: fields reappear empty"):
        qp.click_previous()
        assert qp.wait_for_step(1)
        qp.select("companyRegisteredUnder", value="moci")
        assert qp.field_value("crNumber") == "", "CR Number kept its old value"
        assert qp.attached_file_names("uploadCrCopy") == [], "cr-copy.pdf still attached"
