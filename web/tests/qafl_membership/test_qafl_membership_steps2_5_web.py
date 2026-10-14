"""
web/tests/qafl_membership/test_qafl_membership_steps2_5_web.py — Steps 2-5
field cases for PBI 130718: Senior Executive, Responsible Manager, Company
Location and Supporting Documents (uploads), plus the double-extension
upload edge case (146815).

SCRIPTED OFFLINE 2026-10-07, NOT EXECUTED. Character-limit cases are skipped
N/A (team decision 2026-10-03). Step 5 negatives click Submit, but the
fragment validates the step before any network call, so they never post.
The three Step 5 "accepts" cases do submit (QCTEST identity, QA inbox) and
end in a disclosed skip for the "stored with the record" half.
"""

import allure
import pytest

from web.pages.qafl_membership.qafl_membership_page import QaflMembershipPage
from web.tests.qafl_membership.qafl_data import (
    CHAR_LIMIT_SKIP,
    KB,
    MB,
    FileMaker,
    anon,
    build,
    reach_step,
    run_accepts,
    run_char_limit,
    run_file_size,
    run_file_type_rejected,
    run_invalid,
    run_non_numeric,
    run_required,
    run_whitespace,
)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 2 CEO / Chairman / Manager Name accepts 'Khalid Al-Marri'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146654
@pytest.mark.traceability("146654")
@allure.label("pbi", "130718")
@allure.label("testcase", "146654")
@anon()
def test_146654_step_2_ceo_chairman_manager_name_accepts_khalid_al_marri(page, tmp_path):
    """Verify that Step 2 CEO / Chairman / Manager Name accepts 'Khalid Al-Marri'

    Steps (case is the oracle):
    1. Complete Step 1 with baseline and open Step 2 -> Step 2 displayed
    2. Enter 'Khalid Al-Marri' in CEO / Chairman / Manager Name -> Value accepted
    3. Click Next -> Wizard advances to Step 3; value retained on Previous
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146654, 2, 'seniorExecutiveName', 'Khalid Al-Marri', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 2 CEO / Chairman / Manager Name blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146655
@pytest.mark.traceability("146655")
@allure.label("pbi", "130718")
@allure.label("testcase", "146655")
@anon()
def test_146655_an_empty_step_2_ceo_chairman_manager_name_blocks_progress(page, tmp_path):
    """Verify that an empty Step 2 CEO / Chairman / Manager Name blocks progress

    Steps (case is the oracle):
    1. Open Step 2 leaving the name empty -> Step 2 displayed
    2. Fill other Step 2 fields with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 2
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146655, 2, 'seniorExecutiveName', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Step 2 CEO / Chairman / Manager Name enforces the 200-character limit (200 accepted, 201 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146656
@pytest.mark.traceability("146656")
@allure.label("pbi", "130718")
@allure.label("testcase", "146656")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146656_step_2_ceo_chairman_manager_name_enforces_the_200_character(page, tmp_path):
    """Verify that Step 2 CEO / Chairman / Manager Name enforces the 200-character limit (200 accepted, 201 rejected)

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter 200 x 'A' and click Next -> 200 accepted
    3. Return and enter 201 x 'A' -> Input capped at 200 or inline error; 201 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146656, 2, 'seniorExecutiveName', 200, char='A', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 2 CEO / Chairman / Manager Name is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146657
@pytest.mark.traceability("146657")
@allure.label("pbi", "130718")
@allure.label("testcase", "146657")
@anon()
def test_146657_a_whitespace_only_step_2_ceo_chairman_manager_name_is_reject(page, tmp_path):
    """Verify that a whitespace-only Step 2 CEO / Chairman / Manager Name is rejected as empty

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter '   ' -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146657, 2, 'seniorExecutiveName', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 2 Designation accepts 'Chief Executive Officer'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146658
@pytest.mark.traceability("146658")
@allure.label("pbi", "130718")
@allure.label("testcase", "146658")
@anon()
def test_146658_step_2_designation_accepts_chief_executive_officer(page, tmp_path):
    """Verify that Step 2 Designation accepts 'Chief Executive Officer'

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter 'Chief Executive Officer' in Designation -> Value accepted
    3. Click Next -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146658, 2, 'seniorExecutiveDesignation', 'Chief Executive Officer', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 2 Designation blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146659
@pytest.mark.traceability("146659")
@allure.label("pbi", "130718")
@allure.label("testcase", "146659")
@anon()
def test_146659_an_empty_step_2_designation_blocks_progress(page, tmp_path):
    """Verify that an empty Step 2 Designation blocks progress

    Steps (case is the oracle):
    1. Open Step 2 leaving Designation empty -> Step 2 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 2
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146659, 2, 'seniorExecutiveDesignation', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Step 2 Designation enforces the 150-character limit (150 accepted, 151 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146660
@pytest.mark.traceability("146660")
@allure.label("pbi", "130718")
@allure.label("testcase", "146660")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146660_step_2_designation_enforces_the_150_character_limit_150_acce(page, tmp_path):
    """Verify that Step 2 Designation enforces the 150-character limit (150 accepted, 151 rejected)

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter 150 x 'A' and click Next -> 150 accepted
    3. Return and enter 151 x 'A' -> Input capped at 150 or inline error; 151 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146660, 2, 'seniorExecutiveDesignation', 150, char='A', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 2 Designation is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146661
@pytest.mark.traceability("146661")
@allure.label("pbi", "130718")
@allure.label("testcase", "146661")
@anon()
def test_146661_a_whitespace_only_step_2_designation_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Step 2 Designation is rejected as empty

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter '   ' in Designation -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146661, 2, 'seniorExecutiveDesignation', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 2 Email accepts 'khalid.almarri@gulffreight.qa'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146662
@pytest.mark.traceability("146662")
@allure.label("pbi", "130718")
@allure.label("testcase", "146662")
@anon()
def test_146662_step_2_email_accepts_khalid_almarri_gulffreight_qa(page, tmp_path):
    """Verify that Step 2 Email accepts 'khalid.almarri@gulffreight.qa'

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter 'khalid.almarri@gulffreight.qa' in Email and the same in Confirm Email -> Values accepted,
       no format error
    3. Click Next -> Wizard advances; email stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146662, 2, 'seniorExecutiveEmail', 'khalid.almarri@gulffreight.qa', cru='qfc', extra={'seniorExecutiveConfirmEmail': 'khalid.almarri@gulffreight.qa'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 2 Email blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146663
@pytest.mark.traceability("146663")
@allure.label("pbi", "130718")
@allure.label("testcase", "146663")
@anon()
def test_146663_an_empty_step_2_email_blocks_progress(page, tmp_path):
    """Verify that an empty Step 2 Email blocks progress

    Steps (case is the oracle):
    1. Open Step 2 leaving Email empty -> Step 2 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error under Email; stays on Step 2
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146663, 2, 'seniorExecutiveEmail', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 2 Email rejects the invalid format 'khalid.almarri@gulffreight'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146664
@pytest.mark.traceability("146664")
@allure.label("pbi", "130718")
@allure.label("testcase", "146664")
@anon()
def test_146664_step_2_email_rejects_the_invalid_format_khalid_almarri_gulff(page, tmp_path):
    """Verify that Step 2 Email rejects the invalid format 'khalid.almarri@gulffreight'

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter 'khalid.almarri@gulffreight' in Email and tab out -> Real-time inline email-format error
       under Email
    3. Click Next -> Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_invalid(qp, files, 146664, 2, 'seniorExecutiveEmail', ['khalid.almarri@gulffreight'], cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 2 Email is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146665
@pytest.mark.traceability("146665")
@allure.label("pbi", "130718")
@allure.label("testcase", "146665")
@anon()
def test_146665_a_whitespace_only_step_2_email_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Step 2 Email is rejected as empty

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter '   ' in Email -> Spaces held
    3. Click Next -> Inline required/format error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146665, 2, 'seniorExecutiveEmail', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Step 2 Confirm Email accepts a value matching Email')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146666
@pytest.mark.traceability("146666")
@allure.label("pbi", "130718")
@allure.label("testcase", "146666")
@anon()
def test_146666_step_2_confirm_email_accepts_a_value_matching_email(page, tmp_path):
    """Verify that Step 2 Confirm Email accepts a value matching Email

    Steps (case is the oracle):
    1. Open Step 2 and enter the Email -> Step 2 displayed
    2. Enter the identical value in Confirm Email Address -> No mismatch error
    3. Click Next -> Wizard advances
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146666, 2, 'seniorExecutiveConfirmEmail', 'khalid.almarri@gulffreight.qa', cru='qfc', extra={'seniorExecutiveEmail': 'khalid.almarri@gulffreight.qa'}, retained=False)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 2 Confirm Email blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146667
@pytest.mark.traceability("146667")
@allure.label("pbi", "130718")
@allure.label("testcase", "146667")
@anon()
def test_146667_an_empty_step_2_confirm_email_blocks_progress(page, tmp_path):
    """Verify that an empty Step 2 Confirm Email blocks progress

    Steps (case is the oracle):
    1. Open Step 2 entering Email only -> Step 2 displayed
    2. Leave Confirm Email empty -> Confirm field empty
    3. Click Next -> Inline required error; stays on Step 2
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146667, 2, 'seniorExecutiveConfirmEmail', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 2 Confirm Email shows a mismatch error for 'khalid.almarri@gulffreight.com'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146668
@pytest.mark.traceability("146668")
@allure.label("pbi", "130718")
@allure.label("testcase", "146668")
@anon()
def test_146668_step_2_confirm_email_shows_a_mismatch_error_for_khalid_almar(page, tmp_path):
    """Verify that Step 2 Confirm Email shows a mismatch error for 'khalid.almarri@gulffreight.com'

    Steps (case is the oracle):
    1. Open Step 2 and enter Email 'khalid.almarri@gulffreight.qa' -> Step 2 displayed
    2. Enter 'khalid.almarri@gulffreight.com' in Confirm Email and tab out -> Real-time mismatch error
       under Confirm Email
    3. Click Next -> Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_invalid(qp, files, 146668, 2, 'seniorExecutiveConfirmEmail', ['khalid.almarri@gulffreight.com'], cru='qfc', extra={'seniorExecutiveEmail': 'khalid.almarri@gulffreight.qa'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 2 Confirm Email is rejected')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146669
@pytest.mark.traceability("146669")
@allure.label("pbi", "130718")
@allure.label("testcase", "146669")
@anon()
def test_146669_a_whitespace_only_step_2_confirm_email_is_rejected(page, tmp_path):
    """Verify that a whitespace-only Step 2 Confirm Email is rejected

    Steps (case is the oracle):
    1. Open Step 2 entering a valid Email -> Step 2 displayed
    2. Enter '   ' in Confirm Email -> Spaces held
    3. Click Next -> Inline required/mismatch error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146669, 2, 'seniorExecutiveConfirmEmail', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 2 Phone accepts '+974 4412 3456'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146670
@pytest.mark.traceability("146670")
@allure.label("pbi", "130718")
@allure.label("testcase", "146670")
@anon()
def test_146670_step_2_phone_accepts_974_4412_3456(page, tmp_path):
    """Verify that Step 2 Phone accepts '+974 4412 3456'

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter '+974 4412 3456' in Phone -> Value accepted
    3. Click Next -> Wizard advances; phone stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146670, 2, 'seniorExecutivePhone', '+974 4412 3456', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 2 Phone blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146671
@pytest.mark.traceability("146671")
@allure.label("pbi", "130718")
@allure.label("testcase", "146671")
@anon()
def test_146671_an_empty_step_2_phone_blocks_progress(page, tmp_path):
    """Verify that an empty Step 2 Phone blocks progress

    Steps (case is the oracle):
    1. Open Step 2 leaving Phone empty -> Step 2 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 2
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146671, 2, 'seniorExecutivePhone', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 2 Phone rejects '+971 4 412 3456' (wrong prefix) and '+974 12ab'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146672
@pytest.mark.traceability("146672")
@allure.label("pbi", "130718")
@allure.label("testcase", "146672")
@anon()
def test_146672_step_2_phone_rejects_971_4_412_3456_wrong_prefix_and_974_12a(page, tmp_path):
    """Verify that Step 2 Phone rejects '+971 4 412 3456' (wrong prefix) and '+974 12ab'

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter '+971 4 412 3456' and tab out -> Inline phone error for non +974 prefix; Next blocked
    3. Replace with '+974 12ab' and tab out -> Inline phone-format error for malformed number; Next
       blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_invalid(qp, files, 146672, 2, 'seniorExecutivePhone', ['+971 4 412 3456', '+974 12ab'], cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 2 Phone is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146673
@pytest.mark.traceability("146673")
@allure.label("pbi", "130718")
@allure.label("testcase", "146673")
@anon()
def test_146673_a_whitespace_only_step_2_phone_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Step 2 Phone is rejected as empty

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter '   ' in Phone -> Spaces held
    3. Click Next -> Inline required/format error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146673, 2, 'seniorExecutivePhone', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 2 Extension Number accepts '204'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146674
@pytest.mark.traceability("146674")
@allure.label("pbi", "130718")
@allure.label("testcase", "146674")
@anon()
def test_146674_step_2_extension_number_accepts_204(page, tmp_path):
    """Verify that Step 2 Extension Number accepts '204'

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter 204 in Extension Number -> Value accepted
    3. Click Next -> Wizard advances; 204 stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146674, 2, 'seniorExecutiveExtension', '204', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 2 Extension Number blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146675
@pytest.mark.traceability("146675")
@allure.label("pbi", "130718")
@allure.label("testcase", "146675")
@anon()
def test_146675_an_empty_step_2_extension_number_blocks_progress(page, tmp_path):
    """Verify that an empty Step 2 Extension Number blocks progress

    Steps (case is the oracle):
    1. Open Step 2 leaving Extension empty -> Step 2 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 2
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146675, 2, 'seniorExecutiveExtension', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that Step 2 Extension Number rejects non-numeric 'ab12'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146676
@pytest.mark.traceability("146676")
@allure.label("pbi", "130718")
@allure.label("testcase", "146676")
@anon()
def test_146676_step_2_extension_number_rejects_non_numeric_ab12(page, tmp_path):
    """Verify that Step 2 Extension Number rejects non-numeric 'ab12'

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Type 'ab12' in Extension Number -> Letters not accepted or flagged
    3. Click Next -> Inline numeric-format error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_non_numeric(qp, files, 146676, 2, 'seniorExecutiveExtension', 'ab12')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 2 Extension Number is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146677
@pytest.mark.traceability("146677")
@allure.label("pbi", "130718")
@allure.label("testcase", "146677")
@anon()
def test_146677_a_whitespace_only_step_2_extension_number_is_rejected_as_emp(page, tmp_path):
    """Verify that a whitespace-only Step 2 Extension Number is rejected as empty

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter '   ' in Extension -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146677, 2, 'seniorExecutiveExtension', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 2 Mobile Number accepts '+974 5512 3456'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146678
@pytest.mark.traceability("146678")
@allure.label("pbi", "130718")
@allure.label("testcase", "146678")
@anon()
def test_146678_step_2_mobile_number_accepts_974_5512_3456(page, tmp_path):
    """Verify that Step 2 Mobile Number accepts '+974 5512 3456'

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter '+974 5512 3456' in Mobile Number -> Value accepted
    3. Click Next -> Wizard advances; mobile stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146678, 2, 'seniorExecutiveMobile', '+974 5512 3456', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 2 Mobile Number blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146679
@pytest.mark.traceability("146679")
@allure.label("pbi", "130718")
@allure.label("testcase", "146679")
@anon()
def test_146679_an_empty_step_2_mobile_number_blocks_progress(page, tmp_path):
    """Verify that an empty Step 2 Mobile Number blocks progress

    Steps (case is the oracle):
    1. Open Step 2 leaving Mobile empty -> Step 2 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 2
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146679, 2, 'seniorExecutiveMobile', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 2 Mobile Number rejects '55123456' (no +974 prefix) and '+974 abcd'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146680
@pytest.mark.traceability("146680")
@allure.label("pbi", "130718")
@allure.label("testcase", "146680")
@anon()
def test_146680_step_2_mobile_number_rejects_55123456_no_974_prefix_and_974(page, tmp_path):
    """Verify that Step 2 Mobile Number rejects '55123456' (no +974 prefix) and '+974 abcd'

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter '55123456' and tab out -> Inline prefix/format error; Next blocked
    3. Replace with '+974 abcd' and tab out -> Inline format error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_invalid(qp, files, 146680, 2, 'seniorExecutiveMobile', ['55123456', '+974 abcd'], cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 2 - Senior Executive")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 2 Mobile Number is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146681
@pytest.mark.traceability("146681")
@allure.label("pbi", "130718")
@allure.label("testcase", "146681")
@anon()
def test_146681_a_whitespace_only_step_2_mobile_number_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Step 2 Mobile Number is rejected as empty

    Steps (case is the oracle):
    1. Open Step 2 -> Step 2 displayed
    2. Enter '   ' in Mobile Number -> Spaces held
    3. Click Next -> Inline required/format error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146681, 2, 'seniorExecutiveMobile', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 3 Responsible Manager Name accepts 'Noora Al-Thani'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146682
@pytest.mark.traceability("146682")
@allure.label("pbi", "130718")
@allure.label("testcase", "146682")
@anon()
def test_146682_step_3_responsible_manager_name_accepts_noora_al_thani(page, tmp_path):
    """Verify that Step 3 Responsible Manager Name accepts 'Noora Al-Thani'

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter 'Noora Al-Thani' in Responsible Manager Name -> Value accepted
    3. Click Next -> Wizard advances to Step 4; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146682, 3, 'responsibleManagerName', 'Noora Al-Thani', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 3 Responsible Manager Name blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146683
@pytest.mark.traceability("146683")
@allure.label("pbi", "130718")
@allure.label("testcase", "146683")
@anon()
def test_146683_an_empty_step_3_responsible_manager_name_blocks_progress(page, tmp_path):
    """Verify that an empty Step 3 Responsible Manager Name blocks progress

    Steps (case is the oracle):
    1. Open Step 3 leaving the name empty -> Step 3 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 3
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146683, 3, 'responsibleManagerName', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Step 3 Responsible Manager Name enforces the 200-character limit (200 accepted, 201 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146684
@pytest.mark.traceability("146684")
@allure.label("pbi", "130718")
@allure.label("testcase", "146684")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146684_step_3_responsible_manager_name_enforces_the_200_character_l(page, tmp_path):
    """Verify that Step 3 Responsible Manager Name enforces the 200-character limit (200 accepted, 201 rejected)

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter 200 x 'A' and click Next -> 200 accepted
    3. Return and enter 201 x 'A' -> Input capped at 200 or inline error; 201 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146684, 3, 'responsibleManagerName', 200, char='A', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 3 Responsible Manager Name is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146685
@pytest.mark.traceability("146685")
@allure.label("pbi", "130718")
@allure.label("testcase", "146685")
@anon()
def test_146685_a_whitespace_only_step_3_responsible_manager_name_is_rejecte(page, tmp_path):
    """Verify that a whitespace-only Step 3 Responsible Manager Name is rejected as empty

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter '   ' -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146685, 3, 'responsibleManagerName', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 3 Designation accepts 'Operations Manager'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146686
@pytest.mark.traceability("146686")
@allure.label("pbi", "130718")
@allure.label("testcase", "146686")
@anon()
def test_146686_step_3_designation_accepts_operations_manager(page, tmp_path):
    """Verify that Step 3 Designation accepts 'Operations Manager'

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter 'Operations Manager' in Designation -> Value accepted
    3. Click Next -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146686, 3, 'responsibleManagerDesignation', 'Operations Manager', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 3 Designation blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146687
@pytest.mark.traceability("146687")
@allure.label("pbi", "130718")
@allure.label("testcase", "146687")
@anon()
def test_146687_an_empty_step_3_designation_blocks_progress(page, tmp_path):
    """Verify that an empty Step 3 Designation blocks progress

    Steps (case is the oracle):
    1. Open Step 3 leaving Designation empty -> Step 3 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 3
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146687, 3, 'responsibleManagerDesignation', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Step 3 Designation enforces the 150-character limit (150 accepted, 151 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146688
@pytest.mark.traceability("146688")
@allure.label("pbi", "130718")
@allure.label("testcase", "146688")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146688_step_3_designation_enforces_the_150_character_limit_150_acce(page, tmp_path):
    """Verify that Step 3 Designation enforces the 150-character limit (150 accepted, 151 rejected)

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter 150 x 'A' and click Next -> 150 accepted
    3. Return and enter 151 x 'A' -> Input capped at 150 or inline error; 151 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146688, 3, 'responsibleManagerDesignation', 150, char='A', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 3 Designation is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146689
@pytest.mark.traceability("146689")
@allure.label("pbi", "130718")
@allure.label("testcase", "146689")
@anon()
def test_146689_a_whitespace_only_step_3_designation_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Step 3 Designation is rejected as empty

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter '   ' in Designation -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146689, 3, 'responsibleManagerDesignation', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 3 Email accepts 'noora.althani@gulffreight.qa'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146690
@pytest.mark.traceability("146690")
@allure.label("pbi", "130718")
@allure.label("testcase", "146690")
@anon()
def test_146690_step_3_email_accepts_noora_althani_gulffreight_qa(page, tmp_path):
    """Verify that Step 3 Email accepts 'noora.althani@gulffreight.qa'

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter 'noora.althani@gulffreight.qa' in Email and Confirm Email -> Values accepted, no format
       error
    3. Click Next -> Wizard advances; email stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146690, 3, 'responsibleManagerEmail', 'noora.althani@gulffreight.qa', cru='qfc', extra={'responsibleManagerConfirmEmail': 'noora.althani@gulffreight.qa'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 3 Email blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146691
@pytest.mark.traceability("146691")
@allure.label("pbi", "130718")
@allure.label("testcase", "146691")
@anon()
def test_146691_an_empty_step_3_email_blocks_progress(page, tmp_path):
    """Verify that an empty Step 3 Email blocks progress

    Steps (case is the oracle):
    1. Open Step 3 leaving Email empty -> Step 3 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error under Email; stays on Step 3
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146691, 3, 'responsibleManagerEmail', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 3 Email rejects the invalid format 'noora.althani@@gulffreight.qa'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146692
@pytest.mark.traceability("146692")
@allure.label("pbi", "130718")
@allure.label("testcase", "146692")
@anon()
def test_146692_step_3_email_rejects_the_invalid_format_noora_althani_gulffr(page, tmp_path):
    """Verify that Step 3 Email rejects the invalid format 'noora.althani@@gulffreight.qa'

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter 'noora.althani@@gulffreight.qa' and tab out -> Real-time inline email-format error
    3. Click Next -> Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_invalid(qp, files, 146692, 3, 'responsibleManagerEmail', ['noora.althani@@gulffreight.qa'], cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 3 Email is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146693
@pytest.mark.traceability("146693")
@allure.label("pbi", "130718")
@allure.label("testcase", "146693")
@anon()
def test_146693_a_whitespace_only_step_3_email_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Step 3 Email is rejected as empty

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter '   ' in Email -> Spaces held
    3. Click Next -> Inline required/format error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146693, 3, 'responsibleManagerEmail', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Step 3 Confirm Email accepts a value matching Email')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146694
@pytest.mark.traceability("146694")
@allure.label("pbi", "130718")
@allure.label("testcase", "146694")
@anon()
def test_146694_step_3_confirm_email_accepts_a_value_matching_email(page, tmp_path):
    """Verify that Step 3 Confirm Email accepts a value matching Email

    Steps (case is the oracle):
    1. Open Step 3 and enter the Email -> Step 3 displayed
    2. Enter the identical value in Confirm Email Address -> No mismatch error
    3. Click Next -> Wizard advances
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146694, 3, 'responsibleManagerConfirmEmail', 'noora.althani@gulffreight.qa', cru='qfc', extra={'responsibleManagerEmail': 'noora.althani@gulffreight.qa'}, retained=False)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 3 Confirm Email blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146695
@pytest.mark.traceability("146695")
@allure.label("pbi", "130718")
@allure.label("testcase", "146695")
@anon()
def test_146695_an_empty_step_3_confirm_email_blocks_progress(page, tmp_path):
    """Verify that an empty Step 3 Confirm Email blocks progress

    Steps (case is the oracle):
    1. Open Step 3 entering Email only -> Step 3 displayed
    2. Leave Confirm Email empty -> Confirm field empty
    3. Click Next -> Inline required error; stays on Step 3
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146695, 3, 'responsibleManagerConfirmEmail', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 3 Confirm Email shows a mismatch error for 'noora.althani@gulffreight.com'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146696
@pytest.mark.traceability("146696")
@allure.label("pbi", "130718")
@allure.label("testcase", "146696")
@anon()
def test_146696_step_3_confirm_email_shows_a_mismatch_error_for_noora_althan(page, tmp_path):
    """Verify that Step 3 Confirm Email shows a mismatch error for 'noora.althani@gulffreight.com'

    Steps (case is the oracle):
    1. Open Step 3 and enter Email 'noora.althani@gulffreight.qa' -> Step 3 displayed
    2. Enter 'noora.althani@gulffreight.com' in Confirm Email and tab out -> Real-time mismatch error
    3. Click Next -> Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_invalid(qp, files, 146696, 3, 'responsibleManagerConfirmEmail', ['noora.althani@gulffreight.com'], cru='qfc', extra={'responsibleManagerEmail': 'noora.althani@gulffreight.qa'})


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 3 Confirm Email is rejected')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146697
@pytest.mark.traceability("146697")
@allure.label("pbi", "130718")
@allure.label("testcase", "146697")
@anon()
def test_146697_a_whitespace_only_step_3_confirm_email_is_rejected(page, tmp_path):
    """Verify that a whitespace-only Step 3 Confirm Email is rejected

    Steps (case is the oracle):
    1. Open Step 3 entering a valid Email -> Step 3 displayed
    2. Enter '   ' in Confirm Email -> Spaces held
    3. Click Next -> Inline required/mismatch error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146697, 3, 'responsibleManagerConfirmEmail', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 3 Phone accepts '+974 4412 3457'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146698
@pytest.mark.traceability("146698")
@allure.label("pbi", "130718")
@allure.label("testcase", "146698")
@anon()
def test_146698_step_3_phone_accepts_974_4412_3457(page, tmp_path):
    """Verify that Step 3 Phone accepts '+974 4412 3457'

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter '+974 4412 3457' in Phone -> Value accepted
    3. Click Next -> Wizard advances; phone stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146698, 3, 'responsibleManagerPhone', '+974 4412 3457', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 3 Phone blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146699
@pytest.mark.traceability("146699")
@allure.label("pbi", "130718")
@allure.label("testcase", "146699")
@anon()
def test_146699_an_empty_step_3_phone_blocks_progress(page, tmp_path):
    """Verify that an empty Step 3 Phone blocks progress

    Steps (case is the oracle):
    1. Open Step 3 leaving Phone empty -> Step 3 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 3
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146699, 3, 'responsibleManagerPhone', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 3 Phone rejects '+971 4 412 3457' (wrong prefix) and '+974 12ab'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146700
@pytest.mark.traceability("146700")
@allure.label("pbi", "130718")
@allure.label("testcase", "146700")
@anon()
def test_146700_step_3_phone_rejects_971_4_412_3457_wrong_prefix_and_974_12a(page, tmp_path):
    """Verify that Step 3 Phone rejects '+971 4 412 3457' (wrong prefix) and '+974 12ab'

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter '+971 4 412 3457' and tab out -> Inline prefix error; Next blocked
    3. Replace with '+974 12ab' and tab out -> Inline format error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_invalid(qp, files, 146700, 3, 'responsibleManagerPhone', ['+971 4 412 3457', '+974 12ab'], cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 3 Phone is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146701
@pytest.mark.traceability("146701")
@allure.label("pbi", "130718")
@allure.label("testcase", "146701")
@anon()
def test_146701_a_whitespace_only_step_3_phone_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Step 3 Phone is rejected as empty

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter '   ' in Phone -> Spaces held
    3. Click Next -> Inline required/format error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146701, 3, 'responsibleManagerPhone', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 3 Extension Number accepts '205'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146702
@pytest.mark.traceability("146702")
@allure.label("pbi", "130718")
@allure.label("testcase", "146702")
@anon()
def test_146702_step_3_extension_number_accepts_205(page, tmp_path):
    """Verify that Step 3 Extension Number accepts '205'

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter 205 in Extension Number -> Value accepted
    3. Click Next -> Wizard advances; 205 stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146702, 3, 'responsibleManagerExtension', '205', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 3 Extension Number blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146703
@pytest.mark.traceability("146703")
@allure.label("pbi", "130718")
@allure.label("testcase", "146703")
@anon()
def test_146703_an_empty_step_3_extension_number_blocks_progress(page, tmp_path):
    """Verify that an empty Step 3 Extension Number blocks progress

    Steps (case is the oracle):
    1. Open Step 3 leaving Extension empty -> Step 3 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 3
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146703, 3, 'responsibleManagerExtension', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that Step 3 Extension Number rejects non-numeric 'ab12'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146704
@pytest.mark.traceability("146704")
@allure.label("pbi", "130718")
@allure.label("testcase", "146704")
@anon()
def test_146704_step_3_extension_number_rejects_non_numeric_ab12(page, tmp_path):
    """Verify that Step 3 Extension Number rejects non-numeric 'ab12'

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Type 'ab12' in Extension Number -> Letters not accepted or flagged
    3. Click Next -> Inline numeric-format error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_non_numeric(qp, files, 146704, 3, 'responsibleManagerExtension', 'ab12')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 3 Extension Number is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146705
@pytest.mark.traceability("146705")
@allure.label("pbi", "130718")
@allure.label("testcase", "146705")
@anon()
def test_146705_a_whitespace_only_step_3_extension_number_is_rejected_as_emp(page, tmp_path):
    """Verify that a whitespace-only Step 3 Extension Number is rejected as empty

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter '   ' in Extension -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146705, 3, 'responsibleManagerExtension', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 3 Mobile Number accepts '+974 5512 3457'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146706
@pytest.mark.traceability("146706")
@allure.label("pbi", "130718")
@allure.label("testcase", "146706")
@anon()
def test_146706_step_3_mobile_number_accepts_974_5512_3457(page, tmp_path):
    """Verify that Step 3 Mobile Number accepts '+974 5512 3457'

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter '+974 5512 3457' in Mobile Number -> Value accepted
    3. Click Next -> Wizard advances; mobile stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146706, 3, 'responsibleManagerMobile', '+974 5512 3457', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Step 3 Mobile Number blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146707
@pytest.mark.traceability("146707")
@allure.label("pbi", "130718")
@allure.label("testcase", "146707")
@anon()
def test_146707_an_empty_step_3_mobile_number_blocks_progress(page, tmp_path):
    """Verify that an empty Step 3 Mobile Number blocks progress

    Steps (case is the oracle):
    1. Open Step 3 leaving Mobile empty -> Step 3 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 3
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146707, 3, 'responsibleManagerMobile', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Step 3 Mobile Number rejects '55123457' (no +974 prefix) and '+974 abcd'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146708
@pytest.mark.traceability("146708")
@allure.label("pbi", "130718")
@allure.label("testcase", "146708")
@anon()
def test_146708_step_3_mobile_number_rejects_55123457_no_974_prefix_and_974(page, tmp_path):
    """Verify that Step 3 Mobile Number rejects '55123457' (no +974 prefix) and '+974 abcd'

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter '55123457' and tab out -> Inline prefix/format error; Next blocked
    3. Replace with '+974 abcd' and tab out -> Inline format error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_invalid(qp, files, 146708, 3, 'responsibleManagerMobile', ['55123457', '+974 abcd'], cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 3 - Responsible Manager")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Step 3 Mobile Number is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146709
@pytest.mark.traceability("146709")
@allure.label("pbi", "130718")
@allure.label("testcase", "146709")
@anon()
def test_146709_a_whitespace_only_step_3_mobile_number_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Step 3 Mobile Number is rejected as empty

    Steps (case is the oracle):
    1. Open Step 3 -> Step 3 displayed
    2. Enter '   ' in Mobile Number -> Spaces held
    3. Click Next -> Inline required/format error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146709, 3, 'responsibleManagerMobile', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that Website accepts 'https://www.gulffreight.qa'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146710
@pytest.mark.traceability("146710")
@allure.label("pbi", "130718")
@allure.label("testcase", "146710")
@anon()
def test_146710_website_accepts_https_www_gulffreight_qa(page, tmp_path):
    """Verify that Website accepts 'https://www.gulffreight.qa'

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter 'https://www.gulffreight.qa' in Website -> Value accepted, no error
    3. Click Next -> Wizard advances to Step 5; website stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146710, 4, 'website', 'https://www.gulffreight.qa', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that Website rejects the invalid URL 'www gulffreight'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146711
@pytest.mark.traceability("146711")
@allure.label("pbi", "130718")
@allure.label("testcase", "146711")
@anon()
def test_146711_website_rejects_the_invalid_url_www_gulffreight(page, tmp_path):
    """Verify that Website rejects the invalid URL 'www gulffreight'

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter 'www gulffreight' in Website and tab out -> Inline URL-format error
    3. Click Next -> Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_invalid(qp, files, 146711, 4, 'website', ['www gulffreight'], cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that an empty Website does not block progress (optional field)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146712
@pytest.mark.traceability("146712")
@allure.label("pbi", "130718")
@allure.label("testcase", "146712")
@anon()
def test_146712_an_empty_website_does_not_block_progress_optional_field(page, tmp_path):
    """Verify that an empty Website does not block progress (optional field)

    Steps (case is the oracle):
    1. Open Step 4 leaving Website empty -> Step 4 displayed; Website has no asterisk
    2. Fill the other Step 4 fields with baseline -> Other fields accepted
    3. Click Next -> Wizard advances to Step 5 with no error; Website stored empty
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146712, 4)
    with allure.step("Website has no asterisk"):
        assert not qp.has_required_marker("website"), "Website is marked required"
    with allure.step("Fill the other Step 4 fields with baseline, leave Website empty, click Next"):
        qp.fill(build(4, files, 146712, exclude=("website",)))
        qp.click_next()
    with allure.step("Wizard advances to Step 5 with no error"):
        assert qp.wait_for_step(5), f"blocked on empty Website: {qp.field_error_text('website')!r}"
        assert qp.has_no_field_error("website")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Location Name accepts 'Gulf Freight HQ'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146713
@pytest.mark.traceability("146713")
@allure.label("pbi", "130718")
@allure.label("testcase", "146713")
@anon()
def test_146713_location_name_accepts_gulf_freight_hq(page, tmp_path):
    """Verify that Location Name accepts 'Gulf Freight HQ'

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter 'Gulf Freight HQ' in Location Name -> Value accepted
    3. Click Next -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146713, 4, 'locationName', 'Gulf Freight HQ', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Location Name blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146714
@pytest.mark.traceability("146714")
@allure.label("pbi", "130718")
@allure.label("testcase", "146714")
@anon()
def test_146714_an_empty_location_name_blocks_progress(page, tmp_path):
    """Verify that an empty Location Name blocks progress

    Steps (case is the oracle):
    1. Open Step 4 leaving Location Name empty -> Step 4 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 4
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146714, 4, 'locationName', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Location Name enforces the 200-character limit (200 accepted, 201 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146715
@pytest.mark.traceability("146715")
@allure.label("pbi", "130718")
@allure.label("testcase", "146715")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146715_location_name_enforces_the_200_character_limit_200_accepted(page, tmp_path):
    """Verify that Location Name enforces the 200-character limit (200 accepted, 201 rejected)

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter 200 x 'A' and click Next -> 200 accepted
    3. Return and enter 201 x 'A' -> Input capped at 200 or inline error; 201 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146715, 4, 'locationName', 200, char='A', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Location Name is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146716
@pytest.mark.traceability("146716")
@allure.label("pbi", "130718")
@allure.label("testcase", "146716")
@anon()
def test_146716_a_whitespace_only_location_name_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Location Name is rejected as empty

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter '   ' in Location Name -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146716, 4, 'locationName', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Building Number accepts '12'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146717
@pytest.mark.traceability("146717")
@allure.label("pbi", "130718")
@allure.label("testcase", "146717")
@anon()
def test_146717_building_number_accepts_12(page, tmp_path):
    """Verify that Building Number accepts '12'

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter '12' in Building Number -> Value accepted
    3. Click Next -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146717, 4, 'buildingNumber', '12', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Building Number blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146718
@pytest.mark.traceability("146718")
@allure.label("pbi", "130718")
@allure.label("testcase", "146718")
@anon()
def test_146718_an_empty_building_number_blocks_progress(page, tmp_path):
    """Verify that an empty Building Number blocks progress

    Steps (case is the oracle):
    1. Open Step 4 leaving Building Number empty -> Step 4 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 4
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146718, 4, 'buildingNumber', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Building Number enforces the 20-character limit (20 accepted, 21 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146719
@pytest.mark.traceability("146719")
@allure.label("pbi", "130718")
@allure.label("testcase", "146719")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146719_building_number_enforces_the_20_character_limit_20_accepted(page, tmp_path):
    """Verify that Building Number enforces the 20-character limit (20 accepted, 21 rejected)

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter 20 x '1' and click Next -> 20 accepted
    3. Return and enter 21 x '1' -> Input capped at 20 or inline error; 21 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146719, 4, 'buildingNumber', 20, char='1', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Building Number is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146720
@pytest.mark.traceability("146720")
@allure.label("pbi", "130718")
@allure.label("testcase", "146720")
@anon()
def test_146720_a_whitespace_only_building_number_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Building Number is rejected as empty

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter '   ' in Building Number -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146720, 4, 'buildingNumber', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Zone Number accepts '55'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146721
@pytest.mark.traceability("146721")
@allure.label("pbi", "130718")
@allure.label("testcase", "146721")
@anon()
def test_146721_zone_number_accepts_55(page, tmp_path):
    """Verify that Zone Number accepts '55'

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter '55' in Zone Number -> Value accepted
    3. Click Next -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146721, 4, 'zoneNumber', '55', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Zone Number blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146722
@pytest.mark.traceability("146722")
@allure.label("pbi", "130718")
@allure.label("testcase", "146722")
@anon()
def test_146722_an_empty_zone_number_blocks_progress(page, tmp_path):
    """Verify that an empty Zone Number blocks progress

    Steps (case is the oracle):
    1. Open Step 4 leaving Zone Number empty -> Step 4 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 4
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146722, 4, 'zoneNumber', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Zone Number enforces the 20-character limit (20 accepted, 21 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146723
@pytest.mark.traceability("146723")
@allure.label("pbi", "130718")
@allure.label("testcase", "146723")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146723_zone_number_enforces_the_20_character_limit_20_accepted_21_r(page, tmp_path):
    """Verify that Zone Number enforces the 20-character limit (20 accepted, 21 rejected)

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter 20 x '5' and click Next -> 20 accepted
    3. Return and enter 21 x '5' -> Input capped at 20 or inline error; 21 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146723, 4, 'zoneNumber', 20, char='5', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Zone Number is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146724
@pytest.mark.traceability("146724")
@allure.label("pbi", "130718")
@allure.label("testcase", "146724")
@anon()
def test_146724_a_whitespace_only_zone_number_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Zone Number is rejected as empty

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter '   ' in Zone Number -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146724, 4, 'zoneNumber', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Street Number accepts '310'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146725
@pytest.mark.traceability("146725")
@allure.label("pbi", "130718")
@allure.label("testcase", "146725")
@anon()
def test_146725_street_number_accepts_310(page, tmp_path):
    """Verify that Street Number accepts '310'

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter '310' in Street Number -> Value accepted
    3. Click Next -> Wizard advances; value stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_accepts(qp, files, 146725, 4, 'streetNumber', '310', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that an empty Street Number blocks progress')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146726
@pytest.mark.traceability("146726")
@allure.label("pbi", "130718")
@allure.label("testcase", "146726")
@anon()
def test_146726_an_empty_street_number_blocks_progress(page, tmp_path):
    """Verify that an empty Street Number blocks progress

    Steps (case is the oracle):
    1. Open Step 4 leaving Street Number empty -> Step 4 displayed
    2. Fill others with baseline -> Others accepted
    3. Click Next -> Inline required error; stays on Step 4
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146726, 4, 'streetNumber', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Street Number enforces the 20-character limit (20 accepted, 21 rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146727
@pytest.mark.traceability("146727")
@allure.label("pbi", "130718")
@allure.label("testcase", "146727")
@pytest.mark.skip(reason=CHAR_LIMIT_SKIP)
@anon()
def test_146727_street_number_enforces_the_20_character_limit_20_accepted_21(page, tmp_path):
    """Verify that Street Number enforces the 20-character limit (20 accepted, 21 rejected)

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter 20 x '3' and click Next -> 20 accepted
    3. Return and enter 21 x '3' -> Input capped at 20 or inline error; 21 never accepted
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_char_limit(qp, files, 146727, 4, 'streetNumber', 20, char='3', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 4 - Company Location")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a whitespace-only Street Number is rejected as empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146728
@pytest.mark.traceability("146728")
@allure.label("pbi", "130718")
@allure.label("testcase", "146728")
@anon()
def test_146728_a_whitespace_only_street_number_is_rejected_as_empty(page, tmp_path):
    """Verify that a whitespace-only Street Number is rejected as empty

    Steps (case is the oracle):
    1. Open Step 4 -> Step 4 displayed
    2. Enter '   ' in Street Number -> Spaces held
    3. Click Next -> Inline required error; Next blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_whitespace(qp, files, 146728, 4, 'streetNumber', cru='qfc', value='   ')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 5 - Supporting Documents")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Authorization Letter upload accepts 'auth-letter.pdf' (1 MB)")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146729
@pytest.mark.traceability("146729")
@allure.label("pbi", "130718")
@allure.label("testcase", "146729")
@anon()
def test_146729_authorization_letter_upload_accepts_auth_letter_pdf_1_mb(page, tmp_path):
    """Verify that the Authorization Letter upload accepts 'auth-letter.pdf' (1 MB)

    Steps (case is the oracle):
    1. Open Step 5 -> Step 5 displayed
    2. Upload auth-letter.pdf (1 MB) as the Authorization Letter -> File name shown attached, no error
    3. Upload valid ID front/back, pass CAPTCHA and Submit -> Submission accepted; letter stored with
       the record
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146729, 5)
    with allure.step("Upload auth-letter.pdf"):
        qp.fill(build(5, files, 146729, override={'qaflMembershipAuthorizationLetter': files.make('auth-letter.pdf', 1 * MB)}))
        assert qp.has_no_field_error('qaflMembershipAuthorizationLetter'), qp.field_error_text('qaflMembershipAuthorizationLetter')
        assert 'auth-letter.pdf' in qp.attached_file_names('qaflMembershipAuthorizationLetter'), "file not shown attached"
    with allure.step("Complete the rest and Submit (QCTEST identity, QA inbox)"):
        qp.submit_and_wait_response()
    with allure.step("Submission accepted"):
        assert qp.has_submission_succeeded(), f"not accepted; toast={qp.toast_text(2000)!r} captcha={qp.captcha_error_text()!r}"
    pytest.skip("Web half PASSED. 'stored with the record' needs a Control_Panel read of the QCTEST-146729 "
                "submission; that half is not verified by this Web test.")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 5 - Supporting Documents")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that a missing Authorization Letter blocks submission')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146730
@pytest.mark.traceability("146730")
@allure.label("pbi", "130718")
@allure.label("testcase", "146730")
@anon()
def test_146730_a_missing_authorization_letter_blocks_submission(page, tmp_path):
    """Verify that a missing Authorization Letter blocks submission

    Steps (case is the oracle):
    1. Open Step 5 and attach only ID front/back -> Step 5 displayed
    2. Pass CAPTCHA -> Others attached
    3. Click Submit -> Inline required error under the Authorization Letter; nothing stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146730, 5, 'qaflMembershipAuthorizationLetter', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 5 - Supporting Documents")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the Authorization Letter upload rejects 'letter.jpg'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146731
@pytest.mark.traceability("146731")
@allure.label("pbi", "130718")
@allure.label("testcase", "146731")
@anon()
def test_146731_authorization_letter_upload_rejects_letter_jpg(page, tmp_path):
    """Verify that the Authorization Letter upload rejects 'letter.jpg'

    Steps (case is the oracle):
    1. Open Step 5 -> Step 5 displayed
    2. Upload letter.jpg as the Authorization Letter -> Inline file-type error; file not attached
    3. Click Submit -> Submit blocked while no valid letter is attached
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_type_rejected(qp, files, 146731, 5, 'qaflMembershipAuthorizationLetter', 'letter.jpg', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 5 - Supporting Documents")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the Authorization Letter upload enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146732
@pytest.mark.traceability("146732")
@allure.label("pbi", "130718")
@allure.label("testcase", "146732")
@anon()
def test_146732_authorization_letter_upload_enforces_the_5_mb_limit_4_99_mb(page, tmp_path):
    """Verify that the Authorization Letter upload enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)

    Steps (case is the oracle):
    1. Open Step 5 -> Step 5 displayed
    2. Upload letter-4_99mb.pdf (4.99 MB) -> 4.99 MB accepted
    3. Replace with letter-5_01mb.pdf (5.01 MB) -> 5.01 MB rejected with inline size error
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_size(qp, files, 146732, 5, 'qaflMembershipAuthorizationLetter', 'letter-4_99mb.pdf', 'letter-5_01mb.pdf', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 5 - Supporting Documents")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Qatar ID Front upload accepts 'qid-front.jpg' (500 KB)")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146733
@pytest.mark.traceability("146733")
@allure.label("pbi", "130718")
@allure.label("testcase", "146733")
@anon()
def test_146733_qatar_id_front_upload_accepts_qid_front_jpg_500_kb(page, tmp_path):
    """Verify that the Qatar ID Front upload accepts 'qid-front.jpg' (500 KB)

    Steps (case is the oracle):
    1. Open Step 5 -> Step 5 displayed
    2. Upload qid-front.jpg (500 KB) -> File attached, no error
    3. Complete the rest and Submit -> Submission accepted; front ID stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146733, 5)
    with allure.step("Upload qid-front.jpg"):
        qp.fill(build(5, files, 146733, override={'authorizedPersonQatarIdFront': files.make('qid-front.jpg', 500 * KB)}))
        assert qp.has_no_field_error('authorizedPersonQatarIdFront'), qp.field_error_text('authorizedPersonQatarIdFront')
        assert 'qid-front.jpg' in qp.attached_file_names('authorizedPersonQatarIdFront'), "file not shown attached"
    with allure.step("Complete the rest and Submit (QCTEST identity, QA inbox)"):
        qp.submit_and_wait_response()
    with allure.step("Submission accepted"):
        assert qp.has_submission_succeeded(), f"not accepted; toast={qp.toast_text(2000)!r} captcha={qp.captcha_error_text()!r}"
    pytest.skip("Web half PASSED. 'stored with the record' needs a Control_Panel read of the QCTEST-146733 "
                "submission; that half is not verified by this Web test.")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 5 - Supporting Documents")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that a missing Qatar ID Front blocks submission')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146734
@pytest.mark.traceability("146734")
@allure.label("pbi", "130718")
@allure.label("testcase", "146734")
@anon()
def test_146734_a_missing_qatar_id_front_blocks_submission(page, tmp_path):
    """Verify that a missing Qatar ID Front blocks submission

    Steps (case is the oracle):
    1. Open Step 5 attaching letter and ID back only -> Step 5 displayed
    2. Pass CAPTCHA -> Others attached
    3. Click Submit -> Inline required error under ID Front; nothing stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146734, 5, 'authorizedPersonQatarIdFront', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 5 - Supporting Documents")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the Qatar ID Front upload rejects 'qid-front.png'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146735
@pytest.mark.traceability("146735")
@allure.label("pbi", "130718")
@allure.label("testcase", "146735")
@anon()
def test_146735_qatar_id_front_upload_rejects_qid_front_png(page, tmp_path):
    """Verify that the Qatar ID Front upload rejects 'qid-front.png'

    Steps (case is the oracle):
    1. Open Step 5 -> Step 5 displayed
    2. Upload qid-front.png -> Inline file-type error; file not attached
    3. Click Submit -> Submit blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_type_rejected(qp, files, 146735, 5, 'authorizedPersonQatarIdFront', 'qid-front.png', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 5 - Supporting Documents")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the Qatar ID Front upload enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146736
@pytest.mark.traceability("146736")
@allure.label("pbi", "130718")
@allure.label("testcase", "146736")
@anon()
def test_146736_qatar_id_front_upload_enforces_the_5_mb_limit_4_99_mb_accept(page, tmp_path):
    """Verify that the Qatar ID Front upload enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)

    Steps (case is the oracle):
    1. Open Step 5 -> Step 5 displayed
    2. Upload qidf-4_99mb.jpg (4.99 MB) -> 4.99 MB accepted
    3. Replace with qidf-5_01mb.jpg (5.01 MB) -> 5.01 MB rejected with inline size error
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_size(qp, files, 146736, 5, 'authorizedPersonQatarIdFront', 'qidf-4_99mb.jpg', 'qidf-5_01mb.jpg', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 5 - Supporting Documents")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Qatar ID Back upload accepts 'qid-back.jpg' (500 KB)")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146737
@pytest.mark.traceability("146737")
@allure.label("pbi", "130718")
@allure.label("testcase", "146737")
@anon()
def test_146737_qatar_id_back_upload_accepts_qid_back_jpg_500_kb(page, tmp_path):
    """Verify that the Qatar ID Back upload accepts 'qid-back.jpg' (500 KB)

    Steps (case is the oracle):
    1. Open Step 5 -> Step 5 displayed
    2. Upload qid-back.jpg (500 KB) -> File attached, no error
    3. Complete the rest and Submit -> Submission accepted; back ID stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146737, 5)
    with allure.step("Upload qid-back.jpg"):
        qp.fill(build(5, files, 146737, override={'authorizedPersonQatarIdBack': files.make('qid-back.jpg', 500 * KB)}))
        assert qp.has_no_field_error('authorizedPersonQatarIdBack'), qp.field_error_text('authorizedPersonQatarIdBack')
        assert 'qid-back.jpg' in qp.attached_file_names('authorizedPersonQatarIdBack'), "file not shown attached"
    with allure.step("Complete the rest and Submit (QCTEST identity, QA inbox)"):
        qp.submit_and_wait_response()
    with allure.step("Submission accepted"):
        assert qp.has_submission_succeeded(), f"not accepted; toast={qp.toast_text(2000)!r} captcha={qp.captcha_error_text()!r}"
    pytest.skip("Web half PASSED. 'stored with the record' needs a Control_Panel read of the QCTEST-146737 "
                "submission; that half is not verified by this Web test.")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 5 - Supporting Documents")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that a missing Qatar ID Back blocks submission')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146738
@pytest.mark.traceability("146738")
@allure.label("pbi", "130718")
@allure.label("testcase", "146738")
@anon()
def test_146738_a_missing_qatar_id_back_blocks_submission(page, tmp_path):
    """Verify that a missing Qatar ID Back blocks submission

    Steps (case is the oracle):
    1. Open Step 5 attaching letter and ID front only -> Step 5 displayed
    2. Pass CAPTCHA -> Others attached
    3. Click Submit -> Inline required error under ID Back; nothing stored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_required(qp, files, 146738, 5, 'authorizedPersonQatarIdBack', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 5 - Supporting Documents")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the Qatar ID Back upload rejects 'qid-back.png'")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146739
@pytest.mark.traceability("146739")
@allure.label("pbi", "130718")
@allure.label("testcase", "146739")
@anon()
def test_146739_qatar_id_back_upload_rejects_qid_back_png(page, tmp_path):
    """Verify that the Qatar ID Back upload rejects 'qid-back.png'

    Steps (case is the oracle):
    1. Open Step 5 -> Step 5 displayed
    2. Upload qid-back.png -> Inline file-type error; file not attached
    3. Click Submit -> Submit blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_type_rejected(qp, files, 146739, 5, 'authorizedPersonQatarIdBack', 'qid-back.png', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 5 - Supporting Documents")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the Qatar ID Back upload enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146740
@pytest.mark.traceability("146740")
@allure.label("pbi", "130718")
@allure.label("testcase", "146740")
@anon()
def test_146740_qatar_id_back_upload_enforces_the_5_mb_limit_4_99_mb_accepte(page, tmp_path):
    """Verify that the Qatar ID Back upload enforces the 5 MB limit (4.99 MB accepted, 5.01 MB rejected)

    Steps (case is the oracle):
    1. Open Step 5 -> Step 5 displayed
    2. Upload qidb-4_99mb.jpg (4.99 MB) -> 4.99 MB accepted
    3. Replace with qidb-5_01mb.jpg (5.01 MB) -> 5.01 MB rejected with inline size error
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_size(qp, files, 146740, 5, 'authorizedPersonQatarIdBack', 'qidb-4_99mb.jpg', 'qidb-5_01mb.jpg', cru='qfc')


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that a file named 'qid.jpg.exe' is rejected on the Qatar ID upload")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146815
@pytest.mark.traceability("146815")
@allure.label("pbi", "130718")
@allure.label("testcase", "146815")
@anon()
def test_146815_a_file_named_qid_jpg_exe_is_rejected_on_the_qatar_id_upload(page, tmp_path):
    """Verify that a file named 'qid.jpg.exe' is rejected on the Qatar ID upload

    Steps (case is the oracle):
    1. Open Step 5 -> Step 5 displayed
    2. Upload qid.jpg.exe as ID Front -> Inline file-type error; file not attached; Submit blocked
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    run_file_type_rejected(qp, files, 146815, 5, 'authorizedPersonQatarIdFront', 'qid.jpg.exe', cru='qfc')
