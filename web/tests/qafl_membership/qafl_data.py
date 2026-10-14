"""
web/tests/qafl_membership/qafl_data.py — shared data + AAA bodies for the
QAFL Membership Registration Web modules (PBI 130718).

Plain helper module (not a conftest), imported by the three
`test_qafl_membership*_web.py` modules so the ~170 field cases share one
body per shape instead of copy-pasted steps.

BASELINE DATA ("A-2")
---------------------
The cases say "baseline data (A-2)" but the suite never defines A-2. The
navigation filler below is therefore built from the cases' own literal
values where the live validator (read from the fragment script in
reports/locators/qafl_membership/qafl_membership_en.html) accepts them, and
from validator-valid equivalents where it does not:
  * Phone filler is '+974 44123456' — the live rule is ^\\+974[\\s-]?\\d{8}$,
    which rejects the cases' '+974 4412 3456'. Using the case literal as
    filler would fail ~100 Step 3-5 tests at Step 2 instead of at their
    subject. The case literal is still what the Phone cases themselves type.
  * Mobile filler is '55123456' — the live control is an 8-digit local input
    behind a fixed '+974' chip (maxlength 8).
  * Company names / person names carry `QCTEST-<tc_id>-<uuid8>` and every
    email is the QA inbox, because Step-5 tests can reach a real submit and
    the backend's duplicate guard is email + company name (a fixed name would
    be blocked as a duplicate on the second run).
Upload files are generated per test into tmp_path with
tools.fixture_factory's format-valid makers (import only) — nothing is
written under any committed fixtures/ folder.
"""

import re
import uuid
from pathlib import Path

import allure
import pytest

from core.web.design_tokens import effective_color, font_family_contains, hex_to_rgb, px_close  # noqa: F401
from tools.fixture_factory import make_docx, make_exe, make_jpg, make_pdf, make_png
from web.pages.qafl_membership.qafl_membership_page import FIELD_KINDS, QaflMembershipPage

TEST_INBOX = "heba.samir611.hs@gmail.com"
KB = 1024
MB = 1024 * 1024  # the fragment compares f.size against maxMb * 1024 * 1024

CHAR_LIMIT_SKIP = "N/A: no character limit (team decision 2026-10-03)"

EN_ACK = (
    "Your QAFL Membership Registration has been submitted successfully. Your application is currently "
    "under review. You will be contacted once the review is completed."
)
AR_ACK = "تم إرسال طلب عضوية QAFL بنجاح. طلبكم الآن قيد المراجعة. سيتم التواصل معكم بعد الانتهاء من مراجعة الطلب."

EN_SUBTITLE = (
    "Register your company for QAFL membership by providing verified company information, authorized "
    "contacts, and the required supporting documents."
)
# Labels per the PBI spec (130718.spec.json "Company Registered Under —
# Conditional Behavior") and case 146584's lookup list.
CRU_LABELS = [
    "Qatar Ministry of Commerce and Industry (MOCI)",
    "Qatar Financial Centre (QFC)",
    "Qatar Free Zones Authority (QFZ)",
    "Other",
]
COMPANY_TYPE_LABELS = ["Public", "Private", "LLC", "Non-profit", "Other"]
STEP1_MANDATORY = ("companyEnglishName", "companyArabicName", "companyRegisteredUnder", "companySize",
                   "companyType", "marketPresence")

_LATIN = re.compile(r"[A-Za-z]")


def anon(**extra):
    """Every QAFL case is a public-visitor case: run on a fresh logged-out
    context (the default `page` fixture pre-loads the CMS storageState).
    Extra keys (viewport / engine / locale) pass through to the fixture."""
    return pytest.mark.parametrize("page", [{"auth": False, **extra}], indirect=True, ids=["anon"])


def normalise(text: str) -> str:
    """Typography-only normalisation for copy comparisons: curly apostrophes,
    en/em dashes and repeated whitespace. Wording is still compared exactly."""
    return re.sub(r"\s+", " ", (text or "").replace("’", "'").replace("–", "-").replace("—", "-")).strip()


def has_latin(text: str) -> bool:
    return bool(_LATIN.search(text or ""))


def qctest_name(tc: int) -> str:
    return f"QCTEST-{tc}-{uuid.uuid4().hex[:8]}"


class FileMaker:
    """Writes a format-valid file of an exact byte size into tmp_path."""

    _MAKERS = {"pdf": make_pdf, "png": make_png, "jpg": make_jpg, "jpeg": make_jpg, "docx": make_docx,
               "doc": make_docx, "exe": make_exe}

    def __init__(self, tmp_path: Path):
        self.dir = Path(tmp_path) / "qafl_uploads"
        self.dir.mkdir(parents=True, exist_ok=True)

    def make(self, filename: str, size: int = 50 * KB) -> str:
        # Each call gets its own sub-folder, so a baseline file can never
        # overwrite a same-named subject file (e.g. cr-copy.pdf 1.2 MB vs the
        # 100 KB filler) while the upload keeps the case's exact file name.
        sub = self.dir / uuid.uuid4().hex[:8]
        sub.mkdir()
        path = sub / filename
        ext = filename.rsplit(".", 1)[-1].lower()
        path.write_bytes(self._MAKERS[ext](int(size)))
        return str(path)


# ---------------------------------------------------------------------------
# Baseline values per step (ordered: a trigger always precedes the field it
# reveals, because set_field() fills in dict order).
# ---------------------------------------------------------------------------
def _cond_values(files: FileMaker, cru: str) -> dict:
    if cru == "moci":
        return {
            "crNumber": "CR-1234567",
            "uploadCrCopy": files.make("cr-copy.pdf", 100 * KB),
            "qatarChamberMembershipNumber": "QCM-7654321",
            "uploadQatarChamberMembershipCopy": files.make("qcm-copy.pdf", 100 * KB),
            "verifiedOnQatarCommercialDirectory": "yes",
        }
    if cru == "qfc":
        return {"qfcNumber": "QFC-00123", "qfcMembershipCopy": files.make("qfc-membership.pdf", 100 * KB)}
    if cru == "qfz":
        return {"qfzNumber": "QFZ-00456", "qfzMembershipCopy": files.make("qfz-membership.pdf", 100 * KB)}
    if cru == "other":
        return {
            "companyRegisteredUnderOther": "Dubai Multi Commodities Centre",
            "companyRegisteredUnderOtherMembershipCopy": files.make("other-authority.pdf", 100 * KB),
        }
    return {}


def step_values(step: int, files: FileMaker, tc: int, cru: str = "qfc") -> dict:
    if step == 1:
        v = {
            "companyEnglishName": qctest_name(tc),
            "companyArabicName": f"QCTEST-{tc} اختبار",
            "companyRegisteredUnder": cru,
        }
        v.update(_cond_values(files, cru))
        v.update({"companySize": "medium", "companyType": {"label": "LLC"}, "marketPresence": "local"})
        return v
    if step == 2:
        return {
            "seniorExecutiveName": f"QCTEST-{tc} Senior Executive",
            "seniorExecutiveDesignation": "Chief Executive Officer",
            "seniorExecutiveEmail": TEST_INBOX,
            "seniorExecutiveConfirmEmail": TEST_INBOX,
            "seniorExecutivePhone": "+974 44123456",
            "seniorExecutiveExtension": "204",
            "seniorExecutiveMobile": "55123456",
        }
    if step == 3:
        return {
            "responsibleManagerName": f"QCTEST-{tc} Responsible Manager",
            "responsibleManagerDesignation": "Operations Manager",
            "responsibleManagerEmail": TEST_INBOX,
            "responsibleManagerConfirmEmail": TEST_INBOX,
            "responsibleManagerPhone": "+974 44123457",
            "responsibleManagerExtension": "205",
            "responsibleManagerMobile": "55123457",
        }
    if step == 4:
        return {
            "website": "https://qctest.example.com",
            "locationName": f"QCTEST-{tc} HQ",
            "buildingNumber": "12",
            "zoneNumber": "55",
            "streetNumber": "310",
        }
    if step == 5:
        return {
            "qaflMembershipAuthorizationLetter": files.make("auth-letter.pdf", 100 * KB),
            "authorizedPersonQatarIdFront": files.make("qid-front.jpg", 500 * KB),
            "authorizedPersonQatarIdBack": files.make("qid-back.jpg", 500 * KB),
        }
    raise ValueError(step)


def build(step: int, files: FileMaker, tc: int, cru: str = "qfc", override: dict | None = None,
          exclude: tuple = ()) -> dict:
    """Baseline for `step`, minus `exclude`, with `override` applied in place
    (new keys appended — after their trigger, which is always earlier)."""
    if step == 1 and ("companyRegisteredUnder" in exclude):
        v = step_values(1, files, tc, cru="none")
        v.pop("companyRegisteredUnder", None)
    else:
        v = step_values(step, files, tc, cru)
    for key in exclude:
        v.pop(key, None)
    for key, value in (override or {}).items():
        v[key] = value
    return v


def open_page(qp: QaflMembershipPage, locale: str = "en") -> None:
    with allure.step(f"Open the QAFL Membership Registration page ({locale.upper()})"):
        qp.open_registration(locale=locale)


def reach_step(qp: QaflMembershipPage, files: FileMaker, tc: int, step: int, locale: str = "en",
               cru: str = "qfc", step1_override: dict | None = None, open_first: bool = True) -> dict:
    """Open the page and complete steps 1..step-1 with baseline data. Returns
    the values entered per step (for retention checks)."""
    entered = {}
    if open_first:
        open_page(qp, locale)
    for k in range(1, step):
        with allure.step(f"Complete Step {k} with baseline data and click Next"):
            values = build(k, files, tc, cru=cru, override=step1_override if k == 1 else None)
            qp.fill(values)
            qp.click_next()
            assert qp.wait_for_step(k + 1), (
                f"precondition: could not leave Step {k} with baseline data; errors: "
                f"{ {n: qp.field_error_text(n) for n in values if qp.field_error_text(n)} }"
            )
            entered[k] = values
    return entered


def advance(qp: QaflMembershipPage, step: int) -> None:
    """Next on steps 1-4, Submit on step 5."""
    if step == 5:
        qp.click_submit()
    else:
        qp.click_next()


def _comparable(name: str, value) -> str:
    if FIELD_KINDS[name] == "file":
        return Path(value).name
    if isinstance(value, dict):
        return value.get("label", "")
    return value


def current_matches(qp: QaflMembershipPage, name: str, value) -> bool:
    """Is `value` (as entered by build()/fill()) still in the control?
    Label-selected dropdowns compare the selected option's TEXT, because
    field_value() returns the option's value key, not its label."""
    if isinstance(value, dict):
        return qp.selected_option_text(name) == value.get("label", "")
    return qp.field_value(name) == _comparable(name, value)


# ---------------------------------------------------------------------------
# Shared AAA bodies — the asserts live here, in the test layer.
# ---------------------------------------------------------------------------
def run_accepts(qp, files, tc, step, name, value, cru="qfc", extra: dict | None = None, retained: bool = True):
    """'<field> accepts <value>': no inline error, Next advances, and (where
    the case says so) the value is retained when returning with Previous."""
    reach_step(qp, files, tc, step, cru=cru)
    with allure.step(f"Enter {Path(str(value)).name if FIELD_KINDS[name] == 'file' else value!r} in {name}"):
        qp.fill(build(step, files, tc, cru=cru, override={name: value, **(extra or {})}))
        if FIELD_KINDS[name] == "text":
            qp.blur(name)
    with allure.step("Value accepted with no inline error"):
        assert qp.has_no_field_error(name), f"{name} shows an error for a valid value: {qp.field_error_text(name)!r}"
        if FIELD_KINDS[name] == "file":
            assert Path(value).name in qp.attached_file_names(name), f"{name}: file not shown as attached"
    with allure.step("Click Next"):
        qp.click_next()
        assert qp.wait_for_step(step + 1), (
            f"wizard did not advance from Step {step}; {name} error: {qp.field_error_text(name)!r}"
        )
    if retained:
        with allure.step("Click Previous; value is retained"):
            qp.click_previous()
            assert qp.wait_for_step(step)
            assert current_matches(qp, name, value), (
                f"{name} not retained after Previous: {qp.field_value(name)!r} != {_comparable(name, value)!r}"
            )


def run_blocked(qp, files, tc, step, name, cru="qfc", override: dict | None = None, exclude: tuple = (),
                blur_first: bool = False, label: str = "required"):
    """Shared body for empty / whitespace / invalid-format / mismatch cases:
    fill the step, click Next (Submit on Step 5), inline error under `name`,
    user stays on the step."""
    reach_step(qp, files, tc, step, cru=cru)
    values = build(step, files, tc, cru=cru, override=override, exclude=exclude)
    with allure.step(f"Fill Step {step} ({label} case for {name})"):
        qp.fill(values)
    if blur_first:
        with allure.step(f"Tab out of {name}: real-time inline error"):
            qp.blur(name)
            assert qp.has_field_error(name), f"no real-time inline error under {name} on blur"
    with allure.step("Click " + ("Submit" if step == 5 else "Next")):
        advance(qp, step)
    with allure.step(f"Inline {label} error under {name}; user stays on Step {step}"):
        assert qp.has_field_error(name), f"no inline {label} error under {name}"
        assert qp.current_step() == step, f"wizard left Step {step} despite invalid {name}"
        if step == 5:
            assert not qp.is_ack_visible(), "the application was submitted despite the invalid field"


def run_required(qp, files, tc, step, name, cru="qfc", extra_exclude: tuple = ()):
    run_blocked(qp, files, tc, step, name, cru=cru, exclude=(name,) + tuple(extra_exclude), label="required")


def run_whitespace(qp, files, tc, step, name, cru="qfc", value="   ", extra: dict | None = None):
    run_blocked(qp, files, tc, step, name, cru=cru, override={name: value, **(extra or {})}, label="required")


def run_invalid(qp, files, tc, step, name, bad_values, cru="qfc", extra: dict | None = None):
    """One or more invalid values, each: Tab out -> real-time inline error,
    Next blocked."""
    reach_step(qp, files, tc, step, cru=cru)
    qp.fill(build(step, files, tc, cru=cru, override={name: bad_values[0], **(extra or {})}))
    for bad in bad_values:
        with allure.step(f"Enter {bad!r} in {name} and Tab out"):
            qp.type_into(name, bad)
            qp.blur(name)
            assert qp.has_field_error(name), f"no real-time inline error under {name} for {bad!r}"
        with allure.step("Click Next: blocked"):
            advance(qp, step)
            assert qp.current_step() == step, f"wizard advanced with {name} = {bad!r}"
            assert qp.has_field_error(name)


def run_non_numeric(qp, files, tc, step, name, bad, cru="qfc", extra: dict | None = None):
    """'<field> rejects non-numeric <bad>': the letters are either not
    accepted (stripped) or flagged; Next then shows an inline numeric-format
    error and stays on the step."""
    reach_step(qp, files, tc, step, cru=cru)
    qp.fill(build(step, files, tc, cru=cru, override={name: "", **(extra or {})}))
    with allure.step(f"Type {bad!r} in {name}"):
        qp.press_sequentially(name, bad)
        qp.blur(name)
        value = qp.field_value(name)
        assert not re.search(r"[A-Za-z]", value) or qp.has_field_error(name), (
            f"letters accepted into {name} with no inline error: {value!r}"
        )
    with allure.step("Click Next: inline numeric-format error, Next blocked"):
        advance(qp, step)
        assert qp.has_field_error(name), f"no inline numeric-format error under {name}"
        assert qp.current_step() == step, f"wizard advanced with {name} = {bad!r}"


def run_char_limit(qp, files, tc, step, name, max_len, char="A", cru="qfc", extra: dict | None = None):
    """Kept for completeness; every caller is skipped N/A (no char limits)."""
    reach_step(qp, files, tc, step, cru=cru)
    qp.fill(build(step, files, tc, cru=cru, override={name: char * max_len, **(extra or {})}))
    qp.click_next()
    assert qp.wait_for_step(step + 1)
    qp.click_previous()
    qp.type_into(name, char * (max_len + 1))
    qp.click_next()
    assert len(qp.field_value(name)) <= max_len or qp.has_field_error(name)


def run_file_type_rejected(qp, files, tc, step, name, bad_filename, cru="qfc"):
    reach_step(qp, files, tc, step, cru=cru)
    qp.fill(build(step, files, tc, cru=cru, exclude=(name,)))
    with allure.step(f"Upload {bad_filename} in {name}"):
        qp.attach(name, files.make(bad_filename, 100 * KB))
    with allure.step("Inline file-type error; file not attached"):
        assert qp.has_field_error(name), f"no inline file-type error for {bad_filename}"
        assert bad_filename not in qp.attached_file_names(name), f"{bad_filename} stayed attached to {name}"
    with allure.step("Click " + ("Submit" if step == 5 else "Next") + ": blocked"):
        advance(qp, step)
        assert qp.current_step() == step, f"wizard advanced with no valid file in {name}"
        if step == 5:
            assert not qp.is_ack_visible(), "the application was submitted with no valid file"


def run_file_size(qp, files, tc, step, name, ok_filename, bad_filename, cru="qfc"):
    """4.99 MB accepted; replacing it with 5.01 MB is rejected with an inline
    size error and the 5.01 MB file is not attached."""
    reach_step(qp, files, tc, step, cru=cru)
    qp.fill(build(step, files, tc, cru=cru, exclude=(name,)))
    with allure.step(f"Upload {ok_filename} (4.99 MB)"):
        qp.attach(name, files.make(ok_filename, 4.99 * MB))
        assert qp.has_no_field_error(name), f"4.99 MB rejected: {qp.field_error_text(name)!r}"
        assert ok_filename in qp.attached_file_names(name), "4.99 MB file not attached"
    with allure.step(f"Replace it with {bad_filename} (5.01 MB)"):
        qp.attach(name, files.make(bad_filename, 5.01 * MB))
        assert qp.has_field_error(name), "5.01 MB file accepted with no inline size error"
        assert bad_filename not in qp.attached_file_names(name), "5.01 MB file is attached"


def fill_all_and_submit(qp, files, tc, locale="en", cru="qfc", overrides: dict | None = None) -> int | None:
    """Complete all five steps (QCTEST identity, QA inbox), click Submit and
    wait for the submit POST. Returns its HTTP status (None = no request
    sent). `overrides` maps step -> override dict."""
    overrides = overrides or {}
    open_page(qp, locale)
    for k in range(1, 6):
        with allure.step(f"Complete Step {k}"):
            qp.fill(build(k, files, tc, cru=cru, override=overrides.get(k)))
            if k < 5:
                qp.click_next()
                assert qp.wait_for_step(k + 1), f"precondition: could not leave Step {k}"
    with allure.step("Click Submit (CAPTCHA is the shared invisible/score widget, no interaction)"):
        status = qp.submit_and_wait_response()
        allure.attach(str(status), "submit HTTP status", allure.attachment_type.TEXT)
        return status


# ---------------------------------------------------------------------------
# Figma token helpers — tolerances per .claude/context/active/bug-rules.md:
# layout ±2 px, images/icons ±5 px, text exact, colours exact.
# ---------------------------------------------------------------------------
LAYOUT_TOL = 2
IMAGE_TOL = 5
FONT_PROPS = ["fontFamily", "fontSize", "fontWeight", "lineHeight", "color", "opacity"]


def font_mismatches(st: dict, size=None, weight=None, line_height=None, color=None, family="Cairo") -> list:
    out = []
    if family and not font_family_contains(st.get("fontFamily", ""), family):
        out.append(f"family {st.get('fontFamily')!r} != {family}")
    if size is not None and not px_close(st.get("fontSize", ""), f"{size}px", LAYOUT_TOL):
        out.append(f"size {st.get('fontSize')} != {size}px")
    if weight is not None and str(st.get("fontWeight")) != str(weight):
        out.append(f"weight {st.get('fontWeight')} != {weight}")
    if line_height is not None and not px_close(st.get("lineHeight", ""), f"{line_height}px", LAYOUT_TOL):
        out.append(f"line-height {st.get('lineHeight')} != {line_height}px")
    if color is not None and st.get("color") != hex_to_rgb(color):
        out.append(f"color {st.get('color')} != {hex_to_rgb(color)} ({color})")
    return out


def box_mismatches(box: dict, width=None, height=None, tol=LAYOUT_TOL) -> list:
    out = []
    if not box:
        return ["element has no bounding box (not rendered)"]
    if width is not None and abs(box["width"] - width) > tol:
        out.append(f"width {box['width']:.1f} != {width}±{tol}")
    if height is not None and abs(box["height"] - height) > tol:
        out.append(f"height {box['height']:.1f} != {height}±{tol}")
    return out


def rgb(hex_color: str) -> str:
    return hex_to_rgb(hex_color)


def ltr_readable(qp: QaflMembershipPage, name: str) -> bool:
    """An LTR value (email / phone / URL) inside an RTL page stays readable
    when the control renders it LTR: computed direction ltr, a dir=ltr/auto
    attribute, or unicode-bidi plaintext."""
    st = qp.style(qp.CONTROL.format(name=name), ["direction", "unicodeBidi"])
    dir_attr = (qp.get_attribute(qp.CONTROL.format(name=name), "dir") or "").lower()
    return st["direction"] == "ltr" or dir_attr in ("ltr", "auto") or st["unicodeBidi"] == "plaintext"


def visibility_snapshot(qp: QaflMembershipPage, step: int = 1) -> list:
    return qp.visible_field_names(step)
