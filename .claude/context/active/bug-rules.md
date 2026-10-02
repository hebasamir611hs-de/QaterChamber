# QATAR CHAMBER — Bug Rules (Phase 3)

> **Normative rules only.** These rules decide what counts as a bug, how a finding
> gets filed, and which cases run first. They apply to every Phase-3 run on both
> surfaces (`Web` and `Control_Panel`). They were agreed with the user on
> 2026-10-02.
>
> **Precedence:** for this project these rules **override** the qa-engine plugin
> where the two conflict. That covers `automation-standards.md`'s "every failure,
> no gate" scope, the quality-control-engineer's "every failure is eligible",
> and `create-azure-bug`'s per-TC-only dedup. Where the plugin is silent, the
> plugin applies.
>
> Related rules that stay in `standards.md` and are not repeated here: the
> Priority Rubric, Content Editorial Workflow, Locators and CMS Navigation, and
> Test Data and Destructive Operations.

---

## Rule 1 — Pixel Tolerance Against Figma (±5 px images, ±2 px layout, text exact)

A measured difference **within the tolerance** for its element type is **not a
bug**. A difference beyond it is a finding, and it goes through Rule 3 before
anyone calls it a bug.

| Element type | Tolerance |
|---|---|
| Images | ±5 px |
| Layout (non-image, non-text) | ±2 px |
| Text | exact (0 px) |

- **Images (±5 px):** photos, banners, hero/background images, logos, icons and
  thumbnails. Covers their width, height and position.
- **Layout (±2 px):** spacing and the size of non-image elements. That means
  padding, margin, gap, offset/position, border-radius, and the width and height
  of buttons, cards, inputs and containers (user decision, 2026-10-02).
- **Text (exact):** font size, line height, font family, font weight
  and copy are compared **exactly** against Figma, with no tolerance (user
  decision, 2026-10-02).
- **Also compared exactly:** colour, element presence or absence, element order,
  and RTL/LTR direction.
- **Same viewport:** compare at the viewport the Figma frame was drawn for
  (desktop, tablet or mobile). A difference measured at a different viewport is
  not evidence.
- **Assertions:** automated geometry assertions use the tolerance for their
  element type (`abs(actual - figma) <= 5` for images, `<= 2` for layout), never
  exact equality. Text assertions use exact equality.
- **Cumulative drift:** the tolerance is per measured property. If several
  in-tolerance differences add up to a visibly broken layout (overlap,
  clipping, wrapping, horizontal scroll), the broken layout itself is the
  finding.

## Rule 2 — One Bug per Root Cause, Not per Test

When one defect makes several tests fail, file **one** bug and record every
affected test on it. Do not file one bug per test.

**Same root cause** means a single fix would make all the failures pass. Typical
cases:

- The same form is missing the same field (for example the Arabic field), and
  every case that opens that form fails on it.
- The same UI defect shows on Chrome, Firefox, Edge and tablet runs of the same
  page.
- The same CMS change fails to reach the public page, across every case that
  checks it.

**Not the same root cause:**

- The same symptom on two different pages or components.
- The same page, but different elements or different expected values.
- EN and AR failing differently.

If you are unsure, ask the user before filing, and file nothing until they decide.

**Filing procedure.** The MCP dedups only per Test Case (`TC:<id>`), so it will
not merge across tests on its own.

1. File **one** bug through `create-azure-bug`, against the most representative
   TC. Pick the highest-priority TC, and prefer Chrome/desktop/EN when the cases
   are otherwise equal.
2. List every affected TC in the bug body (Repro Steps) under an **"Also
   reproduces in"** heading. This is the "comment with the repeated tests" the
   rule asks for. Later occurrences go in History comments (step 4). Give the TC ID, title, and the browser/device/language that differs.
3. Add a `TC:<id>` tag for every other affected TC through
   `update_bug(add_tags=…)`. This uses the normal two-call preview and confirm.
   - The tag is what makes later runs dedup onto this bug through
     `find_existing_bug` instead of filing duplicates.
   - It is also how `get_test_cases_of_bug` and `verify-ready-bugs` find every
     affected TC to retest. A TC that is only named in a comment never gets
     retested.
4. When an affected TC fails again in a later run, `add_bug_occurrence` on the
   same bug, with that run's screenshot.
5. **Test outcomes are not merged.** Every affected test point is still marked
   **Failed** through `set-test-results`. Only the bug is shared.
6. **Duplicates already filed** (one bug per test from an earlier run): pick the
   survivor by step 1, move the other TCs' tags onto it, and close the rest as
   Duplicate. The close needs the user's explicit yes on the exact bug IDs.

## Rule 3 — Confirm Before Calling Anything a Bug

A failing assertion is only a **finding**. It becomes a **bug** only after all of
the following hold:

1. **Check it against the PBI.** Re-read the PBI's **Description** and
   **Acceptance Criteria**, and the test case's **Expected Result**. The observed
   behaviour must contradict what they say. If the PBI is silent or ambiguous on
   the point, it is an open question for the user, not a bug.
2. **Reproduce it live.** Repeat the behaviour manually, outside the failing
   assertion, on the environment the run targeted (qcdev by default), and take a
   screenshot. For data-changing cases, also check the persisted result, not
   just the UI message.
3. **Rule out our own side:**
   - test code;
   - the locator or selector (for example a generic `role=alert` that misses
     Liferay's real error UI);
   - test data;
   - timing;
   - the account the test ran as (`TEST_USER` skips review);
   - `Active Status` left unticked;
   - an authenticated context used for a public-visibility check;
   - stale vocabulary (`Submit for Publishing` / `Approved`);
   - the environment (session drop, licence expired, connection-limit gate).

   These checks are defined in `standards.md` and `docs/qa-environment-notes.md`.
   Apply them, do not re-derive them.
4. **Classify it.** `triage-failures` classifies it as `PRODUCT_BUG`.
   `AUTOMATION_BUG`, `ENVIRONMENT_ERROR` and `NEEDS_INVESTIGATION` never reach
   Azure. Fix or escalate them instead.
5. **Get the user's yes.** Show the user the evidence for the confirmed finding
   and get an explicit yes before `create_bug`, even when the evidence is
   convincing. This is the user's existing standing rule, restated here so the
   process sits in one place.

If the root cause is on our side, fix the test and do not file anything. If a
step cannot be completed (the page can't be reached, or the result is
inconclusive), stop and ask the user. Don't guess and don't file.

## Rule 4 — Run Order and the P3/P4 Review

1. **P1 and P2 cases run first.** Script and run every P1/P2 case of the PBI
   before touching anything lower.
2. **P3 and P4 cases are reviewed before they are scripted.** Before writing any
   automation for them, give the user a list with one row per case:

   | TC ID | Title | Priority | Recommendation (Run / Skip) | Reason |
   |---|---|---|---|---|

3. **Skip test.** Recommend **Skip** only when a bug in that case would **neither
   affect the system nor be visible to the client**, or when the client cannot
   realistically reach that state in normal use. Before recommending Skip, check
   whether the case is customer-visible. If it is (a public-facing field, layout
   or message), lean towards **Run**, and say in the Reason column that it is
   visible.
4. **The user decides.** Nothing is skipped, marked Not Applicable, moved to
   Manual, or left unscripted without the user's explicit yes on that list. The
   list is advisory. The user has the final call, and anything they mark Run is
   scripted and run. A case the user approves for Skip is recorded through
   `set-test-results` with the outcome the user chooses (Not Executed or Not
   Applicable), and the reason is stated.
5. **Mixed PBIs** (P1–P3, or P1–P4): finish the P1/P2 run, then present the list
   for the P3/P4 cases. The list never blocks or delays the P1/P2 cases.

## Rule 5 — Character-Limit Cases

The team agreed this rule on 2026-10-01. It decides the outcome of every
character-limit (max-length) case, on both CMS and Web fields.

1. **Rich-text fields → Not Applicable.** No character limit is applied to a
   rich-text field (an editor component, not a plain textarea). This holds even
   when the US states a max for that field. Every char-limit case on one is marked **Not Applicable**
   through `set-test-results`, never Failed, and no bug is filed.
2. **Plain field, implemented limit greater than the US limit:**
   - Test at the **implemented** maximum, not the US one, and check the UI
     wherever the value renders (CMS form and public page, EN and AR).
   - **UI intact:** the case **passes**. The team chose to keep the implemented
     limit.
   - **UI broken** (overflow, clipping, overlap, wrapping that breaks the
     layout, beyond Rule 1's tolerances): file a **UI bug for FE**, and mark the
     case **Failed** with that bug linked.
   - **FE can't fix it:** the bug is reassigned to **Alaa** to apply the
     original US limit. The reassignment is a bug update and needs the user's
     yes.
3. **Plain field, implemented limit shorter than the US limit:** file a bug on
   **Alaa** to raise it to the US limit. The case is **Failed**.

Rules 2 and 3 still apply. The implemented limit is read live from the field
(`maxlength` attribute, or the validation it actually enforces), never assumed
from the US. A bug is filed only after the user's yes, and the
same limit gap across several cases is one bug.

**Open, parked by the user on 2026-10-02.** Do not act on these until the user
decides:
- The user's item "any reported bug with #number 1 to be deleted". Nothing is
  deleted or closed under it.
- Whether old cases with the US limit in their expected result get edited.
- Who Alaa and the FE assignee are in Azure.
- When FE counts as "unable to fix".
