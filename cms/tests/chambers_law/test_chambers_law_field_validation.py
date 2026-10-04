"""
cms/tests/chambers_law/test_chambers_law_field_validation.py --
Control_Panel FIELD-VALIDATION cases for PBI 129394 (QC-ABOUT-003 --
Chamber's Law), ALL SEVEN batches -- this object's field-validation
coverage is complete with batch 7.

  Batch 1 -- Law Entry Icon .......... 134940 134941 134942 134943
  Batch 2 -- Law Number EN + AR ...... 134944 134945 134946 134947
                                       134948 134949 134950 134951
  Batch 3 -- Law Title  EN + AR ...... 134952 134953 134954 134955
                                       134956 134957 134958 134959
  Batch 4 -- Law Description EN + AR . 134960 134961 134962 134963
                                       134964 134965 134966 134967
  Batch 5 -- External Link URL ....... 134968 134969 134970 134971
  Batch 6 -- Display Order ........... 134972 134973 134974 134975
                                       134987
  Batch 7 -- Active Status + Entry ID  134976 134977 134978

SCOPE -- every case here is on the **Law Entry** object
(`manage-law-entry`), the per-CARD record. NOTHING here touches
`manage-chamber-laws-page` (the page-level singleton); that object is the
sibling module's scope.

FILE OWNERSHIP -- this module is deliberately separate from
`test_chambers_law_control_panel.py`: that module and the two Page Objects
it drives were being edited concurrently when this batch was written. Every
helper below that duplicates something already in the sibling module, or
that reaches raw Playwright, is marked `# CONSOLIDATE:` with the home it
belongs in. None of them are new *behaviour* -- they are a temporary, owned
copy so this batch could land without touching a file another engineer had
open.

[RESOLVED 2026-09-15] The duplicate skip stubs in the sibling module are
GONE. `test_chambers_law_control_panel.py` used to carry TWELVE
`@pytest.mark.skip` stubs -- `...` bodies -- for exactly these twelve case
IDs (134940-134951), left behind by an earlier session that could not reach
the admin form at all. They duplicated the function names, the `tc_<id>`
markers and the `allure.label("testcase")` values of the real tests below,
so `-m tc_134940` selected TWO items and Allure double-counted each case.
Those twelve stubs were deleted (that module's other stubs, for IDs outside
134940-134951, were left untouched). Each of these twelve IDs now resolves
to exactly ONE test -- the real one, in this module.

[RESOLVED 2026-09-15, batch 3] The SAME eight stubs existed for
134952-134959 (Law Title) and were deleted for the same reason: with the
real tests below in place, `-m tc_134952` selected TWO items and Allure
double-counted every Law Title case. Verified after removal -- each of the
twenty IDs 134940-134959 now collects exactly ONE test, repo-wide.

[RESOLVED 2026-09-15, batch 4] The SAME eight stubs existed for
134960-134967 (Law Description) and were deleted for the same reason, now
that the real tests below replace them. Verified after removal: each of the
twenty-eight IDs 134940-134967 collects exactly ONE test, repo-wide.

[RESOLVED 2026-09-15, batch 5] The SAME four stubs existed for
134968-134971 (External Link URL) and were deleted for the same reason, now
that the real tests below replace them. Verified after removal: no
`134968`/`134969`/`134970`/`134971` token remains anywhere in
`test_chambers_law_control_panel.py`, and each of the thirty-two IDs
134940-134971 collects exactly ONE test, repo-wide.

[RESOLVED 2026-09-16, batches 6+7] The LAST eight stubs -- 134972-134978
(Display Order, Active Status, Law Entry ID) and 134987 (duplicate Display
Order) -- were deleted for the same reason, now that the real tests below
replace them. They were the final `@pytest.mark.skip` bodies in that module
for any ID this module owns. Verified after removal: no `134972`..`134978`
or `134987` token remains anywhere in `test_chambers_law_control_panel.py`,
and each of the FORTY IDs this module now owns collects exactly ONE test,
repo-wide.

=========================================================================
CONFIRMED LIVE 2026-09-15 -- how a save is actually validated here
=========================================================================
Read off the manage page's OWN shipped JavaScript and a scoped, disclosed
CLI Playwright probe (never the Playwright MCP) against
`manage-law-entry?editEntry=QCDEMO-129394-law-11-1990`, authenticated with
`.auth/state.json` at 1920x1080. This is the model every test below is
written against:

1. **`Save as Draft` performs NO validation at all.** Its handler sets
   `formnovalidate`, and `setConstraints(form, false)` strips the `required`
   attribute off every control before submitting -- the page's own comment
   says so: *"Save as Draft stays deliberately unguarded, because a draft is
   allowed to be incomplete."* So **every case here drives `Submit for
   Publishing`**, which is the only button that validates. A case that says
   "click Save" and expects a validation error can only mean that button.

2. **`Submit for Publishing` validates in three stages**, in order:
   a. `setConstraints(form, true)` restores `required`, then
      `form.checkValidity()` / `form.reportValidity()` -- the BROWSER's own
      required-field check. A missing required value is reported natively
      (on the control, via `validationMessage`), *not* as page text, and the
      submit is cancelled. `Law Number`, `Law Number - العربية`,
      `Law Title*`, `Law Description*`, `Law Icon` and `Display Order` all
      carry `required` (read live off the DOM).
   b. a `/validate` pre-flight POST that returns the Object's own NAMED
      validation rules, plus two local checks the endpoint cannot make
      (a required Attachment, and URL-shaped Text fields).
   c. the real submit; a server refusal is replayed through
      `explainRejection()` to recover the message.
   Anything from (b)/(c) is rendered as a RED BAR --
   `div[data-qc-oel-editbar]` (background `#b91c1c`) -- reading
   *"This record was not saved:"* followed by `&bull;`-prefixed reasons.
   A SUCCESS renders the same element in maroon with either
   *"Draft saved."* or *"Saved and submitted for publishing."*, carried
   across the post-save redirect in `sessionStorage`. The editing banner
   uses that SAME attribute, so a reader must match on TEXT, never on
   "the editbar" as a singleton -- `_LawEntryForm.save_refusal_text()` /
   `.success_message_text()` below do exactly that.

   *** AND THE RED BAR IS NOT WHERE MOST MESSAGES GO. ***
   See the next section -- this point (3) is true but was, on its own,
   dangerously incomplete, and a bug was filed on the gap.

=========================================================================
WHERE A REFUSAL IS RENDERED -- and the reader that could not see it
=========================================================================
[FIXED 2026-09-15. This is the most important correction in this module.]

`_LawEntryForm.save_refusal_text()` used to read `[data-qc-oel-editbar]`
elements ONLY, and match ONLY the prefix "This record was not saved:". Both
halves of that are too narrow, and the consequence was not cosmetic: the
tests reported "refused silently, no message" for saves that had shown a
perfectly good message, and product bug #141989 was filed against a product
that was behaving correctly. #141989 IS NOW CLOSED AS NOT A BUG.

Reproduced by hand on this very form, both cases visible, `display:block`,
`visibility:visible`, still present at 0.5s / 2s / 5s, value NOT stored:

  201 chars in Law Title (EN)       -> "Law Title must not exceed 200 characters"
  501 chars in Law Description (EN) -> "Law Description must not exceed 500 characters"

The old reader returned "" for BOTH.

THERE ARE THREE RENDERERS, read off the page's own shipped JavaScript:

  (1) UNDER THE BOX -- `fieldError(control, message)`:
          var note = document.createElement('div');
          note.setAttribute(FIELD_ERROR_ATTR, '');   // data-qc-oel-field-error
          note.setAttribute('role', 'alert');
          note.textContent = message;
      A CLASS-LESS <div>, inserted after the control, OUTSIDE any editbar,
      with NO "This record was not saved:" prefix. `reportComplaints()`
      routes EVERY message it can tie to a field there, and the page's own
      comment says so: "ADO 141960 - each message under the box it is
      about; the bar is kept for whatever cannot be tied to a field (a rule
      that names none, the server's bare refusal)". An Object NAMED-RULE
      message arriving from `/validate` as plain text is tied to its control
      by `controlForMessage()`, which matches the LONGEST field label
      (either language) or field name occurring in the sentence -- so "Law
      Title must not exceed 200 characters" lands under Law Title and NEVER
      reaches the bar.
  (2) THE RED BAR -- only the leftovers, and in either language
      ("This record was not saved:" / the Arabic twin).
  (3) LIFERAY'S OWN INPUTS-* FRAGMENT ERROR -- `showInputError()` un-hides
      `<p id="...-error" class="... text-danger sr-only">` by dropping
      `sr-only`. Entirely independent of the page's own machinery, and the
      only renderer that reports the fragment's declared `maxLength`.

`save_refusal_text()` now reads ALL THREE and returns them joined, so it is
matched on the MESSAGE, not on a container or a prefix.
`refusal_bar_text()` keeps the old, bar-only reading as its own named read
for callers that need to tell the two apart. `field_error_texts()` /
`fragment_error_texts()` expose each renderer individually, and
`save_message_report()` prints all of them for a failure report.

THE THREE OUTCOMES ARE NOW DISTINGUISHABLE. `_outcome_shape(refusal,
success, attempted, stored)` returns REFUSED_WITH_MESSAGE /
REFUSED_SILENTLY / ACCEPTED_AND_STORED / UNCLEAR_OUTCOME, and "silently"
now means one checkable thing -- nothing in ANY of the three renderers,
not merely nothing in the red bar. **134954 and 134962 have been
re-pointed** at the widened reader and both now report the shape plus a
per-renderer breakdown; their old comments, which asserted the "#141989
silent refusal" as established fact, have been corrected in place.

THE MESSAGE LANGUAGE IS NOT THE UI'S LANGUAGE UNLESS THE URL PINS IT.
Every one of the page's own strings goes through `t(en, ar)`, which picks
by `document.documentElement.lang`. Measured live, same storage state, same
unprefixed URL, one run apart: `ar-SA` from a fresh context (the shared
authoring account's own Liferay language is `ar_SA`), `en-US` after any
`/en`-prefixed page had been visited in that context. That is the root
cause of "messages can arrive in Arabic on the English UI" -- and it moves
the FIELD LABELS too, which is why every batch-5 navigation pins its locale
(see `ObjectAuthoringPage._manage_url()`).

3. **The `Law Number` 100-character cap is a SERVER-SIDE object validation
   rule, with no client-side cap.** Confirmed live: neither the English
   control (`input[name="ObjectField_lawNumber"]`) nor its Arabic twin
   (`#qc-ar-lawNumber`) carries a `maxlength` attribute or the page's own
   `data-qc-oel-counter`, because the page derives those from a
   `maxLength` *objectFieldSetting* and this field expresses its cap as a
   *validation rule* instead (`match(lawNumber, "(?s)^.{0,100}$")` ->
   "Law Number must not exceed 100 characters", per
   cms/liferay-context.md's LawEntry catalogue). Consequence: a 101st
   character CAN be typed, and the refusal arrives from `/validate`, in the
   red bar. 134946/134950 are therefore written against the OTHER half of
   their own either/or expected result, and check both honestly.

[!] LIVE FINDINGS AGAINST THIS BATCH'S CASES. Scripted to the CASE as
   written, per the Result Integrity rule -- an assertion is never loosened
   to match observed behaviour. (i) has since been FIXED IN THE CASE
   ITSELF; (ii)-(iv) stand:

   (i)  [CORRECTED IN AZURE -- 134942 rev 2, 2026-09-15] **The Law Icon
        size cap is 1 MB, and the PBI was right.** The earlier revision of
        134942 asserted a 2 MB cap and explicitly claimed the PBI's 1 MB
        figure was wrong; it was the CASE that was wrong. Three independent
        live sources on this form agree on 1 MB: the visible help line
        *"Upload a .jpg,.png,.svg no larger than 1 MB."*, the Documents &
        Media picker's own iframe `src` config `"maxFileSize": 1` with
        `"extensions":[".jpg",".png",".svg"]`, and the upload fragment's
        feedback string `data-file-size-feedback="Please enter a file with
        a valid file size no larger than 1 MB."`. A full-page scan for
        `2 MB` returns NO match anywhere. 134942 below is scripted to the
        corrected rev-2 case: 1 MB accepted / 1.1 MB rejected / 0.5 MB
        accepted, with the rejection asserted against that exact feedback
        literal.

        [OPEN] **Which "1 MB"?** The picker declares `maxFileSize: 1` --
        a NUMBER OF MB, with the byte multiplier applied somewhere in the
        product's own code, which is not in this repo and could not be read
        from the page's config alone. The fixtures below use the BINARY
        megabyte, `1 MB = 1048576 bytes` (Liferay's own file-size
        conventions are 1024-based, and this module's `ONE_MB` already
        is). If the product actually means 1000000 bytes, then the
        "exactly 1 MB" file (1048576) sits 48576 bytes ABOVE the cap and
        step 2 will be rejected -- that outcome is NOT a locator or
        framework fault, it is the boundary definition, and step 2's
        assertion message says so explicitly. The other two files are
        deliberately unambiguous under EITHER definition: 1153433 bytes is
        over both caps, 524288 bytes is under both.

   (ii) **A 101-character ARABIC Law Number is very unlikely to be
        rejected.** The `Law Number length` rule is evaluated by Liferay
        against the field's DEFAULT-locale value, and the Arabic control
        (`#qc-ar-lawNumber`) carries no `name` attribute, so it is not part
        of the `/validate` payload at all. 134950 step 3 is expected to
        SAVE. Scripted as the case states it.

  (iii) **A whitespace-only Law Number is very unlikely to be rejected.**
        Four spaces satisfy the browser's `required` check (the box is not
        empty) and satisfy `^.{0,100}$`. The page HAS a "cannot be only
        spaces" guard, but its own code (`URL_FIELD_NAME`) applies it ONLY
        to fields whose name ends in url/link/href. 134947/134951 are
        expected to SAVE four spaces. Scripted as the cases state.

   (iv) **The 1990 record's Law Icon is ALREADY `law-icon.svg`** (674
        bytes, read live), which is the very file 134940 uploads. The case
        is still executed as a real upload (a fresh 40 KB SVG of the same
        name), which is a genuine write; Liferay de-duplicates a same-named
        upload into `law-icon (1).svg`, so the read-back matches the file
        STEM + extension, exactly as the sibling module's
        `_restore_content_image()` already does and documents.

=========================================================================
BATCH 3 -- Law Title: what the LIVE page actually says (probed 2026-09-15)
=========================================================================
Read off `manage-law-entry?editEntry=QCDEMO-129394-law-11-1990` with a
scoped, READ-ONLY CLI Playwright probe (no fill, no click, no save; never
the Playwright MCP), authenticated via `.auth/state.json` at 1920x1080,
plus the Object's own rule catalogue in cms/liferay-context.md.

  (a) **THERE IS NO "Save" BUTTON.** The form's complete button set, read
      live: `Unpublish to edit as draft`, `Reset`, `Refresh`,
      `Select File`, `Remove file`, `Undo remove`, `Save as Draft`,
      `Submit for Publishing` (plus the preview shell's `EN` / `AR` /
      `Chamber's Law`). Every batch-3 case says "click Save"; that is a
      known wording defect in the Azure cases, being corrected separately.
      It can ONLY mean `Submit for Publishing`, because `Save as Draft`
      sets `formnovalidate` and calls `setConstraints(form, false)` --
      stripping `required` off every control -- so a draft save performs no
      validation at all and every negative case here would silently
      succeed. All eight tests below drive `Submit for Publishing`.

  (b) **The 200-character cap is server-side, exactly like Law Number's
      100.** Neither `input[name="ObjectField_lawTitle"]` (EN) nor
      `#qc-ar-lawTitle` (AR) carries a `maxlength` attribute or the page's
      `data-qc-oel-counter`, and the string "200" appears NOWHERE in the
      page's scripts or rendered text. The cap is the Object's own named
      validation rule -- `match(lawTitle, "(?s)^.{0,200}$")`, error label
      "Law Title must not exceed 200 characters" /
      "يجب ألا يتجاوز عنوان القانون 200 حرف" (cms/liferay-context.md,
      LawEntry). Consequence, same as Law Number: a 201st character CAN be
      typed, and the refusal (if any) arrives from `/validate` in the red
      bar. 134954/134958 are therefore written against the SECOND half of
      their own either/or expected result, and check both honestly.
      CONFIRMED: the cap here is 200, NOT the 100 of Law Number.

  (c) **`#qc-ar-lawTitle` carries NO `name` attribute** -- `hasNameAttr:
      false`, read live, while its English twin has
      `name="ObjectField_lawTitle"`. That is byte-for-byte the shape behind
      product defect **#141969** on Law Number: without a `name`, the
      Arabic control never enters the `/validate` payload, and the length
      rule is evaluated against the DEFAULT-locale value only. **This makes
      the defect OBJECT-WIDE, not one field's** -- both localized Text
      fields on LawEntry have it, and `Law Description` is very likely the
      third. 134958 step 3 is expected to SAVE 201 Arabic characters.

  (d) **The "cannot be only spaces" guard still cannot reach a Law Title.**
      Read live, verbatim: `var URL_FIELD_NAME = /(^|[a-z0-9])(url|link|
      href)$/i;`, and the guard (`urlComplaint()`, tagged "ADO 139198" in
      its own comment) is invoked only for fields whose name matches it.
      `lawTitle` does not, so four spaces satisfy the browser's `required`
      check (the box is not empty) and satisfy `^.{0,200}$`. That is the
      shape of product defects **#141968 / #141970**. 134955 and 134959 are
      expected to SAVE four spaces.

  (e) Both accessible names resolve to EXACTLY ONE control through
      `ObjectAuthoringPage.label_pattern()` (verified live, count == 1
      each): the English label renders with a trailing space, `'Law Title '`,
      and the Arabic one with the required asterisk,
      `'Law Title — العربية *'`. That pattern is anchored and tolerates
      both shapes (it is quoted in full in the Arabic block further down);
      an `exact=True` match on either name would resolve ZERO.

  [!] EXPECTED TO FAIL, and scripted to the case ANYWAY (Result Integrity
      -- an assertion is never loosened to match observed behaviour):
      **134955**, **134958** (step 3) and **134959**. If they fail the way
      Law Number's 134947/134950/134951 did, that is NEW EVIDENCE that
      #141968/#141969/#141970 are object-wide rather than Law-Number-only,
      which is the point of running them.

  Message language: the live max-length refusal on Law Number came back in
  ARABIC on the English UI ("يجب ألا يتجاوز رقم القانون 100 حرف"). No
  batch-3 case demands a literal message, so the cap assertions below match
  the Object's OWN named-rule error label in EITHER shipped language --
  which identifies the rule precisely without depending on the UI's
  language. That is narrower than "some refusal appeared", not looser.

  Title-field coupling: `lawTitle` is LawEntry's **Title Field**, so the
  entries list's Entry column renders it. Every navigation and restore
  below is keyed on the entry CODE (`open_entry_by_code`), never on the
  title text, so a mutated title cannot strand a test. 134943 does assert
  `row_visible(LAW_1990_TITLE)`; it is in the SAME xdist group, and the
  proved restore in each batch-3 `finally` is what keeps that precondition
  true.

=========================================================================
BATCH 4 -- Law Description: what the LIVE page actually says (2026-09-15)
=========================================================================
Read off `manage-law-entry?editEntry=QCDEMO-129394-law-11-1990` with a
scoped, READ-ONLY CLI Playwright probe (no fill, no click, no save; never
the Playwright MCP), authenticated via `.auth/state.json` at 1920x1080,
plus the Object's own rule catalogue in cms/liferay-context.md.

  (f) **Law Description really is a PLAIN TEXTAREA, in BOTH languages --
      NOT rich text.** Re-confirmed live: the English control is
      `<textarea name="ObjectField_lawDescription">` and the Arabic one is
      `<textarea id="qc-ar-lawDescription">`; neither is contenteditable,
      and the form carries **ZERO** `iframe[title="editor"]` (a CKEditor
      field on this surface always mounts one -- `Intro Content` on the
      sibling object does). The field's own embedded config reads
      `"type": "long-text"`, `"localizable": true`, `"required": true`.
      Every test below therefore uses `fill_text()` / `field_value()`, NOT
      `fill_rich_text()` / `rich_text_value()`, and 134960 asserts the
      textarea shape at runtime so a silent product change to a rich-text
      field is reported as itself instead of as a mystery failure. This
      confirms the difference `chambers_law_admin_page.py` already
      documents against what a "Description" field is on other objects.

  (g) **The 500-character cap is server-side, exactly like Law Number's 100
      and Law Title's 200 -- and it is 500, not either of those.** Neither
      textarea carries a `maxlength` attribute or the page's
      `data-qc-oel-counter`, and the string "500" appears NOWHERE in the
      form's rendered text; the only "500"s in its scripts are a settle
      timeout, a `font:500` style and an HTTP-500 comment. The cap is the
      Object's own named validation rule --
      `match(lawDescription, "(?s)^.{0,500}$")`, error label "Law
      Description must not exceed 500 characters" /
      "يجب ألا يتجاوز وصف القانون 500 حرف" (cms/liferay-context.md,
      LawEntry). Consequence, same as both sibling fields: a 501st
      character CAN be typed, and the refusal (if any) arrives from
      `/validate` in the red bar. 134962/134966 are written against the
      SECOND half of their own either/or expected result, and check both
      honestly.

  (h) **`#qc-ar-lawDescription` carries NO `name` attribute** --
      `hasNameAttr: false`, read live, while its English twin has
      `name="ObjectField_lawDescription"`. That is the THIRD localized
      field on this object with the shape behind product defects **#141969**
      (Arabic Law Number) and its Law Title twin **#141991**: without a
      `name`, the Arabic control never enters the `/validate` payload, so
      the length rule is evaluated against the DEFAULT-locale value only.
      Three of three localized LawEntry fields have it -- the defect is
      OBJECT-WIDE, not one field's. 134966 step 3 is expected to SAVE 501
      Arabic characters.

  (i) **The "cannot be only spaces" guard still cannot reach a Law
      Description.** Read live, verbatim: `var URL_FIELD_NAME =
      /(^|[a-z0-9])(url|link|href)$/i;`, and its call site bails out with
      `if (!URL_FIELD_NAME.test(field.name) || (field.businessType !==
      'Text' && field.businessType !== 'LongText')) return;`. The
      businessType half WOULD admit this field (`LongText`), but the NAME
      half does not: `lawDescription` matches no url/link/href suffix, so
      `urlComplaint()` is never called for it. Five spaces satisfy the
      browser's `required` check (the box is not empty) and satisfy
      `^.{0,500}$`. That is the shape of product defects **#141968 /
      #141970** (Law Number) and **#141990 / #141992** (Law Title).
      **134963 and 134967 are expected to SAVE five spaces.**

  (j) Both accessible names resolve to EXACTLY ONE control through
      `ObjectAuthoringPage.label_pattern()` (verified live, count == 1
      each): `'Law Description'` (the English label renders with NO
      asterisk even though the control itself carries `required`) and
      `'Law Description — العربية *'`. An `exact=True` match on the Arabic
      one would resolve ZERO.

  (k) The 1990 record's live baselines at probe time: EN 337 characters,
      AR 222 characters, record `(approved)`. Nothing below assumes those
      numbers -- every baseline is captured at runtime -- they are recorded
      only so a reader can tell a restored record from a dirty one.

  [!] EXPECTED TO FAIL, and scripted to the case ANYWAY (Result Integrity
      -- an assertion is never loosened to match observed behaviour):
      **134963**, **134966** (step 3) and **134967**. Each mirrors a defect
      already filed twice over on the sibling fields; a failure here is the
      third field's worth of evidence that both are object-wide.

  [!] 134962 step 3 -- THREE outcomes, not two. The English over-length
      save on Law Title (#141989) was refused **with no message at all**:
      the value was correctly not stored, and the red bar never appeared.
      That is a different product behaviour from "refused with a message"
      and from "accepted and stored", and the bug write-up depends on
      which one happens. 134962's step-3 assertion message therefore
      reports all three discriminators explicitly -- the outcome the page
      reported, the refusal text (or its absence), and the length of the
      value the record actually holds afterwards -- so the failure report
      alone identifies the shape.

  Message language: the live max-length refusal on Law Number came back in
  ARABIC on the English UI ("يجب ألا يتجاوز رقم القانون 100 حرف"). No
  batch-4 case demands a literal message, so the cap assertions below match
  the Object's OWN named-rule error label in EITHER shipped language --
  narrower than "some refusal appeared", not looser.

=========================================================================
BATCH 5 -- External Link URL: what the LIVE page/object actually say
=========================================================================
Read off `manage-law-entry?editEntry=QCDEMO-129394-law-11-1990` with a
scoped, READ-ONLY CLI Playwright probe (no fill, no click, no save; never
the Playwright MCP) at 1920x1080 via `.auth/state.json`, plus the Object's
own definition and validation-rule catalogue fetched through the page's own
authenticated `request()` helper
(`/o/object-admin/v1.0/object-definitions/78508`).

  (l) **THIS FIELD IS NOT BILINGUAL -- confirmed three independent ways.**
      The form renders exactly ONE control named
      `ObjectField_externalLinkUrl`; the only `#qc-ar-*` twins on the whole
      form are `qc-ar-lawNumber`, `qc-ar-lawTitle`, `qc-ar-lawDescription`
      (three, all `name`-less); the Object definition reports
      `localized: false` for this field; and the page's own
      `configuration.localizedFields` reads exactly
      "lawNumber,lawTitle,lawDescription". So defects #141969 / #141991 and
      the Law Description twin -- a `name`-less Arabic control absent from
      the `/validate` payload -- CANNOT apply here. There is no twin to be
      missing.

  (m) **The only-spaces guard DOES reach this field** -- the one text field
      on this object it reaches. `var URL_FIELD_NAME =
      /(^|[a-z0-9])(url|link|href)$/i;` and the call site bails out on
      `!URL_FIELD_NAME.test(field.name) || (businessType !== 'Text' &&
      businessType !== 'LongText')`. `externalLinkUrl` matches the name
      pattern and its businessType is `Text`, so `urlComplaint()` runs.
      That is why this field has MORE client-side messages than any other
      here, and why a narrow refusal reader would have produced more false
      "silent" verdicts on this batch than on any before it.

  (n) **`required: false`** in the Object definition, and the control
      carries no `required` attribute -- so the browser's own stage-2a
      check cannot block an empty value. 134971's premise holds.

  (o) **THE LIVE CLIENT-SIDE MESSAGES**, from `urlComplaint()`, composed by
      `complaint()` as `fieldLabelOf(field) + ' ' + message + '.'`:
        * "<label> is not a valid URL - start it with https:// for another
          site, or with / for a page on this one." (EM DASH, not a hyphen)
        * "<label> is not a valid URL - \"<host>\" is not a domain name."
        * "<label> cannot be only spaces."
        * "<label> must not contain spaces."
      ...where `<label>` is "External Link URL" on an English render and
      the Arabic label on an Arabic one. 134969's value
      `almeezan..qa/LawView` takes the FIRST branch (no leading "/", not
      mailto:/tel:, no `https?://` match).

  (p) **THE OBJECT'S ONLY NAMED RULE FOR THIS FIELD IS A FORMAT RULE, NOT A
      LENGTH RULE.** All five active rules on LawEntry, read live:
        External Link URL format  isEmpty(externalLinkUrl) ||
                                  match(externalLinkUrl, "^https?://.*")
        Display Order minimum     displayOrder >= 1
        Law Number length         match(lawNumber, "(?s)^.{0,100}$")
        Law Title length          match(lawTitle, "(?s)^.{0,200}$")
        Law Description length    match(lawDescription, "(?s)^.{0,500}$")
      **There is NO length rule for External Link URL at all**, and the
      field carries NO `maxLength` objectFieldSetting (so the page's
      `applyMaxLengths()` sets no `maxlength` attribute and attaches no
      counter -- confirmed live, zero `[data-qc-oel-counter]` on the whole
      form). What the form DOES declare is the INPUTS-text fragment's own
      `"maxLength": 280` for `ObjectField_externalLinkUrl` -- Liferay's
      default Text width. **134970's premise that the boundary is 500 is
      therefore very likely wrong by 220 characters**, and its step 2 is
      expected to fail. Note also that the fragment enforces its 280 on
      `keyup` only, which `fill()` does not fire -- so the box will hold
      500 characters and the refusal, if any, comes from the server.
      The `isEmpty(...) ||` half of the format rule is a second,
      independent confirmation that an EMPTY value is legal -- 134971.

  (q) **The accessible name is locale-dependent, unlike its siblings.**
      The Object labels this field `{en_US: "External Link URL",
      ar_SA: "\u0631\u0627\u0628\u0637 \u0627\u0644\u0646\u0635 \u0627\u0644\u0642\u0627\u0646\u0648\u0646\u064a \u0627\u0644\u062e\u0627\u0631\u062c\u064a"}`, where
      lawNumber/lawTitle/lawDescription happen to carry ASCII Arabic labels
      ("Law Number (AR)" etc.). Counted live on an Arabic render:
      "External Link URL" resolves ZERO controls, the Arabic label resolves
      exactly ONE. Both are constants on `ChambersLawAdminPage`, and every
      batch-5 navigation pins its locale so the resolution is never left to
      a session that has drifted.

  (r) The 1990 record's live baseline at probe time:
      `https://www.almeezan.qa/LawView.aspx?opt&LawID=2541`, record
      `(approved)`. The PUBLIC page renders that stored value NORMALIZED as
      `...?opt=&LawID=2541&language=en` -- an `=` added to the valueless
      `opt` and a `language` parameter appended. Nothing below compares a
      public href to a stored URL by equality; that exact mistake is why
      TC 134877 fails. 134968 reads back from the CMS only.

  [!] EXPECTED TO FAIL, and scripted to the case ANYWAY (Result Integrity):
      **134969** on its message literal (both steps) -- the case demands
      "Please enter a valid URL." / its Arabic twin, and the product says
      the (o) sentences instead. The rest of each step (no success toast,
      nothing stored, a refusal shown at all) is asserted separately and is
      expected to PASS, so the report distinguishes "the product is broken"
      from "the case's literal is wrong".
      **134970** step 2 -- see (p): 500 characters exceeds the 280 the
      fragment declares, with no object rule licensing 500.
      Both produce the exact live strings needed to correct the CASE in
      Azure, the way 134942 was corrected rather than the test loosened.

=========================================================================
BATCHES 6 + 7 -- Display Order, Active Status, Law Entry ID
what the LIVE page/object actually say (probed 2026-09-16)
=========================================================================
Read off `manage-law-entry?editEntry=QCDEMO-129394-law-11-1990` (and the
1996 sibling) with a scoped, READ-ONLY CLI Playwright probe -- DOM reads,
`fill()`/keyboard into the Display Order box with NO save, never a Save or
Submit click, never the Playwright MCP -- authenticated via `.auth/state.json`
at 1920x1080, `/en` and `/ar` pinned, plus the Object's own rule catalogue in
cms/liferay-context.md (LawEntry, id 78508).

  (s) **DISPLAY ORDER IS `<input type="number">`, AND ITS `min` IS NOT 1.**
      Read live, verbatim: `name="ObjectField_displayOrder"`, `type="number"`,
      `required`, **`min="-2147483648"`**, `max="2147483647"`, NO `step`
      attribute. Accessible name `Display Order` on an `/en` render and
      `ترتيب العرض` on an `/ar` one (count == 1 each). That single attribute
      decides WHICH LAYER refuses what, and it is the finding the whole of
      134973/134974/134975 turns on. Measured, per value, on the live
      control (`el.validity` + `el.validationMessage`, no save):

        value   entered by      validity             native message
        ------  --------------  -------------------  ----------------------
        "0"     fill()          **VALID**            "" (none)
        "-1"    fill()          **VALID**            "" (none)
        "2.5"   fill()          stepMismatch         "Please enter a valid
                                                      value. The two nearest
                                                      valid values are 2 and
                                                      3."
        "2.5"   keyboard.type   **box holds "25"**   "" -- the control
                                                      DISCARDS the "."
        "two"   fill()          Playwright REFUSES: "Cannot type text into
                                input[type=number]"
        "two"   keyboard.type   **box stays EMPTY**  "Please fill out this
                                (valueMissing)        field."
        ""      fill()          valueMissing         "Please fill out this
                                                      field."

      Consequences, and they are all different from one another:
        * **0 and -1 pass the browser's own check** (stage 2a) because
          `min` is INT_MIN. The ONLY thing that can refuse them is the
          Object's named rule (stage 2b, the `/validate` pre-flight) --
          see (t). 134973 is therefore a `/validate` test, not a native one.
        * **2.5 never reaches the server.** `reportValidity()` blocks the
          submit natively on `stepMismatch` (a number input's implicit step
          is 1), and a native bubble is NOT in the DOM -- the only
          observable trace is the control's own `validationMessage`.
        * **"two" is not enterable at all.** The box refuses the keystrokes
          and stays empty, so the save is then blocked as a MISSING value,
          not as a malformed one. "The box would not accept it" is a real,
          reportable outcome and it is NOT the same as "the save was
          refused" -- 134974 step 3 reports which one happened.
        * **An empty box is blocked natively** (`required` + valueMissing),
          exactly like the empty Law Number of 134945. 134975 is a stage-2a
          test.

  (t) **THE OBJECT'S ONLY DISPLAY-ORDER RULE IS A MINIMUM, AND THERE IS NO
      UNIQUENESS RULE ANYWHERE ON THIS OBJECT.** All five active rules on
      LawEntry (id 78508), with BOTH shipped error labels:

        External Link URL format  isEmpty(externalLinkUrl) ||
                                  match(externalLinkUrl, "^https?://.*")
          EN "External Link URL must start with http:// or https://"
          AR "يجب أن يبدأ الرابط الخارجي بـ http:// أو https://"
        **Display Order minimum   displayOrder >= 1**
          EN **"Display Order must be 1 or greater"**
          AR **"يجب أن يكون ترتيب العرض 1 أو أكبر"**
        Law Number length         match(lawNumber, "(?s)^.{0,100}$")
        Law Title length          match(lawTitle, "(?s)^.{0,200}$")
        Law Description length    match(lawDescription, "(?s)^.{0,500}$")

      Read live off the definition + cms/liferay-context.md's LawEntry
      catalogue. (The `/o/object-admin/.../object-validation-rules` and
      `.../validate` endpoints both answer **403** to a plain authenticated
      `fetch()` from the page -- the form's own `send()` helper adds the
      portal auth token this probe did not -- so the rule TEXT below comes
      from the catalogue, and the *behaviour* below comes from live data.)

      Because the message contains the words "Display Order", the page's
      own `controlForMessage()` ties it to the control and
      `reportComplaints()` renders it UNDER THE BOX as
      `<div data-qc-oel-field-error role="alert">`, NOT in the red bar.
      **Every Display Order assertion below therefore reads through the
      WIDENED reader** (`save_refusal_text()` = field notes + fragment
      notes + bar). A bar-only read would return "" and report a working
      product as a silent refusal -- which is precisely the mistake that
      produced, and then retracted, bug #141989.

  (u) **A DUPLICATE DISPLAY ORDER IS ACCEPTED -- and the live data already
      proves it.** There is no uniqueness rule in the five above, no
      `unique` objectFieldSetting on `displayOrder`, and no client-side
      duplicate check anywhere in the page's shipped JS (grepped live: the
      only "duplicate"/"already uses" strings belong to the DEPARTMENT name
      guard and the double-submit guard, neither of which names this
      field). Confirmed by the live records themselves:

        QCDEMO-129394-law-11-1990   Display Order **200**   Approved, active
        QCDEMO-129394-law-11-1996   Display Order **200**   Approved, active

      -- BOTH entries hold the SAME Display Order right now, both are
      published, and the public page renders BOTH cards (1990 first, 1996
      second). That state is already known and already flagged for a human
      in `test_chambers_law_control_panel.py`'s tc_134886 comment block
      ("a previous run's restore did not commit ... their relative public
      order is arbitrary"), and it is left as found here -- repairing real
      editorial numbering is a content decision, not a test's.
      **134987's expected result ("Save is blocked ... the Display Order is
      already in use") is therefore expected to FAIL**, and it is scripted
      as written anyway. What the product actually does is: accept the
      duplicate, publish it, and render the two cards in an arbitrary
      (insertion-ordered) sequence.

  (v) **134987's stated PRECONDITION IS NOT TRUE OF THE LIVE DATA.** The
      case opens with "an existing active entry 'Law No. 11 of 1990'
      holding Display Order 1"; live, it holds 200. The test therefore
      ESTABLISHES that precondition itself -- it writes 1 to the 1990
      record first, as a disclosed, TEST_OWNED setup step -- because
      without it "enter the Display Order already used by another entry"
      would mean writing 200 onto a record that already holds 200, i.e.
      testing nothing at all. Both records' Display Order + status are
      captured at runtime and restored in `finally`, and the PUBLIC page is
      then re-checked for two cards in their original order.

  (w) **DISPLAY ORDER 2 CONTRADICTS THE GUIDE'S NUMBERING CONVENTION, and
      is written anyway here.** OBJECT-AUTHORING-GUIDE.md §3 and the
      Content Admin Guide both say ordering is in multiples of 100. TC
      134886 was ESCALATED over exactly this and performs its reorder with
      100/200 instead of the case's 1/2 -- correctly, because that test
      leaves a PERMANENT reordering of real content. 134972/134987 are the
      opposite shape: the value is transient, written and then restored to
      the captured baseline in the same test, so the case's own literals
      (2, and 1 then 2) are mirrored EXACTLY rather than substituted. The
      convention conflict is reported, not silently resolved.

  (x) **ACTIVE STATUS is `<input type="checkbox" name="ObjectField_activeStatus">`**
      -- accessible name `Active Status` (`/en`) / `الحالة النشطة` (`/ar`),
      `required: false`, currently **ticked** on both live records. Driven
      with `set_checkbox()` / `is_checked()`, never `fill_text()`.
      Un-ticking it REMOVES THE CARD FROM THE LIVE PUBLIC PAGE -- that is
      the documented purpose of the field (guide §4/§8) and is exactly what
      the sibling module's tc_134887 proves live. So:
        * **134977** takes a live card off the site for the duration of the
          test, and **134976** does too -- its case demands a record that
          OPENS with Active Status False, and both live records open True,
          so the test must first set False (a disclosed precondition write)
          before it can set True. Both tests restore the captured baseline
          AND then re-check the anonymous public page for two cards in the
          original order before finishing.

  (y) **THERE IS NO LAW ENTRY ID CONTROL ON THIS FORM -- AT ALL.** Read
      live, every non-hidden control the form renders, in order:
      `Law Number`, `Law Number — العربية *`, `Law Title`,
      `Law Title — العربية *`, `Law Description`,
      `Law Description — العربية *`, `External Link URL`, `Law Icon`
      (`ObjectField_lawIcon`), `Display Order`, `Active Status`. A scan of
      every `label`/`legend`/`th`/`.form-group` for the word "ID" or
      "Identifier" returns **ZERO** matches. The record's identity lives
      outside the form: the entries list carries it as the row's own
      `data-qc-oel-delete` handle and as the `?editEntry=<code>` external
      reference code on the row's Edit link. **134978's expected result
      explicitly permits this** ("it is read-only **or absent** from the
      edit form"), so the absence is the finding, not a failure to locate a
      control -- and the test asserts the absence positively instead of
      timing out hunting for a field that does not exist.

  (z) **134978 CREATES TWO RECORDS AND, PER STANDING PROJECT RULE, NEVER
      DELETES THEM.** Both are created with **Active Status UN-TICKED**, so
      neither can ever reach the public page (proved by tc_134887's own
      live result), and with Display Orders 9100/9200 -- multiples of 100,
      far past the real content, per the guide's convention. Their payload
      carries a per-run timestamp so a rerun cannot collide with the
      previous run's rows. Disclosed, deliberate consequence, identical to
      the sibling module's tc_134884: each run leaves two more hidden
      QCTEST rows in the CMS list. The test re-checks the public page for
      exactly the two original cards before it finishes.

  [!] EXPECTED TO FAIL, and scripted to the case ANYWAY (Result Integrity
      -- an assertion is never loosened to match observed behaviour):
      **134987** step 2/3 -- see (u): there is no uniqueness rule, so the
      duplicate is expected to be accepted and stored.
      **134974** step 3 -- see (s): the box discards the letters of "two"
      entirely, so the save is blocked as a MISSING value and no
      integer-FORMAT message is ever produced. The step's assertion
      separates "the save was blocked" (expected to pass) from "with an
      integer-format validation error" (expected to fail), so the report
      distinguishes a product defect from a case-wording defect.
      Both produce the exact live strings needed to correct the CASE in
      Azure, the way 134942 was corrected rather than the test loosened.

  Message language: no batch-6/7 case demands a literal message, so the
  Display Order minimum assertion matches the Object's OWN named-rule error
  label in EITHER shipped language -- which identifies the rule precisely
  without depending on the UI's language. Every navigation is locale-pinned
  to `/en` anyway (this account's own Liferay language is `ar_SA`, which
  moves both the labels and the message language -- see batch 5).

  Helper note, and it is a deliberate deviation: `_wait_for_committed_value()`
  and `_observed_stored_value()` read through `field_value()`, which is
  bound to the **textbox** role. Display Order is a **spinbutton** and
  Active Status a **checkbox**, so those two helpers resolve ZERO controls
  here and CANNOT be reused as-is. `_observed_stored_number()` and
  `_observed_stored_checkbox()` below are their exact twins -- same polling
  contract, same "return the last value observed, let the caller assert"
  rule -- differing only in which read they call.

-- TEST DATA ------------------------------------------------------------
Every case here edits `QCDEMO-129394-law-11-1990`, a REAL, published
editorial record (its card is live on the public Chamber's Law page).
TEST_OWNED, without exception: the baseline value is read off the record at
runtime immediately before the mutation, restored in `finally`, and the
restore is then PROVED by re-reading it from a fresh navigation -- never
assumed. `_test_owned_reset()` retries the restore and, if the test body
itself passed, fails the test rather than leaving a shared record dirty.
A previous batch's unproved restore left a record in Draft and knocked a
card off the live public page; that is what these guards exist to prevent.

134943 is the one case that would CREATE a record. Its save is expected to
be BLOCKED, so it should create nothing, and the test asserts that. Its
payload nevertheless ships with `Active Status` un-ticked, so that even an
unexpected save can never publish a QCTEST card to the live site. Nothing
is ever deleted (standing project rule): if a row does appear, it is left
in place and reported loudly.

-- xdist ----------------------------------------------------------------
Every test here carries `@pytest.mark.xdist_group("chambers_law_129394")` --
the SAME group the sibling module uses -- so `--dist loadgroup` can never
schedule two writers of this shared record on different workers at once.

-- FIXTURES -------------------------------------------------------------
The five icon files are GENERATED deterministically (byte-exact, no RNG,
no Pillow) into `cms/tests/chambers_law/fixtures/generated/` by the
`law_icon_fixtures` fixture below, so multi-megabyte binaries never enter
git. See `_write_icon_fixtures()`.

-- TIMINGS (measured live, qcdev, 2026-09-15) ---------------------------
Unpublish -> Draft ~1.2-1.4 s; Submit for Publishing -> Approved 27-30 s;
`load` and `networkidle` never fire on this surface (the budgets below are
sized from those measurements, and every wait is a real condition).
"""

import re
import struct
import sys
import zlib
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlsplit

import allure
import pytest

from cms.pages.chambers_law.chambers_law_admin_page import (
    ChambersLawAdminPage,
    LAW_1990_ENTRY_CODE,
    LAW_1990_NUMBER,
    LAW_1990_TITLE,
    # Batch 6 only: 134987 is the one case in this module that needs a
    # SECOND record -- it sets a Display Order already held by another
    # entry, which takes two entries to mean anything.
    LAW_1996_ENTRY_CODE,
    LAW_1996_NUMBER,
)
# Batch 5 only: TC 134971 step 3 leaves the CMS and reads the PUBLIC page as
# a genuine anonymous visitor -- the same pairing the sibling module already
# uses for every "prove a visitor sees it" step.
from web.pages.chambers_law.chambers_law_page import ChambersLawPage
from core.web.browser import new_context
from core.utils.logger import get_logger
from core.utils.waits import wait_until

logger = get_logger("test_chambers_law_field_validation")

# Same group as test_chambers_law_control_panel.py -- these tests write the
# same shared records, so they must serialize against those too.
CHAMBERS_LAW_XDIST_GROUP = pytest.mark.xdist_group("chambers_law_129394")

# ---- Wait budgets (see module docstring's measured timings) --------------
UNPUBLISH_CONFIRM_TIMEOUT = 30.0
PUBLISH_CONFIRM_TIMEOUT = 120.0
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
RESTORE_ATTEMPTS = 3


# =========================================================================
# Deterministic icon fixtures
# =========================================================================
# CONSOLIDATE: byte-exact image builders are generic test-asset tooling, not
# Chamber's-Law knowledge. They belong in a shared helper (e.g.
# `core/utils/image_fixtures.py`) once this batch and the sibling module are
# merged -- PBI 129398's org_structure fixtures currently solve the same
# problem by COMMITTING a 2 MB and a 2.8 MB binary, which these replace.

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "generated"

ONE_KB = 1024
ONE_MB = 1024 * 1024

# Names mirror the case text exactly (134940-134942). 134942 is at rev 2:
# 1 MB / 1.1 MB / 0.5 MB, NOT the 2 MB / 2.1 MB / 1.5 MB of rev 1.
ICON_SVG_NAME = "law-icon.svg"
ICON_GIF_NAME = "law-icon.gif"
ICON_1MB_NAME = "icon-1mb.png"
ICON_OVERSIZE_NAME = "icon-oversize.png"
ICON_0_5MB_NAME = "icon-0_5mb.png"

ICON_SVG_SIZE = 40 * ONE_KB             # "SVG, 40 KB"
ICON_GIF_SIZE = 80 * ONE_KB             # "GIF, 80 KB"
# 1 MB == 1048576 bytes (BINARY megabyte) -- see the [OPEN] note under
# finding (i) in the module docstring: the picker declares `maxFileSize: 1`
# as a COUNT of MB and applies the multiplier in product code this repo
# does not contain, so the boundary file is the one value in this batch
# that depends on which megabyte the product means.
ICON_1MB_SIZE = 1 * ONE_MB              # "PNG, exactly 1 MB"  -> 1048576
ICON_OVERSIZE_SIZE = int(1.1 * ONE_MB)  # "PNG, 1.1 MB"        -> 1153433
ICON_0_5MB_SIZE = ONE_MB // 2           # "PNG, 0.5 MB"        ->  524288


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _png_bytes(total_size: int) -> bytes:
    """A REAL, decodable 1x1 truecolour PNG padded to EXACTLY `total_size`
    bytes with a private ancillary chunk (`qcPd` -- ancillary / private /
    safe-to-copy per the PNG chunk-naming rules, so every decoder skips it
    and the file stays valid). Padding INSIDE a chunk, rather than trailing
    junk after IEND, is what keeps it a valid PNG at an exact size -- which
    matters because 134942 is a BOUNDARY case and "exactly 1 MB" has to
    mean exactly 1048576 bytes, not "about 1 MB"."""
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = _png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00", 9))
    iend = _png_chunk(b"IEND", b"")
    fixed = len(signature) + len(ihdr) + len(idat) + len(iend)
    pad_len = total_size - fixed - 12  # 12 = the pad chunk's own length+tag+crc
    if pad_len < 0:
        raise ValueError(f"{total_size} bytes is too small for a valid PNG")
    return signature + ihdr + _png_chunk(b"qcPd", b"\x00" * pad_len) + idat + iend


def _gif_bytes(total_size: int) -> bytes:
    """A REAL, decodable 1x1 GIF89a padded to EXACTLY `total_size` bytes
    with a Comment Extension (a first-class GIF block, so the file stays
    valid rather than being a PNG with a renamed extension -- 134941 is
    about the product rejecting a genuine GIF, which a fake one would not
    prove)."""
    header = (
        b"GIF89a"
        + struct.pack("<HH", 1, 1)
        + bytes([0x80, 0x00, 0x00])           # global colour table, 2 entries
        + b"\x00\x00\x00" + b"\xff\xff\xff"   # black, white
    )
    # Image Descriptor + LZW (clear, pixel 0, EOI packed LSB-first) + trailer.
    body = (
        b"\x2c" + struct.pack("<HHHH", 0, 0, 1, 1) + b"\x00"
        + b"\x02" + b"\x02\x44\x01" + b"\x00"
        + b"\x3b"
    )
    # Comment Extension: 0x21 0xFE + sub-blocks + 0x00 terminator.
    remaining = total_size - len(header) - len(body) - 3
    if remaining < 1:
        raise ValueError(f"{total_size} bytes is too small for a padded GIF")
    blocks = b""
    while remaining > 0:
        if remaining >= 258:
            size = 255
        elif remaining == 257:
            size = 200  # never leave exactly 1 byte: a sub-block costs >= 2
        else:
            size = remaining - 1
        blocks += bytes([size]) + b"Q" * size
        remaining -= size + 1
    return header + b"\x21\xfe" + blocks + b"\x00" + body


def _svg_bytes(total_size: int) -> bytes:
    """A REAL SVG padded to EXACTLY `total_size` bytes inside an XML
    comment."""
    head = (
        b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" '
        b'viewBox="0 0 64 64"><rect width="64" height="64" fill="#8a1538"/><!-- '
    )
    tail = b" --></svg>"
    pad = total_size - len(head) - len(tail)
    if pad < 0:
        raise ValueError(f"{total_size} bytes is too small for a padded SVG")
    return head + b"Q" * pad + tail


def _write_icon_fixtures() -> dict:
    """Writes the five icon fixtures byte-exactly, rewriting any file whose
    size has drifted. Deterministic: the same bytes on every machine and
    every run, so a boundary case can never be decided by an accident of
    compression."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    spec = {
        ICON_SVG_NAME: (_svg_bytes, ICON_SVG_SIZE),
        ICON_GIF_NAME: (_gif_bytes, ICON_GIF_SIZE),
        ICON_1MB_NAME: (_png_bytes, ICON_1MB_SIZE),
        ICON_OVERSIZE_NAME: (_png_bytes, ICON_OVERSIZE_SIZE),
        ICON_0_5MB_NAME: (_png_bytes, ICON_0_5MB_SIZE),
    }
    paths = {}
    for name, (builder, size) in spec.items():
        path = FIXTURES_DIR / name
        if not path.exists() or path.stat().st_size != size:
            path.write_bytes(builder(size))
        if path.stat().st_size != size:
            raise AssertionError(
                f"fixture {name} is {path.stat().st_size} bytes, expected "
                f"exactly {size} -- a boundary case cannot run on an "
                "approximate file"
            )
        paths[name] = str(path)
    return paths


@pytest.fixture(scope="session")
def law_icon_fixtures():
    """Session-scoped so the 1 MB / 1.1 MB / 0.5 MB files are built once."""
    return _write_icon_fixtures()


# =========================================================================
# The three shapes a save can land in
# =========================================================================
# A save that does not go through has two genuinely DIFFERENT product
# shapes -- refused WITH a message and refused SILENTLY -- and which one it
# is decides whether there is a bug to file at all. Before the refusal
# reader was widened (2026-09-15) they were indistinguishable, because the
# reader could only see the red bar: every message the page renders UNDER
# the box came back as "" and was reported as silence. Bug #141989 was filed
# on exactly that mistake and is now closed as Not a Bug.
#
# Named constants, not free text, so a failure report says the same thing
# every time and a bug write-up can be grepped back to the shape it claims.
REFUSED_WITH_MESSAGE = (
    "REFUSED WITH A MESSAGE -- the value was not stored and the page said why"
)
REFUSED_SILENTLY = (
    "REFUSED SILENTLY -- the value was not stored and the page said NOTHING, "
    "in ANY of its three renderers (under-the-box note, red bar, Liferay "
    "fragment error)"
)
ACCEPTED_AND_STORED = (
    "ACCEPTED AND STORED -- the record now holds exactly what was typed"
)
UNCLEAR_OUTCOME = (
    "UNCLEAR -- the record does not hold what was typed, yet the page "
    "reported a SUCCESS and no refusal; read the per-renderer breakdown"
)


def _outcome_shape(refusal: str, success: str, attempted: str, stored: str) -> str:
    """Names which of the three shapes a save landed in.

    PURE -- it takes the strings the caller ALREADY captured off the page
    (through the widened `_LawEntryForm.save_refusal_text()` /
    `.success_message_text()`) plus the value the record actually holds, and
    computes nothing from the live DOM. That matters: by the time a test can
    read the committed value it has navigated away, and re-reading the
    message from the re-rendered form would report the wrong page.

    "Silently" therefore means one specific, checkable thing: NOTHING in any
    of the three renderers -- not merely nothing in the red bar."""
    if stored == attempted:
        return ACCEPTED_AND_STORED
    if refusal:
        return REFUSED_WITH_MESSAGE
    if not success:
        return REFUSED_SILENTLY
    return UNCLEAR_OUTCOME


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
SIZE_REJECTION_RE = re.compile(
    r"valid\s+file\s+size\s+no\s+larger\s+than\s*[0-9]+(?:[.,][0-9]+)?\s*MB",
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
        self._authoring.submit_for_publishing()
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


# =========================================================================
# Lifecycle + TEST_OWNED restore helpers
# =========================================================================
# CONSOLIDATE: _unpublish_and_confirm / _publish_and_confirm /
# _test_owned_reset carry byte-for-byte the same contracts as the sibling
# module's. One copy should survive the merge -- ideally promoted out of
# both test modules into a shared CMS test-support module.

def _unpublish_and_confirm(authoring):
    """Takes the record off the live site and PROVES it landed in Draft.
    Idempotent: a record already in Draft is left alone."""
    if authoring.current_status() == "Approved":
        authoring.unpublish_to_edit_as_draft()
    authoring.wait_for_status("Draft", timeout=UNPUBLISH_CONFIRM_TIMEOUT)
    return authoring


def _publish_and_confirm(authoring):
    """Submits for publishing and PROVES the record reached Approved."""
    authoring.submit_for_publishing()
    authoring.wait_for_status("Approved", timeout=PUBLISH_CONFIRM_TIMEOUT)
    return authoring


def _wait_for_committed_value(
    admin, entry_code, field_label, expected, timeout=PUBLISH_CONFIRM_TIMEOUT
):
    """Polls a FRESH navigation until the record really stores `expected`.

    This, not the status, is the commit proof for every case here: these
    records are already Approved and STAY Approved across a Submit for
    Publishing, so `wait_for_status("Approved")` would return on its first
    poll without proving anything was written. Measured live: the publish
    itself takes 27-30s, an order of magnitude past the form's own ~2.5s
    settle."""

    def _committed() -> bool:
        return admin.open_law_entry(entry_code).field_value(field_label) == expected

    wait_until(
        _committed,
        timeout=timeout,
        poll=3.0,
        message=(
            f"{field_label!r} on {entry_code} never committed to the expected "
            "value after Submit for Publishing"
        ),
    )


def _observed_stored_icon(
    admin, entry_code, field_label, stem, timeout=PUBLISH_CONFIRM_TIMEOUT
) -> str:
    """Polls a FRESH navigation until the record's stored icon name carries
    `stem`, and returns the LAST name observed -- match or no match.

    Nothing is swallowed: the caller ASSERTS on the returned name, so a file
    that never committed is reported as the real value the record holds
    instead of an opaque timeout. The poll exists because Submit for
    Publishing takes 27-30s here (measured), so a single read straight after
    the click would be a race, not a check."""
    observed = {"name": ""}

    def _committed() -> bool:
        observed["name"] = admin.open_law_entry(entry_code).current_file_name(
            field_label
        )
        return stem in observed["name"]

    try:
        wait_until(_committed, timeout=timeout, poll=3.0)
    except Exception:  # noqa: BLE001 -- the last observed name IS the result
        pass
    return observed["name"]


def _test_owned_reset(restore_fn, label: str, attempts: int = RESTORE_ATTEMPTS) -> None:
    """Runs a TEST_OWNED restore so that it cannot fail silently.

    Retries (restores are idempotent, so retrying is always safe), attaches
    the full trail to Allure on total failure, and re-raises ONLY when no
    exception is already propagating -- so a restore failure never MASKS a
    real product failure, and a green test can never quietly leave a shared
    record broken for the tests that follow it."""
    propagating = sys.exc_info()[0] is not None
    errors = []
    for attempt in range(1, attempts + 1):
        try:
            restore_fn()
            if errors:
                logger.warning(
                    "TEST_OWNED reset %r succeeded on attempt %d after: %s",
                    label,
                    attempt,
                    " | ".join(errors),
                )
            return
        except Exception as exc:  # noqa: BLE001 -- retried, then reported loudly
            errors.append(f"attempt {attempt}: {exc!r}")

    detail = (
        f"TEST_OWNED RESET FAILED for {label} after {attempts} attempts.\n"
        "The shared qcdev record may be left in a non-baseline state, which "
        "will break the PRECONDITIONS of other tests in this module and in "
        "test_chambers_law_control_panel.py.\n" + "\n".join(errors)
    )
    logger.error(detail)
    try:
        allure.attach(detail, name=f"TEST_OWNED RESET FAILED - {label}")
    except Exception:  # noqa: BLE001 -- reporting must never mask anything
        pass
    if not propagating:
        raise AssertionError(detail)


def _restore_law_entry_text(
    admin, entry_code, field_label, baseline_value, baseline_status
):
    """Puts one text field back to the value captured at runtime, then
    PROVES it by re-reading the record from a fresh navigation. Also
    restores the record's publication status."""

    def _restore():
        authoring = admin.open_law_entry(entry_code)
        if authoring.field_value(field_label) != baseline_value:
            if authoring.current_status() == "Approved":
                authoring.fill_text(field_label, baseline_value)
                _publish_and_confirm(authoring)
            else:
                _unpublish_and_confirm(authoring)
                authoring.fill_text(field_label, baseline_value)
                if baseline_status == "Approved":
                    _publish_and_confirm(authoring)
                else:
                    authoring.save_as_draft()

        # PROVE it -- fresh navigation, never a post-save-reflowed DOM.
        authoring = admin.open_law_entry(entry_code)
        actual_value = authoring.field_value(field_label)
        actual_status = authoring.current_status()
        if actual_value != baseline_value:
            raise AssertionError(
                f"TEST_OWNED restore did not commit: {field_label!r} reads "
                f"{actual_value!r}, expected the captured baseline "
                f"{baseline_value!r}"
            )
        if actual_status != baseline_status:
            raise AssertionError(
                f"TEST_OWNED restore did not commit: {entry_code} status is "
                f"{actual_status!r}, expected the captured baseline "
                f"{baseline_status!r}"
            )

    return _restore


def _restore_law_icon(
    admin, entry_code, baseline_bytes_path, baseline_file_name, baseline_status
):
    """Byte-for-byte restore of the Law Entry's own `Law Icon`, from the
    real bytes downloaded off the record's own `Download` link BEFORE
    anything was mutated, then a PROVED re-read.

    A DIRECT `upload_file()` over whatever the field currently holds is the
    correct path (see `ObjectAuthoringPage.remove_current_file()`'s
    docstring: the two-phase remove+save dance is only needed to reach a
    genuinely EMPTY field; a straight replace persists in one save).
    Re-uploading mints a FRESH Documents & Media document rather than
    re-linking the original, so the restored file is byte-identical but may
    be named `law-icon (1).svg` -- a disclosed, accepted side effect, which
    is why the verification matches the file STEM."""

    def _restore():
        authoring = admin.open_law_entry(entry_code)
        if baseline_bytes_path:
            current = authoring.current_file_name(admin.LAW_ICON_UPLOAD_LABEL)
            stem = baseline_file_name.rsplit(".", 1)[0] if baseline_file_name else ""
            if not stem or stem not in current:
                if authoring.current_status() != "Approved":
                    _unpublish_and_confirm(authoring)
                authoring.upload_file(admin.LAW_ICON_UPLOAD_LABEL, baseline_bytes_path)
                _publish_and_confirm(authoring)

        authoring = admin.open_law_entry(entry_code)
        actual_status = authoring.current_status()
        if actual_status != baseline_status:
            raise AssertionError(
                f"TEST_OWNED restore did not commit: {entry_code} status is "
                f"{actual_status!r}, expected {baseline_status!r}"
            )
        if baseline_file_name:
            stem = baseline_file_name.rsplit(".", 1)[0]
            restored = authoring.current_file_name(admin.LAW_ICON_UPLOAD_LABEL)
            if stem not in restored:
                raise AssertionError(
                    "TEST_OWNED restore did not commit: Law Icon reads "
                    f"{restored!r}, expected the original {baseline_file_name!r} "
                    "(or a Liferay-deduplicated variant of it)"
                )

    return _restore


# =========================================================================
# Case data -- mirrored from the approved cases, verbatim where they give a
# literal, deterministic where they describe one ("a 100-character string")
# =========================================================================
LAW_NUMBER_EN_VALID = "Law No. 11 of 1990"              # 134944, verbatim
LAW_NUMBER_AR_VALID = "القانون رقم 11 لسنة 1990"         # 134948, verbatim
FOUR_SPACES = "    "                                     # 134947 / 134951

# 100/101-character strings. Deterministic and self-describing, so a failure
# report shows WHAT was written, not an opaque run of "A"s.
LAW_NUMBER_EN_100 = ("QCTEST129394-EN-" + "ABCDEFGHIJ" * 10)[:100]
LAW_NUMBER_EN_101 = LAW_NUMBER_EN_100 + "X"
LAW_NUMBER_AR_100 = ("القانون رقم 11 لسنة 1990 اختبار الحد الأقصى " + "ب" * 100)[:100]
LAW_NUMBER_AR_101 = LAW_NUMBER_AR_100 + "ب"

LAW_NUMBER_CAP = 100
# The Object's own named rule, as catalogued in cms/liferay-context.md for
# LawEntry: match(lawNumber, "(?s)^.{0,100}$").
LAW_NUMBER_CAP_MESSAGE = "Law Number must not exceed 100 characters"
# 134942 rev 2's own literal, and the product's own string: read live off
# `data-file-size-feedback` on the Law Entry Icon upload fragment. Asserted
# verbatim -- the detector finds the message language-independently, but the
# CASE demands this English wording, so that is what is checked.
ICON_SIZE_ERROR_MESSAGE = (
    "Please enter a file with a valid file size no larger than 1 MB."
)
# Stems, not full names: a re-upload of a name Liferay already stores is
# de-duplicated to "icon-1mb (1).png" (the same convention 134940 and
# _restore_law_icon() already document).
ICON_1MB_STEM = "icon-1mb"
ICON_0_5MB_STEM = "icon-0_5mb"
PERMITTED_ICON_FORMATS = ("JPG", "PNG", "SVG")

# ---- Batch 3: Law Title -------------------------------------------------
# 134952's literal IS the 1990 record's real Law Title, so the already
# imported `LAW_1990_TITLE` is REUSED here instead of being retyped -- one
# string, one source of truth (134943 asserts on the same constant).
LAW_TITLE_EN_VALID = LAW_1990_TITLE                      # 134952, verbatim
LAW_TITLE_AR_VALID = "تأسيس غرفة قطر للتجارة والصناعة"          # 134956, verbatim

# 200/201-character strings. Deterministic and self-describing, so a failure
# report shows WHAT was written, not an opaque run of "A"s. The cap here is
# 200 -- Law Number's was 100; checked against the Object's own rule rather
# than assumed to mirror it (see finding (b) in the module docstring).
LAW_TITLE_EN_200 = ("QCTEST129394-EN-TITLE-" + "ABCDEFGHIJ" * 20)[:200]
LAW_TITLE_EN_201 = LAW_TITLE_EN_200 + "X"
LAW_TITLE_AR_200 = ("عنوان قانون اختباري للحد الأقصى " + "ب" * 200)[:200]
LAW_TITLE_AR_201 = LAW_TITLE_AR_200 + "ب"

LAW_TITLE_CAP = 200
# The Object's own named rule -- match(lawTitle, "(?s)^.{0,200}$") -- and
# BOTH error labels it ships with (cms/liferay-context.md, LawEntry).
# Matched in either language on purpose: this account leaks Arabic messages
# into an English UI (the live Law Number refusal came back as
# "يجب ألا يتجاوز رقم القانون 100 حرف"), and no batch-3 case demands a
# literal message. Naming the RULE in either shipped language is narrower
# than "some refusal appeared", not looser.
LAW_TITLE_CAP_MESSAGES = (
    "Law Title must not exceed 200 characters",
    "يجب ألا يتجاوز عنوان القانون 200 حرف",
)


def _arabic_label(admin, field_label: str) -> str:
    return field_label + admin.ARABIC_SUFFIX


# The Arabic word that identifies an Arabic field inside a refusal message.
# Derived from the Page Object's own ARABIC_SUFFIX rather than retyped, so
# the two can never drift apart.
ARABIC_FIELD_MARKER = ChambersLawAdminPage.ARABIC_SUFFIX.split()[-1]


# =========================================================================
# BATCH 1 -- Law Entry Icon
# =========================================================================

@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid SVG Law Entry Icon under 2 MB is accepted")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134940
@pytest.mark.traceability("134940")
@allure.label("pbi", "129394")
@allure.label("testcase", "134940")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134940_a_valid_svg_law_entry_icon_under_2_mb_is_accepted(
    page, law_icon_fixtures
):
    # TEST_OWNED: the 1990 entry's CURRENT icon bytes are downloaded off its
    # own Download link before anything is uploaded, and re-uploaded in
    # `finally` -- the binary restore path this object's richer upload
    # widget makes possible (see _restore_law_icon).
    # DISCLOSED (finding iv): the record already holds a file called
    # law-icon.svg, so Liferay will de-duplicate this upload's name to
    # "law-icon (1).svg". The read-back therefore matches the STEM +
    # extension, the same convention the sibling module already uses.
    admin = ChambersLawAdminPage(page)
    icon_path = law_icon_fixtures[ICON_SVG_NAME]
    baseline_file_name = None
    baseline_status = None
    baseline_bytes_path = str(FIXTURES_DIR / "restore_134940_law_icon.bin")

    try:
        with allure.step("Open a law entry record with the Law Entry Icon field available"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            baseline_status = authoring.current_status()
            baseline_file_name = authoring.current_file_name(
                admin.LAW_ICON_UPLOAD_LABEL
            )
            downloaded = authoring.download_current_file(
                admin.LAW_ICON_UPLOAD_LABEL, baseline_bytes_path
            )
            baseline_bytes_path = downloaded or None
            form = _LawEntryForm(authoring)
            icon_field_available = not form.attachment_validation_message(
                admin.LAW_ICON_UPLOAD_LABEL
            )

        with allure.step(
            f"Upload {ICON_SVG_NAME} (SVG, 40 KB) to the Law Entry Icon field and click Save"
        ):
            authoring.upload_file(admin.LAW_ICON_UPLOAD_LABEL, icon_path)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record and read the stored icon"):
            def _icon_committed() -> bool:
                reopened = admin.open_law_entry(LAW_1990_ENTRY_CODE)
                return "law-icon" in reopened.current_file_name(
                    admin.LAW_ICON_UPLOAD_LABEL
                )

            wait_until(
                _icon_committed,
                timeout=PUBLISH_CONFIRM_TIMEOUT,
                poll=3.0,
                message="the uploaded SVG never became the record's stored Law Icon",
            )
            stored_name = admin.open_law_entry(LAW_1990_ENTRY_CODE).current_file_name(
                admin.LAW_ICON_UPLOAD_LABEL
            )

        # Assert
        assert icon_field_available, (
            "expected the law entry record to open with the Law Entry Icon field "
            "available and satisfied"
        )
        assert not refusal, (
            f"the SVG upload was rejected with a validation error: {refusal!r}"
        )
        assert outcome == "saved" and success, (
            "expected the success toast after saving a valid SVG Law Entry Icon; "
            f"the page reported {outcome!r} instead"
        )
        assert stored_name.startswith("law-icon") and stored_name.endswith(".svg"), (
            f"expected the Law Entry Icon field to show {ICON_SVG_NAME} (or a "
            "Liferay-deduplicated variant of it) as the stored image; it reads "
            f"{stored_name!r}"
        )
    finally:
        if baseline_status is not None:
            with allure.step("TEST_OWNED reset -- restore the original Law Icon bytes"):
                _test_owned_reset(
                    _restore_law_icon(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        baseline_bytes_path,
                        baseline_file_name,
                        baseline_status,
                    ),
                    label="tc_134940 Law 1990 Law Icon",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a Law Entry Icon in an unsupported format is rejected")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134941
@pytest.mark.traceability("134941")
@allure.label("pbi", "129394")
@allure.label("testcase", "134941")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134941_a_law_entry_icon_in_an_unsupported_format_is_rejected(
    page, law_icon_fixtures
):
    # No save is ever attempted: the case stops at the upload. The GIF is a
    # REAL, decodable GIF89a (see _gif_bytes) -- a renamed PNG would prove
    # nothing about format rejection.
    # NOT TEST_OWNED by necessity, but read-only in effect: the upload is
    # expected to be refused, and `upload_expecting_rejection()` never
    # clicks `Add`, so nothing can attach. The stored icon is re-read
    # afterwards to PROVE that.
    admin = ChambersLawAdminPage(page)
    gif_path = law_icon_fixtures[ICON_GIF_NAME]

    with allure.step("Open a law entry record with the Law Entry Icon field available"):
        authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
        form = _LawEntryForm(authoring)
        icon_before = authoring.current_file_name(admin.LAW_ICON_UPLOAD_LABEL)

    with allure.step(f"Upload {ICON_GIF_NAME} (GIF, 80 KB) to the Law Entry Icon field"):
        # Default detector -- any string the upload markup declares about
        # ITSELF in a `data-*-feedback` attribute. Narrow by construction,
        # so the account's language-preference notice cannot be read as a
        # rejection here either (see SIZE_REJECTION_RE's block).
        outcome = form.upload_expecting_rejection(
            admin.LAW_ICON_UPLOAD_LABEL, gif_path
        )
        rejection = outcome.rejection
        reported = rejection or outcome.picker_text

    with allure.step("Re-read the record's stored icon"):
        icon_after = admin.open_law_entry(LAW_1990_ENTRY_CODE).current_file_name(
            admin.LAW_ICON_UPLOAD_LABEL
        )

    # Assert
    assert rejection, (
        "expected the GIF upload to be rejected with an image-format validation "
        f"error; the picker reported nothing. Picker text was: {reported!r}"
    )
    named_formats = [
        fmt for fmt in PERMITTED_ICON_FORMATS if fmt.lower() in rejection.lower()
    ]
    assert len(named_formats) == len(PERMITTED_ICON_FORMATS), (
        "expected the image-format validation error to name JPG, PNG and SVG as "
        f"the permitted formats; it named {named_formats} in {rejection!r}"
    )
    assert icon_after == icon_before, (
        "expected the previously stored icon to be unchanged after a rejected "
        f"upload; it went from {icon_before!r} to {icon_after!r}"
    )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a Law Entry Icon above 1 MB is rejected at the size boundary")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134942
@pytest.mark.traceability("134942")
@allure.label("pbi", "129394")
@allure.label("testcase", "134942")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134942_a_law_entry_icon_above_1_mb_is_rejected_at_the_size_boundary(
    page, law_icon_fixtures
):
    """134942 rev 2 -- the 1 MB boundary on the Law Entry Icon.

    Scripted to the CORRECTED case: 1 MB accepted, 1.1 MB rejected with the
    product's own size message, 0.5 MB accepted. Rev 1 of this case asserted
    a 2 MB cap and stated the PBI's 1 MB figure was wrong; the live form
    says 1 MB in three independent places and contains the string "2 MB"
    nowhere, so the CASE was corrected -- see finding (i) in the module
    docstring, including the open question of WHICH megabyte
    (1048576 is used here).

    The rejection is read by `size_rejection_text` only -- see the
    SIZE_REJECTION_RE block: the previous implementation treated ANY text in
    the picker as a rejection and so reported this account's
    language-preference notice as a size rejection, failing step 2 without
    the boundary ever being exercised.

    TEST_OWNED: the record's original icon bytes are downloaded off its own
    Download link before anything is written, re-uploaded in `finally`, and
    the restore is PROVED by re-reading the record.
    """
    admin = ChambersLawAdminPage(page)
    icon_label = admin.LAW_ICON_UPLOAD_LABEL
    exact_1mb = law_icon_fixtures[ICON_1MB_NAME]
    oversize = law_icon_fixtures[ICON_OVERSIZE_NAME]
    half_mb = law_icon_fixtures[ICON_0_5MB_NAME]
    baseline_file_name = None
    baseline_status = None
    baseline_bytes_path = str(FIXTURES_DIR / "restore_134942_law_icon.bin")

    try:
        # ---- Step 1 -----------------------------------------------------
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            baseline_status = authoring.current_status()
            baseline_file_name = authoring.current_file_name(icon_label)
            downloaded = authoring.download_current_file(
                icon_label, baseline_bytes_path
            )
            baseline_bytes_path = downloaded or None
            form = _LawEntryForm(authoring)
            icon_field_available = not form.attachment_validation_message(icon_label)

        # ---- Step 2 -- exactly 1 MB is accepted and saved ----------------
        with allure.step(
            f"Upload {ICON_1MB_NAME} (PNG, exactly 1 MB / {ICON_1MB_SIZE} bytes) "
            "to the Law Entry Icon field and click Submit for Publishing"
        ):
            exact_probe = form.upload_expecting_rejection(
                icon_label, exact_1mb, form.size_rejection_text
            )
            exact_rejection = exact_probe.rejection
            exact_outcome = "not-attempted"
            exact_success = ""
            exact_refusal = ""
            exact_stored = ""
            if not exact_rejection:
                # The picker raised no size feedback -- complete the upload
                # the normal way and publish, which is what the step says.
                authoring.upload_file(icon_label, exact_1mb)
                exact_outcome = form.submit_expecting_refusal()
                exact_success = form.success_message_text()
                exact_refusal = form.save_refusal_text()
                exact_stored = _observed_stored_icon(
                    admin, LAW_1990_ENTRY_CODE, icon_label, ICON_1MB_STEM
                )

        # ---- Step 3 -- 1.1 MB is rejected, stored icon unchanged ---------
        with allure.step(
            f"Upload {ICON_OVERSIZE_NAME} (PNG, 1.1 MB / {ICON_OVERSIZE_SIZE} "
            "bytes) to the same field"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            icon_before_oversize = authoring.current_file_name(icon_label)
            oversize_probe = form.upload_expecting_rejection(
                icon_label, oversize, form.size_rejection_text
            )
            oversize_rejection = oversize_probe.rejection
            icon_after_oversize = admin.open_law_entry(
                LAW_1990_ENTRY_CODE
            ).current_file_name(icon_label)

        # ---- Step 4 -- 0.5 MB is accepted and saved ---------------------
        with allure.step(
            f"Upload {ICON_0_5MB_NAME} (PNG, 0.5 MB / {ICON_0_5MB_SIZE} bytes) "
            "to the same field"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            half_probe = form.upload_expecting_rejection(
                icon_label, half_mb, form.size_rejection_text
            )
            half_rejection = half_probe.rejection
            half_outcome = "not-attempted"
            half_success = ""
            half_refusal = ""
            half_stored = ""
            if not half_rejection:
                authoring.upload_file(icon_label, half_mb)
                half_outcome = form.submit_expecting_refusal()
                half_success = form.success_message_text()
                half_refusal = form.save_refusal_text()
                half_stored = _observed_stored_icon(
                    admin, LAW_1990_ENTRY_CODE, icon_label, ICON_0_5MB_STEM
                )

        # ---- Assert -- step 1 -------------------------------------------
        assert icon_field_available, (
            "expected the law entry record to open with the Law Entry Icon "
            "field available and satisfied"
        )

        # ---- Assert -- step 2: exactly 1 MB is accepted and saved --------
        assert not exact_rejection, (
            f"expected the exactly-1 MB file ({ICON_1MB_SIZE} bytes) to be "
            "ACCEPTED at the boundary; the field's own size validation "
            f"rejected it with {exact_rejection!r}. READ THIS BEFORE FILING: "
            "the fixture is 1048576 bytes, i.e. 1 MB read as the BINARY "
            "megabyte. The picker declares `maxFileSize: 1` as a COUNT of "
            "MB and applies the multiplier in product code, so if the "
            "product means 1000000 bytes this file is 48576 bytes OVER the "
            "cap and this rejection is correct behaviour at a different "
            "boundary definition -- not a product bug. Picker text: "
            f"{exact_probe.picker_text!r}"
        )
        assert not exact_refusal, (
            "the exactly-1 MB icon was refused on save with: "
            f"{exact_refusal!r}"
        )
        assert exact_outcome == "saved" and exact_success, (
            "expected the success message after submitting the exactly-1 MB "
            f"Law Entry Icon for publishing; the page reported {exact_outcome!r}"
        )
        assert ICON_1MB_STEM in exact_stored, (
            f"expected the record to store {ICON_1MB_NAME} (or a "
            "Liferay-deduplicated variant of it) after the exactly-1 MB "
            f"upload was saved; the stored icon reads {exact_stored!r}"
        )

        # ---- Assert -- step 3: 1.1 MB is rejected, icon unchanged --------
        assert oversize_rejection, (
            f"expected the 1.1 MB file ({ICON_OVERSIZE_SIZE} bytes) to be "
            "REJECTED with the field's size message; no size feedback was "
            "rendered at all. Note this assertion no longer accepts 'some "
            "text appeared in the picker' as a rejection -- only the size "
            "message itself. Picker text was: "
            f"{oversize_probe.picker_text!r}"
        )
        assert ICON_SIZE_ERROR_MESSAGE in oversize_rejection, (
            f"expected the rejection to read {ICON_SIZE_ERROR_MESSAGE!r}; the "
            f"field rendered {oversize_rejection!r}"
        )
        assert icon_after_oversize == icon_before_oversize, (
            "expected the stored icon to be unchanged after the 1.1 MB "
            f"rejection; it went from {icon_before_oversize!r} to "
            f"{icon_after_oversize!r}"
        )

        # ---- Assert -- step 4: 0.5 MB is accepted and saved --------------
        assert not half_rejection, (
            f"expected the 0.5 MB file ({ICON_0_5MB_SIZE} bytes) to be "
            "accepted -- it is under the cap on either reading of '1 MB' "
            f"(1048576 or 1000000). The field rejected it with "
            f"{half_rejection!r}. Picker text: {half_probe.picker_text!r}"
        )
        assert not half_refusal, (
            f"the 0.5 MB icon was refused on save with: {half_refusal!r}"
        )
        assert half_outcome == "saved" and half_success, (
            "expected the success message after submitting the 0.5 MB Law "
            f"Entry Icon for publishing; the page reported {half_outcome!r}"
        )
        assert ICON_0_5MB_STEM in half_stored, (
            f"expected the record to store {ICON_0_5MB_NAME} (or a "
            "Liferay-deduplicated variant of it) after the 0.5 MB upload was "
            f"saved; the stored icon reads {half_stored!r}"
        )
    finally:
        if baseline_status is not None:
            with allure.step("TEST_OWNED reset -- restore the original Law Icon bytes"):
                _test_owned_reset(
                    _restore_law_icon(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        baseline_bytes_path,
                        baseline_file_name,
                        baseline_status,
                    ),
                    label="tc_134942 Law 1990 Law Icon",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that saving a law entry without an icon is blocked")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134943
@pytest.mark.traceability("134943")
@allure.label("pbi", "129394")
@allure.label("testcase", "134943")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134943_saving_a_law_entry_without_an_icon_is_blocked(page):
    # The save is EXPECTED TO BE BLOCKED, so this case should create
    # nothing -- which the test asserts directly against the Law Entry list.
    #
    # Two live-confirmed blocking mechanisms, both of which ARE "a
    # required-field validation error against Law Entry Icon":
    #   - stage 2a: `Law Icon`'s own control carries `required` on the
    #     create form (it has no `data-qc-oel-has-file`), so
    #     `form.checkValidity()` fails and `reportValidity()` cancels the
    #     submit natively -- readable only as the control's own
    #     `validationMessage`, since a native bubble is not in the DOM.
    #   - stage 2b: the page's own extra check (its comment cites ADO
    #     141925 -- "an Attachment field marked required is not enforced in
    #     the browser") pushes "<Law Icon> is required - upload a file
    #     before publishing." into the red refusal bar.
    # Either satisfies the case; both are checked, and the success toast
    # must be absent either way.
    #
    # SAFETY: the payload ships with Active Status OFF, so even an
    # UNEXPECTED save can never put a QCTEST card on the live public page.
    # DATA POLICY: nothing is ever deleted. If a row does appear, it is left
    # in place and reported loudly.
    import time as _time

    admin = ChambersLawAdminPage(page)
    run_id = _time.strftime("%m%d-%H%M%S")
    qc_number = f"QCTEST-129394 Law No. 98 of 2026 ({run_id})"
    qc_title = f"QCTEST No-Icon Law Entry {run_id} - save expected to be blocked"
    qc_desc = f"QCTEST-129394 created by automated test tc_134943 run {run_id}."

    with allure.step("Confirm the Law Entry list before the attempt"):
        entries = admin.open_law_entries_list()
        assert entries.row_visible(LAW_1990_TITLE), (
            "expected the existing law entries to be listed before attempting a "
            "blocked create"
        )
        row_present_before = entries.row_visible(qc_title)

    with allure.step(
        "Complete every other mandatory field, leaving Law Entry Icon empty"
    ):
        authoring = admin.open_new_law_entry_form()
        form = _LawEntryForm(authoring)
        authoring.fill_text(admin.LAW_NUMBER_LABEL, qc_number)
        authoring.fill_text(_arabic_label(admin, admin.LAW_NUMBER_LABEL), qc_number)
        authoring.fill_text(admin.LAW_TITLE_LABEL, qc_title)
        authoring.fill_text(_arabic_label(admin, admin.LAW_TITLE_LABEL), qc_title)
        authoring.fill_text(admin.LAW_DESCRIPTION_LABEL, qc_desc)
        authoring.fill_text(_arabic_label(admin, admin.LAW_DESCRIPTION_LABEL), qc_desc)
        authoring.fill_text(admin.EXTERNAL_LINK_URL_LABEL, "https://www.almeezan.qa/")
        authoring.fill_number(admin.DISPLAY_ORDER_LABEL, "900")
        authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, False)
        icon_empty = authoring.current_file_name(admin.LAW_ICON_UPLOAD_LABEL) == ""

    with allure.step("Click Save"):
        outcome = form.submit_expecting_refusal()
        refusal = form.save_refusal_text()
        success = form.success_message_text()
        native_message = form.attachment_validation_message(admin.LAW_ICON_UPLOAD_LABEL)

    with allure.step("Check the Law Entry list"):
        entries = admin.open_law_entries_list()
        row_present_after = entries.row_visible(qc_title)

    # Assert
    assert icon_empty, "expected the law entry form to be completed except for the icon"
    assert not success and outcome != "saved", (
        f"expected NO success toast when saving without an icon; got {success!r}"
    )
    blocked_in_banner = (
        admin.LAW_ICON_UPLOAD_LABEL.lower() in refusal.lower()
        and "required" in refusal.lower()
    )
    assert blocked_in_banner or native_message, (
        "expected the save to be blocked with a required-field validation error "
        f"against {admin.LAW_ICON_UPLOAD_LABEL!r}; the refusal bar read "
        f"{refusal!r} and the field reported no browser constraint message"
    )
    assert not row_present_after and not row_present_before, (
        f"expected NO new law entry record named {qc_title!r} in the Law Entry "
        "list after a blocked save -- per the never-delete rule this row has been "
        "LEFT IN PLACE (Active Status is off, so it is not public) and needs a "
        "human decision"
    )


# =========================================================================
# BATCH 2 -- Law Number, English
# =========================================================================

@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid English Law Number is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134944
@pytest.mark.traceability("134944")
@allure.label("pbi", "129394")
@allure.label("testcase", "134944")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134944_a_valid_english_law_number_is_accepted_and_saved(page):
    # DISCLOSED: the case's literal, 'Law No. 11 of 1990', is ALSO the 1990
    # record's current stored value. Writing it to a DIFFERENT record would
    # temporarily mislabel real, published editorial content with another
    # law's number, so the case is executed against the record it belongs
    # to. The save is still a real one (a full fill -> Submit for Publishing
    # -> PUT), and the SUCCESS TOAST is what proves it happened; the reload
    # then proves the punctuation round-tripped intact.
    admin = ChambersLawAdminPage(page)
    label = admin.LAW_NUMBER_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Number (EN) editable"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()
            editable = authoring.field_count(label) == 1

        with allure.step(
            f"Enter {LAW_NUMBER_EN_VALID!r} in Law Number (EN) and click Save"
        ):
            authoring.fill_text(label, LAW_NUMBER_EN_VALID)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record"):
            _wait_for_committed_value(
                admin, LAW_1990_ENTRY_CODE, label, LAW_NUMBER_EN_VALID
            )
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert editable, "expected exactly one editable Law Number (EN) field"
        assert not refusal, f"unexpected validation error: {refusal!r}"
        assert outcome == "saved" and success, (
            f"expected the success toast; the page reported {outcome!r}"
        )
        assert stored == LAW_NUMBER_EN_VALID, (
            f"expected Law Number (EN) to read {LAW_NUMBER_EN_VALID!r} with its "
            f"punctuation preserved; it reads {stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Number (EN)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134944 Law 1990 Law Number (EN)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty English Law Number is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134945
@pytest.mark.traceability("134945")
@allure.label("pbi", "129394")
@allure.label("testcase", "134945")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134945_an_empty_english_law_number_is_rejected_on_save(page):
    # The expected block is stage 2a (the browser's own `required` check):
    # confirmed live, `input[name="ObjectField_lawNumber"]` carries
    # `required`, and Submit for Publishing restores the constraint before
    # calling checkValidity(). A native bubble is not in the DOM, so the
    # observable trace is the control's own validity state -- which is
    # exactly "a required-field validation error against Law Number (EN)".
    admin = ChambersLawAdminPage(page)
    label = admin.LAW_NUMBER_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Number (EN) populated"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step("Clear Law Number (EN) completely and click Save"):
            authoring.fill_text(label, "")
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()
            value_missing = form.is_value_missing(label)
            native_message = form.native_validation_message(label)

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert baseline_value, (
            "precondition: expected the record to open with Law Number (EN) populated"
        )
        assert not success and outcome != "saved", (
            f"expected NO success toast for an empty Law Number (EN); got {success!r}"
        )
        assert value_missing or (label.strip().lower() in refusal.lower()), (
            "expected a required-field validation error against Law Number (EN); "
            f"the browser reported {native_message!r} and the refusal bar read "
            f"{refusal!r}"
        )
        assert stored == baseline_value, (
            f"expected Law Number (EN) to retain {baseline_value!r}; it reads "
            f"{stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Number (EN)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134945 Law 1990 Law Number (EN)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that the English Law Number accepts exactly 100 characters and rejects 101"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134946
@pytest.mark.traceability("134946")
@allure.label("pbi", "129394")
@allure.label("testcase", "134946")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134946_the_english_law_number_accepts_exactly_100_characters_and_rejects_101(
    page,
):
    # The case's step-3 expected result is an EITHER/OR ("the field caps at
    # 100 characters OR a max-length validation error is shown and the value
    # is not saved"). Both halves are checked: the `maxlength` attribute /
    # truncated live value for the cap, and the red refusal bar for the
    # validation error. Confirmed live that this field carries NO `maxlength`
    # and no character counter (the 100 cap is a server-side object
    # validation rule, not a `maxLength` field setting), so the SECOND half
    # is the one this product should satisfy -- but the test accepts either,
    # because the case does.
    admin = ChambersLawAdminPage(page)
    label = admin.LAW_NUMBER_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Number (EN) editable"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step("Enter a 100-character string in Law Number (EN) and click Save"):
            authoring.fill_text(label, LAW_NUMBER_EN_100)
            outcome_100 = form.submit_expecting_refusal()
            refusal_100 = form.save_refusal_text()
            success_100 = form.success_message_text()
            _wait_for_committed_value(
                admin, LAW_1990_ENTRY_CODE, label, LAW_NUMBER_EN_100
            )
            stored_100 = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        with allure.step("Enter a 101-character string in Law Number (EN) and click Save"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            authoring.fill_text(label, LAW_NUMBER_EN_101)
            typed_value = form.live_value(label)
            max_length_attribute = form.max_length_attribute(label)
            outcome_101 = form.submit_expecting_refusal()
            refusal_101 = form.save_refusal_text()
            success_101 = form.success_message_text()
            stored_101 = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert -- step 2
        assert len(LAW_NUMBER_EN_100) == LAW_NUMBER_CAP
        assert not refusal_100, (
            f"the exactly-100-character Law Number (EN) was rejected: {refusal_100!r}"
        )
        assert outcome_100 == "saved" and success_100, (
            "expected the success toast after saving a 100-character Law Number "
            f"(EN); the page reported {outcome_100!r}"
        )
        assert stored_100 == LAW_NUMBER_EN_100

        # Assert -- step 3 (either/or, exactly as the case words it)
        assert len(LAW_NUMBER_EN_101) == LAW_NUMBER_CAP + 1
        capped_by_field = (
            max_length_attribute == str(LAW_NUMBER_CAP)
            or len(typed_value) == LAW_NUMBER_CAP
        )
        rejected_on_save = (
            bool(refusal_101)
            and not success_101
            and stored_101 != LAW_NUMBER_EN_101
        )
        assert capped_by_field or rejected_on_save, (
            "expected the 101st character NOT to be accepted -- either the field "
            f"caps at {LAW_NUMBER_CAP} characters or a max-length validation error "
            f"is shown and the value is not saved. Live: maxlength="
            f"{max_length_attribute!r}, the box held {len(typed_value)} characters, "
            f"the outcome was {outcome_101!r}, the refusal bar read {refusal_101!r}, "
            f"and the record now stores a {len(stored_101)}-character value"
        )
        if rejected_on_save:
            assert LAW_NUMBER_CAP_MESSAGE in refusal_101, (
                f"expected the max-length error to read {LAW_NUMBER_CAP_MESSAGE!r}; "
                f"it read {refusal_101!r}"
            )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Number (EN)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134946 Law 1990 Law Number (EN)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a whitespace-only English Law Number is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134947
@pytest.mark.traceability("134947")
@allure.label("pbi", "129394")
@allure.label("testcase", "134947")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134947_a_whitespace_only_english_law_number_is_rejected_on_save(
    page,
):
    # [!] EXPECTED TO FAIL -- see finding (iii) in the module docstring. Four
    # spaces satisfy the browser's `required` check and the object's
    # `^.{0,100}$` rule, and the page's own "cannot be only spaces" guard is
    # scoped by its own code to url/link/href-named fields only. Scripted as
    # the case states it; the failure is the finding.
    admin = ChambersLawAdminPage(page)
    label = admin.LAW_NUMBER_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Number (EN) editable"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step("Enter four space characters in Law Number (EN) and click Save"):
            authoring.fill_text(label, FOUR_SPACES)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert not success and outcome != "saved", (
            "expected NO success toast for a whitespace-only Law Number (EN); got "
            f"{success!r}"
        )
        assert refusal, (
            "expected the save to be blocked with a required-field validation error "
            "for a whitespace-only Law Number (EN); no refusal was shown"
        )
        assert stored == baseline_value, (
            f"expected Law Number (EN) to retain {baseline_value!r} and NOT be "
            f"stored as blank or spaces; it reads {stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Number (EN)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134947 Law 1990 Law Number (EN)",
                )


# =========================================================================
# BATCH 2 -- Law Number, Arabic
# =========================================================================
# The Arabic half of each bilingual pair is REQUIRED and its rendered label
# carries a trailing " *", so its accessible name is
# 'Law Number - العربية *'. Every lookup below goes through
# `ObjectAuthoringPage.label_pattern()`, whose anchored `^<label>\s*\*?\s*$`
# regex tolerates that asterisk -- an `exact=True` match on
# 'Law Number - العربية' resolves ZERO elements (confirmed live; it is what
# broke TC 134884).

@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Arabic Law Number is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134948
@pytest.mark.traceability("134948")
@allure.label("pbi", "129394")
@allure.label("testcase", "134948")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134948_a_valid_arabic_law_number_is_accepted_and_saved(page):
    # Same disclosure as 134944: the case's literal is the 1990 record's own
    # current Arabic value, so the case runs against the record it belongs
    # to. The save is real; the success toast proves it; the reload proves
    # the Arabic text AND the Latin digits 11 / 1990 round-tripped in order
    # (that digit-order check is the point of this case -- an RTL field is
    # exactly where a bidirectional reorder would show up).
    admin = ChambersLawAdminPage(page)
    label = _arabic_label(admin, admin.LAW_NUMBER_LABEL)
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Number (AR) editable"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()
            editable = authoring.field_count(label) == 1

        with allure.step(
            f"Enter {LAW_NUMBER_AR_VALID!r} in Law Number (AR) and click Save"
        ):
            authoring.fill_text(label, LAW_NUMBER_AR_VALID)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record"):
            _wait_for_committed_value(
                admin, LAW_1990_ENTRY_CODE, label, LAW_NUMBER_AR_VALID
            )
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert editable, "expected exactly one editable Law Number (AR) field"
        assert not refusal, f"unexpected validation error: {refusal!r}"
        assert outcome == "saved" and success, (
            f"expected the success toast; the page reported {outcome!r}"
        )
        assert stored == LAW_NUMBER_AR_VALID, (
            f"expected Law Number (AR) to read {LAW_NUMBER_AR_VALID!r}; it reads "
            f"{stored!r}"
        )
        assert "11" in stored and "1990" in stored, (
            "expected the digits 11 and 1990 to survive intact in the stored "
            f"Arabic Law Number; it reads {stored!r}"
        )
        assert stored.index("11") < stored.index("1990"), (
            "expected the digits 11 and 1990 to be stored in the correct order; "
            f"the value reads {stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Number (AR)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134948 Law 1990 Law Number (AR)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Arabic Law Number is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134949
@pytest.mark.traceability("134949")
@allure.label("pbi", "129394")
@allure.label("testcase", "134949")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134949_an_empty_arabic_law_number_is_rejected_on_save(page):
    # Confirmed live: `#qc-ar-lawNumber` carries `required`, so the expected
    # block is the same stage-2a browser constraint check as 134945.
    admin = ChambersLawAdminPage(page)
    label = _arabic_label(admin, admin.LAW_NUMBER_LABEL)
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Number (AR) populated"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step("Clear Law Number (AR) completely and click Save"):
            authoring.fill_text(label, "")
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()
            value_missing = form.is_value_missing(label)
            native_message = form.native_validation_message(label)

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert baseline_value, (
            "precondition: expected the record to open with Law Number (AR) populated"
        )
        assert not success and outcome != "saved", (
            f"expected NO success toast for an empty Law Number (AR); got {success!r}"
        )
        assert value_missing or ("العربية" in refusal), (
            "expected a required-field validation error against Law Number (AR); "
            f"the browser reported {native_message!r} and the refusal bar read "
            f"{refusal!r}"
        )
        assert stored == baseline_value, (
            f"expected Law Number (AR) to retain {baseline_value!r}; it reads "
            f"{stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Number (AR)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134949 Law 1990 Law Number (AR)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that the Arabic Law Number accepts exactly 100 characters and rejects 101"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134950
@pytest.mark.traceability("134950")
@allure.label("pbi", "129394")
@allure.label("testcase", "134950")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134950_the_arabic_law_number_accepts_exactly_100_characters_and_rejects_101(
    page,
):
    # [!] STEP 3 EXPECTED TO FAIL -- see finding (ii) in the module
    # docstring. The `Law Number length` rule is evaluated against the
    # DEFAULT-locale value, and the Arabic control carries no `name`
    # attribute, so it is not part of the `/validate` payload at all; nor
    # does it carry a `maxlength` (confirmed live). Neither half of the
    # case's either/or is likely to hold for Arabic. Scripted as the case
    # states it.
    admin = ChambersLawAdminPage(page)
    label = _arabic_label(admin, admin.LAW_NUMBER_LABEL)
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Number (AR) editable"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Enter a 100-character Arabic string in Law Number (AR) and click Save"
        ):
            authoring.fill_text(label, LAW_NUMBER_AR_100)
            outcome_100 = form.submit_expecting_refusal()
            refusal_100 = form.save_refusal_text()
            success_100 = form.success_message_text()
            _wait_for_committed_value(
                admin, LAW_1990_ENTRY_CODE, label, LAW_NUMBER_AR_100
            )
            stored_100 = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        with allure.step(
            "Enter a 101-character Arabic string in Law Number (AR) and click Save"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            authoring.fill_text(label, LAW_NUMBER_AR_101)
            typed_value = form.live_value(label)
            max_length_attribute = form.max_length_attribute(label)
            outcome_101 = form.submit_expecting_refusal()
            refusal_101 = form.save_refusal_text()
            success_101 = form.success_message_text()
            stored_101 = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert -- step 2
        assert len(LAW_NUMBER_AR_100) == LAW_NUMBER_CAP
        assert not refusal_100, (
            f"the exactly-100-character Law Number (AR) was rejected: {refusal_100!r}"
        )
        assert outcome_100 == "saved" and success_100, (
            "expected the success toast after saving a 100-character Arabic Law "
            f"Number; the page reported {outcome_100!r}"
        )
        assert stored_100 == LAW_NUMBER_AR_100

        # Assert -- step 3 (either/or, exactly as the case words it)
        assert len(LAW_NUMBER_AR_101) == LAW_NUMBER_CAP + 1
        capped_by_field = (
            max_length_attribute == str(LAW_NUMBER_CAP)
            or len(typed_value) == LAW_NUMBER_CAP
        )
        rejected_on_save = (
            bool(refusal_101)
            and not success_101
            and stored_101 != LAW_NUMBER_AR_101
        )
        assert capped_by_field or rejected_on_save, (
            "expected the 101st character NOT to be accepted in the Arabic Law "
            f"Number -- either the field caps at {LAW_NUMBER_CAP} characters or a "
            "max-length validation error is shown and the value is not saved. Live: "
            f"maxlength={max_length_attribute!r}, the box held {len(typed_value)} "
            f"characters, the outcome was {outcome_101!r}, the refusal bar read "
            f"{refusal_101!r}, and the record now stores a {len(stored_101)}-"
            "character value"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Number (AR)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134950 Law 1990 Law Number (AR)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a whitespace-only Arabic Law Number is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134951
@pytest.mark.traceability("134951")
@allure.label("pbi", "129394")
@allure.label("testcase", "134951")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134951_a_whitespace_only_arabic_law_number_is_rejected_on_save(
    page,
):
    # [!] EXPECTED TO FAIL -- same finding (iii) as 134947, on the Arabic half.
    admin = ChambersLawAdminPage(page)
    label = _arabic_label(admin, admin.LAW_NUMBER_LABEL)
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Number (AR) editable"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step("Enter four space characters in Law Number (AR) and click Save"):
            authoring.fill_text(label, FOUR_SPACES)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert not success and outcome != "saved", (
            "expected NO success toast for a whitespace-only Law Number (AR); got "
            f"{success!r}"
        )
        assert refusal, (
            "expected the save to be blocked with a required-field validation error "
            "for a whitespace-only Law Number (AR); no refusal was shown"
        )
        assert stored == baseline_value, (
            f"expected Law Number (AR) to retain {baseline_value!r} and NOT be "
            f"stored as blank or spaces; it reads {stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Number (AR)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134951 Law 1990 Law Number (AR)",
                )


# =========================================================================
# BATCH 3 -- Law Title, English
# =========================================================================
# Every case in this batch says "click Save". There is NO button by that
# name on this form (confirmed live -- see finding (a) in the module
# docstring), and `Save as Draft` validates nothing at all, so each step
# below drives `Submit for Publishing`, which is the only button that can
# produce the validation errors these cases expect.

@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid English Law Title is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134952
@pytest.mark.traceability("134952")
@allure.label("pbi", "129394")
@allure.label("testcase", "134952")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134952_a_valid_english_law_title_is_accepted_and_saved(page):
    # DISCLOSED, same reasoning as 134944: the case's literal,
    # 'Establishment of the Qatar Chamber of Commerce and Industry', is the
    # 1990 record's OWN current Law Title. Writing it onto the 1996 record
    # instead would temporarily mislabel real, published editorial content
    # with another law's title -- on the object's TITLE FIELD, which is also
    # what the entries list renders -- so the case is executed against the
    # record it belongs to. The save is still a real one (full fill ->
    # Submit for Publishing -> PUT); the SUCCESS MESSAGE is what proves it
    # happened, and the fresh-navigation read-back proves it committed.
    admin = ChambersLawAdminPage(page)
    label = admin.LAW_TITLE_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Title (EN) editable"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()
            editable = authoring.field_count(label) == 1

        with allure.step(
            f"Enter {LAW_TITLE_EN_VALID!r} in Law Title (EN) and click Submit for "
            "Publishing (the case's 'Save' -- there is no Save button)"
        ):
            authoring.fill_text(label, LAW_TITLE_EN_VALID)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record"):
            _wait_for_committed_value(
                admin, LAW_1990_ENTRY_CODE, label, LAW_TITLE_EN_VALID
            )
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert editable, "expected exactly one editable Law Title (EN) field"
        assert not refusal, f"unexpected validation error: {refusal!r}"
        assert outcome == "saved" and success, (
            f"expected the success toast; the page reported {outcome!r}"
        )
        assert stored == LAW_TITLE_EN_VALID, (
            f"expected Law Title (EN) to read {LAW_TITLE_EN_VALID!r}; it reads "
            f"{stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Title (EN)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134952 Law 1990 Law Title (EN)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty English Law Title is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134953
@pytest.mark.traceability("134953")
@allure.label("pbi", "129394")
@allure.label("testcase", "134953")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134953_an_empty_english_law_title_is_rejected_on_save(page):
    # The expected block is stage 2a (the browser's own `required` check):
    # confirmed live, `input[name="ObjectField_lawTitle"]` carries
    # `required`, and Submit for Publishing restores the constraint before
    # calling checkValidity(). A native bubble is not in the DOM, so the
    # observable trace is the control's own validity state -- which is
    # exactly "a required-field validation error against Law Title (EN)".
    admin = ChambersLawAdminPage(page)
    label = admin.LAW_TITLE_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Title (EN) populated"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Clear Law Title (EN) completely and click Submit for Publishing"
        ):
            authoring.fill_text(label, "")
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()
            value_missing = form.is_value_missing(label)
            native_message = form.native_validation_message(label)

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert baseline_value, (
            "precondition: expected the record to open with Law Title (EN) populated"
        )
        assert not success and outcome != "saved", (
            f"expected NO success toast for an empty Law Title (EN); got {success!r}"
        )
        assert value_missing or (label.strip().lower() in refusal.lower()), (
            "expected a required-field validation error against Law Title (EN); "
            f"the browser reported {native_message!r} and the refusal bar read "
            f"{refusal!r}"
        )
        assert stored == baseline_value, (
            f"expected Law Title (EN) to retain {baseline_value!r}; it reads "
            f"{stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Title (EN)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134953 Law 1990 Law Title (EN)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that the English Law Title accepts exactly 200 characters and rejects 201"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134954
@pytest.mark.traceability("134954")
@allure.label("pbi", "129394")
@allure.label("testcase", "134954")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134954_the_english_law_title_accepts_exactly_200_characters_and_rejects_201(
    page,
):
    # The cap on THIS field is 200, not the 100 of Law Number -- checked
    # against the Object's own rule, `match(lawTitle, "(?s)^.{0,200}$")`, and
    # not assumed to mirror the sibling field.
    #
    # Step 3's expected result is an EITHER/OR ("the field caps at 200
    # characters OR a max-length validation error is shown and the value is
    # not saved"). Both halves are checked: the `maxlength` attribute /
    # truncated live value for the cap, and the page's refusal for the
    # validation error. Confirmed live that this control carries NO
    # `maxlength` and no character counter, so the SECOND half is the one
    # this product should satisfy -- but the test accepts either, because
    # the case does.
    #
    # [RE-POINTED 2026-09-15 -- THIS TEST WAS MIS-SCRIPTED AND SO WAS THE BUG
    # IT PRODUCED.] It read the refusal through a reader that looked ONLY at
    # `[data-qc-oel-editbar]` and ONLY for the prefix "This record was not
    # saved:". The Object's named-rule message for this field does not go
    # there: `reportComplaints()` ties it to Law Title by label and renders
    # it UNDER THE BOX, in a class-less `<div data-qc-oel-field-error>`. The
    # old reader returned "" for it, this test reported "refused silently,
    # no message", and product bug #141989 was filed -- now CLOSED AS NOT A
    # BUG, because reproducing it by hand showed the message
    # ("Law Title must not exceed 200 characters") visible and still on
    # screen at 0.5s / 2s / 5s, with the 201-character value correctly not
    # stored. The product was right; the reader was blind.
    #
    # `save_refusal_text()` now reads all three renderers, and the step-3
    # report below names the OUTCOME SHAPE explicitly
    # (`save_outcome_shape()`) plus a per-renderer breakdown
    # (`save_message_report()`), so no future bug can be filed off "the
    # reader saw nothing" without that being visible in the report itself.
    admin = ChambersLawAdminPage(page)
    label = admin.LAW_TITLE_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Title (EN) editable"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Enter a 200-character string in Law Title (EN) and click Submit for "
            "Publishing"
        ):
            authoring.fill_text(label, LAW_TITLE_EN_200)
            outcome_200 = form.submit_expecting_refusal()
            refusal_200 = form.save_refusal_text()
            success_200 = form.success_message_text()
            _wait_for_committed_value(
                admin, LAW_1990_ENTRY_CODE, label, LAW_TITLE_EN_200
            )
            stored_200 = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        with allure.step(
            "Enter a 201-character string in Law Title (EN) and click Submit for "
            "Publishing"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            authoring.fill_text(label, LAW_TITLE_EN_201)
            typed_value = form.live_value(label)
            max_length_attribute = form.max_length_attribute(label)
            outcome_201 = form.submit_expecting_refusal()
            refusal_201 = form.save_refusal_text()
            success_201 = form.success_message_text()
            renderer_report_201 = form.save_message_report()
            stored_201 = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)
            shape_201 = _outcome_shape(
                refusal_201, success_201, LAW_TITLE_EN_201, stored_201
            )
            allure.attach(
                f"{shape_201}\n{renderer_report_201}",
                name="tc_134954 step 3 -- outcome shape and per-renderer breakdown",
            )

        # Assert -- step 2
        assert len(LAW_TITLE_EN_200) == LAW_TITLE_CAP
        assert not refusal_200, (
            f"the exactly-200-character Law Title (EN) was rejected: {refusal_200!r}"
        )
        assert outcome_200 == "saved" and success_200, (
            "expected the success toast after saving a 200-character Law Title "
            f"(EN); the page reported {outcome_200!r}"
        )
        assert stored_200 == LAW_TITLE_EN_200

        # Assert -- step 3 (either/or, exactly as the case words it)
        assert len(LAW_TITLE_EN_201) == LAW_TITLE_CAP + 1
        capped_by_field = (
            max_length_attribute == str(LAW_TITLE_CAP)
            or len(typed_value) == LAW_TITLE_CAP
        )
        rejected_on_save = (
            bool(refusal_201)
            and not success_201
            and stored_201 != LAW_TITLE_EN_201
        )
        assert capped_by_field or rejected_on_save, (
            "expected the 201st character NOT to be accepted -- either the field "
            f"caps at {LAW_TITLE_CAP} characters or a max-length validation error "
            f"is shown and the value is not saved. Live: maxlength="
            f"{max_length_attribute!r}, the box held {len(typed_value)} characters, "
            f"the outcome was {outcome_201!r}, and the record now stores a "
            f"{len(stored_201)}-character value. WHICH SHAPE: {shape_201}. "
            f"WHAT EACH RENDERER SAID: {renderer_report_201}"
        )
        if rejected_on_save:
            assert any(message in refusal_201 for message in LAW_TITLE_CAP_MESSAGES), (
                "expected the refusal to be the Law Title length rule "
                f"({LAW_TITLE_CAP_MESSAGES[0]!r}, or the same rule's Arabic label "
                f"{LAW_TITLE_CAP_MESSAGES[1]!r} -- this UI serves either); it read "
                f"{refusal_201!r}"
            )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Title (EN)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134954 Law 1990 Law Title (EN)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a whitespace-only English Law Title is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134955
@pytest.mark.traceability("134955")
@allure.label("pbi", "129394")
@allure.label("testcase", "134955")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134955_a_whitespace_only_english_law_title_is_rejected_on_save(
    page,
):
    # [!] EXPECTED TO FAIL -- see finding (d) in the module docstring, and
    # product defects #141968 / #141970 already filed for the identical
    # shape on Law Number. Four spaces satisfy the browser's `required`
    # check (the box is not empty) and satisfy `^.{0,200}$`, and the page's
    # own "cannot be only spaces" guard is scoped by its own
    # `URL_FIELD_NAME = /(^|[a-z0-9])(url|link|href)$/i` to url/link/href-
    # named fields, which `lawTitle` is not. Scripted as the case states it;
    # a failure here is NEW EVIDENCE that the defect is object-wide rather
    # than one field's.
    admin = ChambersLawAdminPage(page)
    label = admin.LAW_TITLE_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Title (EN) editable"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Enter four space characters in Law Title (EN) and click Submit for "
            "Publishing"
        ):
            authoring.fill_text(label, FOUR_SPACES)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert not success and outcome != "saved", (
            "expected NO success toast for a whitespace-only Law Title (EN); got "
            f"{success!r}"
        )
        assert refusal, (
            "expected the save to be blocked with a required-field validation error "
            "for a whitespace-only Law Title (EN); no refusal was shown"
        )
        assert stored == baseline_value, (
            f"expected Law Title (EN) to retain {baseline_value!r} and NOT be "
            f"stored as blank or spaces; it reads {stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Title (EN)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134955 Law 1990 Law Title (EN)",
                )


# =========================================================================
# BATCH 3 -- Law Title, Arabic
# =========================================================================
# Same lookup contract as the Arabic Law Number block above: the Arabic half
# is REQUIRED and its rendered accessible name carries a trailing " *"
# ('Law Title — العربية *' -- an EM DASH, as ARABIC_SUFFIX holds it), which `ObjectAuthoringPage.label_pattern()`
# tolerates and an `exact=True` match does not. Verified live 2026-09-15 for
# THIS field specifically: the pattern resolves exactly ONE control.

@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Arabic Law Title is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134956
@pytest.mark.traceability("134956")
@allure.label("pbi", "129394")
@allure.label("testcase", "134956")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134956_a_valid_arabic_law_title_is_accepted_and_saved(page):
    # DISCLOSED -- and DIFFERENT from 134952/134948: the case's Arabic
    # literal is NOT the value this record currently stores. Read live
    # 2026-09-15, the 1990 record's Arabic Law Title begins with the synonym
    # "إنشاء", while the case writes "تأسيس". So unlike its English twin
    # this is a genuine CHANGE to a real, published editorial record -- on
    # the object's title field -- which is exactly why the TEST_OWNED
    # restore below captures the baseline at runtime and PROVES it back.
    admin = ChambersLawAdminPage(page)
    label = _arabic_label(admin, admin.LAW_TITLE_LABEL)
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Title (AR) editable"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()
            editable = authoring.field_count(label) == 1

        with allure.step(
            f"Enter {LAW_TITLE_AR_VALID!r} in Law Title (AR) and click Submit for "
            "Publishing"
        ):
            authoring.fill_text(label, LAW_TITLE_AR_VALID)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record"):
            _wait_for_committed_value(
                admin, LAW_1990_ENTRY_CODE, label, LAW_TITLE_AR_VALID
            )
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert editable, "expected exactly one editable Law Title (AR) field"
        assert not refusal, f"unexpected validation error: {refusal!r}"
        assert outcome == "saved" and success, (
            f"expected the success toast; the page reported {outcome!r}"
        )
        assert stored == LAW_TITLE_AR_VALID, (
            f"expected Law Title (AR) to read {LAW_TITLE_AR_VALID!r}; it reads "
            f"{stored!r}"
        )
        # "with the Arabic characters intact" -- the equality above already
        # proves the round-trip, and this names the failure mode it guards
        # against (a mangled / transliterated / stripped RTL value) so a
        # report reads plainly.
        assert all(
            character in stored for character in set(LAW_TITLE_AR_VALID) - {" "}
        ), (
            "expected every Arabic character of the stored Law Title (AR) to "
            f"survive the round-trip; it reads {stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Title (AR)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134956 Law 1990 Law Title (AR)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Arabic Law Title is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134957
@pytest.mark.traceability("134957")
@allure.label("pbi", "129394")
@allure.label("testcase", "134957")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134957_an_empty_arabic_law_title_is_rejected_on_save(page):
    # Confirmed live 2026-09-15: `#qc-ar-lawTitle` carries `required`, so the
    # expected block is the same stage-2a browser constraint check as 134953
    # -- and it is the ONE negative Arabic case that does not depend on the
    # missing `name` attribute, because the browser checks the control
    # itself, not the `/validate` payload.
    admin = ChambersLawAdminPage(page)
    label = _arabic_label(admin, admin.LAW_TITLE_LABEL)
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Title (AR) populated"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Clear Law Title (AR) completely and click Submit for Publishing"
        ):
            authoring.fill_text(label, "")
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()
            value_missing = form.is_value_missing(label)
            native_message = form.native_validation_message(label)

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert baseline_value, (
            "precondition: expected the record to open with Law Title (AR) populated"
        )
        assert not success and outcome != "saved", (
            f"expected NO success toast for an empty Law Title (AR); got {success!r}"
        )
        assert value_missing or (ARABIC_FIELD_MARKER in refusal), (
            "expected a required-field validation error against Law Title (AR); "
            f"the browser reported {native_message!r} and the refusal bar read "
            f"{refusal!r}"
        )
        assert stored == baseline_value, (
            f"expected Law Title (AR) to retain {baseline_value!r}; it reads "
            f"{stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Title (AR)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134957 Law 1990 Law Title (AR)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that the Arabic Law Title accepts exactly 200 characters and rejects 201"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134958
@pytest.mark.traceability("134958")
@allure.label("pbi", "129394")
@allure.label("testcase", "134958")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134958_the_arabic_law_title_accepts_exactly_200_characters_and_rejects_201(
    page,
):
    # [!] STEP 3 EXPECTED TO FAIL -- see finding (c) in the module
    # docstring. Read live 2026-09-15, `#qc-ar-lawTitle` carries NO `name`
    # attribute (its English twin has `name="ObjectField_lawTitle"`), so the
    # Arabic value never enters the `/validate` payload and the `Law Title
    # length` rule is evaluated against the DEFAULT-locale value only; nor
    # does the control carry a `maxlength`. That is byte-for-byte the shape
    # of product defect #141969, already filed against the Arabic Law
    # Number -- so a failure here shows it is OBJECT-WIDE. Neither half of
    # the case's either/or is likely to hold. Scripted as the case states
    # it.
    admin = ChambersLawAdminPage(page)
    label = _arabic_label(admin, admin.LAW_TITLE_LABEL)
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Title (AR) editable"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Enter a 200-character Arabic string in Law Title (AR) and click Submit "
            "for Publishing"
        ):
            authoring.fill_text(label, LAW_TITLE_AR_200)
            outcome_200 = form.submit_expecting_refusal()
            refusal_200 = form.save_refusal_text()
            success_200 = form.success_message_text()
            _wait_for_committed_value(
                admin, LAW_1990_ENTRY_CODE, label, LAW_TITLE_AR_200
            )
            stored_200 = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        with allure.step(
            "Enter a 201-character Arabic string in Law Title (AR) and click Submit "
            "for Publishing"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            authoring.fill_text(label, LAW_TITLE_AR_201)
            typed_value = form.live_value(label)
            max_length_attribute = form.max_length_attribute(label)
            outcome_201 = form.submit_expecting_refusal()
            refusal_201 = form.save_refusal_text()
            success_201 = form.success_message_text()
            stored_201 = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert -- step 2
        assert len(LAW_TITLE_AR_200) == LAW_TITLE_CAP
        assert not refusal_200, (
            f"the exactly-200-character Law Title (AR) was rejected: {refusal_200!r}"
        )
        assert outcome_200 == "saved" and success_200, (
            "expected the success toast after saving a 200-character Arabic Law "
            f"Title; the page reported {outcome_200!r}"
        )
        assert stored_200 == LAW_TITLE_AR_200

        # Assert -- step 3 (either/or, exactly as the case words it)
        assert len(LAW_TITLE_AR_201) == LAW_TITLE_CAP + 1
        capped_by_field = (
            max_length_attribute == str(LAW_TITLE_CAP)
            or len(typed_value) == LAW_TITLE_CAP
        )
        rejected_on_save = (
            bool(refusal_201)
            and not success_201
            and stored_201 != LAW_TITLE_AR_201
        )
        assert capped_by_field or rejected_on_save, (
            "expected the 201st character NOT to be accepted in the Arabic Law "
            f"Title -- either the field caps at {LAW_TITLE_CAP} characters or a "
            "max-length validation error is shown and the value is not saved. Live: "
            f"maxlength={max_length_attribute!r}, the box held {len(typed_value)} "
            f"characters, the outcome was {outcome_201!r}, the refusal bar read "
            f"{refusal_201!r}, and the record now stores a {len(stored_201)}-"
            "character value"
        )
        if rejected_on_save:
            assert any(message in refusal_201 for message in LAW_TITLE_CAP_MESSAGES), (
                "expected the refusal to be the Law Title length rule "
                f"({LAW_TITLE_CAP_MESSAGES[0]!r}, or the same rule's Arabic label "
                f"{LAW_TITLE_CAP_MESSAGES[1]!r} -- this UI serves either); it read "
                f"{refusal_201!r}"
            )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Title (AR)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134958 Law 1990 Law Title (AR)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a whitespace-only Arabic Law Title is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134959
@pytest.mark.traceability("134959")
@allure.label("pbi", "129394")
@allure.label("testcase", "134959")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134959_a_whitespace_only_arabic_law_title_is_rejected_on_save(
    page,
):
    # [!] EXPECTED TO FAIL -- same finding (d) as 134955, on the Arabic half,
    # and the same shape as filed defects #141968 / #141970.
    admin = ChambersLawAdminPage(page)
    label = _arabic_label(admin, admin.LAW_TITLE_LABEL)
    baseline_value = None
    baseline_status = None

    try:
        with allure.step("Open a law entry record with Law Title (AR) editable"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Enter four space characters in Law Title (AR) and click Submit for "
            "Publishing"
        ):
            authoring.fill_text(label, FOUR_SPACES)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert not success and outcome != "saved", (
            "expected NO success toast for a whitespace-only Law Title (AR); got "
            f"{success!r}"
        )
        assert refusal, (
            "expected the save to be blocked with a required-field validation error "
            "for a whitespace-only Law Title (AR); no refusal was shown"
        )
        assert stored == baseline_value, (
            f"expected Law Title (AR) to retain {baseline_value!r} and NOT be "
            f"stored as blank or spaces; it reads {stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Title (AR)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134959 Law 1990 Law Title (AR)",
                )


# =========================================================================
# BATCH 4 case data -- Law Description
# =========================================================================
# Mirrored from the approved cases: verbatim where they give a literal,
# deterministic where they describe one ("a 300-character description").
#
# FIVE spaces, not four: 134963 and 134967 say "Enter five space
# characters", while 134947/134951/134955/134959 said four. The existing
# FOUR_SPACES constant is deliberately NOT reused here -- the data mirrors
# each case exactly.
FIVE_SPACES = "     "                                    # 134963 / 134967

# 300-character valid values (134960 / 134964). Self-describing, so a
# failure report shows WHAT was written rather than an opaque run of "A"s.
LAW_DESCRIPTION_EN_300 = (
    "QCTEST129394-EN-DESC-" + "Chamber's Law description boundary sample. " * 10
)[:300]
LAW_DESCRIPTION_AR_300 = (
    "وصف قانون اختباري لغرفة قطر للتجارة والصناعة " + "ب" * 300
)[:300]

# 500/501-character boundary values (134962 / 134966). The cap on THIS
# field is 500 -- Law Number's was 100 and Law Title's 200; read off the
# Object's own rule, not assumed to mirror either (finding (g)).
LAW_DESCRIPTION_EN_500 = ("QCTEST129394-EN-DESC-" + "ABCDEFGHIJ" * 50)[:500]
LAW_DESCRIPTION_EN_501 = LAW_DESCRIPTION_EN_500 + "X"
LAW_DESCRIPTION_AR_500 = (
    "وصف قانون اختباري لغرفة قطر للتجارة والصناعة " + "ب" * 500
)[:500]
LAW_DESCRIPTION_AR_501 = LAW_DESCRIPTION_AR_500 + "ب"

LAW_DESCRIPTION_CAP = 500
# The Object's own named rule -- match(lawDescription, "(?s)^.{0,500}$") --
# and BOTH error labels it ships with (cms/liferay-context.md, LawEntry).
# Matched in either language on purpose: this account leaks Arabic messages
# into an English UI, and no batch-4 case demands a literal message.
LAW_DESCRIPTION_CAP_MESSAGES = (
    "Law Description must not exceed 500 characters",
    "يجب ألا يتجاوز وصف القانون 500 حرف",
)

# The tag a PLAIN textbox renders as on this surface (finding (f)). A
# rich-text field would be a CKEditor iframe instead, never a textarea.
PLAIN_TEXTAREA_TAG = "textarea"
RTL_DIRECTION = "rtl"


# =========================================================================
# BATCH 4 -- Law Description, English
# =========================================================================
# Same two contracts as batches 2 and 3, restated because they decide every
# assertion here: there is NO "Save" button on this form (the case wording
# is a known documentation defect), and `Save as Draft` validates nothing at
# all, so each step below drives `Submit for Publishing` -- the only button
# that can produce the validation errors these cases expect.

@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid English Law Description is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134960
@pytest.mark.traceability("134960")
@allure.label("pbi", "129394")
@allure.label("testcase", "134960")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134960_a_valid_english_law_description_is_accepted_and_saved(
    page,
):
    # This is the batch's one place that PROVES the field shape at runtime
    # (finding (f)): Law Description is a plain `<textarea>`, not a
    # rich-text editor, so `fill_text()` is the correct path and
    # `fill_rich_text()` would be wrong. Asserting the tag here means a
    # silent product change to a CKEditor field is reported as exactly that
    # rather than as seven mysterious locator failures.
    admin = ChambersLawAdminPage(page)
    label = admin.LAW_DESCRIPTION_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()
            editable = authoring.field_count(label) == 1
            control_tag = form.tag_name(label)

        with allure.step(
            "Enter a 300-character description in Law Description (EN) and click "
            "Submit for Publishing (the case's 'Save' -- there is no Save button)"
        ):
            authoring.fill_text(label, LAW_DESCRIPTION_EN_300)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record"):
            _wait_for_committed_value(
                admin, LAW_1990_ENTRY_CODE, label, LAW_DESCRIPTION_EN_300
            )
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert editable, (
            "expected exactly one editable Law Description (EN) text area"
        )
        assert control_tag == PLAIN_TEXTAREA_TAG, (
            "expected Law Description (EN) to be a plain text area (confirmed live "
            f"2026-09-15); it renders as a {control_tag!r} element, so this field's "
            "shape changed and every test in this batch fills it the wrong way"
        )
        assert len(LAW_DESCRIPTION_EN_300) == 300
        assert not refusal, f"unexpected validation error: {refusal!r}"
        assert outcome == "saved" and success, (
            f"expected the success toast; the page reported {outcome!r}"
        )
        assert stored == LAW_DESCRIPTION_EN_300, (
            "expected Law Description (EN) to be returned with the full "
            f"300-character text preserved; it reads {len(stored)} characters: "
            f"{stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Description (EN)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134960 Law 1990 Law Description (EN)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty English Law Description is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134961
@pytest.mark.traceability("134961")
@allure.label("pbi", "129394")
@allure.label("testcase", "134961")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134961_an_empty_english_law_description_is_rejected_on_save(
    page,
):
    # The expected block is stage 2a (the browser's own `required` check):
    # confirmed live, `textarea[name="ObjectField_lawDescription"]` carries
    # `required`, and Submit for Publishing restores the constraint before
    # calling checkValidity(). A native bubble is not in the DOM, so the
    # observable trace is the control's own validity state -- which IS "a
    # required-field validation error against Law Description (EN)".
    admin = ChambersLawAdminPage(page)
    label = admin.LAW_DESCRIPTION_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record with Law Description (EN) populated"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Clear Law Description (EN) completely and click Submit for Publishing"
        ):
            authoring.fill_text(label, "")
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()
            value_missing = form.is_value_missing(label)
            native_message = form.native_validation_message(label)

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert baseline_value, (
            "precondition: expected the record to open with Law Description (EN) "
            "populated"
        )
        assert not success and outcome != "saved", (
            "expected NO success toast for an empty Law Description (EN); got "
            f"{success!r}"
        )
        assert value_missing or (label.strip().lower() in refusal.lower()), (
            "expected a required-field validation error against Law Description "
            f"(EN); the browser reported {native_message!r} and the refusal bar "
            f"read {refusal!r}"
        )
        assert stored == baseline_value, (
            f"expected Law Description (EN) to retain {baseline_value!r}; it reads "
            f"{stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Description (EN)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134961 Law 1990 Law Description (EN)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that the English Law Description accepts exactly 500 characters and "
    "rejects 501"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134962
@pytest.mark.traceability("134962")
@allure.label("pbi", "129394")
@allure.label("testcase", "134962")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134962_the_english_law_description_accepts_exactly_500_characters_and_rejects_501(
    page,
):
    # The cap on THIS field is 500 -- not Law Number's 100, not Law Title's
    # 200. Checked against the Object's own rule,
    # `match(lawDescription, "(?s)^.{0,500}$")` (finding (g)), and not
    # assumed to mirror either sibling.
    #
    # Step 3's expected result is an EITHER/OR ("the field caps at 500
    # characters OR a max-length validation error is shown and the
    # previously saved 500-character value is unchanged"). Both halves are
    # checked: the `maxlength` attribute / truncated live value for the cap,
    # and the red refusal bar for the validation error. Confirmed live that
    # this textarea carries NO `maxlength` and no counter, so the SECOND
    # half is the one this product should satisfy -- the test accepts
    # either, because the case does.
    #
    # THREE outcome shapes are distinguished in the failure message, not
    # two: "refused with a message", "refused silently" and "accepted and
    # stored" are three different product behaviours, and the report below
    # names which one happened.
    #
    # [RE-POINTED 2026-09-15.] This comment used to assert as FACT that Law
    # Title's English over-length save (#141989) "was refused SILENTLY: not
    # stored, and no message at all". THAT WAS NOT TRUE -- it was an artefact
    # of the old refusal reader, which looked only at
    # `[data-qc-oel-editbar]` for the prefix "This record was not saved:"
    # and was structurally incapable of seeing a message rendered under the
    # box, which is where `reportComplaints()` puts a named-rule message it
    # can tie to a field. Reproduced by hand: 501 characters in Law
    # Description (EN) renders a visible "Law Description must not exceed
    # 500 characters", still on screen at 0.5s / 2s / 5s, value not stored.
    # #141989 is closed as Not a Bug. `save_refusal_text()` now reads all
    # three renderers, and the shape below is computed from what the page
    # actually said plus what the record actually holds.
    #
    # This test publishes TWICE (27-30 s each, measured) -- budgeted for.
    admin = ChambersLawAdminPage(page)
    label = admin.LAW_DESCRIPTION_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Enter exactly 500 characters in Law Description (EN) and click Submit "
            "for Publishing"
        ):
            authoring.fill_text(label, LAW_DESCRIPTION_EN_500)
            outcome_500 = form.submit_expecting_refusal()
            refusal_500 = form.save_refusal_text()
            success_500 = form.success_message_text()
            _wait_for_committed_value(
                admin, LAW_1990_ENTRY_CODE, label, LAW_DESCRIPTION_EN_500
            )
            stored_500 = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        with allure.step(
            "Add one more character to make 501 and click Submit for Publishing"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            authoring.fill_text(label, LAW_DESCRIPTION_EN_501)
            typed_value = form.live_value(label)
            max_length_attribute = form.max_length_attribute(label)
            outcome_501 = form.submit_expecting_refusal()
            refusal_501 = form.save_refusal_text()
            success_501 = form.success_message_text()
            renderer_report_501 = form.save_message_report()
            stored_501 = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)
            shape = _outcome_shape(
                refusal_501, success_501, LAW_DESCRIPTION_EN_501, stored_501
            )
            allure.attach(
                f"{shape}\n{renderer_report_501}",
                name="tc_134962 step 3 -- outcome shape and per-renderer breakdown",
            )

        # Assert -- step 2
        assert len(LAW_DESCRIPTION_EN_500) == LAW_DESCRIPTION_CAP
        assert not refusal_500, (
            "the exactly-500-character Law Description (EN) was rejected: "
            f"{refusal_500!r}"
        )
        assert outcome_500 == "saved" and success_500, (
            "expected the success toast after saving a 500-character Law "
            f"Description (EN); the page reported {outcome_500!r}"
        )
        assert stored_500 == LAW_DESCRIPTION_EN_500

        # Assert -- step 3 (either/or, exactly as the case words it)
        assert len(LAW_DESCRIPTION_EN_501) == LAW_DESCRIPTION_CAP + 1
        capped_by_field = (
            max_length_attribute == str(LAW_DESCRIPTION_CAP)
            or len(typed_value) == LAW_DESCRIPTION_CAP
        )
        rejected_on_save = (
            bool(refusal_501)
            and not success_501
            and stored_501 != LAW_DESCRIPTION_EN_501
        )
        # `shape` is computed above by `_outcome_shape()`, from the WIDENED
        # reader plus the committed value -- never from the bar alone.
        assert capped_by_field or rejected_on_save, (
            "expected the 501st character NOT to be accepted -- either the field "
            f"caps at {LAW_DESCRIPTION_CAP} characters or a max-length validation "
            "error is shown and the previously saved 500-character value is "
            f"unchanged. Live: maxlength={max_length_attribute!r}, the box held "
            f"{len(typed_value)} characters, the outcome was {outcome_501!r}, and "
            f"the record now stores a {len(stored_501)}-character value. "
            f"WHICH SHAPE: {shape}. WHAT EACH RENDERER SAID: "
            f"{renderer_report_501}. The previously saved 500-character value is "
            + (
                "unchanged"
                if stored_501 == LAW_DESCRIPTION_EN_500
                else f"NOT unchanged -- it now reads {stored_501!r}"
            )
        )
        if rejected_on_save:
            assert any(
                message in refusal_501 for message in LAW_DESCRIPTION_CAP_MESSAGES
            ), (
                "expected the refusal to be the Law Description length rule "
                f"({LAW_DESCRIPTION_CAP_MESSAGES[0]!r}, or the same rule's Arabic "
                f"label {LAW_DESCRIPTION_CAP_MESSAGES[1]!r} -- this UI serves "
                f"either); it read {refusal_501!r}"
            )
            assert stored_501 == LAW_DESCRIPTION_EN_500, (
                "expected the previously saved 500-character value to be unchanged "
                f"after the refused 501-character save; it reads {stored_501!r}"
            )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Description (EN)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134962 Law 1990 Law Description (EN)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that a whitespace-only English Law Description is rejected on save"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134963
@pytest.mark.traceability("134963")
@allure.label("pbi", "129394")
@allure.label("testcase", "134963")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134963_a_whitespace_only_english_law_description_is_rejected_on_save(
    page,
):
    # [!] EXPECTED TO FAIL -- see finding (i) in the module docstring, and
    # product defects #141968 / #141970 (Law Number) and #141990 / #141992
    # (Law Title), already filed for the identical shape. Five spaces
    # satisfy the browser's `required` check (the box is not empty) and
    # satisfy `^.{0,500}$`, and the page's own "cannot be only spaces"
    # guard is scoped by its own
    # `URL_FIELD_NAME = /(^|[a-z0-9])(url|link|href)$/i` to
    # url/link/href-named fields, which `lawDescription` is not -- even
    # though its `LongText` businessType would otherwise qualify (the
    # guard's own bail-out reads `if (!URL_FIELD_NAME.test(field.name) ||
    # (field.businessType !== 'Text' && field.businessType !== 'LongText'))
    # return;`, read live). Scripted as the case states it; a failure here
    # is the THIRD field's evidence that the defect is object-wide.
    admin = ChambersLawAdminPage(page)
    label = admin.LAW_DESCRIPTION_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Enter five space characters in Law Description (EN) and click Submit "
            "for Publishing"
        ):
            authoring.fill_text(label, FIVE_SPACES)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert len(FIVE_SPACES) == 5
        assert not success and outcome != "saved", (
            "expected NO success toast for a whitespace-only Law Description (EN); "
            f"got {success!r}"
        )
        assert refusal, (
            "expected the save to be blocked with a required-field validation error "
            "for a whitespace-only Law Description (EN); no refusal was shown"
        )
        assert stored == baseline_value, (
            f"expected Law Description (EN) to retain {baseline_value!r} and NOT be "
            f"stored as spaces; it reads {stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Description (EN)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134963 Law 1990 Law Description (EN)",
                )


# =========================================================================
# BATCH 4 -- Law Description, Arabic
# =========================================================================
# Same lookup contract as the Arabic blocks above: the Arabic half is
# REQUIRED and its rendered accessible name carries a trailing " *"
# ('Law Description — العربية *' -- an EM DASH, as ARABIC_SUFFIX holds it),
# which `ObjectAuthoringPage.label_pattern()` tolerates and an `exact=True`
# match does not. Verified live 2026-09-15 for THIS field specifically: the
# pattern resolves exactly ONE control, a `<textarea dir="rtl" lang="ar">`.

@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that a valid Arabic Law Description is accepted and saved with RTL text "
    "preserved"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134964
@pytest.mark.traceability("134964")
@allure.label("pbi", "129394")
@allure.label("testcase", "134964")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134964_a_valid_arabic_law_description_is_accepted_and_saved_with_rtl_preserved(
    page,
):
    # This case's expected result names RENDERING, not just storage: "the
    # Arabic text intact AND rendered right-to-left in the text area". Both
    # are checked -- the round-trip equality for "intact", and the
    # control's own computed `direction` for "right-to-left". The latter is
    # an observable product property (read live: `dir="rtl" lang="ar"` on
    # `#qc-ar-lawDescription`), not an inference.
    admin = ChambersLawAdminPage(page)
    label = _arabic_label(admin, admin.LAW_DESCRIPTION_LABEL)
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()
            editable = authoring.field_count(label) == 1
            control_tag = form.tag_name(label)

        with allure.step(
            "Enter a 300-character Arabic description in Law Description (AR) and "
            "click Submit for Publishing"
        ):
            authoring.fill_text(label, LAW_DESCRIPTION_AR_300)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record"):
            _wait_for_committed_value(
                admin, LAW_1990_ENTRY_CODE, label, LAW_DESCRIPTION_AR_300
            )
            reopened = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            stored = reopened.field_value(label)
            direction = _LawEntryForm(reopened).text_direction(label)

        # Assert
        assert editable, (
            "expected exactly one editable Law Description (AR) text area"
        )
        assert control_tag == PLAIN_TEXTAREA_TAG, (
            "expected Law Description (AR) to be a plain text area (confirmed live "
            f"2026-09-15); it renders as a {control_tag!r} element"
        )
        assert len(LAW_DESCRIPTION_AR_300) == 300
        assert not refusal, f"unexpected validation error: {refusal!r}"
        assert outcome == "saved" and success, (
            f"expected the success toast; the page reported {outcome!r}"
        )
        assert stored == LAW_DESCRIPTION_AR_300, (
            "expected Law Description (AR) to read the 300-character Arabic value; "
            f"it reads {len(stored)} characters: {stored!r}"
        )
        # "with the Arabic text intact" -- the equality above already proves
        # the round-trip; this names the failure mode it guards against (a
        # mangled / transliterated / stripped RTL value) so a report reads
        # plainly.
        assert all(
            character in stored
            for character in set(LAW_DESCRIPTION_AR_300) - {" "}
        ), (
            "expected every Arabic character of the stored Law Description (AR) to "
            f"survive the round-trip; it reads {stored!r}"
        )
        # "...and rendered right-to-left in the text area".
        assert direction == RTL_DIRECTION, (
            "expected the Law Description (AR) text area to render right-to-left; "
            f"its computed direction is {direction!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Description (AR)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134964 Law 1990 Law Description (AR)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Arabic Law Description is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134965
@pytest.mark.traceability("134965")
@allure.label("pbi", "129394")
@allure.label("testcase", "134965")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134965_an_empty_arabic_law_description_is_rejected_on_save(
    page,
):
    # Confirmed live 2026-09-15: `#qc-ar-lawDescription` carries `required`,
    # so the expected block is the same stage-2a browser constraint check as
    # 134961 -- and it is the ONE negative Arabic case here that does not
    # depend on the missing `name` attribute, because the browser checks the
    # control itself, not the `/validate` payload.
    admin = ChambersLawAdminPage(page)
    label = _arabic_label(admin, admin.LAW_DESCRIPTION_LABEL)
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record with Law Description (AR) populated"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Clear Law Description (AR) completely and click Submit for Publishing"
        ):
            authoring.fill_text(label, "")
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()
            value_missing = form.is_value_missing(label)
            native_message = form.native_validation_message(label)

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert baseline_value, (
            "precondition: expected the record to open with Law Description (AR) "
            "populated"
        )
        assert not success and outcome != "saved", (
            "expected NO success toast for an empty Law Description (AR); got "
            f"{success!r}"
        )
        assert value_missing or (ARABIC_FIELD_MARKER in refusal), (
            "expected a required-field validation error against Law Description "
            f"(AR); the browser reported {native_message!r} and the refusal bar "
            f"read {refusal!r}"
        )
        assert stored == baseline_value, (
            f"expected Law Description (AR) to retain {baseline_value!r}; it reads "
            f"{stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Description (AR)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134965 Law 1990 Law Description (AR)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that the Arabic Law Description accepts exactly 500 characters and "
    "rejects 501"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134966
@pytest.mark.traceability("134966")
@allure.label("pbi", "129394")
@allure.label("testcase", "134966")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134966_the_arabic_law_description_accepts_exactly_500_characters_and_rejects_501(
    page,
):
    # [!] STEP 3 EXPECTED TO FAIL -- see finding (h) in the module
    # docstring. Read live 2026-09-15, `#qc-ar-lawDescription` carries NO
    # `name` attribute (its English twin has
    # `name="ObjectField_lawDescription"`), so the Arabic value never enters
    # the `/validate` payload and the `Law Description length` rule is
    # evaluated against the DEFAULT-locale value only; nor does the textarea
    # carry a `maxlength`. That is byte-for-byte the shape of product
    # defects #141969 (Arabic Law Number) and #141991 (Arabic Law Title) --
    # a THIRD field with it makes the defect object-wide. Neither half of
    # the case's either/or is likely to hold. Scripted as the case states
    # it.
    #
    # This test publishes TWICE (27-30 s each, measured) -- budgeted for.
    admin = ChambersLawAdminPage(page)
    label = _arabic_label(admin, admin.LAW_DESCRIPTION_LABEL)
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Enter exactly 500 Arabic characters in Law Description (AR) and click "
            "Submit for Publishing"
        ):
            authoring.fill_text(label, LAW_DESCRIPTION_AR_500)
            outcome_500 = form.submit_expecting_refusal()
            refusal_500 = form.save_refusal_text()
            success_500 = form.success_message_text()
            _wait_for_committed_value(
                admin, LAW_1990_ENTRY_CODE, label, LAW_DESCRIPTION_AR_500
            )
            stored_500 = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        with allure.step(
            "Add one more Arabic character to make 501 and click Submit for "
            "Publishing"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            authoring.fill_text(label, LAW_DESCRIPTION_AR_501)
            typed_value = form.live_value(label)
            max_length_attribute = form.max_length_attribute(label)
            outcome_501 = form.submit_expecting_refusal()
            refusal_501 = form.save_refusal_text()
            success_501 = form.success_message_text()
            stored_501 = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert -- step 2
        assert len(LAW_DESCRIPTION_AR_500) == LAW_DESCRIPTION_CAP
        assert not refusal_500, (
            "the exactly-500-character Law Description (AR) was rejected: "
            f"{refusal_500!r}"
        )
        assert outcome_500 == "saved" and success_500, (
            "expected the success toast after saving a 500-character Arabic Law "
            f"Description; the page reported {outcome_500!r}"
        )
        assert stored_500 == LAW_DESCRIPTION_AR_500

        # Assert -- step 3 (either/or, exactly as the case words it)
        assert len(LAW_DESCRIPTION_AR_501) == LAW_DESCRIPTION_CAP + 1
        capped_by_field = (
            max_length_attribute == str(LAW_DESCRIPTION_CAP)
            or len(typed_value) == LAW_DESCRIPTION_CAP
        )
        rejected_on_save = (
            bool(refusal_501)
            and not success_501
            and stored_501 != LAW_DESCRIPTION_AR_501
        )
        assert capped_by_field or rejected_on_save, (
            "expected the 501st character NOT to be accepted in the Arabic Law "
            f"Description -- either the field caps at {LAW_DESCRIPTION_CAP} "
            "characters or a max-length validation error is shown and the "
            "previously saved value is unchanged. Live: maxlength="
            f"{max_length_attribute!r}, the box held {len(typed_value)} characters, "
            f"the outcome was {outcome_501!r}, the refusal bar read {refusal_501!r}, "
            f"and the record now stores a {len(stored_501)}-character value "
            + (
                "-- i.e. ACCEPTED AND STORED, all 501 characters, no cap applied"
                if stored_501 == LAW_DESCRIPTION_AR_501
                else "-- i.e. not stored, but no cap was visible either"
            )
        )
        if rejected_on_save:
            assert any(
                message in refusal_501 for message in LAW_DESCRIPTION_CAP_MESSAGES
            ), (
                "expected the refusal to be the Law Description length rule "
                f"({LAW_DESCRIPTION_CAP_MESSAGES[0]!r}, or the same rule's Arabic "
                f"label {LAW_DESCRIPTION_CAP_MESSAGES[1]!r} -- this UI serves "
                f"either); it read {refusal_501!r}"
            )
            assert stored_501 == LAW_DESCRIPTION_AR_500, (
                "expected the previously saved 500-character Arabic value to be "
                "unchanged after the refused 501-character save; it reads "
                f"{stored_501!r}"
            )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Description (AR)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134966 Law 1990 Law Description (AR)",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that a whitespace-only Arabic Law Description is rejected on save"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134967
@pytest.mark.traceability("134967")
@allure.label("pbi", "129394")
@allure.label("testcase", "134967")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134967_a_whitespace_only_arabic_law_description_is_rejected_on_save(
    page,
):
    # [!] EXPECTED TO FAIL -- same finding (i) as 134963, on the Arabic
    # half, and the same shape as filed defects #141968 / #141970 (Law
    # Number) and #141990 / #141992 (Law Title).
    admin = ChambersLawAdminPage(page)
    label = _arabic_label(admin, admin.LAW_DESCRIPTION_LABEL)
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Enter five space characters in Law Description (AR) and click Submit "
            "for Publishing"
        ):
            authoring.fill_text(label, FIVE_SPACES)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(LAW_1990_ENTRY_CODE).field_value(label)

        # Assert
        assert len(FIVE_SPACES) == 5
        assert not success and outcome != "saved", (
            "expected NO success toast for a whitespace-only Law Description (AR); "
            f"got {success!r}"
        )
        assert refusal, (
            "expected the save to be blocked with a required-field validation error "
            "for a whitespace-only Law Description (AR); no refusal was shown"
        )
        assert stored == baseline_value, (
            f"expected Law Description (AR) to retain {baseline_value!r} and NOT be "
            f"stored as spaces; it reads {stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Law Description (AR)"):
                _test_owned_reset(
                    _restore_law_entry_text(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        label,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134967 Law 1990 Law Description (AR)",
                )


# =========================================================================
# Batch 5 case data -- External Link URL
# =========================================================================
# THIS FIELD IS THE EXCEPTION ON THIS OBJECT, and that is the point of the
# batch. Neither root cause behind the nine bugs filed across Law Number /
# Law Title / Law Description can reach it:
#
#   * The only-spaces guard IS scoped to it. Read live, verbatim:
#     `var URL_FIELD_NAME = /(^|[a-z0-9])(url|link|href)$/i;` and the call
#     site `if (!URL_FIELD_NAME.test(field.name) || (field.businessType !==
#     'Text' && field.businessType !== 'LongText')) return;`.
#     `externalLinkUrl` MATCHES that pattern and its businessType is `Text`,
#     so `urlComplaint()` DOES run here -- unlike on every other text field
#     on this object.
#   * The Arabic-control defect cannot apply: this field is NOT bilingual.
#     Confirmed live (see `ChambersLawAdminPage.EXTERNAL_LINK_URL_LABEL`'s
#     note) -- one control, no `#qc-ar-externalLinkUrl`, `localized: false`
#     in the Object definition, and `configuration.localizedFields` reads
#     exactly "lawNumber,lawTitle,lawDescription".
#
# It is also `required: false` in the Object definition, read live -- which
# is precisely what 134971 asserts.

EXTERNAL_LINK_URL_VALID = "https://www.almeezan.qa/LawView.aspx?opt&LawID=2541"  # 134968, verbatim
EXTERNAL_LINK_URL_INVALID = "almeezan..qa/LawView"                               # 134969, verbatim

# 134969's OWN literals, mirrored from the case exactly as written.
#
# [!] THESE DO NOT MATCH THE LIVE PRODUCT, AND ARE SCRIPTED ANYWAY (Result
# Integrity -- an assertion is never rewritten to match observed behaviour).
# `almeezan..qa/LawView` does not start with "/", is not mailto:/tel: and
# does not match `^(https?)://([^\s/?#]+)([^\s]*)$`, so `urlComplaint()`
# returns its FIRST message, and the page composes the note as
# `fieldLabelOf(field) + ' ' + message + '.'`:
#
#   EN  External Link URL is not a valid URL - start it with https:// for
#       another site, or with / for a page on this one.
#   AR  <Arabic field label> <Arabic "not a valid URL" sentence>.
#
# ("-" above is an EM DASH in the live string.) Neither is "Please enter a
# valid URL." The case literal is what is asserted; the run will report the
# real string, and the CASE is what gets corrected in Azure afterwards --
# the same way 134942 was corrected rather than the test loosened.
EXTERNAL_LINK_URL_INVALID_MESSAGE_EN = "Please enter a valid URL."
EXTERNAL_LINK_URL_INVALID_MESSAGE_AR = "\u064a\u0631\u062c\u0649 \u0625\u062f\u062e\u0627\u0644 \u0631\u0627\u0628\u0637 \u0635\u0627\u0644\u062d."

# The Object's ONLY named validation rule that names this field, read live
# off `/o/object-admin/v1.0/object-definitions/78508`:
#     name   "External Link URL format"
#     script isEmpty(externalLinkUrl) || match(externalLinkUrl, "^https?://.*")
# Both shipped error labels. The `isEmpty(...) ||` half is a second,
# independent confirmation that an EMPTY value is legal here -- 134971.
EXTERNAL_LINK_URL_FORMAT_MESSAGES = (
    "External Link URL must start with http:// or https://",
    "\u064a\u062c\u0628 \u0623\u0646 \u064a\u0628\u062f\u0623 \u0627\u0644\u0631\u0627\u0628\u0637 \u0627\u0644\u062e\u0627\u0631\u062c\u064a \u0628\u0640 http:// \u0623\u0648 https://",
)

# 134970's 500/501. Built from the real almeezan URL the other cases use and
# padded, so the string stays a VALID url by `urlComplaint()`'s own rules
# (https:// scheme, a host containing a dot, no whitespace) and the ONLY
# thing under test at the boundary is its LENGTH.
_EXTERNAL_LINK_URL_PAD_BASE = "https://www.almeezan.qa/LawView.aspx?opt&LawID=2541&qcpad="
EXTERNAL_LINK_URL_500 = (_EXTERNAL_LINK_URL_PAD_BASE + "a" * 500)[:500]
EXTERNAL_LINK_URL_501 = EXTERNAL_LINK_URL_500 + "b"
EXTERNAL_LINK_URL_CAP = 500

# CMS interface languages, pinned into the manage URL -- see
# `ObjectAuthoringPage._manage_url()`'s locale-pinning note. 134969 step 3
# ("switch the CMS interface language to Arabic") IS this switch: the page
# decides its own language from `document.documentElement.lang`, which
# Liferay sets from the URL's locale prefix, and `t(en, ar)` then picks
# every message accordingly.
CMS_LOCALE_EN = "en"
CMS_LOCALE_AR = "ar"

# 134971 step 3 reads the PUBLIC page. Budgets mirror the sibling module's.
PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT = 180.0
# An href that exists but goes nowhere -- what "empty-destination CTA"
# means in 134971's expected result.
EMPTY_DESTINATION_HREFS = ("", "#", "javascript:void(0)", "javascript:;", "about:blank")


def _observed_stored_value(
    admin, entry_code, field_label, expected, locale=None, timeout=PUBLISH_CONFIRM_TIMEOUT
) -> str:
    """Polls a FRESH navigation until the record stores `expected`, and
    returns the LAST value observed -- match or no match.

    The text counterpart of `_observed_stored_icon()`, and used wherever a
    save is EXPECTED TO BE REFUSED. `_wait_for_committed_value()` raises on
    timeout, which is right for a happy path but wrong here: a refused save
    would surface as an opaque 120-second `WaitTimeoutError` instead of the
    assertion the case actually wants, and the failure report would never
    say what the record really holds. Nothing is swallowed -- the caller
    asserts on the returned value."""
    observed = {"value": ""}

    def _committed() -> bool:
        observed["value"] = admin.open_law_entry(
            entry_code, locale=locale
        ).field_value(field_label)
        return observed["value"] == expected

    try:
        wait_until(_committed, timeout=timeout, poll=3.0)
    except Exception:  # noqa: BLE001 -- the last observed value IS the result
        pass
    return observed["value"]


def _restore_external_link_url(
    admin, entry_code, baseline_value, baseline_status, locale=CMS_LOCALE_EN
):
    """TEST_OWNED restore for External Link URL, with the read-backs pinned
    to one interface locale.

    Same contract as `_restore_law_entry_text()` -- restore, then PROVE it
    from a fresh navigation -- but it cannot reuse that helper, because that
    one navigates UNPINNED and this field's accessible name is
    locale-dependent (`External Link URL` in English,
    `\u0631\u0627\u0628\u0637 \u0627\u0644\u0646\u0635 \u0627\u0644\u0642\u0627\u0646\u0648\u0646\u064a \u0627\u0644\u062e\u0627\u0631\u062c\u064a`
    in Arabic). An unpinned restore would resolve ZERO controls whenever the
    session had drifted to `ar_SA`, and a TEST_OWNED restore that cannot
    find its own field is exactly the failure this module exists to
    prevent."""
    label = admin.EXTERNAL_LINK_URL_LABEL

    def _restore():
        authoring = admin.open_law_entry(entry_code, locale=locale)
        if authoring.field_value(label) != baseline_value:
            if authoring.current_status() == "Approved":
                authoring.fill_text(label, baseline_value)
                _publish_and_confirm(authoring)
            else:
                _unpublish_and_confirm(authoring)
                authoring.fill_text(label, baseline_value)
                if baseline_status == "Approved":
                    _publish_and_confirm(authoring)
                else:
                    authoring.save_as_draft()

        # PROVE it -- fresh navigation, never a post-save-reflowed DOM.
        authoring = admin.open_law_entry(entry_code, locale=locale)
        actual_value = authoring.field_value(label)
        actual_status = authoring.current_status()
        if actual_value != baseline_value:
            raise AssertionError(
                "TEST_OWNED restore did not commit: External Link URL reads "
                f"{actual_value!r}, expected the captured baseline "
                f"{baseline_value!r}"
            )
        if actual_status != baseline_status:
            raise AssertionError(
                f"TEST_OWNED restore did not commit: {entry_code} status is "
                f"{actual_status!r}, expected the captured baseline "
                f"{baseline_status!r}"
            )

    return _restore


# =========================================================================
# Batch 5 -- External Link URL (134968-134971)
# =========================================================================


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid External Link URL is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.pbi_129394
@pytest.mark.tc_134968
@pytest.mark.traceability("134968")
@allure.label("pbi", "129394")
@allure.label("testcase", "134968")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134968_a_valid_external_link_url_is_accepted_and_saved(page):
    # DISCLOSED, exactly as 134944 discloses the same thing about Law
    # Number: the case's literal IS this record's current stored value.
    # Writing it onto a DIFFERENT law entry would point real, published
    # editorial content at another law's official text, so the case is
    # executed against the record it belongs to. The save is still a real
    # one (fill -> Submit for Publishing -> PUT), the SUCCESS TOAST is what
    # proves it happened, and the reload proves the query string round-
    # tripped intact.
    #
    # THE QUERY STRING IS THE WHOLE POINT of step 3, and it is read back
    # FROM THE CMS, never from the public page. The public renderer
    # NORMALIZES this URL -- live, the card's href is
    # `...?opt=&LawID=2541&language=en` where the stored value is
    # `...?opt&LawID=2541` (an `=` added to the valueless `opt`, and a
    # `language` parameter appended). Comparing a public href to a stored
    # URL by equality is why TC 134877 fails; this test does not do it.
    admin = ChambersLawAdminPage(page)
    label = admin.EXTERNAL_LINK_URL_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()
            editable = authoring.field_count(label) == 1

        with allure.step(
            f"Enter {EXTERNAL_LINK_URL_VALID!r} as the External Link URL and click "
            "Submit for Publishing"
        ):
            authoring.fill_text(label, EXTERNAL_LINK_URL_VALID)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()
            renderer_report = form.save_message_report()

        with allure.step("Reload the law entry record"):
            # LOCALE-PINNED read-back. `_wait_for_committed_value()` would
            # navigate UNPINNED, and this field's accessible name is
            # locale-dependent -- an unpinned re-read resolves ZERO controls
            # the moment the session drifts to `ar_SA`, which is this
            # account's own Liferay language.
            stored = _observed_stored_value(
                admin,
                LAW_1990_ENTRY_CODE,
                label,
                EXTERNAL_LINK_URL_VALID,
                locale=CMS_LOCALE_EN,
            )

        # Assert -- step 1
        assert editable, (
            "expected exactly one editable External Link URL field on the law "
            "entry form"
        )

        # Assert -- step 2
        assert not refusal, (
            f"the valid External Link URL was rejected: {refusal!r} "
            f"({renderer_report})"
        )
        assert outcome == "saved" and success, (
            "expected the success toast after saving a valid External Link URL; "
            f"the page reported {outcome!r} ({renderer_report})"
        )

        # Assert -- step 3
        assert stored == EXTERNAL_LINK_URL_VALID, (
            f"expected External Link URL to read {EXTERNAL_LINK_URL_VALID!r}; it "
            f"reads {stored!r}"
        )
        assert "?opt&LawID=2541" in stored, (
            "expected the query string to be preserved verbatim, including the "
            f"valueless `opt` parameter; the stored value is {stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore External Link URL"):
                _test_owned_reset(
                    _restore_external_link_url(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134968 Law 1990 External Link URL",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that an invalid External Link URL is rejected with the valid-URL message"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.bilingual
@pytest.mark.pbi_129394
@pytest.mark.tc_134969
@pytest.mark.traceability("134969")
@allure.label("pbi", "129394")
@allure.label("testcase", "134969")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134969_an_invalid_external_link_url_is_rejected_with_the_valid_url_message(
    page,
):
    # [!] EXPECTED TO FAIL ON THE MESSAGE LITERAL, and scripted to the case
    # ANYWAY (Result Integrity). The product DOES refuse this value -- this
    # is the one field on the object whose `urlComplaint()` guard is in
    # scope -- but it says something other than "Please enter a valid URL."
    # See EXTERNAL_LINK_URL_INVALID_MESSAGE_EN's note for the live strings.
    # The other three conditions of each step (no success toast, nothing
    # stored, a refusal shown at all) are expected to PASS, and they are
    # asserted separately so the report distinguishes "the product is
    # broken" from "the case's literal is wrong".
    #
    # STEP 3 IS THE INTERFACE-LANGUAGE SWITCH. It is a real switch, not a
    # simulation: the `/ar` locale prefix makes Liferay render the manage
    # page with `<html lang="ar-SA">`, and the page's own `isArabic()` reads
    # exactly that attribute, so `t(en, ar)` serves every message -- and
    # every field label -- in Arabic. Confirmed live: on that render the
    # accessible name "External Link URL" resolves ZERO controls and
    # `EXTERNAL_LINK_URL_LABEL_AR` resolves exactly one.
    #
    # NOTHING IS MUTATED ON PURPOSE HERE -- both steps expect the save to be
    # refused, so nothing should ever commit. The TEST_OWNED restore is
    # still unconditional, because "should not commit" is the very thing
    # under test and a passing product is not a safe assumption.
    admin = ChambersLawAdminPage(page)
    label_en = admin.EXTERNAL_LINK_URL_LABEL
    label_ar = admin.EXTERNAL_LINK_URL_LABEL_AR
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label_en)
            baseline_status = authoring.current_status()

        with allure.step(
            f"Enter {EXTERNAL_LINK_URL_INVALID!r} as the External Link URL and click "
            "Submit for Publishing"
        ):
            authoring.fill_text(label_en, EXTERNAL_LINK_URL_INVALID)
            outcome_en = form.submit_expecting_refusal()
            refusal_en = form.save_refusal_text()
            success_en = form.success_message_text()
            report_en = form.save_message_report()
            stored_en = _observed_stored_value(
                admin,
                LAW_1990_ENTRY_CODE,
                label_en,
                EXTERNAL_LINK_URL_INVALID,
                locale=CMS_LOCALE_EN,
                timeout=REFUSAL_RENDER_TIMEOUT,
            )
            shape_en = _outcome_shape(
                refusal_en, success_en, EXTERNAL_LINK_URL_INVALID, stored_en
            )
            allure.attach(
                f"{shape_en}\n{report_en}",
                name="tc_134969 step 2 (English UI) -- outcome and renderers",
            )

        with allure.step(
            "Switch the CMS interface language to Arabic and repeat"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_AR)
            form = _LawEntryForm(authoring)
            arabic_ui_field_count = authoring.field_count(label_ar)
            authoring.fill_text(label_ar, EXTERNAL_LINK_URL_INVALID)
            outcome_ar = form.submit_expecting_refusal()
            refusal_ar = form.save_refusal_text()
            success_ar = form.success_message_text()
            report_ar = form.save_message_report()
            stored_ar = _observed_stored_value(
                admin,
                LAW_1990_ENTRY_CODE,
                label_ar,
                EXTERNAL_LINK_URL_INVALID,
                locale=CMS_LOCALE_AR,
                timeout=REFUSAL_RENDER_TIMEOUT,
            )
            shape_ar = _outcome_shape(
                refusal_ar, success_ar, EXTERNAL_LINK_URL_INVALID, stored_ar
            )
            allure.attach(
                f"{shape_ar}\n{report_ar}",
                name="tc_134969 step 3 (Arabic UI) -- outcome and renderers",
            )

        # Assert -- step 2, English interface
        assert not success_en, (
            "expected NO success toast for an invalid External Link URL; the page "
            f"showed {success_en!r}"
        )
        assert stored_en != EXTERNAL_LINK_URL_INVALID, (
            f"the invalid string {EXTERNAL_LINK_URL_INVALID!r} WAS stored on "
            f"{LAW_1990_ENTRY_CODE}"
        )
        assert outcome_en == "refused" and refusal_en, (
            "expected the save to be blocked with a validation message against "
            f"External Link URL. WHICH SHAPE: {shape_en}. WHAT EACH RENDERER SAID: "
            f"{report_en}"
        )
        assert EXTERNAL_LINK_URL_INVALID_MESSAGE_EN in refusal_en, (
            "expected the English validation message "
            f"{EXTERNAL_LINK_URL_INVALID_MESSAGE_EN!r} against External Link URL; "
            f"the page said {refusal_en!r}. For the reader: this field can "
            "refuse through TWO mechanisms -- the page's own client-side "
            "`urlComplaint()` sentence, or the Object's named rule "
            f"({EXTERNAL_LINK_URL_FORMAT_MESSAGES[0]!r} / "
            f"{EXTERNAL_LINK_URL_FORMAT_MESSAGES[1]!r}); the string above "
            "identifies which one fired, and the case's literal matches neither"
        )

        # Assert -- step 3, Arabic interface
        assert arabic_ui_field_count == 1, (
            "expected exactly one External Link URL control on the Arabic render, "
            f"addressed by its Arabic label {label_ar!r}; found "
            f"{arabic_ui_field_count}"
        )
        assert not success_ar, (
            "expected NO success toast on the Arabic interface either; the page "
            f"showed {success_ar!r}"
        )
        assert stored_ar != EXTERNAL_LINK_URL_INVALID, (
            f"the invalid string {EXTERNAL_LINK_URL_INVALID!r} WAS stored on "
            f"{LAW_1990_ENTRY_CODE} from the Arabic interface"
        )
        assert outcome_ar == "refused" and refusal_ar, (
            "expected the same validation to be shown on the Arabic interface. "
            f"WHICH SHAPE: {shape_ar}. WHAT EACH RENDERER SAID: {report_ar}"
        )
        assert EXTERNAL_LINK_URL_INVALID_MESSAGE_AR in refusal_ar, (
            "expected the same validation in Arabic as "
            f"{EXTERNAL_LINK_URL_INVALID_MESSAGE_AR!r}; the page said "
            f"{refusal_ar!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore External Link URL"):
                _test_owned_reset(
                    _restore_external_link_url(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134969 Law 1990 External Link URL",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that the External Link URL accepts exactly 500 characters and rejects 501"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.pbi_129394
@pytest.mark.tc_134970
@pytest.mark.traceability("134970")
@allure.label("pbi", "129394")
@allure.label("testcase", "134970")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134970_the_external_link_url_accepts_exactly_500_characters_and_rejects_501(
    page,
):
    # [!] STEP 2 IS EXPECTED TO FAIL, and is scripted to the case anyway
    # (Result Integrity). Read live off the Object definition, this field
    # carries NO `maxLength` objectFieldSetting and NO named length rule --
    # the five active rules on LawEntry cap Law Number at 100, Law Title at
    # 200 and Law Description at 500, constrain Display Order, and check
    # this field's FORMAT only ("must start with http:// or https://").
    # Nothing on the object licenses 500 characters here. What the form DOES
    # declare is the INPUTS-text fragment's own `"maxLength": 280`, read out
    # of the fragment's embedded config for `ObjectField_externalLinkUrl`,
    # which is Liferay's default Text width. So a 500-character URL is
    # expected to be refused, most likely by the server, and the case's
    # premise that 500 is the boundary looks wrong by 220 characters.
    #
    # The test therefore reports, for BOTH steps, the outcome shape and what
    # each renderer said -- so the run itself produces the evidence needed
    # to correct the case (the way 134942 was corrected) instead of an
    # opaque timeout. `_observed_stored_value()` is used rather than
    # `_wait_for_committed_value()` for exactly that reason.
    #
    # Neither the 500 nor the 501 string can fail for any reason OTHER than
    # length: both are built from the same real almeezan URL, keep the
    # `https://` scheme and a dotted host, and contain no whitespace, so
    # `urlComplaint()` and the Object's format rule both pass them.
    #
    # This test publishes TWICE (27-30 s each, measured) -- budgeted for.
    admin = ChambersLawAdminPage(page)
    label = admin.EXTERNAL_LINK_URL_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Enter a valid URL exactly 500 characters long as the External Link URL "
            "and click Submit for Publishing"
        ):
            authoring.fill_text(label, EXTERNAL_LINK_URL_500)
            typed_500 = form.live_value(label)
            max_length_attribute = form.max_length_attribute(label)
            outcome_500 = form.submit_expecting_refusal()
            refusal_500 = form.save_refusal_text()
            success_500 = form.success_message_text()
            report_500 = form.save_message_report()
            stored_500 = _observed_stored_value(
                admin,
                LAW_1990_ENTRY_CODE,
                label,
                EXTERNAL_LINK_URL_500,
                locale=CMS_LOCALE_EN,
            )
            shape_500 = _outcome_shape(
                refusal_500, success_500, EXTERNAL_LINK_URL_500, stored_500
            )
            allure.attach(
                f"{shape_500}\n{report_500}",
                name="tc_134970 step 2 (500 characters) -- outcome and renderers",
            )

        with allure.step(
            "Extend the same URL to 501 characters and click Submit for Publishing"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            authoring.fill_text(label, EXTERNAL_LINK_URL_501)
            typed_501 = form.live_value(label)
            outcome_501 = form.submit_expecting_refusal()
            refusal_501 = form.save_refusal_text()
            success_501 = form.success_message_text()
            report_501 = form.save_message_report()
            stored_501 = admin.open_law_entry(
                LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN
            ).field_value(label)
            shape_501 = _outcome_shape(
                refusal_501, success_501, EXTERNAL_LINK_URL_501, stored_501
            )
            allure.attach(
                f"{shape_501}\n{report_501}",
                name="tc_134970 step 3 (501 characters) -- outcome and renderers",
            )

        # Assert -- step 2
        assert len(EXTERNAL_LINK_URL_500) == EXTERNAL_LINK_URL_CAP
        assert len(typed_500) == EXTERNAL_LINK_URL_CAP, (
            "the box did not even hold 500 characters before the save -- it held "
            f"{len(typed_500)}, so the control itself truncated the value "
            f"(maxlength={max_length_attribute!r})"
        )
        assert not refusal_500, (
            "the exactly-500-character External Link URL was rejected: "
            f"{refusal_500!r}. WHICH SHAPE: {shape_500}. WHAT EACH RENDERER SAID: "
            f"{report_500}"
        )
        assert outcome_500 == "saved" and success_500, (
            "expected the success toast after saving a 500-character External Link "
            f"URL; the page reported {outcome_500!r}. WHAT EACH RENDERER SAID: "
            f"{report_500}"
        )
        assert stored_500 == EXTERNAL_LINK_URL_500, (
            "expected the 500-character URL to be saved; the record stores a "
            f"{len(stored_500)}-character value ({stored_500!r})"
        )

        # Assert -- step 3 (either/or, exactly as the case words it)
        assert len(EXTERNAL_LINK_URL_501) == EXTERNAL_LINK_URL_CAP + 1
        capped_by_field = (
            max_length_attribute == str(EXTERNAL_LINK_URL_CAP)
            or len(typed_501) == EXTERNAL_LINK_URL_CAP
        )
        rejected_on_save = (
            bool(refusal_501)
            and not success_501
            and stored_501 != EXTERNAL_LINK_URL_501
        )
        assert capped_by_field or rejected_on_save, (
            "expected the 501st character NOT to be accepted -- either the field "
            f"caps at {EXTERNAL_LINK_URL_CAP} characters or a max-length "
            "validation error is shown and the value is not saved. Live: "
            f"maxlength={max_length_attribute!r}, the box held {len(typed_501)} "
            f"characters, the outcome was {outcome_501!r}, and the record now "
            f"stores a {len(stored_501)}-character value. WHICH SHAPE: "
            f"{shape_501}. WHAT EACH RENDERER SAID: {report_501}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore External Link URL"):
                _test_owned_reset(
                    _restore_external_link_url(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134970 Law 1990 External Link URL",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that an empty External Link URL is allowed because the field is optional"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.web
@pytest.mark.pbi_129394
@pytest.mark.tc_134971
@pytest.mark.traceability("134971")
@allure.label("pbi", "129394")
@allure.label("testcase", "134971")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134971_an_empty_external_link_url_is_allowed_because_the_field_is_optional(
    browser, page
):
    # The one case in this batch that leaves the CMS. Step 3 is a PUBLIC
    # check, so it runs in a genuinely ANONYMOUS browser context
    # (`new_context(browser, use_auth_state=False)`) -- reusing the
    # authenticated one would prove only that a signed-in editor can see the
    # card, which is not what the case asks.
    #
    # THE FIELD REALLY IS OPTIONAL, from two independent live sources: the
    # Object definition reports `required: false` for `externalLinkUrl` (and
    # the control carries no `required` attribute, so the browser's own
    # stage-2a check cannot block an empty one), and the Object's only rule
    # naming this field is written `isEmpty(externalLinkUrl) || match(...)`
    # -- it EXEMPTS an empty value by construction. Step 2 is expected to
    # pass.
    #
    # Step 3 is the open question. With no destination stored, a card can
    # honestly do one of two things: render no CTA at all, or render one
    # that goes nowhere. The case permits only the first ("no broken or
    # empty-destination CTA is displayed"), and BOTH anchors the card
    # carries live are checked -- the title anchor and the CTA -- because
    # live they share one href and an empty URL would break them together.
    #
    # TEST_OWNED, and unusually load-bearing: this record's card is live on
    # the public Chamber's Law page, and the test deliberately removes its
    # destination. The `finally` restore puts the real almeezan URL back and
    # PROVES it from a fresh navigation.
    admin = ChambersLawAdminPage(page)
    label = admin.EXTERNAL_LINK_URL_LABEL
    baseline_value = None
    baseline_status = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.field_value(label)
            baseline_status = authoring.current_status()
            # The browser's own required-check is stage 2a; an optional
            # field must not report a missing value once emptied.
            authoring.fill_text(label, "")
            value_missing_after_clear = form.is_value_missing(label)

        with allure.step(
            "Leave the External Link URL field empty, complete all mandatory law "
            "entry fields, and click Submit for Publishing"
        ):
            # The mandatory fields (Law Number EN+AR, Law Title EN+AR, Law
            # Description EN+AR, Law Icon, Display Order) are ALREADY filled
            # on this published record and are deliberately left untouched --
            # "complete all mandatory fields" is a precondition here, not a
            # mutation, and rewriting live editorial content to satisfy it
            # would be a bigger change than the case asks for.
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()
            renderer_report = form.save_message_report()
            stored = _observed_stored_value(
                admin, LAW_1990_ENTRY_CODE, label, "", locale=CMS_LOCALE_EN
            )
            status_after_publish = admin.open_law_entry(
                LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN
            ).current_status()

        with allure.step(
            "Publish the page and open the Chamber's Law page in English as an "
            "anonymous visitor"
        ):
            public = ChambersLawPage(anon_page)
            # WHAT "the public page has caught up" MEANS HERE. It is NOT
            # "the href changed": the renderer NORMALIZES a stored URL
            # (`?opt&LawID=2541` is served as `?opt=&LawID=2541&language=en`),
            # so the public href never equalled the stored one even BEFORE
            # this test touched anything -- a `!= baseline_value` poll would
            # return True on its first tick and race the cache instead of
            # waiting for it. The stable signal is the baseline
            # DESTINATION -- host + path, which normalization preserves --
            # having disappeared from both anchors the card renders.
            baseline_parts = urlsplit(baseline_value)
            baseline_destination = (
                baseline_parts.netloc + baseline_parts.path
                if baseline_parts.netloc
                else baseline_value
            )

            def _card_reflects_empty_url() -> bool:
                public.open_chambers_law()
                if not public.is_card_visible(LAW_1990_NUMBER):
                    return False
                if not baseline_destination:
                    return True
                if public.card_title_is_link(LAW_1990_NUMBER) and (
                    baseline_destination
                    in public.card_title_href(LAW_1990_NUMBER)
                ):
                    return False
                return (
                    public.card_cta_count(LAW_1990_NUMBER) == 0
                    or baseline_destination
                    not in public.card_cta_href(LAW_1990_NUMBER)
                )

            wait_until(
                _card_reflects_empty_url,
                timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT,
                poll=3.0,
                message=(
                    "the public Chamber's Law page never reflected the cleared "
                    "External Link URL on the 1990 card"
                ),
            )
            card_visible = public.is_card_visible(LAW_1990_NUMBER)
            card_icon_visible = public.card_icon_visible(LAW_1990_NUMBER)
            card_title = public.card_title_text(LAW_1990_NUMBER)
            card_desc = public.card_desc_text(LAW_1990_NUMBER)
            # "Is the title an anchor?" and "what is its href?" are two
            # different questions, and conflating them would report a bug
            # for the CORRECT behaviour: a title rendered as plain text is
            # the card honestly offering nothing to click, while a title
            # rendered as <a href=""> is the dead link the case forbids.
            # Confirmed live that the title normally IS an anchor
            # (`a.qc-cl-card-title.qc-cl-card-title-link`).
            title_is_link = public.card_title_is_link(LAW_1990_NUMBER)
            card_title_href = (
                public.card_title_href(LAW_1990_NUMBER) if title_is_link else ""
            )
            cta_count = public.card_cta_count(LAW_1990_NUMBER)
            cta_href = public.card_cta_href(LAW_1990_NUMBER) if cta_count else ""
            allure.attach(
                f"title_is_link={title_is_link} title_href={card_title_href!r} "
                f"cta_count={cta_count} cta_href={cta_href!r}",
                name="tc_134971 step 3 -- what the public card links to with no URL",
            )

        # Assert -- step 1/2
        assert not value_missing_after_clear, (
            "External Link URL reported the browser's own `valueMissing` after "
            "being emptied -- it is behaving as a REQUIRED field, but the Object "
            "definition declares it optional"
        )
        assert not refusal, (
            "expected no validation error against an empty External Link URL; the "
            f"page said {refusal!r} ({renderer_report})"
        )
        assert outcome == "saved" and success, (
            "expected the success toast after saving with an empty External Link "
            f"URL; the page reported {outcome!r} ({renderer_report})"
        )
        assert stored == "", (
            f"expected External Link URL to be stored empty; it reads {stored!r}"
        )
        assert status_after_publish == "Approved", (
            "expected the law entry to be published after Submit for Publishing; "
            f"its status is {status_after_publish!r}"
        )

        # Assert -- step 3
        assert card_visible, (
            f"the {LAW_1990_NUMBER} card is not rendered on the public Chamber's "
            "Law page after clearing its External Link URL"
        )
        assert card_icon_visible, "expected the card to render its icon"
        assert card_title == LAW_1990_TITLE, (
            f"expected the card title {LAW_1990_TITLE!r}; it reads {card_title!r}"
        )
        assert card_desc.strip(), "expected the card to render its description"
        broken_links = [
            f"{name}={href!r}"
            for name, rendered, href in (
                ("card title anchor", title_is_link, card_title_href),
                ("card CTA", bool(cta_count), cta_href),
            )
            if rendered and href.strip().lower() in EMPTY_DESTINATION_HREFS
        ]
        assert not broken_links, (
            "expected NO broken or empty-destination CTA on a law card whose "
            "External Link URL is empty -- the card should simply not offer one. "
            f"Rendered with a dead destination: {', '.join(broken_links)} "
            f"(cta_count={cta_count})"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the result
            pass
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore External Link URL"):
                _test_owned_reset(
                    _restore_external_link_url(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134971 Law 1990 External Link URL",
                )


# =========================================================================
# Batch 6 case data -- Display Order
# =========================================================================
# THE FIELD IS A SPINBUTTON, not a textbox (`<input type="number"
# name="ObjectField_displayOrder" required min="-2147483648"
# max="2147483647">`, no `step` -- read live, finding (s)). Nothing in this
# block may go through `fill_text()` / `field_value()` /
# `_wait_for_committed_value()` / `_observed_stored_value()`: those four are
# all bound to the `textbox` role and resolve ZERO controls here.
# `fill_number()` / `spinbutton_value()` on `ObjectAuthoringPage` are the
# correct pair, and `_observed_stored_number()` below is the numeric twin of
# `_observed_stored_value()` -- same polling contract, same "return the last
# value observed and let the caller assert" rule.
#
# WHICH LAYER REFUSES WHAT (measured live, finding (s)) -- the whole of this
# batch turns on it, and the six values land in four different places:
#
#   "2"    accepted; the Object's minimum rule passes.
#   "0"    passes the BROWSER (`min` is INT_MIN), so only the Object's named
#          rule can refuse it -- from `/validate`, rendered UNDER THE BOX.
#   "-1"   same as "0".
#   "2.5"  `stepMismatch`; `reportValidity()` blocks the submit NATIVELY and
#          the value never reaches the server. A native bubble is not in the
#          DOM -- the only observable trace is `el.validationMessage`.
#   "two"  the control refuses the keystrokes outright and the box stays
#          EMPTY, so the save is then blocked as a MISSING value.
#   ""     blocked natively (`required` + `valueMissing`).
#
# Every value below is the case's own literal, mirrored verbatim. Note the
# conflict with OBJECT-AUTHORING-GUIDE.md section 3's "order in multiples of
# 100" convention, reported and NOT silently resolved -- see finding (w):
# these values are transient (written, then restored to the captured
# baseline in the same test), unlike tc_134886's permanent reorder, which
# was escalated over exactly this and uses 100/200 instead.
DISPLAY_ORDER_VALID = "2"             # 134972 step 2; 134987 step 4
DISPLAY_ORDER_ZERO = "0"              # 134973 step 2, verbatim
DISPLAY_ORDER_NEGATIVE = "-1"         # 134973 step 3, verbatim
DISPLAY_ORDER_NON_INTEGER = "2.5"     # 134974 step 2, verbatim
DISPLAY_ORDER_TEXT = "two"            # 134974 step 3, verbatim
DISPLAY_ORDER_EMPTY = ""              # 134975 step 2
DISPLAY_ORDER_DUPLICATE = "1"         # 134987 steps 1-2, verbatim
# The precondition 134973/134974 state in their own step 1 ("with Display
# Order currently 2"). Live it is 200 on both records, so the tests
# ESTABLISH it themselves as a disclosed TEST_OWNED setup write -- otherwise
# step 4's "Display Order still reads 2" could never be true for any reason
# connected to the product.
DISPLAY_ORDER_PRECONDITION = "2"
# What a rounded 2.5 would look like. 134974 step 2's expected result names
# both ("not silently rounded to 2 or 3") and only ONE of them is
# distinguishable from "the value was retained" -- see that test's own note.
DISPLAY_ORDER_ROUNDED_UP = "3"

# The Object's ONLY named rule for this field, read live off the definition
# (`displayOrder >= 1`, rule name "Display Order minimum"), with BOTH
# shipped error labels. Matched in either language for the reason batches
# 3-5 already document: this account's own Liferay language is `ar_SA` and
# messages leak into an English UI, and no batch-6 case demands a literal
# message. Naming the RULE in either shipped language is NARROWER than
# "some refusal appeared", not looser.
#
# [!] THE CASES PARAPHRASE THIS RULE AND DO NOT QUOTE IT. 134973 says the
# error states "Display Order must be a positive integer"; the product's own
# rule label is "Display Order must be 1 or greater". The same constraint,
# different words -- and since the case supplies no quoted literal, the
# rule's own label is what is asserted. The difference is reported, not
# smoothed over.
# The Arabic label is COPIED programmatically out of finding (t) in this
# module's own docstring, not retyped -- a bidirectional string cannot be
# proof-read inline, and this one has to be byte-exact against the shipped
# label or the either-language match silently degrades to English-only.
DISPLAY_ORDER_MINIMUM_MESSAGES = (
    "Display Order must be 1 or greater",
    "يجب أن يكون ترتيب العرض 1 أو أكبر",
)

# 134987 step 2's expected result, in the product's own vocabulary. There is
# NO uniqueness rule on this object and no client-side duplicate check
# anywhere in the page's shipped JS (finding (u)), so nothing is expected to
# say any of this -- these are the words a duplicate refusal WOULD have to
# contain, and the assertion is scripted to the case anyway.
DUPLICATE_DISPLAY_ORDER_MARKERS = (
    "already in use",
    "already uses",
    "duplicate",
    "unique",
)


def _observed_stored_number(
    admin,
    entry_code,
    field_label,
    expected,
    locale=CMS_LOCALE_EN,
    timeout=PUBLISH_CONFIRM_TIMEOUT,
) -> str:
    """Polls a FRESH navigation until the record's SPINBUTTON stores
    `expected`, and returns the LAST value observed -- match or no match.

    The exact twin of `_observed_stored_value()` (same polling contract, same
    "nothing is swallowed, the caller asserts on the return" rule), differing
    only in which read it calls: `spinbutton_value()` instead of
    `field_value()`. It cannot simply reuse that helper -- `field_value()` is
    bound to the `textbox` role and Display Order is an
    `<input type="number">`, so the textbox lookup resolves ZERO controls
    here and raises on every poll.

    The locale default is `en` rather than `None`, unlike its textbox twin:
    this field's accessible name is `Display Order` on an `/en` render and
    the Arabic label on an `/ar` one, and this account's own Liferay language
    is `ar_SA` -- an unpinned re-read resolves ZERO controls the moment the
    session drifts."""
    observed = {"value": ""}

    def _committed() -> bool:
        observed["value"] = admin.open_law_entry(
            entry_code, locale=locale
        ).spinbutton_value(field_label)
        return observed["value"] == expected

    try:
        wait_until(_committed, timeout=timeout, poll=3.0)
    except Exception:  # noqa: BLE001 -- the last observed value IS the result
        pass
    return observed["value"]


def _establish_display_order(
    admin, entry_code, field_label, value, locale=CMS_LOCALE_EN
) -> str:
    """DISCLOSED TEST_OWNED PRECONDITION WRITE -- puts `value` into a
    record's Display Order and returns what the record actually holds
    afterwards, so the caller can ASSERT the precondition instead of
    assuming it.

    134973/134974 open "with Display Order currently 2" and 134987 with "an
    existing active entry holding Display Order 1"; live, both records hold
    200 (finding (v)). Without this, 134973 step 4's "Display Order still
    reads 2" could never be true for any reason connected to the product,
    and 134987 step 2 would write 200 onto a record that already holds 200 --
    i.e. test nothing at all.

    Idempotent (a record already holding `value` is left alone) and never
    silent: the return value is the real, re-read state, so a precondition
    that did not commit fails its test at step 1 rather than at step 4 for
    the wrong reason. The caller's `finally` restores the captured
    baseline."""
    authoring = admin.open_law_entry(entry_code, locale=locale)
    if authoring.spinbutton_value(field_label) == value:
        return value
    authoring.fill_number(field_label, value)
    authoring.submit_for_publishing()
    return _observed_stored_number(
        admin, entry_code, field_label, value, locale=locale
    )


def _restore_display_order(
    admin, entry_code, baseline_value, baseline_status, locale=CMS_LOCALE_EN
):
    """TEST_OWNED restore for Display Order, with every read pinned to one
    interface locale.

    Same contract as `_restore_external_link_url()` -- restore, then PROVE it
    from a fresh navigation, never a post-save-reflowed DOM -- and it cannot
    reuse `_restore_law_entry_text()` for the same reason nothing else in
    this batch can: that helper drives `fill_text()`/`field_value()`, which
    are bound to the `textbox` role, and this control is a spinbutton. A
    TEST_OWNED restore that cannot find its own field is exactly the failure
    this module exists to prevent."""
    label = admin.DISPLAY_ORDER_LABEL

    def _restore():
        authoring = admin.open_law_entry(entry_code, locale=locale)
        if authoring.spinbutton_value(label) != baseline_value:
            if authoring.current_status() == "Approved":
                authoring.fill_number(label, baseline_value)
                _publish_and_confirm(authoring)
            else:
                _unpublish_and_confirm(authoring)
                authoring.fill_number(label, baseline_value)
                if baseline_status == "Approved":
                    _publish_and_confirm(authoring)
                else:
                    authoring.save_as_draft()

        # PROVE it -- fresh navigation, never a post-save-reflowed DOM.
        authoring = admin.open_law_entry(entry_code, locale=locale)
        actual_value = authoring.spinbutton_value(label)
        actual_status = authoring.current_status()
        if actual_value != baseline_value:
            raise AssertionError(
                "TEST_OWNED restore did not commit: Display Order on "
                f"{entry_code} reads {actual_value!r}, expected the captured "
                f"baseline {baseline_value!r}"
            )
        if actual_status != baseline_status:
            raise AssertionError(
                f"TEST_OWNED restore did not commit: {entry_code} status is "
                f"{actual_status!r}, expected the captured baseline "
                f"{baseline_status!r}"
            )

    return _restore


def _prove_public_card_order(
    public, expected_order, timeout=PUBLIC_REFLECT_AFTER_PUBLISH_TIMEOUT
):
    """TEST_OWNED restore PROOF for the one case in this module that
    reorders real, published editorial content: re-reads the ANONYMOUS
    public Chamber's Law page until both cards are back in the order
    captured before anything was mutated, and raises with the order it
    actually sees if they are not.

    134987 writes Display Order 1 onto one live card and then onto the
    other, which is a visible change to the real website -- so restoring the
    two CMS values is only half the job, and the public render is the half a
    visitor would notice. Read through a genuinely anonymous context per
    this project's logged-out-visibility rule; an authenticated read would
    prove only that a signed-in editor sees the right order.

    The two records hold the SAME Display Order at baseline (200/200,
    finding (u)), so their relative order is decided by the renderer's own
    insertion-ordered tie-break -- stable, and CAPTURED rather than
    assumed."""

    def _restore():
        def _ordered() -> bool:
            public.open_chambers_law()
            return public.card_numbers() == expected_order

        try:
            wait_until(_ordered, timeout=timeout, poll=3.0)
        except Exception:  # noqa: BLE001 -- re-raised with the real order
            raise AssertionError(
                "TEST_OWNED restore did not reach the public page: the "
                "anonymous Chamber's Law page renders its cards as "
                f"{public.card_numbers()!r}, expected the order captured "
                f"before this test mutated anything, {expected_order!r}"
            )

    return _restore


# =========================================================================
# Batch 6 -- Display Order (134972-134975, 134987)
# =========================================================================


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid positive Display Order is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134972
@pytest.mark.traceability("134972")
@allure.label("pbi", "129394")
@allure.label("testcase", "134972")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134972_a_valid_positive_display_order_is_accepted_and_saved(
    page,
):
    # "Click Save" can only mean **Submit for Publishing** -- there is no
    # button called Save on this form, and `Save as Draft` sets
    # `formnovalidate` and strips `required` off every control, so it
    # validates nothing (module docstring, point 1).
    #
    # DISCLOSED CONVENTION CONFLICT, reported and not silently resolved
    # (finding (w)): OBJECT-AUTHORING-GUIDE.md section 3 numbers Display
    # Order in multiples of 100, and this case's literal is 2. The value is
    # TRANSIENT here -- written, then restored to the runtime-captured
    # baseline in the same test -- so the case's own literal is mirrored
    # exactly rather than substituted. tc_134886, whose reorder is
    # PERMANENT, does the opposite and was escalated over it.
    admin = ChambersLawAdminPage(page)
    label = admin.DISPLAY_ORDER_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.spinbutton_value(label)
            baseline_status = authoring.current_status()
            # Resolving through the STRICT role lookup is itself the
            # "exactly one Display Order control" proof; the dict then says
            # whether that one control is editable.
            control_state = form.number_validity(label)

        with allure.step(
            f"Enter {DISPLAY_ORDER_VALID} in Display Order and click Submit for "
            "Publishing"
        ):
            authoring.fill_number(label, DISPLAY_ORDER_VALID)
            typed = form.live_number_value(label)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()
            renderer_report = form.save_message_report()

        with allure.step("Reload the law entry record"):
            stored = _observed_stored_number(
                admin, LAW_1990_ENTRY_CODE, label, DISPLAY_ORDER_VALID
            )
            shape = _outcome_shape(refusal, success, DISPLAY_ORDER_VALID, stored)
            allure.attach(
                f"{shape}\n{renderer_report}",
                name="tc_134972 -- outcome and renderers",
            )

        # Assert -- step 1
        assert not control_state["readonly"] and not control_state["disabled"], (
            "expected the law entry record to open with Display Order EDITABLE; "
            f"the control reports {control_state!r}"
        )

        # Assert -- step 2
        assert typed == DISPLAY_ORDER_VALID, (
            f"the Display Order box holds {typed!r} rather than "
            f"{DISPLAY_ORDER_VALID!r} before the save -- the control itself "
            "mangled the value"
        )
        assert not refusal, (
            f"a valid positive Display Order was rejected: {refusal!r}. WHICH "
            f"SHAPE: {shape}. WHAT EACH RENDERER SAID: {renderer_report}"
        )
        assert outcome == "saved" and success, (
            "expected the success toast after saving a valid positive Display "
            f"Order; the page reported {outcome!r}. WHAT EACH RENDERER SAID: "
            f"{renderer_report}"
        )

        # Assert -- step 3
        assert stored == DISPLAY_ORDER_VALID, (
            f"expected Display Order to read {DISPLAY_ORDER_VALID!r} after the "
            f"reload; it reads {stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Display Order"):
                _test_owned_reset(
                    _restore_display_order(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134972 Law 1990 Display Order",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a zero or negative Display Order is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134973
@pytest.mark.traceability("134973")
@allure.label("pbi", "129394")
@allure.label("testcase", "134973")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134973_a_zero_or_negative_display_order_is_rejected_on_save(
    page,
):
    # THIS IS A `/validate` TEST, NOT A NATIVE ONE, and the distinction is
    # the finding the case turns on. Read live (finding (s)): the control
    # carries `min="-2147483648"`, so BOTH 0 and -1 are perfectly VALID as
    # far as the browser is concerned (`el.validity.valid === true`,
    # `validationMessage === ""`). The only thing that can refuse them is the
    # Object's own named rule `displayOrder >= 1`, which arrives from the
    # `/validate` pre-flight and -- because its message contains the words
    # "Display Order" -- is tied to the control by `controlForMessage()` and
    # rendered UNDER THE BOX as `<div data-qc-oel-field-error>`, never in the
    # red bar. A bar-only read returns "" for it and would report a working
    # product as a silent refusal, which is exactly the mistake that produced
    # and then retracted bug #141989. Every read below therefore goes through
    # the WIDENED reader (`save_refusal_text()` = field notes + fragment
    # notes + bar).
    #
    # PRECONDITION IS ESTABLISHED, NOT ASSUMED. The case opens "with Display
    # Order currently 2"; live, this record holds 200.
    # `_establish_display_order()` writes 2 first as a disclosed TEST_OWNED
    # setup step and the test ASSERTS it landed -- otherwise step 4's
    # "Display Order still reads 2" could never be true for any
    # product-related reason.
    #
    # Each attempt runs on a FRESHLY NAVIGATED form: a refused save leaves
    # its own under-the-box note on screen, and reading step 3's refusal off
    # a page still carrying step 2's would report the wrong message.
    admin = ChambersLawAdminPage(page)
    label = admin.DISPLAY_ORDER_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS "
            "with Display Order currently 2"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            baseline_value = authoring.spinbutton_value(label)
            baseline_status = authoring.current_status()
            opened_with = _establish_display_order(
                admin, LAW_1990_ENTRY_CODE, label, DISPLAY_ORDER_PRECONDITION
            )

        with allure.step(
            f"Enter {DISPLAY_ORDER_ZERO} in Display Order and click Submit for "
            "Publishing"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            authoring.fill_number(label, DISPLAY_ORDER_ZERO)
            native_zero = form.number_validity(label)
            outcome_zero = form.submit_expecting_refusal()
            refusal_zero = form.save_refusal_text()
            success_zero = form.success_message_text()
            report_zero = form.save_message_report()
            stored_zero = _observed_stored_number(
                admin,
                LAW_1990_ENTRY_CODE,
                label,
                DISPLAY_ORDER_ZERO,
                timeout=REFUSAL_RENDER_TIMEOUT,
            )
            shape_zero = _outcome_shape(
                refusal_zero, success_zero, DISPLAY_ORDER_ZERO, stored_zero
            )
            allure.attach(
                f"{shape_zero}\nnative validity={native_zero!r}\n{report_zero}",
                name="tc_134973 step 2 (0) -- outcome and renderers",
            )

        with allure.step(
            f"Enter {DISPLAY_ORDER_NEGATIVE} in Display Order and click Submit for "
            "Publishing"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            authoring.fill_number(label, DISPLAY_ORDER_NEGATIVE)
            native_negative = form.number_validity(label)
            outcome_negative = form.submit_expecting_refusal()
            refusal_negative = form.save_refusal_text()
            success_negative = form.success_message_text()
            report_negative = form.save_message_report()
            stored_negative = _observed_stored_number(
                admin,
                LAW_1990_ENTRY_CODE,
                label,
                DISPLAY_ORDER_NEGATIVE,
                timeout=REFUSAL_RENDER_TIMEOUT,
            )
            shape_negative = _outcome_shape(
                refusal_negative,
                success_negative,
                DISPLAY_ORDER_NEGATIVE,
                stored_negative,
            )
            allure.attach(
                f"{shape_negative}\nnative validity={native_negative!r}\n"
                f"{report_negative}",
                name="tc_134973 step 3 (-1) -- outcome and renderers",
            )

        with allure.step("Reload the law entry record"):
            reloaded = admin.open_law_entry(
                LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN
            ).spinbutton_value(label)

        # Assert -- step 1
        assert opened_with == DISPLAY_ORDER_PRECONDITION, (
            "precondition: expected the law entry record to open with Display "
            f"Order {DISPLAY_ORDER_PRECONDITION!r}; it holds {opened_with!r} "
            f"(its captured baseline was {baseline_value!r})"
        )

        # Assert -- step 2 (0)
        assert not success_zero, (
            f"expected NO success toast for Display Order {DISPLAY_ORDER_ZERO!r}; "
            f"the page showed {success_zero!r}"
        )
        assert stored_zero != DISPLAY_ORDER_ZERO, (
            f"Display Order {DISPLAY_ORDER_ZERO!r} WAS stored on "
            f"{LAW_1990_ENTRY_CODE}"
        )
        assert outcome_zero == "refused" and refusal_zero, (
            "expected the save to be blocked with a validation error against "
            f"Display Order {DISPLAY_ORDER_ZERO!r}. WHICH SHAPE: {shape_zero}. "
            f"THE BROWSER'S OWN VERDICT: {native_zero!r} (note `min` is INT_MIN "
            "on this control, so the browser passes 0 and only the Object's "
            f"named rule can refuse it). WHAT EACH RENDERER SAID: {report_zero}"
        )
        assert any(m in refusal_zero for m in DISPLAY_ORDER_MINIMUM_MESSAGES), (
            "expected the validation error to state the Display Order minimum "
            f"rule, in either shipped language {DISPLAY_ORDER_MINIMUM_MESSAGES!r}; "
            f"the page said {refusal_zero!r}. (The case words this rule as "
            "'Display Order must be a positive integer'; the product's own rule "
            "label is 'Display Order must be 1 or greater' -- the same "
            "constraint, different words, and the case quotes no literal.)"
        )

        # Assert -- step 3 (-1)
        assert not success_negative, (
            "expected NO success toast for Display Order "
            f"{DISPLAY_ORDER_NEGATIVE!r}; the page showed {success_negative!r}"
        )
        assert stored_negative != DISPLAY_ORDER_NEGATIVE, (
            f"Display Order {DISPLAY_ORDER_NEGATIVE!r} WAS stored on "
            f"{LAW_1990_ENTRY_CODE}"
        )
        assert outcome_negative == "refused" and refusal_negative, (
            "expected the save to be blocked AGAIN for Display Order "
            f"{DISPLAY_ORDER_NEGATIVE!r}. WHICH SHAPE: {shape_negative}. THE "
            f"BROWSER'S OWN VERDICT: {native_negative!r}. WHAT EACH RENDERER "
            f"SAID: {report_negative}"
        )
        assert any(m in refusal_negative for m in DISPLAY_ORDER_MINIMUM_MESSAGES), (
            "expected the SAME Display Order minimum rule to be stated for -1, in "
            f"either shipped language {DISPLAY_ORDER_MINIMUM_MESSAGES!r}; the page "
            f"said {refusal_negative!r}"
        )

        # Assert -- step 4
        assert reloaded == DISPLAY_ORDER_PRECONDITION, (
            f"expected Display Order to still read {DISPLAY_ORDER_PRECONDITION!r} "
            f"-- neither {DISPLAY_ORDER_ZERO!r} nor {DISPLAY_ORDER_NEGATIVE!r} "
            f"stored; it reads {reloaded!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Display Order"):
                _test_owned_reset(
                    _restore_display_order(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134973 Law 1990 Display Order",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a non-integer Display Order is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134974
@pytest.mark.traceability("134974")
@allure.label("pbi", "129394")
@allure.label("testcase", "134974")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134974_a_non_integer_display_order_is_rejected_on_save(page):
    # THE TWO STEPS ARE REFUSED BY TWO DIFFERENT MECHANISMS, and neither is
    # the `/validate` rule that refuses 134973's 0 and -1:
    #
    #   2.5   `fill()` puts it in the box, the control reports
    #         `stepMismatch` (a number input's implicit step is 1), and
    #         `reportValidity()` cancels the submit NATIVELY. The value never
    #         reaches the server, and the native bubble is NOT in the DOM --
    #         `el.validationMessage` is the only observable trace, which is
    #         why `number_validity()` is read and asserted on rather than the
    #         page's own renderers.
    #   'two' the box REFUSES THE KEYSTROKES ENTIRELY and stays empty
    #         (measured live, finding (s)), so the save is then blocked as a
    #         MISSING value, not as a malformed one. Playwright's own
    #         `fill()` cannot even attempt it ("Cannot type text into
    #         input[type=number]"), which is why `type_into_number()` exists.
    #
    # [!] STEP 3 IS PART-EXPECTED TO FAIL, and is scripted to the case anyway
    # (Result Integrity -- an assertion is never loosened to match observed
    # behaviour). No integer-FORMAT message can ever be produced for 'two',
    # because the characters never enter the field. "The save was blocked"
    # and "the box would not accept it" are two different product outcomes,
    # so the assertions below separate them, assert on the OBSERVED OUTCOME
    # SHAPE rather than on a specific error string, and record WHAT ACTUALLY
    # HAPPENED -- letting the report distinguish a product defect from a
    # case-wording defect.
    #
    # [!] "NOT SILENTLY ROUNDED TO 2 OR 3" IS ONLY HALF-CHECKABLE, and the
    # case's own precondition is why: with Display Order already 2, a value
    # rounded DOWN to 2 is indistinguishable from the value being retained.
    # Rounding UP to 3 is fully checkable and is asserted. The ambiguity is
    # reported in the assertion message, not resolved by changing the case.
    admin = ChambersLawAdminPage(page)
    label = admin.DISPLAY_ORDER_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS "
            "with Display Order currently 2"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            baseline_value = authoring.spinbutton_value(label)
            baseline_status = authoring.current_status()
            opened_with = _establish_display_order(
                admin, LAW_1990_ENTRY_CODE, label, DISPLAY_ORDER_PRECONDITION
            )

        with allure.step(
            f"Enter {DISPLAY_ORDER_NON_INTEGER} in Display Order and click Submit "
            "for Publishing"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            authoring.fill_number(label, DISPLAY_ORDER_NON_INTEGER)
            typed_fraction = form.live_number_value(label)
            native_fraction = form.number_validity(label)
            outcome_fraction = form.submit_expecting_refusal()
            refusal_fraction = form.save_refusal_text()
            success_fraction = form.success_message_text()
            report_fraction = form.save_message_report()
            stored_fraction = _observed_stored_number(
                admin,
                LAW_1990_ENTRY_CODE,
                label,
                DISPLAY_ORDER_NON_INTEGER,
                timeout=REFUSAL_RENDER_TIMEOUT,
            )
            shape_fraction = _outcome_shape(
                refusal_fraction,
                success_fraction,
                DISPLAY_ORDER_NON_INTEGER,
                stored_fraction,
            )
            allure.attach(
                f"{shape_fraction}\nbox held={typed_fraction!r}\n"
                f"native validity={native_fraction!r}\n{report_fraction}",
                name="tc_134974 step 2 (2.5) -- outcome and renderers",
            )

        with allure.step(
            f"Enter the text {DISPLAY_ORDER_TEXT!r} in Display Order and click "
            "Submit for Publishing"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            # TYPED, not filled: `fill()` raises "Cannot type text into
            # input[type=number]" and would never reach the product at all.
            typed_text = form.type_into_number(label, DISPLAY_ORDER_TEXT)
            native_text = form.number_validity(label)
            outcome_text = form.submit_expecting_refusal()
            refusal_text = form.save_refusal_text()
            success_text = form.success_message_text()
            report_text = form.save_message_report()
            stored_text = _observed_stored_number(
                admin,
                LAW_1990_ENTRY_CODE,
                label,
                DISPLAY_ORDER_TEXT,
                timeout=REFUSAL_RENDER_TIMEOUT,
            )
            shape_text = _outcome_shape(
                refusal_text, success_text, DISPLAY_ORDER_TEXT, stored_text
            )
            allure.attach(
                f"{shape_text}\nbox held={typed_text!r}\n"
                f"native validity={native_text!r}\n{report_text}",
                name="tc_134974 step 3 ('two') -- outcome and renderers",
            )

        with allure.step("Reload the law entry record"):
            reloaded = admin.open_law_entry(
                LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN
            ).spinbutton_value(label)

        # Assert -- step 1
        assert opened_with == DISPLAY_ORDER_PRECONDITION, (
            "precondition: expected the law entry record to open with Display "
            f"Order {DISPLAY_ORDER_PRECONDITION!r}; it holds {opened_with!r} "
            f"(its captured baseline was {baseline_value!r})"
        )

        # Assert -- step 2 (2.5)
        assert not success_fraction, (
            "expected NO success toast for Display Order "
            f"{DISPLAY_ORDER_NON_INTEGER!r}; the page showed {success_fraction!r}"
        )
        assert stored_fraction != DISPLAY_ORDER_NON_INTEGER, (
            f"Display Order {DISPLAY_ORDER_NON_INTEGER!r} WAS stored on "
            f"{LAW_1990_ENTRY_CODE}"
        )
        assert native_fraction["stepMismatch"] or refusal_fraction, (
            "expected the save to be blocked with an integer-format validation "
            f"error for {DISPLAY_ORDER_NON_INTEGER!r}. WHICH SHAPE: "
            f"{shape_fraction}. THE BROWSER'S OWN VERDICT: {native_fraction!r} "
            f"(the box held {typed_fraction!r}, and the page reported "
            f"{outcome_fraction!r}). WHAT EACH RENDERER SAID: {report_fraction}"
        )
        assert stored_fraction != DISPLAY_ORDER_ROUNDED_UP, (
            f"{DISPLAY_ORDER_NON_INTEGER!r} was SILENTLY ROUNDED UP -- Display "
            f"Order now reads {stored_fraction!r}"
        )
        assert stored_fraction == DISPLAY_ORDER_PRECONDITION, (
            f"expected Display Order to retain {DISPLAY_ORDER_PRECONDITION!r} "
            f"after the refused {DISPLAY_ORDER_NON_INTEGER!r}; it reads "
            f"{stored_fraction!r}. (Read this one carefully: because the case's "
            "own precondition is 2, a value rounded DOWN to 2 is "
            "indistinguishable from the value being retained -- only the "
            "round-UP half is decidable, and it is asserted separately above.)"
        )

        # Assert -- step 3 ('two')
        assert not success_text, (
            f"expected NO success toast for the text {DISPLAY_ORDER_TEXT!r}; the "
            f"page showed {success_text!r}"
        )
        assert stored_text != DISPLAY_ORDER_TEXT, (
            f"the text {DISPLAY_ORDER_TEXT!r} WAS stored as the Display Order on "
            f"{LAW_1990_ENTRY_CODE}"
        )
        rejected_somehow = (
            typed_text != DISPLAY_ORDER_TEXT
            or bool(refusal_text)
            or not native_text["valid"]
        )
        assert rejected_somehow, (
            f"expected the text {DISPLAY_ORDER_TEXT!r} to be rejected. WHAT "
            f"ACTUALLY HAPPENED: the box held {typed_text!r} after typing (empty "
            "means the numeric control discarded every keystroke, which is a "
            "rejection BY THE CONTROL rather than by the save), the browser's "
            f"verdict was {native_text!r}, the page reported {outcome_text!r}, "
            f"WHICH SHAPE: {shape_text}, and WHAT EACH RENDERER SAID: "
            f"{report_text}"
        )
        integer_format_error = (
            any(m in refusal_text for m in DISPLAY_ORDER_MINIMUM_MESSAGES)
            or "integer" in refusal_text.lower()
            or native_text["stepMismatch"]
            or native_text["badInput"]
        )
        assert integer_format_error, (
            "expected an integer-FORMAT validation error for the text "
            f"{DISPLAY_ORDER_TEXT!r}. WHAT ACTUALLY HAPPENED: the box held "
            f"{typed_text!r}, the browser's verdict was {native_text!r} and the "
            f"page said {refusal_text!r}. If the box is empty and the verdict is "
            "`valueMissing`, the letters never entered the field at all and the "
            "save was blocked as a MISSING value -- which IS a rejection, but "
            "not the integer-format error this step's expected result names; "
            "that is a case-wording defect, not a product defect. WHICH SHAPE: "
            f"{shape_text}. WHAT EACH RENDERER SAID: {report_text}"
        )

        # Assert -- step 4
        assert reloaded == DISPLAY_ORDER_PRECONDITION, (
            f"expected Display Order to still read {DISPLAY_ORDER_PRECONDITION!r}; "
            f"it reads {reloaded!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Display Order"):
                _test_owned_reset(
                    _restore_display_order(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134974 Law 1990 Display Order",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Display Order is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134975
@pytest.mark.traceability("134975")
@allure.label("pbi", "129394")
@allure.label("testcase", "134975")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134975_an_empty_display_order_is_rejected_on_save(page):
    # A STAGE-2a TEST -- the BROWSER's own `required` check, exactly like the
    # empty Law Number of 134945. Confirmed live (finding (s)):
    # `input[name="ObjectField_displayOrder"]` carries `required`, and
    # Submit for Publishing restores the constraint before calling
    # `checkValidity()`/`reportValidity()`. The native bubble is NOT in the
    # DOM, so the observable trace is the control's own validity state --
    # which IS "a required-field validation error against Display Order".
    # The widened page-level reader is still read and reported, because a
    # required-field message CAN also arrive under the box from `/validate`,
    # and the assertion accepts either.
    #
    # NO PRECONDITION WRITE HERE, unlike 134973/134974: this case asks only
    # for "Display Order populated", which the live record already satisfies,
    # and step 3 asks for "its PREVIOUS value" rather than a literal. The
    # runtime-captured baseline is therefore the expected value, and nothing
    # is written before the step under test.
    admin = ChambersLawAdminPage(page)
    label = admin.DISPLAY_ORDER_LABEL
    baseline_value = None
    baseline_status = None

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS "
            "with Display Order populated"
        ):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            baseline_value = authoring.spinbutton_value(label)
            baseline_status = authoring.current_status()

        with allure.step(
            "Clear Display Order completely and click Submit for Publishing"
        ):
            authoring.fill_number(label, DISPLAY_ORDER_EMPTY)
            cleared_to = form.live_number_value(label)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()
            native = form.number_validity(label)
            renderer_report = form.save_message_report()

        with allure.step("Reload the law entry record"):
            stored = admin.open_law_entry(
                LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN
            ).spinbutton_value(label)
            shape = _outcome_shape(refusal, success, DISPLAY_ORDER_EMPTY, stored)
            allure.attach(
                f"{shape}\nnative validity={native!r}\n{renderer_report}",
                name="tc_134975 -- outcome and renderers",
            )

        # Assert -- step 1
        assert baseline_value, (
            "precondition: expected the law entry record to open with Display "
            "Order populated; it opened empty"
        )

        # Assert -- step 2
        assert cleared_to == DISPLAY_ORDER_EMPTY, (
            f"Display Order would not clear -- the box still holds {cleared_to!r}"
        )
        assert not success and outcome != "saved", (
            "expected NO success toast for an empty Display Order; the page "
            f"showed {success!r} (outcome {outcome!r})"
        )
        assert native["valueMissing"] or (label.lower() in refusal.lower()), (
            "expected a required-field validation error against Display Order. "
            f"THE BROWSER'S OWN VERDICT: {native!r}. WHICH SHAPE: {shape}. WHAT "
            f"EACH RENDERER SAID: {renderer_report}"
        )

        # Assert -- step 3
        assert stored == baseline_value, (
            "expected Display Order to retain its previous value "
            f"{baseline_value!r}; it reads {stored!r}"
        )
    finally:
        if baseline_value is not None:
            with allure.step("TEST_OWNED reset -- restore Display Order"):
                _test_owned_reset(
                    _restore_display_order(
                        admin,
                        LAW_1990_ENTRY_CODE,
                        baseline_value,
                        baseline_status,
                    ),
                    label="tc_134975 Law 1990 Display Order",
                )


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title(
    "Verify that saving a law entry with a Display Order already used by another "
    "entry is rejected"
)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134987
@pytest.mark.traceability("134987")
@allure.label("pbi", "129394")
@allure.label("testcase", "134987")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134987_saving_a_law_entry_with_a_display_order_already_used_by_another_entry_is_rejected(
    browser, page
):
    # [!] STEPS 2 AND 3 ARE EXPECTED TO FAIL, and are scripted to the case
    # anyway (Result Integrity -- an assertion is never loosened to match
    # observed behaviour). THERE IS NO UNIQUENESS RULE ON THIS OBJECT
    # (finding (u)): the five active rules on LawEntry cap three text
    # lengths, check the External Link URL's format and require
    # `displayOrder >= 1` -- none is a uniqueness constraint, there is no
    # `unique` objectFieldSetting on the field, and the only
    # "duplicate"/"already uses" strings anywhere in the page's shipped JS
    # belong to the DEPARTMENT name guard and the double-submit guard. The
    # live data proves it independently: BOTH records already hold Display
    # Order 200 right now, both published, both rendered. What the product
    # actually does is accept the duplicate and render the two cards in an
    # arbitrary, insertion-ordered sequence.
    #
    # THE CASE'S PRECONDITION IS NOT TRUE OF THE LIVE DATA and is ESTABLISHED
    # (finding (v)): 'Law No. 11 of 1990' is stated to hold Display Order 1;
    # live it holds 200. Without writing 1 onto it first, step 2's "enter a
    # Display Order already used by another entry" would mean writing 200
    # onto a record that already holds 200 -- testing nothing at all.
    #
    # THIS TEST CHANGES THE LIVE PUBLIC SITE, on TWO real published records.
    # Both baselines (Display Order + status) are captured at runtime and
    # restored in `finally`, each restore PROVED from a fresh navigation --
    # and then the ANONYMOUS public page is re-read until both cards are back
    # in the order captured before anything was mutated. Nothing is ever
    # deleted (standing project rule).
    #
    # THE ENTRIES LIST DOES NOT RENDER A DISPLAY ORDER COLUMN. Its columns
    # are Entry / Status / Last modified (confirmed live), so step 3's
    # "reload the Law Entry list and read both entries' Display Order values"
    # is performed as the list reload the step names PLUS a read of each
    # record's own form, which is the only place the value is rendered. The
    # gap is reported, not silently reinterpreted.
    admin = ChambersLawAdminPage(page)
    label = admin.DISPLAY_ORDER_LABEL
    baseline_1990 = None
    baseline_1990_status = None
    baseline_1996 = None
    baseline_1996_status = None
    baseline_card_order = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    public = ChambersLawPage(anon_page)

    try:
        with allure.step(
            "Open the Law Entry list under the Chamber's Law page in Liferay CMS "
            "with an existing active entry 'Law No. 11 of 1990' holding Display "
            "Order 1"
        ):
            # Captured BEFORE anything is mutated -- this is what the
            # `finally` restore is proved against. Read as a genuinely
            # ANONYMOUS visitor, per this project's logged-out-visibility
            # rule.
            public.open_chambers_law()
            baseline_card_order = public.card_numbers()

            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            baseline_1990 = authoring.spinbutton_value(label)
            baseline_1990_status = authoring.current_status()
            authoring = admin.open_law_entry(LAW_1996_ENTRY_CODE, locale=CMS_LOCALE_EN)
            baseline_1996 = authoring.spinbutton_value(label)
            baseline_1996_status = authoring.current_status()

            first_entry_order = _establish_display_order(
                admin, LAW_1990_ENTRY_CODE, label, DISPLAY_ORDER_DUPLICATE
            )
            entries = admin.open_law_entries_list(locale=CMS_LOCALE_EN)
            first_entry_listed = entries.row_visible(LAW_1990_TITLE)

        with allure.step(
            f"Open a second law entry, enter Display Order {DISPLAY_ORDER_DUPLICATE} "
            "and click Submit for Publishing"
        ):
            authoring = admin.open_law_entry(LAW_1996_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            authoring.fill_number(label, DISPLAY_ORDER_DUPLICATE)
            outcome_dup = form.submit_expecting_refusal()
            refusal_dup = form.save_refusal_text()
            success_dup = form.success_message_text()
            report_dup = form.save_message_report()
            stored_dup = _observed_stored_number(
                admin,
                LAW_1996_ENTRY_CODE,
                label,
                DISPLAY_ORDER_DUPLICATE,
                timeout=REFUSAL_RENDER_TIMEOUT,
            )
            shape_dup = _outcome_shape(
                refusal_dup, success_dup, DISPLAY_ORDER_DUPLICATE, stored_dup
            )
            allure.attach(
                f"{shape_dup}\n{report_dup}",
                name="tc_134987 step 2 (duplicate Display Order) -- outcome",
            )

        with allure.step(
            "Reload the Law Entry list and read both entries' Display Order values"
        ):
            entries = admin.open_law_entries_list(locale=CMS_LOCALE_EN)
            both_listed = entries.row_visible(LAW_1990_TITLE)
            # The list renders Entry / Status / Last modified only -- the
            # values themselves are read off each record's own form.
            reread_1990 = admin.open_law_entry(
                LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN
            ).spinbutton_value(label)
            reread_1996 = admin.open_law_entry(
                LAW_1996_ENTRY_CODE, locale=CMS_LOCALE_EN
            ).spinbutton_value(label)

        with allure.step(
            f"Change the second entry's Display Order to {DISPLAY_ORDER_VALID} and "
            "click Submit for Publishing"
        ):
            authoring = admin.open_law_entry(LAW_1996_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            authoring.fill_number(label, DISPLAY_ORDER_VALID)
            outcome_unique = form.submit_expecting_refusal()
            refusal_unique = form.save_refusal_text()
            success_unique = form.success_message_text()
            report_unique = form.save_message_report()
            stored_unique = _observed_stored_number(
                admin, LAW_1996_ENTRY_CODE, label, DISPLAY_ORDER_VALID
            )
            shape_unique = _outcome_shape(
                refusal_unique, success_unique, DISPLAY_ORDER_VALID, stored_unique
            )
            allure.attach(
                f"{shape_unique}\n{report_unique}",
                name="tc_134987 step 4 (unique Display Order 2) -- outcome",
            )

        # Assert -- step 1
        assert first_entry_order == DISPLAY_ORDER_DUPLICATE, (
            f"precondition: expected the existing entry {LAW_1990_NUMBER!r} to "
            f"hold Display Order {DISPLAY_ORDER_DUPLICATE!r}; it holds "
            f"{first_entry_order!r} (its captured baseline was {baseline_1990!r})"
        )
        assert first_entry_listed, (
            f"expected the Law Entry list to show {LAW_1990_TITLE!r}"
        )

        # Assert -- step 2
        assert not success_dup, (
            "expected NO success toast when saving a Display Order already used "
            f"by another entry; the page showed {success_dup!r}"
        )
        assert stored_dup != DISPLAY_ORDER_DUPLICATE, (
            f"the duplicate Display Order {DISPLAY_ORDER_DUPLICATE!r} WAS stored "
            f"on {LAW_1996_ENTRY_CODE} -- both {LAW_1990_NUMBER!r} and "
            f"{LAW_1996_NUMBER!r} now hold it"
        )
        assert outcome_dup == "refused" and refusal_dup, (
            "expected the save to be blocked with a validation error stating the "
            f"Display Order is already in use. WHICH SHAPE: {shape_dup}. WHAT "
            f"EACH RENDERER SAID: {report_dup}"
        )
        assert any(
            marker in refusal_dup.lower()
            for marker in DUPLICATE_DISPLAY_ORDER_MARKERS
        ), (
            "expected the validation error to say the Display Order is ALREADY "
            f"IN USE; the page said {refusal_dup!r}. For the reader: this object "
            "declares no uniqueness rule and no `unique` field setting, so there "
            "may be no such message for it to render at all"
        )

        # Assert -- step 3
        assert both_listed, (
            f"expected the reloaded Law Entry list to still show {LAW_1990_TITLE!r}"
        )
        assert reread_1990 == DISPLAY_ORDER_DUPLICATE, (
            f"expected {LAW_1990_NUMBER!r} to still hold Display Order "
            f"{DISPLAY_ORDER_DUPLICATE!r}; it holds {reread_1990!r}"
        )
        assert reread_1996 == baseline_1996, (
            f"expected {LAW_1996_NUMBER!r} to retain its previous Display Order "
            f"{baseline_1996!r}; it holds {reread_1996!r}"
        )
        assert reread_1990 != reread_1996, (
            "expected NO two entries to share Display Order "
            f"{DISPLAY_ORDER_DUPLICATE!r}; {LAW_1990_NUMBER!r} holds "
            f"{reread_1990!r} and {LAW_1996_NUMBER!r} holds {reread_1996!r}"
        )

        # Assert -- step 4
        assert not refusal_unique, (
            f"the unique Display Order {DISPLAY_ORDER_VALID!r} was rejected: "
            f"{refusal_unique!r}. WHICH SHAPE: {shape_unique}. WHAT EACH "
            f"RENDERER SAID: {report_unique}"
        )
        assert outcome_unique == "saved" and success_unique, (
            "expected the success toast after saving the unique Display Order "
            f"{DISPLAY_ORDER_VALID!r}; the page reported {outcome_unique!r}. "
            f"WHAT EACH RENDERER SAID: {report_unique}"
        )
        assert stored_unique == DISPLAY_ORDER_VALID, (
            f"expected {LAW_1996_NUMBER!r} to store Display Order "
            f"{DISPLAY_ORDER_VALID!r}; it reads {stored_unique!r}"
        )
    finally:
        try:
            if baseline_1996 is not None:
                with allure.step(
                    "TEST_OWNED reset -- restore the 1996 entry's Display Order"
                ):
                    _test_owned_reset(
                        _restore_display_order(
                            admin,
                            LAW_1996_ENTRY_CODE,
                            baseline_1996,
                            baseline_1996_status,
                        ),
                        label="tc_134987 Law 1996 Display Order",
                    )
            if baseline_1990 is not None:
                with allure.step(
                    "TEST_OWNED reset -- restore the 1990 entry's Display Order"
                ):
                    _test_owned_reset(
                        _restore_display_order(
                            admin,
                            LAW_1990_ENTRY_CODE,
                            baseline_1990,
                            baseline_1990_status,
                        ),
                        label="tc_134987 Law 1990 Display Order",
                    )
            if baseline_card_order is not None:
                with allure.step(
                    "TEST_OWNED reset -- prove both cards are back in their "
                    "original public order"
                ):
                    _test_owned_reset(
                        _prove_public_card_order(public, baseline_card_order),
                        label="tc_134987 public Chamber's Law card order",
                    )
        finally:
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001 -- cleanup must never mask the result
                pass


# =========================================================================
# Batch 7 case data -- Active Status + Law Entry ID
# =========================================================================
# THE FIELD IS A CHECKBOX, not a textbox and not a spinbutton
# (`<input type="checkbox" name="ObjectField_activeStatus">`, `required:
# false`, accessible name `Active Status` on an `/en` render and
# `الحالة النشطة` on an `/ar` one -- read live, finding (x)). Nothing in this
# block may go through `fill_text()` / `field_value()` / `fill_number()` /
# `spinbutton_value()`: those are bound to the `textbox` and `spinbutton`
# roles and resolve ZERO controls here. `set_checkbox()` / `is_checked()` on
# `ObjectAuthoringPage` are the correct pair, and `_observed_stored_checkbox()`
# below is the boolean twin of `_observed_stored_value()` /
# `_observed_stored_number()` -- same polling contract, same "return the last
# state observed and let the caller assert" rule.
#
# THESE TWO CASES CHANGE THE LIVE PUBLIC SITE. Un-ticking `Active Status`
# REMOVES the card from the public Chamber's Law page -- that is the
# documented purpose of the field (OBJECT-AUTHORING-GUIDE.md sections 4/8)
# and it is exactly what the sibling module's tc_134887 proves live. Both
# tests therefore capture the ANONYMOUS public card order before mutating
# anything and re-prove it in `finally` through `_prove_public_card_order()`,
# on top of the CMS-side `_restore_active_status()`. Restoring the CMS value
# alone would leave the half a visitor actually notices unchecked.
ACTIVE_STATUS_TRUE = True       # 134976 step 2 / 134977 step 1
ACTIVE_STATUS_FALSE = False     # 134976 step 1 / 134977 step 2

# 134978's two created records. Nothing about them is left to chance:
#   * `Active Status` UN-TICKED, so neither can EVER reach the public page
#     (proved live by the sibling module's tc_134887) -- a QCTEST card can
#     never appear on the real website because of this test;
#   * Display Orders 9100/9200 -- multiples of 100 per
#     OBJECT-AUTHORING-GUIDE.md section 3, and far past the real editorial
#     content, so even an unexpected activation could not reorder anything;
#   * a per-run timestamp in every identifying string, so a rerun cannot
#     collide with the previous run's rows.
#
# [!] "EXTERNAL REFERENCE CODE" -- WHAT A TEST CAN AND CANNOT OWN HERE, and
# it is the same fact the case is about. The Law Entry form renders NO
# identifier control of any kind (finding (y)), so a test CANNOT choose the
# record's Liferay external reference code the way the seeded editorial rows
# carry hand-authored ones (`QCDEMO-129394-law-11-1990`): the product mints
# it. What this test owns instead is the record's own VISIBLE identity -- the
# `QCTEST-129394-134978-A/B-<run>` reference below goes verbatim into the Law
# Number and the Law Title, which is what the entries list renders in its
# Entry column, so a human can find these two rows later by eye. The
# product-assigned identifier is then READ BACK at runtime (from the row's own
# `data-qc-oel-delete` handle and from the `?editEntry=` code its own Edit
# link lands on) -- which is precisely what step 1 means by "note its Law
# Entry ID", and it can only be known after the record exists.
LAW_ENTRY_ID_REFERENCE_PREFIX = "QCTEST-129394-134978"
LAW_ENTRY_ID_DISPLAY_ORDER_A = "9100"
LAW_ENTRY_ID_DISPLAY_ORDER_B = "9200"
# Optional field (Object definition: `required: false`), but the object's own
# "External Link URL format" rule is `isEmpty(...) || match(..., "^https?://.*")`
# -- so a value must be a real URL if one is given at all. This is the
# 1990 record's own live host, which satisfies the rule.
LAW_ENTRY_ID_EXTERNAL_LINK = "https://www.almeezan.qa/"

# The four shapes "the Law Entry ID is not editable" can actually take on
# this form. 134978's expected result explicitly licenses TWO of them --
# "it is read-only or absent from the edit form" -- so the test asserts the
# NEGATIVE (no editable identifier control) and REPORTS which shape it
# observed, instead of demanding one and failing on the other.
LAW_ENTRY_ID_ABSENT = (
    "ABSENT FROM THE EDIT FORM -- the form renders no identifier control at "
    "all, so there is nothing to edit"
)
LAW_ENTRY_ID_READ_ONLY = (
    "READ-ONLY -- an identifier control IS rendered and carries `readonly`"
)
LAW_ENTRY_ID_DISABLED = (
    "DISABLED -- an identifier control IS rendered and carries `disabled`"
)
LAW_ENTRY_ID_EDITABLE = (
    "EDITABLE -- an identifier control IS rendered and is neither read-only "
    "nor disabled; the case's guarantee does NOT hold"
)


def _law_entry_id_form_shape(id_controls) -> str:
    """Names which of the four shapes above an edit form landed in, from the
    `(label, name, readonly, disabled)` tuples `identifier_controls()`
    returns. PURE -- it reads nothing from the live DOM itself."""
    if not id_controls:
        return LAW_ENTRY_ID_ABSENT
    if any(not readonly and not disabled for _, _, readonly, disabled in id_controls):
        return LAW_ENTRY_ID_EDITABLE
    if all(readonly for _, _, readonly, _ in id_controls):
        return LAW_ENTRY_ID_READ_ONLY
    return LAW_ENTRY_ID_DISABLED


def _observed_stored_checkbox(
    admin,
    entry_code,
    field_label,
    expected,
    locale=CMS_LOCALE_EN,
    timeout=PUBLISH_CONFIRM_TIMEOUT,
):
    """Polls a FRESH navigation until the record's CHECKBOX stores
    `expected`, and returns the LAST state observed -- match or no match
    (`None` only when the control was never readable at all, which is itself
    a reportable result rather than an opaque timeout).

    The boolean twin of `_observed_stored_value()` / `_observed_stored_number()`
    (same polling contract, same "nothing is swallowed, the caller asserts on
    the return" rule), differing only in which read it calls: `is_checked()`
    instead of `field_value()` / `spinbutton_value()`. It cannot reuse either
    -- those are bound to the `textbox` and `spinbutton` roles, and
    `Active Status` is an `<input type="checkbox">`, so both lookups resolve
    ZERO controls here and raise on every poll.

    The poll exists because Submit for Publishing takes 27-30s on this
    surface (measured live), so a single read straight after the click would
    be a race, not a check. The locale default is `en` rather than `None`
    for the reason `_observed_stored_number()` documents: this account's own
    Liferay language is `ar_SA`, and an unpinned re-read resolves ZERO
    controls the moment the session drifts."""
    observed = {"value": None}

    def _committed() -> bool:
        observed["value"] = admin.open_law_entry(
            entry_code, locale=locale
        ).is_checked(field_label)
        return observed["value"] == expected

    try:
        wait_until(_committed, timeout=timeout, poll=3.0)
    except Exception:  # noqa: BLE001 -- the last observed state IS the result
        pass
    return observed["value"]


def _establish_active_status(
    admin, entry_code, field_label, value, locale=CMS_LOCALE_EN
):
    """DISCLOSED TEST_OWNED PRECONDITION WRITE -- puts `value` into a
    record's Active Status and returns what the record actually holds
    afterwards, so the caller can ASSERT the precondition instead of
    assuming it.

    134976 opens "with Active Status False"; live, BOTH law entries are
    ticked (finding (x)). Without this, the case's own step 1 could never be
    satisfied for any reason connected to the product, and step 2 ("set
    Active Status to True") would be a no-op write of the value the record
    already holds -- i.e. testing nothing at all. 134977's precondition
    ("with Active Status True") IS true of the live data, so that test
    deliberately does NOT call this, exactly as batch 6's 134975 writes no
    precondition while 134973/134974 do.

    THIS WRITE TAKES A LIVE CARD OFF THE PUBLIC SITE for the duration of the
    test. That is unavoidable -- it is the state the case demands -- and it
    is why the caller captures the anonymous public card order BEFORE calling
    this and re-proves it in `finally`.

    Idempotent (a record already holding `value` is left alone) and never
    silent: the return value is the real, re-read state, so a precondition
    that did not commit fails its test at step 1 rather than at step 3 for
    the wrong reason."""
    authoring = admin.open_law_entry(entry_code, locale=locale)
    if authoring.is_checked(field_label) == value:
        return value
    authoring.set_checkbox(field_label, value)
    authoring.submit_for_publishing()
    return _observed_stored_checkbox(
        admin, entry_code, field_label, value, locale=locale
    )


def _restore_active_status(
    admin, entry_code, baseline_checked, baseline_status, locale=CMS_LOCALE_EN
):
    """TEST_OWNED restore for Active Status, with every read pinned to one
    interface locale.

    Same contract as `_restore_display_order()` -- restore, then PROVE it
    from a fresh navigation, never a post-save-reflowed DOM -- and it cannot
    reuse that helper (or `_restore_law_entry_text()`) for the same reason
    nothing in this batch can: those drive `fill_number()`/`spinbutton_value()`
    and `fill_text()`/`field_value()`, and this control is a checkbox. A
    TEST_OWNED restore that cannot find its own field is exactly the failure
    this module exists to prevent.

    This restore is the one that puts a real card BACK on the live public
    page, so its caller pairs it with `_prove_public_card_order()`: a
    committed CMS value is necessary but not sufficient evidence that a
    visitor sees the section as it was found."""
    label = admin.ACTIVE_STATUS_LABEL

    def _restore():
        authoring = admin.open_law_entry(entry_code, locale=locale)
        if authoring.is_checked(label) != baseline_checked:
            if authoring.current_status() == "Approved":
                authoring.set_checkbox(label, baseline_checked)
                _publish_and_confirm(authoring)
            else:
                _unpublish_and_confirm(authoring)
                authoring.set_checkbox(label, baseline_checked)
                if baseline_status == "Approved":
                    _publish_and_confirm(authoring)
                else:
                    authoring.save_as_draft()

        # PROVE it -- fresh navigation, never a post-save-reflowed DOM.
        authoring = admin.open_law_entry(entry_code, locale=locale)
        actual_checked = authoring.is_checked(label)
        actual_status = authoring.current_status()
        if actual_checked != baseline_checked:
            raise AssertionError(
                "TEST_OWNED restore did not commit: Active Status on "
                f"{entry_code} reads {actual_checked!r}, expected the captured "
                f"baseline {baseline_checked!r}"
            )
        if actual_status != baseline_status:
            raise AssertionError(
                f"TEST_OWNED restore did not commit: {entry_code} status is "
                f"{actual_status!r}, expected the captured baseline "
                f"{baseline_status!r}"
            )

    return _restore


def _wait_for_listed_entry(
    admin, title, locale=CMS_LOCALE_EN, timeout=PUBLISH_CONFIRM_TIMEOUT
) -> bool:
    """Polls a FRESH entries list until a row carrying `title` renders, and
    returns whether it ever did -- match or no match, never an exception.

    Needed by 134978 for the same measured reason every other read-back in
    this module polls: Submit for Publishing takes 27-30s here, so reading
    the list once immediately after creating a record is a race. Returning a
    bool rather than raising keeps the caller's assertion -- and therefore
    the failure report -- about the PRODUCT ("the record was never listed")
    instead of about a timeout."""
    observed = {"listed": False}

    def _listed() -> bool:
        observed["listed"] = admin.open_law_entries_list(
            locale=locale
        ).row_visible(title)
        return observed["listed"]

    try:
        wait_until(_listed, timeout=timeout, poll=3.0)
    except Exception:  # noqa: BLE001 -- the last observation IS the result
        pass
    return observed["listed"]


# =========================================================================
# Batch 7 -- Active Status + Law Entry ID (134976-134978)
# =========================================================================


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Active Status stores the value True")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134976
@pytest.mark.traceability("134976")
@allure.label("pbi", "129394")
@allure.label("testcase", "134976")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134976_active_status_stores_the_value_true(browser, page):
    # "Click Save" can only mean **Submit for Publishing** -- there is no
    # button called Save on this form, and `Save as Draft` sets
    # `formnovalidate` and strips `required` off every control, so it
    # validates nothing (module docstring, point 1).
    #
    # PRECONDITION IS ESTABLISHED, NOT ASSUMED. The case opens "with Active
    # Status False"; live, BOTH law entries are ticked (finding (x)).
    # `_establish_active_status()` writes False first as a disclosed
    # TEST_OWNED setup step and the test ASSERTS it landed -- otherwise step
    # 2 would tick a box that is already ticked and step 3's "Active Status
    # reads True" would be true for a reason that has nothing to do with the
    # product.
    #
    # THIS TEST CHANGES THE LIVE PUBLIC SITE. The precondition write above
    # takes the 1990 card OFF the public Chamber's Law page for the duration
    # of the test (un-ticking `activeStatus` is the documented way to do
    # exactly that -- OBJECT-AUTHORING-GUIDE.md sections 4/8, proved live by
    # the sibling module's tc_134887). The baseline is captured at runtime
    # and restored in `finally`, the restore is PROVED from a fresh
    # navigation, and the ANONYMOUS public page is then re-read until both
    # cards are back in the order captured before anything was mutated.
    # Nothing is ever deleted (standing project rule).
    admin = ChambersLawAdminPage(page)
    label = admin.ACTIVE_STATUS_LABEL
    baseline_checked = None
    baseline_status = None
    baseline_card_order = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    public = ChambersLawPage(anon_page)

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS "
            "with Active Status False"
        ):
            # Captured BEFORE anything is mutated -- this is what the
            # `finally` restore is proved against. Read as a genuinely
            # ANONYMOUS visitor, per this project's logged-out-visibility
            # rule; an authenticated read would prove only that a signed-in
            # editor sees the right cards.
            public.open_chambers_law()
            baseline_card_order = public.card_numbers()

            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            baseline_checked = authoring.is_checked(label)
            baseline_status = authoring.current_status()
            opened_with = _establish_active_status(
                admin, LAW_1990_ENTRY_CODE, label, ACTIVE_STATUS_FALSE
            )

        with allure.step("Set Active Status to True and click Submit for Publishing"):
            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            authoring.set_checkbox(label, ACTIVE_STATUS_TRUE)
            ticked_to = authoring.is_checked(label)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()
            renderer_report = form.save_message_report()

        with allure.step("Reload the law entry record"):
            stored = _observed_stored_checkbox(
                admin, LAW_1990_ENTRY_CODE, label, ACTIVE_STATUS_TRUE
            )
            shape = _outcome_shape(
                refusal, success, str(ACTIVE_STATUS_TRUE), str(stored)
            )
            allure.attach(
                f"{shape}\n{renderer_report}",
                name="tc_134976 -- outcome and renderers",
            )

        # Assert -- step 1
        assert opened_with == ACTIVE_STATUS_FALSE, (
            "precondition: expected the law entry record to open with Active "
            f"Status {ACTIVE_STATUS_FALSE!r}; it holds {opened_with!r} (its "
            f"captured baseline was {baseline_checked!r})"
        )

        # Assert -- step 2
        assert ticked_to == ACTIVE_STATUS_TRUE, (
            f"the Active Status box reads {ticked_to!r} rather than "
            f"{ACTIVE_STATUS_TRUE!r} before the save -- the control itself did "
            "not take the change"
        )
        assert not refusal, (
            f"setting Active Status to {ACTIVE_STATUS_TRUE!r} was rejected: "
            f"{refusal!r}. WHICH SHAPE: {shape}. WHAT EACH RENDERER SAID: "
            f"{renderer_report}"
        )
        assert outcome == "saved" and success, (
            "expected the success toast after saving Active Status "
            f"{ACTIVE_STATUS_TRUE!r}; the page reported {outcome!r}. WHAT EACH "
            f"RENDERER SAID: {renderer_report}"
        )

        # Assert -- step 3
        assert stored == ACTIVE_STATUS_TRUE, (
            f"expected Active Status to read {ACTIVE_STATUS_TRUE!r} after the "
            f"reload; it reads {stored!r}"
        )
    finally:
        try:
            if baseline_checked is not None:
                with allure.step("TEST_OWNED reset -- restore Active Status"):
                    _test_owned_reset(
                        _restore_active_status(
                            admin,
                            LAW_1990_ENTRY_CODE,
                            baseline_checked,
                            baseline_status,
                        ),
                        label="tc_134976 Law 1990 Active Status",
                    )
            if baseline_card_order is not None:
                with allure.step(
                    "TEST_OWNED reset -- prove both cards are back on the public "
                    "page in their original order"
                ):
                    _test_owned_reset(
                        _prove_public_card_order(public, baseline_card_order),
                        label="tc_134976 public Chamber's Law card order",
                    )
        finally:
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001 -- cleanup must never mask the result
                pass


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Active Status stores the value False")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134977
@pytest.mark.traceability("134977")
@allure.label("pbi", "129394")
@allure.label("testcase", "134977")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134977_active_status_stores_the_value_false(browser, page):
    # NO PRECONDITION WRITE HERE, unlike 134976: this case asks for a record
    # that opens "with Active Status True", which the live record already
    # satisfies (finding (x): both law entries are ticked). The runtime
    # baseline is therefore ASSERTED rather than established, and nothing is
    # written before the step under test -- exactly the split batch 6 already
    # draws between 134973/134974 (live value contradicts the case, so it is
    # established) and 134975 (live value satisfies it, so it is not).
    #
    # THIS TEST TAKES A REAL CARD OFF THE LIVE PUBLIC SITE -- that IS the
    # step under test. Un-ticking `activeStatus` is the documented way to
    # remove an entry from the website while keeping it
    # (OBJECT-AUTHORING-GUIDE.md sections 4/8), and the sibling module's
    # tc_134887 proves live that the card really does disappear. So the
    # restore has two halves and BOTH are proved: the CMS value is put back
    # and re-read from a fresh navigation, and then the ANONYMOUS public page
    # is re-read until BOTH cards are back in the order captured before
    # anything was mutated. Nothing is ever deleted (standing project rule).
    admin = ChambersLawAdminPage(page)
    label = admin.ACTIVE_STATUS_LABEL
    baseline_checked = None
    baseline_status = None
    baseline_card_order = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    public = ChambersLawPage(anon_page)

    try:
        with allure.step(
            "Open a law entry record under the Chamber's Law page in Liferay CMS "
            "with Active Status True"
        ):
            public.open_chambers_law()
            baseline_card_order = public.card_numbers()

            authoring = admin.open_law_entry(LAW_1990_ENTRY_CODE, locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            baseline_checked = authoring.is_checked(label)
            baseline_status = authoring.current_status()
            opened_with = baseline_checked

        with allure.step("Set Active Status to False and click Submit for Publishing"):
            authoring.set_checkbox(label, ACTIVE_STATUS_FALSE)
            unticked_to = authoring.is_checked(label)
            outcome = form.submit_expecting_refusal()
            refusal = form.save_refusal_text()
            success = form.success_message_text()
            renderer_report = form.save_message_report()

        with allure.step("Reload the law entry record"):
            stored = _observed_stored_checkbox(
                admin, LAW_1990_ENTRY_CODE, label, ACTIVE_STATUS_FALSE
            )
            shape = _outcome_shape(
                refusal, success, str(ACTIVE_STATUS_FALSE), str(stored)
            )
            allure.attach(
                f"{shape}\n{renderer_report}",
                name="tc_134977 -- outcome and renderers",
            )

        # Assert -- step 1
        assert opened_with == ACTIVE_STATUS_TRUE, (
            "precondition: expected the law entry record to open with Active "
            f"Status {ACTIVE_STATUS_TRUE!r}; it opened {opened_with!r}"
        )

        # Assert -- step 2
        assert unticked_to == ACTIVE_STATUS_FALSE, (
            f"the Active Status box reads {unticked_to!r} rather than "
            f"{ACTIVE_STATUS_FALSE!r} before the save -- the control itself did "
            "not take the change"
        )
        assert not refusal, (
            f"setting Active Status to {ACTIVE_STATUS_FALSE!r} was rejected: "
            f"{refusal!r}. WHICH SHAPE: {shape}. WHAT EACH RENDERER SAID: "
            f"{renderer_report}"
        )
        assert outcome == "saved" and success, (
            "expected the success toast after saving Active Status "
            f"{ACTIVE_STATUS_FALSE!r}; the page reported {outcome!r}. WHAT EACH "
            f"RENDERER SAID: {renderer_report}"
        )

        # Assert -- step 3
        assert stored == ACTIVE_STATUS_FALSE, (
            f"expected Active Status to read {ACTIVE_STATUS_FALSE!r} after the "
            f"reload; it reads {stored!r}"
        )
    finally:
        try:
            if baseline_checked is not None:
                with allure.step("TEST_OWNED reset -- restore Active Status"):
                    _test_owned_reset(
                        _restore_active_status(
                            admin,
                            LAW_1990_ENTRY_CODE,
                            baseline_checked,
                            baseline_status,
                        ),
                        label="tc_134977 Law 1990 Active Status",
                    )
            if baseline_card_order is not None:
                with allure.step(
                    "TEST_OWNED reset -- prove both cards are back on the public "
                    "page in their original order"
                ):
                    _test_owned_reset(
                        _prove_public_card_order(public, baseline_card_order),
                        label="tc_134977 public Chamber's Law card order",
                    )
        finally:
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001 -- cleanup must never mask the result
                pass


@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("CMS authoring / admin")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that Law Entry ID is auto-generated, unique, and not editable")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134978
@pytest.mark.traceability("134978")
@allure.label("pbi", "129394")
@allure.label("testcase", "134978")
@CHAMBERS_LAW_XDIST_GROUP
def test_chambers_law_cp_134978_law_entry_id_is_auto_generated_unique_and_not_editable(
    browser, page, law_icon_fixtures
):
    # THE ONE CASE IN THIS MODULE THAT DELIBERATELY CREATES RECORDS -- TWO of
    # them, because "the two identifiers do not collide" cannot be checked
    # with one. Per the standing project rule they are NEVER DELETED: no
    # teardown-by-delete is attempted, and each run therefore leaves two more
    # QCTEST rows in the Law Entry list, exactly as the sibling module's
    # tc_134884 does. Both are created with `Active Status` UN-TICKED and
    # Display Orders 9100/9200, so neither can ever reach the public page
    # (proved live by tc_134887) and neither can reorder real content. Their
    # identifying strings carry a per-run timestamp so a rerun cannot collide
    # with the previous run's rows, and both identities are logged and
    # attached to Allure so a human can find them later.
    #
    # WHERE THE "LAW ENTRY ID" ACTUALLY LIVES. Read live, finding (y): the
    # Law Entry form renders NO identifier control at all -- its complete
    # non-hidden control set is Law Number (+AR), Law Title (+AR), Law
    # Description (+AR), External Link URL, Law Icon, Display Order, Active
    # Status, and a scan of every label/legend/th/.form-group for "ID" or
    # "Identifier" returns ZERO matches. The record's identity is rendered
    # OUTSIDE the form instead, in two independent places on the entries
    # list: the row's own `data-qc-oel-delete` handle
    # (`ObjectAuthoringPage.row_entry_id()`) and the `?editEntry=<code>`
    # external reference code its own Edit link lands on
    # (`ObjectAuthoringPage.entry_code`). BOTH are captured and BOTH are
    # checked for uniqueness, because "the Law Entry ID" is not a field this
    # product exposes by that name and naming only one of them would be a
    # guess.
    #
    # THE CREATE PATH IS READ WITH ITS OWN READER (2026-09-16). This is
    # the module's ONLY create flow, and `submit_expecting_refusal()` --
    # correct for the other 39 tests, every one of which EDITS an existing
    # record -- cannot see a create succeed. The full mechanism is documented
    # on `_LawEntryForm.submit_new_entry_outcome()`; the short version, read
    # off the page's own shipped JS and confirmed live against the create
    # form: an EDIT is a `PUT` whose 200 calls `rememberSaved()`, which parks
    # "Saved and submitted for publishing." in `sessionStorage` for the
    # landing to replay as a bar -- and the CREATE branch never calls
    # `rememberSaved()` at all. It posts natively into a hidden iframe,
    # compares the Object's entry count before and after, and on a growth
    # navigates back to `backURL` with a BLANK form. So the create path's
    # success signal is that blank form, which is what this reader samples,
    # and the product renders NO save-confirmation message for a create.
    # The step-1/step-2 `success_?` half of the assert is therefore left to
    # FAIL deliberately rather than loosened: whether "a create emits no
    # confirmation at all" is acceptable product behaviour is a triage
    # decision, not something a reader should paper over. The raw,
    # unfiltered bar read (`create_message_report()`) is attached so that
    # triage has the landing's own words in front of it.
    #
    # STEP 3 IS ASSERTED POSITIVELY, NOT AS A TIMEOUT. The case's expected
    # result explicitly licenses two different answers -- "it is read-only
    # OR absent from the edit form" -- so the test reads
    # `identifier_controls()`, which returns the identifier controls the form
    # renders (empty when it renders none), and asserts that NONE of them is
    # editable. An empty tuple is positive evidence of absence; a
    # `get_by_role(...)` hunt for a control that does not exist could only
    # ever produce a timeout and no information at all. The observed shape is
    # named in the report either way.
    #
    # The Law Icon is a REQUIRED field on the create form -- the sibling case
    # 134943 proves live that a save without one is blocked -- so the
    # deterministic 40 KB SVG fixture is uploaded on both records. Liferay
    # de-duplicates a same-named upload into `law-icon (N).svg`; nothing here
    # reads the file name back, so that is harmless.
    import time as _time

    admin = ChambersLawAdminPage(page)
    icon_path = law_icon_fixtures[ICON_SVG_NAME]
    run_id = _time.strftime("%m%d-%H%M%S")
    reference_a = f"{LAW_ENTRY_ID_REFERENCE_PREFIX}-A-{run_id}"
    reference_b = f"{LAW_ENTRY_ID_REFERENCE_PREFIX}-B-{run_id}"
    title_a = f"{reference_a} auto-generated Law Entry ID check"
    title_b = f"{reference_b} auto-generated Law Entry ID check"
    number_a = f"{reference_a} Law No. A of 2026"
    number_b = f"{reference_b} Law No. B of 2026"
    desc_a = f"QCTEST-129394 created by automated test tc_134978 run {run_id} (A)."
    desc_b = f"QCTEST-129394 created by automated test tc_134978 run {run_id} (B)."
    baseline_card_order = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    public = ChambersLawPage(anon_page)

    try:
        with allure.step(
            "Create a new law entry under the Chamber's Law page with all "
            "mandatory fields completed and note its Law Entry ID"
        ):
            public.open_chambers_law()
            baseline_card_order = public.card_numbers()

            authoring = admin.open_new_law_entry_form(locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            authoring.fill_text(admin.LAW_NUMBER_LABEL, number_a)
            authoring.fill_text(_arabic_label(admin, admin.LAW_NUMBER_LABEL), number_a)
            authoring.fill_text(admin.LAW_TITLE_LABEL, title_a)
            authoring.fill_text(_arabic_label(admin, admin.LAW_TITLE_LABEL), title_a)
            authoring.fill_text(admin.LAW_DESCRIPTION_LABEL, desc_a)
            authoring.fill_text(
                _arabic_label(admin, admin.LAW_DESCRIPTION_LABEL), desc_a
            )
            authoring.fill_text(
                admin.EXTERNAL_LINK_URL_LABEL, LAW_ENTRY_ID_EXTERNAL_LINK
            )
            authoring.upload_file(admin.LAW_ICON_UPLOAD_LABEL, icon_path)
            authoring.fill_number(
                admin.DISPLAY_ORDER_LABEL, LAW_ENTRY_ID_DISPLAY_ORDER_A
            )
            # SAFETY: un-ticked, so this record can never reach the public
            # Chamber's Law page no matter what else happens in this test.
            authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, ACTIVE_STATUS_FALSE)
            # CREATE-path reader, not the edit-path one -- see
            # `_LawEntryForm.submit_new_entry_outcome()`. Law Title is the
            # sentinel because it was just filled with a value unique to this
            # run, so "the form no longer holds it" cannot be anything but a
            # freshly re-rendered blank form.
            outcome_a = form.submit_new_entry_outcome(admin.LAW_TITLE_LABEL, title_a)
            refusal_a = form.save_refusal_text()
            success_a = form.success_message_text()
            report_a = form.create_message_report()

            listed_a = _wait_for_listed_entry(admin, title_a)
            entries = admin.open_law_entries_list(locale=CMS_LOCALE_EN)
            row_id_a = entries.row_entry_id(title_a) if listed_a else ""
            edit_code_a = (
                entries.open_entry_by_edit_link(title_a).entry_code if listed_a else ""
            )
            allure.attach(
                f"reference={reference_a!r}\ntitle={title_a!r}\n"
                f"row data-qc-oel-delete id={row_id_a!r}\n"
                f"editEntry external reference code={edit_code_a!r}\n"
                f"outcome={outcome_a!r}\n{report_a}",
                name="tc_134978 record A -- created identity (NEVER DELETED)",
            )
            logger.warning(
                "tc_134978 created law entry A and is LEAVING IT IN PLACE per the "
                "never-delete rule: title=%r row_id=%r editEntry=%r",
                title_a,
                row_id_a,
                edit_code_a,
            )

        with allure.step("Create a second law entry and note its Law Entry ID"):
            authoring = admin.open_new_law_entry_form(locale=CMS_LOCALE_EN)
            form = _LawEntryForm(authoring)
            authoring.fill_text(admin.LAW_NUMBER_LABEL, number_b)
            authoring.fill_text(_arabic_label(admin, admin.LAW_NUMBER_LABEL), number_b)
            authoring.fill_text(admin.LAW_TITLE_LABEL, title_b)
            authoring.fill_text(_arabic_label(admin, admin.LAW_TITLE_LABEL), title_b)
            authoring.fill_text(admin.LAW_DESCRIPTION_LABEL, desc_b)
            authoring.fill_text(
                _arabic_label(admin, admin.LAW_DESCRIPTION_LABEL), desc_b
            )
            authoring.fill_text(
                admin.EXTERNAL_LINK_URL_LABEL, LAW_ENTRY_ID_EXTERNAL_LINK
            )
            authoring.upload_file(admin.LAW_ICON_UPLOAD_LABEL, icon_path)
            authoring.fill_number(
                admin.DISPLAY_ORDER_LABEL, LAW_ENTRY_ID_DISPLAY_ORDER_B
            )
            authoring.set_checkbox(admin.ACTIVE_STATUS_LABEL, ACTIVE_STATUS_FALSE)
            outcome_b = form.submit_new_entry_outcome(admin.LAW_TITLE_LABEL, title_b)
            refusal_b = form.save_refusal_text()
            success_b = form.success_message_text()
            report_b = form.create_message_report()

            listed_b = _wait_for_listed_entry(admin, title_b)
            entries = admin.open_law_entries_list(locale=CMS_LOCALE_EN)
            row_id_b = entries.row_entry_id(title_b) if listed_b else ""
            edit_code_b = (
                entries.open_entry_by_edit_link(title_b).entry_code if listed_b else ""
            )
            allure.attach(
                f"reference={reference_b!r}\ntitle={title_b!r}\n"
                f"row data-qc-oel-delete id={row_id_b!r}\n"
                f"editEntry external reference code={edit_code_b!r}\n"
                f"outcome={outcome_b!r}\n{report_b}",
                name="tc_134978 record B -- created identity (NEVER DELETED)",
            )
            logger.warning(
                "tc_134978 created law entry B and is LEAVING IT IN PLACE per the "
                "never-delete rule: title=%r row_id=%r editEntry=%r",
                title_b,
                row_id_b,
                edit_code_b,
            )

        with allure.step("Attempt to edit the Law Entry ID on either record"):
            # Record B's own edit form is already open from the read above;
            # re-opened here anyway so this step reads a freshly rendered
            # form rather than one another step happened to leave behind.
            entries = admin.open_law_entries_list(locale=CMS_LOCALE_EN)
            authoring = entries.open_entry_by_edit_link(title_a)
            form = _LawEntryForm(authoring)
            id_controls_a = form.identifier_controls()
            all_controls_a = form.visible_control_labels()
            shape_a = _law_entry_id_form_shape(id_controls_a)

            entries = admin.open_law_entries_list(locale=CMS_LOCALE_EN)
            authoring = entries.open_entry_by_edit_link(title_b)
            form = _LawEntryForm(authoring)
            id_controls_b = form.identifier_controls()
            shape_b = _law_entry_id_form_shape(id_controls_b)

            allure.attach(
                f"record A: {shape_a}\nidentifier controls={id_controls_a!r}\n"
                f"record B: {shape_b}\nidentifier controls={id_controls_b!r}\n"
                f"every control the edit form renders={all_controls_a!r}",
                name="tc_134978 -- is the Law Entry ID editable?",
            )

        # Assert -- step 1
        assert not refusal_a, (
            f"the first law entry was rejected on save: {refusal_a!r}. WHAT EACH "
            f"RENDERER SAID: {report_a}"
        )
        # The `and success_a` half was REMOVED on 2026-09-16 because it was
        # STRICTER THAN THE CASE. Step 1's expected result reads "The first law
        # entry is saved and its Law Entry ID is populated automatically" -- it
        # says nothing about a confirmation message, and the two asserts below
        # already prove the record was written (it is listed, and it carries a
        # product-minted id). What the create path renders is asserted nowhere
        # here because it is NOT this case's subject; it is reported instead,
        # and is tracked as its own finding: verified live in the page's own
        # JS, `rememberSaved()` has exactly ONE call site and it sits inside
        # the `send('PUT', restPath + '/' + entry.id)` EDIT branch, so a CREATE
        # emits no confirmation of any kind. Asserting a message here would
        # have failed this case for a defect it does not test.
        assert outcome_a == "saved", (
            "expected the first law entry to be SAVED; the page reported "
            f"{outcome_a!r}. WHAT EACH RENDERER SAID: {report_a}"
        )
        assert listed_a, (
            f"expected the first law entry {title_a!r} to appear in the Law Entry "
            "list after being saved; it never did"
        )
        assert row_id_a and edit_code_a, (
            "expected the first law entry's Law Entry ID to be populated "
            "AUTOMATICALLY -- this form has no identifier field, so the product "
            "mints it. Its row handle reads {0!r} and its own editEntry external "
            "reference code reads {1!r}".format(row_id_a, edit_code_a)
        )

        # Assert -- step 2
        assert not refusal_b, (
            f"the second law entry was rejected on save: {refusal_b!r}. WHAT EACH "
            f"RENDERER SAID: {report_b}"
        )
        # See the step-1 note above -- `and success_b` removed for the same
        # reason: the case asks whether the entry was SAVED, not whether the
        # product announced it.
        assert outcome_b == "saved", (
            "expected the second law entry to be SAVED; the page reported "
            f"{outcome_b!r}. WHAT EACH RENDERER SAID: {report_b}"
        )
        assert listed_b, (
            f"expected the second law entry {title_b!r} to appear in the Law Entry "
            "list after being saved; it never did"
        )
        assert row_id_b and edit_code_b, (
            "expected the second law entry's Law Entry ID to be populated "
            "automatically; its row handle reads {0!r} and its own editEntry "
            "external reference code reads {1!r}".format(row_id_b, edit_code_b)
        )
        assert row_id_a != row_id_b, (
            "expected the two law entries to receive DIFFERENT Law Entry IDs; both "
            f"rows carry the same handle {row_id_a!r} -- the two identifiers "
            "COLLIDE"
        )
        assert edit_code_a != edit_code_b, (
            "expected the two law entries to receive DIFFERENT external reference "
            f"codes; both read {edit_code_a!r} -- the two identifiers COLLIDE"
        )

        # Assert -- step 3
        assert shape_a != LAW_ENTRY_ID_EDITABLE, (
            "expected the Law Entry ID to be NOT EDITABLE on the first record -- "
            "read-only or absent from the edit form, per the case's own expected "
            f"result. WHAT WAS OBSERVED: {shape_a}; identifier controls "
            f"{id_controls_a!r}; every control the form renders {all_controls_a!r}"
        )
        assert shape_b != LAW_ENTRY_ID_EDITABLE, (
            "expected the Law Entry ID to be NOT EDITABLE on the second record "
            f"either. WHAT WAS OBSERVED: {shape_b}; identifier controls "
            f"{id_controls_b!r}"
        )
    finally:
        try:
            # NO TEARDOWN-BY-DELETE -- standing project rule. The two records
            # created above are LEFT IN PLACE, inactive, and reported. The
            # only thing restored here is the public page, which this test
            # should never have changed: proving that is how a surprise
            # (an unexpectedly active QCTEST card) becomes a loud failure
            # instead of a silent one.
            if baseline_card_order is not None:
                with allure.step(
                    "TEST_OWNED check -- the public page still shows exactly the "
                    "two original cards, in their original order"
                ):
                    _test_owned_reset(
                        _prove_public_card_order(public, baseline_card_order),
                        label="tc_134978 public Chamber's Law card order",
                    )
        finally:
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001 -- cleanup must never mask the result
                pass
