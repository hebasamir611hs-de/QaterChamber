# Qatar Chamber — automation repo

Playwright + pytest. Two surfaces, two top-level trees:

```
web/pages/<f>/<f>_page.py         web/tests/<f>/test_<f>_web.py           # public site
cms/pages/<f>/<f>_admin_page.py   cms/tests/<f>/test_<f>_control_panel.py # Liferay CMS
```

Target environment is **`qcdev.ihorizons.com` — shared, live, and not a sandbox.**

---

## Read before doing CMS work

- **`.claude/context/active/standards.md`** — the binding QA rules. Read it at the
  start of a session, before running anything.
- **`.claude/context/active/bug-rules.md`** — binding for every Phase-3 run, Web and
  CMS: Figma tolerance ±5 px images / ±2 px layout / text exact, one bug per root cause, confirm before calling a bug,
  P1/P2 first and a P3/P4 run/skip list for the user.
- **`PBI running rules.md`** (repo root) — the QA lead's standing decisions for running
  PBIs (scope, live-data writes, what is / is not a bug, Test Plan recording). Read it
  before any PBI run.
- `docs/qa-environment-notes.md` — qcdev quirks, shared-record table, login gate.
- `docs/qa-decisions-log.md` — why a rule exists; incidents; superseded rules.

`standards.md` holds rules only. If you find text in it saying "do not follow
this", that is a bug in the file — report it.

---

## CMS non-negotiables

These are the ones that get re-broken. They are enforced by
`cms/tests/test_cms_conventions.py`, which runs without a browser.

1. **Seven workflow states, and the account decides the path.** `Draft`,
   `Pending Review`, `Rejected`, `Published`, `Unpublished`, `Archived`,
   `Scheduled`. The old two-state Draft/Approved model was an artifact of only
   ever observing through the super-admin `TEST_USER` — that account skips the
   review step, so an outcome reached through it is not the system's behaviour.
   Always name the account a lifecycle case runs as.

2. **Vocabulary.** The control is **"Submit for Review"**, and the published
   badge reads **`PUBLISHED`**. Never write the old `"Submit for Publishing"` /
   `"Approved"` literals — use `object_authoring_page.py`'s `STATUS_*` and
   `SUBMIT_FOR_REVIEW_BUTTON` constants.

3. **Two independent visibility gates.** A record is public only when it is
   `Published` **and** its `Active Status` is ticked. `Active Status` defaults to
   **unticked** on a new entry, and the resulting failure looks exactly like a
   propagation bug. Check both before calling anything a defect.

4. **Object Authoring is the only content path** (`/object-authoring`). Content &
   Data is retired for Object-Definition-backed records. Documented exception:
   Home Contact Us is a Journal article (53012), not an object.

5. **Object names come from `cms/Content-Admin-Guide.docx`** — never guessed,
   never derived by probing `/object-authoring` or by copying a sibling's slug.

6. **Never touch fragments or page layout.** Automation operates on content
   records only. A missing page section is a finding to report, not a repair job.

7. **Roles resolve through `config.settings.cms_role_credentials("<Role>")`** —
   never a hard-coded email, and never `TEST_USER` for a permission-boundary case.

8. **Destructive work.** Never delete by position — resolve by ID or exact title.
   A precondition that would mutate real shared content must be built on a
   disposable `QCTEST-<tc_id>-*` record and torn down every run. Irreversible
   operations on shared data are never inferred from a general "fix and re-run";
   they need their own explicit go-ahead.

9. **Public-visibility checks use a fresh logged-out context**
   (`new_context(browser, use_auth_state=False)`) — never the CMS-authenticated
   `page`, which can render staff-only preview paths a visitor never sees.

---

## Running

```bash
pytest -m control_panel          # CMS surface        pytest -m web
pytest -m tc_135453              # one Azure case     pytest --lf / -x while fixing
```

- `addopts` carries `-n 3 --dist loadgroup`. **One agent at a time against
  qcdev** — concurrent live-browser sessions land on each other's navigations.
- While fixing a failure, run only the failing test(s). Reserve full-batch runs
  for confirmation.
- ⚠ `cms/tests/board_of_directors/` — 39 tests share one real Board Member record
  with no `xdist_group`. Run that module with `-n 0` until that is resolved.

## Generated files — do not hand-edit

| File | Owner |
|---|---|
| `pytest.ini`'s `pbi_`/`tc_` marker block | `tools/sync_tc_markers.py` (`--check` in CI) |
| `cms|web/tests/*/fixtures/` upload binaries | `tools/fixture_factory.py` (auto-run at session start) |

Add the mark in the test, then run the tool — never edit between the sentinels.
