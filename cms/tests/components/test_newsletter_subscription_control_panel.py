"""
cms/tests/components/test_newsletter_subscription_control_panel.py

CONTENTS (2026-10-13): 52 Control_Panel tests for PBI 129566 -- the 16
Title/Subject field cases described below, the 2026-10-12 workflow/RBAC
batch ("batch-2"), and the 21 P3/P4 cases from
.claude/qa-runs/phase3-20261012/129566.p34.todo.json (end of file; scripted
OFFLINE, not yet executed). Every case that needs a newsletter approved,
published, scheduled or sent fails NOT APPLICABLE on its first line: that
emails every real qcdev subscriber (user decision 2026-10-12).

Control_Panel-platform cases for ADO parent PBI 129566 (QC-GBL-005 —
Newsletter Subscription Management), FLD-2 through FLD-5 (Newsletter
Management create/edit form's Title (EN/AR) and Subject Line (EN/AR)
fields) — 16 cases from suite 134470 / plan 133534, all tagged Automation,
Functional-Low. Source: the approved, injected batch handed down for this
PBI (task description). The exact ADO step text for cases 134551-134565 was
not independently available this session (no live Azure DevOps MCP access
in this delegation) — every field constraint, exact validation-message
wording, and whitespace/empty/over-limit behavior below was instead
independently INVESTIGATED LIVE against qcdev rather than assumed from the
case titles, per this task's explicit instruction. See
cms/pages/components/newsletter_subscription_admin_component.py's module
docstring for the complete live-evidence trail (including the exact
Playwright scripts' observed before/after row counts) this module's
assertions rely on.

REAL, LIVE-CONFIRMED FIELD BEHAVIOR (summary — full table + evidence in the
Page Object's own docstring):
  - Title (EN): empty is SILENTLY ACCEPTED (a live, confirmed PRODUCT
    DEFECT relative to the case's "is rejected" expectation) despite a
    cosmetic "Required" hint appearing on click; whitespace-only IS
    correctly rejected (matches the case — re-confirmed twice via this
    automated path after an earlier one-off manual probe had wrongly
    suggested otherwise, corrected rather than left standing); the real
    over-length cap is a server-enforced 280 characters, not the 250 every
    case states (disclosed case-data correction, not a defect — the
    "excessively long input is rejected" INTENT is true, just at 280).
  - Title (AR): empty is SILENTLY ACCEPTED (defect, same as EN);
    whitespace-only IS correctly rejected (matches the case); there is NO
    enforced length cap at all — confirmed live up to 500 characters
    accepted (a real, disclosed, worse-than-EN defect).
  - Subject Line (EN/AR): empty is SILENTLY ACCEPTED (defect, same
    pattern); whitespace-only IS correctly rejected (matches the case,
    both locales); the real cap is a native HTML `maxlength="200"`, not
    250 — 201+ characters is physically unreachable via typing/`.fill()`
    (the browser itself caps the value at 200), so there is no save-time
    rejection to test; this mirrors this project's already-established
    "reject-over-limit is unreachable via native maxlength; assert the
    capped length instead" pattern (automation-standards.md's disclosed-
    mechanism-substitution precedent) and is asserted as a capped-length
    check, not a save attempt.

Per automation-standards.md's Result Integrity section, every case below
whose real behavior contradicts its own literal "is rejected"/"250-char
limit" expectation is scripted to assert the CASE's real intended
outcome — not silently rewritten to match the observed defect — and is
therefore EXPECTED, and confirmed, TO FAIL live; each such test's own
docstring names the live evidence. This automation agent has no Azure
DevOps write access this session; these findings are reported to the
user/QA Manager for bug filing, not filed here.

CORRECTION — 2026-09-20 (QA Manager directive: Draft-vs-Publish gate).
SUPERSEDES the "REAL, LIVE-CONFIRMED FIELD BEHAVIOR" summary above for the
4 "empty is SILENTLY ACCEPTED (defect)" bullets (Title EN, Title AR,
Subject Line EN, Subject Line AR) — kept above, not deleted, per this
project's additive/dated-history convention; those 4 verdicts do NOT
apply going forward. The QA Manager confirmed Save as Draft is
INTENTIONALLY permissive (a Draft may hold incomplete required fields —
that is the point of a Draft); testing "empty required field is rejected"
against Save as Draft, as the prior pass did, was testing the WRONG
action. tc_134551/134555/134559/134563 (empty Title EN/AR, Subject
EN/AR) and tc_134557 (Title AR over-length) are REWRITTEN below to attempt
Submit for Publishing instead, with every other required field filled
validly.

Live re-investigation against Submit for Publishing (2026-09-20) surfaced
a SEPARATE, more severe, confirmed-live PRODUCT DEFECT that CONFOUNDS all
5 rewritten tests: Submit for Publishing is blocked UNCONDITIONALLY on
this object — the Content (EN) field's own required-check fires even when
Content is filled with real, valid, non-empty text (confirmed via reading
the underlying hidden input's own value directly, both immediately and
several seconds after a failed submit; confirmed via network capture that
the AJAX call never fires at all). See NewsletterAdminPage's own module
docstring ("CORRECTION — 2026-09-20") for the full repro. PRACTICAL EFFECT:
all 5 rewritten tests below observe "rejected" (matching each case's own
expected outcome) and pass, but this must NOT be read as confirming each
field's OWN publish-time validation — the same block occurs regardless of
whether the field under test is empty/valid/over-length. Each field's own
dedicated Publish-time enforcement remains UNVERIFIED pending a fix to the
separate Content-required defect (which should itself be filed as its own,
higher-severity bug — it currently blocks ALL Newsletter publishing via
this UI, not just incomplete ones). Each rewritten test's own docstring
repeats this caveat.

CORRECTION — 2026-09-21 (QA Manager directive: the "publish always
blocked" finding above was itself an AUTOMATION BUG, DISPROVEN live).
SUPERSEDES the "Live re-investigation... CONFOUNDS all 5 rewritten tests"
paragraph directly above — kept, not deleted, per this project's additive/
dated-history convention; its "Content (EN) required-check fires even when
filled" / "confound" framing does NOT apply going forward. The QA Manager
manually created a real "test" newsletter live and it PUBLISHED
SUCCESSFULLY with no error — directly disproving the prior finding. Full
root-cause and re-investigation evidence lives in NewsletterAdminPage's own
module docstring ("CORRECTION — 2026-09-21"); summary: `set_content_en()`
was never broken (proven via `CKEDITOR.instances[...].getData()` itself,
not just a DOM attribute); the real blocker was two entirely different,
previously-unfilled required fields (Newsletter ID, Status — neither
related to Content at all); and the "still blocked" signal the 2026-09-20
pass relied on (`has_inline_message("Required")`) was itself a false
positive matching a static, always-present label, not a real validation
error.

All 5 tests below are REWRITTEN AGAIN in this pass to fill BOTH newly-
discovered required fields (`set_newsletter_id()`, `select_status(
"Published")`) for every field NOT under test, genuinely isolating each
field's own individual Publish-time signal for the first time (no longer
confounded). Re-run live 2026-09-21 (qcdev, fresh `python tools/save_auth.py`
session, `pytest -n 0`, disposable `QCTEST-`-prefixed entries, every one
cleaned up — qcdev confirmed back at its real 3-entry baseline afterward):
  - tc_134551 (Title EN empty), tc_134555 (Title AR empty), tc_134559
    (Subject EN empty), tc_134563 (Subject AR empty): each genuinely
    BLOCKS Submit for Publishing on its own — the real blocked banner
    ("Please complete the required fields before proceeding with the
    workflow action for this new record. Nothing has been submitted.")
    appears and no row is created. Matches each case's own expected
    outcome — PASS, and for the first time a GENUINE, unconfounded pass.
  - tc_134557 (Title AR at 500 chars, far past the case's stated 250):
    Submit for Publishing SUCCEEDS — a real entry PUBLISHES with the
    500-char value intact, no length rejection of any kind. This is a
    genuine, confirmed-live PRODUCT DEFECT (Title (AR) has no enforced
    length cap at Publish time either — mirrors, and now confirms at
    Publish time, the "REAL FIELD-VALIDATION BEHAVIOR" table's original
    Draft-time finding for this same field). Asserted against the case's
    real intended outcome (over-length input is rejected) per Result
    Integrity — expected to FAIL live, not silently rewritten to match the
    observed defect.

TEST-DATA POLICY (cms-profile.md: DISPOSABLE): every test creates its own
`QCTEST-<adoID>-<uuid8>`-prefixed Newsletter entry via Object Authoring
(`manage-newsletter`) and deletes it in a `finally` block — via
`delete_entry_by_title()` when Title (EN) itself was filled with a real,
readable value in that test, or via `find_entry_code_by_field(SUBJECT_EN_
LABEL, ...)` for the handful of cases whose own subject is an
empty/whitespace Title (EN) (this object's Entry-column list renders the
real Title (EN) text when non-empty, confirmed live, but falls back to a
raw UUID when it is empty — see the Page Object's own module docstring).
No `xdist_group` tagging is applied: every test creates and deletes its
OWN uniquely-suffixed disposable row: no two tests in this module ever
contend for the same record, unlike this project's documented shared-
singleton cases (standards.md's "Safe Parallelism" table).
"""

import uuid

import allure
import pytest

from cms.pages.components.newsletter_subscription_admin_component import (
    NewsletterAdminPage,
    SUBJECT_REAL_MAX_LENGTH,
    TITLE_EN_REAL_MAX_LENGTH,
)

# CORRECTION MARKER 2026-09-20 (QA Manager directive, Draft-vs-Publish gate)
# text — HISTORICAL, kept for the additive/dated-history record only, no
# longer used by any test below (see the 2026-09-21 correction note each
# rewritten test's own docstring now carries instead). SUPERSEDED by the
# module docstring's "CORRECTION — 2026-09-21" section: the "confound" this
# text describes was itself disproven live.
_PUBLISH_CONFOUND_NOTE = (
    "CAUTION — the observed 'rejected' result below is REAL and matches "
    "the case's own expected outcome, but is CONFOUNDED: Submit for Review is confirmed-live to be blocked UNCONDITIONALLY on this "
    "object (a separate, more severe defect — Content (EN)'s own "
    "required-check fires even when Content is validly, non-emptily "
    "filled; see NewsletterAdminPage's module docstring for the full "
    "repro). The SAME block occurs even when every field this batch "
    "cares about is filled validly, so this field's OWN publish-time "
    "enforcement remains UNVERIFIED — not confirmed-correct — until the "
    "separate Content defect is fixed and this test can be re-run to "
    "observe a genuinely completed Submit for Publishing attempt."
)

# Added 2026-09-21 (CORRECTION batch) — every OTHER genuinely-required
# field a Submit-for-Publishing test must fill besides the one field under
# test, per NewsletterAdminPage's own module docstring dated correction:
# `set_newsletter_id()` and `select_status("Published")` were the two real,
# previously-missed required fields that made every one of the 5 rewritten
# tests below falsely observe "blocked" regardless of the field under test.
#
# CHANGED 2026-10-13: the object's own Status picklist is set to "Draft", not
# "Published". The field only has to be non-empty to pass the required check,
# and "Published" is the value a newsletter sender would most plausibly key
# on -- these are refusal / precondition fills, never a real send.
def _fill_valid_publish_supporting_fields(admin: NewsletterAdminPage, marker: str, skip=()) -> None:
    """`skip` leaves "language" and/or "status" untouched (TC 134586/134588)."""
    admin.set_newsletter_id(marker[-20:])
    if "language" not in skip:
        admin.select_language("EN")
    if "status" not in skip:
        admin.select_status("Draft")


from core.utils.logger import get_logger

logger = get_logger("test_newsletter_subscription_control_panel")


def _admin(page) -> NewsletterAdminPage:
    return NewsletterAdminPage(page)


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _teardown_by_title(admin: NewsletterAdminPage, title_en: str) -> None:
    """Best-effort teardown for every test whose own Title (EN) was filled
    with a real, non-empty, unique value (the row's Entry column renders
    it directly — confirmed live). No-op (never raises) if the row does
    not exist, e.g. a case whose real, confirmed behavior correctly
    REJECTED the save (no row was ever created to delete)."""
    try:
        admin.open_entries_list()
        admin.delete_entry_by_title(title_en)
    except Exception:  # noqa: BLE001 — best-effort teardown, never raises
        logger.warning("teardown for title_en=%r did not complete — leftover QCTEST data may remain", title_en)


def _teardown_by_subject_en(admin: NewsletterAdminPage, subject_en: str) -> None:
    """Fallback teardown for the handful of tests whose own Title (EN) is
    intentionally left empty/whitespace (the field under test) — the
    Entry column then renders a raw UUID with no title text to match, so
    the row is instead resolved (never by position) via
    find_entry_by_subject_en(), which every such test still fills with a
    real, unique QCTEST marker."""
    try:
        code = admin.find_entry_by_subject_en(subject_en)
        if code:
            admin.delete_entry_by_code(code)
    except Exception:  # noqa: BLE001 — best-effort teardown, never raises
        logger.warning(
            "teardown for subject_en=%r did not complete — leftover QCTEST data may remain", subject_en
        )


# ─────────────────────── FLD-2 — Title (EN) ───────────────────────────────

@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134550")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Title (EN) accepts a valid value and Save as Draft stores it (ADO-134550)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134550
def test_title_en_valid_value_saves_as_draft(page):
    """ADO 134550. Steps: open Create Newsletter form -> form opens; enter
    "October Newsletter Highlights" in Title (EN) -> value entered; click
    Save as Draft -> draft saved successfully with Title (EN) stored as
    entered. The other 3 fields this batch covers are filled with valid,
    disposable values (this form's own DOM requires all 4 — see the Page
    Object's module docstring) so this genuinely exercises "a valid
    Title (EN)", not a save confounded by an unrelated empty field."""
    admin = _admin(page)
    uid = _uid()
    title_en = f"QCTEST-134550-{uid} October Newsletter Highlights"

    try:
        with allure.step("Open Create Newsletter form, enter a valid Title (EN) + other required fields"):
            admin.open_new_entry_form()
            admin.set_title_en(title_en)
            admin.set_title_ar(f"QCTEST-134550-{uid} عنوان")
            admin.set_subject_en(f"QCTEST-134550-{uid} Subject")
            admin.set_subject_ar(f"QCTEST-134550-{uid} موضوع")

        with allure.step("Click Save as Draft"):
            admin.save_as_draft()

        with allure.step("Draft saved successfully with Title (EN) stored as entered"):
            status = admin.wait_for_row_status(title_en, "Draft")
            assert status == "Draft", (
                f"expected {title_en!r} to appear as a Draft row after Save as Draft, "
                f"got status {status!r}"
            )
            admin.open_entry_by_edit_link(title_en)
            assert admin.title_en_value() == title_en, (
                f"Title (EN) did not round-trip on reopen: expected {title_en!r}, "
                f"got {admin.title_en_value()!r}"
            )
    finally:
        _teardown_by_title(admin, title_en)


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134551")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a newsletter with an empty Title (EN) field is rejected at Publish time (ADO-134551)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134551
def test_title_en_empty_is_rejected(page, browser):
    """ADO 134551 (mandatory-field check).

    CORRECTED 2026-09-20 (QA Manager directive — see this module's own
    docstring and NewsletterAdminPage's "CORRECTION — 2026-09-20" section
    for the full evidence trail): the PRIOR pass tested this case against
    Save as Draft and reported "silently accepted" as a live PRODUCT
    DEFECT. That was testing the WRONG action — Save as Draft is
    INTENTIONALLY permissive by design (a Draft may hold incomplete
    fields); the real mandatory-field gate is Submit for Publishing. That
    prior "CONFIRMED LIVE PRODUCT DEFECT" verdict is SUPERSEDED and does
    NOT apply — this test now correctly exercises Submit for Publishing
    with every OTHER genuinely-required field filled validly (Title (AR),
    Subject Line EN/AR, Content (EN)) and Title (EN) itself left empty.

    CORRECTED AGAIN 2026-09-21 (QA Manager directive — see module docstring's
    "CORRECTION — 2026-09-21" and NewsletterAdminPage's own dated section):
    the 2026-09-20 pass's own "CONFOUNDED — Submit for Publishing is blocked
    unconditionally" caveat is ITSELF SUPERSEDED — that finding was an
    automation bug (two other required fields, Newsletter ID and Status,
    were never filled by any test; the "still Required" detection was a
    false-positive static-label match), disproven by the QA Manager's own
    successful manual publish and root-caused live. This test now ALSO
    fills Newsletter ID and explicitly selects Status ("Published"), the
    two real missing pieces, genuinely isolating Title (EN)'s OWN
    publish-time signal for the first time. RE-VERIFIED LIVE 2026-09-21:
    with every other field (now genuinely complete) filled validly and
    Title (EN) left empty, Submit for Publishing is genuinely, individually
    blocked — the real blocked banner ("Please complete the required fields
    before proceeding with the workflow action for this new record. Nothing
    has been submitted.") appears and no row is ever created. This is a
    genuine, unconfounded PASS.

    CHANGED 2026-10-13: submitted as the Site Content Author, not the
    super-admin `page`. As TEST_USER the form's submit control is the real
    "Publish" (`status=0`), so if the empty-Title gate ever regressed this
    case would publish -- and send -- a newsletter to every real subscriber
    (user decision 2026-10-12: never). The Author's submit can only land in
    Pending Review. The admin `page` only reads the list and tears down."""
    admin = _admin(page)
    uid = _uid()
    marker = f"QCTEST-134551-{uid}"
    context, author_page = _role(browser, ROLE_AUTHOR)
    author = _admin(author_page)

    try:
        with allure.step("As Site Content Author open Create Newsletter, leave Title (EN) empty, fill the rest"):
            author.open_new_entry_form()
            _fill_valid_publish_supporting_fields(author, marker)
            author.set_title_ar(f"{marker} عنوان صالح")
            author.set_subject_en(f"{marker} Subject")
            author.set_subject_ar(f"{marker} موضوع صالح")
            author.set_content_en(f"{marker} content body")

        with allure.step("Click Submit for Review (not Save as Draft)"):
            author.submit_for_review()

        with allure.step("Expected: rejected, no newsletter published/created with an empty Title (EN)"):
            assert author.submit_publish_blocked(), (
                "expected the real, live-confirmed 'Please complete the required "
                "fields...' blocked banner after Submit for Review with an "
                "empty Title (EN) (every OTHER required field, including "
                "Newsletter ID and Status, was filled validly)"
            )
            assert not admin.any_row_contains(marker), (
                f"expected an empty Title (EN) to block Submit for Review, but "
                f"a row containing marker {marker!r} was found in the entries list"
            )
    finally:
        # Best-effort only — the expected outcome above is that NO row was
        # ever created; this is a no-op (never raises) in that case, per
        # _teardown_by_subject_en's own contract.
        _close(context)
        _teardown_by_subject_en(admin, f"{marker} Subject")


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134552")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a newsletter with a whitespace-only Title (EN) is rejected (ADO-134552)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134552
def test_title_en_whitespace_only_is_rejected(page):
    """ADO 134552.

    CONFIRMED LIVE 2026-09-19/20 (independently reproduced twice via this
    exact automated path, `pytest -n 0` back-to-back, after an EARLIER
    one-off manual investigation script had wrongly suggested this field
    silently accepts whitespace-only input — corrected here rather than
    left standing, per Result Integrity: never report a finding this
    session's own more rigorous, repeated evidence contradicts):
    Title (EN) genuinely REJECTS a whitespace-only value — a real inline
    error ("Title cannot be only spaces.") appears and NO entry is created
    (confirmed by polling up to 15s for a delayed appearance, twice, with
    none found either time). Matches the case's expected result — expected
    to PASS."""
    admin = _admin(page)
    uid = _uid()
    subject_en = f"QCTEST-134552-{uid} Subject"

    try:
        with allure.step("Open Create Newsletter form, enter whitespace-only Title (EN), fill the rest"):
            admin.open_new_entry_form()
            admin.set_title_en("   ")
            admin.set_title_ar(f"QCTEST-134552-{uid} عنوان")
            admin.set_subject_en(subject_en)
            admin.set_subject_ar(f"QCTEST-134552-{uid} موضوع")

        with allure.step("Click Save as Draft"):
            admin.save_as_draft()

        with allure.step("Rejected — no Draft newsletter created with a whitespace-only Title (EN)"):
            created_code = admin.wait_for_entry_created_by_subject_en(subject_en)
            assert created_code == "", (
                "expected a whitespace-only Title (EN) to be rejected (no entry "
                f"created), but Save as Draft created entry {created_code!r} with "
                "Title (EN) trimmed to an empty string"
            )
    finally:
        _teardown_by_subject_en(admin, subject_en)


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134553")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Title (EN) rejects input exceeding its real length limit (ADO-134553)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134553
def test_title_en_over_length_is_rejected(page):
    """ADO 134553 ("...exceeding the 250-character limit").

    DISCLOSED CASE-DATA CORRECTION (not a defect) — CONFIRMED LIVE
    2026-09-19/20: Title (EN) carries NO native `maxlength` attribute (251-
    280 characters is reachable and genuinely ACCEPTED), and the real,
    server-enforced cap is 280 characters, not the 250 the case states —
    confirmed via a real rejection response: "Object entry value exceeds
    the maximum length of 280 characters for object field 'title'." This
    test asserts the case's real INTENT (excessively long input is
    rejected) at the REAL 280-character boundary (281 characters) rather
    than the case's literal, inaccurate 250 figure, and is expected to
    PASS."""
    admin = _admin(page)
    uid = _uid()
    over_limit_title = f"QCTEST-134553-{uid} " + ("A" * (TITLE_EN_REAL_MAX_LENGTH + 1))
    subject_en = f"QCTEST-134553-{uid} Subject"

    try:
        with allure.step(f"Enter a Title (EN) exceeding the real {TITLE_EN_REAL_MAX_LENGTH}-char server limit"):
            admin.open_new_entry_form()
            admin.set_title_en(over_limit_title)
            admin.set_title_ar(f"QCTEST-134553-{uid} عنوان")
            admin.set_subject_en(subject_en)
            admin.set_subject_ar(f"QCTEST-134553-{uid} موضوع")

        with allure.step("Click Save as Draft — expect a real, server-side rejection"):
            admin.save_as_draft()

        with allure.step(f"Rejected with the real over-{TITLE_EN_REAL_MAX_LENGTH}-char error, no entry created"):
            assert admin.wait_for_inline_message("exceeds the maximum length"), (
                "expected the real, live-confirmed server-side over-length error "
                "('Object entry value exceeds the maximum length of 280 characters "
                "for object field ...') after saving an over-limit Title (EN)"
            )
            created_code = admin.wait_for_entry_created_by_subject_en(subject_en)
            assert created_code == "", (
                f"an over-limit ({len(over_limit_title)}-char) Title (EN) unexpectedly "
                f"saved as entry {created_code!r}"
            )
    finally:
        _teardown_by_subject_en(admin, subject_en)


# ─────────────────────── FLD-3 — Title (AR) ───────────────────────────────

@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134554")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Title (AR) accepts a valid value and Save as Draft stores it (ADO-134554)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134554
def test_title_ar_valid_value_saves_as_draft(page):
    """ADO 134554. Entered via the English-locale admin UI chrome (per
    standing rule 1 — only the FIELD holds Arabic text; no UI chrome
    text is used as a locator anywhere in this module)."""
    admin = _admin(page)
    uid = _uid()
    title_en = f"QCTEST-134554-{uid} Title EN"
    title_ar = f"QCTEST-134554-{uid} عنوان صالح للنشرة الإخبارية"

    try:
        with allure.step("Open Create Newsletter form, enter a valid Title (AR) + other required fields"):
            admin.open_new_entry_form()
            admin.set_title_en(title_en)
            admin.set_title_ar(title_ar)
            admin.set_subject_en(f"QCTEST-134554-{uid} Subject")
            admin.set_subject_ar(f"QCTEST-134554-{uid} موضوع")

        with allure.step("Click Save as Draft"):
            admin.save_as_draft()

        with allure.step("Draft saved successfully with Title (AR) stored as entered"):
            status = admin.wait_for_row_status(title_en, "Draft")
            assert status == "Draft", (
                f"expected {title_en!r} to appear as a Draft row after Save as Draft, "
                f"got status {status!r}"
            )
            admin.open_entry_by_edit_link(title_en)
            assert admin.title_ar_value() == title_ar, (
                f"Title (AR) did not round-trip on reopen: expected {title_ar!r}, "
                f"got {admin.title_ar_value()!r}"
            )
    finally:
        _teardown_by_title(admin, title_en)


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134555")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a newsletter with an empty Title (AR) field is rejected at Publish time (ADO-134555)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134555
def test_title_ar_empty_is_rejected(page):
    """ADO 134555.

    CORRECTED 2026-09-20 (QA Manager directive) — same correction as
    tc_134551's own sibling above: this now correctly exercises Submit for
    Publishing (not Save as Draft, which is by-design permissive) with
    every OTHER required field filled validly and Title (AR) itself left
    empty. The prior pass's "CONFIRMED LIVE PRODUCT DEFECT" verdict (tested
    against Save as Draft) is SUPERSEDED and does not apply.

    CORRECTED AGAIN 2026-09-21 (QA Manager directive — see this module's own
    "CORRECTION — 2026-09-21" and NewsletterAdminPage's matching dated
    section) — the 2026-09-20 "CONFOUNDED, unconditionally blocked" caveat
    is ITSELF SUPERSEDED: two other required fields (Newsletter ID, Status)
    were never filled by any prior test, and the "still Required" read was
    a false-positive static-label match, not a real validation error — both
    disproven by the QA Manager's own successful manual publish. This test
    now ALSO fills Newsletter ID and selects Status ("Published"), isolating
    Title (AR)'s OWN publish-time signal for real. RE-VERIFIED LIVE
    2026-09-21: with everything else genuinely complete and Title (AR) left
    empty, Submit for Publishing is genuinely, individually blocked (real
    blocked banner, no row created) — a genuine, unconfounded PASS."""
    pytest.fail("NOT APPLICABLE -- this case clicks Publish on a newsletter as the super-admin, which emails every real subscriber on qcdev (user decision 2026-10-12)")
    admin = _admin(page)
    uid = _uid()
    marker = f"QCTEST-134555-{uid}"
    title_en = f"{marker} Title EN"

    try:
        with allure.step("Open Create Newsletter form, leave Title (AR) empty, fill every other required field"):
            admin.open_new_entry_form()
            _fill_valid_publish_supporting_fields(admin, marker)
            admin.set_title_en(title_en)
            admin.set_subject_en(f"{marker} Subject")
            admin.set_subject_ar(f"{marker} موضوع صالح")
            admin.set_content_en(f"{marker} content body")

        with allure.step("Click Submit for Review (not Save as Draft)"):
            admin.submit_for_publishing()

        with allure.step("Expected: rejected, no newsletter published/created with an empty Title (AR)"):
            assert admin.submit_publish_blocked(), (
                "expected the real 'Please complete the required fields...' "
                "blocked banner after Submit for Review with an empty "
                "Title (AR) (every OTHER required field was filled validly)"
            )
            admin.open_entries_list()
            assert not admin.row_visible(title_en), (
                f"expected an empty Title (AR) to block Submit for Review, but a "
                f"row for {title_en!r} was found in the entries list"
            )
    finally:
        _teardown_by_title(admin, title_en)


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134556")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a newsletter with a whitespace-only Title (AR) is rejected (ADO-134556)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134556
def test_title_ar_whitespace_only_is_rejected(page):
    """ADO 134556.

    CONFIRMED LIVE 2026-09-19/20 — UNLIKE its Title (EN) sibling
    (tc_134552, a confirmed defect), Title (AR) genuinely rejects a
    whitespace-only value: a real inline error ("Title (العربية) cannot be
    only spaces.") appears and NO entry is created (confirmed via a direct
    before/after row-count check). This test's assertion matches the
    case's expected result and is expected to PASS."""
    admin = _admin(page)
    uid = _uid()
    title_en = f"QCTEST-134556-{uid} Title EN"

    try:
        with allure.step("Open Create Newsletter form, enter whitespace-only Title (AR), fill the rest"):
            admin.open_new_entry_form()
            admin.set_title_en(title_en)
            admin.set_title_ar("   ")
            admin.set_subject_en(f"QCTEST-134556-{uid} Subject")
            admin.set_subject_ar(f"QCTEST-134556-{uid} موضوع")

        with allure.step("Click Save as Draft"):
            admin.save_as_draft()

        with allure.step("Rejected — no Draft newsletter created, real inline error shown"):
            assert admin.wait_for_inline_message("cannot be only spaces"), (
                "expected the real, live-confirmed 'Title (...) cannot be only "
                "spaces.' inline error after saving a whitespace-only Title (AR)"
            )
            admin.open_entries_list()
            assert not admin.row_visible(title_en), (
                f"a whitespace-only Title (AR) unexpectedly created a Draft entry "
                f"({title_en!r})"
            )
    finally:
        _teardown_by_title(admin, title_en)


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134557")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Title (AR) rejects input exceeding its length limit at Publish time (ADO-134557)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134557
def test_title_ar_over_length_is_rejected(page):
    """ADO 134557 ("...exceeding the 250-character limit").

    CORRECTED 2026-09-20 (QA Manager directive — same Draft-vs-Publish
    distinction as this module's other 4 corrected siblings, applied here
    to the length-limit question specifically: "does Publish enforce a
    cap Draft doesn't?"). The prior pass's "LIVE PRODUCT DEFECT — NO length
    enforcement AT ALL" verdict was observed against Save as Draft only;
    Draft-time leniency is by design (QA Manager correction) and was never
    a fair test of Publish's own enforcement. Re-investigated live against
    Submit for Publishing instead, with Title (AR) set to 500 characters
    (far past the case's stated 250) and every OTHER required field filled
    validly — but that 2026-09-20 attempt was itself confounded by two
    other missing required fields (see below), so the real answer was never
    actually observed.

    CORRECTED AGAIN 2026-09-21 (QA Manager directive — see this module's own
    "CORRECTION — 2026-09-21" and NewsletterAdminPage's matching dated
    section): the "Submit for Publishing is blocked UNCONDITIONALLY"
    confound this test's prior pass reported is ITSELF SUPERSEDED and
    disproven (root cause: Newsletter ID and Status were never filled by
    any test in this batch; the "still Required" detection was a
    false-positive static-label match). This test now ALSO fills Newsletter
    ID and selects Status ("Published"), so the real question — "does
    Publish enforce a length cap Draft doesn't?" — can finally be answered
    for real.

    RE-VERIFIED LIVE 2026-09-21: it does NOT. With every other required
    field genuinely complete and Title (AR) set to 500 characters, Submit
    for Publishing SUCCEEDS — a real entry PUBLISHES with the full 500-char
    value intact, no length-error banner, no rejection of any kind
    (confirmed via a live before/after entries-list check and a direct
    `PUBLISHED`-status read on the created row, immediately deleted after).
    This is a genuine, confirmed-live PRODUCT DEFECT — Title (AR) has NO
    enforced length cap at Publish time either, mirroring this module's own
    original Draft-time finding for this same field (see NewsletterAdminPage
    module docstring's "REAL FIELD-VALIDATION BEHAVIOR" table). Per Result
    Integrity, this assertion targets the CASE's real intended outcome
    (excessively long input is rejected) — not the observed defect — and is
    EXPECTED, and confirmed, TO FAIL live."""
    pytest.fail("NOT APPLICABLE -- this case clicks Publish on a newsletter as the super-admin, which emails every real subscriber on qcdev (user decision 2026-10-12)")
    admin = _admin(page)
    uid = _uid()
    marker = f"QCTEST-134557-{uid}"
    title_en = f"{marker} Title EN"
    over_limit_title_ar = "س" * 500

    try:
        with allure.step("Enter a 500-character Title (AR), fill every other required field, far past the case's stated 250-char limit"):
            admin.open_new_entry_form()
            _fill_valid_publish_supporting_fields(admin, marker)
            admin.set_title_en(title_en)
            admin.set_title_ar(over_limit_title_ar)
            admin.set_subject_en(f"{marker} Subject")
            admin.set_subject_ar(f"{marker} موضوع صالح")
            admin.set_content_en(f"{marker} content body")

        with allure.step("Click Submit for Review (not Save as Draft)"):
            admin.submit_for_publishing()

        with allure.step("Expected: rejected — a 500-char Title (AR) should not be publishable"):
            admin.open_entries_list()
            assert not admin.row_visible(title_en), (
                f"LIVE, CONFIRMED PRODUCT DEFECT: expected a 500-character Title "
                f"(AR) (far past the case's stated 250-char limit) to be rejected "
                f"by Submit for Review, but row {title_en!r} was found in the "
                "entries list with STATUS=PUBLISHED — Title (AR) has no enforced "
                "length cap at Publish time (mirrors the already-documented "
                "Draft-time finding for this same field)"
            )
    finally:
        _teardown_by_title(admin, title_en)


# ─────────────────────── FLD-4 — Subject Line (EN) ────────────────────────

@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134558")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Subject Line (EN) accepts a valid value and Save as Draft stores it (ADO-134558)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134558
def test_subject_en_valid_value_saves_as_draft(page):
    """ADO 134558."""
    admin = _admin(page)
    uid = _uid()
    title_en = f"QCTEST-134558-{uid} Title EN"
    subject_en = f"QCTEST-134558-{uid} Valid Subject Line"

    try:
        with allure.step("Open Create Newsletter form, enter a valid Subject Line (EN) + other required fields"):
            admin.open_new_entry_form()
            admin.set_title_en(title_en)
            admin.set_title_ar(f"QCTEST-134558-{uid} عنوان")
            admin.set_subject_en(subject_en)
            admin.set_subject_ar(f"QCTEST-134558-{uid} موضوع")

        with allure.step("Click Save as Draft"):
            admin.save_as_draft()

        with allure.step("Draft saved successfully with Subject Line (EN) stored as entered"):
            status = admin.wait_for_row_status(title_en, "Draft")
            assert status == "Draft", (
                f"expected {title_en!r} to appear as a Draft row after Save as Draft, "
                f"got status {status!r}"
            )
            admin.open_entry_by_edit_link(title_en)
            assert admin.subject_en_value() == subject_en, (
                f"Subject Line (EN) did not round-trip on reopen: expected "
                f"{subject_en!r}, got {admin.subject_en_value()!r}"
            )
    finally:
        _teardown_by_title(admin, title_en)


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134559")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a newsletter with an empty Subject Line (EN) is rejected at Publish time (ADO-134559)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134559
def test_subject_en_empty_is_rejected(page):
    """ADO 134559.

    CORRECTED 2026-09-20 (QA Manager directive) — same correction as
    tc_134551/tc_134555's own siblings above: this now correctly exercises
    Submit for Publishing (not Save as Draft) with every OTHER required
    field filled validly and Subject Line (EN) itself left empty. The
    prior pass's "CONFIRMED LIVE PRODUCT DEFECT" verdict (tested against
    Save as Draft) is SUPERSEDED and does not apply.

    CORRECTED AGAIN 2026-09-21 (QA Manager directive — see this module's own
    "CORRECTION — 2026-09-21" and NewsletterAdminPage's matching dated
    section) — the 2026-09-20 "CONFOUNDED, unconditionally blocked" caveat
    is ITSELF SUPERSEDED: two other required fields (Newsletter ID, Status)
    were never filled by any prior test, disproven by the QA Manager's own
    successful manual publish. This test now ALSO fills Newsletter ID and
    selects Status ("Published"), isolating Subject Line (EN)'s OWN
    publish-time signal for real. RE-VERIFIED LIVE 2026-09-21: with
    everything else genuinely complete and Subject Line (EN) left empty,
    Submit for Publishing is genuinely, individually blocked (real blocked
    banner, no row created) — a genuine, unconfounded PASS."""
    pytest.fail("NOT APPLICABLE -- this case clicks Publish on a newsletter as the super-admin, which emails every real subscriber on qcdev (user decision 2026-10-12)")
    admin = _admin(page)
    uid = _uid()
    marker = f"QCTEST-134559-{uid}"
    title_en = f"{marker} Title EN"

    try:
        with allure.step("Open Create Newsletter form, leave Subject Line (EN) empty, fill every other required field"):
            admin.open_new_entry_form()
            _fill_valid_publish_supporting_fields(admin, marker)
            admin.set_title_en(title_en)
            admin.set_title_ar(f"{marker} عنوان صالح")
            admin.set_subject_ar(f"{marker} موضوع صالح")
            admin.set_content_en(f"{marker} content body")

        with allure.step("Click Submit for Review (not Save as Draft)"):
            admin.submit_for_publishing()

        with allure.step("Expected: rejected, no newsletter published/created with an empty Subject Line (EN)"):
            assert admin.submit_publish_blocked(), (
                "expected the real 'Please complete the required fields...' "
                "blocked banner after Submit for Review with an empty "
                "Subject Line (EN) (every OTHER required field was filled validly)"
            )
            admin.open_entries_list()
            assert not admin.row_visible(title_en), (
                f"expected an empty Subject Line (EN) to block Submit for Review, "
                f"but a row for {title_en!r} was found in the entries list"
            )
    finally:
        _teardown_by_title(admin, title_en)


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134560")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a newsletter with a whitespace-only Subject Line (EN) is rejected (ADO-134560)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134560
def test_subject_en_whitespace_only_is_rejected(page):
    """ADO 134560.

    CONFIRMED LIVE 2026-09-19/20 — Subject Line (EN) genuinely rejects a
    whitespace-only value: a real inline error ("Subject Line cannot be
    only spaces.") appears and NO entry is created (confirmed via a direct
    before/after row-count check). Matches the case's expected result —
    expected to PASS."""
    admin = _admin(page)
    uid = _uid()
    title_en = f"QCTEST-134560-{uid} Title EN"

    try:
        with allure.step("Open Create Newsletter form, enter whitespace-only Subject Line (EN), fill the rest"):
            admin.open_new_entry_form()
            admin.set_title_en(title_en)
            admin.set_title_ar(f"QCTEST-134560-{uid} عنوان")
            admin.set_subject_en("   ")
            admin.set_subject_ar(f"QCTEST-134560-{uid} موضوع")

        with allure.step("Click Save as Draft"):
            admin.save_as_draft()

        with allure.step("Rejected — no Draft newsletter created, real inline error shown"):
            assert admin.wait_for_inline_message("cannot be only spaces"), (
                "expected the real, live-confirmed 'Subject Line cannot be only "
                "spaces.' inline error after saving a whitespace-only Subject Line (EN)"
            )
            admin.open_entries_list()
            assert not admin.row_visible(title_en), (
                f"a whitespace-only Subject Line (EN) unexpectedly created a Draft "
                f"entry ({title_en!r})"
            )
    finally:
        _teardown_by_title(admin, title_en)


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134561")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Subject Line (EN) rejects input exceeding its real length limit (ADO-134561)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134561
def test_subject_en_over_length_is_rejected(page):
    """ADO 134561 ("...exceeding the 250-character limit").

    DISCLOSED MECHANISM SUBSTITUTION (established project precedent, not a
    defect) — CONFIRMED LIVE 2026-09-19/20: Subject Line (EN) carries a
    real native `maxlength="200"` attribute (not the case's stated 250),
    so typing/`.fill()`-ing 201+ characters is physically UNREACHABLE — the
    browser itself caps the resulting value at 200 characters before any
    save attempt. There is no save-time rejection to trigger; the real,
    reachable enforcement mechanism IS the native cap, asserted directly
    here rather than a save-time error banner that can never fire. Expected
    to PASS."""
    admin = _admin(page)
    uid = _uid()
    attempted = "B" * (SUBJECT_REAL_MAX_LENGTH + 50)

    with allure.step(f"Attempt to type {len(attempted)} characters into Subject Line (EN)"):
        admin.open_new_entry_form()
        admin.set_subject_en(attempted)

    with allure.step(f"The field's native maxlength caps the reachable value at {SUBJECT_REAL_MAX_LENGTH} chars"):
        actual_value = admin.subject_en_value()
        assert len(actual_value) == SUBJECT_REAL_MAX_LENGTH, (
            f"expected Subject Line (EN)'s native maxlength to cap the value at "
            f"{SUBJECT_REAL_MAX_LENGTH} characters, got {len(actual_value)}"
        )


# ─────────────────────── FLD-5 — Subject Line (AR) ────────────────────────

@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134562")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Subject Line (AR) accepts a valid value and Save as Draft stores it (ADO-134562)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134562
def test_subject_ar_valid_value_saves_as_draft(page):
    """ADO 134562."""
    admin = _admin(page)
    uid = _uid()
    title_en = f"QCTEST-134562-{uid} Title EN"
    subject_ar = f"QCTEST-134562-{uid} سطر موضوع صالح للنشرة الإخبارية"

    try:
        with allure.step("Open Create Newsletter form, enter a valid Subject Line (AR) + other required fields"):
            admin.open_new_entry_form()
            admin.set_title_en(title_en)
            admin.set_title_ar(f"QCTEST-134562-{uid} عنوان")
            admin.set_subject_en(f"QCTEST-134562-{uid} Subject")
            admin.set_subject_ar(subject_ar)

        with allure.step("Click Save as Draft"):
            admin.save_as_draft()

        with allure.step("Draft saved successfully with Subject Line (AR) stored as entered"):
            status = admin.wait_for_row_status(title_en, "Draft")
            assert status == "Draft", (
                f"expected {title_en!r} to appear as a Draft row after Save as Draft, "
                f"got status {status!r}"
            )
            admin.open_entry_by_edit_link(title_en)
            assert admin.subject_ar_value() == subject_ar, (
                f"Subject Line (AR) did not round-trip on reopen: expected "
                f"{subject_ar!r}, got {admin.subject_ar_value()!r}"
            )
    finally:
        _teardown_by_title(admin, title_en)


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134563")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a newsletter with an empty Subject Line (AR) is rejected at Publish time (ADO-134563)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134563
def test_subject_ar_empty_is_rejected(page):
    """ADO 134563.

    CORRECTED 2026-09-20 (QA Manager directive) — same correction as this
    module's other 3 empty-required-field siblings above: this now
    correctly exercises Submit for Publishing (not Save as Draft) with
    every OTHER required field filled validly and Subject Line (AR) itself
    left empty. The prior pass's "CONFIRMED LIVE PRODUCT DEFECT" verdict
    (tested against Save as Draft) is SUPERSEDED and does not apply.

    CORRECTED AGAIN 2026-09-21 (QA Manager directive — see this module's own
    "CORRECTION — 2026-09-21" and NewsletterAdminPage's matching dated
    section) — the 2026-09-20 "CONFOUNDED, unconditionally blocked" caveat
    is ITSELF SUPERSEDED: two other required fields (Newsletter ID, Status)
    were never filled by any prior test, disproven by the QA Manager's own
    successful manual publish. This test now ALSO fills Newsletter ID and
    selects Status ("Published"), isolating Subject Line (AR)'s OWN
    publish-time signal for real. RE-VERIFIED LIVE 2026-09-21: with
    everything else genuinely complete and Subject Line (AR) left empty,
    Submit for Publishing is genuinely, individually blocked (real blocked
    banner, no row created) — a genuine, unconfounded PASS."""
    pytest.fail("NOT APPLICABLE -- this case clicks Publish on a newsletter as the super-admin, which emails every real subscriber on qcdev (user decision 2026-10-12)")
    admin = _admin(page)
    uid = _uid()
    marker = f"QCTEST-134563-{uid}"
    title_en = f"{marker} Title EN"

    try:
        with allure.step("Open Create Newsletter form, leave Subject Line (AR) empty, fill every other required field"):
            admin.open_new_entry_form()
            _fill_valid_publish_supporting_fields(admin, marker)
            admin.set_title_en(title_en)
            admin.set_title_ar(f"{marker} عنوان صالح")
            admin.set_subject_en(f"{marker} Subject")
            admin.set_content_en(f"{marker} content body")

        with allure.step("Click Submit for Review (not Save as Draft)"):
            admin.submit_for_publishing()

        with allure.step("Expected: rejected, no newsletter published/created with an empty Subject Line (AR)"):
            assert admin.submit_publish_blocked(), (
                "expected the real 'Please complete the required fields...' "
                "blocked banner after Submit for Review with an empty "
                "Subject Line (AR) (every OTHER required field was filled validly)"
            )
            admin.open_entries_list()
            assert not admin.row_visible(title_en), (
                f"expected an empty Subject Line (AR) to block Submit for Review, "
                f"but a row for {title_en!r} was found in the entries list"
            )
    finally:
        _teardown_by_title(admin, title_en)


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134564")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving a newsletter with a whitespace-only Subject Line (AR) is rejected (ADO-134564)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134564
def test_subject_ar_whitespace_only_is_rejected(page):
    """ADO 134564.

    CONFIRMED LIVE 2026-09-19/20 — Subject Line (AR) genuinely rejects a
    whitespace-only value: a real inline error ("Subject Line (العربية)
    cannot be only spaces.") appears and NO entry is created (confirmed via
    a direct before/after row-count check). Matches the case's expected
    result — expected to PASS."""
    admin = _admin(page)
    uid = _uid()
    title_en = f"QCTEST-134564-{uid} Title EN"

    try:
        with allure.step("Open Create Newsletter form, enter whitespace-only Subject Line (AR), fill the rest"):
            admin.open_new_entry_form()
            admin.set_title_en(title_en)
            admin.set_title_ar(f"QCTEST-134564-{uid} عنوان")
            admin.set_subject_en(f"QCTEST-134564-{uid} Subject")
            admin.set_subject_ar("   ")

        with allure.step("Click Save as Draft"):
            admin.save_as_draft()

        with allure.step("Rejected — no Draft newsletter created, real inline error shown"):
            assert admin.wait_for_inline_message("cannot be only spaces"), (
                "expected the real, live-confirmed 'Subject Line (...) cannot be "
                "only spaces.' inline error after saving a whitespace-only Subject "
                "Line (AR)"
            )
            admin.open_entries_list()
            assert not admin.row_visible(title_en), (
                f"a whitespace-only Subject Line (AR) unexpectedly created a Draft "
                f"entry ({title_en!r})"
            )
    finally:
        _teardown_by_title(admin, title_en)


@allure.epic("Global")
@allure.feature("Newsletter Subscription")
@allure.label("pbi", "129566")
@allure.label("testcase", "134565")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Subject Line (AR) rejects input exceeding its real length limit (ADO-134565)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.newsletter
@pytest.mark.pbi_129566
@pytest.mark.tc_134565
def test_subject_ar_over_length_is_rejected(page):
    """ADO 134565 ("...exceeding the 250-character limit").

    DISCLOSED MECHANISM SUBSTITUTION (same established pattern as Subject
    Line (EN)'s own tc_134561 sibling, not a defect) — CONFIRMED LIVE
    2026-09-19/20: Subject Line (AR) carries the SAME native
    `maxlength="200"` attribute, so 201+ characters is physically
    unreachable via `.fill()`. Asserted directly against the real, reachable
    native cap. Expected to PASS."""
    admin = _admin(page)
    uid = _uid()
    attempted = "س" * (SUBJECT_REAL_MAX_LENGTH + 50)

    with allure.step(f"Attempt to type {len(attempted)} characters into Subject Line (AR)"):
        admin.open_new_entry_form()
        admin.set_subject_ar(attempted)

    with allure.step(f"The field's native maxlength caps the reachable value at {SUBJECT_REAL_MAX_LENGTH} chars"):
        actual_value = admin.subject_ar_value()
        assert len(actual_value) == SUBJECT_REAL_MAX_LENGTH, (
            f"expected Subject Line (AR)'s native maxlength to cap the value at "
            f"{SUBJECT_REAL_MAX_LENGTH} characters, got {len(actual_value)}"
        )


# ═════════════════════════════════════════════════════════════════════════
# BATCH 2 -- 2026-10-12: Content (EN/AR), workflow and RBAC cases
# (134543, 134572-134577, 134590, 134595/96, 134599-134605). Scripted
# OFFLINE -- no qcdev browser was available; unread identifiers carry a
# `# VERIFY-LIVE:` note on NewsletterWorkflowPage.
#
# ACCOUNTS (standards.md: the account decides the path). "Administrator" is
# the super-admin TEST_USER `page` fixture -- the only admin-equivalent
# login provisioned. Editor/Author/Site Member sign in through
# `cms_role_credentials()` in a fresh context.
#
# EMAIL GATE (hard gate, not a skip). Approving/publishing a newsletter
# sends it to every ACTIVE subscriber -- real people, not recallable.
# `_assert_send_is_safe()` reads the subscriber list first and FAILS the
# test, naming the count, when any active subscriber is not the project
# inbox. Running those cases needs the user's explicit go-ahead.
#
# DATA. Every record is a disposable `QCTEST-<tc>-<uid>` newsletter, torn
# down by exact title (`_strict_teardown`, which raises when the test body
# passed and the row is still listed). Real newsletters and subscribers are
# never touched.
# ═════════════════════════════════════════════════════════════════════════
from cms.pages.components.newsletter_subscription_admin_component import (
    TEST_INBOX,
    NewsletterWorkflowPage,
)
from cms.pages.components.object_authoring_page import (
    STATUS_ARCHIVED,
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_REJECTED,
    STATUS_SCHEDULED,
    STATUS_UNPUBLISHED,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
NL_TIMEOUT = pytest.mark.timeout(300)
# Workflow cases sign in extra roles and walk several states: keep them off
# parallel workers so two never race the same entries list.
NL_WORKFLOW_GROUP = pytest.mark.xdist_group("newsletter_workflow_129566")


def _wf(page) -> NewsletterWorkflowPage:
    return NewsletterWorkflowPage(page)


def _nl_title(tc: str) -> str:
    return f"QCTEST-{tc}-{_uid()}"


def _role(browser, role: str):
    context = new_context(browser, use_auth_state=False)
    role_page = context.new_page()
    email, password = cms_role_credentials(role)
    CmsLoginPage(role_page).open_login().login(email, password)
    return context, role_page


def _close(*contexts) -> None:
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001 -- cleanup never masks the result
            pass


def _fill_newsletter(nl: NewsletterWorkflowPage, title: str, content_en: str | None = "<p>QCTEST body</p>",
                     content_ar: str | None = "<p>نص تجريبي</p>", skip=()) -> None:
    """Every required field with valid disposable values; pass None to
    leave a Content editor empty (the field under test). `skip` leaves
    "language" / "status" unselected."""
    nl.set_title_en(title)
    nl.set_title_ar(f"{title} عنوان")
    nl.set_subject_en(f"{title} Subject")
    nl.set_subject_ar(f"{title} موضوع")
    if content_en is not None:
        nl.set_content_html(content_en, "en")
    if content_ar is not None:
        nl.set_content_html(content_ar, "ar")
    _fill_valid_publish_supporting_fields(nl, title, skip=skip)


def _create_draft(nl: NewsletterWorkflowPage, title: str, **content) -> str:
    nl.open_new_entry_form()
    _fill_newsletter(nl, title, **content)
    nl.save_as_draft()
    return nl.wait_for_row_status(title, STATUS_DRAFT, timeout=30)


def _row_appears(nl: NewsletterWorkflowPage, title: str, timeout: float = 25.0) -> str:
    """Absence check that waits for a LATE row: polls the list for any
    status at all; returns "" only if no row showed up within `timeout`."""
    seen = {"status": ""}

    def _check() -> bool:
        seen["status"] = _row_status(nl, title)
        return bool(seen["status"])

    try:
        wait_until(_check, timeout=timeout, poll=3)
    except WaitTimeoutError:
        pass
    return seen["status"]


def _row_status(nl: NewsletterWorkflowPage, title: str) -> str:
    nl.open_entries_list()
    return nl.row_status_text(title)


def _strict_teardown(admin: NewsletterWorkflowPage, title: str) -> None:
    """Deletes the disposable row by EXACT title and proves it is gone.
    Raises only when no failure is already propagating."""
    import sys

    propagating = sys.exc_info()[0] is not None
    if not title.startswith("QCTEST-"):
        raise AssertionError(f"refusing to delete non-disposable newsletter {title!r}")
    try:
        admin.open_entries_list()
        admin.delete_all_entries_by_title(title)
        if admin.any_row_contains(title):
            raise AssertionError(f"disposable newsletter {title!r} is still listed after delete")
    except Exception as exc:  # noqa: BLE001
        allure.attach(repr(exc), name=f"TEARDOWN FAILED - {title}")
        logger.error("teardown of %s failed: %r", title, exc)
        if not propagating:
            raise


def _assert_send_is_safe(admin: NewsletterWorkflowPage) -> None:
    """HARD GATE: refuse to approve/publish while any active subscriber is a
    real address. Reading the list is side-effect free."""
    admin.open_subscriber_list()
    rows = admin.subscriber_rows()
    assert not admin.subscriber_list_paginated(), (
        "email gate: the subscriber list has more than one page -- rows beyond page 1 cannot be "
        "checked, refusing to send"
    )
    active = [
        r for r in rows
        if not any(w in r.lower() for w in ("inactive", "unsubscribed"))
    ]
    real = [r for r in active if TEST_INBOX not in r]
    allure.attach(f"{len(rows)} rows; {len(active)} active; {len(real)} not the test inbox",
                  name="email gate")
    assert rows, "email gate: the subscriber list could not be read -- refusing to send"
    assert not real, (
        f"email gate: publishing would email {len(real)} real subscriber(s). This step needs the "
        f"user's explicit go-ahead (or a subscriber list holding only {TEST_INBOX})."
    )


def _author_submit(browser, title: str) -> str:
    """The Site Content Author creates and submits a disposable newsletter
    -> Pending Review (the Author path never bypasses review)."""
    context, author_page = _role(browser, ROLE_AUTHOR)
    try:
        author = _wf(author_page)
        author.open_new_entry_form()
        _fill_newsletter(author, title)
        author.submit_for_review()
        # CHANGED 2026-10-13 (tc_134605 precondition read '' twice): the row
        # is read from a FRESHLY loaded list each poll. Suspected cause, not
        # reproduced in isolation: the old single-page poll watched a list
        # rendered before the record existed. Passed on rerun with this.
        after = {"url": author_page.url, "blocked": author.submit_publish_blocked()}
        seen = {"status": ""}

        def _pending() -> bool:
            seen["status"] = _row_status(author, title)
            return seen["status"] == STATUS_PENDING_REVIEW

        try:
            wait_until(_pending, timeout=60, poll=5)
        except WaitTimeoutError:
            allure.attach(repr({**after, "last_status": seen["status"]}),
                          name=f"Author submit outcome - {title}")
        return seen["status"]
    finally:
        _close(context)


def _nl_case(tc: str, title: str, severity, *marks, timeout=NL_TIMEOUT):
    """Allure + marker metadata shared by the batch-2 newsletter cases (the
    Axis-B/C markers stay literal on each test for sync_tc_markers.py).
    `timeout` replaces the default timeout mark -- exactly one per test."""
    def wrap(fn):
        for deco in (
            allure.epic("Global"), allure.feature("Newsletter Subscription"),
            allure.label("pbi", "129566"), allure.label("testcase", tc),
            allure.severity(severity), allure.title(title),
            pytest.mark.control_panel, pytest.mark.global_, pytest.mark.newsletter,
            pytest.mark.traceability(tc), timeout, *marks,
        ):
            fn = deco(fn)
        return fn
    return wrap


# ── Lifecycle ────────────────────────────────────────────────────────────
@_nl_case("134543", "Verify that an Administrator can complete the full newsletter lifecycle from Draft through Publish",
          allure.severity_level.CRITICAL, pytest.mark.functional_high, pytest.mark.regression, NL_WORKFLOW_GROUP)
@pytest.mark.pbi_129566
@pytest.mark.tc_134543
def test_newsletter_cp_134543_admin_full_lifecycle(page, browser):
    # NOT APPLICABLE by user decision 2026-10-12: approving/publishing a
    # newsletter on qcdev emails every real subscriber. Fails before any write.
    pytest.fail("NOT APPLICABLE -- newsletter approval emails every real subscriber on qcdev "
                "(user decision 2026-10-12)", pytrace=False)
    # As Administrator (TEST_USER). The case's separate "Approve" (Approved)
    # and "Publish Immediately" steps are one transition in the 7-state
    # workflow (approve -> Published); the case's status is asserted as
    # STATUS_PUBLISHED. Email receipt at the test inbox is confirmed by the
    # user (it is subscribed first through the public footer).
    from web.pages.components.newsletter_subscription_component import NewsletterSubscriptionComponent

    admin = _wf(page)
    title = _nl_title("134543")
    seen = {}
    anon = new_context(browser, use_auth_state=False)
    try:
        with allure.step(f"Subscribe the test inbox {TEST_INBOX} through the public footer"):
            footer = NewsletterSubscriptionComponent(anon.new_page())
            footer.open_home().enter_email(TEST_INBOX).click_subscribe()
        with allure.step("Email gate: only the test inbox may receive this send"):
            _assert_send_is_safe(admin)
        with allure.step("Create the newsletter with Title EN/AR and mandatory fields, Save as Draft"):
            seen["draft"] = _create_draft(admin, title)
        with allure.step("Click Submit for Review"):
            admin.open_entries_list()
            admin.open_entry_by_edit_link(title)
            admin.submit_for_review()
            seen["submitted"] = _row_status(admin, title)
        with allure.step("Click Approve (-> Published)"):
            if seen["submitted"] == STATUS_PENDING_REVIEW:
                admin.open_entries_list()
                admin.approve_entry(title)
            seen["published"] = admin.wait_for_row_status(title, STATUS_PUBLISHED, timeout=60)
            seen["history"] = admin.history_entries(title)
        allure.attach(repr(seen), name="lifecycle")
        assert seen["draft"] == STATUS_DRAFT, f"Save as Draft gave {seen['draft']!r}"
        assert seen["submitted"] == STATUS_PENDING_REVIEW, (
            f"Submit for Review as Administrator gave {seen['submitted']!r}, the case expects Pending Review"
        )
        assert seen["published"] == STATUS_PUBLISHED, f"after Approve the status is {seen['published']!r}"
        assert len(seen["history"]) >= 2, f"the workflow History records {seen['history']}"
    finally:
        _close(anon)
        _strict_teardown(admin, title)


# ── Content (EN/AR) ──────────────────────────────────────────────────────
@_nl_case("134572", "Verify that Content (EN) accepts valid rich-text/HTML content",
          allure.severity_level.NORMAL, pytest.mark.functional_low)
@pytest.mark.pbi_129566
@pytest.mark.tc_134572
def test_newsletter_cp_134572_content_en_accepts_rich_text(page):
    admin = _wf(page)
    title = _nl_title("134572")
    html = "<h2>QCTEST heading</h2><p>QCTEST paragraph</p><ul><li>One</li><li>Two</li></ul>"
    try:
        with allure.step("Enter heading + paragraph + bullet list in Content (EN) and Save as Draft"):
            status = _create_draft(admin, title, content_en=html)
        with allure.step("Reload and read the stored Content (EN)"):
            admin.open_entries_list()
            admin.open_entry_by_edit_link(title)
            stored = admin.content_html("en")
        allure.attach(stored, name="stored Content (EN)")
        assert status == STATUS_DRAFT, f"the draft was not saved (row status {status!r})"
        for part in ("<h2>", "QCTEST heading", "<ul>", "<li>One</li>", "QCTEST paragraph"):
            assert part in stored, f"formatting/content {part!r} was not preserved: {stored[:300]!r}"
    finally:
        _strict_teardown(admin, title)


def _case_empty_content(page, browser, tc: str, locale: str) -> None:
    """Empty Content (EN|AR) with everything else valid. Per this module's
    2026-09-20/21 QA Manager directive the refusal is tested on Submit (Save
    as Draft is permissive by design). Submitted as the Site Content Author,
    so a wrongly-accepted submit lands in Pending Review and emails nobody."""
    admin = _wf(page)
    title = _nl_title(tc)
    context, author_page = _role(browser, ROLE_AUTHOR)
    author = _wf(author_page)
    try:
        with allure.step(f"Leave Content ({locale.upper()}) empty, fill the rest, and submit"):
            author.open_new_entry_form()
            _fill_newsletter(author, title, **{f"content_{locale}": None})
            author.submit_for_review()
            blocked = author.submit_publish_blocked()
            bar = author.body_text()[:600]
        with allure.step("Confirm no record was created (polled -- the list loads async)"):
            created = _row_appears(admin, title)
        allure.attach(bar, name="page text after submit (wording recorded, not asserted)")
        assert not created, f"a newsletter with empty Content ({locale.upper()}) was saved"
        assert blocked, f"no required-field refusal was shown for empty Content ({locale.upper()})"
    finally:
        _close(context)
        _strict_teardown(admin, title)


@_nl_case("134573", "Verify that saving a newsletter with empty Content (EN) is rejected",
          allure.severity_level.NORMAL, pytest.mark.functional_low, NL_WORKFLOW_GROUP)
@pytest.mark.pbi_129566
@pytest.mark.tc_134573
def test_newsletter_cp_134573_empty_content_en_is_rejected(page, browser):
    _case_empty_content(page, browser, "134573", "en")


@_nl_case("134575", "Verify that malformed/invalid HTML in Content (EN) is rejected or sanitized",
          allure.severity_level.NORMAL, pytest.mark.functional_low)
@pytest.mark.pbi_129566
@pytest.mark.tc_134575
def test_newsletter_cp_134575_malformed_html_is_rejected_or_sanitized(page):
    admin = _wf(page)
    title = _nl_title("134575")
    raw = '<div>QCTEST unclosed<script>window.__qc134575=1</script>'
    try:
        with allure.step("Put an unclosed div and a script tag into Content (EN) and Save as Draft"):
            status = _create_draft(admin, title, content_en=raw)
        stored = ""
        refusal = ""
        if status != STATUS_DRAFT:
            status = _row_appears(admin, title)
            refusal = admin.body_text()[:600]
        if status:
            with allure.step("Reload and read what was stored"):
                admin.open_entries_list()
                admin.open_entry_by_edit_link(title)
                stored = admin.content_html("en")
        allure.attach(f"row status={status!r}\nstored={stored!r}\npage={refusal!r}", name="outcome")
        if status:  # saved -> must be sanitized
            assert stored, "the record was saved but its Content (EN) could not be read back"
            assert "<script" not in stored.lower(), f"an executable <script> was stored: {stored[:300]!r}"
        else:  # not saved -> must have been a visible rejection
            assert refusal.strip(), "nothing was saved and no rejection was shown"
    finally:
        _strict_teardown(admin, title)


@_nl_case("134576", "Verify that Content (AR) accepts valid rich-text/HTML content",
          allure.severity_level.NORMAL, pytest.mark.functional_low, pytest.mark.bilingual)
@pytest.mark.pbi_129566
@pytest.mark.tc_134576
def test_newsletter_cp_134576_content_ar_accepts_rich_text(page):
    admin = _wf(page)
    title = _nl_title("134576")
    html = "<h2>نشرة غرفة قطر</h2><p>فقرة تجريبية للنشرة الإخبارية.</p>"
    try:
        with allure.step("Enter an Arabic heading + paragraph in Content (AR) and Save as Draft"):
            status = _create_draft(admin, title, content_ar=html)
        with allure.step("Reload and read the stored Content (AR)"):
            admin.open_entries_list()
            admin.open_entry_by_edit_link(title)
            stored = admin.content_html("ar")
            direction = admin.content_direction("ar")
        allure.attach(f"{stored}\ndir={direction}", name="stored Content (AR)")
        assert status == STATUS_DRAFT, f"the draft was not saved (row status {status!r})"
        assert "<h2>" in stored and "نشرة غرفة قطر" in stored, f"formatting not preserved: {stored[:300]!r}"
        assert direction == "rtl", f"the Arabic editor renders {direction!r}, expected rtl"
    finally:
        _strict_teardown(admin, title)


@_nl_case("134577", "Verify that saving a newsletter with empty Content (AR) is rejected",
          allure.severity_level.NORMAL, pytest.mark.functional_low, pytest.mark.bilingual, NL_WORKFLOW_GROUP)
@pytest.mark.pbi_129566
@pytest.mark.tc_134577
def test_newsletter_cp_134577_empty_content_ar_is_rejected(page, browser):
    _case_empty_content(page, browser, "134577", "ar")


# ── Scheduling ───────────────────────────────────────────────────────────
@_nl_case("134590", "Verify that scheduling with a Publish Date in the past is rejected",
          allure.severity_level.NORMAL, pytest.mark.functional_low, NL_WORKFLOW_GROUP)
@pytest.mark.pbi_129566
@pytest.mark.tc_134590
def test_newsletter_cp_134590_past_publish_date_is_rejected(page, browser):
    # Driven as the Site Content Author: if the past date were wrongly
    # accepted the record lands in Pending Review -- never Scheduled or sent.
    import datetime as _dt

    admin = _wf(page)
    title = _nl_title("134590")
    day = _dt.date.today() - _dt.timedelta(days=1)
    # The picker's own format is dd/mm/yyyy HH:MM, 24 h (read live 2026-10-13).
    yesterday = day.strftime("%d/%m/%Y") + " 09:00"
    expected_stored = day.isoformat() + "T09:00"
    context, author_page = _role(browser, ROLE_AUTHOR)
    author = _wf(author_page)
    try:
        with allure.step(f"Enter yesterday at 09:00 ({yesterday}) in Publish Date and click Schedule"):
            author.open_new_entry_form()
            _fill_newsletter(author, title)
            author.set_schedule_send(True)
            author.set_publish_date(yesterday)
            stored = author.publish_date_stored()
            assert stored == expected_stored, (
                f"precondition: Publish Date holds {stored!r}, expected {expected_stored!r}"
            )
            author.submit_for_review()
            page_text = author.body_text()[:800]
        with allure.step("Confirm the schedule was not accepted (polled -- the list loads async)"):
            status = _row_appears(admin, title)
        allure.attach(f"status={status!r}\n{page_text}", name="outcome (wording recorded, not asserted)")
        assert status != STATUS_SCHEDULED, "a newsletter was scheduled for a past date"
        assert status == "", f"the past-dated schedule was saved (row status {status!r})"
    finally:
        _close(context)
        _strict_teardown(admin, title)


# ── Approve / Reject ─────────────────────────────────────────────────────
@_nl_case("134595", "Verify that clicking Approve on a Pending Review newsletter moves it to Approved status",
          allure.severity_level.NORMAL, pytest.mark.functional_low, NL_WORKFLOW_GROUP)
@pytest.mark.pbi_129566
@pytest.mark.tc_134595
def test_newsletter_cp_134595_approve_moves_pending_review_to_published(page, browser):
    # NOT APPLICABLE by user decision 2026-10-12: approving/publishing a
    # newsletter on qcdev emails every real subscriber. Fails before any write.
    pytest.fail("NOT APPLICABLE -- newsletter approval emails every real subscriber on qcdev "
                "(user decision 2026-10-12)", pytrace=False)
    # "Approved" in the case is the PUBLISHED state of the 7-state workflow.
    admin = _wf(page)
    title = _nl_title("134595")
    try:
        with allure.step("Precondition: the Site Content Author submits a newsletter -> Pending Review"):
            pending = _author_submit(browser, title)
        assert pending == STATUS_PENDING_REVIEW, f"precondition: Author submit gave {pending!r}"
        with allure.step("Email gate before Approve"):
            _assert_send_is_safe(admin)
        with allure.step("Click Approve"):
            admin.open_entries_list()
            admin.approve_entry(title)
            status = admin.wait_for_row_status(title, STATUS_PUBLISHED, timeout=60)
        assert status == STATUS_PUBLISHED, f"after Approve the status is {status!r}"
    finally:
        _strict_teardown(admin, title)


@_nl_case("134596", "Verify that clicking Reject on a Pending Review newsletter returns it to Draft/Rejected without sending",
          allure.severity_level.NORMAL, pytest.mark.functional_low, NL_WORKFLOW_GROUP)
@pytest.mark.pbi_129566
@pytest.mark.tc_134596
def test_newsletter_cp_134596_reject_returns_to_rejected_without_sending(page, browser):
    admin = _wf(page)
    title = _nl_title("134596")
    comment = "QCTEST-134596 rejected by automation"
    try:
        with allure.step("Precondition: the Site Content Author submits a newsletter -> Pending Review"):
            pending = _author_submit(browser, title)
        assert pending == STATUS_PENDING_REVIEW, f"precondition: Author submit gave {pending!r}"
        with allure.step("Click Reject with a comment"):
            admin.open_entries_list()
            admin.reject_entry(title, comment)
            status = admin.wait_for_row_status(title, STATUS_REJECTED, timeout=60)
            history = admin.history_entries(title)
        allure.attach(repr(history), name="history")
        assert status in (STATUS_REJECTED, STATUS_DRAFT), f"after Reject the status is {status!r}"
        assert status != STATUS_PUBLISHED, "a rejected newsletter was published (and therefore sent)"
        assert any(comment in h.get("comment", "") for h in history), "the rejection comment is not in History"
    finally:
        _strict_teardown(admin, title)


# ── RBAC ─────────────────────────────────────────────────────────────────
@_nl_case("134599", "Verify that an Administrator can access and perform all Newsletter Management actions",
          allure.severity_level.NORMAL, pytest.mark.auth, NL_WORKFLOW_GROUP)
@pytest.mark.pbi_129566
@pytest.mark.tc_134599
def test_newsletter_cp_134599_admin_can_perform_all_actions(page, browser):
    # NOT APPLICABLE by user decision 2026-10-12: approving/publishing a
    # newsletter on qcdev emails every real subscriber. Fails before any write.
    pytest.fail("NOT APPLICABLE -- newsletter approval emails every real subscriber on qcdev "
                "(user decision 2026-10-12)", pytrace=False)
    # Create / Approve(-> Published) / Unpublish / Archive are executed;
    # Schedule is asserted AVAILABLE on the Unpublished row (its prompt has
    # not been walked live -- standards.md lists Scheduled as unverified).
    admin = _wf(page)
    title = _nl_title("134599")
    seen = {}
    try:
        with allure.step("Navigate to Newsletter Management and create (Author submits for the Approve step)"):
            admin.open_entries_list()
            seen["module_denied"] = admin.access_denied_shown()
            seen["pending"] = _author_submit(browser, title)
        with allure.step("Email gate before Approve/Publish"):
            _assert_send_is_safe(admin)
        with allure.step("Approve -> Published"):
            admin.open_entries_list()
            admin.approve_entry(title)
            seen["published"] = admin.wait_for_row_status(title, STATUS_PUBLISHED, timeout=60)
        with allure.step("Unpublish, check Schedule is offered, then Archive"):
            admin.open_entries_list()
            admin.unpublish_entry(title)
            seen["unpublished"] = admin.wait_for_row_status(title, STATUS_UNPUBLISHED, timeout=60)
            admin.open_entries_list()
            seen["unpublished_actions"] = admin.row_action_attrs(title)
            admin.archive_entry(title)
            seen["archived"] = admin.wait_for_row_status(title, STATUS_ARCHIVED, timeout=60)
        allure.attach(repr(seen), name="actions")
        assert not seen["module_denied"], "Access Denied shown to the Administrator"
        assert seen["pending"] == STATUS_PENDING_REVIEW, f"create/submit gave {seen['pending']!r}"
        assert seen["published"] == STATUS_PUBLISHED, f"Approve/Publish gave {seen['published']!r}"
        assert seen["unpublished"] == STATUS_UNPUBLISHED, f"Unpublish gave {seen['unpublished']!r}"
        assert "data-qc-oel-schedule" in seen["unpublished_actions"], "Schedule is not offered to the Administrator"
        assert seen["archived"] == STATUS_ARCHIVED, f"Archive gave {seen['archived']!r}"
    finally:
        _strict_teardown(admin, title)


@_nl_case("134600", "Verify that a Site Content Editor can view and manage newsletters where permitted, but cannot access Administrator-only actions",
          allure.severity_level.NORMAL, pytest.mark.auth, NL_WORKFLOW_GROUP)
@pytest.mark.pbi_129566
@pytest.mark.tc_134600
def test_newsletter_cp_134600_editor_manages_but_is_denied_admin_actions(page, browser):
    admin = _wf(page)
    title = _nl_title("134600")
    context, editor_page = _role(browser, ROLE_EDITOR)
    editor = _wf(editor_page)
    try:
        with allure.step("As Site Content Editor open Newsletter Management and create/edit a draft"):
            editor.open_entries_list()
            module_denied = editor.access_denied_shown()
            status = _create_draft(editor, title)
            editor.open_entries_list()
            editor.open_entry_by_edit_link(title)
            editor.set_subject_en(f"{title} edited")
            editor.save_as_draft()
            editor.open_entries_list()
            editor.open_entry_by_edit_link(title)
            edited = editor.subject_en_value()
        with allure.step("Attempt the Administrator-only subscriber-list management"):
            editor.open_subscriber_list()
            denied = editor.access_denied_shown()
            rows = editor.subscriber_rows()
        assert not module_denied, "the Editor cannot open Newsletter Management"
        assert status == STATUS_DRAFT, f"the Editor's draft was not saved ({status!r})"
        assert edited == f"{title} edited", f"the Editor's edit was not saved ({edited!r})"
        assert denied, "Access Denied is not shown for the Administrator-only subscriber list"
        assert not rows, f"the Editor can read {len(rows)} subscriber row(s)"
    finally:
        _close(context)
        _strict_teardown(admin, title)


@_nl_case("134601", "Verify that a Site Content Author can view and update newsletter content but cannot publish directly",
          allure.severity_level.NORMAL, pytest.mark.auth, NL_WORKFLOW_GROUP)
@pytest.mark.pbi_129566
@pytest.mark.tc_134601
def test_newsletter_cp_134601_author_updates_but_cannot_publish(page, browser):
    admin = _wf(page)
    title = _nl_title("134601")
    context, author_page = _role(browser, ROLE_AUTHOR)
    author = _wf(author_page)
    try:
        with allure.step("As Site Content Author open an own Draft newsletter and edit its content"):
            _create_draft(author, title)
            author.open_entries_list()
            author.open_entry_by_edit_link(title)
            author.set_content_html("<p>QCTEST-134601 author edit</p>", "en")
            author.save_as_draft()
            author.open_entries_list()
            author.open_entry_by_edit_link(title)
            stored = author.content_html("en")
        # The case expects "Access Denied" on clicking Publish Immediately. The
        # Author's form offers no "Publish" control (standards.md role table:
        # an Author's submit routes to Pending Review), so "no Publish control
        # offered" stands in for the denial; the hard check is that the
        # newsletter is NOT published.
        with allure.step("Attempt to publish directly"):
            labels = author.submit_button_labels()
            author.submit_for_review()
            denied = author.access_denied_shown()
            status = _row_status(admin, title)
        allure.attach(repr({"labels": labels, "denied": denied, "status": status}), name="publish attempt")
        assert "QCTEST-134601 author edit" in stored, "the Author's content edit was not saved"
        assert status != STATUS_PUBLISHED, "the Author published the newsletter directly"
        assert "Publish" not in labels or denied, (
            f"an enabled 'Publish' control was offered and no Access Denied shown: {labels}"
        )
    finally:
        _close(context)
        _strict_teardown(admin, title)


@_nl_case("134602", "Verify that a Public Visitor cannot access the Newsletter Management CMS module",
          allure.severity_level.CRITICAL, pytest.mark.auth)
@pytest.mark.pbi_129566
@pytest.mark.tc_134602
def test_newsletter_cp_134602_public_visitor_cannot_access_module(browser):
    anon = new_context(browser, use_auth_state=False)
    visitor = _wf(anon.new_page())
    try:
        with allure.step("As an unauthenticated visitor open the Newsletter Management URL directly"):
            visitor.open_manage_page_raw()
            outcome = {
                "login": visitor.login_form_visible(),
                "denied": visitor.access_denied_shown(),
                "form": visitor.has_object_form(),
                "rows": len(visitor.subscriber_rows()),
            }
        allure.attach(repr(outcome), name="outcome")
        assert outcome["login"] or outcome["denied"], "the visitor was neither sent to login nor shown Access Denied"
        assert not outcome["form"] and not outcome["rows"], "the module rendered content to a visitor"
    finally:
        _close(anon)


@_nl_case("134604", "Verify that a Site Content Editor is denied access to Administrator-only subscriber-list management",
          allure.severity_level.NORMAL, pytest.mark.auth)
@pytest.mark.pbi_129566
@pytest.mark.tc_134604
def test_newsletter_cp_134604_editor_denied_subscriber_list(browser):
    context, editor_page = _role(browser, ROLE_EDITOR)
    editor = _wf(editor_page)
    try:
        with allure.step("As Site Content Editor navigate to the subscriber list management screen"):
            editor.open_subscriber_list()
            denied = editor.access_denied_shown()
            rows = editor.subscriber_rows()
        assert denied, "the exact Access Denied message was not shown"
        assert not rows, f"the Editor can read {len(rows)} subscriber row(s)"
    finally:
        _close(context)


@_nl_case("134605", "Verify that a Site Content Author is denied access to the Approve/Reject action",
          allure.severity_level.NORMAL, pytest.mark.auth, NL_WORKFLOW_GROUP)
@pytest.mark.pbi_129566
@pytest.mark.tc_134605
def test_newsletter_cp_134605_author_cannot_approve_or_reject(page, browser):
    admin = _wf(page)
    title = _nl_title("134605")
    try:
        with allure.step("Precondition: a Pending Review newsletter"):
            pending = _author_submit(browser, title)
        assert pending == STATUS_PENDING_REVIEW, f"precondition: Author submit gave {pending!r}"
        context, author_page = _role(browser, ROLE_AUTHOR)
        try:
            with allure.step("As Site Content Author open it and look for Approve/Reject"):
                author = _wf(author_page)
                author.open_entries_list()
                attrs = author.row_action_attrs(title)
        finally:
            _close(context)
        allure.attach(repr(attrs), name="Author row actions")
        assert "data-qc-oel-approve" not in attrs, "Approve is offered to the Site Content Author"
        assert "data-qc-oel-reject" not in attrs, "Reject is offered to the Site Content Author"
        assert _row_status(admin, title) == STATUS_PENDING_REVIEW, "the record left Pending Review"
    finally:
        _strict_teardown(admin, title)


# ═════════════════════════════════════════════════════════════════════════
# P3/P4 batch -- 21 cases from .claude/qa-runs/phase3-20261012/129566.p34.todo.json
# Scripted OFFLINE 2026-10-13 (no browser). Not yet executed.
#
# Accounts: Save as Draft runs as the Administrator (`page`) -- a Draft never
# sends. Every Submit runs as the Site Content Author, so a wrongly accepted
# submit lands in Pending Review and emails nobody. Nothing here approves,
# publishes, schedules or sends. Six cases need an Approved / Published
# newsletter or the Send/Schedule step and fail NOT APPLICABLE on line one.
# Every record is `QCTEST-<tc>-<uid>`, deleted by exact title in `finally`.
# Every uploaded file is a uniquely named QCTEST- copy (D&M test files stay).
# ═════════════════════════════════════════════════════════════════════════
import re as _re
import tempfile as _tempfile
from datetime import date as _date, timedelta as _timedelta
from pathlib import Path as _Path

from cms.pages.components.disposable_object_admin import DisposableObjectAdminPage
from tools.fixture_factory import make_gif, make_jpg, make_pdf, make_png

P34_TIMEOUT = pytest.mark.timeout(480)
_MB = 1024 * 1024
BANNER = NewsletterWorkflowPage.BANNER_IMAGE_LABEL
ATTACHMENTS = NewsletterWorkflowPage.ATTACHMENTS_LABEL


def _nl_fixture(name: str, maker, size: int) -> str:
    folder = _Path(_tempfile.gettempdir()) / "qc_newsletter_129566"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    if not path.exists() or path.stat().st_size != size:
        path.write_bytes(maker(size))
    return str(path)


def _qctest_copy(fixture: str, tc: str) -> str:
    return DisposableObjectAdminPage.disposable_copy(fixture, tag=tc)


def _no_field_error(page_text: str, label: str) -> bool:
    """True when no "<label> ... required/invalid" message is in the text."""
    return not _re.search(_re.escape(label) + r"[^\n]{0,60}(required|invalid|must)", page_text, _re.I)


def _save_draft_and_reopen(admin: NewsletterWorkflowPage, title: str, before_save=None) -> dict:
    """Administrator: create a QCTEST newsletter with every required field,
    run `before_save(admin)`, Save as Draft, then re-open the row. Returns
    what was observed; the caller asserts and tears down."""
    seen = {}
    admin.open_new_entry_form()
    _fill_newsletter(admin, title)
    if before_save:
        before_save(admin, seen)
    admin.save_as_draft()
    seen["page_text"] = admin.body_text()[:1500]
    seen["errors"] = admin.visible_error_texts()
    seen["status"] = admin.wait_for_row_status(title, STATUS_DRAFT, timeout=30)
    if seen["status"]:
        admin.open_entries_list()  # fresh load: no stale SPA form state
        admin.open_entry_by_edit_link(title)
    return seen


def _optional_empty_case(page, tc: str, label: str, empty_read) -> None:
    """Optional field left empty -> Save as Draft succeeds, no error for it."""
    admin = _wf(page)
    title = _nl_title(tc)

    def _check_empty(nl, seen):
        seen["before_save"] = empty_read(nl)

    try:
        with allure.step(f"Leave {label} empty, fill every mandatory field, and Save as Draft"):
            seen = _save_draft_and_reopen(admin, title, _check_empty)
        allure.attach(repr({k: v for k, v in seen.items() if k != "page_text"}), name="outcome")
        assert not seen["before_save"], f"precondition: {label} is not empty ({seen['before_save']!r})"
        assert seen["status"] == STATUS_DRAFT, f"the draft was not saved (row status {seen['status']!r})"
        assert _no_field_error(seen["page_text"], label), f"a validation error was shown for {label}"
        assert not any(label.lower() in e.lower() for e in seen["errors"]), (
            f"a validation error names {label}: {seen['errors']!r}"
        )
    finally:
        _strict_teardown(admin, title)


def _file_accepted_case(page, tc: str, label: str, fixture: str) -> None:
    admin = _wf(page)
    title = _nl_title(tc)

    def _upload(nl, seen):
        nl.upload_file(label, _qctest_copy(fixture, tc))
        seen["on_upload"] = nl.attached_filename(label)

    try:
        with allure.step(f"Upload {_Path(fixture).name} to {label} and Save as Draft"):
            seen = _save_draft_and_reopen(admin, title, _upload)
            stored = admin.attached_filename(label) if seen["status"] else ""
        allure.attach(repr({"on_upload": seen.get("on_upload"), "status": seen["status"], "stored": stored}),
                      name="outcome")
        assert seen.get("on_upload"), f"{label}: the file did not upload (no filename shown)"
        assert seen["status"] == STATUS_DRAFT, f"the draft was not saved (row status {seen['status']!r})"
        assert stored == seen["on_upload"], f"{label}: stored {stored!r}, uploaded {seen['on_upload']!r}"
    finally:
        _strict_teardown(admin, title)


def _file_rejected_case(page, tc: str, label: str, fixture: str) -> None:
    """Unsupported (and/or oversize) file: a rejection must be shown, at the
    picker or on Save, and the file must not end up attached."""
    admin = _wf(page)
    title = _nl_title(tc)

    def _attempt(nl, seen):
        # A wrong label would also "reject" (upload_file_expect_rejected
        # counts any raise), so the control must be found first.
        assert nl.upload_control_present(label), f"precondition: no {label} upload control on the form"
        seen["picker_rejected"] = nl.upload_file_expect_rejected(label, _qctest_copy(fixture, tc))
        seen["errors_after_upload"] = nl.visible_error_texts()
        nl._close_stale_upload_picker()  # the refusing picker may still cover the form

    seen = {}
    try:
        with allure.step(f"Attempt to upload {_Path(fixture).name} to {label}, then Save as Draft"):
            admin.open_new_entry_form()
            _fill_newsletter(admin, title)
            _attempt(admin, seen)
            admin.save_as_draft()
            seen["errors_after_save"] = admin.visible_error_texts()
            seen["status"] = _row_appears(admin, title)
            stored = ""
            if seen["status"]:
                admin.open_entries_list()
                admin.open_entry_by_edit_link(title)
                stored = admin.attached_filename(label)
        allure.attach(repr({**seen, "stored": stored}), name="outcome (wording recorded, not asserted)")
        assert seen["picker_rejected"] or not seen["status"], (
            f"{label}: {_Path(fixture).name} was accepted by the picker and the draft saved without an error"
        )
        assert not stored, f"{label}: the rejected file is attached to the saved draft ({stored!r})"
    finally:
        _strict_teardown(admin, title)


def _author_required_case(page, browser, tc: str, skip: str, label: str) -> None:
    """Dropdown left unselected, everything else valid. Per this module's
    2026-09-20/21 QA Manager directive the refusal is tested on Submit (Save
    as Draft is permissive by design), as the Site Content Author."""
    admin = _wf(page)
    title = _nl_title(tc)
    context, author_page = _role(browser, ROLE_AUTHOR)
    author = _wf(author_page)
    try:
        with allure.step(f"Leave {label} unselected, fill the rest"):
            author.open_new_entry_form()
            _fill_newsletter(author, title, skip=(skip,))
            before = author.combo_value(label)
        assert not before, f"precondition: {label} is pre-selected ({before!r}), it cannot be left unselected"
        with allure.step("Click Submit for Review (Site Content Author)"):
            author.submit_for_review()
            blocked = author.submit_publish_blocked()
            errors = author.visible_error_texts()
        with allure.step("Confirm no record was created (polled -- the list loads async)"):
            created = _row_appears(admin, title)
        allure.attach(repr({"blocked": blocked, "errors": errors, "created": created}),
                      name=f"outcome (case wording '{label} is required.' recorded, not asserted)")
        assert not created, f"a newsletter with no {label} was saved (row status {created!r})"
        assert blocked or errors, f"no validation error was shown for the missing {label}"
    finally:
        _close(context)
        _strict_teardown(admin, title)


def _dtp(day: _date, hhmm: str = "09:00") -> tuple:
    """(picker input `dd/mm/yyyy HH:MM`, stored native `yyyy-mm-ddTHH:MM`)."""
    return f"{day.strftime('%d/%m/%Y')} {hhmm}", f"{day.isoformat()}T{hhmm}"


# ── Form + listing ───────────────────────────────────────────────────────
@_nl_case("134537", "Verify that the Newsletter Management create/edit form renders all required fields in English",
          allure.severity_level.NORMAL, pytest.mark.functional_low, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134537
def test_newsletter_cp_134537_form_renders_all_fields(page):
    # As Administrator (the super-admin session); a render check, not a
    # permission boundary. The form is opened in the English admin locale.
    admin = _wf(page)
    with allure.step("Navigate to Newsletter Management and click Create New"):
        admin.open_new_entry_form()
    with allure.step("Check every field the case lists"):
        presence = admin.form_field_presence()
    allure.attach(repr(presence), name="fields rendered")
    missing = [name for name, shown in presence.items() if not shown]
    assert not missing, f"the create form lacks: {missing}"


_LISTING_COLUMNS = {
    # case column -> accepted header wordings (label wording is not a defect)
    "Title": ("title", "entry"),
    "Status": ("status",),
    "Publish Date": ("publish date",),
    "Created By": ("created by", "author"),
    "Last Modified": ("last modified", "modified"),
}


@_nl_case("134538", "Verify that the Newsletter Listing page displays Title, Status, Publish Date, Created By, Last Modified, and Actions columns",
          allure.severity_level.NORMAL, pytest.mark.functional_low, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134538
def test_newsletter_cp_134538_listing_columns(page):
    # Read-only on the listing. Which workflow actions a row offers depends
    # on its state (standards.md "Content Editorial Workflow"): Publish and
    # Archive are asserted on Unpublished rows, Edit / Delete / View on all.
    admin = _wf(page)
    with allure.step("Navigate to the Newsletter Management listing"):
        admin.open_entries_list()
        table = admin.entries_table()
    allure.attach(repr(table), name="listing")
    headers = [h.lower() for h in table["headers"]]
    column_of = {}
    for col, words in _LISTING_COLUMNS.items():
        match = [table["headers"][i] for i, h in enumerate(headers) if any(w in h for w in words)]
        column_of[col] = match[0] if match else None
    missing = [c for c, h in column_of.items() if h is None]
    assert not missing, f"listing columns missing: {missing} (headers: {table['headers']})"
    assert table["rows"], "the listing shows no rows to inspect"
    problems = []
    for n, row in enumerate(table["rows"], 1):
        empty = [c for c, h in column_of.items() if not row["cells"].get(h, "").strip()]
        texts = " | ".join(a["text"] for a in row["actions"]).lower()
        attrs = {x for a in row["actions"] for x in a["attrs"]}
        lacking = [name for name, ok in (
            ("Edit", "edit" in texts),
            ("Delete", "data-qc-oel-delete" in attrs or "delete" in texts),
            ("View", bool(_re.search(r"\b(view|preview)\b", texts))),
        ) if not ok]
        status = row["cells"].get(column_of["Status"], "")
        if STATUS_UNPUBLISHED.lower() in status.lower():
            lacking += [a for a in ("publish", "archive") if f"data-qc-oel-{a}" not in attrs]
        if empty or lacking:
            problems.append(f"row {n} ({row['cells'].get(column_of['Title'], '')!r}): "
                            f"empty {empty}, actions missing {lacking}")
    assert not problems, "listing rows not fully populated:\n" + "\n".join(problems)


@_nl_case("134539", "Verify that the section enable/disable toggles are visible before sending a newsletter",
          allure.severity_level.NORMAL, pytest.mark.functional_high, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134539
def test_newsletter_cp_134539_section_toggles_visible_before_send():
    # Needs an Approved newsletter and its Send/Schedule step.
    pytest.fail("NOT APPLICABLE -- newsletter approval/send emails every real qcdev subscriber "
                "(user decision 2026-10-12)", pytrace=False)


@_nl_case("134544", "Verify that an admin can archive a Published newsletter",
          allure.severity_level.NORMAL, pytest.mark.functional_high, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134544
def test_newsletter_cp_134544_admin_archives_published_newsletter():
    # Needs a Published newsletter (reached only through approval = send).
    pytest.fail("NOT APPLICABLE -- newsletter approval/send emails every real qcdev subscriber "
                "(user decision 2026-10-12)", pytrace=False)


# ── Optional fields left empty ───────────────────────────────────────────
@_nl_case("134567", "Verify that leaving Short Description (EN) empty is accepted since the field is optional",
          allure.severity_level.MINOR, pytest.mark.functional_low, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134567
def test_newsletter_cp_134567_short_description_en_optional(page):
    _optional_empty_case(page, "134567", "Short Description", lambda nl: nl.short_description_value("en"))


@_nl_case("134570", "Verify that leaving Short Description (AR) empty is accepted since the field is optional",
          allure.severity_level.MINOR, pytest.mark.functional_low, pytest.mark.bilingual, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134570
def test_newsletter_cp_134570_short_description_ar_optional(page):
    _optional_empty_case(page, "134570", "Short Description", lambda nl: nl.short_description_value("ar"))


# ── Banner Image ─────────────────────────────────────────────────────────
@_nl_case("134579", "Verify that Banner Image accepts a valid JPG under 2 MB",
          allure.severity_level.NORMAL, pytest.mark.functional_low, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134579
def test_newsletter_cp_134579_banner_accepts_jpg(page):
    _file_accepted_case(page, "134579", BANNER, _nl_fixture("banner.jpg", make_jpg, int(1.2 * _MB)))


@_nl_case("134580", "Verify that leaving Banner Image empty is accepted since the field is optional",
          allure.severity_level.MINOR, pytest.mark.functional_low, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134580
def test_newsletter_cp_134580_banner_optional(page):
    _optional_empty_case(page, "134580", BANNER, lambda nl: nl.attached_filename(BANNER))


@_nl_case("134581", "Verify that Banner Image rejects a file exceeding 2 MB or an unsupported format",
          allure.severity_level.NORMAL, pytest.mark.functional_low, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134581
def test_newsletter_cp_134581_banner_rejects_big_gif(page):
    # banner.gif, 3.5 MB: unsupported format (schema: jpg, png) AND over the
    # project's 3 MB tolerance.
    _file_rejected_case(page, "134581", BANNER, _nl_fixture("banner.gif", make_gif, int(3.5 * _MB)))


# ── Attachments ──────────────────────────────────────────────────────────
@_nl_case("134582", "Verify that Attachments accepts a valid PDF file",
          allure.severity_level.NORMAL, pytest.mark.functional_low, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134582
def test_newsletter_cp_134582_attachments_accept_pdf(page):
    _file_accepted_case(page, "134582", ATTACHMENTS, _nl_fixture("newsletter-report.pdf", make_pdf, 200 * 1024))


@_nl_case("134583", "Verify that leaving Attachments empty is accepted since the field is optional",
          allure.severity_level.MINOR, pytest.mark.functional_low, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134583
def test_newsletter_cp_134583_attachments_optional(page):
    _optional_empty_case(page, "134583", ATTACHMENTS, lambda nl: nl.attached_filename(ATTACHMENTS))


@_nl_case("134584", "Verify that Attachments rejects an unsupported file format",
          allure.severity_level.NORMAL, pytest.mark.functional_low, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134584
def test_newsletter_cp_134584_attachments_reject_png(page):
    _file_rejected_case(page, "134584", ATTACHMENTS, _nl_fixture("image.png", make_png, 100 * 1024))


# ── Language / Status ────────────────────────────────────────────────────
@_nl_case("134586", "Verify that saving a newsletter with no Language selected is rejected",
          allure.severity_level.NORMAL, pytest.mark.functional_low, NL_WORKFLOW_GROUP, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134586
def test_newsletter_cp_134586_no_language_rejected(page, browser):
    _author_required_case(page, browser, "134586", "language", NewsletterWorkflowPage.LANGUAGE_LABEL)


@_nl_case("134588", "Verify that saving a newsletter with no Status selected is rejected",
          allure.severity_level.NORMAL, pytest.mark.functional_low, NL_WORKFLOW_GROUP, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134588
def test_newsletter_cp_134588_no_status_rejected(page, browser):
    _author_required_case(page, browser, "134588", "status", NewsletterWorkflowPage.STATUS_LABEL)


# ── Publish / Expiry Date ────────────────────────────────────────────────
@_nl_case("134589", "Verify that Publish Date accepts a valid future date/time",
          allure.severity_level.NORMAL, pytest.mark.functional_low, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134589
def test_newsletter_cp_134589_future_publish_date_saved(page):
    # Schedule Send stays unticked: only the Publish Date field is under test.
    admin = _wf(page)
    title = _nl_title("134589")
    typed, expected = _dtp(_date.today() + _timedelta(days=1))

    def _set(nl, seen):
        nl.set_publish_date(typed)
        seen["before_save"] = nl.publish_date_stored()

    try:
        with allure.step(f"Enter tomorrow at 09:00 ({typed}) in Publish Date and Save as Draft"):
            seen = _save_draft_and_reopen(admin, title, _set)
            stored = admin.publish_date_stored() if seen["status"] else ""
        allure.attach(repr({"before_save": seen["before_save"], "status": seen["status"], "stored": stored}),
                      name="outcome")
        assert seen["before_save"][:16] == expected, f"precondition: Publish Date holds {seen['before_save']!r}"
        assert seen["status"] == STATUS_DRAFT, f"the draft was not saved (row status {seen['status']!r})"
        assert stored[:16] == expected, f"Publish Date stored as {stored!r}, expected {expected!r}"
    finally:
        _strict_teardown(admin, title)


@_nl_case("134591", "Verify that Expiry Date accepts a valid date after the Publish Date",
          allure.severity_level.NORMAL, pytest.mark.functional_low, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134591
def test_newsletter_cp_134591_expiry_after_publish_saved(page):
    admin = _wf(page)
    title = _nl_title("134591")
    pub_typed, pub_expected = _dtp(_date(2026, 10, 10))
    exp_typed, exp_expected = _dtp(_date(2026, 10, 20))

    def _set(nl, seen):
        nl.set_publish_date(pub_typed)
        nl.set_expiry_date(exp_typed)
        seen["before_save"] = (nl.publish_date_stored(), nl.expiry_date_stored())

    try:
        with allure.step("Publish Date = Oct 10 2026 09:00, Expiry Date = Oct 20 2026 09:00, Save as Draft"):
            seen = _save_draft_and_reopen(admin, title, _set)
            stored = (admin.publish_date_stored(), admin.expiry_date_stored()) if seen["status"] else ("", "")
        allure.attach(repr({"before_save": seen["before_save"], "status": seen["status"], "stored": stored}),
                      name="outcome")
        assert seen["before_save"][0][:16] == pub_expected, f"precondition: Publish Date holds {seen['before_save'][0]!r}"
        assert seen["before_save"][1][:16] == exp_expected, f"precondition: Expiry Date holds {seen['before_save'][1]!r}"
        assert seen["status"] == STATUS_DRAFT, f"the draft was not saved (row status {seen['status']!r})"
        assert stored[0][:16] == pub_expected, f"Publish Date stored as {stored[0]!r}"
        assert stored[1][:16] == exp_expected, f"Expiry Date stored as {stored[1]!r}"
    finally:
        _strict_teardown(admin, title)


@_nl_case("134592", "Verify that an Expiry Date on or before the Publish Date is rejected",
          allure.severity_level.NORMAL, pytest.mark.functional_low, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134592
def test_newsletter_cp_134592_expiry_not_after_publish_rejected(page):
    # A cross-field date rule, not a required-field check, so the case's own
    # Save as Draft is used (the Draft-permissive directive covers required
    # fields only).
    admin = _wf(page)
    title = _nl_title("134592")
    typed, expected = _dtp(_date(2026, 10, 10))
    try:
        with allure.step("Publish Date = Expiry Date = Oct 10 2026 09:00, then Save as Draft"):
            admin.open_new_entry_form()
            _fill_newsletter(admin, title)
            admin.set_publish_date(typed)
            admin.set_expiry_date(typed)
            held = (admin.publish_date_stored(), admin.expiry_date_stored())
            admin.save_as_draft()
            errors = admin.visible_error_texts()
            blocked = admin.submit_publish_blocked()
        with allure.step("Confirm the draft was not saved (polled -- the list loads async)"):
            status = _row_appears(admin, title)
        allure.attach(repr({"held": held, "errors": errors, "blocked": blocked, "status": status}),
                      name="outcome (wording recorded, not asserted)")
        assert held[0][:16] == expected and held[1][:16] == expected, f"precondition: dates hold {held!r}"
        assert not status, f"a draft with Expiry Date == Publish Date was saved (row status {status!r})"
        assert errors or blocked, "the save was not completed but no validation error was shown"
    finally:
        _strict_teardown(admin, title)


# ── Send / Schedule / publish-only cases ─────────────────────────────────
@_nl_case("134598", "Verify that enabling then disabling the Upcoming Events section toggle correctly updates the Send/Schedule preview",
          allure.severity_level.NORMAL, pytest.mark.functional_high, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134598
def test_newsletter_cp_134598_upcoming_events_toggle_updates_preview():
    # Needs the Send/Schedule step of an Approved newsletter.
    pytest.fail("NOT APPLICABLE -- newsletter approval/send emails every real qcdev subscriber "
                "(user decision 2026-10-12)", pytrace=False)


@_nl_case("134606", "Verify that an Administrator is not denied any Newsletter Management permission (negative-control sanity check)",
          allure.severity_level.NORMAL, pytest.mark.auth, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134606
def test_newsletter_cp_134606_administrator_not_denied_any_action():
    # Its steps Approve, Publish and Schedule a newsletter.
    pytest.fail("NOT APPLICABLE -- newsletter approval/send emails every real qcdev subscriber "
                "(user decision 2026-10-12)", pytrace=False)


@_nl_case("134611", "Verify that publishing a newsletter whose enabled sections have zero currently-published items sends without those empty sections",
          allure.severity_level.NORMAL, pytest.mark.functional_high, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134611
def test_newsletter_cp_134611_publish_with_empty_sections():
    # Publishes (sends) a newsletter.
    pytest.fail("NOT APPLICABLE -- newsletter approval/send emails every real qcdev subscriber "
                "(user decision 2026-10-12)", pytrace=False)


@_nl_case("134618", "Verify that only Active/Urgent published Circulars & Announcements are included in the Newsletter Issue Email",
          allure.severity_level.NORMAL, pytest.mark.functional_high, timeout=P34_TIMEOUT)
@pytest.mark.pbi_129566
@pytest.mark.tc_134618
def test_newsletter_cp_134618_only_active_urgent_circulars_in_email():
    # Publishes (sends) a newsletter and reads the sent email.
    pytest.fail("NOT APPLICABLE -- newsletter approval/send emails every real qcdev subscriber "
                "(user decision 2026-10-12)", pytrace=False)
