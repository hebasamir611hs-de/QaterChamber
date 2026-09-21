"""
cms/pages/org_structure/org_structure_admin_page.py — OrgStructureAdminPage.

Control_Panel Page Object for PBI 129399 (QC-ABOUT-007 — Organizational
Structure / Departments).

MIGRATED 2026-09-15 (mandatory, standards.md's "Object Authoring Is the Only
Path for Content Operations — Not Content & Data", superseded/broadened
2026-09-07): this class previously drove every field write and every save
through `Content & Data`'s raw Object Definitions grid
(objectDefinitionId=80610). That surface is retired for this project.
Department has its OWN dedicated Object Authoring surface, CONFIRMED LIVE
this session (scripted Playwright, qcdev, real TEST_USER/TEST_PASSWORD login
— .auth/cp_admin_state.json was refreshed with a fresh login this session;
.auth/state.json, the DEFAULT `AUTH_STATE_PATH` a plain test run loads, was
NOT touched and may still hold an old/expired session — flagged for the QA
Manager's rerun):

  - **Slug: `department`** — `https://qcdev.ihorizons.com/web/qatar-chamber/
    manage-department` (redirects live to `/en/manage-department`, confirmed
    harmless — same page, same fields). Renders the generic Save-as-Draft /
    Submit-for-Publishing / Unpublish-to-edit-as-draft state machine every
    other Object Authoring surface uses — see
    `cms/pages/components/object_authoring_page.py` (`ObjectAuthoringPage`),
    which this class now composes instead of duplicating.
  - **16 live entries** confirmed at probe time (Board of Directors (General
    Assembly), General Director Office, Legal Affairs Department, Member
    Services Sector, Public Relations & Media Department, Finance &
    Administration Sector, Certificates & Attestations Section, Business
    Committees Department, plus 8 QCTEST-prefixed/leftover rows from prior
    Content & Data-era test runs — e.g. "Legal Affairs Unit AR", "<b>IT
    Support</b>", "Temp Dept", "Root Dept No Parent", "Old Division", "PN
    Test Dept EN", "No Photo Test Dept" — real leftover test data on qcdev,
    not created by this migration pass, flagged for cleanup). Each row's
    Entry column renders the real Department Name (EN) text (not a UUID —
    title-based row lookup is correct here, unlike manage-strategic-
    pillar-card), and every row DOES carry a real `a[data-qc-oel-delete]`
    (contradicting the pre-migration test module's own docstring note "no
    teardown/delete action was found on this Objects list UI" — that was
    true of the retired Content & Data grid only; `delete_entry_by_title()`
    (inherited from `ObjectAuthoringPage`) is a real, working teardown path
    now, not used by this class since the test module didn't call for one).
  - **Field labels on the create/edit form, confirmed live** (exact visible
    accessible names, all reachable via `page.get_by_role(...)`/the
    `role=<role>[name="<label>" i]` raw-selector syntax): Department Name
    (EN)*, Department Name (AR)*, Parent Department (combobox), Person Name
    (EN)*, Person Name (AR)*, Person Title (EN)*, Person Title (AR)*, Person
    Photo (single file upload, no EN/AR split — unlike Widget Image on
    manage-dynamic-widget), Department Description (EN) (textarea, optional),
    Department Description (AR) (textarea, optional), Display Order*
    (spinbutton), Active Status (checkbox). Unlike GM Message's bilingual
    fields (one input + a locale-toggle button), Department's EN/AR pairs
    are genuinely SEPARATE fields with distinct accessible names — same
    pattern as `HomeDynamicWidgetsAdminPage`'s "Widget Image (EN)"/"Widget
    Image (AR)".
  - **Locator-constant contract, deliberately NOT the base class's plain
    label strings:** every field-locator constant below (`DEPT_NAME_EN`,
    `PARENT_DEPARTMENT`, `ACTIVE_STATUS_CHECKBOX`, `DISPLAY_ORDER`, ...) is a
    raw Playwright selector STRING using the `role=<role>[name="<label>" i]`
    engine syntax (confirmed live, each uniq=1) — not a bare label. This
    keeps the existing test module's own direct usage working unchanged
    underneath the same public names: `admin.field_value(admin.DEPT_NAME_EN)`,
    `admin.type(admin.PARENT_DEPARTMENT, ...)`,
    `page.locator(admin.ACTIVE_STATUS_CHECKBOX).is_checked()`. `field_value()`
    is therefore OVERRIDDEN below (the base class's own `field_value(label)`
    expects a bare label, which would break every one of those call sites).
  - **PARENT_DEPARTMENT** (`role=combobox[name="Parent Department" i]`) is a
    real autocomplete combobox (`role="combobox"`, `aria-autocomplete="list"`,
    placeholder "Choose an Option", a paired hidden id-value input) driven by
    the shared `select_combobox_option()`/"Open Options Menu" pattern
    (confirmed live: exactly one such trigger on this form) for setting an
    EXISTING department as parent. RE-CONFIRMED LIVE 2026-09-15 typing a
    free-text, non-matching value then blurring: the field silently CLEARS
    back to empty — this matches the NEWER 2026-09-08 finding already in the
    test module (TC-018B, `test_parent_department_rejects_free_text_invalid_
    reference`), NOT the OLDER 2026-08-23 claim behind the skipped duplicate
    case (ADO-133327 / TC-082, `_CONFIRMED_BUG_PARENT_FIELD_FREE_TEXT`,
    "Parent Department is a plain free-text input holding the raw numeric
    ID"). That older claim was almost certainly true of the retired Content
    & Data grid only and does not reproduce on the real Object Authoring
    surface — flagged for the QA Manager; the skip reason for TC-082 was not
    touched here (test-file changes are out of this pass's scope) but should
    be re-examined given this finding. IMPORTANT CAVEAT, also confirmed live
    this session: the clearing only fires on **blur** (tab/click away) —
    `BasePage.type()` (`.clear()` + `.fill()`, no blur) leaves the field
    still holding the just-typed invalid text immediately afterward. TC-018B
    calls `admin.type(admin.PARENT_DEPARTMENT, invalid_value)` then
    IMMEDIATELY asserts `field_value(...) != invalid_value` with no blur in
    between — reproduced live exactly as the test does it: `field_value()`
    still equalled `invalid_value` right after `type()`, i.e. TC-018B is
    likely to FAIL as currently written against this surface, not because
    the picker doesn't reject free text (it does, on blur) but because
    nothing in the test's own call sequence ever blurs the field. Flagged,
    not fixed (test-file change, out of this pass's scope).
  - **SEARCH_INPUT** — CONFIRMED LIVE this is `[data-qc-oel-q]` (placeholder
    "Search entries…", client-side filter over rows already fetched — a
    generic entries-list filter present on every `manage-<slug>` page, ADO
    139124), and it is NOT the same element as the OLD generic locator
    (`input[placeholder="Search"], input[type="search"]`), which on THIS
    page resolves to the SITE-WIDE HEADER search box instead
    (`[data-qa-id="searchInput"]`, `role=textbox[name="Search" i]`) —
    confirmed live the hard way: typing into that box and pressing Enter
    NAVIGATES AWAY to `/search?q=...`, losing the admin page entirely. Kept
    as a disclosed near-miss for anyone touching this again.
  - **NEW_BUTTON** — there is no button literally labelled "New"/"Add" on
    this surface; `manage-department` renders the create form directly below
    the entries list (see `ObjectAuthoringPage.open_new_entry_form()`'s own
    docstring) with Save-as-Draft/Submit-for-Publishing as its only actions.
    Redefined here to `ObjectAuthoringPage.SAVE_AS_DRAFT_BUTTON` — it only
    renders for an authenticated session with the create form mounted,
    satisfying the existing test module's use of it as an "am I on the
    management screen" signal (TC-001/003) and its absence as the "admin
    surface not reached" signal for the anonymous case (TC-002).
  - **No Cancel button was found anywhere on the create form** (confirmed
    live — Save as Draft and Submit for Publishing are the only two
    buttons). `CANCEL_BUTTON` is left an explicit unresolved placeholder
    (`_require_verified`, project convention) rather than guessed —
    `cancel()` now RAISES instead of silently no-op'ing a button that no
    longer exists. TC-054 (`test_cancel_add_form_discards_data`, ADO-133363)
    calls `admin.cancel()` and will error until this is resolved (e.g. by
    confirming there genuinely is no discard action beyond "navigate away
    without saving" — trivially true here since nothing was ever submitted
    — or by finding a real one). Flagged, not guessed.
  - **`save()` now maps to `submit_for_publishing()`, not `save_as_draft()`
    — a real, load-bearing behavior decision, not an arbitrary pick.**
    CONFIRMED LIVE both ways: (1) `save_as_draft()` enforces NO required-
    field validation at all — an entry with an EMPTY Department Name (AR)
    saved as Draft with zero error, twice, reproduced independently; (2)
    `submit_for_publishing()` DOES block on a missing required field (see
    the validation finding below) and is the only path that produces an
    APPROVED record. Roughly half this module's cases assert the change on
    the PUBLIC frontend afterward (TC-006, TC-007, TC-018B, TC-019, TC-034,
    TC-051/052, TC-079(skipped)...) — a Draft entry never renders there (see
    `ObjectAuthoringPage`'s own Preview-banner wording: "Visitors do not see
    this"). Only `submit_for_publishing()` satisfies both halves of the
    module. Net effect the QA Manager should know: every test in this
    module now publishes straight to the LIVE qcdev site with no
    draft/staging step at all — there is no way to exercise these cases
    without doing so on this surface.
  - **VALIDATION MECHANISM — CONFIRMED LIVE, RE-VERIFIES ADO-133322
    DIFFERENTLY THAN FILED:** this surface has NO app-rendered validation-
    error element for a missing-required-field violation. The only
    `.text-danger`/`[role="alert"]` nodes present in the DOM (9 of them,
    confirmed live via `outerHTML` dump) are `sr-only` LENGTH/FILE-SIZE
    FEEDBACK TEMPLATES (`data-length-feedback="Maximum Number of Characters
    Exceeded"`, `data-file-size-feedback="..."`) that exist unconditionally
    on every load, regardless of actual validation state, and read empty via
    `.inner_text()`/`is_visible()` either way — they are not a real signal.
    The actual, confirmed-live gate on a blocked Submit for Publishing is
    the BROWSER'S OWN native HTML5 constraint validation on each `required`
    field (`element.checkValidity()` reports `false`,
    `element.validationMessage` reports exactly **"Please fill out this
    field."** — confirmed live for the Department Name (AR) field). This is
    a native browser popup, not part of the page DOM at all, and its text is
    always in the BROWSER'S OWN locale (English here), never a localized
    app-level message in either language. **ADO-133322 re-verification
    result: the bug reproduces, but more broadly than filed** — the filed
    title ("Empty Department Name (AR) is rejected... shows the wrong-
    language message") implies an app message exists in the wrong language;
    live, on the correct (Object Authoring) surface, there is NO app-level
    validation message in EITHER language for this or any other required
    field — only the browser's own generic native string. `is_save_error_
    shown()`/`save_error_text()` below are reimplemented against
    `checkValidity()` accordingly; every "exact bilingual error message"
    assertion in the test module (TC-009/014/022/026/029/032/037/046 — ADO-
    133317/133322/133331/133335/133338/133341/133346/133355) now compares
    against a native English browser string that will never equal the
    app's intended bilingual copy — one class of finding, not eight
    unrelated ones.
  - **MAXLENGTH TRUNCATION — a second, separate class of finding:** every
    150/1000-char-limited field (Department Name EN/AR, Person Name EN/AR,
    Person Title EN/AR = maxlength 150; Department Description EN/AR =
    maxlength 1000) carries a real native `maxlength` attribute. CONFIRMED
    LIVE: `.fill("A" * 151)` on Department Name (EN) yields a 150-character
    value, never 151 — the browser truncates before the value can ever
    exist, so the record saves as perfectly valid. Every "exceeding N
    characters is rejected" case (TC-010/015/023/027/030/033/041/044 — ADO-
    133318/133323/133332/133336/133339/133342/133350/133353) can never
    actually submit an over-limit value on this surface and will see NO
    error where the test expects one — not a defect in the app, a client-
    side control masking the intended boundary condition.
      **HEALED 2026-09-15** (one-shot heal, triage AUTOMATION_BUG verdict;
      a separate Low-priority product bug, ADO-142173, was already filed for
      the underlying "truncates with no visible feedback" UX gap — NOT
      re-litigated here): TC-010/023/027/032 (ADO-133318/133323/133332/
      133336 — the 150-char EN/AR Department Name and EN/AR Person Name
      cases) were rewritten in the test module to assert the truncated
      `field_value()` (== 150 chars) immediately after `fill()`, instead of
      `is_save_error_shown()` after `save()` — the real, confirmed-live
      enforcement mechanism on this surface. The other four maxlength cases
      in this family (TC-030/033/041/044 — Person Title EN/AR, Department
      Description EN/AR) were flagged by the same triage pass but were OUT
      OF THIS PASS'S EXPLICIT SCOPE (only the Department/Person Name four
      were named) — they almost certainly need the identical fix and are
      left as a follow-up, not silently carried along here.
      **FOLLOW-UP HEAL 2026-09-15 (explicit, one-shot, scoped to exactly
      these four tests):** live-reconfirmed via a direct DOM probe against
      the real manage-department form (framework's own
      `open_departments_list()` login path, not a possibly-stale cached
      storageState) — Person Title (EN) and Person Title (AR) are
      `<input>` elements with `maxlength="150"` (a 200-char fill()
      truncates to exactly 150), matching each case's own stated boundary.
      Department Description (EN) and Department Description (AR) are
      `<textarea>` elements with `maxlength="1000"` (a 1050-char fill()
      truncates to exactly 1000) — confirmed live, not assumed, that HTML5
      `maxlength` applies to a `<textarea>` the same way it does to an
      `<input>` on this surface. All four are the identical truncation
      mechanism as the four already-healed Name fields, at each case's own
      stated boundary (150 vs. 1000) rather than a guessed shared limit.
      TC-030 (ADO-133339), TC-033 (ADO-133342), TC-041 (ADO-133350), and
      TC-044 (ADO-133353) were rewritten in the test module the same way —
      assert the truncated `field_value()` immediately after `fill()`, no
      `save()` call. All four already used `_unique_ar_dept_name()` for
      `name_ar` — no fixture-collision literal to fix here, already
      covered by the module-wide pass.
      Also confirmed by this same triage pass and fixed in the test module:
      these tests (and ~27 siblings) reused the single hardcoded literal
      `name_ar="قسم"` as throwaway boilerplate with zero teardown, so every
      rerun collided with a prior run's leftover record via this surface's
      REAL duplicate-name rejection banner ("This record was not saved:
      another department already uses this English/Arabic name") — not
      previously recognized by `is_save_error_shown()` at all (see that
      method's own docstring) and now the actual, wrong-signal root cause
      three of these four tests were seeing. Fixed at the source with a
      per-invocation unique AR-name suffix (`_unique_ar_dept_name()` in the
      test module) rather than only patched via the now-moot truncation
      rewrite (which no longer saves at all, so does not even hit this
      collision) — done module-wide since the same collision is latent in
      every other test still using the bare literal.
  - **DISPLAY ORDER is a native `type="number"` input** (`required`,
    `min="-2147483648"`, `max="2147483647"` — confirmed live) — a real,
    confirmed product/UI difference from the retired Content & Data grid,
    which rendered this same field as plain `type="text"`. Three concrete,
    live-tested consequences:
      1. `fill("0")` and `fill("-1")` both pass native `checkValidity()`
         (the native `min` doesn't encode the business rule "must be
         positive") — so `is_save_error_shown()`'s native-validity check
         CANNOT detect TC-046/047 (ADO-133355/133356) by itself.
      2. CONFIRMED LIVE by an independent create-and-cleanup probe:
         `Submit for Publishing` with Display Order = "0" does NOT create
         the entry (real, server-side rejection) — so the underlying
         business rule IS enforced, just not through any signal this
         session could positively identify (no native invalid state, no
         non-empty custom error node found in a direct post-click DOM
         scan). TC-046 (ADO-133355) is therefore likely to under-report via
         `is_save_error_shown()` as currently implemented — flagged, not
         silently special-cased on a guessed selector.
      3. CONFIRMED LIVE: `page.get_by_role("spinbutton", ...).fill("abc")`
         RAISES (`Error: Cannot type text into input[type=number]`) rather
         than producing any in-app rejection — TC-048 (ADO-133357,
         `display_order="abc"`) will ERROR, not fail an assertion, the
         first time this module runs against the real surface. Not
         special-cased here (would be guessing at an intended replacement
         behavior); flagged for the QA Manager to decide (e.g. is the case
         really about a non-numeric STRING, which this native input can no
         longer receive at all, or about "reject anything that isn't a
         valid positive integer", which would need a different action).
  - **Auth:** Object Authoring's `manage-<slug>` URL performs NO login/
    session check of its own (confirmed live: a stale/expired storageState
    silently renders the public "Coming Soon" template, not a login
    redirect). `open_departments_list()` below therefore owns a real
    login-if-needed step (mirrors the shape of every sibling `*AdminPage`'s
    own equivalent), entering via the explicit English-locale `/en/home`
    URL — confirmed live elsewhere on this project (see
    `GmMessageAdminPage`'s own docstring) that a prior AR-locale public-page
    visit can otherwise leak Arabic chrome into a subsequent admin
    navigation even under an `/en/...` path.

PAGE-SETTINGS SURFACE RE-VERIFICATION (2026-09-16, corrects the 2026-08-23
record in test_org_structure_control_panel.py): re-investigated on a direct
instruction that a Page Title (EN/AR) / Hero Banner (EN/AR) / page-Status
surface for the Organizational Structure page DOES exist somewhere on
qcdev. Live-confirmed, scripted Playwright, fresh admin login, THREE
independent, more thorough methods than the original 2026-08-23 check
(which only searched the retired Content & Data object grid):
  1. The full, UNFILTERED Objects admin list (`Control Panel > Objects`) —
     every one of the ~150 objects carrying a Content & Data panel-link
     entry for this site was enumerated directly from the rendered nav
     (not a search box, which this admin's own search is unreliable for —
     see point 3). No object named anything containing "Organizational",
     "Organisation", or "Structure" exists. Every sibling About-Us sub-page
     DOES have its own dedicated "<Name> Page(s)" object in this same list
     — Chairman Message Pages (78084), About Qatar Chamber Pages (77427),
     Board Directory Pages (147370), Chamber Laws Pages (146377) — making
     Organizational Structure's absence a real, contrastable gap, not a
     search miss.
  2. The full Site Pages admin (`Site Builder > Pages`, 322 pages total)
     was searched for "Manage: Org" — the ~258 "Manage: <Object>" content
     pages that back every `manage-<slug>` Object Authoring surface on
     this project were enumerated (confirmed: "Manage: Department",
     "Manage: Chairman Message Page", "Manage: Board Directory Page",
     "Manage: About Hero Banner", "Manage: About Qatar Chamber Page", etc.
     all present) — no "Manage: Organizational ..." page exists among
     them. (NOTE: this admin's own search, like the Objects admin's, is a
     relevance-ranked fuzzy match that pads results with the full
     unrelated corpus below the true top matches when the term itself has
     zero real hits — verified by checking that a true miss ("Manage:
     Org") surfaces zero relevant top results while a true hit ("Manage:
     Chairman") surfaces the exact match first; single-word terms were
     used throughout for this reason, after "Hero Banner"/"Page" as
     multi-word queries were observed to error internally and silently
     fall back to the unfiltered full list — a broken-search false
     positive, not evidence of anything.)
  3. Direct single-word searches in the Objects admin for "Structure",
     "Organizational", and "Organisation" each returned 0 results; "Org"
     matched only the unrelated system "Organization" object (Liferay's
     own user-organization entity, scope=company).
  4. The live public page itself (`/about-us/organizational-structure`,
     fresh anonymous context) was checked for any Hero-Banner-related
     network call or DOM element — zero: no `/o/c/...` REST call for any
     Hero Banner object, and a full-page screenshot confirms no hero
     banner element renders at all, consistent with the original
     2026-08-27 finding.
Conclusion: the 2026-08-23 "no page-level settings surface" finding for
PAGE TITLE and page STATUS is CORRECT and now more strongly confirmed — no
such surface exists anywhere on qcdev for this page specifically (kept
skipped in the test module, reason updated to cite this stronger
re-verification).

HERO BANNER IS DIFFERENT — a real, live, working, GENERIC multi-page Hero
Banner registry DOES exist: the "About Hero Banner" object (id 79334,
`manage-about-hero-banner`, ERC `QCDEMO-ABOUT-HERO-BANNER`), confirmed live
to already back 5 real entries for OTHER About-Us sub-pages, one per
`Page Key` value (`about-us`, `chairman-message`, `chamber-laws`,
`vision-mission-objectives`, plus a stray `kdhfkds` test leftover not
created by this session). Its Fields tab (confirmed live) has exactly:
Page Key (Text, Mandatory=Yes, the object's own Entry Title Field — no
separate "Title" field), Banner Image (Attachment, Mandatory=No, ONE
shared field — no EN/AR split, unlike Department's other bilingual pairs),
Banner Image Alt Text (Text, Translatable=Yes — rendered as two separate
named textboxes, "Banner Image Alt Text" / "Banner Image Alt Text —
العربية", same pattern as GmMessageAdminPage's bilingual fields). No entry
with Page Key `organizational-structure` (or similar) exists yet — an
admin COULD create one using this already-working mechanism, but nothing
currently wires the public Organizational Structure page to consume it
(see point 4 above: zero API call, zero DOM element there) — creating such
an entry today would have no visible effect on that page. `AboutHeroBanner
AdminPage` below drives this surface; the 4 EN-locale Hero Banner cases
(ADO-133307/133308/133309/133310) are now implemented for real against it.

THREE FURTHER LIVE FINDINGS from implementing those 4 cases (scripted
Playwright, fresh probes, 2026-09-16), each independent of the missing
Organizational Structure wiring above:
  a. Banner Image's own Mandatory=No (per its Fields-tab definition) is
     NOT a locator-detection gap — CONFIRMED LIVE by directly submitting
     an entry with a Page Key and NO Banner Image: it reaches Approved
     status with no rejection of any kind. ADO-133310 ("Leaving Hero
     Banner (EN) empty is rejected as mandatory") does not reproduce; the
     real, confirmed behavior is acceptance. Implemented to assert the
     CASE'S intended (rejected) behavior, which will legitimately FAIL
     against the real product — the correct, honest outcome per this
     project's own established convention (cf. the DISPLAY ORDER gap
     documented on Department above), not inverted to force a pass.
  b. NO file-size limit is actually enforced for Banner Image either —
     CONFIRMED LIVE with three escalating real uploads: 2.8MB (this
     case's own literal boundary), then ~5.9MB, then ~14.7MB — ALL THREE
     reached Approved with no rejection, despite the upload widget's own
     instructional copy claiming "Upload a .jpg,.jpeg,.png,.svg no larger
     than 5 MB." ADO-133309 does not reproduce either; implemented the
     same way as (a) — asserting the case's intended rejection, expected
     to legitimately FAIL, documenting a real product gap.
  c. `ObjectAuthoringPage.upload_file_expect_rejected()` is UNRELIABLE for
     a large (multi-MB) file on this specific surface — CONFIRMED LIVE by
     running the identical 2.8MB upload twice: once via a direct
     `upload_file()` + `submit_for_publishing()` flow (accepted, Approved,
     reproducibly, twice), and once via `upload_file_expect_rejected()`
     directly (returned `True`, i.e. "rejected") — a real, live
     contradiction traced to `upload_file_expect_rejected()`'s own
     15000ms "Add" button click timeout racing a slow real multi-MB
     upload's server round-trip, NOT a genuine validation rejection (the
     large-file case is inherently slower than the small-file case that
     method's `1 of 1` progress wait was designed around). Consequently
     ADO-133309 below does NOT use `upload_file_expect_rejected()` — it
     drives the full `upload_file()` + `submit_for_publishing()` +
     entries-list-status flow directly instead, which is deterministic
     and was independently reproduced 3 times. `upload_file_expect_
     rejected()` itself is left unchanged (correct, and independently
     reproduced twice, for the genuinely-instant, tiny-file .bmp
     format-rejection case, ADO-133308) — this is a usage-boundary
     finding (large files need the direct flow), not a defect in the
     shared helper worth changing project-wide off one surface's probe.

RE-VERIFICATION 2026-09-21 (developer Alaa Medhat posted fix comments on
ADO-142187/142200/142173 claiming these three gaps closed on qcdev as of
2026-09-19; each surface below was independently re-probed live — scripted
Playwright, fresh admin login — before writing anything, per this project's
"never trust a dev comment blindly" convention):

1. ADO-142187 (Page Title/Hero Banner/Status surface, bug behind ADO-133298)
   — the dev's claim is CONFIRMED LIVE AND CORRECT, superseding the "NO
   PAGE-SETTINGS SURFACE" finding above for THIS specific gap. A real, new
   Object Authoring surface now exists: slug `org-structure-page`
   (`/web/qatar-chamber/manage-org-structure-page`, page title "Manage:
   Organizational Structure Page", confirmed live 2026-09-21), with real
   fields Page Title (EN, `name="ObjectField_pageTitle"`, `maxlength=100`,
   `required`), Page Title — العربية (`#qc-ar-pageTitle`, `maxlength=100`,
   `required`), Hero Banner (`name="ObjectField_heroBanner"`, file upload,
   `.jpg,.jpeg,.png,.svg`, NOT `required`), Hero Banner (Arabic)
   (`name="ObjectField_heroBannerAr"`, same accept list, NOT `required`),
   Hero Banner Alt Text (EN + `#qc-ar-heroBannerAltText`, `maxlength=150`,
   optional), and a genuine "Status" content field (a `select-from-list`
   combobox, CONFIRMED LIVE default value `"Draft"` on a fresh create form
   — matches the dev's claim exactly). See `OrgStructurePageAdminPage`
   below. **Entry-column caveat** (same exception class as
   manage-strategic-pillar-card, see `ObjectAuthoringPage`'s own
   docstring): this object's list Entry column renders a UUID/ERC
   (confirmed live: the pre-existing real row shows
   `QCDEMO-129399-ORG_STRUCTURE_PAGE-01`, dated 2026-09-19 — almost
   certainly the dev's own fix-verification content, already
   PUBLISHED — and a disposable test-created row showed a plain UUID),
   never the Page Title text — `find_entry_code_by_field()` /
   `delete_entry_by_code()` are the only safe lookup/teardown path here,
   never a title-based match, and the real singleton-looking row above must
   never be touched by any test (create your own disposable row; do not
   edit or delete `QCDEMO-129399-ORG_STRUCTURE_PAGE-01`).
   ADO-133298 (`test_valid_page_title_en_saved`) is now implemented for
   real: create a disposable entry, fill both Page Title fields, Submit for
   Publishing, assert the save succeeds (no error) — confirmed live this
   session with an actual create → verify-via-edit-form → delete round
   trip (a real QCTEST-prefixed row was created, its Page Title (EN) read
   back byte-for-byte equal after Submit for Publishing, then deleted; the
   real singleton row's count was unaffected before and after). The 8
   sibling skipped Page-Title cases (133299-133306) and 3 Page-Status cases
   (133313-133315) were NOT touched this pass (out of this pass's explicit
   scope — flagged as a reasonable follow-up on this same confirmed-real
   surface, not attempted here).

2. ADO-142200 (AR-specific Hero Banner control, bug behind ADO-133311) —
   the dev's claim is CONFIRMED LIVE AND CORRECT for the SHARED
   `manage-about-hero-banner` object specifically (a DIFFERENT object from
   #1 above — do not conflate them): a second field, "Banner Image
   (Arabic)" (hidden filename textbox accessible name confirmed live:
   `"Banner Image (Arabic) Select File"`, uniq=1, same
   `.jpg,.jpeg,.png,.svg`/2MB rule copy as the EN field), now exists on the
   real add/edit form alongside the original "Banner Image" field — the
   "NO DISTINCT AR-LOCALE HERO BANNER IMAGE CONTROL EXISTS" finding below
   is SUPERSEDED for this field (kept below, historical, for the record).
   ADO-133311 (`test_valid_hero_banner_ar_uploads`) is now implemented for
   real: create a disposable entry, upload a DISTINCT image into each of
   Banner Image (EN) and Banner Image (Arabic), Submit, assert the save
   reaches the real live "Published" state (see finding 2a below for why
   not "Approved") — confirmed live this session with an actual
   create → verify → delete round trip.
   **2a. INCIDENTAL LIVE FINDING, NOT part of either filed bug, discovered
   while implementing 133311, fixed locally in `AboutHeroBannerAdminPage`
   only (never touched the shared `ObjectAuthoringPage` base or any other
   object's button text):** this object's Submit button now reads "Submit
   for Review", not "Submit for Publishing" — confirmed live 2026-09-21
   (`button:has-text("Submit for Publishing")` matches 0 elements on this
   surface today; `"Submit for Review"` matches 1). The resulting entry
   still reaches real, live "PUBLISHED" status on submit (not a pending
   review queue) — confirmed live via the entries list. `row_status_text()`
   normalizes this to `"Published"`, never `"Approved"` — the ALREADY
   confirmed-live vocabulary for the SEPARATE `manage-department` surface's
   generic Object Authoring wording does not hold here; this object's own
   Status column literally renders `"PUBLISHED"`/`"DRAFT"` uppercase text.
   **This means the 4 already-implemented Hero Banner cases
   (ADO-133307-133310), which all call `hero.save()` then assert
   `row_status_text(page_key) == "Approved"`, are silently broken by this
   same drift** — flagged here as a real, live, out-of-this-pass-scope
   finding (not fixed in the test module this pass; only 133311's own new
   test uses the corrected `"Published"` expectation).
   **2b. Delivery-surface check NOT attempted, disclosed rather than
   skipped silently:** the dev's comment also claims Arabic About-Us pages
   now render the AR image with EN fallback. Verifying that would require
   either mutating one of the 3 real, live, already-PUBLISHED Page-Key
   entries this registry backs (`about-us`/`chairman-message`/
   `chamber-laws` — prohibited, this project's Test-Data Policy classifies
   real editorial content as SNAPSHOT_RESTORE, "prohibited in automation
   outside an explicit, documented exception") or creating a disposable
   entry under a Page Key no real page consumes (which would prove
   nothing, since nothing is wired to render it). Save-succeeds is the
   confirmed evidence for this pass; the delivery-rendering claim is
   neither confirmed nor refuted.

3. ADO-142173 (silent-truncation UX gap, bug behind ADO-133318) — the
   dev's claim is PARTIALLY CONFIRMED LIVE: a real, live inline warning
   (`<div aria-live="polite">`, scoped to the field's own
   `.form-group` ancestor, no stable id — matched relative to the field
   locator, never a hardcoded fragment id, since Liferay mints a fresh
   `fragment-<uuid>` id per page load) DOES render the moment a real
   keystroke is rejected past the 150-char cap on Department Name (EN),
   Department Name (AR), Person Name (EN), AND Person Name (AR) — confirmed
   live for all four fields this session via real `press_sequentially()`
   keystrokes (never `.fill()`, which sets the value directly with no
   keystroke events and was confirmed live to NOT trigger this warning at
   all — a real trap for anyone re-verifying this with the existing
   `fill_text()` helper). **What did NOT confirm live: the claimed Arabic
   translation of the warning.** For BOTH Arabic fields
   (Department Name (AR), Person Name (AR)), the exact same ENGLISH string
   rendered — `"Maximum 150 characters reached — anything further is not
   accepted."` — not the dev's claimed Arabic text
   («تم بلوغ الحد الأقصى 150 حرفاً — لا يُقبل أي نص إضافي.»). The mechanism
   (element, timing, per-field wiring) is genuinely mechanical/uniform
   across all four fields, so all four are implemented this pass, but the
   two AR-field tests assert the REAL observed (English) text, not the
   claimed localized one — this is real, honest retest evidence that
   ADO-142173's fix is real but incomplete (missing localization), not a
   locator gap. Self-clearing was probed for up to 10s with no keystroke
   activity and did NOT clear in that window — not asserted either way
   here (out of this test's scope; the case only requires the warning to
   appear). Paste-specific wording was not probed (not required by the
   named test cases). See `OrgStructureAdminPage.type_past_limit()` /
   `max_length_warning_text()` below.

NO DISTINCT AR-LOCALE HERO BANNER IMAGE CONTROL EXISTS (ADO-133311/133312)
— HISTORICAL, SUPERSEDED for the Banner Image field by finding 1 above
(2026-09-21) — kept verbatim for the record, not deleted, per this
project's "never silently erase a prior finding" convention:
confirmed live via both the Fields tab (exactly one "Banner Image"
Attachment field, no locale variant) and the real add/edit form (exactly
one "Select File" control) — only Banner Image Alt Text is genuinely
bilingual. Writing a distinct "AR" test against this object would
necessarily re-assert the exact same control 133307/133310 already cover
— a duplicate test body, not a real additional verification. Kept SKIPPED
with a precise, dedicated reason (not the generic no-surface one) rather
than force a duplicate. ADO-133312 (Hero Banner AR empty-mandatory) was
NOT re-investigated this pass — the dev's comment for ADO-142200 says
nothing about the AR field being mandatory (only that it exists,
optional, with a fallback) — left SKIPPED under its existing reason.
"""

from cms.pages.components.object_authoring_page import (
    APPROVED_BANNER_SETTLE_TIMEOUT_MS,
    ObjectAuthoringPage,
)
from config.settings import control_panel_url, settings

SLUG = "department"

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
    (`ObjectAuthoringPage`) with Department's own field map — see module
    docstring for every confirmed-live fact this class relies on.
    Constructed with just `page` (slug fixed to "department"), unlike the
    shared base class's own `__init__(page, slug)` signature."""

    # ---- Field locators — role=<role>[name="<label>" i] raw selector
    # strings, each confirmed uniq=1 live 2026-09-15 (see module docstring's
    # "Locator-constant contract" note on why these are full selectors, not
    # bare labels).
    DEPT_NAME_EN = f'role=textbox[name="{FIELD_DEPT_NAME_EN}" i]'
    DEPT_NAME_AR = f'role=textbox[name="{FIELD_DEPT_NAME_AR}" i]'
    PARENT_DEPARTMENT = f'role=combobox[name="{FIELD_PARENT_DEPARTMENT}" i]'
    PERSON_NAME_EN = f'role=textbox[name="{FIELD_PERSON_NAME_EN}" i]'
    PERSON_NAME_AR = f'role=textbox[name="{FIELD_PERSON_NAME_AR}" i]'
    PERSON_TITLE_EN = f'role=textbox[name="{FIELD_PERSON_TITLE_EN}" i]'
    PERSON_TITLE_AR = f'role=textbox[name="{FIELD_PERSON_TITLE_AR}" i]'
    DEPT_DESCRIPTION_EN = f'role=textbox[name="{FIELD_DEPT_DESCRIPTION_EN}" i]'
    DEPT_DESCRIPTION_AR = f'role=textbox[name="{FIELD_DEPT_DESCRIPTION_AR}" i]'
    DISPLAY_ORDER = f'role=spinbutton[name="{FIELD_DISPLAY_ORDER}" i]'
    ACTIVE_STATUS_CHECKBOX = f'role=checkbox[name="{FIELD_ACTIVE_STATUS}" i]'
    # Confirmed live: exactly one "Select File" button exists on this form
    # (Person Photo is the only upload field — no EN/AR split).
    PERSON_PHOTO_SELECT_FILE_BTN = 'role=button[name="Select File" i]'

    # ---- List / management-screen aliases (see module docstring for why
    # each is redefined rather than reused verbatim from Content & Data) ----
    NEW_BUTTON = ObjectAuthoringPage.SAVE_AS_DRAFT_BUTTON
    LIST_ROW = ObjectAuthoringPage.ENTRIES_TABLE_ROW
    SAVE_BUTTON = ObjectAuthoringPage.SUBMIT_FOR_PUBLISHING_BUTTON  # see save()
    # Confirmed live: `[data-qc-oel-q]` (placeholder "Search entries…") is
    # this list's OWN client-side filter — NOT `[data-qa-id="searchInput"]`
    # (the site-wide header search, which navigates to /search on Enter).
    SEARCH_INPUT = "[data-qc-oel-q]"

    # ---- Not confirmed this session — explicit placeholder, never guessed --
    CANCEL_BUTTON = _UNVERIFIED  # no Cancel button found on the create form (see docstring)
    PAGE_SETTINGS_URL = _UNVERIFIED
    CASCADE_WARNING_DIALOG = _UNVERIFIED
    CASCADE_CONFIRM_BUTTON = _UNVERIFIED
    CIRCULAR_REFERENCE_ERROR = _UNVERIFIED
    # CONFIRMED LIVE 2026-09-15 (triage-failures, Allure evidence from the
    # ADO-133318/133323/133332/133336 rerun): the real app-rendered
    # duplicate-name rejection banner text, e.g. "This record was not saved:
    # another department already uses this English/Arabic name." Matched by
    # stable leading substring (exact bilingual wording not itself
    # confirmed for the Arabic case this session) — see
    # is_save_error_shown()'s docstring for how this is used.
    DUPLICATE_NAME_ERROR = "This record was not saved"
    ACCESS_DENIED_MESSAGE_EN = _UNVERIFIED
    ACCESS_DENIED_MESSAGE_AR = _UNVERIFIED

    # Required fields whose native HTML5 constraint validation is the real
    # save-blocking signal on this surface (see is_save_error_shown()).
    _REQUIRED_FIELD_LOCATORS = (
        DEPT_NAME_EN, DEPT_NAME_AR, PERSON_NAME_EN, PERSON_NAME_AR,
        PERSON_TITLE_EN, PERSON_TITLE_AR, DISPLAY_ORDER,
    )

    ADMIN_HOME_EN_URL_PATH = "/en/home"

    def __init__(self, page):
        super().__init__(page, SLUG)

    def _require_verified(self, value: str, name: str) -> None:
        if value == _UNVERIFIED:
            raise RuntimeError(
                f"OrgStructureAdminPage.{name} is an unverified placeholder — locate the "
                f"real admin surface / trigger the real UI state and replace it before "
                f"running this test."
            )

    # ---- Navigation -----------------------------------------------------
    def open_departments_list(self) -> "OrgStructureAdminPage":
        """Ensures a real, authenticated session (Object Authoring's
        `manage-department` performs no login check of its own — a stale
        session silently renders the public "Coming Soon" page instead of
        redirecting to login, confirmed live), then opens the combined
        entries-list + create-form page via the shared
        `ObjectAuthoringPage.open_new_entry_form()`. No Content & Data menu
        walk is needed anymore — this surface is one direct URL."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))
        if not login.login_succeeded():
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))
        self.open_new_entry_form()
        return self

    def open_new_department_form(self) -> "OrgStructureAdminPage":
        """`manage-department` already renders the create form directly
        below the entries list with no separate "New" button (see module
        docstring) — `open_departments_list()` already lands there. Kept so
        the existing test module's own
        `open_departments_list().open_new_department_form()` chaining keeps
        working; just reconfirms the create form's first field is present
        rather than performing a second, redundant navigation."""
        self.wait_for(self.DEPT_NAME_EN, timeout=15000)
        return self

    def open_department_by_name(self, department_name: str) -> "OrgStructureAdminPage":
        """Opens a department row for edit via its own `Edit` link, matched
        directly against the (unfiltered) entries list.

        Deliberately does NOT type into `SEARCH_INPUT` first (unlike the
        pre-migration Content & Data-era version of this method) — CONFIRMED
        LIVE 2026-09-15 (two isolated repro scripts, one straight click vs.
        one preceded by a `SEARCH_INPUT` fill): typing into `SEARCH_INPUT`
        immediately before clicking a row's `Edit` link produces a real,
        reproducible defect — the resulting navigation lands on a BLANK
        create form (Department Name (EN) reads "") instead of the intended
        entry's edit form, even though the link's own `href` (captured right
        before the click) is provably correct (`?editEntry=<the right
        code>`) in both cases. The identical click against the SAME row
        located WITHOUT having touched `SEARCH_INPUT` first correctly loads
        the target entry's real field values every time. Root cause not
        further isolated this session (a client-side router/history-state
        interaction with the search filter's own debounce, not a wrong
        locator — the href is correct either way); avoiding the search step
        entirely sidesteps it. At the list sizes this project's Department
        object has (mid-teens, confirmed live), matching directly against
        the full unfiltered list is not a scale problem. (Separately,
        confirmed harmless: after ANY successful Edit-link click on this
        surface the browser's own `page.url` reads back WITHOUT the
        `?editEntry=...` query string — the app calls a client-side
        `history.replaceState` to clean the URL after reading it; the form
        still loads the correct entry, confirmed live by reading its field
        values back, not just the URL.)

        Also NOT the inherited `ObjectAuthoringPage.open_entry_by_edit_
        link()` — that method waits on `CANCEL_AND_ADD_NEW_LINK`, confirmed
        live ABSENT from this object's editing banner text (this surface's
        banner reads "Previewing <title> (approved) · open in a new tab",
        not the "Editing ... Cancel and add a new entry instead" wording
        other objects render — a genuine per-object rendering difference,
        not a shared-component bug, so it is overridden locally rather than
        changed in `object_authoring_page.py`). The confirmed-live, reliable
        settle signal here is the `Unpublish to edit as draft` button,
        which every department opened by this test module has (every entry
        this module creates is Submitted for Publishing, i.e. Approved —
        see `save()`'s own docstring)."""
        row = f'{self.LIST_ROW}:has-text("{department_name}")'
        self.wait_for(row, timeout=15000)
        edit_link = self.page.locator(row).get_by_role("link", name="Edit")
        try:
            edit_link.click(timeout=10000)
        except Exception:
            from core.web.overlays import dismiss_overlays

            dismiss_overlays(self.page)
            edit_link.click(force=True)
        self._wait_for_network_settle()
        self.wait_for(self.UNPUBLISH_BUTTON, timeout=APPROVED_BANNER_SETTLE_TIMEOUT_MS)
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
            # See module docstring's DISPLAY ORDER note: this is now a
            # native type="number" spinbutton — a non-numeric string here
            # will raise, not silently no-op (confirmed live).
            self.fill_number(FIELD_DISPLAY_ORDER, display_order)
        if parent_department is not None:
            self.select_combobox_option(FIELD_PARENT_DEPARTMENT, parent_department)
        if active_status is not None:
            self.set_checkbox(FIELD_ACTIVE_STATUS, active_status)
        return self

    def upload_person_photo(self, file_path: str) -> "OrgStructureAdminPage":
        self.upload_file(FIELD_PERSON_PHOTO, file_path)
        return self

    def save(self) -> "OrgStructureAdminPage":
        """Maps to Submit for Publishing — see module docstring's `save()`
        note for why (Save as Draft enforces no required-field validation
        at all, and most of this module's cases assert on the public
        frontend, which never renders a Draft record). Every call now
        publishes straight to the live qcdev site."""
        self.submit_for_publishing()
        return self

    def cancel(self) -> "OrgStructureAdminPage":
        self._require_verified(self.CANCEL_BUTTON, "CANCEL_BUTTON")
        self.click(self.CANCEL_BUTTON)
        return self

    def confirm_cascade_deactivation(self) -> "OrgStructureAdminPage":
        self._require_verified(self.CASCADE_CONFIRM_BUTTON, "CASCADE_CONFIRM_BUTTON")
        self.click(self.CASCADE_CONFIRM_BUTTON)
        return self

    # ---- State queries --------------------------------------------------------
    def field_value(self, locator: str) -> str:
        """OVERRIDES `ObjectAuthoringPage.field_value(field_label)` (which
        expects a bare label). Every field-locator constant on THIS class is
        a full `role=...` selector string, not a label (see module
        docstring) — the existing test module calls this with those
        constants directly (`admin.field_value(admin.DEPT_NAME_EN)`), so
        this must treat the argument as a raw selector, matching the
        pre-migration Content & Data-era contract exactly."""
        return self.page.locator(locator).input_value()

    def is_save_error_shown(self) -> bool:
        """See module docstring's VALIDATION MECHANISM finding: no
        app-rendered error element exists here for a required-field
        violation — the surface's own `.text-danger` nodes are `sr-only`
        length/file-size FEEDBACK TEMPLATES always present, never actually
        populated for a `required` violation. The real, confirmed-live
        signal is the browser's own native constraint validation on a
        `required` field, read via `checkValidity()` (the native validation
        bubble itself is not part of the DOM Playwright can query as text).
        Falls back to any VISIBLE, NON-EMPTY custom alert/error node for
        forward-compatibility (e.g. a future in-app toast) since the
        sr-only templates always read empty and would otherwise never
        trip a false positive.

        KNOWN GAP (see module docstring's DISPLAY ORDER note): a Display
        Order of "0" or a negative value is confirmed LIVE to be rejected
        server-side (Submit for Publishing does not create the entry), but
        passes native `checkValidity()` (native `min` is `-2147483648`) and
        produced no positively-identified custom error node in this
        session's probe — this method will likely under-report that
        specific case (ADO-133355/133356) as "no error shown" even though
        the real product correctly blocks it. Flagged, not silently
        special-cased on a guessed selector.

        EXTENDED 2026-09-15 (heal pass, triage AUTOMATION_BUG verdict on
        ADO-133318/133323/133332/133336 — see module docstring's HEALED
        note under MAXLENGTH TRUNCATION): this surface DOES render one more
        real, confirmed-live app error distinct from the sr-only templates
        above — the duplicate-name rejection banner (`DUPLICATE_NAME_ERROR`,
        "This record was not saved: ..."). Neither the native-validity loop
        nor the generic `[role="alert"], .alert-danger` scan recognized
        it. Recognized here as a third, generic signal so any test that
        legitimately needs to detect a duplicate-name rejection can do so —
        not specific to the four healed tests.

        HEALED 2026-09-15 (one-shot heal, explicit user-reported regression
        — 7 valid-save tests, ADO-133316/133319/133321/133325/133326/
        133328/133330, all failing `assert not is_save_error_shown()`,
        plus an "Execution context was destroyed" crash on ADO-133334):
        CONFIRMED LIVE this session (scripted Playwright, fresh login,
        qcdev) the requested hypothesis was WRONG — `DUPLICATE_NAME_ERROR`'s
        `get_by_text(...).is_visible()` check (added last session) is NOT
        the cause and needed no change: reproduced live against a genuine
        duplicate ("Legal Affairs Department", already a real live entry)
        and the match is a real, correctly-styled red `data-qc-oel-editbar`
        banner with a non-zero bounding box — a true positive, not a stray
        hidden template. The ACTUAL root cause is the native-validity loop
        directly above, live-traced with a step-by-step timeline probe:
        **on this surface, a SUCCESSFUL Submit for Publishing resets the
        screen to a fresh, BLANK "Add new entry" form roughly 600ms-1200ms
        after the click** (confirmed live, reproducible on every valid
        save, with or without a Parent Department selection) — and
        `submit_for_publishing()`'s own `_wait_for_settle()` already blocks
        for ~2500ms before returning, i.e. by the time a caller's very next
        line runs `is_save_error_shown()`, the reset has already happened.
        Checking `checkValidity()` on that fresh blank form's required
        fields then reports EVERY one of them invalid (all genuinely empty)
        — indistinguishable, by validity alone, from a real rejection.
        This reproduced on 100% of valid-save probes this session (not
        just the 7 named tests), so it is a general defect in this method,
        not one specific to any test's data. The distinguishing, live-
        confirmed signal: a REAL validation rejection leaves the SAME form
        on screen with every OTHER required field still holding the value
        the test just typed (only the deliberately-empty field is blank) —
        confirmed against every existing `assert admin.is_save_error_
        shown()` case in the test module (ADO-133317/133322/133331/133335/
        133338/133341 each leave exactly one required field unset, all
        others filled). A freshly-reset blank form instead has ALL required
        fields empty simultaneously. The loop below now only trusts a
        native-invalid finding when at least one OTHER required field is
        still non-empty; if every required field is blank, that is treated
        as "no error" (the blank-reset-form case), not silently re-litigating
        the separate pre-existing DISPLAY ORDER gap (0/negative bypassing
        `min`) noted above, which is unrelated and unchanged.
        Separately, `field.count()` itself (not just the `.evaluate()`
        call already guarded below) is now wrapped in the same try/except:
        live-reproduced the exact "Execution context was destroyed, most
        likely because of a navigation" error (ADO-133334) by querying
        `.count()` mid-transition, during the same async reset window —
        this was an unguarded call racing that same navigation, not a
        different bug."""
        # HEALED 2026-09-16 (one-shot heal, ADO-133326, live-confirmed via
        # ACTUAL PYTEST EXECUTION — not a manual probe): the PRIOR
        # implementation read each required field's checkValidity()/value via
        # its OWN separate `locator.evaluate()` round-trip, one field at a
        # time, in `_REQUIRED_FIELD_LOCATORS`' declared order (Dept Name
        # EN/AR, Person Name EN/AR, Person Title EN/AR, Display Order).
        # Direct pytest reproduction of a genuinely successful, non-colliding
        # save (fresh uuid-suffixed EN/AR names, confirmed no duplicate-name
        # banner) caught this loop MID-TRANSITION during this surface's
        # already-documented post-save "reset to a blank form" — 3 of 7
        # fields (the first 3 in declared order) read back still filled, the
        # remaining 4 read back empty, all within one single call. That torn
        # read satisfies the "at least one other field still filled"
        # heuristic below (designed to distinguish one real rejected field
        # from a fully-blank reset) and incorrectly reported a rejection.
        # FIX: resolve an element handle for every present field FIRST (each
        # still its own round-trip, but each is just a stable DOM node
        # reference — cheap and not itself value-sensitive), then read
        # validity/value for ALL handles in one SINGLE, atomic
        # `page.evaluate()` call. A single evaluate() runs synchronously in
        # the page's own JS engine, so it can only ever observe a fully-old
        # or fully-new snapshot — never a torn mix of the two — closing the
        # specific race this session reproduced.
        handles = []
        handle_locators = []
        for locator in self._REQUIRED_FIELD_LOCATORS:
            try:
                field = self.page.locator(locator)
                if field.count() != 1:
                    continue
                handle = field.element_handle()
                if handle is None:
                    continue
            except Exception:  # noqa: BLE001 — field may be mid-navigation (destroyed
                # execution context, ADO-133334) or not a native validity-bearing element
                continue
            handles.append(handle)
            handle_locators.append(locator)

        invalid_locators = []
        filled_count = 0
        if handles:
            try:
                results = self.page.evaluate(
                    "elements => elements.map(e => ({valid: e.checkValidity ? "
                    "e.checkValidity() : true, value: e.value}))",
                    handles,
                )
            except Exception:  # noqa: BLE001 — same destroyed-context guard as above
                results = []
            for locator, result in zip(handle_locators, results):
                if result["value"]:
                    filled_count += 1
                if not result["valid"]:
                    invalid_locators.append(locator)
        if invalid_locators and filled_count > 0:
            return True
        try:
            duplicate_banner = self.page.get_by_text(self.DUPLICATE_NAME_ERROR, exact=False)
            if duplicate_banner.count() > 0 and duplicate_banner.first.is_visible():
                return True
        except Exception:  # noqa: BLE001
            pass
        alert = self.page.locator('[role="alert"], .alert-danger')
        for i in range(alert.count()):
            try:
                if alert.nth(i).inner_text().strip():
                    return True
            except Exception:  # noqa: BLE001
                continue
        return False

    def save_error_text(self) -> str:
        """Custom app-level error text if any real one is ever found (see
        is_save_error_shown()'s docstring), else the FIRST invalid required
        field's own native `validationMessage`. CONFIRMED LIVE this is
        ALWAYS the browser's own default English wording ("Please fill out
        this field."), never a localized app message in either language —
        see module docstring's ADO-133322 re-verification note. Every
        "exact bilingual error message" assertion in the test module will
        legitimately fail against this real, confirmed-live value; that is
        the correct, honest outcome given the product's actual behavior on
        this surface, not a locator defect."""
        alert = self.page.locator('[role="alert"], .alert-danger')
        for i in range(alert.count()):
            try:
                text = alert.nth(i).inner_text().strip()
            except Exception:  # noqa: BLE001
                continue
            if text:
                return text
        for locator in self._REQUIRED_FIELD_LOCATORS:
            field = self.page.locator(locator)
            if field.count() != 1:
                continue
            try:
                result = field.evaluate(
                    "e => ({valid: e.checkValidity ? e.checkValidity() : true, "
                    "msg: e.validationMessage || ''})"
                )
            except Exception:  # noqa: BLE001
                continue
            if not result["valid"]:
                return result["msg"]
        return ""

    def is_cascade_warning_shown(self) -> bool:
        self._require_verified(self.CASCADE_WARNING_DIALOG, "CASCADE_WARNING_DIALOG")
        return self.is_visible(self.CASCADE_WARNING_DIALOG)

    def department_row_visible(self, department_name_en: str) -> bool:
        return self.row_visible(department_name_en)

    def is_access_denied_shown(self, locale: str = "en") -> bool:
        name = "ACCESS_DENIED_MESSAGE_AR" if locale == "ar" else "ACCESS_DENIED_MESSAGE_EN"
        locator = getattr(self, name)
        self._require_verified(locator, name)
        return self.is_visible(locator)

    # ---- Max-length inline warning (ADO-142173's claimed fix) ------------
    # CONFIRMED LIVE 2026-09-21 (see module docstring, finding 3): scoped
    # relative to whichever field locator is passed — never a hardcoded
    # fragment id (Liferay mints a fresh `fragment-<uuid>` id per page
    # load, see this class's own docstring on why every other locator here
    # is role/label-anchored) — via the field's own nearest `.form-group`
    # ancestor, which was confirmed live to contain exactly one
    # `[aria-live="polite"]` warning node per length-limited field.
    _MAX_LENGTH_WARNING_RELATIVE = 'xpath=ancestor::div[contains(@class, "form-group")][1]//*[@aria-live="polite"]'

    def type_past_limit(self, field_locator: str, text: str) -> "OrgStructureAdminPage":
        """Types `text` via real, per-character keystrokes
        (`press_sequentially`) rather than `fill_text()`'s `.fill()` —
        CONFIRMED LIVE 2026-09-21 (module docstring, finding 3) that a bare
        `.fill()` sets the value directly with no keystroke events and
        never triggers the max-length warning at all, even though the
        native `maxlength` truncation still applies either way. Use this
        (not `fill_text()`/`fill_department_form()`) whenever a test needs
        to observe the live warning, not just the truncated value."""
        field = self.page.locator(field_locator)
        field.click()
        field.press_sequentially(text, delay=15)
        return self

    def max_length_warning_text(self, field_locator: str) -> str:
        """Real, live text of the field-scoped max-length warning (empty
        string if not present/not yet rendered). See module docstring,
        finding 3, for the confirmed-live English wording and the
        confirmed-live ABSENCE of the claimed Arabic translation on the AR
        fields — this method returns whatever actually rendered, verbatim,
        never a guessed/localized value."""
        warning = self.page.locator(field_locator).locator(self._MAX_LENGTH_WARNING_RELATIVE)
        if warning.count() == 0:
            return ""
        return warning.first.inner_text().strip()


ABOUT_HERO_BANNER_SLUG = "about-hero-banner"

FIELD_HERO_BANNER_PAGE_KEY = "Page Key"
FIELD_HERO_BANNER_IMAGE = "Banner Image"
FIELD_HERO_BANNER_IMAGE_AR = "Banner Image (Arabic)"
FIELD_HERO_BANNER_ALT_TEXT_EN = "Banner Image Alt Text"
FIELD_HERO_BANNER_ALT_TEXT_AR = "Banner Image Alt Text — العربية"


class AboutHeroBannerAdminPage(ObjectAuthoringPage):
    """Drives the SHARED, generic "About Hero Banner" Object Authoring
    surface (`manage-about-hero-banner`, object id 79334) — see this
    module's own docstring ("HERO BANNER IS DIFFERENT" section) for the
    full live-confirmed trail. This is a genuinely SEPARATE object from
    Department — not org-structure-specific — already used by 5 real
    entries for OTHER About-Us sub-pages (`about-us`, `chairman-message`,
    `chamber-laws`, `vision-mission-objectives`), keyed by its own
    mandatory `Page Key` field (also this object's Entry Title Field, so
    every inherited `ObjectAuthoringPage` row-lookup/teardown method that
    takes a "title" works directly with a Page Key value).

    Composed here (rather than given its own `cms/pages/<page>/` folder)
    because this pass's scope is limited to the two Organizational
    Structure files — a project convention violation this creates
    (cross-page shared surfaces normally belong in `cms/pages/components/`
    per `object_authoring_page.py`'s own docstring) that should be
    revisited if/when another page's test suite also needs to drive this
    same object, to avoid duplicating this class."""

    # CONFIRMED LIVE 2026-09-21 (module docstring, finding 2a): this
    # object's own Submit button now reads "Submit for Review", not the
    # base class's generic "Submit for Publishing" — a real, live,
    # per-object drift discovered while implementing ADO-133311, fixed
    # HERE ONLY (the shared ObjectAuthoringPage base and every other
    # object composing it — Department, the new OrgStructurePageAdminPage
    # below — were independently confirmed live to still say "Submit for
    # Publishing"; widening the shared base would have been wrong). The
    # entry still reaches a real, live "PUBLISHED" status on click (not a
    # pending-review queue) — see row_status_text()'s own normalization,
    # which for THIS object yields "Published", never "Approved".
    SUBMIT_FOR_PUBLISHING_BUTTON = 'button:has-text("Submit for Review")'

    def __init__(self, page):
        super().__init__(page, ABOUT_HERO_BANNER_SLUG)

    # ---- Navigation -------------------------------------------------------
    def open_hero_banner_form(self) -> "AboutHeroBannerAdminPage":
        """Mirrors `OrgStructureAdminPage.open_departments_list()`'s own
        defensive login-if-needed shape — `manage-<slug>` performs no login
        check of its own on this project (confirmed live project-wide, see
        that method's docstring): a stale/expired session silently renders
        the public "Coming Soon" template instead of redirecting to
        login."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(OrgStructureAdminPage.ADMIN_HOME_EN_URL_PATH))
        if not login.login_succeeded():
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(OrgStructureAdminPage.ADMIN_HOME_EN_URL_PATH))
        self.open_new_entry_form()
        return self

    # ---- Form actions -------------------------------------------------------
    def fill_hero_banner_form(
        self,
        page_key: str = None,
        alt_text_en: str = None,
        alt_text_ar: str = None,
    ) -> "AboutHeroBannerAdminPage":
        if page_key is not None:
            self.fill_text(FIELD_HERO_BANNER_PAGE_KEY, page_key)
        if alt_text_en is not None:
            self.fill_text(FIELD_HERO_BANNER_ALT_TEXT_EN, alt_text_en)
        if alt_text_ar is not None:
            self.fill_text(FIELD_HERO_BANNER_ALT_TEXT_AR, alt_text_ar)
        return self

    def upload_banner_image(self, file_path: str) -> "AboutHeroBannerAdminPage":
        self.upload_file(FIELD_HERO_BANNER_IMAGE, file_path)
        return self

    def upload_banner_image_ar(self, file_path: str) -> "AboutHeroBannerAdminPage":
        """CONFIRMED LIVE 2026-09-21 (module docstring, finding 2 — ADO-
        142200): the second, Arabic-specific "Banner Image (Arabic)" field
        now exists on this real add/edit form (hidden filename textbox
        accessible name confirmed live: "Banner Image (Arabic) Select
        File", uniq=1) — drives it via the same generic upload_file() flow
        as the EN field."""
        self.upload_file(FIELD_HERO_BANNER_IMAGE_AR, file_path)
        return self

    def upload_banner_image_expect_rejected(self, file_path: str) -> bool:
        """Safe ONLY for a small/instantly-rejected file (e.g. an
        unsupported format) — CONFIRMED LIVE UNRELIABLE for a large
        (multi-MB) file on this surface (see this module's own docstring,
        finding (c)): the underlying `upload_file_expect_rejected()`'s
        15000ms "Add" button timeout can race a slow real large-file
        upload and report a false "rejected" for a file the product
        actually accepts. For a file-size boundary case, drive
        `upload_banner_image()` + `submit_for_publishing()` +
        `row_status_text()` directly instead (see
        test_hero_banner_en_over_2mb_rejected)."""
        return self.upload_file_expect_rejected(FIELD_HERO_BANNER_IMAGE, file_path)

    def save(self) -> "AboutHeroBannerAdminPage":
        self.submit_for_publishing()
        return self


ORG_STRUCTURE_PAGE_SLUG = "org-structure-page"

FIELD_ORG_PAGE_TITLE_EN = "Page Title"
# CONFIRMED LIVE 2026-09-21: this is the field's real, exact accessible
# name (its <label for="qc-ar-pageTitle">'s own text content), asterisk and
# em-dash included — an exact-match fill_text()/field_value() call must use
# this literal string, not a guessed "Page Title (AR)"-style label.
FIELD_ORG_PAGE_TITLE_AR = "Page Title — العربية *"


class OrgStructurePageAdminPage(ObjectAuthoringPage):
    """Drives the NEW Object Authoring surface for the Organizational
    Structure page's own settings (`manage-org-structure-page`, ERC
    `QCDEMO-129399-ORG_STRUCTURE_PAGE`) — CONFIRMED LIVE 2026-09-21, see
    this module's own docstring (RE-VERIFICATION section, finding 1) for
    the full trail. This closes the gap the module's older "NO PAGE-
    SETTINGS SURFACE" finding documented for Page Title specifically (Hero
    Banner/Status on THIS object were not previously covered by that older
    finding at all — this is a brand-new object, not a re-verification of
    an old one).

    Composed here (same file, same convention already established by
    `AboutHeroBannerAdminPage` above) rather than a separate
    `cms/pages/<page>/` folder — this object is specific to the
    Organizational Structure page, so it belongs in this module's own
    per-page folder either way.

    **Entry-column caveat (same class as manage-strategic-pillar-card,
    see `ObjectAuthoringPage`'s own docstring):** this object's list Entry
    column renders a UUID/ERC, never the Page Title text — confirmed live
    both for the pre-existing real row (`QCDEMO-129399-ORG_STRUCTURE_PAGE-
    01`, dated 2026-09-19, already PUBLISHED — almost certainly the
    developer's own fix-verification content; NEVER touch this row) and
    for a disposable test-created row (a plain UUID). Always resolve a
    just-created entry via `find_entry_code_by_field(FIELD_ORG_PAGE_
    TITLE_EN, ...)` and tear down via `delete_entry_by_code()` — never a
    title-based match, and never a positional/"last row" assumption (see
    `ObjectAuthoringPage.newest_entry_code()`'s own incident note)."""

    def __init__(self, page):
        super().__init__(page, ORG_STRUCTURE_PAGE_SLUG)

    # ---- Navigation -------------------------------------------------------
    def open_org_structure_page_form(self) -> "OrgStructurePageAdminPage":
        """Mirrors `AboutHeroBannerAdminPage.open_hero_banner_form()`'s own
        login-if-needed shape — confirmed live project-wide that
        `manage-<slug>` performs no login check of its own."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(OrgStructureAdminPage.ADMIN_HOME_EN_URL_PATH))
        if not login.login_succeeded():
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(OrgStructureAdminPage.ADMIN_HOME_EN_URL_PATH))
        self.open_new_entry_form()
        return self

    # ---- Form actions -------------------------------------------------------
    def fill_page_title(self, title_en: str = None, title_ar: str = None) -> "OrgStructurePageAdminPage":
        if title_en is not None:
            self.fill_text(FIELD_ORG_PAGE_TITLE_EN, title_en)
        if title_ar is not None:
            self.fill_text(FIELD_ORG_PAGE_TITLE_AR, title_ar)
        return self

    def upload_hero_banner(self, file_path: str) -> "OrgStructurePageAdminPage":
        self.upload_file("Hero Banner", file_path)
        return self

    def save(self) -> "OrgStructurePageAdminPage":
        self.submit_for_publishing()
        return self
