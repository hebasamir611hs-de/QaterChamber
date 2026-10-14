f = r"D:\MCP servers\QaterChamper\.claude\qa-runs\phase3_129368_2026-10-07_report.md"
s = open(f, encoding="utf-8").read()


def R(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b)


R("| 126 | 56 | 55 | 43 | 12 (11 failed, plus 135235 passed but its pass is unreliable) | 13 cases (see 5) | 49 Automation-tagged P3/P4 | 19 (3 are P2: 135183, 135227, 135268) |",
  "| 126 | 58 | 57 | 48 | 9 | 12 cases (see 5) | 47 Automation-tagged P3/P4 | 19 (3 are P2: 135183, 135227, 135268) |")
R("- P1/P2 Automation cases: 50 scripted, 4 missing. All 4 are NEEDS USER: 135131, 135228, 135247, 135248.",
  "- P1/P2 Automation cases: 52 scripted, 2 missing (135131, 135228; both NEEDS USER). 135247/135248 were scripted in the follow-up.\n"
  "- An earlier draft said 49 unscripted P3/P4; the inventory and the §6 table both give **47**, which is correct.")
R("- After that: one heal, then one targeted rerun of 33 nodeids.",
  "- After that: one heal, then one targeted rerun of 33 nodeids.\n"
  "- **Follow-up (reviewer, 2026-10-07):** fixes 1-3 below, then one rerun of only the 6 touched nodeids (`-rerun2`): **6/6 passed**.")
R("## 3. Results (final, after the one rerun)", "## 3. Results (final, after the rerun and the follow-up rerun2)")
R("| 135119 | Enable disabled slot | 2 | FAIL | NEEDS_INVESTIGATION | list badge reads `INACTIVE`, see 4 |",
  "| 135119 | Enable disabled slot | 2 | PASS (rerun2) | AUTOMATION_BUG (fixed) | the test's own Published precondition was removed; the TC has no workflow step. Now Save as Draft, toggle, stored value re-read |")
R("| 135120 | Disable active slot | 2 | PASS (rerun) | ENV in run 1 | |",
  "| 135120 | Disable active slot | 2 | PASS (rerun2) | ENV in run 1 | same function as 135119, re-run after the change |")
R("| 135186 | Deactivate keeps Published | 2 | FAIL | NEEDS_INVESTIGATION | `INACTIVE` badge, see 4 |",
  "| 135186 | Deactivate keeps Published | 2 | FAIL | NEEDS_INVESTIGATION | run 1 failed on its **precondition**: the Published + Active banner was not seen on the public page within 60 s (`test:396`). That is unexplained, most likely propagation lag under the concurrent load. The rerun got past that, then failed because the state after deactivating reads `Inactive`, not Published (`test:401`). See 4 |")
R("| 135232 | >2 MB / .gif refused (EN) | 2 | FAIL | INCONCLUSIVE, NEEDS USER | picker attaches an over-size file and Submit refuses it; .gif is refused at the picker (see 4) |",
  "| 135232 | >3 MB / .gif refused (EN) | 2 | PASS (rerun2) | AUTOMATION_BUG (fixed) | the assertion moved from the picker to Submit: size error shown, field empty, nothing persisted |")
R("| 135235 | >2 MB / .bmp refused (AR) | 2 | not counted as passed | INCONCLUSIVE, NEEDS USER | the pass came from a picker exception counted as \"rejected\". Manual check: same behaviour as 135232 |",
  "| 135235 | >3 MB / .bmp refused (AR) | 2 | PASS (rerun2) | re-scored | the run-1 pass came from a picker exception counted as \"rejected\" and was discarded. The new Submit-based check passes |")
R("| 135147 / 135244 | Valid redirect URL saved | 2 | PASS (rerun) | | |",
  "| 135147 / 135244 | Valid redirect URL saved | 2 | PASS (rerun) | | |\n"
  "| 135247 | Valid Redirect URL (AR) saved | 2 | PASS (rerun2) | scripted in follow-up | AR control `Redirect URL — العربية` (`bilingual=True`) |\n"
  "| 135248 | Invalid Redirect URL (AR) refused | 2 | PASS (rerun2) | scripted in follow-up | `htp:/broken` in AR: Submit refused, not Published |")
for a in ("| 135105 / 135106 | Section renders LTR / RTL | 2 | FAIL | PRODUCT_BUG | dots root cause |",
          "| 135132 | Multiple banners in one slider | 2 | FAIL | PRODUCT_BUG | dots root cause |",
          "| 135107 / 135108 | Next arrow / prev + dot | 3 | FAIL | PRODUCT_BUG | dots root cause (healed 135107 now fails on dots) |"):
    R(a, a.replace("PRODUCT_BUG | dots root cause", "INCONCLUSIVE | dots hidden on desktop by an explicit CSS rule (see 4)"))

A = s.index("- **CONFIRMED — pagination dots never visible (one root cause).**")
D = s.index("- **ENVIRONMENT — 135190.**")
dots = """- **INCONCLUSIVE (downgraded from CONFIRMED) — pagination dots hidden on desktop by design of the build.**
  - **The hiding rule** (read live, anonymous):
    - In the fragment CSS, `@media (min-width: 768px) { .qc-home-promotional-banners .qc-promo-dots { display: none !important; } }`.
    - Base rule: `.qc-promo-dots { display: none }`.
    - `@media (max-width: 767.98px) { .qc-promo-dots.qc-promo-dots--on { display: flex } }`.
    - The fragment JS sets `dotsBox.hidden = !multi` and toggles `qc-promo-dots--on` when `realCount > 1`.
  - **So the rule is count-based and viewport-based:**
    - dots on mobile (< 768 px) when there are 2+ banners;
    - always hidden at 768 px and wider, by an `!important` rule.
    - It is not a JS failure: there were no console errors, and the class `qc-promo-dots--on` is applied.
  - **Viewport check:**
    - At 375 px: `display: flex`, 3 dots visible (active pill).
    - At 1920 px: `display: none`, 3 dots in the DOM.
  - **Evidence:** `reports/manual-repro-129368-dots-section-375.png`, `reports/manual-repro-129368-dots-section-1920.png` (section screenshots that include the dots row); raw rules in `.claude/qa-runs/a129368/repro4.json`.
  - **Why INCONCLUSIVE:** desktop dots are deliberately switched off by the implementation, while TCs 135105 (step 3), 135106, 135107 (step 1), 135108 and 135132 ("3 pagination dots") expect them at desktop width. Whether the design wants dots on desktop needs the Figma desktop frame or a BA ruling (the Figma MCP did not connect). One root cause covers all five TCs.
- **Fixed in the follow-up (was INCONCLUSIVE) — image refusal, 135232/135235.**
  - Behaviour, reproduced manually and now asserted:
    - An over-size JPG is attached by the picker. Submit refuses it: `"… is 2.2 MB. Banner Image (EN) accepts files up to 2 MB … Nothing was saved"`. The field is empty and nothing persists.
    - GIF and BMP are refused at the picker.
  - That matches the TC end state ("rejected with a file-size error; field remains empty"); only the stage differs. Classified AUTOMATION_BUG: `check_file_refused` asserted the picker only. It is now replaced by `_image_refused_at_submit`, and a picker exception no longer counts as a refusal. Rerun2: both pass.
- **INCONCLUSIVE — the `Inactive` state (135130, 135257, 135186).**
  - Reproduced manually: an Editor submits a QCTEST banner with Active Status unticked.
  - The list status badge reads `INACTIVE`, and the edit form reads `Editing <title> (Inactive)`.
  - The product also treats the record as non-Published in two more places:
    - the staff **preview strip reads "this record is Draft. Visitors do not see it."**;
    - the **row offers no Unpublish action** (only History / Delete).
  - Ticking Active and resubmitting returns `Published` without any workflow action.
  - A logged-out `/home` doesn't show it (4 reads over 20 s), so the "not public" half of 135130/135257 holds. **Automation gap:** those two tests assert the status *before* visibility, so their "not public" half is currently covered only by this manual repro.
  - Evidence: `reports/manual-repro-129368-135186-inactive-list.png`, `-inactive-edit.png`.
  - 135119 is no longer in this group: its TC has no workflow step, it was fixed, and it passes.
"""
s = s[:A] + dots + s[D:]
R("  - On this object the form's submit button reads \"Submit for Publishing\" for both Editor and Author. That's wording only, and the workflow outcomes match the 7-state model: Author → Pending Review, Editor → Published, Unpublish → Unpublished.",
  "  - **Submit label.** Read live on `manage-promotional-banner`, the form buttons are `[\"Save as Draft\", \"Submit for Publishing\"]` for **both** Editor and Author (`reports/manual-repro-129368-submit-label-editor.png`, `-author.png`).\n"
  "    - The suite-wide `authoring_checks.check_author_submit_pending` asserts the label `\"Submit for Review\"` (`authoring_checks.py:446`), and `ObjectAuthoringPage.SUBMIT_FOR_REVIEW_BUTTON` matches only \"Submit for Review\" / \"Publish\". On this object both would miss.\n"
  "    - This module doesn't use that helper; it matches the button by structure (`name=status`, not the draft button).\n"
  "    - Wording only: the outcomes match the 7-state model (Author → Pending Review, Editor → Published, Unpublish → Unpublished). But the user should know the shared constant assumes the newer label.")
R("  - The arrow shape/opacity expectations in 135105/106 were not reached, because the test stops at the dots. They need Figma, and the Figma MCP failed to connect.",
  "  - The arrow shape/opacity expectations in 135105/106 were not reached, because the test stops at the dots. They need Figma, and the Figma MCP failed to connect.\n"
  "  - 135176 no longer has a skip, so any `-m pbi_129368` run will fail it until its precondition is approved.\n"
  "  - Run-1 environment breaks happened while other sessions' lock dirs (a10, b2) were present, i.e. concurrent browsers on qcdev. That is an orchestration issue.")
R("| 135247, 135248 | the live form has one **Redirect URL** field (`ObjectField_redirectUrl`); there is no AR control, while the PBI says \"Redirect URL (Per Lang.)\" and guide §16 says bilingual | QA Manager/BA ruling (requirement vs implementation) |\n", "")
R("| 135119, 135130, 135257, 135186 | Published + Active=false is shown as state \"Inactive\" (list + form), not Published | is \"Inactive\" intended? If yes, the tests accept Inactive as the inactive-Published state (visibility already verified) |",
  "| 135130, 135257, 135186 | Published + Active=false is shown as \"Inactive\" in the list badge and the edit form; the preview strip says \"this record is Draft\"; the row has no Unpublish. Re-ticking Active returns Published with no workflow action | is \"Inactive\" intended? If yes, the tests accept Inactive as the inactive-Published state and assert visibility first |")
R("| 135105, 135106 (arrow shape) | Figma oracle unavailable (Figma MCP did not connect) | reconnect Figma, or rule on the TC text |",
  "| 135105, 135106, 135107, 135108, 135132 | desktop dots are hidden by an explicit `@media (min-width:768px) … display:none !important` rule; the TCs expect them at desktop | Figma desktop frame or BA ruling. Arrow shape/opacity in 135105/106 also needs Figma |")
R("| 135232, 135235 | rejection happens at Submit, not at upload; TC-oracle and 3 MB tolerance rules conflict | ruling; then the check moves to the Submit refusal (next heal cycle) |\n", "")
R("- `reports/allure-results-phase3-129368-20261007-1840-rerun`",
  "- `reports/allure-results-phase3-129368-20261007-1840-rerun`\n"
  "- `reports/allure-results-phase3-129368-20261007-2010-rerun2` (follow-up: 135247, 135248, 135232, 135235, 135119, 135120 — 6/6 passed)")
open(f, "w", encoding="utf-8").write(s)
print("ok")
