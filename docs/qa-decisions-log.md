# QA Decisions & Incident Log — Qatar Chamber

> Split out of `.claude/context/active/standards.md` on 2026-09-30.
> **This file is history, not rules.** Every binding rule distilled from the
> entries below now lives in `standards.md`. Read this when you need to know
> *why* a rule exists, or to check whether a past finding is still valid.
>
> Nothing here should be followed as an instruction. Where an entry records a
> **superseded** rule, the superseded text has been deleted from `standards.md`
> on purpose — git history holds the full wording.

---

## 2026-09-03 — Real content permanently deleted (record 49108)

**What happened.** During the PBI 129381 batch, the real "Objectives" pillar
card (ID 49108) was **permanently deleted** from qcdev. Content lost, no recycle
bin, no backup.

**Cause.** A delete-targeting helper, `newest_entry_code()` in
`ObjectAuthoringPage`, assumed "last row in the admin grid = most recently
created row" in order to pick a disposable `QCTEST-*` entry to clean up. That
assumption was wrong at least once, and the helper deleted whatever real record
happened to be last.

**Contributing factor.** The row list's "Entry" column showed an internal UUID
rather than the title — a separate Page Object defect — which is what made
position-based targeting look necessary in the first place. The actual fix is a
title/ID-based lookup, not a positional one.

**Rules this produced** (now in `standards.md` → *Destructive Operations*):
never delete by position; positively confirm a delete target is disposable
before running it; a "fix and re-run" instruction never implies authorization
for irreversible deletes.

---

## 2026-08-16 — `55a5c91` silently overwrote this file

The commit "baselines from Phase 1/2 PBI runs" — a routine baseline-sync commit
— **overwrote local additions** to `standards.md`, dropping whole sections with
no conflict and no notice. Known casualties:

- **Dev-Environment Navigation Quirks** — noticed and restored 2026-08-18.
- **Automation Structure** — the rule went missing long enough that a
  `web/pages/control_panel/` + `web/pages/header/` tree was written against a
  pattern the then-current rule had explicitly rejected. (That rule was later
  superseded anyway — see below.)
- **The "2 languages × 2 themes × 2 contrast" test-matrix methodology** — the
  original is **not recoverable**. A replacement was **reconstructed 2026-09-30**
  from `background.md`'s BRD facts plus what the framework actually supports, and
  now lives in `standards.md` → *Theme & Contrast Coverage Matrix*. It is labelled
  there as a reconstruction, not as ratified prior practice, and is open to
  correction by the QA Manager.

**Standing caution:** if you run `analyze-pbi` or baseline-sync tooling, diff
`standards.md` afterwards rather than assuming it is untouched.

---

## 2026-08-11 → 2026-09-01 — Automation structure: separate trees (superseded twice)

1. **2026-08-11** — framework flattened to the project root (not `./automation/`),
   at the QA Manager's request. *Still current.*
2. **2026-08-19** — a rule was re-confirmed requiring **co-located** CMS and web
   page objects, explicitly rejecting a separate tree. **Superseded.**
3. **2026-09-01** — the QA Manager reviewed the layout again and decided the
   CMS/Admin side deserved its own top-level tree, for clearer ownership between
   public-site and control-panel automation. **This is the current rule** and is
   stated in `standards.md`.

The 2026-08-19 text was kept inline in `standards.md` for months, annotated
"do not follow it" — a live risk of someone following it anyway. Deleted
2026-09-30.

---

## 2026-09-07 — Object Authoring replaces Content & Data (broadened same day)

**Original rule (morning):** publish / unpublish / set-to-draft / preview on a
content record must be performed from Object Authoring, not `Content & Data`.

**Broadened (same day):** `Content & Data` is retired **entirely** as an
automation path for any Object-Definition-backed content record — creating
content, editing field values, and every lifecycle action all go through Object
Authoring.

The narrower original wording was kept inline in `standards.md` under the
heading "Original rule text (still correct for the narrower case...)", which
made the section self-contradicting on a quick read. Deleted 2026-09-30; the
broadened rule is the only one that stands.

**Consequence flagged at the time, still worth honouring:** any Page Object or
test that previously drove content operations via `Content & Data` may show
*different behaviour* once corrected — including bugs already filed against the
old path. Re-verify rather than assuming an old result still holds.

---

## 2026-09-01 — Wait-strategy audit (one-time)

Audited every Page Object built in the 2026-08-31 CMS batch for blind
`wait_for_timeout(...)` calls.

**Converted to condition-based waits:**
`HomeBusinessEventsAdminPage.delete_row_by_title()`'s two fixed sleeps (300 ms
before reading the kebab menu, 1500 ms after confirming delete) became
`delete_item.first.wait_for(state="visible")` and
`row.first.wait_for(state="detached")`, each keeping the old fixed value as an
upper-bound timeout rather than a mandatory sleep. Live-verified: the real
teardown path ran end-to-end against qcdev and a direct admin-grid query
confirmed `QCTEST-135747`/`QCTEST-135748` were fully deleted (0 rows each) — the
teardown swallows exceptions, so the grid check, not the pytest summary, is the
real verification.

**Already correct, no change needed:**
`CommunityPartnersAdminPage.upload_partner_logo()` and
`HomeBusinessEventsAdminPage.upload_event_image()` wait on the upload modal
iframe's `state="detached"`, falling back to a short fixed sleep only if that
wait times out. `HomeBusinessEventsAdminPage.save()` waits on
`wait_for_url(... ENTRY_PERSISTED_URL_MARKER ...)`.

**Justified fixed graces, left as-is (evidence-based, not guesses):**
`SAVE_COMMIT_GRACE_MS = 2000` and `FORM_MOUNT_GRACE_MS = 2500` cover a
confirmed-live Liferay write-vs-read-cache propagation gap — the object-entry
write commits synchronously, but the read path a subsequent portlet render
queries is served off an asynchronously updated index that lags. There is **no
observable DOM or network signal** for it: no toast, spinner, or distinguishable
request. The windows were measured live, not guessed, and are documented at each
call site. `GmMessageAdminPage`'s extra 250 ms settle after the Status combobox
reports hidden is the same class of finding (the button label re-renders
~100–250 ms after the popup-close event).

**The rule this produced** (now in `standards.md`): waits are condition-based; a
fixed grace is permitted only where it is measured live, has no observable
signal to wait on, and is disclosed at the call site.

---

## 2026-09-01 — loadgroup vs. serial timing comparison: NOT OBTAINED

Reported honestly rather than manufactured. The `-n 0` serial baseline run of
the batch's 13 runnable tests came back unusable — 6 errors, 3 failures, 3
passed, 1 skipped, with real
`playwright._impl._errors.TimeoutError: Timeout 30000ms exceeded` failures.

Root-cause investigation during the same session found **an actual second
agent/process concurrently restructuring the framework's directory tree** while
the serial run was executing — a real violation of the one-agent-at-a-time rule,
which most plausibly explains the timeouts rather than the grouping change.
Running the 3-worker comparison on an already-unstable baseline, with another
actor confirmed active on the same shared session, was assessed as compounding a
known-bad condition, so it was not run.

**Status as of 2026-09-30: still not done.** This carried an "Action for the
next session" label in `standards.md` for four weeks without being executed. It
has been removed from the rules file and recorded here instead. If the number is
still wanted: confirm no other agent is active, then run the same 13-marker set
with `-n 0` and with `-n 3 --dist loadgroup` back-to-back and record both
wall-clock times.

---

## 2026-09-22 — Field-Coverage Tiered Derivation entered TRIAL

Introduced as **binding but unratified**, to be reviewed after the next 2–3 CMS
PBIs against four criteria: cases folded per PBI by tier vs. the predicted
15–20%; **zero** Tier-1 or never-reducible folds; no defect later found in a
folded area; a measurable drop in Phase-3 authoring time.

**Status as of 2026-09-30: the review is overdue** — several CMS batches have
run since, and no graduate-or-remove decision has been recorded. The section
remains in `standards.md` and remains binding until the QA Manager decides.

The measurement it quoted — *"387 of 609 `cms/tests` functions carry
`@pytest.mark.skip` (64%, vs 8% in `web/tests`)"* — was **stale by 2026-09-30**.
Re-measured that day: **447 / 1,098 = 41% in `cms/`**, and **193 / 1,715 = 11%
in `web/`**. The figures in `standards.md` were corrected; the original is kept
here for the record.

---

## 2026-09-30 — pytest.ini marker block converted to generated

The `markers =` block in `pytest.ini` was hand-maintained and had drifted badly:
**1,937 `tc_*` markers registered, of which 200 matched no test, while 535
`tc_*` marks present in the code were never registered at all.** A further 313
marks were applied *dynamically* (`getattr(pytest.mark, f"tc_{tc_id}")`) in 7
modules and so were invisible to any source grep.

Verified before changing anything: there is **no `--strict-markers` and no
`filterwarnings = error`** in `pytest.ini`, `conftest.py` or
`azure-pipelines.yml`, and **nothing in the repo parses the block**. Registration
is therefore documentation and `pytest --markers` discoverability, not a
correctness requirement — so regenerating it could not break marker selection.

`tools/sync_tc_markers.py` now owns every `pbi_*` and `tc_*` entry, harvesting
from pytest's own collection (which catches the dynamic marks, and keeps the
~640 skipped tests' entries). Hand-written taxonomy markers are preserved
verbatim. `--check` runs in the CI collect gate.

Result: 2,584 accurate `tc_` entries, zero `PytestUnknownMarkWarning` at
collection (previously ~700+), 2,999 tests still collected.

**Dropped in the process:** freeform batch-provenance comments that sat
interleaved between `tc_` lines. They were narrative, not configuration, and git
history retains them.

---

## 2026-09-30 — xdist_group table audited against the code

The singleton/`xdist_group` table in `standards.md` had drifted in both
directions — four groups listed but never applied, six applied but never listed,
and two rows under-counting their tests. The full audit, and the open question
it raised about the Strategic Pillar Card module, are recorded in
`docs/qa-environment-notes.md` § 5b–5d.

**No grouping was changed.** Altering xdist scheduling against a shared live
environment is a QA-Manager decision, not a documentation fix.

---

## 2026-09-30 — Theme/contrast matrix reconstructed

The methodology lost in `55a5c91` could not be recovered, so a replacement was
authored from first principles and is now in `standards.md`.

**What it rules:** the toggle *mechanism* is tested once globally against
`AccessibilityToolsComponent`; per-feature cases assert *rendering under* a
state and never re-test the switch. Default per feature is 4 cases (one per
axis: EN/Light/Normal baseline, AR, Dark, High Contrast), escalating to the full
8-combination cross-product only where the axes genuinely interact — features
asserting Figma colour tokens, and features rendering text over an
image/overlay/gradient.

**Divergence found while writing it (now named as debt in `standards.md`):**
three different signals were in use for "is dark mode on" —
`document.documentElement.getAttribute('data-theme') === 'dark'`
(`about_qatar_chamber`), `"dark" in html class`
(`business_opportunities/listing_page.py`, which also declares its own toggle
locators rather than composing the shared component), and the switch's own
`aria-checked` (the component). The rule now states the authoritative signals —
`<html data-theme="dark">` and `<html class~="qc-a11y-contrast">` — and notes
that asserting `aria-checked` proves the control flipped, not that the theme
applied. `AccessibilityToolsComponent` also carries `switch_to_dark_mode()` and
`enable_dark_mode()` as two names for one action.
