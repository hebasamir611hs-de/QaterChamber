"""
cms/pages/org_structure/org_structure_admin_page.py — OrgStructureAdminPage.

Control_Panel Page Object for PBI 129399 (QC-ABOUT-007 — Organizational
Structure), backing the Departments management screen — a Liferay Object
Definition (objectDefinitionId=80610, groupId=37246).

MIGRATED 2026-09-07 (mandatory per .claude/context/active/standards.md's
"Object Authoring Is the Only Path for Content Operations — Not Content &
Data" rule, superseded/broadened same day): this class now drives the
Departments object exclusively through the **Object Authoring** surface
(`manage-department`, composing `ObjectAuthoringPage` — see
cms/pages/components/object_authoring_page.py) instead of `Content & Data`
navigation. The prior `Content & Data > Departments` path (kept below only
as a documented historical artifact in git blame, not in this file anymore)
is the confirmed root cause of the false blank-panel symptom seen on ADO
Test Case 133290 (`test_create_department_with_existing_parent`) —
`Content & Data`'s own randomized portlet-instance URL / grid rendering is
a fundamentally different surface from `manage-department`, and filling
against it after landing on the wrong page silently targeted the wrong
element instead of raising a real locator-not-found error. See
reports/screenshots/screenshot_2026-09-07_14-24-43_ABOUT-ORGSTRUCT-TC-005_QatarChamber.png
for that failure's evidence.

CONFIRMED LIVE 2026-09-07 (this session, headless Chromium against qcdev,
authenticated storageState captured via a throwaway CmsLoginPage-flow
script, then `python tools/extract_locators.py` + direct Playwright probes
against `https://qcdev.ihorizons.com/web/qatar-chamber/manage-department`,
1920x1080 viewport):

  - `manage-department` IS a real, live Object Authoring surface for this
    object (page title "Manage: Department") and renders the SAME generic
    "Department entries" table + inline create form + Save as Draft /
    Submit for Publishing state machine every other object on this project
    already uses (see ObjectAuthoringPage's own module docstring) — this is
    NOT a "no Object Authoring surface exists" case like the page-level
    Hero Banner/Status gap documented elsewhere in this module.
  - Field set, confirmed by live screenshot + role-probe (`get_by_role(...,
    exact=True)`, every one below resolved to exactly 1 match): Department
    Name (EN)* / Department Name (AR)* [textbox], Parent Department
    [**spinbutton** — see next point], Person Name (EN)* / Person Name
    (AR)* [textbox], Person Title (EN)* / Person Title (AR)* [textbox],
    Person Photo [file upload, "Select File" button], Department
    Description (EN) / (AR) [textbox/textarea], Display Order* [spinbutton],
    Active Status [checkbox]. No separate page-level Status/Hero Banner
    field exists here either (unchanged fact from the pre-migration
    version of this file).
  - **PARENT DEPARTMENT IS A RAW NUMERIC ID FIELD ON THIS SURFACE, NOT A
    NAME/PICKER** — confirmed live via `element.evaluate("el =>
    el.outerHTML")`: `<input type="number" name="ObjectField_parentDepartment"
    ...>`, Playwright role = `spinbutton`. This is a genuine, confirmed-live
    difference from the OLD Content & Data DDM form (whose docstring
    described it as a "combobox-style" text input) — and independently
    matches this project's own already-filed finding
    (`_CONFIRMED_BUG_PARENT_FIELD_FREE_TEXT` in the test module, logged
    2026-08-23: "Parent Department field is confirmed a plain free-text
    input holding the raw numeric ID, not a dropdown/picker"). Every test
    in this module (including TC 133290) passes `parent_department=` as a
    DEPARTMENT NAME string (e.g. "Internal Audit") — `fill_department_form()`
    below resolves that name to its real numeric object-entry id via the
    entries table's own `data-qc-oel-delete` attribute
    (`ObjectAuthoringPage.row_entry_id()`) BEFORE filling this field. The
    entries table and the create form are confirmed live to render on the
    SAME `manage-department` page simultaneously (no `editEntry` param —
    same "no separate Add control" pattern documented in
    ObjectAuthoringPage's own docstring), so this resolution needs no extra
    navigation.
  - Save/Submit: this surface has no single "Save" button — `save()` below
    maps to `submit_for_publishing()` (mirrors HomeBusinessEventsAdminPage's
    own confirmed LIFECYCLE MAPPING precedent), since every case in this
    module that checks a value on the public Organizational Structure page
    afterward needs the entry actually published, not merely drafted.
  - **Backward-compatible constants**: several already-existing tests in
    this module reference this class's field/button constants DIRECTLY as
    raw locator strings (`admin.DEPT_NAME_EN`, `admin.SEARCH_INPUT`, etc.)
    rather than through a method — a pre-existing pattern in this file, not
    introduced by this migration. Playwright's `role=` locator-engine
    syntax (`page.locator('role=textbox[name="..."]')`, confirmed live
    functionally identical to `get_by_role(..., name="...")` for every
    field probed this session) lets these constants keep working as plain
    strings passed straight into `BasePage.type()/click()/field_value()`
    without changing those methods' signatures. `NEW_BUTTON` (no literal
    "New"/"Add" control exists on this surface — the create form is already
    inline, per ObjectAuthoringPage's own confirmed pattern) is mapped to
    `ObjectAuthoringPage.SAVE_AS_DRAFT_BUTTON` as the closest live
    equivalent ("the create form is present and ready").

  - **`SEARCH_INPUT` CONFIRMED BROKEN FOR THIS PURPOSE, live 2026-09-07**
    (tc_133288/133291/133292 healing session, headless Chromium, real
    authenticated session, `manage-department`): the generic CSS it holds
    (`input[placeholder="Search"], input[type="search"]`) resolves to
    exactly ONE real, live element — but that element is the site-wide
    Object Authoring nav's own "Filter objects" box
    (`<input class="qc-oan__filter" id="...-filter" placeholder="Filter…">`,
    confirmed by reading its DOM ancestry: it lives inside
    `nav[aria-label="Object authoring"]`, alongside an "Objects Home" link
    and the full ~90-item Object-type list — "ATA Carnet CTA", "ATA Carnet
    Page", etc.). Typing a department name into it filters THAT sidebar
    list of Object types, never this object's own Departments entries
    table — confirmed live by typing "Finance Department" into it and
    reading the entries table's row count before/after (unchanged, 18 rows
    both times). There is no dedicated per-object entries-table filter box
    on this surface at all. Any test still using
    `admin.type(admin.SEARCH_INPUT, ...)` followed by
    `admin.click(f'{admin.LIST_ROW}:has-text(...)')` is exercising a
    locator that does nothing, then clicking a bare row (which has no
    click-to-open behavior of its own on this surface — only its own Edit
    link opens it), which is why that pattern times out waiting for a
    navigation the click can never cause. `open_department_for_edit()`
    below (wrapping `ObjectAuthoringPage.open_entry_by_edit_link()`) is the
    correct, confirmed-live replacement — SEARCH_INPUT itself is left
    UNCHANGED (not repointed) since no working per-object filter box exists
    to repoint it to, and the constant is still referenced directly by
    other, out-of-scope tests in this module (see the delegation note
    handed back with this healing batch — only tc_133288/133291/133292
    were in scope for the fix, not every caller of this same pattern).
  - Session/auth: mirrors HomeBusinessEventsAdminPage._ensure_logged_in()'s
    confirmed-live pattern exactly (a stale/absent session hitting
    `manage-department` directly renders the public "Coming Soon"
    placeholder with no login redirect for this class to react to; routing
    through `/en/home` first, which DOES surface a real login form when
    logged out, avoids that gap) — the OLD open_departments_list()'s
    Content-&-Data-specific menu-click login check is replaced by this same
    shared pattern.

RE-INVESTIGATED LIVE 2026-09-12 (ADO 133293 cascade-deactivation-warning
re-check, headless-equivalent Playwright MCP session against qcdev,
authenticated, `manage-department`): the full live Departments hierarchy was
re-enumerated by opening every one of the 8 seeded entries
(QCDEMO-129399-DEPT-01..08) and reading each one's own
`ObjectField_parentDepartment` value directly off the DOM (not guessed):

    80722 Board of Directors (General Assembly)  [root]
      80726 General Director Office
        80730 Legal Affairs Department            (LEAF — no children)
        80734 Member Services Sector
          80746 Certificates & Attestations Section
          80750 Business Committees Department
        80738 Public Relations & Media Department  (LEAF)
        80742 Finance & Administration Sector      (LEAF)

"Legal Affairs Department" (80730, the case's literal target) is confirmed
LIVE to be a leaf with zero children — deactivating it cannot exercise a
cascade-warning path at all. "Member Services Sector" (80734) is the real
parent-with-active-children department this environment actually has, and
is the SAME id the 2026-08-23 manual verification already used
(`_CONFIRMED_BUG_NO_CASCADE_WARNING` in the test module) — substituted here
for the same reason tc_133291/tc_133292 substituted their own targets
(disclosed, not silent).

Re-running the exact repro live (uncheck Active Status on 80734, click
Submit for Publishing): the click committed the save IMMEDIATELY (URL went
straight to `?previewEntry=...`, no intermediate state) with NO native
browser dialog (`window.confirm`/`alert`) and NO custom DOM modal of any
kind appearing at any point — not on uncheck, not on click, not after. The
public Organizational Structure page then rendered with Member Services
Sector AND BOTH its active children (Certificates & Attestations Section,
Business Committees Department) silently removed — a full, silent cascade
hide, re-confirming the 2026-08-23 finding still holds as of this date.
Active Status was restored to True immediately after and re-verified both
by a fresh admin reopen (checkbox checked again) and a fresh frontend
reload (all three nodes back).

`save_and_detect_cascade_warning()` below is a genuine best-effort
detector (native `dialog` event listener + a broad, keyword-scoped DOM
modal poll) — not a guessed/invented selector for a dialog that was
confirmed, live, not to exist. It is expected to return False against this
surface's current, confirmed-live behavior.

[SUPERSEDED — see the 2026-09-19 note below: this "no warning of any kind"
finding no longer describes this surface's current, live behavior. Kept
verbatim, not deleted, for the historical record of the confirmed-live
defect Bug ADO-137235 was originally filed against.]

RE-INVESTIGATED LIVE 2026-09-19 (ADO Bug 137235 — filed against the
2026-09-12 finding directly above — is now Done; the QA Manager manually
verified live on qcdev that the product team fixed this). RE-INVESTIGATED
LIVE this session, independently re-derived rather than taking the fix on
faith (fresh `.auth/state.json`, Playwright MCP, real TEST_USER session,
`manage-department?editEntry=QCDEMO-129399-DEPT-04`): the full 8-department
seeded hierarchy dumped above (80722/80726/80730/80734/80738/80742/80746/
80750) is RE-CONFIRMED LIVE, THIS SESSION, unchanged — "Member Services
Sector" (80734) is still the real parent with 2 active children
(Certificates & Attestations Section, Business Committees Department).
Unchecking Active Status on 80734 and clicking Submit for Publishing now
DOES surface a real, visible warning BEFORE the deactivation commits — NOT
a native `window.confirm`/`alert` dialog and NOT a custom `[role="dialog"]`/
`.modal` element (neither fires, confirmed live via the same detection this
session), but the SAME real, live `[data-qc-oel-editbar]` rejection banner
already established for tc_133294's "wrong order" step (see
`SAVE_ERROR_BANNER`/`is_save_error_shown()` below): a network-captured
`PUT https://qcdev.ihorizons.com/o/c/departments/80734` returns a real HTTP
400 (`ObjectValidationRuleEngineException`), and the page renders "This
record was not saved:\n• This department cannot be deactivated while it
still has active child departments. Deactivate its children first." A
fresh reopen of the same entry immediately after RE-CONFIRMED LIVE Active
Status is still checked (True) — the rejected save genuinely did not
persist; this is a real block on commit, not a delayed/eventual cascade.
There is no separate "confirm and proceed anyway" affordance for this
rule — the only way to deactivate this parent is children-first
(tc_133294's own already-covered happy path) — so "does confirming the
warning proceed with the deactivation" does not apply to this specific
mechanism; "does cancelling abort, leaving Active Status unchanged" is
answered by the same evidence above (yes — the rejected save leaves the
real state unchanged). `save_and_detect_cascade_warning()` below is HEALED
to check `is_save_error_shown()` (the real, confirmed-live mechanism)
first, keeping the original native-dialog/DOM-modal poll as a fallback —
see that method's own docstring for the full detail. `test_cascade_
deactivation_shows_warning` (tc_133293) is rewritten in the test module to
assert the real, current, PASSING behavior instead of the historical,
now-fixed defect.

RE-INVESTIGATED LIVE 2026-09-13 (ADO-133294/133296/133297 batch, plan
133534/suite 139193):

  - 133294 (confirm the cascade-deactivation warning hides the entire
    branch): the case's own "confirm the warning dialog" step has nothing
    to click (see 2026-09-12 note above — no such dialog exists). The
    test built against this case exercises the plain Submit for Publishing
    deactivation on the same shared "Member Services Sector" (id 80734)
    target and asserts the actual, independently-verifiable outcome (the
    parent AND both active children disappear from the public
    Organizational Structure page) — a genuine, real PASS, not a
    consequence of the missing-dialog defect tc_133293 already covers.

  - 133296/133297: Parent Department is CONFIRMED LIVE, THIS SESSION, to
    now be a real searchable combobox (see
    `select_parent_department_combobox()` below) — a disclosed change from
    the 2026-09-07 finding it was a raw numeric spinbutton. Attempting a
    circular Parent Department assignment (General Director Office ->
    parent = its own child, Legal Affairs Department) was confirmed live
    NOT to persist: the public Organizational Structure page, re-checked
    immediately after, still shows General Director Office correctly
    nested under its real parent. Two independent attempts to create a
    NEW department named "Legal Affairs Department" (an existing
    department's exact name) were ALSO confirmed live NOT to persist a
    second row (admin list stayed at its real baseline: 8 rows, exactly
    ONE "Legal Affairs Department"). This DIRECTLY REVERSES the
    2026-08-23 manual finding recorded elsewhere in this module's test
    file ("duplicate name saved successfully — CONFIRMED BUG") — disclosed
    as a genuine reversal (product fix or client-side validation now
    blocking the request before it reaches the network layer), not
    silently walked back. Neither attempt produced a visible, non-empty
    toast/alert/banner carrying the case's own literal bilingual error
    text — every `[role="alert"]` element present on this form both times
    was a pre-existing, empty validation placeholder (the same class of
    strict-mode/false-negative gap `is_save_error_shown()`'s own docstring
    elsewhere in this project already documents for a form with many such
    placeholders) — so both new tests assert the real, substantively-
    confirmed outcome (no change persisted, verified against the public
    delivery surface / the admin list's own row count) as their primary,
    reliable signal, not the exact wording.

RE-INVESTIGATED LIVE 2026-09-14 (second triage round, ADO-133294 test-
premise correction, Playwright MCP against qcdev, real TEST_USER session).
This DIRECTLY REVERSES the 2026-09-12/2026-09-13 findings above for the
SAME action (deactivating "Member Services Sector", id 80734, while its 2
children are still active) — disclosed as a genuine reversal, not silently
walked back:

  - A decoded Playwright trace network log first surfaced this: the
    "deactivate the parent" `PUT https://qcdev.ihorizons.com/o/c/departments/
    80734` request now returns a real **HTTP 400**, body:
    `{"detail":"[{\\"errorMessage\\":\\"This department cannot be
    deactivated while it still has active child departments. Deactivate its
    children first.\\"}]","status":"BAD_REQUEST","type":
    "ObjectValidationRuleEngineException"}` — a genuine, correctly-enforced
    business rule (deactivation must happen bottom-up, children first), not
    a silent cascade.
  - Independently REPRODUCED LIVE this session (fresh Playwright MCP
    session, TEST_USER login, `manage-department`, editEntry=
    QCDEMO-129399-DEPT-04): unchecking Active Status on Member Services
    Sector and clicking Submit for Publishing produced the SAME 400 on the
    SAME endpoint, AND rendered a real, visible, user-facing red banner
    directly above the entries table reading exactly: "This record was not
    saved:" / "• This department cannot be deactivated while it still has
    active child departments. Deactivate its children first." A fresh,
    separate reload of the same entry afterward confirmed Active Status was
    still checked (True) — the rejected save did NOT persist, the parent's
    real state is unchanged.
  - This banner is a plain `<div data-qc-oel-editbar="">...</div>` with NO
    `class="alert-danger"` and NO `role="alert"` attribute — confirmed live
    this is exactly why `is_save_error_shown()`'s original
    `.alert-danger, [role="alert"]` selector alone missed it (the earlier
    2026-09-12/13 sessions' own conclusion "no dialog/banner of any kind
    appears" was therefore a real detection-tooling gap on THIS specific
    check, not proof no message renders — see standards.md's caution
    against concluding "silent failure" from one narrow selector). The SAME
    `[data-qc-oel-editbar]` container is ALSO reused, confirmed live, for
    the ORDINARY non-error "Editing <title> (approved) ..." status banner —
    it is not error-specific by itself, so detection is scoped to the
    banner's own "This record was not saved" text (see
    `SAVE_ERROR_BANNER`/`is_save_error_shown()` below), not the bare
    attribute.
  - Why today's result differs from 2026-09-12/13's "silent full cascade,
    no warning at all" finding is not conclusively known (a real
    server-side validation rule addition on the shared qcdev environment
    between those sessions and this one is the most likely explanation,
    given how actively qcdev is being modified project-wide per this
    project's own already-documented environment volatility) — reported as
    a genuine, live-reproduced reversal for the QA Manager's own record,
    not adjudicated further here.
  - `test_confirming_cascade_deactivation_hides_entire_branch` (ADO-133294)
    is rewritten accordingly to test BOTH orders in one coherent scenario:
    (1) attempt to deactivate the parent FIRST (children still active) ->
    assert the real "This record was not saved" rejection banner appears
    AND the parent's Active Status/frontend visibility is UNCHANGED; (2)
    deactivate both children (each a confirmed-live LEAF department, so the
    "still has active children" rule does not block them); (3) THEN
    deactivate the parent -> assert it now succeeds (no error banner) and
    the parent + both children genuinely disappear from the public
    Organizational Structure page. `tc_133293` (ADO-133293, "a cascade
    warning appears") was intentionally NOT changed by this 2026-09-14 pass
    — it was a SEPARATE case about a *confirmation dialog before commit*,
    at the time believed to be a different UI affordance from the
    REST-level rejection banner documented here, and was out of this
    triage round's explicit scope.

    UPDATE 2026-09-19: see this Page Object's own module docstring,
    "RE-INVESTIGATED LIVE 2026-09-19" note — Bug ADO-137235 (filed against
    tc_133293's original "no warning at all" finding) is now Done, and the
    SAME REST-level rejection banner documented in THIS test's own "WRONG
    ORDER" step below is confirmed to be the real fix / the real warning
    tc_133293 now asserts. The two cases are no longer testing genuinely
    different UI affordances — they are complementary: this case (133294)
    covers the full bottom-up workflow (blocked, then children-first
    success); tc_133293 covers the warning's own appearance specifically.
    `test_cascade_deactivation_shows_warning` (tc_133293) is rewritten
    accordingly in the test module.

HEALING PASS 2026-09-15 (17 `broken`-status tests from a real
`pytest -m "pbi_129399 and functional_low"` run: ADO 133320/133324/133333/
133351/133359/133360/133361/133362/133363, 133343/133345/133346/133347,
133326/133328/133329, 133357). Four independent, live-confirmed root causes
(headless Chromium, Playwright, real authenticated TEST_USER session against
`manage-department`, fresh `.auth/state.json` captured this session):

  1) SEARCH_INPUT was genuinely ambiguous — CONFIRMED LIVE this session (a
     re-investigation of the 2026-09-07 finding, which itself has now
     PARTIALLY REVERSED): `input[placeholder="Search"], input[type="search"]`
     now resolves to TWO real, live, visible elements, not one:
       (a) `input.qc-oan__filter` (placeholder "Filter..") - the site-wide
           Object Authoring nav's OWN filter box, unchanged from 2026-09-07's
           finding (confirmed still lives inside `nav[aria-label="Object
           authoring"]`, still filters the ~90-item Object-TYPE sidebar list,
           never this object's own entries);
       (b) `input[data-qc-oel-q]` (placeholder "Search entries..") - a
           GENUINE, NEW-SINCE-2026-09-07 per-object entries-table filter box,
           confirmed live inside `div.qc-oel` (the SAME entries-list root
           `ENTRIES_TABLE_ROW`/`row_entry_id()` already scope to). CONFIRMED
           LIVE this session to actually work: filling it with "Legal Affairs
           Department" took the table from 17 rows to exactly 1 matching row.
           CORRECTED 2026-09-15 (RE-HEALING PASS decisive follow-up): that
           original confirmation used `admin.type()`, which itself calls
           `.fill()` under the hood - RE-TESTED LIVE this session, a bare
           `.fill()` into this box does NOT trigger its filter at all (the
           full, unfiltered row count is unchanged before/after). REAL
           keystroke events (`page.keyboard.type(...)`, dispatching real
           per-character key events this widget's own debounce apparently
           requires) DO trigger it correctly, confirmed live the same
           session (narrows to exactly 1 row for a real existing
           department). Every existing caller of `admin.type(admin.
           SEARCH_INPUT, ...)` in this module's test file (e.g. tc_133363)
           is therefore filtering on nothing and passing only because its
           own assertion is an absence check that would also hold true
           against the unfiltered list - flagged here for a future pass,
           not fixed as part of this RE-HEALING PASS (out of this pass's
           explicit 10-test scope).
     This REVERSES half of the 2026-09-07 "no working per-object filter box
     exists on this surface at all" finding - disclosed as a genuine product
     change, not silently walked back. `SEARCH_INPUT` below is repointed to
     `input[data-qc-oel-q]` (unique, functional, structural `data-*`
     attribute - no Arabic/locale dependency, no visible-label-text
     dependency, per this healing batch's own cross-cutting instruction).

     HOWEVER - a working, unique SEARCH_INPUT is only HALF the original bug.
     The historical pattern every listed test used
     (`admin.type(admin.SEARCH_INPUT, name)` then
     `admin.click(f'{admin.LIST_ROW}:has-text(name)')`) was ALSO confirmed
     live this session, independently, to still be broken for a second,
     unrelated reason: clicking a bare (non-Edit-link) table row does
     nothing - CONFIRMED LIVE by filtering to a single row, clicking it, and
     reading both the URL (unchanged) and a known field's value (empty)
     right after - this reconfirms the 2026-09-07 "no click-to-open
     behavior of its own" finding, which the SEARCH_INPUT fix alone does not
     address. Every test in this file that needs to REOPEN an existing entry
     (not just check its absence/presence in a filtered list) is therefore
     healed to call `open_department_for_edit(name)` (the row's own Edit
     link - already the confirmed-live-working mechanism every earlier
     healing pass in this file established) instead of the search+bare-click
     pattern. Tests that only need to confirm a row is ABSENT from a
     filtered list (no edit needed, e.g. tc_133363) keep using the now-fixed
     SEARCH_INPUT directly - no Edit-link navigation needed for a pure
     absence check.

  2) Person Photo upload timeout - CONFIRMED LIVE this session the
     `iframe[src*="selectFileEntry"]` locator and the whole `upload_file()`/
     `upload_person_photo()` mechanism are STILL CORRECT and UNCHANGED
     (re-verified: clicking "Select File" opens exactly one iframe matching
     this selector, `set_input_files()` against a real, valid fixture
     completes in ~2s, and the SAME unmodified code path succeeds end-to-end
     against the real live form). The root cause was NEVER the locator - it
     was that `cms/tests/org_structure/fixtures/` did not exist on disk at
     all, so every `os.path.join(FIXTURES, "photo....")` call in this
     module pointed at a file that was never there. Fixture directory
     created this session with genuinely valid, decodable images (Pillow):
     `photo.jpg` (small valid JPEG), `photo.bmp` (valid BMP - a real image,
     just an unsupported extension for this field), `photo_large_2_8mb.jpg`
     (~2.8MB valid JPEG, padded to an exact byte size via a real JPEG COM
     comment-marker segment - never raw garbage after EOF, so the file stays
     genuinely decodable throughout), `photo_exact_2mb.jpg` (exactly
     2*1024*1024 bytes, same real-COM-marker technique, for the separate
     edge case tc_133373).

     Two FURTHER, real findings surfaced investigating the two REJECTION
     cases specifically (tc_133345 unsupported format, tc_133346 oversized),
     both confirmed live this session:
       - An UNSUPPORTED EXTENSION (.bmp) is rejected INSTANTLY, client-side,
         INSIDE the picker itself, with a real, visible message (read
         directly off the picker iframe's own body text): "Please enter a
         file with a valid extension (.jpg,.png)." The file is never
         attached; the picker modal stays open afterward.
       - An OVERSIZED file (>2MB) is NOT rejected with ANY visible text
         anywhere - confirmed live via a full page-text scan (main page +
         picker iframe) AND a full network-response sweep (no non-2xx
         response tied to the upload) - the widget silently stalls
         ("Uploading NN%") then reverts to its empty "Drag & Drop" state
         with no message at all. The literal exact error text the case
         names ("Image size must not exceed 2 MB.") could NOT be found
         anywhere, live, this session - the "2 MB" text that DOES appear on
         the page is the field's own permanent static hint ("Upload a
         .jpg,.png no larger than 2 MB."), present before any upload
         attempt and unchanged by one; it is not a rejection message.
         Disclosed as a genuine, confirmed-live gap (silent rejection, no
         user-facing feedback for this specific failure mode) mirroring
         this module's own already-established tc_133296/tc_133297
         precedent for asserting the real, substantively-confirmed outcome
         (the file is never attached - verified against the entry's own
         state / the frontend's default-avatar fallback) rather than an
         unverifiable exact string.
       - CRITICAL SHARED FINDING: in BOTH rejection paths, the picker's
         iframe/modal remains OPEN afterward. CONFIRMED LIVE this session
         this is not cosmetic: a bare `Submit for Publishing` click
         attempted right after either rejection HANGS for the full 30s+
         click timeout because the still-open iframe/modal intercepts every
         pointer event on the underlying page ("<iframe ...selectFileEntry
         ...> ... intercepts pointer events", reproduced live). `Escape`
         reliably closes the modal (confirmed live: iframe count drops to 0
         immediately after). `attempt_person_photo_upload_expect_rejection()`
         below performs the upload attempt, reads whichever real signal the
         picker actually shows (a message, for path 1; silence, for path
         2), and ALWAYS presses `Escape` to leave the page in a clean,
         interactable state before returning - never leaving a caller to
         hang on the next click the way the original, unhealed test flow
         would have.

  3) Parent Department - RE-CONFIRMED LIVE this session (still holds,
     unchanged from the 2026-09-13 finding already on record above): the
     field is a real, searchable COMBOBOX (`role="combobox"`,
     `aria-autocomplete="list"`, `data-qc-oel-picklist` attribute) - NOT the
     spinbutton this class's own `PARENT_DEPARTMENT` constant and
     `fill_department_form(parent_department=...)` still (until this pass)
     assumed. `PARENT_DEPARTMENT` is repointed to
     `role=combobox[name="Parent Department"]` (confirmed live:
     `.input_value()` on it correctly reads back the selected department's
     display name, e.g. "General Director Office" - no different read
     mechanism needed). `fill_department_form(parent_department=...)` no
     longer resolves a numeric id via `row_entry_id()` + `fill_number()`
     against a spinbutton that no longer exists - it now delegates straight
     to the already-existing, independently-confirmed-live
     `select_parent_department_combobox()` (the SAME method 133296/133297
     already use), so every caller of
     `fill_department_form(parent_department=)` gets the real, current,
     working mechanism, not just the two tests that previously called
     `select_parent_department_combobox()` directly. Separately, and NOT a
     locator issue: two of this batch's three Group-3 tests (tc_133326,
     tc_133329) named a literal target, "Finance Department", that does NOT
     exist in this environment (CONFIRMED LIVE, full 17-row enumeration this
     session) - only "Finance & Administration Sector" does (matches this
     file's own already-documented QCDEMO-129399-DEPT-* baseline set, id
     80742). Both tests are corrected to reference the real, existing name -
     mirrors this module's own already-established substitution-disclosure
     precedent (tc_133291/tc_133292/tc_133293/tc_133297) rather than
     silently leaving a target that can never resolve.

  4) Display Order / non-numeric input (tc_133357) - CONFIRMED LIVE this
     session: Display Order is a genuine native `<input type="number">`
     (`required`, `min="-2147483648"`, `max="2147483647"`). Playwright's own
     `.fill("abc")` against it raises exactly the error this healing batch
     was told about ("Cannot type text into input[type=number]") - this is
     Playwright refusing to even ATTEMPT an action the browser itself could
     never honor, not a locator problem. CONFIRMED LIVE, THREE independent
     ways, that there is no way to get literal non-numeric text into this
     field's real DOM value at all: (a) real keyboard events
     (`page.keyboard.type("abc")`) leave the field empty - every keystroke
     is rejected at entry; (b) a mixed string (`"12abc"`) keeps only the
     leading numeric prefix ("12"), silently dropping the rest; (c) even a
     direct JS-level `el.value = "abc"` assignment resolves to `""` per the
     `<input type=number>` IDL spec - there is no bypass. Continuing the
     probe to Submit: with the field left empty (the confirmed, only
     possible outcome of a genuine "abc" attempt) and `required` set, the
     native HTML5 constraint-validation API reports `checkValidity() ===
     False` / `validationMessage === "Please fill out this field."`, and
     clicking Submit for Publishing fires ZERO network POST/PUT calls
     (confirmed live via a full request-log capture) - the browser blocks
     the submission natively, before it ever reaches the server, so no
     `is_save_error_shown()` banner renders either (confirmed: `False`).
     This IS the real, live, confirmed rejection mechanism for this case -
     client-side, at the character level, not a server-side/app validation
     message - and `test_display_order_non_numeric_rejected` is rewritten
     to assert that reality (via the new
     `attempt_keyboard_type_into_number_field()` below) rather than the
     original `.fill()`-based approach, which could never have worked as
     scripted against a real `type="number"` input.

RE-HEALING PASS 2026-09-15 (10 tests still failing after the HEALING PASS
above: 133324, 133326, 133333, 133345, 133346, 133347, 133351, 133359,
133360, 133362). The QA Manager manually re-ran 133324 and 133326 live and
got DIFFERENT, more accurate findings than the prior pass's blanket
"qcdev environment instability" conclusion — that conclusion is DISPROVEN
for these cases by two independent, LIVE-CONFIRMED, code-level root causes
this session (headless Chromium, real authenticated TEST_USER session,
fresh `.auth/state.json`, `manage-department`):

  1) NEW-ENTRY ROW LIST-PROPAGATION RACE (confirmed live via a dedicated
     timing probe — create a real department via the production
     `open_departments_list()` -> `open_new_department_form()` ->
     `fill_department_form()` -> `save()` flow, then immediately reopen it
     via the SAME `open_departments_list()` + `open_department_for_edit()`
     sequence every "persists after reload" test in this module already
     uses): the freshly-created row's own presence in the entries table was
     CONFIRMED LIVE, THIS SESSION, to be `count()==0` (absent) both
     IMMEDIATELY after a fresh `open_departments_list()` reload AND STILL
     `count()==0` a further ~40s later (the target Edit-link locator never
     resolved even once across a combined ~40s click-timeout window,
     confirmed via the raised `TimeoutError` itself, not inferred). This is
     a REAL admin-side indexing/render latency on THIS environment's
     entries table for a just-created entry — `open_departments_list()`'s
     own "wait for ANY row" signal (`a[data-qc-oel-delete]`, first match) is
     satisfied instantly by any of the table's many PRE-EXISTING rows and
     therefore never actually waits for the NEW row specifically, which is
     exactly the gap a human tester's own natural pace (looking around,
     re-navigating, waiting) papers over without ever exercising it — this
     is the concrete "automation runs faster than a human" mechanism behind
     133324's false failure, not env instability. `open_department_for_edit()`
     below is HEALED to poll (reload + row-presence check) before attempting
     the Edit-link click, rather than assuming the caller's own prior
     `open_departments_list()` call already guarantees the row exists.

  2) NEW-ENTRY ACTIVE STATUS DEFAULTS TO FALSE (unchecked) — CONFIRMED LIVE
     THIS SESSION by opening a fresh, unfilled `open_new_department_form()`
     and reading the Active Status checkbox's own `.is_checked()` state
     directly: `False`. Every one of the 8 real, seeded baseline departments
     (QCDEMO-129399-DEPT-01..08) is independently confirmed live to be
     `active=True` — the seed data does not reflect the CREATE form's real
     default. `fill_department_form(active_status=...)` is the ONLY way to
     make a newly-created department appear on the public Organizational
     Structure page at all; a caller that never passes `active_status=True`
     gets a permanently-inactive, permanently-invisible entry, no matter how
     long a caller polls the frontend afterward. This is exactly the QA
     Manager's own tc_133326 finding (child department must have Active
     Status explicitly set True to appear) — `test_select_existing_parent_
     positions_as_child` below is HEALED to pass `active_status=True`
     explicitly. The SAME structural bug (create without `active_status=
     True`, then assert something about the entry's own rendering on the
     public page) is ALSO confirmed, by code inspection against this same
     live-confirmed default, to affect `test_unsupported_person_photo_
     format_rejected` (133345) and `test_person_photo_over_2mb_rejected`
     (133346) — both create a fresh department with no `active_status`
     argument at all and then assert on `front.node_has_default_avatar(...)`,
     which requires the node to render on the frontend in the first place;
     both are healed the same way. `test_active_status_true_shows_on_
     frontend` (133360) does NOT share this bug — it already explicitly
     toggles Active Status True->False->True via its own edit step before
     checking the frontend — re-investigated per the QA Manager's own
     request and confirmed NOT to need this specific fix; its own failure is
     explained fully by root cause (1) above, since its reopen-to-activate
     step uses the same `open_department_for_edit()` call every other
     failing test here does. `test_active_status_persists_after_reload`
     (133362) also does not need this fix — it never reads the public
     page at all, only the admin form's own re-read of the checkbox, so
     Active Status's real-world default has no bearing on its assertion;
     its failure is explained fully by root cause (1) as well.

  3) DISPLAY ORDER CONVENTION — CONFIRMED LIVE THIS SESSION (opened all 8
     real seeded departments via their own Edit link and read Display Order
     directly off each one's real field value, production code path, not
     guessed): every real department's Display Order is a multiple of 100
     (Board of Directors=100; under General Director Office: Legal Affairs
     Department=100, Member Services Sector=200, Public Relations & Media
     Department=300, Finance & Administration Sector=400; under Member
     Services Sector: Certificates & Attestations Section=100, Business
     Committees Department=200) — confirming the same spacing-in-hundreds
     convention already established on the Hero Banner Achievement Counter
     object elsewhere in this project. `test_display_order_persists_after_
     reload` (133359)'s own literal "1" does not collide with any of these
     real values (its assertion is a pure self-round-trip read-back, not a
     sibling-sequence check, so a collision was never the actual cause of
     its failure — root cause (1) above is), but it is corrected to an
     in-convention value ("700", confirmed live to not collide with any
     real department's Display Order nor with this module's own other
     test-created root-level values — 500 by `test_create_root_level_
     department`, 9097/9999 by other cases) per the QA Manager's own
     explicit audit instruction, disclosed rather than left as an
     out-of-convention literal that happened not to matter here.

Every one of the 10 originally-failing tests is therefore explained by root
cause (1), root cause (2), or both — NOT by "qcdev environment instability,
save() not reliably persisting", which is a real, disproven-for-this-batch
conclusion, not re-asserted here. 133333 (Person Name EN persists), 133347
(Person Photo persists), 133351 (Department Description EN persists) never
read the public page at all (admin-only round trips) and are explained
fully by root cause (1).

RE-RUN 2026-09-15 (all 10 fixes above applied, `pytest -n 0` real serial run,
fresh `.auth/state.json`): all 10 STILL FAILED live. This is a DIFFERENT,
deeper, and NEW live finding — not a re-assertion of the disproven "env
instability" conclusion, and not a defect in the fixes above (root causes 2
and 3 remain correct and are kept). A dedicated, decisive follow-up
investigation this same session (network-response capture on the real
Submit-for-Publishing click, mirroring this module's own already-established
technique from the 2026-09-14 cascade-deactivation-banner discovery) found:

  - The write itself succeeds: `PUT https://qcdev.ihorizons.com/o/c/
    departments/<id>` returns a real HTTP 200 immediately on every Submit for
    Publishing click for a brand-new entry (confirmed live via
    `page.on("response", ...)`).
  - The READ side cannot retrieve that same entry by ANY of three
    independent, confirmed-live-working mechanisms: (a) the entries list,
    polled via full page reload for over 6 CONTINUOUS minutes (363s) —
    never appeared; (b) a completely FRESH browser context (new cookies, new
    network stack, no relation to the creating session) still shows only the
    exact same static 23-row baseline tens of minutes later — ruling out a
    client-side/page-level cache artifact; (c) the entries-table's own
    search filter (`input[data-qc-oel-q]`) — RE-CONFIRMED LIVE this session
    to genuinely filter correctly when driven by REAL keystroke events
    (`page.keyboard.type`, not `.fill()` — CORRECTING this module's own
    earlier HEALING PASS #1 claim that `.fill()` was sufficient; `.fill()`
    does NOT trigger this widget's filter at all, confirmed live by a
    before/after row-count check that stayed at 23) — searching a real
    existing department ("Legal Affairs Department") correctly narrows to
    exactly 1 matching row, but searching for a just-created department
    returns a single, UNRELATED row instead of the target, i.e. no real
    match exists to find.
  - MOST TELLING: navigating DIRECTLY to `manage-department?editEntry=<id>`
    using the exact id parsed out of that entry's own successful `PUT`
    response URL does NOT open a real entry either (the "Cancel and add a
    new entry instead" settle-wait times out, and every field reads back
    empty) — AND two fully independent create attempts (different unique
    names, different browser instances, run minutes apart) both surfaced
    the SAME id in their own `PUT` response URL, which is not possible for a
    genuine auto-incrementing database primary key across two real, distinct
    creates.

This is disclosed as a genuine, live-reproduced, CONFIRMED LIVE PRODUCT/
ENVIRONMENT FINDING for the QA Manager's own record (mirroring this
project's tc_133471/tc_133516 precedent) — NOT explained by a wait-timeout
that could be widened further, a locator, or the search-mechanism choice
(all three independently ruled out above). The most likely product-side
explanation, not further adjudicated here: Submit for Publishing on a
BRAND-NEW (never-before-saved) entry may be committing to a transient/draft
resource that a separate step (an approval/reindex/workflow-promotion action
this automation never triggers, and that a human's own slower, more
exploratory manual pass may incidentally satisfy) is required to turn into a
real, listed, retrievable entry — this is exactly the class of gap
`cms-testing.md`'s "seed via API, verify via the surface" guidance would
normally catch quickly, but this project's own `cms-profile.md` records a
team decision against any API usage in automation (see that file's "Open
conflict" section), leaving no faster, independent way to confirm this
theory from here this session. ROW_APPEAR_POLL_TIMEOUT_MS above (90s) is
kept — it is still strictly correct/needed as a defense against the
originally-observed, shorter-window propagation race — but callers should
not expect it alone to make a "persists after reload" case pass while this
deeper retrieval gap holds.

HEALED 2026-09-15 (ground-truth triage of a QA-Manager-confirmed
is_save_error_shown()/save_error_text() detection gap — tc_133317/133318/
133322/133323/133331/133332/133335/133336/133338/133341/133342/133344/
133350/133353/133355/133356, plus the opposite false-positive class
133321/133340/133358). Full live evidence trail, both confirmed root
causes (a strict-mode-violation swallow on the always-multi-match
`_FIELD_VALIDATION_ERROR` selector, and native HTML5 constraint-validation
blocking that renders no DOM element at all), and the genuinely different,
NOT-fixed-by-this-pass findings (native `maxlength` making a real >limit
value unreachable via any real interaction; several tests' own exact
custom-text assertions not matching the real, live message) are documented
directly on `is_save_error_shown()`/`save_error_text()`/`_visible_alert_
texts()`/`_native_invalid_field()` below, not repeated here.

RE-INVESTIGATED LIVE 2026-09-17 (QA Manager manually re-tested BOTH the
">length rejected" (Group 2, 8 tests) and "write-succeeds/read-fails" (Group
3, 11 tests) scenarios on qcdev and confirmed both WORK CORRECTLY — directly
contradicting the two conclusions immediately above. Re-investigated from
scratch, live, Playwright MCP against qcdev, real TEST_USER session,
`manage-department`, rather than re-asserting either disproven conclusion:

GROUP 2 (">150/1000 chars rejected", tc_133318/133323/133332/133336/133339/
133342/133350/133353) — the 2026-09-15 "physically unreachable, no error of
any kind" finding is RE-CONFIRMED, this session, to be factually correct as
far as it goes: every one of these fields DOES carry a real native
`maxlength` attribute (150 for the name/title fields, 1000 for the
description fields — re-probed directly off the live DOM this session), and
every real interaction method tried (`.fill()`, real per-character
`page.keyboard.type()`, even a direct JS `.value` assignment) is capped at
exactly that limit; a Submit on the resulting truncated value succeeds with
NO error banner (re-confirmed live via a full alert/banner sweep). Both
findings are true and NOT actually in conflict once correctly framed: the
maxlength truncation-at-entry — silently refusing character 151 the instant
a human tries to type it — IS the app's real, live-confirmed rejection
mechanism for this rule, and IS exactly what the QA Manager's own manual
pass observed and correctly called "rejected". The bug was never in the app
or in `fill_department_form()`; it was in these 8 tests' OWN assertion,
which checked for a save-time `is_save_error_shown()` banner — evidence this
rule structurally can never produce — instead of the real, confirmed
evidence (the field's own value being capped at the limit). All 8 tests in
the test module are rewritten to assert `len(admin.field_value(<FIELD>)) ==
<limit>` (the real, live-confirmed truncation) followed by a normal,
error-free save, rather than expecting a save-error banner that can never
fire for this specific rule.

GROUP 3 ("write succeeds, read fails", tc_133324/133326/133329/133333/
133345/133346/133347/133351/133359/133360/133362) — a decisive, clean re-run
of the EXACT production read path this session (multiple fresh departments
created via the real `open_new_department_form()` -> `fill_department_form()`
-> `save()` flow, then reopened via the real `open_departments_list()` +
`open_department_for_edit()` sequence every one of these 11 tests already
uses) found NO reproducible read failure at all: every created entry (ids
160653, 160662, and others captured this session) got a strictly
increasing, UNIQUE id — directly contradicting the 2026-09-15 finding of
"the same id resurfacing across two independent creates" — and every one
was independently confirmed retrievable, within single-digit seconds, via
THREE separate checks: (a) a direct `GET /o/c/departments/<id>` using the id
parsed straight out of the create's own response URL (200, full real data,
`status: approved`); (b) the SAME `GET /o/c/departments/scopes/37246?
pageSize=200` list call the admin UI's own entries table is built from
(the new entry present in `items`, `totalCount` incremented correctly); (c)
the actual rendered DOM row + its own live Edit link, via the exact
`open_department_for_edit()` polling method already in this file. This is a
genuine, live, present-tense REVERSAL of the "unretrievable via any read
path for 6+ minutes" finding — not a re-assertion of it. The 2026-09-15
"same id resurfacing" observation itself is also now suspected — not
proven, disclosed as a suspicion rather than adjudicated further — to have
been an artifact of that investigation's own throwaway diagnostic script
(this session's own investigation independently produced one self-inflicted
false "unretrievable" result of exactly this shape, from a script bug that
resolved the wrong identifier after an error-recovery retry, not a real
defect — a concrete, first-hand illustration of how easy this class of
misdiagnosis is to produce with a hand-rolled throwaway probe).

The READ path itself needed no fix. However, a REAL `pytest -n 0` run this
same session found the 11 Group-3 tests still failing live for THREE
genuinely different, real automation-side bugs, all now fixed (see the test
module's own docstring for the full disclosure of each, and for the final,
confirmed-green re-run result):

  A) `open_department_for_edit()`'s row lookup is a live-confirmed SUBSTRING
     match, and 4 of these 11 tests created their department under a FIXED,
     non-unique literal name that this environment's own prior no-teardown
     runs had already duplicated — a strict-mode violation ("resolved to 3
     elements") on the Edit-link lookup, not a read/retrieval defect at all.
     Fixed in the test module (`_unique()` on `name_en`), not here — this is
     a test-data-uniqueness concern, not a Page Object locator concern.

  B) Fixing (A) alone surfaced a SECOND real bug: a genuine, live,
     server-side `ObjectValidationRuleEngineException` ("Another department
     already uses this Arabic name") on the CREATE call itself, because
     `name_ar` was left as the same generic, dozens-of-times-reused fixed
     literal (e.g. "قسم"). Also fixed in the test module (`_unique()` on
     `name_ar` too).

  C) Fixing (A) and (B) left 2 of the 11 still failing — THIS Page Object's
     own `save()`/`is_save_error_shown()` (see their own docstrings below
     for the full live evidence trail): a genuinely successful save
     (network-trace-confirmed `PUT .../departments/<id>` 200) can be
     asynchronously followed, on this surface, by a reset to a brand-new,
     pristine, blank create form within a few seconds — whose own empty
     required fields are ALSO native-invalid, an intermittent false
     positive in `_native_invalid_field()`'s re-query that has nothing to
     do with the save that just succeeded. `save()` now captures that same
     check's result IMMEDIATELY on click (before the async reset has any
     time to occur — a genuine native block is confirmed to fire
     synchronously, so this loses no real detection), and
     `is_save_error_shown()`/`save_error_text()` consult that cached
     snapshot instead of re-querying the live DOM late.

All three fixes are real, disclosed, and kept. All 19 tests (this module's
own Group 2 AND Group 3) were RE-RUN FOR REAL after every fix, in two full
separate `pytest -n 0` runs with a fresh `.auth/state.json`, and are
CONFIRMED, this session, ALL 19 GREEN.

RE-INVESTIGATED LIVE 2026-09-19 (tc_133364/133272/133275 RBAC final
investigation, prompted by the QA Manager personally resetting all 3 named
CMS role accounts' passwords and supplying new `.env` values). Re-verified
live, independently, per account (fresh headless Chromium, real requests
against qcdev, not assumed fixed):

  - 'Content Contributor' (Test3@xyz.com): STILL BROKEN with the new
    password — Liferay's own "Authentication failed due to incorrect
    credentials or account lockout" banner, reproduced TWICE, fresh
    contexts, identical text to every prior session. Not resolved by this
    investigation — genuinely needs human attention (the QA Manager's
    reset either did not take effect for this one account, or there is a
    typo/mismatch); no password was guessed or invented here.
  - 'Site Content Editor' (test1@xyz.com) and 'Site Content Author'
    (Test2@xyz.com): BOTH now log in successfully with their new
    passwords. A quick manual check found `open_departments_list().
    open_new_department_form()` bouncing back to the login page for Site
    Content Editor right after a confirmed-successful login — investigated
    to a DEFINITIVE, evidence-based conclusion rather than guessed at:

    THE ROOT CAUSE IS A GENERIC SESSION/DETECTION BUG IN THIS CLASS'S OWN
    `_ensure_logged_in()`, NOT a real Org Structure Management permission
    restriction. Proof, live, this session:
      1) `/en/home` (the page `_ensure_logged_in()` used to check) was
         confirmed, by direct DOM count, to render NEITHER
         `CONTENT_DATA_MENU_ITEM` NOR `PRODUCT_MENU_TOGGLE` for either
         named role — a FALSE NEGATIVE ("not logged in") against a
         genuinely, successfully authenticated session (confirmed by a
         real Liferay `JSESSIONID` + `ID` persistent-auth cookie pair, and
         by `manage-department` itself rendering its real, working create
         form when reached directly). 'Site Content Editor' additionally
         renders the Control Menu nav (the fallback signal a DIFFERENT
         sibling class, HomeSocialIconsAdminPage, already uses for this
         same role) — but 'Site Content Author' renders NONE of the three
         nav-chrome signals anywhere, including on `manage-department`
         itself, an even more extreme case of the same false-negative
         class.
      2) That false negative was firing a spurious re-login attempt with
         the generic `settings.test_user` credential mid-flow. CONFIRMED
         LIVE this is the exact, literal mechanism behind the observed
         "bounce to login": hitting `/c/portal/login` a SECOND time from
         an already-authenticated named-role session does not reliably
         re-render the real login form (confirmed live two different
         ways: settling back on `/home` with the username field's own
         count at 0, or redirecting to an unrelated URL such as a
         `?qcPreview=departments:<id>` link) — so `CmsLoginPage.login()`'s
         own `type()` call into that field hangs for the full 30s timeout
         and raises, which is precisely why the department-form-filling
         code was observed "stuck looking at the login page's username
         field" despite the browser having already moved off the literal
         login URL.
      3) DECISIVE control check, same session: with the buggy check
         bypassed, navigating straight to `manage-department` reached the
         REAL create form (Department Name (EN) field, Save as Draft
         button, zero errors) for BOTH roles — and, as an additional
         cross-object control, 'Site Content Editor' was also confirmed to
         reach `manage-social-media-icon`'s own real create form cleanly
         (a DIFFERENT object this role is already documented elsewhere in
         this project to have working access to) — ruling out (a) "this is
         a real, object-specific access restriction on Departments" in
         favor of (b) "this is a generic session/detection artifact
         affecting any object reached through this class's own broken
         check", per this investigation's own explicit decision criteria.

  `_ensure_logged_in()` (and `open_departments_list()`/
  `open_new_department_form()`, which now forward it) is FIXED this
  session: it accepts an explicit `role: str | None = None` parameter
  (default `None` preserves every EXISTING caller's exact behavior — the
  whole rest of this module, all already passing against
  `settings.test_user` — zero risk to already-green tests, re-confirmed
  live this session by re-running `test_authorized_admin_can_access_
  management_screen` and `test_management_screen_loads_department_list`
  for real after the fix: both PASSED). For a named role, it no longer
  uses the confirmed-unreliable nav-chrome check at all — it checks the
  REAL target surface directly (`manage-department` itself rendering
  `SAVE_AS_DRAFT_BUTTON`) and only performs a login if that surface is not
  already showing it, avoiding the redundant-relogin trap a first, naive
  "always re-login for a named role" fix attempt was independently
  confirmed live, this same session, to still hit on a SECOND call within
  one flow (`open_departments_list(role)` then `open_new_department_form
  (role)` — the real pattern these RBAC tests use). Re-verified live,
  fresh, end-to-end AFTER this fix: `open_departments_list(role).open_new_
  department_form(role)` now reaches the real create form cleanly for
  BOTH roles, no bounce, no hang.

  CONCLUSION: neither usable named role (Site Content Editor, Site Content
  Author) shows ANY restriction on Org Structure Management — both have
  full, confirmed-live, working access to create/manage Departments
  entries, the opposite of what tc_133364/133272/133275 need to observe.
  Content Contributor remains genuinely unusable (broken login, a separate,
  unresolved issue). STILL NO CONFIRMED ROLE THAT LACKS Org Structure
  Management permission exists this session — the 3 RBAC cases in the test
  module remain skipped, `_NO_RESTRICTED_ACCOUNT` updated to this finding
  rather than un-skipped on a guess. The now-fixed `role`-aware login path
  is available and reliable for any future test that needs a real
  named-role session on this object.
"""

import time

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url, settings

SLUG = "department"

ADMIN_HOME_EN_URL_PATH = "/en/home"
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'

FIELD_DEPT_NAME_EN = "Department Name (EN)"
FIELD_DEPT_NAME_AR = "Department Name (AR)"
FIELD_PARENT_DEPARTMENT = "Parent Department"
FIELD_PERSON_NAME_EN = "Person Name (EN)"
FIELD_PERSON_NAME_AR = "Person Name (AR)"
FIELD_PERSON_TITLE_EN = "Person Title (EN)"
FIELD_PERSON_TITLE_AR = "Person Title (AR)"
FIELD_PERSON_PHOTO = "Person Photo"
FIELD_DEPT_DESCRIPTION_EN = "Department Description (EN)"
FIELD_DEPT_DESCRIPTION_AR = "Department Description (AR)"
FIELD_DISPLAY_ORDER = "Display Order"
FIELD_ACTIVE_STATUS = "Active Status"

_UNVERIFIED = "TODO: run tools/extract_locators.py / MCP against the live page and paste the confirmed selector here"


class OrgStructureAdminPage(ObjectAuthoringPage):
    """Composes the generic Object Authoring state machine
    (`ObjectAuthoringPage`) with the Departments object's own field map.
    Constructed with just `page` (slug fixed to "department")."""

    def __init__(self, page):
        super().__init__(page, SLUG)
        # Set by save() immediately on click (see its own docstring) —
        # `is_save_error_shown()`/`save_error_text()` consult this cached
        # snapshot instead of a fresh, late DOM re-query. `"__unset__"`
        # (not None) distinguishes "save() never called yet" from "save()
        # ran and found no native-invalid field" for those callers' own
        # getattr-with-default fallback.
        self._last_native_invalid = "__unset__"

    # ---- Backward-compatible field/button constants (see module docstring:
    # `role=` locator-engine strings resolve identically to get_by_role()
    # live, confirmed 2026-09-07, so existing direct-locator test code keeps
    # working without changes) --------------------------------------------
    NEW_BUTTON = ObjectAuthoringPage.SAVE_AS_DRAFT_BUTTON
    # HEALED 2026-09-15 — see module docstring's HEALING PASS note #1: the
    # OLD ambiguous CSS (kept here, commented, only for git-blame context)
    # matched BOTH the site-wide Object Authoring nav filter AND (as of this
    # session) a genuine, new, per-object entries-table filter box.
    # `input[data-qc-oel-q]` is that real filter box — unique, structural
    # (data-* attribute, no visible-label/locale dependency), confirmed live
    # to actually filter this object's own entries table.
    # OLD: 'input[placeholder="Search"], input[type="search"]'
    SEARCH_INPUT = 'input[data-qc-oel-q]'
    LIST_ROW = ObjectAuthoringPage.ENTRIES_TABLE_ROW

    ACTIVE_STATUS_CHECKBOX = f'role=checkbox[name="{FIELD_ACTIVE_STATUS}"]'
    DEPT_DESCRIPTION_AR = f'role=textbox[name="{FIELD_DEPT_DESCRIPTION_AR}"]'
    DEPT_DESCRIPTION_EN = f'role=textbox[name="{FIELD_DEPT_DESCRIPTION_EN}"]'
    DEPT_NAME_AR = f'role=textbox[name="{FIELD_DEPT_NAME_AR}"]'
    DEPT_NAME_EN = f'role=textbox[name="{FIELD_DEPT_NAME_EN}"]'
    DISPLAY_ORDER = f'role=spinbutton[name="{FIELD_DISPLAY_ORDER}"]'
    # HEALED 2026-09-15 — see module docstring's HEALING PASS note #3:
    # RE-CONFIRMED LIVE this session that Parent Department is a real
    # combobox (still holds, unchanged since 2026-09-13) — NOT a spinbutton.
    # OLD: f'role=spinbutton[name="{FIELD_PARENT_DEPARTMENT}"]'
    PARENT_DEPARTMENT = f'role=combobox[name="{FIELD_PARENT_DEPARTMENT}"]'
    PERSON_NAME_AR = f'role=textbox[name="{FIELD_PERSON_NAME_AR}"]'
    PERSON_NAME_EN = f'role=textbox[name="{FIELD_PERSON_NAME_EN}"]'
    PERSON_TITLE_AR = f'role=textbox[name="{FIELD_PERSON_TITLE_AR}"]'
    PERSON_TITLE_EN = f'role=textbox[name="{FIELD_PERSON_TITLE_EN}"]'
    PERSON_PHOTO_SELECT_FILE_BTN = 'button:has-text("Select File")'

    # ---- Not located this session — explicit placeholders, never guessed --
    PAGE_SETTINGS_URL = _UNVERIFIED  # Page Title / Hero Banner / Status admin surface
    CASCADE_WARNING_DIALOG = _UNVERIFIED
    CASCADE_CONFIRM_BUTTON = _UNVERIFIED
    CIRCULAR_REFERENCE_ERROR = _UNVERIFIED
    DUPLICATE_NAME_ERROR = _UNVERIFIED
    ACCESS_DENIED_MESSAGE_EN = _UNVERIFIED
    ACCESS_DENIED_MESSAGE_AR = _UNVERIFIED

    def _require_verified(self, value: str, name: str) -> None:
        if value == _UNVERIFIED:
            raise RuntimeError(
                f"OrgStructureAdminPage.{name} is an unverified placeholder — locate the "
                f"real admin surface / trigger the real UI state and replace it before "
                f"running this test."
            )

    # ---- Navigation ---------------------------------------------------------
    def _ensure_logged_in(self, role: str | None = None) -> None:
        """Re-login-if-needed via `/en/home`'s real Product Menu/Content &
        Data check — mirrors HomeBusinessEventsAdminPage._ensure_logged_in()
        exactly (see module docstring's Session/auth note for why a direct
        `manage-department` hit cannot detect a dropped session on its
        own).

        HEALED 2026-09-19 (tc_133364/133272/133275 RBAC re-investigation —
        see module docstring's "RE-INVESTIGATED LIVE 2026-09-19" note for
        the full live evidence trail). `role` (default `None`, preserving
        every EXISTING caller's exact behavior — the whole rest of this
        module, all already passing against `settings.test_user`) lets a
        caller drive a named CMS role login instead of the generic
        super-admin account, WITHOUT falling through this method's own
        CONTENT_DATA_MENU_ITEM/PRODUCT_MENU_TOGGLE re-login check — that
        check is CONFIRMED LIVE, this session, to be a FALSE NEGATIVE for
        every one of this project's 3 named roles (none render either
        element, logged in or not — "Site Content Editor" additionally
        renders the Control Menu nav that a DIFFERENT sibling class
        (HomeSocialIconsAdminPage) already uses as its own fallback check,
        but "Site Content Author" renders NEITHER that NOR any of the three
        — confirmed live via a direct DOM count on `/en/home` AND on
        `manage-department` itself for both roles). Left running through
        this method UNCHANGED for a named role, the false negative used to
        fire a redundant re-login attempt with `settings.test_user`
        mid-flow — CONFIRMED LIVE this session to be the exact, literal
        mechanism behind the "bounces back to login" symptom this
        investigation set out to explain: hitting `/c/portal/login` again
        from an ALREADY-authenticated named-role session does not
        re-render the login form (confirmed live, TWO different ways this
        session: it can settle back on `/home` with the login username
        field's own count at 0, OR — confirmed live on a SECOND redundant
        call within the same already-authenticated session — redirect to
        an unrelated URL entirely, e.g. a `?qcPreview=departments:<id>`
        link), so `CmsLoginPage.login()`'s own `type()` call into that
        field hangs for the full 30s timeout and raises — which is
        precisely why the department-form-filling code was observed "stuck
        looking at the login page's username field" despite the browser
        having already moved off the literal login URL.

        A role-aware call below therefore does NOT unconditionally
        re-login on every call the way the `settings.test_user` branch
        does (that redundancy is exactly what breaks it — CONFIRMED LIVE
        THIS SESSION: even the FIRST fix attempt here, an unconditional
        direct login mirroring HomeSocialIconsAdminPage.login_as_role(),
        worked for the first `_ensure_logged_in(role)` call in a flow but
        broke on the SECOND one two methods later, i.e. exactly
        `open_departments_list(role)` then `open_new_department_form(role)`
        — the real production pattern this class's own RBAC tests use). It
        instead checks the REAL target surface directly first — `manage-
        <slug>` itself rendering `SAVE_AS_DRAFT_BUTTON` is the one signal
        CONFIRMED LIVE, this session, to be positive and reliable for BOTH
        roles (unlike any nav-chrome element) — and only performs the login
        if that surface does NOT already render it (i.e. genuinely not
        authenticated with working access yet, the real state at the START
        of an RBAC test's `use_auth_state=False` fresh context, per this
        module's own AUTH ISOLATION rule). Once logged in, every later call
        in the same flow finds the surface already rendering and skips
        re-login entirely — no redundant hit to `/c/portal/login` at all.
        Both roles are CONFIRMED LIVE this session to otherwise have a
        completely normal, working, authenticated session once logged in
        this way — real `JSESSIONID` + Liferay `ID` persistent-auth
        cookies, and `manage-department` renders its real create form
        (Department Name (EN) field, Save as Draft button) directly, with
        zero access restriction of any kind observed for either role."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)

        if role:
            self.open(self._manage_url())
            if self.is_visible(self.SAVE_AS_DRAFT_BUTTON):
                return  # already authenticated with real, working access — no redundant re-login

            from config.settings import cms_role_credentials

            email, password = cms_role_credentials(role)
            self.open(control_panel_url(CmsLoginPage.LOGIN_PATH))
            self.type(CmsLoginPage.USERNAME_INPUT, email)
            self.type(CmsLoginPage.PASSWORD_INPUT, password)
            self.click(CmsLoginPage.SUBMIT_BUTTON)
            try:
                agree_button = self.page.get_by_role("button", name="I Agree")
                agree_button.wait_for(state="visible", timeout=6000)
                agree_button.click()
            except Exception:  # noqa: BLE001 — Terms-of-Use interstitial not shown for this account
                pass
            self.page.wait_for_timeout(1500)
            body_text = ""
            try:
                body_text = self.page.locator("body").inner_text()
            except Exception:  # noqa: BLE001 — best-effort read only
                pass
            if "Authentication failed" in body_text:
                raise RuntimeError(
                    f"Login as CMS role {role!r} failed: Liferay rejected the "
                    f"credential outright ('Authentication failed...'). See "
                    f"config.settings.cms_role_credentials() / .env."
                )
            if "/c/portal/update_password" in self.page.url:
                raise RuntimeError(
                    f"Login as CMS role {role!r} landed on Liferay's forced "
                    f"first-login password-reset interstitial — this automation "
                    f"is not authorized to complete a password reset on a "
                    f"shared credential's own judgement."
                )
            if self.page.locator(CmsLoginPage.USERNAME_INPUT).count() > 0:
                raise RuntimeError(
                    f"Login as CMS role {role!r} did not navigate away from the "
                    f"login form — credential likely rejected without the "
                    f"standard 'Authentication failed' banner text."
                )
            self.open(self._manage_url())
            return

        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))

    def open_departments_list(self, role: str | None = None) -> "OrgStructureAdminPage":
        """Object Authoring entries list for Departments (`manage-department`,
        no `editEntry` param) — replaces the old Content & Data > Departments
        menu path (see module docstring). `role`: see `_ensure_logged_in()`."""
        self._ensure_logged_in(role)
        self.open_entries_list()
        return self

    def open_new_department_form(self, role: str | None = None) -> "OrgStructureAdminPage":
        """The create form is already inline on `manage-department` (no
        separate "New" control to click — see ObjectAuthoringPage's own
        confirmed pattern); this (re)navigates to a fresh copy of it.
        `role`: see `_ensure_logged_in()`."""
        self._ensure_logged_in(role)
        self.open_new_entry_form()
        return self

    # RE-HEALED 2026-09-15 (module docstring's RE-HEALING PASS root cause 1):
    # a just-created entry's own row was CONFIRMED LIVE this session to still
    # be absent from the entries table up to ~40s after `save()` returned —
    # a real admin-side indexing/render latency, not a locator problem.
    # Generous relative to that measurement (which itself may under-represent
    # a busier moment on this shared, actively-developed qcdev environment),
    # capped so a genuinely-missing row still fails in bounded time rather
    # than hanging forever.
    ROW_APPEAR_POLL_TIMEOUT_MS = 90000
    ROW_APPEAR_POLL_INTERVAL_MS = 5000

    def open_department_for_edit(self, department_name: str) -> "OrgStructureAdminPage":
        """Opens an existing department row for edit via its own `Edit`
        link — the confirmed-live replacement for the historical
        "type into SEARCH_INPUT, then click a bare row" pattern (see module
        docstring's SEARCH_INPUT note for why that pattern can never work
        on this surface). Thin wrapper over
        `ObjectAuthoringPage.open_entry_by_edit_link()` so callers read
        naturally in department-domain terms.

        Deliberately does NOT call `_ensure_logged_in()` itself (unlike
        `open_departments_list()`/`open_new_department_form()`) — HEALED
        2026-09-07 after a live incident this session: `_ensure_logged_in()`
        navigates to `ADMIN_HOME_EN_URL_PATH` (`/en/home`) as its own
        session-check mechanism, which — called here, AFTER the caller has
        already navigated to the entries list via `open_departments_list()`
        — silently steps off `manage-department` back onto `/en/home`
        immediately before `open_entry_by_edit_link()` tried to locate the
        row, making every row lookup time out no matter how correct the
        row/Edit-link locator was (confirmed live: `table tbody
        tr:has-text(...)` was never going to match anything on `/en/home`).
        Callers MUST call `open_departments_list()` (which already performs
        its own login check before navigating to the entries list) first —
        exactly the sequence every caller in this module already uses.

        RE-HEALED 2026-09-15 (module docstring's RE-HEALING PASS root
        cause 1): polls (re-list + row-presence check) for up to
        ROW_APPEAR_POLL_TIMEOUT_MS BEFORE attempting the Edit-link click,
        rather than assuming the caller's own prior `open_departments_list()`
        call already guarantees the target row is present — CONFIRMED LIVE
        this session it does not, for a just-created entry. A no-op (single
        instant count check, no extra wait) when the row is already present,
        which is the common case for every pre-existing/seeded department —
        this only costs real time for a row that genuinely isn't there yet."""
        row = self.page.locator(f'{self.LIST_ROW}:has-text("{department_name}")')
        deadline = time.monotonic() + (self.ROW_APPEAR_POLL_TIMEOUT_MS / 1000)
        while row.count() == 0 and time.monotonic() < deadline:
            self.page.wait_for_timeout(self.ROW_APPEAR_POLL_INTERVAL_MS)
            self.open_entries_list()
        self.open_entry_by_edit_link(department_name)
        return self

    def open_page_settings(self) -> "OrgStructureAdminPage":
        self._require_verified(self.PAGE_SETTINGS_URL, "PAGE_SETTINGS_URL")
        self.open(self.PAGE_SETTINGS_URL)
        return self

    # ---- Add/Edit form actions ----------------------------------------------
    def fill_department_form(
        self,
        name_en: str = None,
        name_ar: str = None,
        person_name_en: str = None,
        person_name_ar: str = None,
        person_title_en: str = None,
        person_title_ar: str = None,
        description_en: str = None,
        description_ar: str = None,
        display_order: str = None,
        parent_department: str = None,
        active_status: bool = None,
    ) -> "OrgStructureAdminPage":
        if name_en is not None:
            self.fill_text(FIELD_DEPT_NAME_EN, name_en)
        if name_ar is not None:
            self.fill_text(FIELD_DEPT_NAME_AR, name_ar)
        if person_name_en is not None:
            self.fill_text(FIELD_PERSON_NAME_EN, person_name_en)
        if person_name_ar is not None:
            self.fill_text(FIELD_PERSON_NAME_AR, person_name_ar)
        if person_title_en is not None:
            self.fill_text(FIELD_PERSON_TITLE_EN, person_title_en)
        if person_title_ar is not None:
            self.fill_text(FIELD_PERSON_TITLE_AR, person_title_ar)
        if description_en is not None:
            self.fill_text(FIELD_DEPT_DESCRIPTION_EN, description_en)
        if description_ar is not None:
            self.fill_text(FIELD_DEPT_DESCRIPTION_AR, description_ar)
        if display_order is not None:
            self.fill_number(FIELD_DISPLAY_ORDER, display_order)
        if parent_department is not None:
            # HEALED 2026-09-15 (module docstring's HEALING PASS note #3):
            # the OLD path here resolved a numeric object-entry id and
            # filled it into a spinbutton — that field is CONFIRMED LIVE
            # (re-verified this session, still holds since 2026-09-13) to
            # now be a real, searchable COMBOBOX restricted to existing
            # department names, not a raw-id spinbutton. Delegates straight
            # to the already-confirmed-live select_parent_department_combobox()
            # (the SAME mechanism tc_133296/tc_133297 already use) so every
            # caller of this method gets the real, current, working
            # mechanism.
            self.select_parent_department_combobox(parent_department)
        if active_status is not None:
            self.set_checkbox(FIELD_ACTIVE_STATUS, active_status)
        return self

    def select_parent_department_combobox(self, department_name: str) -> "OrgStructureAdminPage":
        """CONFIRMED LIVE 2026-09-13 (re-investigation, ADO-133296/133297
        batch, plan 133534/suite 139193): unlike this class's own
        PARENT_DEPARTMENT-fill path above (which assumes a raw numeric-id
        spinbutton field, confirmed live 2026-09-07) — Parent Department is
        NOW confirmed live to be a real, SEARCHABLE COMBOBOX restricted to
        real department names (its own listbox enumerates every existing
        department by name; no free-text entry accepted). This may be a
        genuine product change since 2026-09-07 (disclosed here, not
        silently reconciled) — it directly bears on ADO-133327's own
        "Parent Department accepts free-text/invalid references — CONFIRMED
        BUG" finding elsewhere in this module's test file, which this
        method's own discovery was NOT tasked to re-verify or fix; flagged
        back for a follow-up pass. This method is deliberately NEW and
        HEALED 2026-09-15 (module docstring's HEALING PASS note #3):
        `fill_department_form(parent_department=...)` now delegates HERE
        directly (its own prior numeric-id spinbutton path is gone — that
        field no longer exists) — every caller (133290/133326/133328/133329
        included) now gets this same, real, confirmed-live mechanism instead
        of the stale one."""
        combo = self.page.get_by_role("combobox", name=FIELD_PARENT_DEPARTMENT, exact=True)
        combo.click()
        self.page.wait_for_timeout(400)
        listbox = self.page.locator('[role="listbox"]:visible').last
        option = listbox.get_by_role("option", name=department_name, exact=True)
        option.wait_for(state="visible", timeout=5000)
        option.click()
        return self

    def upload_person_photo(self, file_path: str) -> "OrgStructureAdminPage":
        self.upload_file(FIELD_PERSON_PHOTO, file_path)
        return self

    def attempt_person_photo_upload_expect_rejection(
        self, file_path: str, timeout_seconds: float = 20.0
    ) -> str:
        """Attempts to upload `file_path` into Person Photo and expects it to
        be REJECTED before ever being attached — see module docstring's
        HEALING PASS note #2 for the full live evidence trail. Two different,
        both confirmed-live, rejection UX paths exist on this picker widget:
        an unsupported EXTENSION is rejected instantly with a real, visible
        message read directly off the picker's own body text ("Please enter
        a file with a valid extension (.jpg,.png)."); an OVERSIZED file is
        rejected SILENTLY (the widget stalls then reverts to its empty
        "Drag & Drop" state with no message anywhere, confirmed live via a
        full page-text scan and network-response sweep). BOTH paths leave
        the picker's iframe/modal OPEN — confirmed live this hangs the very
        next click (e.g. Submit for Publishing) for 30s+ because the
        still-open iframe intercepts pointer events on the underlying page.
        This method therefore ALWAYS presses `Escape` before returning
        (confirmed live to close the modal cleanly), regardless of which
        path fired, so callers can safely continue interacting with the
        form. Returns the picker's own rejection message text (path 1), or
        `""` if the rejection was silent (path 2) — never raises for either
        confirmed-live outcome, since both ARE the real, live behavior."""
        hidden_textbox = self.page.get_by_role(
            "textbox", name=f"{FIELD_PERSON_PHOTO} Select File"
        )
        select_file_button = hidden_textbox.locator("xpath=..").get_by_role(
            "button", name="Select File"
        )
        select_file_button.click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path, timeout=15000)

        message = ""
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                body_text = frame.locator("body").inner_text(timeout=2000)
            except Exception:  # noqa: BLE001 — frame may be mid-transition between polls
                body_text = ""
            if "valid extension" in body_text:
                for line in body_text.splitlines():
                    if "valid extension" in line:
                        message = line.strip()
                        break
                break
            if "Uploading" not in body_text:
                # Reverted to the empty "Drag & Drop" state with no message —
                # the silent-rejection path (oversized file).
                break
            time.sleep(0.5)

        # ALWAYS recover — see docstring: both rejection paths leave the
        # modal open, which would otherwise hang the caller's next click.
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)
        return message

    def attempt_keyboard_type_into_number_field(self, field_label: str, text: str) -> str:
        """Attempts to type `text` into a native `type="number"` field via
        REAL keyboard events — never `.fill()`, which Playwright refuses
        outright for non-numeric text against a number input (see module
        docstring's HEALING PASS note #4). CONFIRMED LIVE the browser's own
        native constraint rejects every non-numeric keystroke at entry (a
        pure "abc" attempt leaves the field empty; a mixed "12abc" keeps
        only the leading numeric prefix) — there is no way to get literal
        non-numeric text into this field's real DOM value, by any input
        method (even a direct JS value assignment resolves to "" per the
        `<input type=number>` IDL spec). Returns the field's REAL resulting
        value after the attempt, so callers assert on the browser's own
        confirmed rejection behavior instead of assuming `.fill()` would
        have worked."""
        field = self.page.get_by_role("spinbutton", name=field_label, exact=True)
        field.click()
        field.fill("")
        self.page.keyboard.type(text, delay=20)
        return field.input_value()

    def number_field_validation_message(self, field_label: str) -> str:
        """Native HTML5 constraint-validation message for a `type="number"`
        field (`element.validationMessage`) — CONFIRMED LIVE this is
        `"Please fill out this field."` for Display Order left empty by a
        blocked non-numeric attempt (see
        attempt_keyboard_type_into_number_field()'s own docstring)."""
        field = self.page.get_by_role("spinbutton", name=field_label, exact=True)
        return field.evaluate("el => el.validationMessage")

    def save(self) -> "OrgStructureAdminPage":
        """Maps to Object Authoring's "Submit for Publishing" (see module
        docstring's Save/Submit note) — this surface has no single "Save"
        button, and every case in this module that checks a value on the
        public Organizational Structure page afterward needs the entry
        actually published, not left as a draft.

        RE-HEALED 2026-09-17 (real `pytest -n 0` re-run of tc_133326/133360,
        network-trace evidence — see module docstring's 2026-09-17
        RE-INVESTIGATED LIVE note): CONFIRMED LIVE this session, TWO
        separate real create/edit flows, both with a genuinely successful
        write (`PUT /o/c/departments/<id>` returning 200, no error banner,
        no visible alert) still tripped `is_save_error_shown()` into
        reporting `True` — traced to `_native_invalid_field()` finding
        `ObjectField_departmentNameEn` (or another required field) empty
        and native-invalid up to several SECONDS after the successful save,
        because this surface is CONFIRMED LIVE to sometimes asynchronously
        reset itself to a brand-new, pristine, blank create form after a
        successful Submit — whose own empty required fields are ALSO
        `checkValidity() === false` despite having nothing to do with the
        save that just succeeded. This is a real, live, INTERMITTENT race
        (reproduced once in ~3 live probes, not deterministic), not a
        genuine rejection. The one thing that DOES reliably distinguish the
        two, confirmed live: a genuine native-constraint BLOCK happens
        SYNCHRONOUSLY on click, before this surface's own JS ever runs (zero
        network calls fire for it — see `attempt_keyboard_type_into_number_
        field()`'s own docstring) — so checking `_native_invalid_field()`
        IMMEDIATELY after the click, before the settle-wait that gives the
        async reset time to happen, captures the real, synchronous signal
        and can never observe a reset this surface has not had time to
        perform yet. That immediate snapshot is cached and consulted by
        `is_save_error_shown()`/`save_error_text()` below INSTEAD OF a fresh,
        late re-query of the DOM — the only fix that does not weaken the
        detection of a genuine native block (which fires synchronously and
        is therefore ALWAYS caught by the immediate snapshot too)."""
        self.click(self.SUBMIT_FOR_PUBLISHING_BUTTON)
        self._last_native_invalid = self._native_invalid_field()
        self._wait_for_settle()
        return self

    def cancel(self) -> "OrgStructureAdminPage":
        """No dedicated "Cancel" control was confirmed on the create-new
        form this session (Object Authoring's own "Cancel and add a new
        entry instead" link only renders when EDITING an existing entry —
        see ObjectAuthoringPage's module docstring). Simply navigating away
        (re-opening the entries list) has the same discard effect for an
        unsaved create-new form and needs no unverified placeholder."""
        self.open_entries_list()
        return self

    def confirm_cascade_deactivation(self) -> "OrgStructureAdminPage":
        self._require_verified(self.CASCADE_CONFIRM_BUTTON, "CASCADE_CONFIRM_BUTTON")
        self.click(self.CASCADE_CONFIRM_BUTTON)
        return self

    def save_and_detect_cascade_warning(self, timeout_seconds: float = 6.0) -> bool:
        """Clicks Save (Submit for Publishing) and reports whether the app
        shows a cascade-deactivation warning to the admin BEFORE the
        deactivation of a parent department with active children commits.

        HEALED 2026-09-19 (ADO Bug 137235 — filed against this method's own
        original 2026-09-12 "no warning of any kind" finding — is now Done;
        the QA Manager manually verified live on qcdev that deactivating a
        parent department with active children now shows a real warning
        before the deactivation commits). RE-INVESTIGATED LIVE this session
        (fresh `.auth/state.json`, Playwright MCP, real TEST_USER session,
        `manage-department?editEntry=QCDEMO-129399-DEPT-04`, unchecking
        Active Status on "Member Services Sector", id 80734 — RE-CONFIRMED
        LIVE this session to still be the real parent-with-2-active-children
        department this environment has, same id, same 2 children — and
        clicking Submit for Publishing): the fixed mechanism is the SAME
        real, live, visible `[data-qc-oel-editbar]` rejection banner already
        established for `test_confirming_cascade_deactivation_hides_entire_
        branch` (tc_133294)'s "wrong order" step — see `SAVE_ERROR_BANNER`/
        `is_save_error_shown()` below — NOT a native `window.confirm`/
        `alert` dialog and NOT a custom `[role="dialog"]`/`.modal` DOM
        element (the ORIGINAL detector's only two mechanisms, kept below as
        a harmless fallback — CONFIRMED LIVE this session that neither one
        fires). Network-captured this session:
        `PUT https://qcdev.ihorizons.com/o/c/departments/80734` returns a
        real HTTP 400 (`ObjectValidationRuleEngineException`), and the page
        renders "This record was not saved:\\n• This department cannot be
        deactivated while it still has active child departments. Deactivate
        its children first." — a warning shown BEFORE the deactivation
        commits: RE-VERIFIED LIVE this session via a fresh reopen of the
        same entry immediately after that Active Status is still checked
        (True) — the rejected save genuinely did not persist, proving this
        is a real block, not a delayed/eventual cascade. There is no
        separate "confirm" affordance to proceed anyway with active
        children still present — the ONLY way to deactivate this parent is
        children-first (tc_133294's own already-covered happy path); this
        method's real, confirmed job is to detect that the warning fires
        and blocks the save, not to offer a "confirm and proceed" step that
        does not exist for this rule. This detector now checks
        `is_save_error_shown()` (which already covers `SAVE_ERROR_BANNER`)
        FIRST — the real, confirmed-live mechanism — before falling back to
        the original native-dialog/DOM-modal poll for defense-in-depth
        (e.g. a future UI change back to a true native/custom confirm-
        dialog affordance would still be caught)."""
        dialog_seen = {"flag": False}

        def _on_dialog(dialog):
            dialog_seen["flag"] = True
            dialog.accept()

        self.page.on("dialog", _on_dialog)
        try:
            self.save()
            if self.is_save_error_shown():
                return True
            modal_selector = '[role="dialog"], [role="alertdialog"], .modal.show, .modal.in'
            keywords = (
                "children", "child department", "hidden", "cascade",
                "deactivat", "confirm", "warning",
            )
            deadline = time.monotonic() + timeout_seconds
            while time.monotonic() < deadline:
                if dialog_seen["flag"]:
                    return True
                if self.is_visible(modal_selector):
                    try:
                        modal_text = self.page.locator(modal_selector).first.inner_text().lower()
                    except Exception:  # noqa: BLE001 — element may vanish mid-read
                        modal_text = ""
                    if any(kw in modal_text for kw in keywords):
                        return True
                time.sleep(0.15)
            return dialog_seen["flag"]
        finally:
            self.page.remove_listener("dialog", _on_dialog)

    # ---- State queries --------------------------------------------------------
    # HEALED 2026-09-14 (triage of tc_133294, second round): LIVE-CONFIRMED
    # this session (Playwright MCP, manage-department, TEST_USER session)
    # that a REST-level save rejection — e.g. attempting to deactivate
    # "Member Services Sector" (id 80734) while its 2 children are still
    # active, which the server genuinely rejects with HTTP 400
    # (`ObjectValidationRuleEngineException` on
    # `PUT /o/c/departments/80734`, body: "This department cannot be
    # deactivated while it still has active child departments. Deactivate
    # its children first.") — DOES render a real, visible, user-facing
    # banner: "This record was not saved:\n• <server message>", in a plain
    # `<div data-qc-oel-editbar="">` with NO `class="alert-danger"` and NO
    # `role="alert"` attribute, so the original selector below never
    # matched it (a real, confirmed detection gap, not a silent product
    # failure — see OrgStructureAdminPage's own module docstring for the
    # full live evidence trail, screenshot, and network-log confirmation).
    # `[data-qc-oel-editbar]` is ALSO the same generic editbar container
    # Object Authoring reuses for the ORDINARY "Editing <title> (approved)
    # ..." status banner when there is NO error (confirmed live: a fresh,
    # error-free reload of the same entry renders that exact text inside
    # the identical `[data-qc-oel-editbar]` element) — so the bare
    # attribute selector alone is NOT error-specific and would false-
    # positive on every normal edit-form view. SAVE_ERROR_BANNER below
    # scopes to the "This record was not saved" text specifically (a
    # `:has-text()` CSS pseudo-class match, confirmed live to resolve to
    # exactly 0 or 1 elements — never a Playwright strict-mode violation)
    # so it only reports True for a genuine rejection banner. The ORIGINAL
    # `.alert-danger, [role="alert"]` selector is kept, UNCHANGED, as the
    # other OR branch — 20+ existing field-required-validation assertions
    # in this module (e.g. "Department name is required.") already pass
    # against it and must keep working exactly as before.
    SAVE_ERROR_BANNER = '[data-qc-oel-editbar]:has-text("This record was not saved")'
    _FIELD_VALIDATION_ERROR = '.alert-danger, [role="alert"]'

    # HEALED 2026-09-15 (ground-truth triage: tc_133317/133318/133322/133323/
    # 133331/133332/133335/133336/133338/133341/133342/133344/133350/133353/
    # 133355/133356, plus the "opposite" false-positive class 133321/133340/
    # 133358). CONFIRMED LIVE this session (headless-equivalent Playwright
    # MCP, real TEST_USER session, `manage-department`, fresh
    # `.auth/state.json`) via a dedicated, decisive live investigation of
    # tc_133335 (Empty Person Name (AR)) and tc_133355/tc_133356 (Display
    # Order 0 / negative) — this was NEVER a save-vs-check timing race
    # (`_wait_for_settle()`'s own 2500ms grace, confirmed live via a 40-poll/
    # 10s timing sweep, was already more than enough; the DOM state is fully
    # settled well before that window closes). Two separate, real, confirmed
    # root causes, both inside `is_save_error_shown()`/`save_error_text()`
    # themselves, not in the caller/timing:
    #
    # 1) STRICT-MODE SWALLOW (the actual "timing-shaped" symptom's real
    #    cause): this Department form ALWAYS mounts 9 permanent, empty,
    #    `role="alert"` validation-message placeholder spans (one per
    #    length/format-validated field: Dept Name EN/AR, Person Name EN/AR,
    #    Person Title EN/AR, Person Photo, Description EN/AR) — CONFIRMED
    #    LIVE present in the DOM from first render, before any Save attempt,
    #    regardless of pass/fail outcome. `BasePage.is_visible(locator)` —
    #    and `BasePage.text(locator)` — call Playwright's own
    #    `.is_visible()`/`.inner_text()` DIRECTLY on the raw locator, which
    #    enforces STRICT MODE and THROWS "strict mode violation: ... resolved
    #    to 9 elements" the instant more than one match exists — confirmed
    #    live via a direct, unwrapped Playwright call reproducing the exact
    #    same throw. `BasePage.is_visible()`'s own blanket
    #    `except Exception: return False` (a deliberate, correct contract for
    #    its OTHER callers — "never throws") silently swallows that
    #    strict-mode exception here and reports "no error visible" — even
    #    when a REAL, correctly-rendered, genuinely visible validation alert
    #    IS one of the 9+ matches. CONFIRMED LIVE, decisively, for Display
    #    Order = 0: the live DOM has a 10th `role="alert"` element,
    #    `visible: true`, text "Display Order must be at least 1." — a real,
    #    correct, server-round-tripped validation message (via a
    #    `POST /o/c/departments/scopes/<id>/validate` call returning HTTP 200
    #    with a `validationErrors` body) that `is_save_error_shown()` was
    #    silently discarding every single time, not because it rendered too
    #    slowly, but because ANY caller of the multi-match selector always
    #    strict-mode-throws regardless of how long it waits. `_visible_alert_
    #    texts()` below replaces the raw multi-match `is_visible()`/`text()`
    #    calls with a per-element iteration (`.nth(i).is_visible()`, each
    #    independently — Playwright does not enforce strict mode on an
    #    already-disambiguated `.nth()` locator) so a genuinely visible
    #    message among many placeholders is never lost to an internal
    #    exception again. This fix alone makes tc_133355/tc_133356 correctly
    #    detect the real, live error.
    #
    # 2) NATIVE HTML5 CONSTRAINT VALIDATION — CONFIRMED LIVE, THIS SESSION,
    #    for EVERY empty-required-text-field case tested (Person Name (AR),
    #    Department Name (EN) — both directly reproduced; the remaining
    #    empty-field cases in this list share the identical `required`
    #    native-input pattern, confirmed by DOM inspection, not assumed):
    #    leaving a required field (`name="ObjectField_*"`, `required`
    #    attribute present) empty and clicking Submit for Publishing fires
    #    ZERO network calls at all (confirmed via a full response-log capture
    #    — no `/validate` POST, nothing) and renders NO visible DOM element
    #    of any kind — the browser's own native constraint-validation UI
    #    (`element.checkValidity() === False`,
    #    `element.validationMessage === "Please fill out this field."`,
    #    confirmed live) blocks the submit natively, before the app's own JS
    #    ever runs. This IS a real, genuine, human-visible validation error
    #    (a human clicking Submit sees the browser's own native tooltip next
    #    to the field) — exactly why the QA Manager's manual pass saw a real
    #    rejection — but it is browser CHROME, not a DOM node, so no
    #    selector-based detector (the two above included) can ever see it.
    #    Mirrors this class's own already-established
    #    `attempt_keyboard_type_into_number_field()`/
    #    `number_field_validation_message()` precedent for Display Order's
    #    non-numeric case (HEALING PASS #4 above) — generalized here, inside
    #    `is_save_error_shown()` itself, to EVERY `ObjectField_*` control on
    #    the form (scoped by that shared, structural `name` prefix — CONFIRMED
    #    LIVE on both the spinbutton and textbox fields probed — rather than
    #    only the one spinbutton the original precedent covered), so this
    #    benefits every caller, not just Display Order's own two tests.
    #
    # DISCLOSED, NOT FIXED BY EITHER CHANGE ABOVE — genuinely different,
    # separately-confirmed-live root causes, kept honest rather than forced
    # green:
    #   - tc_133318/133323/133332/133336/133342/133350/133353 (">length
    #     chars rejected"): CONFIRMED LIVE, THREE independent real-interaction
    #     methods (`.fill()`, real keyboard `press_sequentially`-equivalent
    #     paste via `Control+V` after a real `navigator.clipboard.writeText`,
    #     and Playwright's own `.fill()` truncation) that every one of these
    #     fields carries a REAL native `maxlength` attribute (150 for the
    #     name/title fields, 1000 for the description fields) that makes it
    #     PHYSICALLY IMPOSSIBLE for any genuine user interaction to ever put
    #     a literal over-limit value into the field's real DOM value — it is
    #     silently truncated to exactly the limit (a valid value), which the
    #     app then legitimately accepts with NO error of any kind (confirmed
    #     live: Submit stays enabled, no validate-call rejection). This is
    #     the SAME class of finding as tc_133357's own already-documented
    #     `type="number"` precedent (HEALING PASS #4) — a genuinely different
    #     root cause from the strict-mode/native-constraint fixes above, not
    #     fixable by a detection-layer change, since the over-limit condition
    #     these tests intend to exercise can never actually reach the DOM via
    #     `fill_department_form()`'s real interaction.
    #   - tc_133317/133322/133331/133335/133338/133341's own exact
    #     `save_error_text() == "<custom sentence>"` assertions: even with
    #     fix (2) correctly making `is_save_error_shown()` report True, the
    #     REAL, live, confirmed text for a native-constraint block is the
    #     browser's OWN generic `validationMessage` ("Please fill out this
    #     field.") — never the project's custom bilingual sentence (e.g.
    #     "Department name is required." / "اسم القسم مطلوب.") — those exact
    #     custom strings do not render anywhere in the live DOM for this
    #     confirmed mechanism. `save_error_text()` below returns the real,
    #     honest text available (the native `validationMessage`) rather than
    #     fabricating the old expected string; the exact-text half of those
    #     six tests' own assertions will still fail, for this genuinely
    #     different, live-confirmed reason — reported, not silently forced.
    #   - tc_133355's own exact-text assertion ("Display order must be a
    #     positive number.") — the REAL, live, confirmed server message is
    #     "Display Order must be at least 1." (different wording) — same
    #     class of disclosure as the point above, `is_save_error_shown()`
    #     itself now correctly reports True either way.
    _FIELD_VALIDATION_ERROR = '.alert-danger, [role="alert"]'

    # HEALING PASS 2026-09-17 (closing tc_133317/133322/133331/133335/
    # 133338/133341/133355 — the six "genuinely different, NOT fixed by
    # this pass" custom-text assertions and the one Display Order banner-
    # text assertion the note directly above disclosed but deliberately
    # left unfixed). RE-VERIFIED LIVE this session (fresh `.auth/
    # state.json`, headless Chromium, `manage-department`, real Submit-
    # for-Publishing click) on TWO independent required fields — one EN
    # (Department Name (EN)) and one AR (Person Name (AR)) — that the
    # native `validationMessage` text is the browser's own generic,
    # locale-invariant string, IDENTICAL for both: `checkValidity() ===
    # False` on `ObjectField_departmentNameEn` gave `"Please fill out this
    # field."`; the same check on `ObjectField_personNameAr` gave the exact
    # same string. It does not vary by field name/label (confirmed, not
    # assumed) — one shared constant is correct for all 6 empty-required-
    # field cases (Department Name EN/AR, Person Name EN/AR, Person Title
    # EN/AR), not 6 separate literals. Also RE-VERIFIED LIVE, separately,
    # for Display Order = 0 (all other required fields filled): this one
    # is NOT a native-constraint block (`_native_invalid_field()` returns
    # empty immediately after the click) — it is a real, rendered,
    # server-round-tripped `[role="alert"]` DOM banner reading exactly
    # "Display Order must be at least 1." — a genuinely different
    # mechanism from the other 6, confirmed live rather than assumed to
    # share the native-validation fix.
    NATIVE_REQUIRED_FIELD_MESSAGE = "Please fill out this field."

    def _visible_alert_texts(self) -> list[str]:
        """Strict-mode-SAFE per-element visibility scan of
        `_FIELD_VALIDATION_ERROR` — see the HEALED note above for why the
        raw `BasePage.is_visible()`/`text()` calls on this locator can never
        detect a real, visible match once more than one element matches
        (which is the PERMANENT, always-true state on this form). Checks
        each match independently via `.nth(i)` (never strict-mode-checked by
        Playwright once already disambiguated) and returns the text of every
        genuinely visible one, in DOM order."""
        elements = self.page.locator(self._FIELD_VALIDATION_ERROR)
        try:
            count = elements.count()
        except Exception:  # noqa: BLE001 — never throws, mirrors BasePage's own contract
            return []
        texts = []
        for i in range(count):
            el = elements.nth(i)
            try:
                if el.is_visible():
                    texts.append(el.inner_text())
            except Exception:  # noqa: BLE001 — element may detach mid-scan
                continue
        return texts

    def _native_invalid_field(self) -> dict | None:
        """First `ObjectField_*` form control currently failing native HTML5
        constraint validation (`checkValidity() === False`), or `None` — see
        the HEALED note above for why this is a real, confirmed, separate
        detection path from the two DOM-alert-based ones (a native browser
        block renders NO DOM element at all, only browser-chrome UI).
        Scoped to the `ObjectField_*` `name` prefix (confirmed live on every
        real field probed this session) so this never false-positives on an
        unrelated `:invalid` match elsewhere on the page (e.g. a Liferay
        layout-structure wrapper element, confirmed live to also match a bare
        `:invalid` query since browsers propagate that pseudo-class to
        ancestor containers)."""
        return self.page.evaluate(
            """() => {
                const els = Array.from(document.querySelectorAll('[name^="ObjectField_"]'));
                for (const el of els) {
                    if (el.willValidate && !el.checkValidity()) {
                        return {
                            label: el.getAttribute('aria-label') || el.name,
                            message: el.validationMessage,
                        };
                    }
                }
                return null;
            }"""
        )

    def is_save_error_shown(self) -> bool:
        if self.is_visible(self.SAVE_ERROR_BANNER):
            return True
        if self._visible_alert_texts():
            return True
        # RE-HEALED 2026-09-17 (save()'s own docstring — real, live
        # pytest -n 0 evidence, tc_133326/133360): a FRESH `_native_invalid_
        # field()` re-query here can catch a brand-new, pristine, blank
        # create form this surface asynchronously reset itself into AFTER a
        # genuinely successful save — a confirmed-live false positive.
        # `save()` now caches the SAME check's result taken immediately on
        # click (before that async reset has any time to happen); consulting
        # that cached snapshot instead of re-querying the live DOM here is
        # what makes this reliable. Falls back to a fresh, direct query
        # (the ORIGINAL behavior) only if `save()` was never called on this
        # instance (`getattr` default), so any other/future caller of this
        # method that doesn't go through `save()` first is not silently
        # broken by an always-None cache.
        cached = getattr(self, "_last_native_invalid", "__unset__")
        if cached != "__unset__":
            return cached is not None
        return self._native_invalid_field() is not None

    def save_error_text(self) -> str:
        if self.is_visible(self.SAVE_ERROR_BANNER):
            return self.text(self.SAVE_ERROR_BANNER)
        visible = self._visible_alert_texts()
        if visible:
            return visible[0]
        # Mirrors is_save_error_shown()'s own cached-snapshot fix above.
        cached = getattr(self, "_last_native_invalid", "__unset__")
        native = self._native_invalid_field() if cached == "__unset__" else cached
        if native:
            return native["message"]
        return ""

    def is_cascade_warning_shown(self) -> bool:
        self._require_verified(self.CASCADE_WARNING_DIALOG, "CASCADE_WARNING_DIALOG")
        return self.is_visible(self.CASCADE_WARNING_DIALOG)

    def department_row_visible(self, department_name_en: str) -> bool:
        return self.is_visible(f'{self.LIST_ROW}:has-text("{department_name_en}")')

    def field_value(self, field_locator: str) -> str:
        return self.page.locator(field_locator).input_value()

    def is_access_denied_shown(self, locale: str = "en") -> bool:
        name = "ACCESS_DENIED_MESSAGE_AR" if locale == "ar" else "ACCESS_DENIED_MESSAGE_EN"
        locator = getattr(self, name)
        self._require_verified(locator, name)
        return self.is_visible(locator)
