# Ready-Bug Retest — 141918 / 142249 / 143511

**Date:** 2026-09-28 · **Environment:** qcdev.ihorizons.com (QA) · **Account:** TEST_USER (locale forced en_US)
**Method:** developer's own retest steps from each bug's comment, walked live via the framework's
Playwright layer; REST API used as the independent confirmation for 142249.
All three bugs are in state **Ready**.

---

## Verdict summary

| Bug | Sev | Retest | Verdict | Proposed |
|---|---|---|---|---|
| 141918 — Empty Pinned Event submits + no Unpublish | 2 - High | **PASS** (both halves) | Fixed on QA | → **Done** |
| 142249 — Social Icon Image over 2 MB accepted | 3 - Medium | **PASS** (server-side, API-confirmed) | Fixed on QA | → **Done** |
| 143511 — Empty "معلومات" Info box | 4 - Low | **PASS** on the dev's described element | Element identity needs user confirmation | **hold** |

State vocabulary confirmed live from this project's own bugs, not assumed:
`Done · Not a Bug · Ready · Reopen`. There is no "Ready for UAT" / "Ready for Live" state
here — every other verified-fixed bug under PBIs 129373/129382 went `Ready → Done`
(142250, 142266, 142275, 142280). The reopen state is `Reopen`.

---

## 141918 — PASS (both halves)

Linked TC **135669** is a *different* scenario (pin propagation to the Home Page) and is
`@pytest.mark.skip` for an unrelated confirmed defect — **no scripted test proves this bug**.
Retested manually per the developer's 2026-09-27 comment.

- `Pinned Event` now renders **required** (red `*`).
- Empty form + **Save as Draft** → red message: *"Fill in at least one field before saving -
  an empty record cannot be saved as a draft or submitted."* Nothing saved.
- Empty form + **Submit for Review** → same message, nothing saved.
- Entry count unchanged: **2 rows before, 2 rows after** (matches the dev's own measurement).
- **Unpublish present on the row**: `QCDEMO-129382-PIN-001` (PUBLISHED) offers
  `Edit · Preview · Control panel · Unpublish · History · Delete`; the DRAFT row offers the
  same list **without** Unpublish. Exactly the claimed behaviour.
- The positive "fill Pinned Event and save a draft" step was **deliberately not run** — it
  creates a record on shared qcdev content and was out of scope for a negative retest.

Evidence: `scratchpad/retest_shots/141918_*.png`, `retest_log.json`.

## 142249 — PASS (server-side), with a separate UI blocker found

Linked TC **131180** (`test_oversized_icon_image_rejected`) **did run** and came back `broken`,
**not** as product evidence: `TimeoutError` clicking `button:has-text("Submit for Publishing")`.
That button no longer exists — the CMS renamed it to **"Submit for Review"**. Automation debt,
not a product failure (see *Automation drift* below).

Live retest per the developer's 2026-09-27 comment:

- Form helper text now reads **"Upload a .jpg,.jpeg,.png,.svg,.gif,.webp no larger than 2 MB."**
  (was 10 MB) — the configured cap changed as claimed.
- A **2.92 MB** PNG (matching the reporter's ~3 MB repro) uploaded through **Select File →
  Documents and Media** — the exact path that defeated fix #1 — and linked as document `235932`.
- Independent server-side confirmation, the same route the developer measured:

  ```
  POST /o/c/socialmediaicons/scopes/37246   {"image": {"id": 235932}}
  → 400 BAD_REQUEST
    "File exceeds the maximum permitted size of 2 MB for object field Image."
  ```
  No record created. The message names the size rule, the limit and the field, so the refusal
  is attributable to the size check and nothing else.

**Separate issue observed — NOT this bug, NOT filed, needs a human click-through.** Through the
*authoring form*, with the image attached and every required field filled, **Submit for Review
fails with `No value was provided for required object field "image"`** and nothing is saved —
**including with a valid 500 KB image** (control run). Two independent attempts, both sizes,
same result.

Checked against the closest existing bug, **ADO 142266** ("Social Icon Image upload fails"), and
it is **a different failure mode**: 142266 was the picker *refusing the upload outright* ("An
unexpected error occurred while uploading your file", no file created) because ~51 duplicate
copies of `icon_500kb.png` had accumulated in the root Documents folder; it was fixed 2026-09-19
by archiving the duplicates. In this session the uploads **succeeded** — documents `235932` and
`235948` were created and linked into the field — and the failure happens later, at submit.
The inline `# BLOCKED by ADO Bug #142266` comment on `test_site_content_editor_can_access_and_
publish_directly` predates that fix and is now stale.

Whether this is a product defect or an artifact of driving the picker through automation is
**not established** — it needs one manual click-through before anything is filed or an
occurrence is added to 142266. It does **not** undercut 142249's verdict: the 2 MB cap was
confirmed on the server, which is where the fix was implemented.

Evidence: `scratchpad/retest_shots2/`, `retest_shots4/`, `retest_log2.json`, `retest_log4.json`.

## 143511 — PASS on the described element; identity open

Linked TC **131153** is an unrelated RBAC publish case — **no scripted test proves this bug**.

Retested per the developer's 2026-09-27 comment, with the account language forced to **English**
and the page in **Arabic** (the precondition that triggers Liferay's language notice):

- `/ar/manage-social-media-icon`, watched for **10.5 s across 7 samples** — **no empty
  "معلومات:" notice box appeared**. Only the unrelated full-width "activation key expired"
  license banner at the top.
- Repeated on the English page — same, clean.
- No `Info` element found in the Objects panel.

**Open question for QA:** the bug as filed describes *"the 'Info' ('معلومات') icon in the Objects
admin panel shows no tooltip on hover and is not clickable."* The developer re-read it as
Liferay's bottom-right **language-notice toast**. That reinterpretation may well be right, but it
is their reading of a screenshot — the reporter should confirm it is the same element before the
bug is moved.

---

## Automation drift found (separate follow-up, not part of any bug's verdict)

The CMS UI moved under the suite. Confirmed live this session:

| Framework expects | Live CMS now |
|---|---|
| `SUBMIT_FOR_PUBLISHING_BUTTON = 'button:has-text("Submit for Publishing")'` | button is **"Submit for Review"** |
| row status `"Approved"` | status renders **"PUBLISHED"** / `منشور` |
| (no Unpublish on rows) | rows now expose **Unpublish** |

`ObjectAuthoringPage.submit_for_publishing()` / `save()` back **every** `manage-<slug>` test in
`cms/`, so this is broad, not local to Social Media Icon. Healing it is a separate, user-gated
change — not done here.

Also re-confirmed: the shared TEST_USER account's Liferay language **drifted to Arabic mid-run**
after an `/ar/` navigation, silently invalidating a whole round of English-locator checks. The
standards.md note on this is accurate and still unresolved.

---

## Artifacts

- `.allure-results-retest-142249/` — the tc_131180 run (broken, stale locator)
- scratchpad: `live_retest.py`, `live_retest2.py`, `live_retest3.py`, `live_retest4.py`,
  `retest_log*.json`, `retest_shots*/`

## Outcome — applied 2026-09-28 with the reporter's explicit approval

All three moved **Ready → Done**, each with its own history comment recording the evidence,
how it was verified, and the stated limitations:

- **141918** → Done (Sev 2 - High unchanged)
- **142249** → Done (Sev 3 - Medium unchanged)
- **143511** → Done (Sev 4 - Low unchanged) — the reporter confirmed the language-notice box
  is the element they filed.

No severities, tags or other fields were touched.

## Open follow-ups

1. **The Social Media Icon form save failure** — the reporter will check it by hand first.
   Nothing filed until it reproduces without automation.
2. **Heal the drifted CMS locators** (`Submit for Publishing` → `Submit for Review`,
   `Approved` → `PUBLISHED`) — user-gated, not done here. Affects every `manage-<slug>`
   test in `cms/`, not just Social Media Icon.
3. Two throwaway documents were uploaded to Documents and Media during the retest
   (`235932` 2.92 MB, `235948` 500 KB). **Not deleted** — awaiting go-ahead.
   No Social Media Icon or Upcoming Event Pin **records** were created or deleted —
   verified by API after the run: `upcomingeventpins totalCount = 2`,
   `socialmediaicons totalCount = 10`, both unchanged from the pre-run counts.

> Note for the automation backlog: 142266's own comment warns the duplicate-filename
> problem **will recur** because the suite re-uploads the same fixture name every run and
> never cleans up. This session added 2 more copies. Worth switching the fixtures to
> run-unique names.
