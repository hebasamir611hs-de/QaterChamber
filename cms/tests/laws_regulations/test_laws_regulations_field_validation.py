"""
cms/tests/laws_regulations/test_laws_regulations_field_validation.py —
Control_Panel FIELD-VALIDATION cases (Functional-Low) for PBI 130699
"QC - Business Gateway - 006 - Laws & Regulations" — Engineer B batch:

  Display Order revert ... 140110
  Law Number ............. 140129 140130 140131
  Year ................... 140132 140133 140134 140135
  Law Title EN + AR ...... 140136 140137 140138 140139
  External URL ........... 140140 140141 140142
  Open Behavior .......... 140143 140144
  Display Order .......... 140145 140146 140147 140148
  Active Status .......... 140149 140150

Split from test_laws_regulations_control_panel.py (lifecycle/auth/edge) the
same way chambers_law is split. Fixtures come from this folder's conftest.py,
shared helpers from lawreg_support.py.

OBJECT: Law Regulation (`manage-law-regulation`) — one ENTRY per law card.
The cases' "Law Card 'QCTEST-130699-Labour Law and its Amendments'" /
"'QCTEST-130699-Commercial Companies Law'" do not exist on qcdev; each test
creates its OWN disposable copy titled `QCTEST-130699-<tc_id>-<case title>`
(Destructive-Precondition rule) and tears it down through the `disposable`
fixture (id + exact title + prefix re-verified before the click — the only
delete path). No real `QCDEMO-130699-LAWREG-*` record is ever edited.

HOW "SAVE" IS DRIVEN — live facts (read-only probe of an UNSAVED new form,
2026-09-29; nothing was saved):
  - "Save as Draft" skips required validation; the role-dependent submit
    button ("Publish" for the Editor) is the only validating save, so every
    case that says "save" and expects a refusal drives `submit()`.
  - Every field carries HTML `required`; NO maxlength, pattern, or real min
    (Year / Display Order are `type=number` with min -2147483648). So any
    format / length / positive-integer / whitespace refusal these cases
    expect must come from the server-side `/validate` rules (inline
    `[data-qc-oel-field-error]` or the red "This record was not saved" bar).
  - Typing '20O4' into Year leaves '204' (the letter keystroke is dropped);
    typing spaces into a number field leaves '' (native "Please fill out
    this field."). Spaces in a TEXT field are natively valid.
  - Open Behavior is a picklist: exactly "Same Tab" / "New Tab"; typed free
    text is discarded on blur.
  A refusal is asserted as: the save did NOT go through (no reload) AND the
  refusal is attributed to the field the case names (its native validation
  message, its inline note, or the red bar naming it); then the STORED value
  is re-read off a freshly opened form, then the public card in a fresh
  logged-out context.

DATA MAPPING (not re-authoring):
  - Law Number: the public chip prints the stored Law Number VERBATIM
    ("{lawNumber} · {year}"); the 24 real records store "Law No. 14" etc.
    Where Law Number is NOT the field under test the seed follows that live
    convention ("Law No. 14" / "Law No. 11") so the case's chip text is
    reachable. Where it IS under test (140129/140130/140131) the case's
    literal '14' is used, and the case's 'Law No. 14 · 2004' chip is
    asserted as written — a known conflict (renders '14 · 2004').
  - Display Order: positive-path seeds use the 100-grid (500 / 600);
    140110/140145/140146/140147 keep the literal values the cases name
    (5, 6, 1, 0, -3) as validation inputs on disposable records.
  - The Arabic titles are tc-scoped ('QCTEST-130699-<tc>-قانون العمل ...') so
    exact-title matching on the Arabic page is unambiguous.

ACCOUNT PINNING / KNOWN BLOCKER: every test signs in as the pinned Site
Content Editor (userId 156488). While `.env` CMS_SITE_CONTENT_EDITOR_* is
stale Liferay refuses it and every test SKIPS with that reason — never a
TEST_USER fallback. After each submit / reopen the signed-in userId is
re-read; a silent session_guard re-login as another account SKIPS (never
asserts).
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.laws_regulations.laws_regulations_admin_page import (
    OPEN_BEHAVIOR_NEW_TAB,
    OPEN_BEHAVIOR_SAME_TAB,
    QCTEST_PREFIX,
    ROLE_EDITOR,
    MSG_DISPLAY_ORDER_GRID,
    CreatedEntry,
    LawsRegulationsAdminPage,
)
from cms.tests.laws_regulations.lawreg_support import (
    AUTH_FREE_PAGE,
    PBI,
    PUBLISH_CONFIRM_TIMEOUT,
    _chip,
    _create,
    _pinned_login,
    _public,
    _public_until,
    _require_no_leftovers,
    _skip_unless_still_pinned,
    _title,
    _typography_mismatches,
    _wait_row_status,
)
from core.utils.waits import WaitTimeoutError
from web.pages.laws_regulations.laws_regulations_page import PUBLIC_PATH

pytestmark = [
    pytest.mark.control_panel,
    pytest.mark.pbi_130699,
    pytest.mark.invest,
    pytest.mark.functional_low,
    # Same public grid as the lifecycle module — never run two at once.
    pytest.mark.xdist_group("laws_regulations_130699"),
]

LABOUR = "Labour Law and its Amendments"
COMPANIES = "Commercial Companies Law"
URL_3961 = "https://www.almeezan.qa/LawPage.aspx?id=3961&language=en"

LAW_NUMBER = LawsRegulationsAdminPage.LAW_NUMBER_LABEL
YEAR = LawsRegulationsAdminPage.YEAR_LABEL
LAW_TITLE = LawsRegulationsAdminPage.LAW_TITLE_LABEL
LAW_TITLE_AR = LawsRegulationsAdminPage.LAW_TITLE_LABEL + LawsRegulationsAdminPage.ARABIC_SUFFIX
EXTERNAL_URL = LawsRegulationsAdminPage.EXTERNAL_URL_LABEL
DISPLAY_ORDER = LawsRegulationsAdminPage.DISPLAY_ORDER_LABEL

# Case typography (hex -> computed rgb).
# The chip is a pill sized to its text with equal padding, so its text sits
# centred whatever the computed text-align reads; alignment is not measurable.
CHIP_STYLE = dict(family="Cairo", weight="600", size="14px", line_height="22px",
                  align=(), color="rgb(108, 108, 107)")                   # #6C6C6B
TITLE_STYLE_EN = dict(family="Cairo", weight="600", size="18px", line_height="28px",
                      align=("left", "start"), color="rgb(29, 29, 27)")   # #1D1D1B
TITLE_STYLE_AR = dict(family="Cairo", weight="600", size="18px", line_height="28px",
                      align=("right", "start"), color="rgb(29, 29, 27)")


# =============================================================================
# Helpers (test layer — no raw Playwright)
# =============================================================================
def _labour_ar_title(tc_id: str) -> str:
    return f"{QCTEST_PREFIX}{tc_id}-قانون العمل رقم (14) لسنة 2004 وتعديلاته."


def _labour(tc_id: str, **overrides) -> dict:
    """The disposable stand-in for the cases' 'Labour Law and its
    Amendments' card (live convention: Law No. 14, 2004)."""
    data = {
        "law_number": "Law No. 14", "law_number_ar": "قانون رقم (14)", "year": "2004",
        "law_title": _title(tc_id, LABOUR), "law_title_ar": _labour_ar_title(tc_id),
        "external_url": URL_3961, "open_behavior": OPEN_BEHAVIOR_NEW_TAB,
        "display_order": "500", "active_status": True,
    }
    data.update(overrides)
    return data


def _companies(tc_id: str, **overrides) -> dict:
    """The disposable stand-in for 'Commercial Companies Law' (Law No. 11, 2015)."""
    data = {
        "law_number": "Law No. 11", "law_number_ar": "قانون رقم (11)", "year": "2015",
        "law_title": _title(tc_id, COMPANIES),
        "law_title_ar": f"{QCTEST_PREFIX}{tc_id}-قانون الشركات التجارية رقم (11) لسنة 2015.",
        "external_url": URL_3961, "open_behavior": OPEN_BEHAVIOR_NEW_TAB,
        "display_order": "600", "active_status": True,
    }
    data.update(overrides)
    return data


def _editor(page) -> LawsRegulationsAdminPage:
    admin = LawsRegulationsAdminPage(page)
    _pinned_login(admin, ROLE_EDITOR)
    return admin


def _seed_published(admin, disposable, data: dict) -> CreatedEntry:
    """Creates + publishes one disposable record and waits for its list badge
    to read Published. The badge shows the workflow state only: a Published
    record with Active Status unticked still reads PUBLISHED (confirmed live
    2026-09-30) and is hidden from visitors by the Active Status gate alone."""
    expected = STATUS_PUBLISHED
    _skip_unless_still_pinned(admin, ROLE_EDITOR)
    entry = _create(admin, disposable, data, publish=True)
    _skip_unless_still_pinned(admin, ROLE_EDITOR)
    status = _wait_row_status(admin, entry, expected, PUBLISH_CONFIRM_TIMEOUT)
    assert status == expected, f"ARRANGE: the seed {entry.title!r} reached {status!r}, not {expected}"
    return entry


def _open(admin, entry: CreatedEntry) -> LawsRegulationsAdminPage:
    admin.open_entry(entry)
    _skip_unless_still_pinned(admin, ROLE_EDITOR)
    return admin


def _no_validation_errors(admin, context: str) -> None:
    assert admin.field_errors() == [] and admin.invalid_field_count() == 0, (
        f"validation errors shown on valid input ({context}): {admin.field_errors()}"
    )


def _submit_accepted(admin, entry: CreatedEntry, context: str,
                     expected_status: str = STATUS_PUBLISHED) -> None:
    """Publishes the open form and requires it to go through and reach
    `expected_status` (Published; Inactive when Active Status was unticked)."""
    _skip_unless_still_pinned(admin, ROLE_EDITOR)
    admin.submit()
    _skip_unless_still_pinned(admin, ROLE_EDITOR)
    assert admin.save_redirected(), (
        f"{context}: the save was refused — field errors {admin.field_errors()}, "
        f"refusal bar {admin.refusal_bar_text()!r}"
    )
    status = _wait_row_status(admin, entry, expected_status, PUBLISH_CONFIRM_TIMEOUT)
    assert status == expected_status, f"{context}: the record reached {status!r}, not {expected_status}"


def _submit_expecting_refusal(admin, label: str, context: str) -> dict:
    """Clicks the validating submit and returns the refusal evidence for
    `label` (see LawsRegulationsAdminPage.refusal_evidence)."""
    _skip_unless_still_pinned(admin, ROLE_EDITOR)
    admin.submit()
    evidence = admin.refusal_evidence(label)
    if evidence["redirected"]:
        # The save went through — make sure it was still the pinned account.
        _skip_unless_still_pinned(admin, ROLE_EDITOR)
    allure.attach(repr(evidence), name=f"refusal evidence — {context}")
    return evidence


def _refusal_problem(evidence: dict, label: str, context: str) -> str:
    """"" when the save was refused AND the refusal names `label`; else a
    plain-English description of what happened instead."""
    if evidence["redirected"]:
        return f"{context}: the save went THROUGH (page reloaded) — no validation error was shown on {label!r}"
    if not evidence.get("refused"):
        return (
            f"{context}: no refusal was confirmed — either no refusal evidence appeared for this attempt "
            f"or a save request / navigation happened within the quiet window (save requests "
            f"{evidence.get('save_requests')})"
        )
    if evidence["native"] or evidence["inline"] or label in evidence["bar"]:
        return ""
    return (
        f"{context}: the save stopped but no error is attributed to {label!r} — native "
        f"{evidence['native']!r}, inline {evidence['inline']!r}, all inline notes "
        f"{evidence['all_inline']}, red bar {evidence['bar']!r}"
    )


def _assert_refused(evidence: dict, label: str, context: str) -> None:
    problem = _refusal_problem(evidence, label, context)
    assert not problem, problem


def _same_host_path(actual: str, expected: str) -> bool:
    """final_url comparison by host + path only (an external host may add
    or reorder query parameters on arrival); the clicked href stays exact."""
    a, e = urlsplit(actual or ""), urlsplit(expected or "")
    return (a.netloc.lower(), a.path.rstrip("/")) == (e.netloc.lower(), e.path.rstrip("/"))


def _public_card(anon_pages, title: str, locale: str = "en") -> dict:
    public = _public_until(anon_pages, lambda p: p.has_card(title),
                           f"{title!r} is not rendered on the public {locale} page", locale=locale)
    return public.card(title)


def _expected_public_index(public, title: str) -> int:
    """The position the renderer's own rule gives `title`: the active entries
    this page load received, stable-sorted by displayOrder."""
    ordered = sorted((e for e in public.delivered_entries() if e["active"]),
                     key=lambda e: _display_order_key(e["display_order"]))
    titles = [e["title"] for e in ordered]
    assert title in titles, f"{title!r} is not among the active entries the page received"
    return titles.index(title)


def _display_order_key(value) -> float:
    """Mirrors the fragment's `Number(displayOrder) || 0` (Python's sort is
    stable, as the renderer's Array.prototype.sort is)."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if number != number else number  # NaN -> 0


def _style_problems(public, title: str, part: str, style: dict) -> list[str]:
    return _typography_mismatches(public.card_text_style(title, part), style["family"], style["weight"],
                                  style["size"], style["line_height"], style["align"], style["color"])


class _Checks:
    """Collects every expectation of a multi-step case so one run reports
    all of them (hard asserts still guard the arrange steps)."""

    def __init__(self):
        self.failures: list[str] = []

    def check(self, ok: bool, message: str) -> None:
        if not ok:
            self.failures.append(message)

    def done(self) -> None:
        assert not self.failures, "\n".join(f"- {f}" for f in self.failures)


def _marks(tc_id: str, title: str, severity=allure.severity_level.MINOR):
    """tc marker + Allure traceability for one case."""
    def _apply(fn):
        for deco in (
            allure.title(title),
            allure.severity(severity),
            allure.label("testcase", tc_id),
            allure.label("pbi", PBI),
            getattr(pytest.mark, f"tc_{tc_id}"),
            AUTH_FREE_PAGE,
        ):
            fn = deco(fn)
        return fn
    return _apply


# =============================================================================
# Display Order — revert (140110)
# =============================================================================
@_marks("140110", "Reverting the Display Order of two Law cards restores their original public order")
def test_140110_reverting_display_order_restores_original_order(page, disposable, anon_pages):
    """Starts from the swapped state (Labour 600, Companies 500), reverts to
    Labour 500 / Companies 600, publishes, and expects Labour before Companies
    with every other card unmoved. The case's 5/6 are superseded by the user's
    100-grid rule (100, 200, 300 ...; the server refuses off-grid values)."""
    admin = _editor(page)
    labour, companies = _title("140110", LABOUR), _title("140110", COMPANIES)
    _require_no_leftovers(admin, labour, companies)
    labour_entry = _seed_published(admin, disposable, _labour("140110", display_order="600"))
    companies_entry = _seed_published(admin, disposable, _companies("140110", display_order="500"))
    before = _public_until(anon_pages, lambda p: p.has_card(labour) and p.has_card(companies),
                           "the two seeded cards never went live")
    others_before = [t for t in before.visible_card_titles() if t not in (labour, companies)]

    # Step 1 — both show the swapped values.
    assert _open(admin, labour_entry).display_order() == "600"
    assert _open(admin, companies_entry).display_order() == "500"

    # Step 2 + 3 — revert and publish each; both accepted with no error.
    for entry, value in ((labour_entry, "500"), (companies_entry, "600")):
        _open(admin, entry).fill_display_order(value)
        _no_validation_errors(admin, f"Display Order {value} on {entry.title!r}")
        _submit_accepted(admin, entry, f"reverting {entry.title!r} to Display Order {value}")

    after = _public_until(
        anon_pages,
        lambda p: p.has_card(labour) and p.has_card(companies)
        and p.card(labour)["index"] < p.card(companies)["index"],
        f"{labour!r} never rendered before {companies!r} after the revert",
    )
    others_after = [t for t in after.visible_card_titles() if t not in (labour, companies)]
    assert others_after == others_before, (
        f"other cards moved after the revert:\nbefore: {others_before}\nafter:  {others_after}"
    )


# =============================================================================
# Law Number (140129 – 140131)
# =============================================================================
@_marks("140129", "A valid Law Number is saved and rendered in the card chip")
def test_140129_valid_law_number_saved_and_rendered_in_chip(page, disposable, anon_pages):
    """Sets Law Number '14' and expects the chip 'Law No. 14 · 2004'.
    Known conflict: the chip prints Law Number verbatim ('14 · 2004')."""
    admin = _editor(page)
    title = _title("140129", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140129", law_number="13"))

    # Step 1 — opens with its stored values.
    stored = _open(admin, entry).read_law()
    assert (stored["law_title"], stored["law_number"], stored["year"]) == (title, "13", "2004"), stored

    # Step 2 — '14' accepted with no validation error.
    admin.fill_law_number("14")
    _no_validation_errors(admin, "Law Number '14'")
    _submit_accepted(admin, entry, "saving Law Number '14'")
    assert _open(admin, entry).law_number() == "14", f"stored Law Number is {admin.law_number()!r}"

    # Step 3 — public chip and its typography.
    public = _public_until(anon_pages, lambda p: (p.card(title) or {}).get("chip", "").startswith(("14", "Law No. 14")),
                           f"the public chip of {title!r} never reflected Law Number '14'")
    chip = public.card(title)["chip"]
    assert chip == _chip("14", "2004"), (
        f"chip reads {chip!r}, the case expects {_chip('14', '2004')!r} (the renderer prints the "
        f"stored Law Number verbatim and adds no 'Law No.' prefix — conflict, see report)"
    )
    problems = _style_problems(public, title, "chip", CHIP_STYLE)
    assert not problems, f"chip typography differs from Cairo 600 14px/22px #6C6C6B: {problems}"


@_marks("140130", "Saving a Law card with an empty Law Number is blocked")
def test_140130_empty_law_number_is_blocked(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140130", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140130", law_number="14"))

    # Step 1 — shows Law Number 14, marked required.
    _open(admin, entry)
    assert admin.law_number() == "14", admin.law_number()
    assert admin.is_field_required(LAW_NUMBER), "Law Number is not marked required on the form"

    # Step 2 — cleared + save -> blocked on Law Number; stored stays '14'.
    admin.fill_law_number("")
    _assert_refused(_submit_expecting_refusal(admin, LAW_NUMBER, "empty Law Number"),
                    LAW_NUMBER, "empty Law Number")
    assert _open(admin, entry).law_number() == "14", f"stored Law Number became {admin.law_number()!r}"
    chip = _public_card(anon_pages, title)["chip"]
    assert chip == _chip("14", "2004"), (
        f"public chip reads {chip!r}, the case expects {_chip('14', '2004')!r} (renderer prints the "
        f"stored Law Number verbatim — conflict, see report)"
    )


@_marks("140131", "A whitespace-only Law Number is rejected as empty")
def test_140131_whitespace_law_number_is_rejected(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140131", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140131", law_number="14"))
    chip_before = _public_card(anon_pages, title)["chip"]

    assert _open(admin, entry).law_number() == "14"
    admin.fill_law_number("   ")
    evidence = _submit_expecting_refusal(admin, LAW_NUMBER, "whitespace-only Law Number")

    checks = _Checks()
    checks.check(not _refusal_problem(evidence, LAW_NUMBER, "three spaces in Law Number"),
                 _refusal_problem(evidence, LAW_NUMBER, "three spaces in Law Number"))
    stored = _open(admin, entry).law_number()
    checks.check(stored == "14", f"stored Law Number became {stored!r}, not '14'")
    chip_after = _public_card(anon_pages, title)["chip"]
    checks.check(chip_after == chip_before, f"public chip changed from {chip_before!r} to {chip_after!r}")
    checks.check(chip_after != "Law No.  · 2004" and not re.match(r"^\s*·", chip_after),
                 f"a blank-number chip is rendered publicly: {chip_after!r}")
    checks.done()


# =============================================================================
# Year (140132 – 140135)
# =============================================================================
@_marks("140132", "A valid four-digit Year is saved and rendered in the card chip")
def test_140132_valid_year_saved_and_rendered_in_chip(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140132", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140132", year="2003"))

    assert _open(admin, entry).year() == "2003"
    admin.fill_year("2004")
    _no_validation_errors(admin, "Year 2004")
    _submit_accepted(admin, entry, "saving Year 2004")
    stored = _open(admin, entry).year()
    assert stored == "2004", f"stored Year is {stored!r}"

    public = _public_until(anon_pages, lambda p: (p.card(title) or {}).get("chip", "").endswith("2004"),
                           f"the public chip of {title!r} never showed 2004")
    chip = public.card(title)["chip"]
    assert chip == _chip("14", "2004"), f"chip reads {chip!r}, expected {_chip('14', '2004')!r}"
    assert re.search(r"· \d{4}$", chip), f"the year is not shown as four digits: {chip!r}"
    problems = _style_problems(public, title, "chip", CHIP_STYLE)
    assert not problems, f"chip typography differs from Cairo 600 14px/22px #6C6C6B: {problems}"


@_marks("140133", "A non-numeric Year is rejected")
def test_140133_non_numeric_year_is_rejected(page, disposable, anon_pages):
    """Either the letter keystroke is dropped or the save is blocked on Year
    — and in BOTH cases the stored Year must stay 2004. Live: the keystroke
    IS dropped ('20O4' -> '204'), so what the save does with '204' decides."""
    admin = _editor(page)
    title = _title("140133", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140133"))

    assert _open(admin, entry).year() == "2004"
    held = admin.type_into_field(YEAR, "20O4")
    allure.attach(repr(held), name="Year after typing '20O4'")
    letter_rejected = "O" not in held and "o" not in held
    evidence = _submit_expecting_refusal(admin, YEAR, "Year '20O4'")

    checks = _Checks()
    if not letter_rejected:
        checks.check(not _refusal_problem(evidence, YEAR, "Year '20O4'"), _refusal_problem(evidence, YEAR, "Year '20O4'"))
    stored = _open(admin, entry).year()
    checks.check(stored == "2004", (
        f"stored Year became {stored!r}, not 2004 — the field held {held!r} after typing '20O4' "
        f"(letter {'dropped' if letter_rejected else 'kept'}) and the save "
        f"{'went through' if evidence['redirected'] else 'was refused'}"
    ))
    chip = _public_card(anon_pages, title)["chip"]
    checks.check(chip == _chip("14", "2004"), f"public chip reads {chip!r}, not {_chip('14', '2004')!r}")
    checks.done()


@_marks("140134", "The Year digit-count boundary holds: four digits accepted, three and five rejected")
def test_140134_year_digit_count_boundary(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140134", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140134", year="2003"))

    # Step 1 + 2 — editable, 2004 accepted and stored.
    _open(admin, entry)
    assert admin.is_field_editable(YEAR) and re.fullmatch(r"\d{4}", admin.year()), admin.year()
    admin.type_into_field(YEAR, "2004")
    _submit_accepted(admin, entry, "saving Year 2004")
    assert _open(admin, entry).year() == "2004"

    # Step 3 — 204 and 20045 each refused on Year; stored stays 2004.
    checks = _Checks()
    for value in ("204", "20045"):
        _open(admin, entry).type_into_field(YEAR, value)
        evidence = _submit_expecting_refusal(admin, YEAR, f"Year {value}")
        problem = _refusal_problem(evidence, YEAR, f"Year {value} ({len(value)} digits)")
        checks.check(not problem, problem)
        stored = _open(admin, entry).year()
        checks.check(stored == "2004", f"after entering {value}, the stored Year is {stored!r}, not 2004")
    chip = _public_card(anon_pages, title)["chip"]
    checks.check(chip == _chip("14", "2004"), f"public chip reads {chip!r}, not {_chip('14', '2004')!r}")
    checks.done()


@_marks("140135", "A whitespace-only Year is rejected as empty")
def test_140135_whitespace_year_is_rejected(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140135", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140135"))
    chip_before = _public_card(anon_pages, title)["chip"]

    assert _open(admin, entry).year() == "2004"
    admin.type_into_field(YEAR, "  ")
    _assert_refused(_submit_expecting_refusal(admin, YEAR, "whitespace Year"), YEAR, "two spaces in Year")
    assert _open(admin, entry).year() == "2004", f"stored Year became {admin.year()!r}"
    chip_after = _public_card(anon_pages, title)["chip"]
    assert chip_after == chip_before, f"public chip changed from {chip_before!r} to {chip_after!r}"


# =============================================================================
# Law Title EN + AR (140136 – 140139)
# =============================================================================
@pytest.mark.bilingual
@_marks("140136", "Valid English and Arabic Law Titles are saved and rendered in the matching language",
        allure.severity_level.NORMAL)
def test_140136_bilingual_law_titles_saved_and_rendered(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140136", LABOUR)
    title_ar = _labour_ar_title("140136")
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140136", law_title_ar=f"{QCTEST_PREFIX}140136-مسودة"))

    # Step 1 — both language variants editable.
    _open(admin, entry)
    assert admin.is_field_editable(LAW_TITLE) and admin.is_field_editable(LAW_TITLE_AR)

    # Step 2 — both accepted and stored per language.
    admin.fill_law_title(title).fill_law_title_ar(title_ar)
    _no_validation_errors(admin, "bilingual titles")
    _submit_accepted(admin, entry, "saving the bilingual titles")
    _open(admin, entry)
    assert (admin.law_title(), admin.law_title_ar()) == (title, title_ar), (
        f"stored titles are {admin.law_title()!r} / {admin.law_title_ar()!r}"
    )

    # Step 3 — English page, then Arabic page.
    checks = _Checks()
    english = _public_until(anon_pages, lambda p: p.has_card(title), f"{title!r} not on the English page")
    problems = _style_problems(english, title, "title", TITLE_STYLE_EN)
    checks.check(not problems, f"English title typography differs from Cairo 600 18px/28px LEFT #1D1D1B: {problems}")
    arabic = _public_until(anon_pages, lambda p: p.has_card(title_ar),
                           f"{title_ar!r} never rendered on the Arabic page", locale="ar")
    card = arabic.card(title_ar)
    checks.check(card["title"] == title_ar, f"Arabic card title reads {card['title']!r}")
    problems = _style_problems(arabic, title_ar, "title", TITLE_STYLE_AR)
    checks.check(not problems, f"Arabic title typography differs from Cairo 600 18px/28px RIGHT #1D1D1B: {problems}")
    checks.check(card["chip"] == "قانون رقم (14) · 2004", f"Arabic chip reads {card['chip']!r}, not 'قانون رقم (14) · 2004'")
    checks.check(not arabic.has_card(title), f"the English title {title!r} appears on the Arabic page (fallback)")
    checks.done()


@pytest.mark.bilingual
@_marks("140137", "Publishing is blocked when the required Arabic Law Title is missing",
        allure.severity_level.NORMAL)
def test_140137_missing_arabic_title_blocks_publish(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140137", LABOUR)
    title_ar = _labour_ar_title("140137")
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140137"))
    _public_card(anon_pages, title_ar, locale="ar")  # live Arabic baseline

    # Step 1 — both populated and required.
    _open(admin, entry)
    assert (admin.law_title(), admin.law_title_ar()) == (title, title_ar), admin.read_law()
    assert admin.is_field_required(LAW_TITLE) and admin.is_field_required(LAW_TITLE_AR), (
        "Law Title / Law Title — العربية are not both marked required"
    )

    # Step 2 — cleared and flagged required.
    admin.fill_law_title_ar("")
    assert admin.law_title_ar() == "" and admin.is_field_required(LAW_TITLE_AR)

    # Step 3 — Publish blocked with an error naming Title AR; nothing changed.
    _assert_refused(_submit_expecting_refusal(admin, LAW_TITLE_AR, "empty Arabic title"),
                    LAW_TITLE_AR, "Publish with Law Title — العربية empty")
    assert _open(admin, entry).law_title_ar() == title_ar, f"stored Arabic title became {admin.law_title_ar()!r}"
    admin.open_list()
    assert admin.row_status(entry) == STATUS_PUBLISHED, f"the record is now {admin.row_status(entry)!r}"
    assert _public(anon_pages, locale="ar").has_card(title_ar), (
        f"the live Arabic page no longer renders {title_ar!r}"
    )


@_marks("140138", "The Law Title accepts exactly 250 characters and rejects 251")
def test_140138_law_title_250_accepted_251_rejected(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140138", LABOUR)
    title_250 = QCTEST_PREFIX + "C" * 236
    title_251 = QCTEST_PREFIX + "C" * 237
    assert (len(title_250), len(title_251)) == (250, 251)
    _require_no_leftovers(admin, title, title_250, title_251)
    entry = _seed_published(admin, disposable, _labour("140138"))

    # Step 1 + 2 — 250 accepted, stored in full, rendered in full.
    _open(admin, entry)
    assert admin.is_field_editable(LAW_TITLE)
    admin.fill_law_title(title_250)
    entry = disposable.add_title(entry, title_250)  # known to teardown BEFORE the rename is sent
    _submit_accepted(admin, entry, "saving a 250-character title")
    stored = _open(admin, entry).law_title()
    assert stored == title_250, f"stored title has {len(stored)} characters, not the 250 entered"
    public = _public_until(anon_pages, lambda p: p.has_card(title_250),
                           "the 250-character title never rendered in full on the public page")
    problems = _typography_mismatches(public.card_text_style(title_250, "title"), "Cairo", "600",
                                      "18px", "28px", (), None)
    assert not problems, f"250-character title typography differs from Cairo 600 18px/28px: {problems}"

    # Step 3 — 251 refused (input stops at 250, or the save is blocked).
    _open(admin, entry).fill_law_title(title_251)
    held = admin.law_title()
    disposable.add_title(entry, held)  # whatever the field holds may be saved — known BEFORE submit
    evidence = _submit_expecting_refusal(admin, LAW_TITLE, "251-character title")
    checks = _Checks()
    if len(held) > 250:
        problem = _refusal_problem(evidence, LAW_TITLE, "a 251-character Law Title")
        checks.check(not problem, problem)
    stored = _open(admin, entry).law_title()
    checks.check(stored == title_250, f"stored title has {len(stored)} characters, not the 250-character string")
    checks.done()


@_marks("140139", "A whitespace-only Law Title is rejected as empty")
def test_140139_whitespace_law_title_is_rejected(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140139", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140139"))

    assert _open(admin, entry).law_title() == title
    admin.fill_law_title("      ")
    evidence = _submit_expecting_refusal(admin, LAW_TITLE, "whitespace Law Title")
    if evidence["redirected"]:
        # The blank title was STORED: capture the public evidence, then put
        # the record's own title back so teardown can re-verify it.
        blank_cards = _public(anon_pages).blank_or_raw_card_texts()
        _open(admin, entry).fill_law_title(title)
        _submit_accepted(admin, entry, "restoring the disposable record's title after the unexpected save")
        pytest.fail(
            f"six spaces in Law Title were SAVED (no validation error); blank/raw cards on the public "
            f"page right after: {blank_cards}"
        )
    _assert_refused(evidence, LAW_TITLE, "six spaces in Law Title")
    assert _open(admin, entry).law_title() == title, f"stored title became {admin.law_title()!r}"
    public = _public(anon_pages)
    assert public.has_card(title) and public.blank_or_raw_card_texts() == [], public.blank_or_raw_card_texts()


# =============================================================================
# External URL (140140 – 140142)
# =============================================================================
@pytest.mark.redirect
@_marks("140140", "A valid External URL is saved and used as the card's redirect destination",
        allure.severity_level.NORMAL)
def test_140140_valid_external_url_saved_and_used(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140140", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140140", external_url="https://www.almeezan.qa/"))

    assert _open(admin, entry).external_url() == "https://www.almeezan.qa/"
    admin.fill_external_url(URL_3961)
    _no_validation_errors(admin, "External URL")
    _submit_accepted(admin, entry, "saving the External URL")
    stored = _open(admin, entry).external_url()
    assert stored == URL_3961, f"stored URL is {stored!r}, not verbatim {URL_3961!r}"

    public = _public_until(anon_pages, lambda p: (p.card(title) or {}).get("href") == URL_3961,
                           f"the public card never linked to {URL_3961!r}")
    followed = public.follow_card_link(title)
    allure.attach(repr(followed), name="card click")
    assert followed["clicked_href"] == URL_3961, followed
    assert _same_host_path(followed["final_url"], URL_3961), (
        f"the click landed on {followed['final_url']!r}, not the host/path of {URL_3961!r}"
    )


@_marks("140141", "A malformed External URL is rejected", allure.severity_level.NORMAL)
def test_140141_malformed_external_url_is_rejected(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140141", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140141"))

    assert _open(admin, entry).external_url() == URL_3961
    admin.fill_external_url("htp:/almeezan qa/law")
    _assert_refused(_submit_expecting_refusal(admin, EXTERNAL_URL, "malformed URL"),
                    EXTERNAL_URL, "External URL 'htp:/almeezan qa/law'")
    assert _open(admin, entry).external_url() == URL_3961, f"stored URL became {admin.external_url()!r}"
    public = _public_until(anon_pages, lambda p: p.has_card(title), f"{title!r} not on the public page")
    assert public.card(title)["href"] == URL_3961, f"public card links to {public.card(title)['href']!r}"
    followed = public.follow_card_link(title)
    assert followed["clicked_href"] == URL_3961, followed
    assert _same_host_path(followed["final_url"], URL_3961), f"the card now redirects to {followed['final_url']!r}"


@_marks("140142", "A whitespace-only External URL is rejected as empty")
def test_140142_whitespace_external_url_is_rejected(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140142", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140142"))

    assert _open(admin, entry).external_url() == URL_3961
    admin.fill_external_url("    ")
    _assert_refused(_submit_expecting_refusal(admin, EXTERNAL_URL, "whitespace URL"),
                    EXTERNAL_URL, "four spaces in External URL")
    assert _open(admin, entry).external_url() == URL_3961, f"stored URL became {admin.external_url()!r}"
    href = _public_card(anon_pages, title)["href"]
    assert href == URL_3961, f"the public card's destination is {href!r}"


# =============================================================================
# Open Behavior (140143 – 140144)
# =============================================================================
@pytest.mark.redirect
@_marks("140143", "Open Behavior = New Tab opens the law's source in a new browser tab",
        allure.severity_level.NORMAL)
def test_140143_open_behavior_new_tab(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140143", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140143", open_behavior=OPEN_BEHAVIOR_SAME_TAB))

    # Step 1 — exactly two options, no free text.
    _open(admin, entry)
    options = admin.open_behavior_options()
    assert options == [OPEN_BEHAVIOR_SAME_TAB, OPEN_BEHAVIOR_NEW_TAB], f"Open Behavior offers {options}"
    kept = admin.open_behavior_after_free_text("Free text")
    assert kept in ("", OPEN_BEHAVIOR_SAME_TAB, OPEN_BEHAVIOR_NEW_TAB), f"the picklist kept free text {kept!r}"

    # Step 2 — New Tab stored.
    admin.select_open_behavior(OPEN_BEHAVIOR_NEW_TAB)
    _submit_accepted(admin, entry, "saving Open Behavior = New Tab")
    assert _open(admin, entry).open_behavior() == OPEN_BEHAVIOR_NEW_TAB, admin.open_behavior()

    # Step 3 — a second tab opens; the listing stays put.
    public = _public_until(anon_pages, lambda p: (p.card(title) or {}).get("target") == "_blank",
                           f"the public card {title!r} never rendered with target=_blank")
    followed = public.follow_card_link(title)
    allure.attach(repr(followed), name="New Tab click")
    assert followed["opened_new_tab"], "no second browser tab opened"
    assert followed["clicked_href"] == URL_3961, followed
    assert _same_host_path(followed["final_url"], URL_3961), f"the new tab opened {followed['final_url']!r}"
    assert PUBLIC_PATH in public.current_url() and public.has_card(title), (
        f"the original tab left the Laws & Regulations page: {public.current_url()!r}"
    )


@pytest.mark.redirect
@_marks("140144", "Open Behavior = Same Tab opens the law's source in the current tab",
        allure.severity_level.NORMAL)
def test_140144_open_behavior_same_tab(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140144", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140144", open_behavior=OPEN_BEHAVIOR_NEW_TAB))

    assert _open(admin, entry).open_behavior() == OPEN_BEHAVIOR_NEW_TAB
    admin.select_open_behavior(OPEN_BEHAVIOR_SAME_TAB)
    _submit_accepted(admin, entry, "saving Open Behavior = Same Tab")
    assert _open(admin, entry).open_behavior() == OPEN_BEHAVIOR_SAME_TAB, admin.open_behavior()

    public = _public_until(anon_pages, lambda p: p.has_card(title) and p.card(title)["target"] != "_blank",
                           f"the public card {title!r} still opens in a new tab")
    followed = public.follow_card_link_in_place(title)
    allure.attach(repr(followed), name="Same Tab click")
    assert not followed["new_tab_opened"], "a new tab opened for a Same Tab card"
    assert followed["clicked_href"] == URL_3961, followed
    assert _same_host_path(followed["final_url"], URL_3961), f"the current tab went to {followed['final_url']!r}"
    back = public.go_back()
    assert PUBLIC_PATH in back and public.has_card(title), f"Back landed on {back!r}, not the listing"


# =============================================================================
# Display Order (140145 – 140148)
# =============================================================================
@_marks("140145", "A valid positive Display Order is saved and controls the card's grid position")
def test_140145_display_order_one_renders_first(page, disposable, anon_pages):
    """The case's 5 -> 1 is superseded by the user's 100-grid rule: seed 500,
    change to 100 (the lowest grid value). "Renders first" is asserted as the
    position the renderer's own rule gives Display Order 100 among the entries
    the page received — real records may also sit at 100."""
    admin = _editor(page)
    title = _title("140145", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140145", display_order="500"))

    assert _open(admin, entry).display_order() == "500"
    admin.fill_display_order("100")
    _no_validation_errors(admin, "Display Order 100")
    _submit_accepted(admin, entry, "saving Display Order 100")
    assert _open(admin, entry).display_order() == "100"

    public = _public_until(anon_pages, lambda p: p.has_card(title), f"{title!r} is not on the public page")
    expected = _expected_public_index(public, title)
    ahead = public.visible_card_titles()[:expected]
    assert public.card(title)["index"] == expected, (
        f"{title!r} renders at position {public.card(title)['index'] + 1}; Display Order 100 places it at "
        f"{expected + 1} (cards ahead of it: {ahead})"
    )


@_marks("140146", "A negative Display Order is rejected")
def test_140146_negative_display_order_is_rejected(page, disposable, anon_pages):
    """Case values (5 / -3) superseded by the user's 100-grid rule: seed 500,
    try -300."""
    admin = _editor(page)
    title = _title("140146", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140146", display_order="500"))
    index_before = _public_card(anon_pages, title)["index"]

    assert _open(admin, entry).display_order() == "500"
    admin.fill_display_order("-300")
    _assert_refused(_submit_expecting_refusal(admin, DISPLAY_ORDER, "Display Order -300"),
                    DISPLAY_ORDER, "Display Order -300")
    assert _open(admin, entry).display_order() == "500", f"stored Display Order became {admin.display_order()!r}"
    index_after = _public_card(anon_pages, title)["index"]
    assert index_after == index_before, f"the card moved from position {index_before} to {index_after}"


@_marks("140147", "The Display Order boundary holds: 0 is rejected and the lowest grid value is accepted")
def test_140147_display_order_boundary_zero_and_one(page, disposable, anon_pages):
    """The case wording (seed 5, 0 rejected, 1 accepted) is superseded by the
    user's 100-grid rule (100, 200, 300 ...): seed 500; 0 is refused; 1 is
    refused with the 100-grid message (documented behaviour); 100 — the lowest
    valid grid value — is accepted and renders at its computed position."""
    admin = _editor(page)
    title = _title("140147", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140147", display_order="500"))

    _open(admin, entry)
    assert admin.is_field_editable(DISPLAY_ORDER) and admin.display_order() == "500"
    checks = _Checks()

    # Step 2 — 0 and 1 refused, stored unchanged; 1 names the 100-grid rule.
    for value in ("0", "1"):
        _open(admin, entry).fill_display_order(value)
        evidence = _submit_expecting_refusal(admin, DISPLAY_ORDER, f"Display Order {value}")
        problem = _refusal_problem(evidence, DISPLAY_ORDER, f"Display Order {value}")
        checks.check(not problem, problem)
        if value == "1":
            shown = " ".join([evidence["bar"], evidence["inline"]] + list(evidence["all_inline"]))
            checks.check(MSG_DISPLAY_ORDER_GRID in shown,
                         f"Display Order 1 was not refused with the 100-grid message; shown: {shown!r}")
        stored = _open(admin, entry).display_order()
        checks.check(stored == "500", f"after entering {value} the stored Display Order is {stored!r}, not 500")

    # Step 3 — 100 accepted, stored, and rendered at its computed position.
    _open(admin, entry).fill_display_order("100")
    _submit_accepted(admin, entry, "saving Display Order 100")
    stored = _open(admin, entry).display_order()
    checks.check(stored == "100", f"after entering 100 the stored Display Order is {stored!r}")
    public = _public_until(anon_pages, lambda p: p.has_card(title), f"{title!r} is not on the public page")
    expected = _expected_public_index(public, title)
    checks.check(public.card(title)["index"] == expected,
                 f"{title!r} renders at position {public.card(title)['index'] + 1}, not the computed {expected + 1}")
    checks.done()


@_marks("140148", "A whitespace-only Display Order is rejected as empty")
def test_140148_whitespace_display_order_is_rejected(page, disposable, anon_pages):
    admin = _editor(page)
    title = _title("140148", LABOUR)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _labour("140148", display_order="500"))
    index_before = _public_card(anon_pages, title)["index"]

    assert _open(admin, entry).display_order() == "500"
    admin.type_into_field(DISPLAY_ORDER, "  ")
    _assert_refused(_submit_expecting_refusal(admin, DISPLAY_ORDER, "whitespace Display Order"),
                    DISPLAY_ORDER, "two spaces in Display Order")
    assert _open(admin, entry).display_order() == "500", f"stored Display Order became {admin.display_order()!r}"
    index_after = _public_card(anon_pages, title)["index"]
    assert index_after == index_before, f"the card moved from position {index_before} to {index_after}"


# =============================================================================
# Active Status (140149 – 140150)
# =============================================================================
@_marks("140149", "A Law card with Active Status = Active appears on the public page",
        allure.severity_level.NORMAL)
def test_140149_active_card_appears_publicly(page, disposable, anon_pages):
    """User rule: public only when Published AND Active Status ticked; an
    unticked Published record's list badge still reads PUBLISHED. The seed is
    published with Active Status unticked (stored unticked, not public), then
    ticked and saved. Case 'Display Order 6' is seeded as 600 (100-grid); the
    position asserted is the one the renderer's own rule gives it."""
    admin = _editor(page)
    title = _title("140149", COMPANIES)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _companies("140149", active_status=False))

    # Step 1 — toggle visible, stored values; not on the public page yet.
    stored = _open(admin, entry).read_law()
    assert (stored["law_number"], stored["year"], stored["display_order"], stored["active_status"]) == (
        "Law No. 11", "2015", "600", False
    ), stored
    assert not _public(anon_pages).has_card(title), f"{title!r} is public while Active Status is unticked"

    # Step 2 — tick Active, publish; badge Published, stored ticked.
    _open(admin, entry).set_active_status(True)
    _submit_accepted(admin, entry, "saving Active Status = Active", expected_status=STATUS_PUBLISHED)
    assert _open(admin, entry).active_status() is True, "Active Status did not stay ticked"

    # Step 3 — rendered (logged-out) at its computed position with the chip.
    public = _public_until(anon_pages, lambda p: p.has_card(title), f"{title!r} never appeared publicly")
    card = public.card(title)
    expected_index = _expected_public_index(public, title)
    assert card["index"] == expected_index, (
        f"{title!r} renders at position {card['index'] + 1}; its Display Order places it at "
        f"{expected_index + 1} in the delivered order"
    )
    assert card["chip"] == _chip("11", "2015"), f"chip reads {card['chip']!r}, not {_chip('11', '2015')!r}"


@_marks("140150", "A Law card with Active Status = Inactive is removed from the public page",
        allure.severity_level.NORMAL)
def test_140150_inactive_card_removed_publicly(page, disposable, anon_pages):
    """Conflict handled: a REAL published 'Commercial Companies Law' record
    exists, so the case's search for 'Commercial Companies' cannot return the
    empty state on qcdev. The search is still run and must return exactly
    the matching OTHER cards (never ours); the empty state is asserted on a
    search for this card's own unique title."""
    admin = _editor(page)
    title = _title("140150", COMPANIES)
    _require_no_leftovers(admin, title)
    entry = _seed_published(admin, disposable, _companies("140150"))

    # Step 1 — Active and rendered.
    before = _public_until(anon_pages, lambda p: p.has_card(title), f"{title!r} never went live")
    others_before = [t for t in before.visible_card_titles() if t != title]
    assert _open(admin, entry).active_status() is True

    # Step 2 — set Inactive, publish, stored.
    admin.set_active_status(False)
    _submit_accepted(admin, entry, "saving Active Status = Inactive", expected_status=STATUS_PUBLISHED)
    stored_after_toggle = _open(admin, entry).read_law()
    assert stored_after_toggle["active_status"] is False, "Active Status is still ticked"

    # Step 3 — gone from every page of the grid and from the delivered source.
    checks = _Checks()
    public = _public_until(anon_pages, lambda p: not p.has_card(title),
                           f"{title!r} is still rendered after being set Inactive")
    checks.check(not public.is_load_more_visible(), "Load More was not exhausted before checking absence")
    checks.check(not public.delivered_source_contains(title),
                 f"{title!r} is still in the page source / data delivered to an anonymous visitor")
    checks.check(public.visible_card_titles() == others_before,
                 f"the remaining cards changed order:\nbefore: {others_before}\nafter:  {public.visible_card_titles()}")
    public.search("Commercial Companies")
    results = public.visible_card_titles()
    expected_matches = [t for t in others_before if "commercial companies" in t.lower()]
    checks.check(title not in results, f"searching 'Commercial Companies' still returns {title!r}")
    checks.check(results == expected_matches,
                 f"searching 'Commercial Companies' returned {results}, expected only {expected_matches}")
    checks.check(public.is_empty_state_visible() == (not results),
                 "the empty-state message does not match the search result set")
    public.search(title)
    checks.check(public.visible_card_count() == 0 and public.is_empty_state_visible(),
                 f"searching the inactive card's exact title shows {public.visible_card_titles()} instead of the empty state")

    # Step 4 — still in the CMS, values intact, Inactive.
    admin.open_list()
    checks.check(admin.row_present(entry), f"{title!r} is gone from the CMS list — deactivation deleted it")
    checks.check(admin.row_status(entry) == STATUS_PUBLISHED,
                 f"the list badge reads {admin.row_status(entry)!r}, not {STATUS_PUBLISHED!r}")
    stored = _open(admin, entry).read_law()
    want = {k: v for k, v in _companies("140150", active_status=False).items() if k != "law_number_ar"}
    got = {k: stored[k] for k in want}
    checks.check(got == want, f"stored values changed after deactivation: {got} (expected {want})")
    checks.done()
