"""
cms/tests/chambers_law/law_entry_form.py -- the Object Authoring form probe
(`_LawEntryForm`) and the rejection-detection contract it reads against.

MOVED 2026-10-12 out of test_chambers_law_field_validation.py, verbatim, so
no test module imports another test module (test_chambers_law_control_panel.py
used to import it from there). Both Chamber's Law test modules import it from
here. Not a test module: pytest collects nothing in this file.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from core.utils.waits import wait_until


def _log_submit(authoring, note: str) -> None:
    """Logs a Submit for Publishing on a Law Entry BEFORE the click (user
    decision 2026-10-13: every persisted -- or possibly persisted -- write to
    reports/live-writes-20261013.jsonl). The test case id is inferred from
    the running test's name."""
    from cms.tests.live_write_guard import LiveRecord, log_live_write

    code = getattr(authoring, "_entry_code", None) or "<new entry (create form)>"
    log_live_write(LiveRecord("law-entry", code, f"Law Entry {code}"), "<form submit>",
                   "the values entered by the test", None, action="publish", note=note)

# ---- Wait budgets the probe uses (moved with it) --------------------------
# A refusal is rendered by client-side JS right after the click; the form's
# own settle already spends ~2.5s, so this is a short, real poll on top.
REFUSAL_RENDER_TIMEOUT = 20.0
# The CREATE path is slower than an edit BY DESIGN and needs its own budget
# (read off the page's own `submitWithoutFollowingRedirect()`, 2026-09-16 --
# see `_LawEntryForm.submit_new_entry_outcome()`): the native multipart POST
# is retargeted into a hidden iframe, the page then asks the Object for its
# entry count a second time to decide whether anything was written, and it
# arms an 8000ms belt timer for the case where the iframe never reports a
# `load` at all. 8s belt + the count round-trip + the landing page's own
# render is comfortably inside this; `REFUSAL_RENDER_TIMEOUT`'s 20s is not.
CREATE_OUTCOME_TIMEOUT = 60.0
# ...and once the create landing HAS rendered, its bars are put there by the
# entries-list fetch that follows the navigation, not by the navigation
# itself. Sampling the instant the blank form appears samples too early, so
# the reader waits for a bar on its own terms -- bounded, and it stops the
# moment one renders. Expiring is not an error: no bar at all is precisely
# the observation 134978 needs to report.
CREATE_LANDING_BAR_TIMEOUT = 20.0
# The picker's own upload round-trip (set_input_files -> server upload ->
# either the "1 of 1" count or a rejection message).
PICKER_RESULT_TIMEOUT_MS = 25000


# =========================================================================
# Upload-rejection detection -- the contract the pickers are read against
# =========================================================================
# EXACTLY TWO things count as "this upload was rejected":
#
#   1. rendered text matching the SIZE-FEEDBACK FAMILY below -- the live
#      literal is "Please enter a file with a valid file size no larger
#      than 1 MB." (read off `data-file-size-feedback` on this form); or
#   2. rendered text repeating one of the strings the upload markup ITSELF
#      declares as user feedback, in a `data-*-feedback` attribute.
#
# It is deliberately NOT "any text rendered inside the picker". That older,
# far broader reading is what the 2026-09-15 run actually captured, four
# times over, and reported as a size rejection:
#
#   "Info: / <Arabic> / Set English (United States) as your preferred
#    language."
#
# -- this account's LANGUAGE-PREFERENCE notice, nothing to do with uploads.
# 134942 therefore failed at step 2 and the size boundary was never
# exercised at all. Neither rule above can match that notice: it contains
# no "valid file size no larger than <N> MB", and it is not the value of
# any `*-feedback` attribute. Rule 2 is also what keeps detection
# LANGUAGE-INDEPENDENT (this account leaks Arabic into an English UI)
# without widening it -- the product's own declared string is matched
# whatever language it ships in, while the ASSERTION still checks the
# English literal the case demands.
#
# The field's visible help line, "Upload a .jpg,.png,.svg no larger than
# 1 MB.", must NOT be read as a rejection -- it is always on screen. It
# does not match: the family below requires the words "valid file size",
# which the help line does not contain.
# The picker's format refusal (live 2026-10-13): "Please enter a file with a
# valid extension (.jpg,.png,.svg)."
EXTENSION_REJECTION_RE = re.compile(r"valid\s+extension", re.IGNORECASE)
SIZE_REJECTION_RE = re.compile(
    r"valid\s+file\s+size\s+no\s+larger\s+than\s*[0-9]+(?:[.,][0-9]+)?\s*MB"
    # live 2026-10-13: '"icon-oversize.png" is 1.1 MB. Law Icon accepts files
    # up to 1 MB - choose a smaller file.'
    r"|accepts\s+files\s+up\s+to\s*[0-9]+(?:[.,][0-9]+)?\s*MB",
    re.IGNORECASE,
)


class _PickerOutcome(NamedTuple):
    """What the Documents & Media picker reported about one upload."""

    rejection: str   # the SPECIFIC feedback message, "" when none rendered
    accepted: bool   # the picker positively reported the file as uploaded
    picker_text: str # whole picker text, captured BEFORE the picker closes
                     # -- for the FAILURE REPORT only, never asserted on


# =========================================================================
# Form probe -- the ONLY place in this module that touches raw Playwright
# =========================================================================
class _LawEntryForm:
    """CONSOLIDATE: every method here is GENERIC Object-Authoring behaviour
    and belongs on `cms/pages/components/object_authoring_page.py`
    (suggested names in each docstring). It lives here only because that
    file was owned by another engineer while this batch was written. No
    test body below touches `self.page` / `playwright` directly -- raw
    Playwright stays inside this class, which is the same contract
    `BasePage` / `ObjectAuthoringPage` hold."""

    # Confirmed live 2026-09-15: the page's own `banner()` helper creates
    # `<div data-qc-oel-editbar>` for BOTH the editing banner and every save
    # message, so these must be matched on TEXT, not on the attribute.
    EDIT_BAR = "[data-qc-oel-editbar]"
    # ---- THE THREE PLACES A REFUSAL IS ACTUALLY RENDERED -----------------
    # (read off the page's own shipped JS, 2026-09-15 -- see the
    # "WHERE A REFUSAL IS RENDERED" block in the module docstring)
    #
    # 1. UNDER THE BOX. `fieldError(control, message)` builds
    #    `document.createElement('div')`, sets `data-qc-oel-field-error`
    #    (its own `FIELD_ERROR_ATTR`) and `role="alert"`, gives it NO class,
    #    and inserts it after the control. `reportComplaints()` sends EVERY
    #    message it can tie to a field there -- both the page's own local
    #    complaints AND a plain-text named-rule message from `/validate`,
    #    which `controlForMessage()` matches to a control by the longest
    #    field label (either language) or field name occurring in it.
    #    The page's own comment: "ADO 141960 - each message under the box it
    #    is about; the bar is kept for whatever cannot be tied to a field".
    # 2. THE RED BAR. Only what `controlForMessage()` could NOT place --
    #    "a rule that names none, the server's bare refusal".
    # 3. LIFERAY'S OWN FRAGMENT ERROR. The INPUTS-text/textarea fragment
    #    calls `showInputError({errorType:'length', ...})`, which un-hides
    #    `<p id="...-error" class="... text-danger sr-only">` by dropping
    #    `sr-only`. Independent of the page's own machinery entirely.
    FIELD_ERROR_NOTE = "[data-qc-oel-field-error]"
    FRAGMENT_ERROR_NOTE = 'p[id$="-error"].text-danger:not(.sr-only)'
    # Both shipped languages of every bar literal. `t(en, ar)` picks by
    # `document.documentElement.lang`, and on qcdev the shared authoring
    # account renders `ar-SA` unless the URL pins `/en` -- so an
    # English-only prefix match is blind half the time.
    SAVE_REFUSED_PREFIXES = (
        "This record was not saved:",
        "لم يتم حفظ هذا السجل:",
    )
    # Kept as the single-string form the pre-2026-09-15 reader used, because
    # a few call sites still read it for reporting.
    SAVE_REFUSED_PREFIX = SAVE_REFUSED_PREFIXES[0]
    PUBLISHED_MESSAGES = (
        "Saved and submitted for publishing.",
        "تم الحفظ وإرساله للنشر.",
    )
    DRAFT_SAVED_MESSAGES = ("Draft saved.", "تم حفظ المسودة.")
    PUBLISHED_MESSAGE = PUBLISHED_MESSAGES[0]
    DRAFT_SAVED_MESSAGE = DRAFT_SAVED_MESSAGES[0]
    # Same picker iframe ObjectAuthoringPage.upload_file() drives.
    PICKER_IFRAME = 'iframe[src*="selectFileEntry"]'
    # The form's value=0 submit (Publish / Submit for Review / نشر), read by
    # attribute -- the same control ChambersLawAdminPage.PUBLISH_SUBMIT names.
    PUBLISH_SUBMIT = 'button[type="submit"][name="status"][value="0"]'
    PICKER_UPLOADED_COUNT_TEXT = "1 of 1"
    # An upload-feedback string the product declares about ITSELF lives in a
    # `data-*-feedback` attribute -- `data-file-size-feedback` is the one
    # read live on this form. Harvested by attribute-name SUFFIX, so no
    # attribute name is guessed: whatever the fragment declares is found.
    FEEDBACK_ATTR_SUFFIX = "-feedback"
    # ...and the size one is identified by its attribute NAME, not by its
    # wording, so an Arabic-rendered message is still classified correctly.
    SIZE_FEEDBACK_ATTR_TOKEN = "size"
    _COLLECT_FEEDBACK_JS = """
    (root) => {
      const doc = root.ownerDocument || root;
      const out = [];
      for (const el of doc.querySelectorAll('*')) {
        for (const attr of el.attributes) {
          if (!attr.name.endsWith('-feedback')) continue;
          const value = (attr.value || '').trim();
          if (value.length > 10) out.push([attr.name, value]);
        }
      }
      return out;
    }
    """

    def __init__(self, authoring):
        self._authoring = authoring
        self._page = authoring.page

    # ---- Save messages ---------------------------------------------------
    def _visible_texts(self, selector: str) -> list:
        """Every VISIBLE, non-empty rendered text matching `selector`.

        Visibility is checked per element, because these renderers leave
        their container in the DOM when there is nothing to say (Liferay's
        fragment note is `sr-only` until it fires; the page's own notes are
        removed on the next `input` event). Reading text out of a hidden
        element would invent a refusal that is not on screen."""
        found = self._page.locator(selector)
        out = []
        for index in range(found.count()):
            element = found.nth(index)
            try:
                if not element.is_visible():
                    continue
                text = (element.inner_text() or "").strip()
            except Exception:  # noqa: BLE001 -- a node that vanished mid-read
                continue
            if text:
                out.append(text)
        return out

    def _bar_texts(self) -> list:
        bars = self._page.locator(self.EDIT_BAR)
        return [bars.nth(i).inner_text() for i in range(bars.count())]

    def field_error_texts(self) -> tuple:
        """The per-field notes the page renders UNDER the box they are about
        -- `<div data-qc-oel-field-error role="alert">`.

        THIS IS THE READ THE OLD REFUSAL READER DID NOT HAVE, and its
        absence produced a false "refused silently, no message" verdict that
        a product bug (#141989) was filed on. That bug is now closed as Not
        a Bug: the message WAS on screen, in one of these notes -- outside
        any editbar, in a class-less `<div>`, with no
        "This record was not saved:" prefix to match on.

        Everything `reportComplaints()` can tie to a field lands here, which
        is nearly everything: the Object's named-rule messages relayed from
        `/validate` (matched to their control by field label), the page's own
        URL complaints, its max-length backstop and its required-attachment
        check. Only a message naming no field falls through to the bar."""
        return tuple(self._visible_texts(self.FIELD_ERROR_NOTE))

    def fragment_error_texts(self) -> tuple:
        """Liferay's OWN INPUTS-* fragment error (`showInputError`), which
        un-hides `<p id="...-error" class="text-danger sr-only">` by dropping
        `sr-only`. A third, entirely independent renderer -- it is what
        reports the fragment's own declared `maxLength` on a text input."""
        return tuple(self._visible_texts(self.FRAGMENT_ERROR_NOTE))

    def refusal_bar_text(self) -> str:
        """Text of the RED refusal BAR only, or "".

        This is the pre-2026-09-15 reader, kept as its own named read --
        deliberately narrowed to the bar -- so a caller can still tell a
        bar-level refusal (a rule naming no field, or the server's bare
        refusal) from an under-the-box one. BOTH shipped languages of the
        prefix are matched now: `t()` picks by
        `document.documentElement.lang`, which is `ar-SA` for the shared
        qcdev authoring account unless the URL pins `/en`, so an
        English-only match was blind half the time on its own terms."""
        for text in self._bar_texts():
            if any(prefix in text for prefix in self.SAVE_REFUSED_PREFIXES):
                return text
        return ""

    def save_refusal_text(self) -> str:
        """CONSOLIDATE -> `ObjectAuthoringPage.save_refusal_text()`.
        EVERYTHING the page is currently saying about why the save did not go
        through, from ALL THREE renderers, joined with " | ", or "" when it
        is saying nothing.

        WIDENED 2026-09-15. It used to read `[data-qc-oel-editbar]` only, and
        only match the English prefix "This record was not saved:", so it
        returned "" for every message rendered under a box -- which is where
        the page puts almost all of them. Verified by hand against this very
        form: 201 characters in Law Title (EN) and 501 in Law Description
        (EN) each render a visible message ("Law Title must not exceed 200
        characters" / "Law Description must not exceed 500 characters"),
        still on screen at 0.5s / 2s / 5s, with the value correctly NOT
        stored -- and the old reader saw NONE of it and reported "refused
        silently".

        Field notes come first and the bar last on purpose: the note is the
        specific, field-named message; the bar is the fallback."""
        parts = list(self.field_error_texts()) + list(self.fragment_error_texts())
        bar = self.refusal_bar_text()
        if bar:
            parts.append(bar)
        return " | ".join(parts)

    def success_message_text(self) -> str:
        """CONSOLIDATE -> `ObjectAuthoringPage.success_message_text()`. The
        confirmation the page carries across its own post-save redirect
        ("Saved and submitted for publishing." / "Draft saved.", or either
        one's Arabic twin), or ""."""
        wanted = self.PUBLISHED_MESSAGES + self.DRAFT_SAVED_MESSAGES
        for text in self._bar_texts():
            if any(message in text for message in wanted):
                return text
        return ""

    def bar_texts(self) -> tuple:
        """EVERY `[data-qc-oel-editbar]` on the page right now, verbatim and
        UNFILTERED -- no prefix match, no message whitelist.

        The four named readers above each answer "is MY message here?", and
        when all four answer no they cannot tell "the page said nothing"
        apart from "the page said something none of us recognises". On the
        CREATE landing that distinction is the whole finding, so the raw
        read exists as its own named method and is printed by
        `create_message_report()`. Reporting only -- never asserted on."""
        return tuple(
            text.strip() for text in self._bar_texts() if text and text.strip()
        )

    def save_message_report(self) -> str:
        """A one-string, attach-to-Allure breakdown of WHICH renderer said
        WHAT -- so a failure report never again leaves a reader guessing
        whether "no message" meant "the page said nothing" or "the reader
        was not looking there"."""
        return (
            f"under-the-box notes={self.field_error_texts()!r}; "
            f"fragment notes={self.fragment_error_texts()!r}; "
            f"refusal bar={self.refusal_bar_text()!r}; "
            f"success bar={self.success_message_text()!r}"
        )

    def create_message_report(self) -> str:
        """`save_message_report()` plus the UNFILTERED bar read.

        Used by the create flow only. The 2026-09-15 run of 134978 reported
        four empty renderers for a save that demonstrably landed, which left
        no way to tell whether the create landing renders nothing at all or
        renders something the named readers do not match -- so the raw bars
        are now part of the create report."""
        return (
            f"{self.save_message_report()}; "
            f"EVERY bar rendered={self.bar_texts()!r}"
        )

    def wait_for_save_outcome(self, timeout: float = REFUSAL_RENDER_TIMEOUT) -> str:
        """Polls until the page reports EITHER outcome, and returns
        "refused" / "saved" / "none". "none" is a real, reportable result
        (it is what a natively-blocked submit looks like -- stage 2a in the
        module docstring), never an error.

        Now that `save_refusal_text()` reads all three renderers, "refused"
        fires on an under-the-box note too, so a message-carrying refusal can
        no longer be misreported as "none"/silent."""
        outcome = {"value": "none"}

        def _settled() -> bool:
            if self.save_refusal_text():
                outcome["value"] = "refused"
                return True
            if self.success_message_text():
                outcome["value"] = "saved"
                return True
            return False

        try:
            wait_until(_settled, timeout=timeout, poll=1.0)
        except Exception:  # noqa: BLE001 -- "neither appeared" is itself a result
            pass
        return outcome["value"]

    # ---- Native (browser) constraint state -------------------------------
    def _control(self, field_label: str, role: str = "textbox"):
        return self._page.get_by_role(
            role, name=self._authoring.label_pattern(field_label)
        )

    def native_validation_message(self, field_label: str, role: str = "textbox") -> str:
        """CONSOLIDATE -> `ObjectAuthoringPage.native_validation_message()`.
        The BROWSER's own constraint message for a control
        (`el.validationMessage`), "" when the control is currently valid.
        This is the only readable trace of stage 2a: `reportValidity()`
        paints a native bubble that is not in the DOM, so a test can only
        observe the constraint state on the element itself."""
        return self._control(field_label, role).evaluate(
            "el => el.validity && !el.validity.valid "
            "? (el.validationMessage || 'invalid') : ''"
        )

    def is_value_missing(self, field_label: str, role: str = "textbox") -> bool:
        """True when the control fails the browser's `required` check."""
        return bool(
            self._control(field_label, role).evaluate(
                "el => !!(el.validity && el.validity.valueMissing)"
            )
        )

    def attachment_validation_message(self, field_label: str) -> str:
        """Same as native_validation_message(), for an ATTACHMENT field --
        whose real control is the `sr-only`
        `<input name="ObjectField_...">` addressed as
        "<Field Label> Select File" (confirmed live: exactly one match)."""
        return self._page.get_by_role(
            "textbox", name=f"{field_label} Select File"
        ).evaluate(
            "el => el.validity && !el.validity.valid "
            "? (el.validationMessage || 'invalid') : ''"
        )

    def max_length_attribute(self, field_label: str) -> str:
        """CONSOLIDATE -> `ObjectAuthoringPage.max_length_attribute()`. The
        control's own `maxlength`, or "" -- the signal that decides which
        half of 134946/134950's either/or expected result applies (a field
        that caps typing vs one that refuses on save)."""
        return self._control(field_label).get_attribute("maxlength") or ""

    def live_value(self, field_label: str) -> str:
        """Value currently IN the box, without re-navigating -- used to see
        whether an over-long fill was truncated by the control itself."""
        return self._control(field_label).input_value()

    def text_direction(self, field_label: str) -> str:
        """CONSOLIDATE -> `ObjectAuthoringPage.text_direction()`. The
        direction the control RENDERS in -- the browser's own computed
        `direction`, falling back to the element's `dir` attribute when a
        computed value is unavailable.

        Added for 134964, the one case in this module whose expected result
        names rendering and not just storage ("the Arabic text intact and
        rendered right-to-left in the text area"). Read live 2026-09-15:
        `#qc-ar-lawDescription` carries `dir="rtl"` and `lang="ar"` while
        its English twin carries `dir="ltr"`, so this is an observable
        product property, not an inferred one."""
        return self._control(field_label).evaluate(
            "el => (getComputedStyle(el).direction || el.getAttribute('dir') "
            "|| '').toLowerCase()"
        )

    def tag_name(self, field_label: str) -> str:
        """CONSOLIDATE -> `ObjectAuthoringPage.tag_name()`. The control's own
        tag, lower-cased -- how batch 4 PROVES, at runtime, that Law
        Description is a plain `<textarea>` and not a rich-text editor
        (confirmed live 2026-09-15; see finding (f) in the module
        docstring). A rich-text field on this surface is a CKEditor
        `iframe`, never a textarea, so this single read distinguishes them
        and stops a silently-changed field shape from being mistaken for a
        product bug."""
        return self._control(field_label).evaluate("el => el.tagName.toLowerCase()")

    # ---- Numeric control state (batch 6) ---------------------------------
    # CONSOLIDATE -> `ObjectAuthoringPage`. Display Order is the object's one
    # `<input type="number">`, and it behaves differently enough from a text
    # box that the text-shaped helpers above cannot serve it: `fill()`
    # REFUSES a non-numeric string outright, and the browser's own constraint
    # set (`stepMismatch`, `rangeUnderflow`, `valueMissing`) is where three of
    # batch 6's four refusals actually happen. See finding (s).

    def number_validity(self, field_label: str) -> dict:
        """The BROWSER's full constraint verdict on a numeric control -- the
        only observable trace of stage 2a, which paints a native bubble that
        is not in the DOM.

        Returned as a dict rather than a bare message because batch 6 has to
        tell the three native refusals APART: `stepMismatch` (2.5 -- a
        malformed integer), `rangeUnderflow` (a value below `min`, which on
        this control CANNOT fire -- `min` is INT_MIN, see finding (s)), and
        `valueMissing` (an empty box, or a box the control refused to let
        anything be typed into).

        `readonly`/`disabled` ride along because 134972 step 1's expected
        result is "the record opens with Display Order EDITABLE", and that
        is a property of the control, not of the value. Resolving at all is
        the other half of the same check: this read goes through
        `get_by_role("spinbutton", name=label_pattern(...))`, which is
        STRICT -- zero matches raise, and so do two -- so a dict coming back
        already proves exactly one Display Order control exists."""
        return self._control(field_label, role="spinbutton").evaluate(
            "el => ({value: el.value, valid: !!(el.validity && el.validity.valid),"
            " readonly: el.readOnly === true, disabled: el.disabled === true,"
            " badInput: !!(el.validity && el.validity.badInput),"
            " stepMismatch: !!(el.validity && el.validity.stepMismatch),"
            " rangeUnderflow: !!(el.validity && el.validity.rangeUnderflow),"
            " valueMissing: !!(el.validity && el.validity.valueMissing),"
            " message: el.validationMessage || '',"
            " min: el.getAttribute('min') || '', max: el.getAttribute('max') || '',"
            " step: el.getAttribute('step') || ''})"
        )

    def type_into_number(self, field_label: str, text: str) -> str:
        """Types `text` into a numeric control THE WAY A PERSON WOULD --
        click, select-all, keystrokes -- and returns what the box actually
        holds afterwards.

        REQUIRED, not a stylistic choice: `ObjectAuthoringPage.fill_number()`
        goes through Playwright's `fill()`, which raises
        `Error: Cannot type text into input[type=number]` for a value like
        "two" and so can never reach the product's own behaviour at all.
        Typed instead, the control silently DISCARDS every non-numeric
        keystroke and the box stays empty (measured live -- finding (s)).
        "The box would not accept it" and "the save was refused" are two
        different product outcomes, and 134974 has to be able to report
        WHICH one happened."""
        control = self._control(field_label, role="spinbutton")
        control.click()
        self._page.keyboard.press("Control+a")
        self._page.keyboard.type(text, delay=30)
        return control.input_value()

    def live_number_value(self, field_label: str) -> str:
        """Value currently IN the numeric box, without re-navigating -- the
        spinbutton twin of `live_value()`, used to see whether the control
        itself mangled or dropped what was entered."""
        return self._control(field_label, role="spinbutton").input_value()

    # ---- "Is there an ID control on this form at all?" (batch 7) ----------
    ID_LABEL_RE = r"(^|[^A-Za-z])(ID|IDs|Identifier)([^A-Za-z]|$)"

    def identifier_controls(self) -> tuple:
        """Every non-hidden form control whose own label, `name` or `id`
        mentions an identifier, as `(label, name, readonly, disabled)`
        tuples -- empty when the form renders none.

        134978 asks whether the Law Entry ID is "read-only or absent from
        the edit form". Those are two different answers and this read
        returns whichever is true, POSITIVELY: an empty tuple is the
        evidence that the field is absent, where a `get_by_role(...)` lookup
        for a control that does not exist could only ever produce a timeout
        and no information. Confirmed live 2026-09-16: this returns EMPTY on
        `manage-law-entry` -- finding (y)."""
        return tuple(
            tuple(row)
            for row in self._page.evaluate(
                """(pattern) => {
                  const re = new RegExp(pattern);
                  const out = [];
                  for (const el of document.querySelectorAll('form input, form select, form textarea')) {
                    if (el.type === 'hidden') continue;
                    let label = '';
                    if (el.id) {
                      const l = document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
                      if (l) label = (l.innerText || '').trim();
                    }
                    if (!label && el.closest('label')) label = (el.closest('label').innerText || '').trim();
                    const haystack = [label, el.name || '', el.id || ''].join(' ');
                    if (!re.test(haystack)) continue;
                    out.push([label, el.name || el.id || '', el.readOnly === true, el.disabled === true]);
                  }
                  return out;
                }""",
                self.ID_LABEL_RE,
            )
        )

    def visible_control_labels(self) -> tuple:
        """Every non-hidden form control's rendered label, in DOM order --
        the FULL field inventory of whatever record is open.

        Attached to 134978's report so "there is no Law Entry ID control"
        is backed by the list of controls there ARE, rather than by an
        absence nobody can check."""
        return tuple(
            self._page.evaluate(
                """() => {
                  const out = [];
                  for (const el of document.querySelectorAll('form input, form select, form textarea')) {
                    if (el.type === 'hidden' || el.type === 'search') continue;
                    let label = '';
                    if (el.id) {
                      const l = document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
                      if (l) label = (l.innerText || '').trim();
                    }
                    if (!label && el.closest('label')) label = (el.closest('label').innerText || '').trim();
                    if (label) out.push(label);
                  }
                  return out;
                }"""
            )
        )

    # ---- Lifecycle without a success assumption --------------------------
    def submit_expecting_refusal(self) -> str:
        """CONSOLIDATE -> `ObjectAuthoringPage.submit_for_publishing(
        expect_success=False)`. Clicks Submit for Publishing and settles,
        WITHOUT waiting for an Approved status -- a refused save never
        reaches one, and `wait_for_status()` would burn its whole budget
        before failing for the wrong reason."""
        _log_submit(self._authoring, "Submit for Publishing (the case decides whether it must be refused)")
        # By the Liferay `status` value, not the label (FIX 2026-10-13, 134969's
        # Arabic step: the button reads "نشر" there, so the English
        # "Submit for Review" / "Publish" text match timed out). Same control.
        self._authoring.submit_via(self.PUBLISH_SUBMIT)
        return self.wait_for_save_outcome()

    # ---- CREATE-path outcome (this module's ONE create flow) -------------
    # CONFIRMED LIVE 2026-09-16 -- read off the manage page's own shipped
    # JavaScript (`submitWithoutFollowingRedirect()`, `rememberSaved()`,
    # `announceSaved()`) plus a live, non-destructive read of the create
    # form itself on `/en/web/qatar-chamber/manage-law-entry`. A CREATE does
    # NOT save the way an EDIT does, and `wait_for_save_outcome()` -- which
    # is correct for the other 39 tests here, every one of which edits an
    # existing record -- cannot see a create succeed:
    #
    #   EDIT (`?editEntry=<erc>` in the URL) is intercepted by the entry-list
    #   fragment and written through `PUT <rest>/<id>`. On a 200 that branch
    #   calls `rememberSaved(...)`, parking "Saved and submitted for
    #   publishing." / "Draft saved." in `sessionStorage['qc-oel-saved']`,
    #   and the landing replays it via `announceSaved()` -> `banner(...)`.
    #   THAT bar is the one `success_message_text()` reads.
    #
    #   CREATE (no `editEntry`) never reaches that code at all. Liferay's own
    #   form -- confirmed live, `action=".../c/portal/edit_info_item"`,
    #   `backURL="/en/web/qatar-chamber/manage-law-entry"` -- is retargeted at
    #   a hidden iframe so the portal's 302 to `https://localhost/...` cannot
    #   strand the editor, and the page then decides the outcome ITSELF by
    #   asking the Object for its entry count a second time:
    #     * count GREW  -> `go()` -> `window.location.href = backURL`, i.e. it
    #       navigates back to the SAME manage URL and re-renders a BLANK
    #       create form. The page's own comment: "the only reliable signal is
    #       whether the Object gained an entry".
    #     * count SAME  -> `explainRejection()` -> `reportComplaints()`, and
    #       THE FILLED FORM STAYS PUT with the messages on it.
    #   `rememberSaved()` is called on NEITHER branch, so
    #   `sessionStorage['qc-oel-saved']` is never set and NO save-confirmation
    #   bar is ever rendered for a create. That is a product fact, not a
    #   reader gap -- see the note on 134978's step-1 assert.
    #
    # So the create path's success signal is the product's own winning
    # branch: THE FORM IS RE-RENDERED EMPTY. This reader samples exactly
    # that, keeps the three refusal renderers as the losing branch, and is
    # deliberately given its own name rather than folded into
    # `submit_expecting_refusal()` -- 134943 also submits from the create
    # form and asserts `outcome != "saved"` against a NATIVELY blocked
    # submit, and its reader must not be changed underneath it.

    def _create_form_was_reset(self, sentinel_label: str, sentinel_value: str) -> bool:
        """True once the create form no longer holds `sentinel_value` in
        `sentinel_label` -- i.e. `go()` fired and a blank form re-rendered.

        Every failure mode answers False and keeps the caller polling: the
        control is absent mid-navigation, and a read against a destroyed
        execution context raises. Neither is evidence of a save."""
        try:
            control = self._control(sentinel_label)
            if control.count() < 1:
                return False
            return control.first.input_value() != sentinel_value
        except Exception:  # noqa: BLE001 -- mid-navigation, not an outcome
            return False

    def submit_new_entry_outcome(
        self,
        sentinel_label: str,
        sentinel_value: str,
        timeout: float = CREATE_OUTCOME_TIMEOUT,
    ) -> str:
        """Clicks Submit for Publishing on the CREATE form and returns
        "refused" / "saved" / "none", reading the signals the create path
        actually emits (see the block above).

        `sentinel_label`/`sentinel_value` are a field the caller just filled
        and the value it filled it with; they are how "the form was
        re-rendered blank" is told from "the form is still sitting there".
        Refusal is checked FIRST on every poll, so a create that was refused
        can never be read as a save just because a control went unreadable.

        "none" stays a real, reportable result -- it is what a natively
        blocked submit looks like (stage 2a) -- never an error."""
        _log_submit(self._authoring, f"CREATE form Submit for Publishing ({sentinel_label} = {sentinel_value!r})")
        self._authoring.submit_for_publishing()
        outcome = {"value": "none", "by": "nothing"}

        def _settled() -> bool:
            if self.save_refusal_text():
                outcome["value"], outcome["by"] = "refused", "complaint"
                return True
            if self.success_message_text():
                outcome["value"], outcome["by"] = "saved", "message"
                return True
            if self._create_form_was_reset(sentinel_label, sentinel_value):
                outcome["value"], outcome["by"] = "saved", "landing"
                return True
            return False

        try:
            wait_until(_settled, timeout=timeout, poll=1.0)
        except Exception:  # noqa: BLE001 -- "neither appeared" is itself a result
            pass

        if outcome["by"] == "landing":
            # Hold here until the landing has actually SAID something, so the
            # caller's own `success_message_text()` / `create_message_report()`
            # reads happen after the last point at which the product could
            # still emit a message -- not in the gap between the navigation
            # and the entries-list fetch that renders the bars.
            try:
                wait_until(
                    lambda: bool(self.bar_texts()),
                    timeout=CREATE_LANDING_BAR_TIMEOUT,
                    poll=0.5,
                )
            except Exception:  # noqa: BLE001 -- no bar at all IS the observation
                pass
        return outcome["value"]

    # ---- Attachment picker ----------------------------------------------
    def _picker_closed(self, timeout: int) -> bool:
        try:
            self._page.locator(self.PICKER_IFRAME).wait_for(
                state="detached", timeout=timeout
            )
            return True
        except Exception:  # noqa: BLE001 -- caller decides what to do next
            return False

    def upload_expecting_rejection(
        self,
        field_label: str,
        file_path: str,
        rejection_reader=None,
        timeout_ms: int = PICKER_RESULT_TIMEOUT_MS,
    ) -> _PickerOutcome:
        """CONSOLIDATE -> `ObjectAuthoringPage.upload_file_expecting_
        rejection()`. Drives the Documents & Media picker exactly as
        `ObjectAuthoringPage.upload_file()` does up to `set_input_files()`,
        then reports what the picker said about the file -- a SPECIFIC
        rejection message, or nothing (which, for 134941/134942, is itself
        the finding).

        `rejection_reader` is the detector, and it is deliberately a
        parameter: 134942 passes `size_rejection_text`, so ONLY a
        size-feedback message counts as a rejection, while the default,
        `declared_rejection_text`, accepts any string the upload markup
        declares about itself. Neither can match this account's
        language-preference notice -- see the SIZE_REJECTION_RE block above
        for what the older, broader reading cost on 2026-09-15.

        It deliberately never clicks `Add`, so a rejected upload cannot
        half-attach anything, and it always closes the picker before
        returning: a still-open modal silently overlays the form's
        Save/Publish buttons and turns the next click into an unexplained
        30s timeout (already documented on
        `ObjectAuthoringPage.select_existing_file()`)."""
        reader = rejection_reader or self.declared_rejection_text
        hidden_textbox = self._page.get_by_role(
            "textbox", name=f"{field_label} Select File"
        )
        hidden_textbox.locator("xpath=..").get_by_role(
            "button", name="Select File"
        ).click()
        frame = self._page.frame_locator(self.PICKER_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path)

        captured = {"rejection": "", "accepted": False}

        def _resolved() -> bool:
            rejection = reader(frame)
            if rejection:
                captured["rejection"] = rejection
                return True
            if frame.get_by_text(self.PICKER_UPLOADED_COUNT_TEXT).count():
                captured["accepted"] = True
                return True
            return False

        try:
            wait_until(_resolved, timeout=timeout_ms / 1000.0, poll=1.0)
        except Exception:  # noqa: BLE001 -- "neither" is a reportable result
            pass

        # Read the picker BEFORE closing it -- afterwards the iframe is
        # detached and the failure report would carry an empty string.
        picker_text = self.picker_body_text()
        self.close_picker()
        return _PickerOutcome(
            rejection=captured["rejection"],
            accepted=captured["accepted"],
            picker_text=picker_text,
        )

    # ---- Rejection detectors --------------------------------------------
    def _scopes(self, frame=None):
        """Where a rejection can be rendered: inside the picker iframe, and
        on the form page itself (the upload fragment validates there too)."""
        return [scope for scope in (frame, self._page) if scope is not None]

    def _declared_feedback(self, frame=None):
        """Every `(attribute_name, value)` pair the live markup declares as
        upload feedback -- each attribute whose name ends in `-feedback`.

        This is the product describing its OWN rejection vocabulary, which
        is what makes matching against it both narrow and
        language-independent: whatever wording ships, English or Arabic, it
        is one of these strings -- and the account's language-preference
        notice is not one of them."""
        pairs = []
        for scope in self._scopes(frame):
            try:
                pairs.extend(
                    scope.locator("body").evaluate(self._COLLECT_FEEDBACK_JS)
                )
            except Exception:  # noqa: BLE001 -- a detached frame reads as none
                continue
        return [(str(name), str(value)) for name, value in pairs]

    def declared_size_feedback(self, frame=None) -> str:
        """The product's own SIZE-rejection string, identified by its
        ATTRIBUTE NAME (`data-file-size-feedback`), never by its wording --
        so an Arabic-rendered message is still classified correctly."""
        for name, value in self._declared_feedback(frame):
            if self.SIZE_FEEDBACK_ATTR_TOKEN in name:
                return value
        return ""

    def _visible_text(self, scope, needle) -> str:
        """The first VISIBLE element in `scope` whose text matches `needle`
        (a literal substring or a compiled regex), whitespace-normalised, or
        "".

        Visibility is required on purpose: a feedback string the fragment
        ships in a hidden node is not a rejection until the product actually
        renders it."""
        try:
            nodes = scope.get_by_text(needle)
            count = min(nodes.count(), 10)
        except Exception:  # noqa: BLE001 -- the iframe can detach mid-read
            return ""
        for index in range(count):
            node = nodes.nth(index)
            try:
                if node.is_visible():
                    return " ".join(node.inner_text().split())
            except Exception:  # noqa: BLE001 -- try the next candidate
                continue
        return ""

    def size_rejection_text(self, frame=None) -> str:
        """134942's detector: the SIZE rejection the product rendered, or "".

        Two narrow rules, in order -- the size-feedback wording family
        (SIZE_REJECTION_RE), then the exact string the markup declares for
        the size rule. Nothing else is read, so "there is text in the
        picker" can never again be mistaken for a size rejection."""
        for scope in self._scopes(frame):
            text = self._visible_text(scope, SIZE_REJECTION_RE)
            if text:
                return text
        declared = self.declared_size_feedback(frame)
        if declared:
            for scope in self._scopes(frame):
                text = self._visible_text(scope, declared)
                if text:
                    return text
        return ""

    def declared_rejection_text(self, frame=None) -> str:
        """The general detector (134941's): the first of the product's OWN
        declared feedback strings that is currently rendered, or ""."""
        for _name, value in self._declared_feedback(frame):
            for scope in self._scopes(frame):
                text = self._visible_text(scope, value)
                if text:
                    return text
        return ""

    def format_rejection_text(self, frame=None) -> str:
        """134941's detector (2026-10-13): the picker's FORMAT refusal, or "".
        Read live: a GIF makes the picker render "Please enter a file with a
        valid extension (.jpg,.png,.svg)." -- visible only after a refused
        file (absent before any upload and after a valid SVG), and NOT
        declared in a `*-feedback` attribute, so declared_rejection_text()
        never saw it. Falls back to that declared reader."""
        for scope in self._scopes(frame):
            text = self._visible_text(scope, EXTENSION_REJECTION_RE)
            if text:
                return text
        return self.declared_rejection_text(frame)

    def attachment_control_count(self, field_label: str) -> int:
        """How many upload controls named "<Field Label> Select File" the form
        renders -- 1 means the attachment field is available."""
        return self._page.get_by_role("textbox", name=f"{field_label} Select File").count()

    def picker_body_text(self) -> str:
        """Whole rendered text of the picker -- REPORT ONLY. It is attached
        to a failure message so a reader sees what the picker actually said;
        it is never a rejection signal, because reading it as one is exactly
        what captured the language-preference notice on 2026-09-15."""
        try:
            return (
                self._page.frame_locator(self.PICKER_IFRAME)
                .locator("body")
                .inner_text()
            )
        except Exception:  # noqa: BLE001
            return ""

    def close_picker(self) -> None:
        """Closes the picker if it is still open, and refuses to pretend it
        did when it did not."""
        if self._picker_closed(1500):
            return
        try:
            self._page.keyboard.press("Escape")
        except Exception:  # noqa: BLE001
            pass
        if self._picker_closed(4000):
            return
        for name in ("Cancel", "Close"):
            try:
                button = self._page.get_by_role("button", name=name)
                if button.count():
                    button.first.click(timeout=5000)
                    break
            except Exception:  # noqa: BLE001 -- try the next candidate label
                continue
        if not self._picker_closed(6000):
            raise AssertionError(
                "the Documents & Media picker would not close -- refusing to "
                "continue, because a still-open modal overlays the form's "
                "Save/Publish buttons and turns the next click into an "
                "unexplained 30s timeout"
            )
