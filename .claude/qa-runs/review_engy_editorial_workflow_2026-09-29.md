# Review — `qa/editorial-workflow-2026-09` (engy nassar, 2026-09-29)

Reviewed 2026-09-29 against `origin/main` @ `0c675f3`.
Branch head `6bc8f55`. **Not merged into main.**

## What landed today

Four commits, 10:12–10:13, **8,538 insertions across 23 files**:

| Commit | Subject |
|---|---|
| `8741f09` | Model the real 7-state editorial workflow, not the admin's view of it |
| `36b6efd` | Wire the eight named CMS role accounts, and fix the admin-only login check |
| `2652ed9` | Point standards.md citations at sections that actually exist |
| `6bc8f55` | Add Circulars and B2B Matchmaking web tests (PBIs 129408, 129409) |

## Verdict

**The content is good and worth taking — the branch's *state* is what blocks it.**
`8741f09` is a genuinely valuable correction: it establishes that the two-state
Draft/Approved model in our repo was an artifact of only ever observing through the
super-admin `TEST_USER`, and that the real machine is 7 states, gated by account
privilege. That is the right kind of finding, properly evidenced (one probe record walked
end to end as Author 156492 then Editor 156488, cross-checked on seven objects).

Two things must be fixed before merge. Neither is a criticism of today's work.

---

## Blocker 1 — the branch carries a `CMS/` vs `cms/` case conflict

The branch's git tree contains **both** spellings as separate top-level directories:

```
CMS/   14 files      cms/   116 files
```

Main has **only** `cms/`. None of the 14 `CMS/` paths has a `cms/` counterpart — they are
distinct files, not duplicates.

**Not introduced today.** They date from `e7666c1` (2026-08-31), `3843619` (2026-09-08)
and `3f73561` (2026-09-16), carried along the `qa/object-authoring-standards-unification`
lineage. Main never received them — previous merges from this lineage left them behind.

**Measured effect.** Checked the branch out into a clean worktree and collected:

| | tests collected | collection errors |
|---|---|---|
| `origin/main` | **2999** | **0** |
| this branch | **1263** | **29** |

All 29 are `ModuleNotFoundError: No module named 'cms'`. On Windows the two spellings
collapse into one directory (`CMS`), and Python's case-sensitive import check on Windows
then refuses `import cms`. Every module that imports a CMS Page Object from the `web/`
tree fails to collect.

**Fix:** merge main into the branch and drop the 14 `CMS/` paths, keeping `cms/`.

*(The 1263-vs-2999 gap is separate and expected — see Blocker 2.)*

## Blocker 2 — the branch is 11 commits behind main

Missing from the branch: the Media Centre and Expo automation (959 tests), the Sprint-2
Web automation for 5 PBIs (195 tests), the QA baselines for 7 PBIs, the tiered
field-coverage trial rule, and the qcdev dead-session detection fix. Merging as-is would
need a real merge, and `standards.md` is edited on **both** sides (+185 lines here, plus
the tiered-coverage section on main) — expect a conflict there and resolve it by hand.

---

## Finding — the login fix landed in the *minority* implementation

`36b6efd` correctly identifies that `nav[aria-label="Control Menu"]` is rendered only for
admin-level users, and that seven of the eight role accounts therefore signed in fine and
then timed out waiting for a toolbar they will never get. Engy's own measured table:

| role | signedIn | body.signed-in | Control Menu |
|---|---|---|---|
| Site Content Editor | True | True | True |
| Site Content Author | True | True | **FALSE** |
| Site Member (no role) | True | True | **FALSE** |

The fix — `LOGIN_SUCCESS_INDICATOR = "body.signed-in"`, with the toolbar check preserved
as `has_admin_toolbar()` — is the right call.

**But there are two live `CmsLoginPage` implementations, and only one was fixed:**

| file | success indicator | importers |
|---|---|---|
| `web/pages/components/cms_login_page.py` | `body.signed-in` ✅ fixed | **8** |
| `cms/pages/control_panel/login_page.py` | `nav[aria-label="Control Menu"], [data-qa-id="productMenu"]` ❌ unchanged | **26** |

The unfixed one is the **majority** implementation, and it is the one the entire `cms/`
tree routes through — including `cms/pages/home_social_icons/home_social_icons_admin_page.py`'s
`login_as_role()`, which is exactly the Control_Panel RBAC path the eight role accounts
were provisioned for. By the table above, those 26 modules will still time out for 7 of
the 8 accounts.

This is not stale-file cleanup: `cms/pages/control_panel/login_page.py` was last updated
2026-09-21 from main's own lineage, and both files exist on main too. The consolidation
that `dea62d5` claimed ("remove reintroduced control_panel/ tree") did not hold.

**Fix:** apply the same `body.signed-in` change to `cms/pages/control_panel/login_page.py`,
or make one file import the other so there is a single definition.

## Note — `.env` needs five new accounts

The branch adds 16 keys (8 roles) to `.env.example`. The local `.env` has 6 keys (3 roles):
Site Content Editor, Site Content Author, Content Contributor. The five new ones —
Form Manager, Event Organizer, SEO Manager, SEO Editor, Site Member — are **not set here**,
and `cms_role_credentials()` raises on an unset role. Anyone running those tests needs the
values from whoever provisioned the accounts on 2026-09-27.

---

## What this means for the 2026-09-28 retest

`8741f09` **already contains the heal I deliberately left undone yesterday.** Verified in
the branch's `cms/pages/components/object_authoring_page.py`:

```python
SUBMIT_FOR_REVIEW_BUTTON = 'button:has-text("Submit for Review")'
SUBMIT_FOR_PUBLISHING_BUTTON = SUBMIT_FOR_REVIEW_BUTTON   # deprecated alias
STATUS_PUBLISHED = "Published"
STATUS_APPROVED_LEGACY = STATUS_PUBLISHED
```

The alias means the ~181 broken call sites heal without being touched, and `tc_131180`
(which came back `broken` yesterday on exactly this locator) should run again once this
lands. **Follow-up 2 in `ready_bug_retest_2026-09-28.md` is retired by this branch.**

**Not covered by this branch:** the Social Media Icon form save failure
(`No value was provided for required object field "image"`, reproduced with both a 2.92 MB
and a valid 500 KB file). Follow-up 1 still stands on the manual check.

**The three bug verdicts are unaffected.** 141918's pre-submit validation, 142249's
server-side `400`, and 143511's toast absence are all independent of account privilege, so
the super-admin-artifact correction in `8741f09` does not touch them. Checked: none of the
three Azure bug comments repeats the now-withdrawn "no Pending Review status" claim.

## Worth following up separately

`8741f09` withdraws earlier findings of the form *"this build has no Pending Review
status"* as super-admin artifacts. At least one still lives in the tree as a written
justification — `test_footer_control_panel.py`'s
`test_site_content_author_can_access_but_cannot_publish_directly` cites it as
"confirmed live twice". Those comments should be corrected wherever they were used to
justify weakening an assertion.
