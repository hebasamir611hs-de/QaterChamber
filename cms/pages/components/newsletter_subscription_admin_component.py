"""
cms/pages/components/newsletter_subscription_admin_component.py — NewsletterAdminPage.

Control_Panel Page Object for PBI 129566 (QC-GBL-005 — Newsletter
Subscription Management)'s CMS authoring surface: the "Newsletter" Object
Definition's Object Authoring form (`manage-newsletter`). Composes
ObjectAuthoringPage (cms/pages/components/object_authoring_page.py) for the
generic Draft/Submit-for-Publishing/Entries-list/Delete state machine, per
standards.md's "Object Authoring Is the Only Path for Content Operations"
rule — Content & Data is never used.

Lives under `pages/components/` (not a new `pages/newsletter/` folder) per
this project's own pre-established convention: standards.md's "Section
folder naming" table already assigns PBI QC-GBL-005 to the GLOBAL
cross-cutting `newsletter_subscription` file base, and skeleton files for
exactly this class already existed at this path before this batch (confirmed
by reading the tree — `web/pages/components/newsletter_subscription_component.py`
and this file's own prior placeholder content), which is what this batch
fills in rather than a parallel `pages/newsletter/` tree the task's own
draft description suggested but explicitly asked to be verified first.

SLUG CONFIRMED LIVE 2026-09-19/20 (scripted Playwright probe, TEST_USER
session, qcdev) — CLI-first `tools/extract_locators.py` alone was
insufficient here (see below) so this investigation fell back to short,
disclosed, throwaway Playwright scripts (not the interactive MCP) driving
the SAME `.auth/state.json` storageState the CLI extractor itself uses:
  - Object Authoring's own index (`/web/qatar-chamber/object-authoring`)
    lists 246 objects, filterable by a "Type to filter" box. Filtering for
    "newsletter" surfaces exactly 3: "Newsletter" (the compose-a-newsletter-
    issue object these 16 Control_Panel cases exercise), "Newsletter
    Subscriber" (marked `(view only)` — no create/edit form; the store the
    PUBLIC footer widget's Subscribe button writes into, see
    web/pages/components/newsletter_subscription_component.py), and
    "Newsletter Unsubscribe" (a site PAGE, not an object).
  - Clicking "Newsletter" resolves to `/web/qatar-chamber/manage-newsletter`
    -> `NEWSLETTER_SLUG = "newsletter"` below. Direct `page.goto()` to this
    URL DOES work (confirmed both via a fresh script and via every test in
    this batch), but only once the page is given a real settle window after
    `domcontentloaded` (~6s in every successful probe this session) — a
    `tools/extract_locators.py` run with its own default 5s post-load
    settle landed on the SITE PAGES admin panel instead (same "wrong
    surface after too-short a settle" class of finding already documented
    project-wide, e.g. `open_new_entry_form()`'s own 35000ms widening note
    in object_authoring_page.py) — this is why the live field investigation
    below used a scripted Playwright probe with an explicit longer wait
    instead of trusting the CLI extractor's single default-timeout pass.

FIELD SET CONFIRMED LIVE (same session, via `page.accessibility.snapshot()`
and direct DOM attribute reads — never guessed): Newsletter ID, Title,
Title — العربية, Subject Line, Subject Line — العربية, Short Description
(EN/AR), Content (EN/AR, CKEditor), Banner Image, Attachments, Language,
Status (originally logged here as "read-only on the create/edit form —
auto-set by Save as Draft/Submit for Publishing, not user-editable despite
carrying a DOM `required` attribute" — CORRECTED 2026-09-21, this was
wrong; see module docstring's dated CORRECTION section and
`select_status()` below: it is a real, interactive, required combobox),
Publish Date, Expiry Date, Include
News/Events/Circulars/Publications checkboxes, Schedule Send + its own date,
Sent Date, Sent Count. Only the 4 fields these 16 cases cover (Title EN/AR,
Subject Line EN/AR) get named methods below — the rest are out of this
batch's scope and intentionally not wrapped.

ACCESSIBLE NAMES — the Arabic-locale sibling of each bilingual field
carries a trailing " *" in its OWN accessible name (confirmed live via
`page.accessibility.snapshot()`; the English sibling's accessible name
carries NO such suffix despite the DOM `required` attribute being present
on both) — `TITLE_AR_LABEL`/`SUBJECT_AR_LABEL` below include that literal
suffix because `get_by_role(..., exact=True)` needs the exact string to
resolve. This is a structural/attribute-derived accessible-name fact, not
Arabic body text being used as a locator — standing rule 1 (no
Arabic-text-anchored locators) is about visible Arabic COPY, not an ARIA
name that happens to end in " *"; if this trailing marker ever moves,
`ObjectAuthoringPage.fill_text()`'s underlying `get_by_role` call will
simply fail loudly (a maintenance point, not a hidden Arabic-text
dependency).

REAL FIELD-VALIDATION BEHAVIOR — CONFIRMED LIVE 2026-09-19/20 via repeated
disposable `QCTEST-`-prefixed Save-as-Draft attempts against
`manage-newsletter` (each cleaned up via `ObjectAuthoringPage.
delete_entry_by_code()` in the same investigation session; qcdev left at its
pre-investigation baseline of 2 real entries afterward — verified by a final
row-count check). This form's client-side validation is a CUSTOM,
PARTIALLY-COSMETIC layer — unlike the public footer widget's 100%-native
HTML5 validation (see NewsletterSubscriptionComponent's own module
docstring for that contrast) — and does NOT uniformly gate the underlying
Save-as-Draft AJAX call the way its own inline messages suggest it should:

  | Field         | Empty                          | Whitespace-only                         | Over max length |
  |---------------|---------------------------------|-------------------------------------------|------------------|
  | Title (EN)    | ACCEPTED (saved with `""`)     | REJECTED (real inline error "Title cannot be only spaces.", confirmed no entry created — re-verified twice via the automated suite after an earlier one-off manual probe wrongly suggested a silent-accept; corrected here rather than left standing) | REJECTED — real server cap is **280** chars, not the 250 the ADO case states (error: "Object entry value exceeds the maximum length of 280 characters for object field 'title'"); no native `maxlength` attribute exists on this field, so 251-280 chars is REACHABLE and ACCEPTED, only >280 is rejected |
  | Title (AR)    | ACCEPTED (saved with `""`)     | REJECTED (real inline error "Title (العربية) cannot be only spaces.", confirmed no entry created) | NOT ENFORCED AT ALL — confirmed live up to 500 chars accepted with no rejection and no native `maxlength`; a real, disclosed asymmetry vs. its own EN sibling |
  | Subject Line (EN) | ACCEPTED (saved with `""`) | REJECTED (real inline error "Subject Line cannot be only spaces.", confirmed no entry created) | Native `maxlength="200"` on the `<input>` — NOT the 250 the ADO case states; 201+ chars is physically unreachable via `.fill()`/typing (value is silently capped at 200 characters), so there is no save-time rejection to test — mirrors this project's already-established "reject-over-limit is unreachable via native maxlength; assert the capped length instead" pattern (see PILLAR/other objects' own precedent referenced in automation-standards.md) |
  | Subject Line (AR) | ACCEPTED (saved with `""`) | REJECTED (real inline error "Subject Line (العربية) cannot be only spaces.", confirmed no entry created) | Native `maxlength="200"`, same unreachable-over-limit pattern as the EN sibling |

  Every "ACCEPTED" (empty-field) row above still shows a cosmetic inline
  hint ("Required") at the moment of the click — but the underlying AJAX
  save fires anyway and a new Draft entry appears in the entries table with
  that field's value genuinely empty. This is the opposite of "rejected"
  and is asserted as the confirmed, live, disclosed PRODUCT DEFECT it is in
  each affected test's own docstring below — per automation-standards.md's
  Result Integrity section, the assertion checks the ADO case's real
  intended outcome (the field's emptiness is rejected) and is EXPECTED TO
  FAIL live, not silently rewritten to match the buggy behavior. Every
  "REJECTED" (whitespace-only) row genuinely blocks the save with a real,
  non-cosmetic inline error and no entry created — these assertions match
  the case and are expected to PASS. This automation agent has no Azure
  write access this session — the empty-field findings are reported to the
  user/QA Manager for bug filing, not filed here.

  The Title (EN) 280-char cap is asserted at its REAL threshold (281 chars,
  not 251) — the case's core INTENT ("excessively long input is rejected")
  is genuinely true here, just at a different real number than the case's
  own 250 figure; this is a disclosed case-data correction, not a defect,
  and is asserted as a PASS.

CORRECTION — 2026-09-20 (QA Manager directive: Draft-vs-Publish gate).
SUPERSEDES the "REAL FIELD-VALIDATION BEHAVIOR" table's own "ACCEPTED
(empty-field)... LIVE PRODUCT DEFECT" verdicts above for Title (EN/AR) and
Subject Line (EN/AR) — kept in place above, not deleted, per this project's
additive/dated-history convention; read this section as the current,
governing finding for those 4 fields.

The QA Manager confirmed, as real domain knowledge about this project's
Object Authoring workflow, that Save as Draft is INTENTIONALLY permissive
(a Draft may hold incomplete/empty required fields — that is the point of a
Draft) and that the REAL validation gate a mandatory-field case must be
tested against is Submit for Publishing, not Save as Draft. Testing the 4
"empty required field is rejected" cases (tc_134551/134555/134559/134563)
against Save as Draft, as the prior pass did, was testing the WRONG action
— the resulting "silently accepted, PRODUCT DEFECT" verdicts above do NOT
apply; Draft-time leniency is by design, not a bug.

Re-investigated LIVE 2026-09-20 (qcdev, disposable `QCTEST-INVESTIGATE-*`/
`QCTEST-DIAG*`/`QCTEST-CONTROL*`/`QCTEST-ISO-*`/`QCTEST-DRAFTFIRST*`
entries, ~15 independent scripted Playwright probes, every one cleaned up —
qcdev confirmed back at its 2-real-entry baseline afterward) with Submit
for Publishing instead, filling every OTHER genuinely DOM-`required` field
validly (Title EN/AR, Subject EN/AR except the one field under test,
Content (EN) via CONTENT_EN_EDITOR_IFRAME, Language via select_language())
so the field under test's own gate could be isolated from an incomplete
form's own generic rejection. Finding, reproduced identically across every
probe (empty Title EN, empty Title AR, empty Subject EN, empty Subject AR,
a fully-valid control run, and a Draft-then-reopen-for-edit run):

  Submit for Publishing is UNCONDITIONALLY BLOCKED on this object,
  regardless of Title/Subject Line's own state — a SEPARATE, newly
  confirmed, live PRODUCT DEFECT, more severe than (and orthogonal to) the
  4 fields this batch was originally scoped to: the Content (EN) field's
  own required-check fires "Required" and blocks the workflow action even
  when Content (EN) is filled with real, valid, non-empty text. Verified
  NOT a fill-timing/race artifact: the underlying hidden
  `...-ckeditor-required` input's own `.value` was read directly (by id,
  bypassing the visual editor) both immediately after typing and again
  several seconds after the failed Submit-for-Publishing click, and held
  the correct, non-empty `<p>...</p>` content throughout in every probe.
  Confirmed via network capture that Submit for Publishing's own AJAX call
  never fires at all when this happens (zero POST/PUT/PATCH requests) —
  the block is entirely client-side, before any request reaches the
  server. Reproduced identically whether starting from a fresh create form
  OR reopening an already-Draft-saved entry (with Content already
  persisted and non-empty) for edit — ruling out "the create form's
  editor never mounted its real state" as the cause.

  PRACTICAL CONSEQUENCE for this batch's 5 corrected tests (tc_134551,
  tc_134555, tc_134559, tc_134563, tc_134557): because Submit for
  Publishing is blocked for EVERY attempt on this object regardless of the
  field under test, the OBSERED behavior for all 5 ("no entry is ever
  published when <field> is empty/over-limit") technically MATCHES each
  case's own literal expected result ("is rejected") and is asserted,
  and passes, as such below — but this pass must NOT be read as confirming
  that <field>'s OWN publish-time validation is what caused the rejection;
  the SAME block is observed even when every field this batch cares about,
  including the one nominally "under test", is filled validly. Each field's
  own dedicated publish-time enforcement (including whether Title (AR)
  gets a real length cap at Submit-for-Publishing time that Draft does
  not) remains UNVERIFIED, not confirmed-correct, until the separate
  Content-required defect above is fixed and this batch can be re-run to
  actually observe a completed Submit-for-Publishing attempt. This
  caveat is repeated in each corrected test's own docstring below —
  Result Integrity requires disclosing the confound, not just the pass.

CORRECTION — 2026-09-21 (QA Manager directive: the "publish always blocked"
finding above was itself an AUTOMATION BUG, not a product defect).
SUPERSEDES the "CORRECTION — 2026-09-20" section's own "Submit for
Publishing is UNCONDITIONALLY BLOCKED... Content (EN)'s own required-check
fires even when Content (EN) is filled" verdict — kept above, not deleted,
per this project's additive/dated-history convention; that verdict does
NOT apply and must not be reported as a product defect.

The QA Manager manually created a real "test" newsletter live (Title/
Content/etc. genuinely filled through the normal UI) and it PUBLISHED
SUCCESSFULLY (STATUS=PUBLISHED, working Edit/Preview/Unpublish/Delete
actions) — directly disproving the "always blocked" finding. Re-
investigated live 2026-09-21 (qcdev, fresh `python tools/save_auth.py`
session, disposable `QCTEST-INVESTIGATE*`/`QCTEST-134551..134563` entries,
every one cleaned up — qcdev confirmed back at its real 3-entry baseline
afterward, `Qatar Chamber Monthly — Sample Issue` / `New letter` (Draft) /
`test`) to find the TWO real, distinct root causes:

  1. `set_content_en()` itself was NEVER broken. Its fill mechanism (real
     `body.click()` + `Control+A` + `page.keyboard.type()` into the actual
     CKEditor iframe body, via `BasePage.fill_iframe_editor()`) is confirmed
     live to be exactly what a real human/browser interaction does — proven
     by reading BOTH the hidden `...-ckeditor-required` input's `.value`
     AND (new this pass) `window.CKEDITOR.instances[...].getData()` itself
     (the editor's own real internal document model, not just a DOM
     attribute) directly after typing: both held the correct, non-empty
     `<p>...</p>` content, both reported native `validity.valid: true`. The
     "classic form-fill-bypasses-framework-state" hypothesis this
     correction was scoped to investigate is DISPROVEN for this method —
     there was no CKEditor-state bug to fix, and `set_content_en()` below
     is UNCHANGED by this correction.

  2. The REAL blocker was TWO required fields this batch's Submit-for-
     Publishing flow never filled, discovered by reading every `[required]`
     form element's live `validity.valid`/`validationMessage` immediately
     after a blocked click (a diagnostic the 2026-09-20 pass never ran —
     it stopped at the hidden Content input alone):
       - **Newsletter ID** — a plain required text field, confirmed live on
         the QA Manager's own real "test" entry (`Newsletter ID = "test10"`)
         and never once filled by any test in this batch or the prior
         correction pass. `set_newsletter_id()` is added below.
       - **Status** — CONTRARY to this same module's own prior "read-only
         on the create/edit form... not user-editable despite carrying a
         DOM `required` attribute" claim (see the FIELD SET note above,
         now corrected): confirmed live the create/edit form renders a
         SECOND, genuinely interactive "Open Options Menu" combobox (the
         same `select_language()` pattern, `.nth(1)`) offering Draft /
         Approved / Published / Archived, and its own backing required
         input reports `validationMessage: "Please fill out this field."`
         (native constraint validation) until a real option is explicitly
         clicked — the "Published" TEXT visible in the combobox before any
         click is a display default, not a bound value. `select_status()`
         is added below; every Submit-for-Publishing test must now call
         `select_status("Published")` alongside `select_language("EN")`.
     With BOTH filled (plus every already-known required field), a real,
     fully-valid, disposable `QCTEST-`-prefixed entry published
     successfully live (STATUS=PUBLISHED, real row in the entries table) —
     confirming Submit for Publishing genuinely WORKS on this object; it
     was never unconditionally blocked.

  3. A SEPARATE contributing bug in the 2026-09-20 pass's own DETECTION
     logic (not a fix to product code, a correction to how "blocked" was
     read): `has_inline_message("Required")` / raw body-text-contains-
     "Required" was used as the "blocked" signal, but "Required" is a
     STATIC label suffix rendered next to the Content field's own name on
     EVERY page load of this form — confirmed live present in the DOM
     before any interaction at all, before any click, on a completely fresh
     `open_new_entry_form()` call. That prior pass's every "confirmed
     blocked" read was matching this permanent label, not a genuine
     validation-error banner. The REAL, live-confirmed blocked-state signal
     is the page's own literal banner text: "Please complete the required
     fields before proceeding with the workflow action for this new
     record. Nothing has been submitted." — `submit_publish_blocked()`
     below reads THIS text, not a bare "Required" substring.

  PRACTICAL CONSEQUENCE for this batch's 5 corrected tests
  (tc_134551/134555/134559/134563/134557): re-run live 2026-09-21 with
  BOTH missing fields now filled (Newsletter ID + Status=Published) for
  every field NOT under test, isolating each field's own real publish-time
  signal for the first time:
    - Title (EN) empty (tc_134551): genuinely BLOCKED — the real banner
      shown, no row created. Matches the case's expected outcome.
    - Title (AR) empty (tc_134555): genuinely BLOCKED — same, real banner,
      no row created. Matches the case's expected outcome.
    - Subject Line (EN) empty (tc_134559): genuinely BLOCKED — same. Matches
      the case's expected outcome.
    - Subject Line (AR) empty (tc_134563): genuinely BLOCKED — same. Matches
      the case's expected outcome.
    - Title (AR) at 500 chars, far past the case's stated 250 (tc_134557):
      NOT blocked — PUBLISHED SUCCESSFULLY (confirmed live: a real row with
      STATUS=PUBLISHED appeared, no length-error banner, no rejection of
      any kind). This is a genuine, confirmed-live PRODUCT DEFECT — Title
      (AR) has NO enforced length cap AT PUBLISH TIME either (mirrors, and
      now confirms at Publish time rather than only Draft time, this
      module's own original "REAL FIELD-VALIDATION BEHAVIOR" table finding
      for Title (AR) above). Per Result Integrity, this is asserted against
      the case's real intended outcome (over-length input is rejected) and
      is EXPECTED TO FAIL live, not silently rewritten to match the buggy
      accept-everything behavior.
  Every field's own dedicated publish-time enforcement is now genuinely
  VERIFIED (not confounded) for the first time this batch.

ROW LOOKUP — this object's own Entry-column list DOES render the real Title
(EN) text when non-empty (confirmed live, e.g. a saved "QCTEST NL Title EN
<uuid>" entry renders exactly that string in its own row) — UNLIKE
manage-strategic-pillar-card's documented externalReferenceCode-only
exception (see ObjectAuthoringPage's own module docstring). When a test's
own Title (EN) is intentionally left empty/whitespace (the exact fields
under test in several cases below), the row's Entry column instead renders
a raw UUID with no title text to match against — those tests therefore
resolve/tear down their own row via `find_entry_code_by_field()` against
whichever OTHER field they did fill with a real, unique `QCTEST-` marker
(Subject Line (EN), which every Title-focused test still fills with a
readable, non-empty value) rather than a title-based lookup, per
ObjectAuthoringPage's own "never delete by position" rule.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from core.utils.waits import WaitTimeoutError, wait_until

NEWSLETTER_SLUG = "newsletter"

TITLE_EN_LABEL = "Title"
TITLE_AR_LABEL = "Title — العربية *"
SUBJECT_EN_LABEL = "Subject Line"
SUBJECT_AR_LABEL = "Subject Line — العربية *"

# Real, live-confirmed limits (see module docstring's table) — deliberately
# NOT the 250 every ADO case in this batch states.
TITLE_EN_REAL_MAX_LENGTH = 280
SUBJECT_REAL_MAX_LENGTH = 200  # native maxlength, both EN and AR

# ---- Added 2026-09-20 (Draft-vs-Publish correction batch, see module
# docstring's dated section) — supporting fields needed to correctly drive
# Submit for Publishing (not part of the original 4-field/Draft-only batch,
# but genuinely DOM-`required` for this object's publish-time validation —
# confirmed live via `document.querySelectorAll('[required]')`, see the
# docstring's "REQUIRED-FIELD SET" note). Only Content (EN) carries a real
# `required` attribute of this pair — Content (AR) does not — so only the
# EN editor is filled by these correction-batch tests, mirroring the DOM
# truth rather than over-filling for appearance.
CONTENT_EN_EDITOR_IFRAME = 'iframe[title="editor"] >> nth=0'
CONTENT_AR_EDITOR_IFRAME = 'iframe[title="editor"] >> nth=1'

# ---- Added 2026-09-21 (CORRECTION — automation-bug fix batch, see module
# docstring's dated section) — the TWO real, previously-missed required
# fields Submit for Publishing genuinely gates on for this object.
NEWSLETTER_ID_LABEL = "Newsletter ID"

# The real, literal client-side "blocked" banner text — confirmed live
# 2026-09-21, replaces the prior pass's false-positive "Required"
# substring match (see module docstring's dated correction).
SUBMIT_BLOCKED_BANNER_TEXT = "Please complete the required fields"


class NewsletterAdminPage(ObjectAuthoringPage):
    """`manage-newsletter`'s Title/Subject Line field actions — the 4
    fields this batch's 16 Control_Panel cases cover. Every other
    Draft/Submit-for-Publishing/entries-list/delete method is inherited
    as-is from ObjectAuthoringPage (do not re-declare here)."""

    def __init__(self, page):
        super().__init__(page, NEWSLETTER_SLUG)

    # ---- Title (EN) ---------------------------------------------------
    def set_title_en(self, value: str) -> "NewsletterAdminPage":
        self.fill_text(TITLE_EN_LABEL, value)
        return self

    def title_en_value(self) -> str:
        return self.field_value(TITLE_EN_LABEL)

    # ---- Title (AR) -----------------------------------------------------
    def set_title_ar(self, value: str) -> "NewsletterAdminPage":
        self.fill_text(TITLE_AR_LABEL, value)
        return self

    def title_ar_value(self) -> str:
        return self.field_value(TITLE_AR_LABEL)

    # ---- Subject Line (EN) -----------------------------------------------
    def set_subject_en(self, value: str) -> "NewsletterAdminPage":
        self.fill_text(SUBJECT_EN_LABEL, value)
        return self

    def subject_en_value(self) -> str:
        return self.field_value(SUBJECT_EN_LABEL)

    # ---- Subject Line (AR) -----------------------------------------------
    def set_subject_ar(self, value: str) -> "NewsletterAdminPage":
        self.fill_text(SUBJECT_AR_LABEL, value)
        return self

    def subject_ar_value(self) -> str:
        return self.field_value(SUBJECT_AR_LABEL)

    # ---- Content (EN) — Added 2026-09-20, see class-level constant note --
    def set_content_en(self, value: str) -> "NewsletterAdminPage":
        """Fills the real, DOM-`required` Content (EN) CKEditor field via
        BasePage.fill_iframe_editor() (click + Ctrl+A + real keyboard type
        — never page.evaluate(), see that method's own docstring).

        LIVE INCIDENT (2026-09-20, this correction batch): the underlying
        hidden `...-ckeditor-required` input's OWN value was confirmed,
        repeatedly, to correctly and durably hold whatever this method
        writes — yet Submit for Publishing's own client-side validation
        appeared to still flag this exact field "Required" and block the
        action regardless, reported at the time as a real, separate,
        confirmed-live PRODUCT DEFECT.

        CORRECTION — 2026-09-21 (QA Manager directive, see module
        docstring's dated CORRECTION section for the full re-investigation):
        DISPROVEN. The QA Manager manually published a real newsletter live
        through the normal UI with no error at all. Re-investigated live:
        this method's own fill mechanism was NEVER the problem — confirmed,
        this time, via `window.CKEDITOR.instances[...].getData()` itself
        (the editor's real internal document model, not just a DOM
        attribute) immediately after typing, which correctly held this
        method's exact value. The 2026-09-20 pass's own "still flags
        Required" read was a false positive: it was matching a STATIC
        "Required" label that renders next to the Content field's name on
        EVERY page load of this form, before any interaction — not a
        validation-error banner. The REAL blocker was two ENTIRELY
        DIFFERENT required fields this batch never filled (Newsletter ID,
        Status — see `set_newsletter_id()`/`select_status()` below), which
        have nothing to do with this method or the Content field at all.
        This method is UNCHANGED by that correction — it was already
        correct. Newsletter mounts TWO CKEditor iframes (Content EN/AR) —
        unlike ObjectAuthoringPage.fill_rich_text()'s single-field
        DESCRIPTION_EDITOR_IFRAME convention (nth=0 only), so this calls
        BasePage.fill_iframe_editor() directly against the EN-specific
        iframe locator rather than reusing that inherited single-field
        helper."""
        self.fill_iframe_editor(CONTENT_EN_EDITOR_IFRAME, value)
        return self

    def content_en_value(self) -> str:
        return self.iframe_editor_text(CONTENT_EN_EDITOR_IFRAME)

    # ---- Newsletter ID — Added 2026-09-21, see module docstring's dated
    # CORRECTION section (the real, previously-missed Submit-for-Publishing
    # required field) ------------------------------------------------------
    def set_newsletter_id(self, value: str) -> "NewsletterAdminPage":
        self.fill_text(NEWSLETTER_ID_LABEL, value)
        return self

    def newsletter_id_value(self) -> str:
        return self.field_value(NEWSLETTER_ID_LABEL)

    # ---- Language — Added 2026-09-20, see class-level constant note ------
    # FIXED 2026-10-13 (tc_134551: 5 s option timeout at the old
    # `nth(0)` click). Read live 2026-10-13 on manage-newsletter: Language and
    # Status are `input[role=combobox][id$=-select-from-list-input]` named by
    # their own label, each with `aria-controls=<listbox id>`, a toggle
    # `button[aria-controls=<listbox id>]`, and `<li role=option
    # data-option-label=...>` options (Language: EN / AR / Both; Status:
    # Draft / Approved / Published / Archived). The toggle TOGGLES and the
    # form hydrates after Save as Draft is visible -- an early click opened
    # nothing -- so the open is retried until the wanted option is visible,
    # and the pick is verified by read-back. Never positional.
    FORM_COMBOBOX = '[id$="-select-from-list-input"]'
    COMBO_OPEN_ATTEMPTS = 4
    COMBO_OPTION_MS = 5000

    def _pick_form_option(self, field_label: str, option_label: str) -> None:
        combo = self.page.get_by_role("combobox", name=self.label_pattern(field_label)).and_(
            self.page.locator(self.FORM_COMBOBOX)
        ).first
        combo.wait_for(state="visible", timeout=20000)
        listbox = combo.get_attribute("aria-controls")
        toggle = self.page.locator(f'button[aria-controls="{listbox}"]').first
        option = self.page.locator(
            f'[id="{listbox}"] [role="option"][data-option-label="{option_label}"]'
        )
        for _ in range(self.COMBO_OPEN_ATTEMPTS):
            if combo.get_attribute("aria-expanded") != "true":
                toggle.click()
            try:
                option.wait_for(state="visible", timeout=self.COMBO_OPTION_MS)
                break
            except Exception:  # noqa: BLE001 -- not hydrated yet: re-open
                continue
        option.click()
        got = combo.input_value()
        if got != option_label:
            raise LookupError(f"{field_label!r}: picked {option_label!r} but the field reads {got!r}")

    def select_language(self, option_label: str) -> "NewsletterAdminPage":
        """Language combobox (EN / AR / Both) -- see `_pick_form_option()`."""
        self._pick_form_option("Language", option_label)
        return self

    # ---- Status — Added 2026-09-21, see module docstring's dated
    # CORRECTION section -----------------------------------------------------
    def select_status(self, option_label: str) -> "NewsletterAdminPage":
        """The object's own required "Status" picklist (Draft / Approved /
        Published / Archived) -- an object field, NOT the workflow state the
        row badge shows. See `_pick_form_option()`."""
        self._pick_form_option("Status", option_label)
        return self

    # ---- Submit-for-Publishing blocked-state read — Added 2026-09-21, see
    # module docstring's dated CORRECTION section ----------------------------
    def submit_publish_blocked(self) -> bool:
        """The REAL, live-confirmed client-side "blocked" signal
        (`SUBMIT_BLOCKED_BANNER_TEXT`) — replaces the prior pass's
        `has_inline_message("Required")`-based check, which was a
        false-positive matching a STATIC "Required" label suffix that
        renders next to the Content field's own name on every page load of
        this form, before any interaction at all (confirmed live: present
        in the DOM on a totally fresh `open_new_entry_form()` call, no
        click, no submit). This reads the page's own literal banner text
        instead ("Please complete the required fields before proceeding
        with the workflow action for this new record. Nothing has been
        submitted.")."""
        return SUBMIT_BLOCKED_BANNER_TEXT in self.page.locator("body").inner_text()

    # ---- Validation-message reads (see module docstring's behavior table) --
    def has_inline_message(self, text_fragment: str) -> bool:
        """True if `text_fragment` appears anywhere on the current form —
        used to read this surface's cosmetic inline validation hints
        ("Required", "<Field> cannot be only spaces.", the real 280-char
        server error) without anchoring to Arabic body copy (every fragment
        this batch's tests pass is English UI chrome text, per standing
        rule 1 — a field's own OWN name, e.g. "Title (العربية)", appearing
        inside an English sentence is UI chrome, not a case asserting on
        Arabic content)."""
        return self.page.get_by_text(text_fragment, exact=False).count() > 0

    def wait_for_inline_message(self, text_fragment: str, timeout: float = 8.0) -> bool:
        """Polling counterpart to has_inline_message() — HEALED (live
        incident this batch, tc_134553): the real over-280-char server
        error is a genuine round trip (a validate/save request that must
        complete before the message renders), and an immediate,
        single-shot has_inline_message() call right after save_as_draft()
        intermittently missed it live (observed: `False` on first read,
        the message DID exist after a short poll) — the same class of
        async-settle race already documented project-wide for this
        surface's entries table (see the module docstring's 'Loading
        entries...' note below)."""
        try:
            wait_until(lambda: self.has_inline_message(text_fragment), timeout=timeout, poll=0.5)
            return True
        except WaitTimeoutError:
            return False

    # ---- Entries-table polling (see module docstring's async-settle note) --
    def wait_for_row_status(self, title: str, expected_status: str, timeout: float = 12.0) -> str:
        """Polls row_status_text(title) until it equals `expected_status`
        or `timeout` elapses, returning whatever the LAST read was
        (possibly still not matching) — never raises, so a caller asserts
        on the returned value with its own message. HEALED (live incident
        this batch): this surface's entries table re-fetches
        ASYNCHRONOUSLY after Save as Draft — confirmed live via screenshot,
        a "Loading entries..." placeholder briefly renders — so a single,
        immediate read right after save_as_draft()'s own settle grace can
        race that fetch and read an empty/stale table, especially as this
        shared qcdev environment accumulates more rows over a run. Reusable
        in BOTH directions: a test expecting "Draft" to appear asserts
        `== "Draft"` on the result; a test expecting NO entry to have been
        created (the real, disclosed rejection-cases) still calls this
        (waiting long enough for a real, slower-landing DEFECT-created row
        to surface rather than risk a false pass from checking too early)
        and asserts `!= "Draft"`."""
        result = {"value": ""}

        def _check() -> bool:
            result["value"] = self.row_status_text(title)
            return result["value"] == expected_status

        try:
            wait_until(_check, timeout=timeout, poll=1.0)
        except WaitTimeoutError:
            pass
        return result["value"]

    def any_row_contains(self, marker: str) -> bool:
        """Added 2026-09-20 (Draft-vs-Publish correction batch) — a simple,
        non-positional "did ANY row get created for this disposable
        marker" check, used by the corrected Submit for Publishing tests
        below whose expected outcome is that NO row is ever created (a
        genuinely rejected/blocked publish attempt) and which therefore
        have no single known title/subject value to look up by (the field
        actually under test is the one left empty). Scoped by substring
        match against the row's own rendered text — safe here because
        every marker this batch uses is a unique `QCTEST-<adoID>-<uuid8>`
        string, never a bare/ambiguous value."""
        self.open_entries_list()
        return self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{marker}")').count() > 0

    def find_entry_by_subject_en(self, subject_en_value: str) -> str:
        """Newsletter-scoped, resilient counterpart to
        ObjectAuthoringPage.find_entry_code_by_field() — HEALED (live
        incident this batch, tc_134551 and siblings): the shared method
        calls `open_entry_by_code(code)` OUTSIDE any try/except inside its
        per-row loop, so if ANY single row's open+settle raises, the whole
        scan aborts immediately rather than skipping to the next row.
        Confirmed live that this object's own PRE-EXISTING "Qatar Chamber
        Monthly — Sample Issue" row (Status=Approved/Published, the very
        first row iterated) intermittently outlives the shared method's
        per-row settle wait under real load — the scan then aborts before
        it ever reaches a LATER row this test actually created, silently
        reporting "not found" (`""`) even though the entry genuinely
        exists (confirmed by an independent direct row-count check: the
        table gained exactly one row after Save as Draft). This is a real
        false-negative in the shared helper on an object whose pre-existing
        rows include an Approved entry — not something this batch works
        around by abandoning the safe, non-positional "verify by real field
        value" principle (standards.md's "Destructive Operations — Never
        Delete by Position"). This method keeps that same principle but
        isolates each row's own open+read behind ITS OWN try/except, so one
        slow/unusual pre-existing row never masks a later genuine match."""
        self.open_entries_list()
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        codes = [rows.nth(i).locator("td").nth(0).inner_text().strip() for i in range(rows.count())]
        for code in codes:
            try:
                self.open_entry_by_code(code)
                value = self.page.get_by_role("textbox", name=SUBJECT_EN_LABEL, exact=True).input_value()
            except Exception:  # noqa: BLE001 — one bad row must never abort the rest of the scan
                continue
            if value == subject_en_value:
                return code
        return ""

    def wait_for_entry_created_by_subject_en(self, subject_en_value: str, timeout: float = 15.0) -> str:
        """wait_for_row_status()'s counterpart for the handful of tests
        whose own Title (EN) is empty/whitespace (the field under test) —
        find_entry_by_subject_en() is the non-positional lookup available
        then (see class docstring), so this polls IT, same async-settle
        rationale, with a longer per-poll interval since each attempt
        re-opens and scans every existing row."""
        result = {"code": ""}

        def _check() -> bool:
            result["code"] = self.find_entry_by_subject_en(subject_en_value)
            return result["code"] != ""

        try:
            wait_until(_check, timeout=timeout, poll=2.0)
        except WaitTimeoutError:
            pass
        return result["code"]


# ---- Added 2026-10-12 (PBI 129566 batch 2: content, workflow, RBAC). ------
# Scripted OFFLINE -- no qcdev browser was available. Every unread
# identifier carries a VERIFY-LIVE note.
# VERIFY-LIVE: the view-only "Newsletter Subscriber" object's slug.
NEWSLETTER_SUBSCRIBER_SLUG = "newsletter-subscriber"
# "Schedule Send" resolves as a checkbox by its name (read live 2026-10-13).
PUBLISH_DATE_LABEL = "Publish Date"
SCHEDULE_SEND_LABEL = "Schedule Send"
# The project's email-delivery inbox (memory: test_email_inbox).
TEST_INBOX = "heba.samir611.hs@gmail.com"
ACCESS_DENIED_EN = "Access Denied. You do not have permission to perform this action."


class NewsletterWorkflowPage(NewsletterAdminPage):
    """Content (EN/AR) as HTML, row-action reads, and the subscriber-list
    surface -- what the 2026-10-12 workflow/RBAC cases need on top of the
    field actions above."""

    # Content EN/AR: two CKEditor 4 instances, located BY FIELD NAME --
    # read live 2026-10-13 on manage-newsletter: the EN instance is
    # `<fragment-id>-ObjectField_content`, the Arabic twin `qc-ar-content`.
    # FIXED 2026-10-13 (run allure-129566-20261012-2145): never positional.
    # FIXED AGAIN 2026-10-13 (tc_134572/134575 read back '', tc_134601
    # "Cannot read properties of undefined (reading 'getSelection')"): after
    # the row's Edit link (a SPA navigation) CKEDITOR.instances still holds
    # the PREVIOUS form's EN editor -- read live: two `...ObjectField_content`
    # instances, the first `isConnected=false` with empty data, the second
    # live with the stored HTML. Only instances whose element is still in the
    # document are candidates; more than one live match is an error.
    CONTENT_FIELD_NAMES = ("content",)
    _CONTENT_TOKENS = {
        "en": tuple(f"ObjectField_{n}" for n in CONTENT_FIELD_NAMES),
        "ar": tuple(f"qc-ar-{n}" for n in CONTENT_FIELD_NAMES),
    }
    # Label fallback, anchored (EN "Content" + its static "Required" suffix;
    # AR twin "Content — العربية").
    _CONTENT_LABEL_RE = {
        "en": r"^Content(\s*\(EN\))?\s*\*?(\s*Required)?$",
        "ar": r"^Content\s*(—\s*العربية|\(AR\))\s*\*?$",
    }
    CONTENT_EDITOR_TIMEOUT_MS = 20000

    # Resolves ONE locale's instance name, or null. Order of evidence:
    # 1. instance name ends with a token; 2. an ancestor's id carries the
    # token as a whole word; 3. the enclosing form group's label matches.
    _RESOLVE_CONTENT_JS = """
    ({tokens, labelRe}) => {
      const C = window.CKEDITOR;
      if (!C || !C.instances) return null;
      const live = n => { const ed = C.instances[n]; const e = ed && ed.element && ed.element.$;
                          return !!(e && e.isConnected); };
      const names = Object.keys(C.instances).filter(live);
      const ready = n => C.instances[n] && C.instances[n].status === 'ready';
      for (const t of tokens) {
        const hits = names.filter(n => n.endsWith(t));
        if (hits.length > 1) return 'AMBIGUOUS:' + hits.join(',');
        const k = hits[0];
        if (k) return ready(k) ? k : null;
      }
      const el = n => (C.instances[n].element && C.instances[n].element.$) || null;
      for (const t of tokens) {
        const word = new RegExp(t.replace(/[-]/g, '\\\\-') + '(?![A-Za-z0-9])');
        const k = names.find(n => {
          for (let e = el(n); e; e = e.parentElement) { if (e.id && word.test(e.id)) return true; }
          return false;
        });
        if (k) return ready(k) ? k : null;
      }
      const re = new RegExp(labelRe);
      const k = names.find(n => {
        const e = el(n);
        const g = e && e.closest('.form-group, .lfr-ddm-field-group, fieldset');
        const l = g && g.querySelector('label');
        return !!l && re.test(l.textContent.replace(/\\s+/g, ' ').trim());
      });
      return k && ready(k) ? k : null;
    }
    """

    _CONTENT_DIAG_JS = """
    () => {
      const C = window.CKEDITOR;
      if (!C || !C.instances) return {ckeditor: typeof C, instances: []};
      return {ckeditor: typeof C, instances: Object.keys(C.instances).map(n => {
        const ed = C.instances[n];
        const e = ed.element && ed.element.$;
        const g = e && e.closest('[id*="ObjectField_"], [id*="qc-ar-"]');
        return `${n} (status=${ed.status}, connected=${!!(e && e.isConnected)}, container=${g ? g.id : '-'})`;
      }), editorIframes: document.querySelectorAll('iframe[title="editor"]').length};
    }
    """

    def _content_instance(self, locale: str) -> str:
        """Waits for, then returns, the CKEditor instance name of Content
        (`locale`). Raises naming every instance on the form if none is
        Content (`locale`) within CONTENT_EDITOR_TIMEOUT_MS."""
        arg = {"tokens": list(self._CONTENT_TOKENS[locale]), "labelRe": self._CONTENT_LABEL_RE[locale]}
        try:
            handle = self.page.wait_for_function(
                self._RESOLVE_CONTENT_JS, arg=arg, timeout=self.CONTENT_EDITOR_TIMEOUT_MS
            )
            name = handle.json_value()
        except Exception as exc:  # noqa: BLE001 -- re-raised with the editors found
            diag = self.page.evaluate(self._CONTENT_DIAG_JS)
            raise RuntimeError(
                f"Newsletter Content ({locale.upper()}) CKEditor not found/ready after "
                f"{self.CONTENT_EDITOR_TIMEOUT_MS} ms. Tried name tokens "
                f"{list(self._CONTENT_TOKENS[locale])}, then container id, then label "
                f"/{self._CONTENT_LABEL_RE[locale]}/. typeof CKEDITOR={diag.get('ckeditor')}; "
                f"instances on the form: {diag.get('instances') or 'NONE'}; "
                f"iframe[title=editor] count={diag.get('editorIframes', 0)}. "
                "Update CONTENT_FIELD_NAMES from the instance names above."
            ) from exc
        if name.startswith("AMBIGUOUS:"):
            raise RuntimeError(f"Newsletter Content ({locale.upper()}): more than one live CKEditor "
                               f"matches -- {name[len('AMBIGUOUS:'):]}")
        return name

    def content_html(self, locale: str = "en") -> str:
        name = self._content_instance(locale)
        return self.page.evaluate("(n) => CKEDITOR.instances[n].getData()", name)

    def set_content_html(self, html: str, locale: str = "en") -> "NewsletterWorkflowPage":
        """setData() + updateElement() + change -- the only way to put raw
        markup (an unclosed <div>, a <script>) in, like the source view.
        Same call as ChambersLawAdminPage.set_intro_html()."""
        name = self._content_instance(locale)
        self.page.evaluate(
            "([n, html]) => new Promise(resolve => { const ed = CKEDITOR.instances[n];"
            " ed.setData(html, { callback: () => {"
            " ed.updateElement(); ed.fire('change'); resolve(true); } }); })",
            [name, html],
        )
        return self

    def content_direction(self, locale: str = "ar") -> str:
        name = self._content_instance(locale)
        return self.page.frame_locator(f'[id="cke_{name}"] iframe').locator("body").evaluate(
            "b => (getComputedStyle(b).direction || b.getAttribute('dir') || '').toLowerCase()"
        )

    def body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def access_denied_shown(self) -> bool:
        return ACCESS_DENIED_EN in self.body_text()

    def has_object_form(self) -> bool:
        return self.page.locator('input[name^="ObjectField_"]').count() > 0

    def submit_button_labels(self) -> list:
        return [t.strip() for t in self.page.locator('button[type="submit"]').all_inner_texts() if t.strip()]

    def row_action_attrs(self, title: str) -> list:
        """`data-qc-oel-*` attribute names on the row matching `title`
        exactly as rendered. Call on the open entries list."""
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title}")')
        if row.count() == 0:
            return []
        return row.first.evaluate(
            "r => Array.from(r.querySelectorAll('*')).flatMap(e => Array.from(e.attributes)"
            ".map(a => a.name)).filter(n => n.startsWith('data-qc-oel-'))"
        )

    # Read live 2026-10-13: Publish Date is a custom picker -- a visible
    # text input `#qc-dtp-<id>` (placeholder "dd/mm/yyyy hh:mm", no
    # accessible name, so the old role lookup timed out on tc_134590) bound
    # to the hidden native `input[name=ObjectField_publishDate]`
    # (datetime-local). Typing "12/10/2026 09:00" stored "2026-10-12T09:00".
    PUBLISH_DATE_NATIVE = 'input[name="ObjectField_publishDate"]'

    def set_publish_date(self, value: str) -> "NewsletterWorkflowPage":
        """`value` in the picker's own format, `dd/mm/yyyy HH:MM` (24 h)."""
        native_id = self.page.locator(self.PUBLISH_DATE_NATIVE).first.get_attribute("id")
        box = self.page.locator(f'[id="qc-dtp-{native_id}"]')
        box.click()
        box.fill("")
        box.press_sequentially(value, delay=20)
        box.press("Tab")
        return self

    def publish_date_stored(self) -> str:
        """The hidden native value the form submits (`yyyy-mm-ddTHH:MM`)."""
        return self.page.locator(self.PUBLISH_DATE_NATIVE).first.input_value()

    def set_schedule_send(self, checked: bool) -> "NewsletterWorkflowPage":
        self.set_checkbox(SCHEDULE_SEND_LABEL, checked)
        return self

    def open_manage_page_raw(self) -> "NewsletterWorkflowPage":
        """manage-newsletter WITHOUT waiting for the entries table -- for
        visitors/denied roles, where none must render."""
        from config.settings import control_panel_url
        self.open(control_panel_url(f"/web/qatar-chamber/manage-{NEWSLETTER_SLUG}"))
        self.page.wait_for_load_state("load")
        return self

    # ---- Subscriber list (admin-only surface) -----------------------------
    def open_subscriber_list(self) -> "NewsletterWorkflowPage":
        """Navigates to the Newsletter Subscriber manage page WITHOUT
        assuming it renders (permission cases expect it not to)."""
        from config.settings import control_panel_url
        self.open(control_panel_url(f"/web/qatar-chamber/manage-{NEWSLETTER_SUBSCRIBER_SLUG}"))
        self.page.wait_for_load_state("load")
        return self

    def subscriber_rows(self) -> list:
        """Every subscriber row's text. Call after open_subscriber_list()."""
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        try:
            rows.first.wait_for(state="visible", timeout=30000)
        except Exception:  # noqa: BLE001 -- an empty/denied list reads as []
            return []
        return [t.strip() for t in rows.all_inner_texts() if t.strip()]

    def subscriber_list_paginated(self) -> bool:
        """True when ANY pagination / next-page control renders, or a
        "... of N" total exceeds the rows read -- the email gate fails
        closed on it. VERIFY-LIVE: pagination markup of this list."""
        import re as _re

        if self.page.locator(
            '.pagination, [aria-label*="Next"], button:has-text("Next"), a:has-text("Next")'
        ).count() > 0:
            return True
        match = _re.search(r"of\s+(\d+)", self.page.locator("body").inner_text())
        rows = self.page.locator(self.ENTRIES_TABLE_ROW).count()
        return bool(match) and int(match.group(1)) > rows

    def login_form_visible(self) -> bool:
        return self.page.locator('input[type="password"]').count() > 0

    # ---- P3/P4 field cases (scripted OFFLINE 2026-10-13, not yet run) ------
    # Labels follow the object schema (cms/liferay-context.md, QCDEMO-129566)
    # and this surface's bilingual naming ("<Label> — العربية", a trailing
    # " *" when required -- label_pattern() tolerates it).
    SHORT_DESCRIPTION_LABEL = "Short Description"
    SHORT_DESCRIPTION_AR_LABEL = "Short Description — العربية"
    BANNER_IMAGE_LABEL = "Banner Image"
    ATTACHMENTS_LABEL = "Attachments"
    LANGUAGE_LABEL = "Language"
    STATUS_LABEL = "Status"
    # VERIFY-LIVE: Expiry Date is assumed to be the same `qc-dtp` picker as
    # Publish Date, bound to `ObjectField_<schema field name>` (expiryDate).
    EXPIRY_DATE_NATIVE = 'input[name="ObjectField_expiryDate"]'

    def _set_dtp(self, native_css: str, value: str) -> None:
        """Types `value` (`dd/mm/yyyy HH:MM`) into the visible `qc-dtp-<id>`
        picker bound to the hidden native input `native_css`."""
        native_id = self.page.locator(native_css).first.get_attribute("id")
        box = self.page.locator(f'[id="qc-dtp-{native_id}"]')
        box.click()
        box.fill("")
        box.press_sequentially(value, delay=20)
        box.press("Tab")

    def set_expiry_date(self, value: str) -> "NewsletterWorkflowPage":
        """`value` in the picker's own format, `dd/mm/yyyy HH:MM` (24 h)."""
        self._set_dtp(self.EXPIRY_DATE_NATIVE, value)
        return self

    def expiry_date_stored(self) -> str:
        """The hidden native value the form submits (`yyyy-mm-ddTHH:MM`)."""
        return self.page.locator(self.EXPIRY_DATE_NATIVE).first.input_value()

    def set_short_description(self, value: str, locale: str = "en") -> "NewsletterWorkflowPage":
        label = self.SHORT_DESCRIPTION_AR_LABEL if locale == "ar" else self.SHORT_DESCRIPTION_LABEL
        self.fill_text(label, value)
        return self

    def short_description_value(self, locale: str = "en") -> str:
        label = self.SHORT_DESCRIPTION_AR_LABEL if locale == "ar" else self.SHORT_DESCRIPTION_LABEL
        return self.field_value(label)

    def _textbox_present(self, label: str) -> bool:
        return self.page.get_by_role("textbox", name=self.label_pattern(label)).count() > 0

    def _upload_present(self, label: str) -> bool:
        return self.page.get_by_role("textbox", name=f"{label} Select File").count() > 0

    def upload_control_present(self, label: str) -> bool:
        """The field's Documents & Media upload control is on the form."""
        return self._upload_present(label)

    def _combo_present(self, label: str) -> bool:
        return self.page.get_by_role("combobox", name=self.label_pattern(label)).and_(
            self.page.locator(self.FORM_COMBOBOX)
        ).count() > 0

    def _dtp_present(self, native_css: str) -> bool:
        native = self.page.locator(native_css)
        if native.count() == 0:
            return False
        native_id = native.first.get_attribute("id")
        return self.page.locator(f'[id="qc-dtp-{native_id}"]').count() > 0

    def _content_present(self, locale: str) -> bool:
        try:
            self._content_instance(locale)
            return True
        except RuntimeError:
            return False

    def form_field_presence(self) -> dict:
        """{case field name: rendered?} for the create/edit form (TC 134537).
        Call on an open form; waits for Title (EN) to hydrate first."""
        self.page.get_by_role("textbox", name=self.label_pattern(TITLE_EN_LABEL)).first.wait_for(
            state="visible", timeout=20000
        )
        return {
            "Title (EN)": self._textbox_present(TITLE_EN_LABEL),
            "Title (AR)": self._textbox_present(TITLE_AR_LABEL),
            "Subject Line (EN)": self._textbox_present(SUBJECT_EN_LABEL),
            "Subject Line (AR)": self._textbox_present(SUBJECT_AR_LABEL),
            "Short Description (EN)": self._textbox_present(self.SHORT_DESCRIPTION_LABEL),
            "Short Description (AR)": self._textbox_present(self.SHORT_DESCRIPTION_AR_LABEL),
            "Content (EN)": self._content_present("en"),
            "Content (AR)": self._content_present("ar"),
            "Banner Image upload": self._upload_present(self.BANNER_IMAGE_LABEL),
            "Attachments upload": self._upload_present(self.ATTACHMENTS_LABEL),
            "Language dropdown": self._combo_present(self.LANGUAGE_LABEL),
            "Status dropdown": self._combo_present(self.STATUS_LABEL),
            "Publish Date": self._dtp_present(self.PUBLISH_DATE_NATIVE),
            "Expiry Date": self._dtp_present(self.EXPIRY_DATE_NATIVE),
        }

    # ---- entries table read (TC 134538) ------------------------------------
    ENTRIES_TABLE_HEADER = "table thead th"
    _ROW_ACTIONS_JS = """
    r => Array.from(r.querySelectorAll('a, button')).map(e => ({
      text: (e.innerText || e.getAttribute('aria-label') || e.getAttribute('title') || '').trim(),
      attrs: Array.from(e.attributes).map(a => a.name).filter(n => n.startsWith('data-qc-oel-'))
    }))
    """

    def entries_table(self) -> dict:
        """{"headers": [...], "rows": [{"cells": {header: text}, "actions":
        [{"text", "attrs"}]}]} for the CURRENT page of the open entries list.
        Read-only. Call after open_entries_list()."""
        headers = [" ".join(t.split()) for t in self.page.locator(self.ENTRIES_TABLE_HEADER).all_inner_texts()]
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        out = []
        for i in range(rows.count()):
            row = rows.nth(i)
            tds = [" ".join(t.split()) for t in row.locator("td").all_inner_texts()]
            cells = {(headers[j] if j < len(headers) else f"col{j}"): tds[j] for j in range(len(tds))}
            out.append({"cells": cells, "actions": row.evaluate(self._ROW_ACTIONS_JS)})
        return {"headers": headers, "rows": out}

    # ---- file fields -------------------------------------------------------
    def attached_filename(self, label: str) -> str:
        """The field's filename readout ("" when nothing is attached).
        Strict: raises unless exactly ONE readout carries the label, so a
        wrong label can never read as "no file attached"."""
        readout = self.page.get_by_role("textbox", name=self.label_pattern(label))
        found = readout.count()
        if found != 1:
            raise LookupError(f"{label!r}: {found} filename readouts on the form, expected exactly 1")
        # The readout shows a newly SELECTED file only; a SAVED file is in the
        # field's `Current file:` block (read live 2026-10-13 on the sample
        # newsletter: readout "" vs current "press-kit.pdf").
        return readout.inner_text().strip() or self.current_file_name(label)

    # ---- validation reads --------------------------------------------------
    # Same selector family as DisposableObjectAdminPage.REFUSAL_BAR plus
    # Clay's inline feedback. Only elements carrying text count: every field
    # renders an always-present, EMPTY `role=alert` slot (live 2026-10-13).
    VALIDATION_ERRORS = '[role="alert"], .alert-danger, .form-feedback-item'

    def visible_error_texts(self) -> list:
        out = []
        found = self.page.locator(self.VALIDATION_ERRORS)
        for i in range(found.count()):
            el = found.nth(i)
            try:
                text = " ".join((el.inner_text(timeout=2000) or "").split())
                if text and el.is_visible():
                    out.append(text)
            except Exception:  # noqa: BLE001 -- detached between count and read
                continue
        return out

    def combo_value(self, label: str) -> str:
        """Current value of the form's Language / Status combobox."""
        combo = self.page.get_by_role("combobox", name=self.label_pattern(label)).and_(
            self.page.locator(self.FORM_COMBOBOX)
        ).first
        combo.wait_for(state="visible", timeout=20000)
        return combo.input_value()
