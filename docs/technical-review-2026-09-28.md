# Technical & QA Review — Qatar Chamber Automation Repo

**Date:** 2026-09-28 · **Branch:** `automation/phase3-cms-2026-09-08`
**Scope:** repo organisation, suite performance, and `.claude/context/active/standards.md`

> **Status: the DO items were executed on 2026-09-30** — see *Execution status*
> at the end. DECIDE and ASK items are untouched and still need your call.
> Every item carries an owner decision: **DO** (safe, mechanical),
> **DECIDE** (needs a QA-Manager call), **ASK** (destructive / needs approval).

---

## 0. Measured baseline (live, 2026-09-28)

| Metric | Value |
|---|---|
| Test functions — `cms/tests` | 1,098 (**447 skipped, 41%**) |
| Test functions — `web/tests` | 1,715 (**193 skipped, 11%**) |
| **Total** | **2,813 tests, 640 skipped (23%)** |
| `pytest.ini` | 2,406 lines — **1,937 are `tc_<id>` marker registrations** |
| Largest test module | `cms/tests/board_of_directors/...` — 5,143 lines |
| Tracked binary fixtures | 72 files; largest single blob 22 MB |
| `.git` | 48 MB |
| Untracked root clutter | 167 `scratch_*`, 87 PNGs, 18 ad-hoc `.py`, 27 allure dirs |

---

## PART 1 — Technical Manager hat

### 1.1 Line count is NOT the performance problem

A 5,143-line module holding ~100 real test functions plus a documented
drop-decision log is **normal at this test count**, not a defect. Splitting
those files is an **organisation** win (review diffs, merge conflicts,
ownership) — not a speed win. It should not be sold as performance.

**The real wall-clock cost, in order:**

1. **The qcdev environment** — license/connection gate
   (`core/web/license_gate.py`), the ~30 s session drop
   (`core/web/session_guard.py`), and the `-n 3` parallelism ceiling those
   force. This dominates everything else.
2. **640 skipped tests** — they cost collection time, review time and
   reporting noise, and return zero signal.
3. Everything else is noise by comparison.

### 1.2 `pytest.ini` — 1,937 hand-maintained marker lines *(DO)*

**Verified:** there is no `--strict-markers` and no `filterwarnings = error` —
not in `pytest.ini`, not in `conftest.py`, not in `azure-pipelines.yml`.
Those 1,937 lines therefore do **nothing** except silence
`PytestUnknownMarkWarning`. `pytest -m tc_137713` selects correctly without
them.

Two acceptable fixes — pick one:

- **(a) One line:** `filterwarnings = ignore::pytest.PytestUnknownMarkWarning`,
  and delete the `tc_*` block entirely. Smallest change, and `pytest --markers`
  stops being a 2,400-line wall.
- **(b) Generate it:** `tools/sync_tc_markers.py` rebuilds the block from the
  `@pytest.mark.tc_*` marks actually present in code, run in the existing
  `--collect-only` CI stage. Keeps the documentation value, removes the hand
  maintenance.

**Recommendation: (b).** The descriptions carry real traceability value
(TC id → what it asserts); they just must never be typed by hand again.

### 1.3 Binary fixtures committed to git *(DO — going forward only)*

72 tracked fixture blobs, with obvious duplication:

| File | Copies |
|---|---|
| `valid_pdf_4mb.pdf` | 4 |
| `valid_cover_1_5mb.jpg` | 4 |
| `unsupported_cover.gif` | 4 |
| `pdf_at_5mb_boundary.pdf` | 3 |
| `oversized_pdf_6mb.pdf` | 3 |

Plus `web/tests/home_about_summary/fixtures/about_counter_icon_oversized.png`
(22 MB) and `about_building_oversized.jpg` (12 MB).

These are **synthetic size-boundary files** — their only meaningful property is
byte size and format. Replace with a shared generator:

```
tools/fixture_factory.py
  make_pdf(size_bytes) · make_image(fmt, size_bytes, dims) · make_unsupported(ext)
```

called from a session fixture writing into `tmp_path`. The repo shrinks, the
"is this 5 MB boundary file actually 5 MB?" question becomes code, and the
4x/3x duplication disappears.

**History rewrite is a separate decision (ASK)** — it invalidates every existing
clone. Do the going-forward fix first; only rewrite if clone time actually hurts.

### 1.4 Root directory clutter *(DO)*

167 `scratch_*` files, 87 PNGs, 18 ad-hoc `.py` scripts (`parse_130713.py`,
`merge_classification_*.py` ...), 27 allure output directories, and
`_to_delete/` still present — the `.gitignore` comment asking for its manual
deletion dates from 2026-08-18.

**Not a delete sweep — a placement rule:**

- Scratch / throwaway analysis output → the session scratchpad directory,
  never the repo root.
- Reusable one-off scripts → `tools/`.
- **Bug/test evidence PNGs (`bug_evidence_*`, `tc*`, `live_*`) →
  `docs/evidence/`, kept.** 24 of these are *tracked* and are attachments on
  filed Azure bugs — they must not be deleted as part of tidying
  (**ASK** before touching any of them).
- `.gitignore` additions: `scratch_*`, `.allure-results-*`, `*_snapshot.md`,
  `snap*.md`.
- `_to_delete/` → confirm nothing of value remains, then remove *(ASK)*.

### 1.5 Module organisation *(DECIDE)*

The `web/` + `cms/` split by surface is sound and should stay. The issue is
**inside** the large modules:

- Split any `test_<feature>_control_panel.py` over ~1,500 lines by **concern**
  (`_fields.py` / `_lifecycle.py` / `_rbac.py`) within the same folder.
  Collection and markers are unaffected; reviews become readable.
- **Stale docstrings are actively misleading.**
  `cms/tests/board_of_directors/test_board_of_directors_control_panel.py`
  opens with the path `web/tests/board_of_directors/...` (the wrong tree since
  the 2026-09-01 split) and states "the default `-n 2` in pytest.ini" when
  `addopts` carries `-n 3`. Sweep these — a wrong instruction in a docstring is
  worse than no docstring.
- The copy-paste probe found small helpers duplicated across modules
  (`_hex_to_rgb` x3, `_is_arabic_text` x3, `_login_as_site_content_editor` x3,
  `_parse_css_color` x2 ...). Promote them to `core/utils/` — colour parsing and
  Arabic-text detection are assertion primitives, not per-feature code.

---

## PART 2 — QA Manager hat: `standards.md` (793 lines)

The content quality is genuinely high. The incident write-ups (the 49108
deletion, the locale drift, the Liferay read-cache gap) are the kind of
institutional memory most projects never capture. **The problem is the file's
shape, not its thinking.** It is read at session start, every session, and it
has grown into three different documents wearing one hat.

### 2.1 Superseded rules kept inline — the highest-risk defect *(DO)*

The file contains rules it explicitly tells the reader not to follow:

- **"Automation Structure"** keeps a 2026-08-19 re-confirmation annotated
  *"Superseded 2026-09-01 ... do not follow it"*.
- **"Object Authoring"** keeps *"Original rule text (still correct for the
  narrower lifecycle-action case ...)"* under a rule that broadened it.

An agent — or a new engineer — reading 793 lines at session start can act on
the retired text. **Delete the superseded bodies. Git holds the history.**
Keep at most a one-line pointer: *"Superseded 2026-09-01 — see commit X."*

### 2.2 The measured numbers are stale *(DO)*

The Field-Coverage section states:

> "387 of 609 `cms/tests` functions carry `@pytest.mark.skip` (64%, vs 8% in `web/tests`)"

**Live today: 447 / 1,098 = 41% in `cms/`, and 193 / 1,715 = 11% in `web/`.**
A standards document quoting wrong measurements undermines the rules built on
them. Either refresh the figures, or date-stamp them explicitly as a historical
snapshot.

### 2.3 The TRIAL section is overdue for a verdict *(DECIDE — yours)*

"Field-Coverage Depth — Tiered Derivation (TRIAL, 2026-09-22)" is **binding but
unratified**, pending review "after the next 2–3 CMS PBIs". Several CMS batches
have run since. It names four graduation criteria (cases folded by tier against
the predicted 15–20%; zero Tier-1 folds; no defect found in a folded area; a
measurable authoring-time drop). **A graduate-or-remove decision is owed.**

**Recommendation: graduate it**, keeping the Tier-2 exemption list verbatim —
that list is what prevents a `Read More URL`-class P1 from being folded. But
graduate it on *recorded numbers*, not impression: the rule's own text demands
the real reduction figure, not the prediction.

### 2.4 The singleton table had drifted — audited 2026-09-30 *(DECIDE)*

**Correcting my own earlier finding.** I first reported the `Vision` singleton's
"ID pending confirmation" as a live race on an unprotected shared record. Having
checked the code, that framing was wrong on both halves:

- **The "missing Vision ID" is probably a phantom.** The old table said Vision was
  "the third member of the same Strategic Pillar Card carousel as Mission (49082)
  and Objectives (49108)". But VMO is a **separate 3-entry object** (`vmo-section`,
  keyed by `QCDEMO-129395-VMO-*` external reference codes, confirmed live
  2026-09-07), while 49082/49108 are Strategic Pillar Card records in a different
  module. The table conflated two surfaces; the number may not exist there at all.
- **There is no unprotected-real-record risk in that module.** `tc_135556`,
  `tc_135558`, `tc_135559`, `tc_135560` and `tc_135561` each create their own
  disposable `QCTEST-<tc_id>-*` card, act on it, and delete it **by entry code** in
  teardown. None touches the real Vision/Mission/Objectives records. That is
  exactly what the disposable-test-data and never-delete-by-position rules
  require — **the module complies.**

**What the audit did find is a documentation defect, in both directions:**

| | Groups |
|---|---|
| Listed in the table, applied to **no** test | `objectives_49108`, `about_us_section_52157`, `home_contact_us_section_article_53012`, `home_contact_us_inquiry_category_52706` |
| Applied in code, **absent** from the table | `board_directory_page_main` (21 tests), `smi_production_rows` (5), `hero_banner_slide_45560` (4), `achievement_counter_45659` (4), `member_services_sector_80734` (3), `contact_us_public_webform` (2) |
| Listed but **under-counted** | `gm_message_79878` (table: 1 test, code: 5), `pin_event_49205` (table: 1, code: 4) |

**The one open question, lower severity than I first said:** the disposable cards
in `home_strategic_direction` are created in the same carousel that
`tc_135557`/`tc_135562` mutate under `xdist_group("mission_49082")`, and some
tests assert on public carousel contents/ordering. A module-level group would
remove that interference. **I have changed no grouping** — altering xdist
scheduling against a shared live environment is your call, not a doc fix.

**🟡 Separately, a real coverage hole stands:** the "2 languages × 2 themes × 2
contrast" matrix lost in commit `55a5c91` was never restored. Theme/contrast is
BRD-confirmed at the same tier as bilingual, so it should be restored rather than
left as an open question.

### 2.5 A stale action item *(DO)*

The loadgroup-vs-serial timing comparison has carried "**Action for the next
session**" since **2026-09-01** — four weeks. Either run it or delete the
commitment; a standing action nobody executes trains readers to skim the file.

### 2.6 Structural fix — split the document *(DECIDE — highest leverage)*

Three documents are currently fused into one:

| Goes to | Content |
|---|---|
| **`standards.md`** — normative only | Service/Platform codes, ID convention, priority rubric, tag taxonomy, Definition of Done, writing rules, and the *rules* distilled from every incident (never delete by position; Object Authoring only; anonymous context for public-visibility checks; English-only locators; disposable test data; condition-based waits) |
| **`docs/qa-decisions-log.md`** | The 49108 deletion narrative, the locale-drift investigation, the Wait-Strategy Audit, the `55a5c91` overwrite history, superseded rules, the un-obtainable timing comparison |
| **`docs/qa-environment-notes.md`** | qcdev quirks — announcement popup, license gate, session drop, the singleton record table and its baselines |

The **Wait-Strategy Audit** is the clearest example: it is a one-time audit log.
Only its *rule* — "condition-based waits; a fixed grace is allowed only when
measured live and disclosed at the call site" — belongs in standards.

**Effect:** roughly halves what must be read at session start. That is the
performance win that actually compounds, because it is paid every session.

### 2.7 Overlap with `MEMORY.md` *(DO)*

`MEMORY.md` and `standards.md` both carry the singleton records, the
no-concurrent-agents rule, and the destructive-ops rule. Duplication is fine —
drift is not. **Name `standards.md` as the single source of truth** in
`MEMORY.md`, so the memory entries stay pointers rather than second copies.

### 2.8 What should NOT change

- The **Priority rubric** — correctly reasoned for a project with no payment flow.
- The **Webform/Approval** and **Bilingual** checklists — the real backbone of
  this BRD, and specific enough to be assertable.
- The **Destructive-Operations** rules — written in blood (record 49108). Keep
  every word; only move the narrative to the decisions log.
- **English-only locators** — the right call, and the locale-drift gotcha note
  is what makes it usable.

---

## PART 3 — The item that actually cuts cost: 640 skipped tests *(DECIDE)*

23% of the suite returns no signal. standards.md's own 2026-09-22 rule already
identifies **68 of them (20% of that Web batch) as buildable** with disposable
`QCTEST-*` records rather than permanently skipped.

Proposed sequence — **reduce cost per test, never cut scope**:

1. Classify all 640 skips into: (a) buildable with disposable test data,
   (b) blocked by the qcdev environment, (c) genuinely not automatable.
2. Bucket (a) → convert per the disposable-test-data rule.
3. Bucket (b) → this is an **environment escalation**, not a QA problem. The
   license/connection gate is the single largest cost in the suite; it warrants
   a request for a dedicated CMS instance or a raised connection limit, with the
   measured 41% CMS skip rate as the evidence.
4. Bucket (c) → must be `Manual`-tagged in Azure, not `skip`-ped in code. A
   permanently-skipped automated test is test debt booked as coverage.

---

## Priority order

| # | Item | Type | Effort | Payoff |
|---|---|---|---|---|
| 1 | Confirm and group the `Vision` singleton ID | ASK | minutes | prevents a shared-record race |
| 2 | Delete superseded rule bodies from standards.md | DO | ~1 h | removes the wrong-rule risk |
| 3 | Split standards.md into 3 files | DECIDE | ~2 h | paid back every session |
| 4 | `tools/sync_tc_markers.py` + shrink pytest.ini | DO | ~1 h | −1,900 hand-maintained lines |
| 5 | Refresh the stale skip measurements | DO | minutes | credibility of the rules |
| 6 | TRIAL section: graduate or remove | DECIDE | judgement | closes an unratified binding rule |
| 7 | Classify the 640 skips into 3 buckets | DECIDE | ~1 day | the real cost reduction |
| 8 | `fixture_factory.py`, stop committing blobs | DO | ~3 h | repo weight, going forward |
| 9 | Root clutter → placement rule + `.gitignore` | DO | ~1 h | readable repo |
| 10 | Restore the theme/contrast matrix | DECIDE | ~1 h | closes a real coverage hole |
| 11 | Stale docstrings + shared helpers → `core/utils/` | DO | ~2 h | maintenance |
| 12 | git history rewrite for binaries | ASK | — | only if clone time hurts |

---

## Execution status — 2026-09-30

### Done and verified

| # | Item | Evidence |
|---|---|---|
| 4 | `pytest.ini` marker block is now **generated** by `tools/sync_tc_markers.py` | 2,584 accurate `pbi_`/`tc_` entries; **zero** `PytestUnknownMarkWarning` (was ~700+); 2,999 tests still collect; `--check` idempotent and wired into the CI collect gate |
| 2 | Superseded rule bodies deleted from `standards.md` | No "do not follow it" text remains; the history moved to `docs/qa-decisions-log.md` |
| 3 | `standards.md` split into 3 files | `standards.md` 793 → **642** lines (normative only) + `docs/qa-environment-notes.md` (211) + `docs/qa-decisions-log.md` (216) |
| 5 | Stale skip measurements refreshed | `387/609 (64%)` → the measured **447/1,098 (41%)** in `cms/`, **193/1,715 (11%)** in `web/` |
| 9 | Root-clutter placement rule + `.gitignore` patterns | `scratch_*`, `.allure-results-*`, `snap*.md`, `out_*.txt` ignored; evidence PNGs explicitly **kept** |
| — | Memory updated to point at the new structure | `read_standards_before_any_run`, `qcdev_singleton_records` |

**Honest correction to my own estimate:** I predicted the split would "roughly
halve" what is read each session. The real reduction is **793 → 642 lines, ~19%**,
because most of the file turned out to be genuinely normative (the tag taxonomy,
the tiered-derivation rules and the folder tables all had to stay). The larger
win is qualitative: zero self-contradicting text, and the narrative no longer
competes with the rules.

**Also honest:** `pytest.ini` got *longer* (2,406 → 2,743 lines), because the
generator added the 535 + 313 markers that were missing. The win is correctness
and zero hand-maintenance — not line count. Which is the same point Part 1.1
makes: line count was never the problem.

### Found while executing (not in the original review)

- **The marker block was worse than reported.** Not just unmaintained: 200
  registered markers matched no test, 535 marks in code were unregistered, and a
  further **313 were applied dynamically** (`getattr(pytest.mark, f"tc_{tc_id}")`
  in 7 modules) so no source grep could ever see them. The generator harvests
  from pytest's own collection to catch these.
- **3 taxonomy markers were never registered** — `comm`, `chatbot`, `navigation`.
  Added by hand (they are taxonomy, not traceability, so they stay hand-owned).
- **`pytest.ini` has been corrupted by a merge before** — a `<<<<<<< HEAD` marker
  at line 30 appears in an old baseline log. A generated block removes that whole
  class of conflict.
- **Code docstrings cite `standards.md` section headings by name** (12 cite
  "Destructive Operations Against qcdev" alone). The split initially orphaned
  several; all headings were renamed back to their cited forms and re-verified,
  and a warning now sits at the top of `standards.md`. There is already a commit
  in the history titled *"Point standards.md citations at sections that actually
  exist"* — so this has bitten the team before.

### Not done — still needs your call

| # | Item | Why it is blocked |
|---|---|---|
| 1 | Add/merge an `xdist_group` on `home_strategic_direction` | Changes scheduling against shared live qcdev — your decision |
| 6 | TRIAL section: graduate or remove | QA-Manager judgement; recommendation is **graduate** |
| 7 | Classify the 640 skips into 3 buckets | ~1 day of work; needs scheduling |
| 8 | `fixture_factory.py` + stop committing blobs | Touches test code across many modules |
| 10 | Restore the theme/contrast matrix | Needs the original methodology or a fresh decision |
| 11 | Stale docstrings + shared helpers → `core/utils/` | Mechanical but broad; worth its own pass |
| 12 | git history rewrite for binaries | **ASK** — invalidates every clone |
| — | Move root evidence PNGs → `docs/evidence/` | **ASK** — 24 are tracked attachments on filed Azure bugs |
| — | Delete `_to_delete/` | **ASK** — confirm nothing of value first |

**Nothing was committed.** All changes are in the working tree for your review.

---

## Item #7 — the 640 skips, classified (2026-09-30)

Full inventory: [`docs/skip-audit-2026-09-30.md`](skip-audit-2026-09-30.md)
(+ `.json`), regenerable with `python tools/audit_skips.py`.

**629 of 640 skips inventoried** by AST walk (the ~11 gap is skips applied
inside decorator factories, not literal decorators — stated in the report, not
smoothed over). Bucket-level agreement on a hand-checked stratified sample of
32: **28/32 (88%)**, and all 4 disagreements were rows left `UNCLASSIFIED` that
should have been bucketed — the tool fails conservatively rather than filing a
test under the wrong owner.

| Bucket | Count | Share | Owner |
|---|---:|---:|---|
| ENVIRONMENT | 355 | 56% | Infra / project |
| UNCLASSIFIED | 118 | 19% | QA automation (human read) |
| BUILDABLE | 101 | 16% | QA automation |
| PRODUCT_GAP | 49 | 8% | QA Manager |
| NOT_AUTOMATABLE | 6 | 1% | QA Manager |

### The finding that matters

**343 of 629 skips (55%) sit in three CMS modules** — `gm_message` (141),
`chambers_law` (108), `vision_mission_objectives` (94) — and **323 skips (51%)
across the whole suite** name either the qcdev connection-limit gate or an
unreachable Control Panel session.

**That is one environment escalation, not hundreds of test tickets.** More than
half the skipped suite unblocks with a dedicated CMS instance or a raised dev
connection limit. No test rewriting required. This is the single biggest lever
on the suite's value, and it is consistent with "reduce cost per test, never cut
scope".

### Ready to act on, small and concrete

- **6 `NOT_AUTOMATABLE` cases** — 2 reCAPTCHA (Google Enterprise *invisible*
  mode, so there is genuinely no unsolved state to drive) and 4 requiring a real
  email inbox. `standards.md` Axis 1b says these belong under `Manual` in Azure,
  **not** skipped in code. TCs: `142571`, `143602`, `143606`, `143607`,
  `143609`, plus one media-dept CAPTCHA case with no `tc_` marker.
  **Needs your yes — it is an Azure write.**
- **17 skips carry no reason string at all** (15 in
  `web/tests/made_in_china_expo/`). `standards.md` requires the exact blocking
  reason on every skip; these violate it regardless of bucket.
- **101 `BUILDABLE`** — QA owns these outright. They can be rebuilt against
  disposable `QCTEST-*` records without anyone's permission, per the
  2026-09-22 rule. Note one is already flagged in-code as *"re-evaluated
  2026-09-22: CMS write access IS available now — this is no longer an access
  gap, it is a cost decision."*

---

## Items #10 and #8 — done 2026-09-30

### #10 — Theme & contrast matrix *(reconstructed, not restored)*

The 2026-08 original is **not recoverable**, so a replacement was authored from
`background.md`'s BRD facts plus what the framework actually supports. It is in
`standards.md` → *Theme & Contrast Coverage Matrix*, **labelled as a
reconstruction** so nobody mistakes it for ratified prior practice.

What it rules:
- **Mechanism vs. rendering split** — the toggle itself (flips, applies,
  persists) is tested **once** globally against `AccessibilityToolsComponent`.
  Per-feature cases assert *rendering under* a state and never re-test the
  switch. Without this, 40 features each re-verify the same toggle.
- **Default 4 cases per feature**, one per axis: EN/Light/Normal baseline, AR,
  Dark, High Contrast — not the 8-way cross-product.
- **Escalate to the full 2×2×2** only where the axes genuinely interact:
  features asserting Figma colour tokens, and features rendering text over an
  image/overlay/gradient. Both classes have already produced findings here.

**Divergence found while writing it** (now named as debt in `standards.md`):
three different signals were in use for "is dark mode on" —
`data-theme="dark"` (`about_qatar_chamber`), `"dark" in html class`
(`business_opportunities/listing_page.py`, which also declares its own toggle
locators instead of composing the shared component), and the switch's own
`aria-checked` (the component). The rule now names the authoritative signals
(`<html data-theme="dark">`, `<html class~="qc-a11y-contrast">`) and states that
asserting `aria-checked` proves the control flipped, **not** that the theme
applied.

### #8 — `tools/fixture_factory.py`

Generates all 50 upload-test binaries instead of committing them —
**116 MB of tracked blobs replaced by one pure-stdlib script.**

| Check | Result |
|---|---|
| Byte-exact vs. the committed originals | **50/50**, verified with `--verify` against the real tree |
| Format-valid (Pillow decode / PDF structure) | **50/50** |
| Test changes required | **none** — files are written to the paths tests already reference |
| Cost at session start | 0.002 s (idempotent, size-checked) |

Wired into `conftest.py`'s `pytest_sessionstart`, so a fresh clone materialises
its own fixtures. Collection still green at 2,999 tests.

**Two things worth stating honestly:**
- Hand-rolled JPEG and GIF headers **failed validation on the first attempt**
  (22/50 undecodable). The fix was to embed a known-good 1×1 JPEG and GIF and
  pad *those* through legal container slots (JPEG `COM`, GIF Comment Extension,
  PNG `tEXt`, PDF comment) rather than hand-building headers. Caught because the
  files were decoded, not just size-checked.
- **The originals are still tracked, on purpose.** These files satisfy the size
  and format contract, but whether *Liferay's uploader* accepts a synthetic
  JPEG/PDF as valid content has **not** been verified against qcdev. One real
  upload test must pass against generated fixtures before the committed
  originals are removed — and that removal needs your yes.

---

## Item #11 + a severe finding — 2026-09-30

### Docstring self-paths — 11 fixed

Eleven `cms/` modules opened with a docstring naming a `web/...` path — leftovers
from the 2026-09-01 tree split. All corrected (line 2 only, rest verbatim);
0 remain. The three `web/` files that looked wrong were legitimate
cross-references, not self-path errors.

### 🔴 39 tests race on ONE real Board Member record — NOT FIXED, needs your call

Found while correcting the docstring in
`cms/tests/board_of_directors/test_board_of_directors_control_panel.py`, whose
old warning ("every test in this module edits the SAME shared page draft…
default `-n 2`") was stale in both directions.

What is actually true:

| Group | Tests | Protected? |
|---|---:|---|
| Page-draft (`board_directory_field_edit`) | 21 | ✅ `xdist_group("board_directory_page_main")` |
| **Board-member (`board_member_field_edit`, `short_bio_edit`, `role_badge_label_edit`, `display_order_edit`, `board_member_rich_text_edit`)** | **39** | ❌ **none** |

Those 39 each open the **first** row matching category "Board Member" —
`find_row_index_by_category` is **deterministic**, so all 39 hit the **same real
record** — then capture the original value, edit it, and revert in teardown.

Under `-n 3 --dist loadgroup`, three can interleave on that record. A revert can
write back a value another test had just set: a **lost update that permanently
corrupts real CMS content**, not a flaky failure. **This is the same failure
class that destroyed record 49108 on 2026-09-03.**

**Proposed fix (one line per test):**
`@pytest.mark.xdist_group("board_member_shared_row")` on those 39. It can only
*reduce* concurrency, never increase it.

**Why it is not applied:** I attempted the bulk edit and the harness blocked it
as a sweeping automated change to test code — correctly, in my view, for a
39-function rewrite. It also changes xdist scheduling against a live shared
environment, which is a QA-Manager decision either way. **It needs your explicit
go-ahead.**

**Interim mitigation, already in place:** the module's docstring now states the
accurate situation and tells anyone running it to use `-n 0` or
`--dist loadfile` for that file. Also recorded in
`docs/qa-environment-notes.md` § 5c-bis.

### Helper de-duplication — deliberately NOT done

The "duplicated" helpers have **diverged**, so unifying them would silently
change assertions:

| Helper | Divergence |
|---|---|
| `_hex_to_rgb` | `faq`/`member_services` return a **tuple** `(r,g,b)`; `qatar_market_overview` returns a **string** `"rgb(r, g, b)"` |
| `_px` | `chairman_message` returns `round(float(...))`; `vision_mission_objectives` returns unrounded `float` |
| `_parse_css_color` | one uses `startswith("rgb")`, the other `find("rgb")` + slice — different behaviour on prefixed values |

Note `core/web/design_tokens.py` **already exports `hex_to_rgb`** (the string
form) and is being bypassed. The real hazard is the shared *name* with unshared
*semantics*: copying `_hex_to_rgb` between modules silently changes the return
type. Consolidation is worth doing, but as its own reviewed change with each
call site checked — not as a mechanical sweep.

---

## 2026-10-01 — shared-row race fixed, vocabulary cleaned

### ✅ The Board Member race is closed

All **39** tests using `board_member_field_edit`, `short_bio_edit`,
`role_badge_label_edit`, `display_order_edit` and `board_member_rich_text_edit`
now carry `@pytest.mark.xdist_group("board_member_shared_row")`.

| | before | after |
|---|---:|---:|
| tests sharing one real record, ungrouped | 39 | **0** |

The module's two groups are now `board_directory_page_main` (19 — the shared
page draft) and `board_member_shared_row` (39 — the shared member row). The
module is safe under the default `-n 3 --dist loadgroup` again, and the `-n 0`
workaround is withdrawn from the docstring, `CLAUDE.md` and
`docs/qa-environment-notes.md` § 5c-bis.

> Correction to the 2026-09-30 entry: the page-draft group covers **19** tests,
> not 21. The earlier figure came from a `grep` that also counted a docstring
> mention; the AST count was 19 throughout.

**Standing rule now recorded:** a fixture that selects its target by "first
match" is a shared-record fixture even when nothing in its name says so. A new
test using any of those five fixtures must carry the same group.

### Report vocabulary — 94 → 9

Allure step titles and assertion messages still said "Submit for Publishing"
and "Status 'Approved'", so the **reports stakeholders read** showed retired
vocabulary even though the code was correct.

| | count |
|---|---:|
| `Submit for Publishing` → `Submit for Review` (report-facing) | 85 |
| `Status 'Approved'` → `Status 'Published'` | 4 |
| **remaining** | **9** |

Docstrings and comments were deliberately **left alone** — they legitimately
explain the migration, and rewriting them would destroy the history.

**Why 9 remain:** they sit inside f-string expressions split irregularly across
implicitly-concatenated literals, where a safe automated edit stops being safe.
Two separate passes were attempted; one was aborted by its own `ast.parse`
guard before writing, after it produced a broken literal. Left for a hand pass:
6 in `test_chambers_law_field_validation.py`, and 1 each in
`test_home_community_partners`, `test_home_promo_banners`,
`test_home_strategic_partners`.

### Verified after every change

0 syntax errors across `cms/` and `web/` · conventions guard 11/11 ·
**3,822 tests collect, 0 errors** · `sync_tc_markers --check` in sync ·
fixture manifest 50/50.
