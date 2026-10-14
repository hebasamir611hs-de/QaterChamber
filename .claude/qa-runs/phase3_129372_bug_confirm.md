# Bug confirmation — PBI 129372 (Home Latest News) — 2026-10-07 — independent reviewer (offline)

Sources: report + earlier review, `reports/manual-repro-129372-*.png` (opened), Allure attachments of the four G1 runs, PBI 129372 (one read), `cms/Content-Admin-Guide.docx`, `bug-rules.md`, `standards.md` Priority Rubric.

## Verdicts
| Finding | Verdict | Why |
|---|---|---|
| G1 — 135287/135291/135295/135299 | **BACK — one bug** | PBI field table: Section Heading (EN) / (AR) = `Text, Mandatory: Yes`; Section Description (EN) / (AR) = `Rich Text, Mandatory: Yes`. Manual repro meets Rule 3: `G1-1` form as Editor (hint "As an Editor, what you publish here goes live straight away", Publish button), Heading EN + Description EN empty, AR filled, Active unticked; `G1-2` banner **"Saved and published."**, new row `07d29b47…` INACTIVE; `G1-3` reopened record, Field view "Section Heading (empty) / Section Description (empty)", form shows EN `""` and `0 / 1000`. 2026-10-03 rule: PBI-mandatory but form-optional IS a bug. Control: 135314 proves the refusal detector works on the sibling form. |
| G1 evidence scope | note | **Only EN was emptied in the manual repro**: it covers **135287 and 135295**. 135291/135299 rest on run evidence only: assertion "Publish with Section Heading — العربية empty was ACCEPTED", refusal text `(none)`, and the record persisted (`cc8f3259…` rerun 18:25, `8515d20f…` run-1 18:17, both found by tag and moved to the Recycle Bin). Their Allure screenshots show the teardown toast, not the acceptance. Same path, same detector, so list them under "Also reproduces in" with that caveat; a 2-minute AR manual confirm is optional, not blocking. |
| G2 — 135294 (+135298) | **NEEDS USER** | PBI: `Section Description (EN) — Rich Text — Yes — Body text — English` (same for AR). Live: plain `<textarea>` with `11 / 1000` counter, no toolbar (`manual-repro-129372-135294.png`). The guide does **not** define this field: §11 lists only `NewsArticle (title, thumbnailImage, publicationDate, activeStatus, viewCount)`; no "Home Latest News Section" object and no "Section Description" anywhere. So it is NOT a documented requirements-vs-guide conflict — it is a PBI-vs-build gap with no ruling. The PBI note says this field table "is generic throughout the Home page", so the user's call applies to every Home section Description, not just this one. Not-Bugs item 4 needs the user's judgement first. If filed: separate bug from G1 (field type, different fix), P3. |
| 135272 step 5 / 135276 — View All | **destination: PASS. content: SILENT** | PBI: "Visitor clicks View All CTA — browser redirects to the full News listing page" and "The system shall display a view all CTA button; clicking it shall redirect the visitor to the news listing page." `/news-archive` ("News & Press Releases12", search + categories + sort + news cards, Archive Page record PUBLISHED, Active ticked) is a news listing page → redirect clause met. The PBI says nothing about which articles the listing shows; "showing all published articles" is TC 135276's wording, not PBI text. The 3 Home articles missing from the listing is a data-source question for the News listing PBI's owner, not a 129372 bug. Not SILENT-blocking: 135272 steps 1-4 passed, so both can be set Passed once the user accepts the SILENT reading. |

Rule 2: **G1 = 1 bug** (one form, one absent required-field validation, one fix clears all four). **G2 = a separate bug** if the user wants it (different root cause: field component type).

## Draft bug — G1 (BACKed)
- **Title:** `[129372] Home Latest News Section — Publish accepted with mandatory Section Heading / Section Description left empty (EN and AR)`
- **Severity:** **P2 — High** (Priority Rubric: "missing mandatory field enforcement").
- **Representative TC:** 135287 (Section Heading EN rejects empty). **Also reproduces in:** 135295 (Section Description EN, manual-confirmed); 135291 (Section Heading AR) and 135299 (Section Description AR) — run evidence (2026-10-07 18:25 / 18:17), same path; likely also P3 135288/292/296/300 (whitespace-only) once run.
- **Env / account:** qcdev.ihorizons.com, Site Content Editor (`cms_role_credentials`), Object Authoring → Home Latest News Section.
- **Steps:**
  1. Sign in as Site Content Editor; open Object Authoring → Home Latest News Section → **+ Add New**.
  2. Fill Section Heading — العربية and Section Description — العربية; leave **Section Heading** (EN) and **Section Description** (EN) empty; leave Active Status unticked.
  3. Click **Publish**.
  4. Open the new row from the entries list.
- **Expected (PBI 129372 field table):** Section Heading (EN/AR) and Section Description (EN/AR) are `Mandatory: Yes` → validation error, save blocked (TC: "Validation error 'Section Heading (EN) is required' shown; save blocked").
- **Actual:** banner "Saved and published."; a new row is created (status INACTIVE because Active was unticked); reopening it shows Section Heading `(empty)` and Section Description `(empty)`, `0 / 1000`. Same for the AR fields in the automated run (record persisted, no refusal text).
- **Evidence:** `reports/manual-repro-129372-G1-1-before-publish.png`, `…-G1-2-after-publish.png`, `…-G1-3-reopened-record.png`; run: `reports/allure-results-phase3-129372-20261007-1755/225bdad8…png` (135287), `…/07fa1fc4…png` (135295), `…/a7c68548…png` (135299), `…-rerun/0e5477cd…png` (135291).
- **Note for the bug:** the repro record was torn down (`07d29b47…` deleted); the live MAIN record was not touched.

## Draft bug — G2 (only if the user says it is a bug)
- **Title:** `[129372] Home Latest News Section — Section Description (EN/AR) is a plain text area, PBI specifies Rich Text`
- **Severity:** P3 — Medium (editor capability gap; not visitor-visible unless formatting is needed). Representative TC 135294; Also reproduces in: 135298 (AR, same textarea; its automated pass never checked the Bold control).
- **Steps:** Editor → Object Authoring → Home Latest News Section → + Add New → look at Section Description (EN) and (AR). **Expected (PBI):** `Section Description (EN) — Rich Text`. **Actual:** `<textarea>` with a character counter, no formatting toolbar; bold cannot be applied. **Evidence:** `reports/manual-repro-129372-135294.png`.
- Before filing, decide the same for every Home section Description (PBI note: table is generic across the Home page).
