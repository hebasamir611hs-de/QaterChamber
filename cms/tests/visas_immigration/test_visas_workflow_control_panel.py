"""
cms/tests/visas_immigration/test_visas_workflow_control_panel.py — Agent A.

Workflow / lifecycle / auth / ordering / inactive / audit cases of PBI 130701
"Visas & Immigration" (Azure suite 140362, plan 137724) on the Business
Gateway Object Authoring surface (`/web/qatar-chamber/manage-bg-*`) and the
public page `/web/qatar-chamber/visas-immigration`.

Data rules (user decisions, scratchpad bg_rules.md + ADDENDUM):
  - The REAL page record 109104 is touched only under
    scratchpad/locks/real_page_109104.lock, after a full snapshot
    (scratchpad/snapshots/109104_A_<ts>.json + screenshots), and restored +
    re-published + diffed in the fixture's finally. A failed restore or a
    remaining diff STOPS the session (pytest.exit).
  - Every other state change happens on Agent A's own QCTEST-130701-A-
    sections (pageKey visas-immigration, Display Order 500-599) and their
    QCTEST children; teardown deletes only captured ids (guarded delete).
    Real sections / items are never edited.
  - Public checks: fresh logged-out context; the stored Active Status is
    re-read first. Budget 5 s (cms-profile.md) measured from the save
    confirmation to the START of the page load that shows the change.

Substitutions disclosed (case wording -> what runs):
  - "Liferay generic success toast" -> the Object Authoring edit-bar message
    ("Saved and published." / "Draft saved.").
  - "audit log" -> the row History trail (the only per-record log offered to
    these roles); 140537 also probes the Control Panel audit log screen.
  - 140341/140343-140346/140348-140351: "Section 01/02/03/04" and the real
    items are replaced by Agent A's own QCTEST section(s) with the same
    shape (real sections/items may not be edited); 100-grid orders inside
    sections, 510/520 for the two reorder sections (band 500-599).
  - 140342/140347 "QCTEST-130701-… hero content" marker -> the real page's
    own hero (title/description) — only the workflow state is changed.
  - 140338 "QCTEST-130701 Draft Flow" is written into the real page's Eyebrow
    Label (a plain-text field that can be restored exactly).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from time import monotonic

import allure
import pytest

from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.visas_immigration.bg_admin_page import (
    MSG_DRAFT_SAVED,
    MSG_SAVED_AND_PUBLISHED,
    OPT_BLOCK_STYLE_PARAGRAPH,
    OPT_OPEN_NEW_TAB,
    QCTEST_PREFIXES,
    REAL_SECTIONS,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    SCRATCH_DIR,
    SLUG_CHECKLIST,
    SLUG_LINK,
    SLUG_PAGE,
    SLUG_SECTION,
    SLUG_SUBTOPIC,
    STATUS_INACTIVE,
    VISAS_PAGE_CODE,
    BGAdminPage,
    BGEntry,
    BGRealPageA,
    bg_data,
    real_page_lock,
)
from config.settings import PROJECT_ROOT, control_panel_url
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context
from web.pages.visas_immigration.visas_immigration_page import VisasImmigrationPage

pytestmark = [pytest.mark.control_panel, pytest.mark.pbi_130701, pytest.mark.xdist_group("visas_130701_a")]

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
STAMP = datetime.now().strftime("%m%d%H%M")
PREFIX = QCTEST_PREFIXES["A"]
EVIDENCE = os.path.join(str(PROJECT_ROOT), "reports", "evidence", "130701_A")
STOP_FILE = os.path.join(SCRATCH_DIR, "locks", "STOP_130701_A.txt")

PUBLIC_BUDGET_S = 5.0         # cms-profile.md budget, the cases' own 5 s
PUBLIC_DIAGNOSTIC_S = 45.0    # keeps polling after a breach to report the real latency
PUBLISH_CONFIRM_TIMEOUT = 120.0
REAL_TITLES = [v[2] for v in sorted(REAL_SECTIONS.values())]

EPIC = "Business Gateway"
FEATURE = "Visas & Immigration — Control Panel (workflow)"


def _name(tc: str, suffix: str = "") -> str:
    return f"{PREFIX}{tc}-{STAMP}" + (f" {suffix}" if suffix else "")


def _key(tc: str) -> str:
    return f"{PREFIX}{tc}-{STAMP}".lower()


# ===========================================================================
# Fixtures
# ===========================================================================
def _check_stop() -> None:
    if os.path.exists(STOP_FILE):
        pytest.exit(f"STOP file present ({STOP_FILE}) — a real-page restore failed earlier; nothing more runs")


def _login(page, role: str, slug: str = SLUG_SECTION) -> BGAdminPage:
    admin = BGAdminPage(page, slug, "A")
    outcome = admin.login_as_role(role)
    if outcome == "auth_failed":
        pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for '{role}'")
    admin.open_list_all()
    user_id, _ = admin.signed_in_user()
    if user_id != ROLE_USER_IDS[role]:
        pytest.fail(f"PRECONDITION: '{role}' signs in as userId {user_id!r}, not the pinned {ROLE_USER_IDS[role]}")
    return admin


class Registry:
    """Records THIS test created (captured identity). Only these are deleted."""

    def __init__(self):
        self.entries: list[BGEntry] = []

    def track(self, entry: BGEntry | None) -> BGEntry | None:
        if entry is not None:
            if not entry.in_namespace() or entry.prefix != PREFIX:
                raise ValueError(f"{entry} is not a {PREFIX} record")
            self.entries.append(entry)
        return entry


def _cleanup(browser, entries: list[BGEntry]) -> None:
    if not entries:
        return
    ctx = new_context(browser, use_auth_state=False)
    outcome, failures = [], []
    try:
        page = ctx.new_page()
        cleaner = BGAdminPage(page, SLUG_SECTION, "A")
        if cleaner.login_as_role(ROLE_EDITOR) == "auth_failed":
            raise AssertionError("cleanup login refused")
        for entry in reversed(entries):  # children before their section
            label = f"{entry.slug} {entry.entry_value!r} (id {entry.entry_id}, code {entry.code})"
            try:
                driver = cleaner.for_object(entry.slug)
                driver.open_list_all()
                if not driver.row_present(entry):
                    (outcome if driver.is_list_fully_expanded() else failures).append(f"not listed: {label}")
                    continue
                driver.adopt(entry)
                (outcome if driver.delete_disposable_entry(entry) else failures).append(
                    f"{'removed' if driver.row_present(entry) is False else 'NOT removed'} {label}")
            except Exception as exc:  # noqa: BLE001 — collected below
                failures.append(f"{label}: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(outcome + failures) or "nothing", name="QCTEST teardown")
    failures = [f for f in failures if not f.startswith("removed")]
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def own(browser):
    registry = Registry()
    yield registry
    _cleanup(browser, registry.entries)


@pytest.fixture
def anon_pages(browser):
    contexts = []

    def _make():
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return ctx.new_page()

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


@dataclass
class Base:
    section: BGEntry
    key: str
    title: str


@pytest.fixture(scope="module")
def base_section(browser):
    """ONE published QCTEST-130701-A- section (order 590) children attach to."""
    _check_stop()
    entries: list[BGEntry] = []
    ctx = new_context(browser, use_auth_state=False)
    try:
        admin = BGAdminPage(ctx.new_page(), SLUG_SECTION, "A")
        assert admin.login_as_role(ROLE_EDITOR) != "auth_failed"
        title, key = _name("base", "Base section"), _key("base")
        entry = admin.create_entry(bg_data(SLUG_SECTION, title, key, displayOrder=590))
        assert entry is not None, f"base section {title!r} could not be created/captured: {admin.refusal_evidence()}"
        entries.append(entry)
    finally:
        ctx.close()
    yield Base(section=entries[0], key=key, title=title)
    _cleanup(browser, entries)


@dataclass
class RealPage:
    admin: BGRealPageA
    before: dict
    public_before: dict
    snapshot: str
    notes: list = field(default_factory=list)


# The real page ends with the nested "Official sources" block (order 400);
# every QCTEST section (order >= 500, any language) renders after it.
LAST_REAL_HEADING = {"en": "Official sources", "ar": "المصادر الرسمية"}


def _real_headings(headings: list[str], locale: str) -> list[str]:
    last = LAST_REAL_HEADING[locale]
    return headings[: headings.index(last) + 1] if last in headings else headings


def _public_hero(view: VisasImmigrationPage, locale: str) -> dict:
    view.open_page(locale)
    model = view.model() or {}
    return {"hidden": model.get("hidden"), "eyebrow": model.get("eyebrow"), "title": model.get("title"),
            "description_html": model.get("description_html"),
            "hero_img": (model.get("hero_img") or "").split("?")[0],
            "headings": _real_headings(view.headings_in_order(), locale),
            "disclaimer": model.get("disclaimer")}


@pytest.fixture
def real_page(browser, anon_pages):
    """Lock + snapshot of 109104; restore + republish + diff in finally."""
    _check_stop()
    with real_page_lock("A") as lock:
        ctx = new_context(browser, use_auth_state=False)
        try:
            admin = BGRealPageA(ctx.new_page(), lock)
            if admin.login_as_role(ROLE_EDITOR) == "auth_failed":
                pytest.skip("PRECONDITION: Editor login refused")
            status = admin.real_status()
            admin.open_real_page()
            before = admin.read_page_record()
            admin.evidence(f"109104 snapshot form {STAMP}")
            public_before = {}
            for loc in ("en", "ar"):
                view = VisasImmigrationPage(anon_pages())

                def _rendered(view=view, loc=loc) -> bool:  # rides out a slow/failed fragment fetch
                    public_before[loc] = _public_hero(view, loc)
                    return not public_before[loc]["hidden"]

                try:
                    wait_until(_rendered, timeout=90.0, poll=3.0)
                except WaitTimeoutError:
                    pass
                view.a_evidence(EVIDENCE, f"109104 snapshot public {loc} {STAMP}")
            path = admin.write_snapshot(before, status, public_before)
            allure.attach(path, name="109104 snapshot file")
            if status != STATUS_PUBLISHED or public_before["en"]["hidden"] or public_before["ar"]["hidden"]:
                pytest.fail(f"PRECONDITION: real page 109104 is {status!r} / public hidden="
                            f"{public_before['en']['hidden']} before the test — nothing was changed")
            state = RealPage(admin=admin, before=before, public_before=public_before, snapshot=path)
            try:
                yield state
            finally:
                diffs = _restore_real_page(state, anon_pages)
                allure.attach("\n".join(diffs) or "restored: no differences", name="109104 restore diff")
                if diffs:
                    os.makedirs(os.path.dirname(STOP_FILE), exist_ok=True)
                    with open(STOP_FILE, "w", encoding="utf-8") as handle:
                        handle.write(f"snapshot {path}\n" + "\n".join(diffs))
                    pytest.exit(f"STOP: real page 109104 restore incomplete (snapshot {path}): {diffs}")
        finally:
            ctx.close()


def _restore_real_page(state: RealPage, anon_pages) -> list[str]:
    admin, before = state.admin, state.before
    try:
        admin.open_real_page()
        current = admin.read_page_record()
        for key in BGRealPageA.PLAIN_RESTORABLE:
            if current[key] != before[key]:
                admin.set_plain_field(key, before[key])
            if current[f"{key}_ar"] != before[f"{key}_ar"]:
                admin.set_plain_field(key, before[f"{key}_ar"], arabic=True)
        unrestorable = [d for d in admin.diff(before, current)
                        if d.split(":")[0] not in BGRealPageA.PLAIN_RESTORABLE
                        and d.split(":")[0] not in tuple(f"{k}_ar" for k in BGRealPageA.PLAIN_RESTORABLE)]
        if unrestorable:
            return ["NOT RESTORABLE BY AGENT A: " + d for d in unrestorable]
        changed = admin.diff(before, current) != []
        status = admin.real_status()
        if changed or status != STATUS_PUBLISHED:
            if not changed and "publish" in admin.real_row_actions():
                admin.real_row_action("publish")
            else:
                admin.open_real_page()
                for key in BGRealPageA.PLAIN_RESTORABLE:
                    admin.set_plain_field(key, before[key])
                    admin.set_plain_field(key, before[f"{key}_ar"], arabic=True)
                if not admin.publish_open_record():
                    return [f"republish did not go through: {admin.refusal_evidence()}"]
            status = admin.wait_real_status((STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT)
        diffs = [] if status == STATUS_PUBLISHED else [f"workflow status after restore: {status!r}"]
        admin.open_real_page()
        diffs += admin.diff(before, admin.read_page_record())
        for loc in ("en", "ar"):
            ok = {"v": None}

            def _same(loc=loc) -> bool:
                # Headings are cut after the real page's last block (_real_headings),
                # so other agents' live QCTEST sections in any language do not count.
                ok["v"] = _public_hero(VisasImmigrationPage(anon_pages()), loc)
                before_pub = state.public_before[loc]
                return ok["v"] == before_pub

            try:
                wait_until(_same, timeout=60.0, poll=2.0)
            except WaitTimeoutError:
                diffs.append(f"public {loc} differs: before={state.public_before[loc]!r} after={ok['v']!r}")
        return diffs
    except Exception as exc:  # noqa: BLE001 — any failure here is a STOP
        return [f"restore raised {exc!r}"]


# ===========================================================================
# Helpers
# ===========================================================================
def _create(admin: BGAdminPage, own: Registry, slug: str, data: dict, publish: bool = True) -> BGEntry:
    driver = admin if admin.slug == slug else admin.for_object(slug)
    driver.last_identify_matches = []
    entry = own.track(driver.create_entry(data, publish=publish))
    if entry is None and len(getattr(driver, "last_identify_matches", [])) > 1:
        dupes = driver.last_identify_matches
        for dupe in dupes:  # all are THIS save's own new records (id diff + exact read-back)
            own.track(driver.adopt(dupe))
        driver.evidence(f"duplicate records {dupes[0].entry_value}")
        pytest.fail(f"PRODUCT: ONE {'Publish' if publish else 'Save as Draft'} click created {len(dupes)} identical "
                    f"{slug} records {[d.entry_id for d in dupes]} for {data!r}")
    assert entry is not None, f"creating {data!r} did not go through / was not captured: {driver.refusal_evidence()}"
    return entry


def _require_active(admin: BGAdminPage, entry: BGEntry) -> None:
    driver = admin.for_object(entry.slug)
    driver.open_entry_en(entry.code)
    stored = driver.active_status_stored()
    allure.attach(f"{entry.entry_value}: stored Active Status {stored!r}", name="public precondition")
    assert stored == "true", f"PRECONDITION: {entry.entry_value!r} stores Active Status {stored!r}"


def _public(anon_pages, predicate, message: str, locale: str = "en", started: float | None = None):
    """Publish-then-poll in ONE fresh logged-out context. Passes when a page
    load that STARTED within PUBLIC_BUDGET_S of `started` shows the state;
    keeps polling (diagnostic) after a breach to report the real latency."""
    view = VisasImmigrationPage(anon_pages())
    started = monotonic() if started is None else started
    seen = {"latency": None, "model": None}

    def _check() -> bool:
        load_started = monotonic() - started
        view.open_page(locale)
        seen["model"] = view.model()
        if seen["model"] and predicate(seen["model"]):
            seen["latency"] = load_started
            return True
        return False

    try:
        wait_until(_check, timeout=PUBLIC_DIAGNOSTIC_S, poll=0.5, message=message)
    except WaitTimeoutError:
        view.a_evidence(EVIDENCE, f"public timeout {message}")
        pytest.fail(f"{message}: not seen within {PUBLIC_DIAGNOSTIC_S:.0f}s on the public page")
    allure.attach(f"{seen['latency']:.1f}s", name=f"public latency — {message}")
    assert seen["latency"] <= PUBLIC_BUDGET_S, (
        f"{message}: first seen on a load started {seen['latency']:.1f}s after the publish — "
        f"breaches the {PUBLIC_BUDGET_S:.0f}s budget")
    return view, seen["model"]


def _public_hold(anon_pages, predicate, message: str, locale: str = "en"):
    """Every load during the full 5 s window must satisfy `predicate`."""
    view = VisasImmigrationPage(anon_pages())
    started, loads = monotonic(), 0
    while True:
        view.open_page(locale)
        loads += 1
        model = view.model()
        if not (model and predicate(model)):
            view.a_evidence(EVIDENCE, f"public hold broken {message}")
            pytest.fail(f"{message}: violated on load {loads} after {monotonic() - started:.1f}s")
        if monotonic() - started >= PUBLIC_BUDGET_S:
            return view, model


def _row(model: dict, title: str) -> dict | None:
    return next((r for r in model["rows"] if r["title"] == title), None)


def _history(driver: BGAdminPage, entry: BGEntry) -> list[dict]:
    trail = driver.history(entry)
    allure.attach("\n".join(repr(h) for h in trail) or driver.history_cell_text(entry) or "(empty)",
                  name=f"History of {entry.entry_value}")
    return trail


def _banner(driver: BGAdminPage, expected: str) -> list[str]:
    texts = driver.success_messages(expected, timeout=15.0)
    allure.attach("\n".join(texts) or "(none)", name="edit-bar messages")
    return texts


def _has(texts: list[str], expected: str) -> bool:
    return any(expected in t for t in texts)


def _publish_edit(driver: BGAdminPage, entry: BGEntry, changes: dict) -> float:
    """Re-opens a captured record, applies `changes` (fill_data keys), Publish.
    Returns the monotonic time of the save confirmation."""
    driver.open_entry_en(entry.code)
    driver.fill_data(changes)
    driver.click_publish()
    assert driver.save_went_through(), f"publishing {entry.entry_value!r} did not go through: {driver.refusal_evidence()}"
    assert _has(_banner(driver, MSG_SAVED_AND_PUBLISHED), MSG_SAVED_AND_PUBLISHED)
    return monotonic()


def _real_page_status_shown(admin: BGRealPageA) -> str:
    admin.open_real_page()
    return admin.editing_bar_text()


def _soft(failures: list, ok: bool, message: str) -> None:
    if not ok:
        failures.append(message)


def _finish(failures: list) -> None:
    if failures:
        pytest.fail("\n".join(failures))


# ===========================================================================
# Auth
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.auth
@pytest.mark.tc_140327
@AUTH_FREE_PAGE
def test_140327_unauthenticated_edit_url_is_refused(page, anon_pages):
    """140327 — the Object Authoring edit URL of the real page is refused to a
    context with no auth state; nothing of the record leaks; nothing can be published."""
    admin = _login(page, ROLE_EDITOR, SLUG_PAGE)
    real = BGRealPageA(page)
    real.open_real_page()
    edit_url = page.url
    record = real.read_page_record()
    status_before = real.real_status()
    allure.attach(edit_url, name="captured edit URL")

    anon = VisasImmigrationPage(anon_pages())
    http = anon.open_raw(edit_url)
    body = anon.document_text()
    landed = anon.current_url()
    signed_in = anon.is_signed_in()
    anon.a_evidence(EVIDENCE, "140327 anonymous edit URL")
    leaks = [v for v in (record["heroDescription_html"][3:60], REAL_SECTIONS["arrivals"][2],
                         "Confirm current visa, immigration and departure requirements.", record["pageTitle_ar"])
             if v and v in body]
    publish_controls = anon.button_count("Publish")
    assert not signed_in, "the probe context is signed in — the check is void"
    allure.attach(f"HTTP {http}\nlanded on {landed}\nleaks {leaks}\npublish buttons {publish_controls}\n\n{body[:1500]}",
                  name="anonymous response")
    failures: list[str] = []
    _soft(failures, not leaks, f"record values leaked to the anonymous response: {leaks}")
    _soft(failures, publish_controls == 0, "a Publish control is offered to the anonymous context")
    admin.open_list_all()
    _soft(failures, real.real_status() == status_before, f"status changed to {real.real_status()!r}")
    signed_in_redirect = "/c/portal/login" in landed or "LoginPortlet" in landed
    _soft(failures, signed_in_redirect,
          f"PRODUCT vs CASE: the request is refused with HTTP {http} at {landed} — it does NOT redirect to the "
          f"Liferay sign-in page (case step 3)")
    _finish(failures)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.auth
@pytest.mark.tc_140328
@AUTH_FREE_PAGE
def test_140328_author_view_and_update_content(page, own, base_section):
    """140328 — the Author opens the Visas page record (read + update expected)
    and updates a Block Body (substituted: the Author's own QCTEST block)."""
    author = _login(page, ROLE_AUTHOR, SLUG_PAGE)
    real = BGRealPageA(page)
    real.open_real_page()
    bar = " ".join(real.editbar_texts())
    buttons = real.form_buttons()
    real.evidence("140328 author opens real page")
    allure.attach(f"edit bar: {bar}\nbuttons: {buttons}", name="Author on the real page")
    failures: list[str] = []
    _soft(failures, "Access denied" not in bar,
          f"PRODUCT vs CASE (step 2): the Author cannot update the Visas & Immigration record — {bar!r}")
    _soft(failures, False,
          "PRODUCT vs CASE (step 2): the page record does not list its four sections (sections are separate "
          "BG Info Section records joined by pageKey)")

    blocks = author.for_object(SLUG_SUBTOPIC)
    heading = _name("140328", "E-gate block")
    entry = _create(blocks, own, SLUG_SUBTOPIC, bg_data(SLUG_SUBTOPIC, heading, base_section.key), publish=False)
    new_body = "QCTEST-130701 updated e-gate guidance for automated verification"
    blocks.open_entry_en(entry.code)
    blocks.fill_rich("blockBody", new_body)
    blocks.click_save_as_draft()
    _soft(failures, blocks.save_went_through(), f"the Author's save did not go through: {blocks.refusal_evidence()}")
    _soft(failures, _has(_banner(blocks, MSG_DRAFT_SAVED), MSG_DRAFT_SAVED), "no 'Draft saved.' message")
    blocks.open_entry_en(entry.code)
    blocks.wait_for_rich_text_loaded()
    _soft(failures, blocks.rich_text("blockBody") == new_body,
          f"Block Body after re-open reads {blocks.rich_text('blockBody')!r}")
    blocks.open_list_all()
    trail = _history(blocks, entry)
    _soft(failures, any("Test Author" in h["text"] for h in trail),
          f"History holds no entry by Test Author: {trail or blocks.history_cell_text(entry)!r}")
    _finish(failures)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.auth
@pytest.mark.workflow
@pytest.mark.web
@pytest.mark.tc_140329
@AUTH_FREE_PAGE
def test_140329_author_cannot_publish(page, own, base_section, anon_pages):
    """140329 — an Author's Draft record (QCTEST block in Agent A's published
    section) offers no Publish transition and never reaches the public page."""
    author = _login(page, ROLE_AUTHOR, SLUG_SUBTOPIC)
    heading = _name("140329", "Author draft block")
    entry = _create(author, own, SLUG_SUBTOPIC, bg_data(SLUG_SUBTOPIC, heading, base_section.key), publish=False)
    author.open_list_all()
    assert author.row_status_of(entry) == STATUS_DRAFT, f"status {author.row_status_of(entry)!r}, not Draft"
    author.open_entry_en(entry.code)
    buttons = author.form_buttons()
    actions = (author.open_list_all() and None) or author.row_actions(entry)
    author.evidence("140329 author draft form")
    allure.attach(f"form buttons {buttons}\nrow actions {actions}", name="Author controls")
    assert "Publish" not in buttons, f"the Author is offered a Publish button: {buttons}"
    assert "publish" not in actions, f"the Author's row offers Publish: {actions}"
    assert author.row_status_of(entry) == STATUS_DRAFT
    trail = _history(author, entry)
    assert not any("publish" in h["action"].casefold() and "Test Author" in h["text"] for h in trail), trail
    view, model = _public_hold(anon_pages, lambda m: heading not in str(m),
                               f"{heading} must stay off the public page")
    assert view.http_status() == 200


# ===========================================================================
# Real page lifecycle (lock + snapshot + restore)
# ===========================================================================
def _unpublish_real(real: RealPage) -> str:
    dialogs = real.admin.unpublish_real_page()
    allure.attach("\n".join(dialogs) or "(no dialog)", name="Unpublish dialogs")
    status = real.admin.wait_real_status((STATUS_DRAFT, STATUS_UNPUBLISHED), timeout=PUBLISH_CONFIRM_TIMEOUT)
    real.admin.evidence("109104 after unpublish")
    return status


def _publish_real(real: RealPage) -> tuple[list[str], float]:
    """Publish lifecycle action: the row's Publish action when offered (no form
    re-submission of the real record), else the form's Publish button."""
    admin = real.admin
    if "publish" in admin.real_row_actions():
        dialogs = admin.real_row_action("publish")
        confirmed = monotonic()
        texts = dialogs + admin.editbar_texts() + [admin.rendered_body_text()[:600]]
        allure.attach(chr(10).join(texts), name="row Publish dialogs / messages")
        return texts, confirmed
    admin.open_real_page()
    assert admin.publish_open_record(), f"Publish did not go through: {admin.refusal_evidence()}"
    confirmed = monotonic()
    texts = _banner(admin, MSG_SAVED_AND_PUBLISHED)
    return texts, confirmed


def _history_real(real: RealPage) -> list[dict]:
    admin = real.admin
    entry = BGEntry(SLUG_PAGE, "Visas & Immigration", "109104", VISAS_PAGE_CODE, PREFIX)
    admin.open_list_all()
    trail = admin.history(entry)
    allure.attach("\n".join(repr(h) for h in trail) or admin.history_cell_text(entry) or "(empty)",
                  name="History of 109104")
    return trail


# History action labels observed live 2026-10-06: "Created" (first save, as
# draft), "Approved" (Publish by an Editor), "Unpublished".
HISTORY_LABELS = {"draft": ("Created", "edit-as-draft", "Edited", "Saved as draft", "Draft saved", "Draft"),
                  "publish": ("Approved", "Published"),
                  "unpublish": ("Unpublished",)}


def _has_action(trail: list[dict], kind: str, who: str = "Test Editor") -> bool:
    labels = HISTORY_LABELS[kind]
    return any(h["action"].strip() in labels and who in (h["who"] or h["text"]) and h["when"] for h in trail)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.auth
@pytest.mark.workflow
@pytest.mark.web
@pytest.mark.tc_140326
def test_140326_editor_draft_to_published(real_page, anon_pages):
    """140326 — Editor: Draft -> Published on the real page, History, public within 5 s."""
    failures: list[str] = []
    status = _unpublish_real(real_page)
    allure.attach(status, name="status after the precondition unpublish")
    _soft(failures, status == STATUS_DRAFT, f"the unpublished record reads {status!r}, not Draft")
    texts, confirmed = _publish_real(real_page)
    _soft(failures, _has(texts, MSG_SAVED_AND_PUBLISHED), f"no '{MSG_SAVED_AND_PUBLISHED}' message: {texts}")
    status = real_page.admin.wait_real_status((STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT)
    _soft(failures, status == STATUS_PUBLISHED, f"status after Publish {status!r}")
    trail = _history_real(real_page)
    _soft(failures, _has_action(trail, "publish"), f"History has no publish entry by Test Editor with a time: {trail}")
    view, model = _public(anon_pages, lambda m: not m["hidden"] and m["title"] == real_page.public_before["en"]["title"],
                          "the real page renders again", started=confirmed)
    _soft(failures, view.http_status() == 200, f"HTTP {view.http_status()}")
    _finish(failures)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.workflow
@pytest.mark.web
@pytest.mark.tc_140340
def test_140340_publish_shows_active_sections_in_order(real_page, anon_pages):
    """140340 — publishing the page renders hero + the four real sections in configured order."""
    failures: list[str] = []
    status = _unpublish_real(real_page)
    _soft(failures, status == STATUS_DRAFT, f"the unpublished record reads {status!r}, not Draft")
    texts, confirmed = _publish_real(real_page)
    _soft(failures, _has(texts, MSG_SAVED_AND_PUBLISHED), f"no '{MSG_SAVED_AND_PUBLISHED}' message: {texts}")
    status = real_page.admin.wait_real_status((STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT)
    _soft(failures, status == STATUS_PUBLISHED, f"status after Publish {status!r}")
    _soft(failures, _has_action(_history_real(real_page), "publish"), "History has no publish entry by Test Editor")
    view, model = _public(anon_pages, lambda m: not m["hidden"] and bool(m["title"]), "hero renders", started=confirmed)
    _soft(failures, view.http_status() == 200, f"HTTP {view.http_status()}")
    order = [h for h in view.headings_in_order() if h in REAL_TITLES]
    allure.attach(repr(view.headings_in_order()), name="headings in document order")
    _soft(failures, order == REAL_TITLES, f"real section order {order}, expected {REAL_TITLES}")
    _finish(failures)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.web
@pytest.mark.tc_140338
@AUTH_FREE_PAGE
def test_140338_save_as_draft_keeps_content_off_public(page, own, anon_pages):
    """140338 — (user decision 2026-10-06: status = workflow; drafts are the
    Author's) the Author saves Agent A's own QCTEST section as Draft: Draft in
    the Author's list + record, History records it, never reaches visitors."""
    author = _login(page, ROLE_AUTHOR)
    marker = "QCTEST-130701 Draft Flow"
    title = _name("140338", "Draft Flow")
    entry = _create(author, own, SLUG_SECTION, bg_data(SLUG_SECTION, title, _key("140338"), displayOrder=510,
                                                       sectionBody=marker), publish=False)
    failures: list[str] = []
    messages = getattr(author, "last_create_messages", [])
    allure.attach(" | ".join(messages) or "(none)", name="edit-bar after Save as Draft")
    _soft(failures, _has(messages, MSG_DRAFT_SAVED), f"no 'Draft saved.' message after the save: {messages}")
    author.open_list_all()
    _soft(failures, author.row_status_of(entry) == STATUS_DRAFT, f"Author's list shows {author.row_status_of(entry)!r}")
    author.open_entry_en(entry.code)
    author.wait_for_rich_text_loaded()
    bar = author.editing_bar_text()
    author.evidence("140338 author draft record")
    _soft(failures, "(Draft)" in bar or "draft" in bar.casefold(), f"record edit bar: {bar!r}")
    _soft(failures, author.rich_text("sectionBody") == marker, f"stored body {author.rich_text('sectionBody')!r}")
    author.open_list_all()
    trail = _history(author, entry)
    _soft(failures, _has_action(trail, "draft", who="Test Author"), f"History has no draft save by Test Author: {trail}")
    _public_hold(anon_pages, lambda m: marker not in str(m) and title not in str(m),
                 f"'{marker}' never reaches visitors")
    _finish(failures)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.workflow
@pytest.mark.web
@pytest.mark.tc_140342
def test_140342_unpublish_removes_page_from_public(real_page, anon_pages):
    """140342 — Unpublish takes the real page's content off the public site within 5 s."""
    failures: list[str] = []
    title = real_page.public_before["en"]["title"]
    _soft(failures, title == "Visas & Immigration", f"public hero before: {title!r}")
    admin = real_page.admin
    admin.open_real_page()
    _soft(failures, "(Published)" in admin.editing_bar_text(), f"edit bar: {admin.editing_bar_text()!r}")
    status = _unpublish_real(real_page)
    confirmed = monotonic()
    _soft(failures, status == STATUS_UNPUBLISHED, f"status after Unpublish {status!r} (case: Unpublished)")
    _soft(failures, _has_action(_history_real(real_page), "unpublish"), "History has no unpublish entry by Test Editor")
    _public(anon_pages, lambda m: m["hidden"] or title not in (m["title"] or ""), "hero content is gone",
            started=confirmed)
    _finish(failures)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.web
@pytest.mark.tc_140347
def test_140347_unpublished_page_not_served_stale(real_page, anon_pages):
    """140347 — after Unpublish the URL stops serving the content (not-found
    page expected) and the navigation no longer reaches it."""
    failures: list[str] = []
    description = real_page.public_before["en"]["description_html"]
    status = _unpublish_real(real_page)
    confirmed = monotonic()
    _soft(failures, status == STATUS_UNPUBLISHED, f"status after Unpublish {status!r} (case: Unpublished)")
    view, model = _public(anon_pages, lambda m: m["hidden"], "fragment stops rendering the record", started=confirmed)
    view.a_evidence(EVIDENCE, "140347 public after unpublish")
    body = view.document_text()
    leaked = [v for v in (real_page.public_before["en"]["title"], REAL_SECTIONS["arrivals"][2],
                          "Ministry of Interior") if v in view.body_text()]
    http = view.http_status()
    nav = view.links_to_page()
    allure.attach(f"HTTP {http}\nleaked in fragment {leaked}\nnav links {nav}\n\n{body[:1500]}", name="after unpublish")
    _soft(failures, not leaked and bool(description), f"record values still rendered: {leaked}")
    _soft(failures, http == 404, f"PRODUCT vs CASE (step 4): the URL answers HTTP {http} with the site shell, "
                                 f"not the standard not-found page")
    _soft(failures, not nav, f"PRODUCT vs CASE (step 5): the navigation still links to the page: {nav}")
    _finish(failures)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.web
@pytest.mark.tc_140339
@AUTH_FREE_PAGE
def test_140339_preview_unpublished_changes(page, own, anon_pages):
    """140339 — (user decision 2026-10-06) the Author's unpublished QCTEST
    section renders in Preview while the public page stays unchanged."""
    before = VisasImmigrationPage(anon_pages())
    before.open_page("en")
    hero_before = {k: before.model()[k] for k in ("title", "description_html")}
    author = _login(page, ROLE_AUTHOR)
    body = "QCTEST-130701 preview-only hero body"
    title = _name("140339", "Preview")
    entry = _create(author, own, SLUG_SECTION, bg_data(SLUG_SECTION, title, _key("140339"), displayOrder=520,
                                                       sectionBody=body), publish=False)
    author.open_list_all()
    assert author.row_status_of(entry) == STATUS_DRAFT
    preview = author.open_preview(author.preview_url(entry.entry_id), [title, body])
    author.evidence("140339 author preview")
    assert body in preview and title in preview, "the Preview does not render the Author's draft"
    view, model = _public_hold(anon_pages, lambda m: body not in str(m) and title not in str(m),
                               "the draft stays off the public page")
    assert {k: model[k] for k in ("title", "description_html")} == hero_before, "the public hero changed"


# ===========================================================================
# QCTEST sections (band 500-599) — publish / edit / order / inactive / audit
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.web
@pytest.mark.tc_140341
@AUTH_FREE_PAGE
def test_140341_republish_delivers_new_value(page, own, anon_pages):
    """140341 — re-publishing an edited section body delivers v2 within 5 s, not v1."""
    admin = _login(page, ROLE_EDITOR)
    title, v1, v2 = _name("140341", "Section"), "QCTEST-130701 body version one", "QCTEST-130701 body version two"
    entry = _create(admin, own, SLUG_SECTION, bg_data(SLUG_SECTION, title, _key("140341"), displayOrder=570,
                                                      sectionBody=v1))
    _require_active(admin, entry)
    _public(anon_pages, lambda m: (_row(m, title) or {}).get("body") == v1, "v1 is live")
    confirmed = _publish_edit(admin, entry, {"sectionBody": v2})
    admin.open_list_all()
    assert admin.row_status_of(entry) == STATUS_PUBLISHED
    view, model = _public(anon_pages, lambda m: (_row(m, title) or {}).get("body") == v2, "v2 is live",
                          started=confirmed)
    assert v1 not in view.body_text(), "the previous body v1 is still in the response"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.tc_140343
@AUTH_FREE_PAGE
def test_140343_new_subtopic_block_rendered(page, own, base_section, anon_pages):
    """140343 — a newly added sub-topic block renders last, styled, with its paragraph."""
    admin = _login(page, ROLE_EDITOR, SLUG_SUBTOPIC)
    for i in (1, 2):
        _create(admin, own, SLUG_SUBTOPIC, bg_data(SLUG_SUBTOPIC, _name("140343", f"Block {i}"), base_section.key,
                                                   displayOrder=i * 100))
    heading = _name("140343", "Transit passengers")
    body = "QCTEST-130701 transit passengers paragraph."
    entry = _create(admin, own, SLUG_SUBTOPIC, bg_data(SLUG_SUBTOPIC, heading, base_section.key, displayOrder=300,
                                                       blockBody=body, blockStyle=OPT_BLOCK_STYLE_PARAGRAPH))
    confirmed = monotonic()
    _require_active(admin, entry)
    view, model = _public(anon_pages, lambda m: heading in [b["heading"] for b in (_row(m, base_section.title) or
                                                                                   {"blocks": []})["blocks"]],
                          "new block renders", started=confirmed)
    blocks = _row(model, base_section.title)["blocks"]
    assert [b["heading"] for b in blocks][-1] == heading and len(blocks) == 3, [b["heading"] for b in blocks]
    assert blocks[-1]["style"] == "paragraph" and blocks[-1]["prose"] == body, blocks[-1]
    style = view.block_heading_style(heading)
    allure.attach(repr(style), name="block heading computed style")
    assert "Cairo" in style["fontFamily"] and style["fontSize"] == "18px" and style["fontWeight"] == "700" \
        and style["color"] == "rgb(29, 29, 27)", f"heading style {style} (expected Cairo 18px 700 #1D1D1B)"


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_high
@pytest.mark.web
@pytest.mark.tc_140344
@AUTH_FREE_PAGE
def test_140344_edit_source_link_publishes_new_values(page, own, base_section, anon_pages):
    """140344 — editing an official-source link's description publishes it (styled)."""
    admin = _login(page, ROLE_EDITOR, SLUG_LINK)
    title = _name("140344", "Ministry of Interior")
    old = "Confirm current visa, immigration and departure requirements."
    new = "QCTEST-130701 confirm the latest entry and exit rules before travelling."
    entry = _create(admin, own, SLUG_LINK, bg_data(SLUG_LINK, title, base_section.key, linkDescription=old))
    _require_active(admin, entry)
    _public(anon_pages, lambda m: any(lk["title"] == title and lk["desc"] == old
                                      for lk in (_row(m, base_section.title) or {"links": []})["links"]), "link live")
    admin.open_entry_en(entry.code)
    assert admin.text_value("linkTitle") == title, "the link item is not resolved by its exact title"
    confirmed = _publish_edit(admin, entry, {"linkDescription": new})
    view, model = _public(anon_pages, lambda m: any(lk["title"] == title and lk["desc"] == new
                                                    for lk in (_row(m, base_section.title) or {"links": []})["links"]),
                          "new description live", started=confirmed)
    t_style, d_style = view.source_title_style(title), view.source_desc_style(new)
    allure.attach(f"title {t_style}\ndesc {d_style}", name="link computed styles")
    failures: list[str] = []
    _soft(failures, "Cairo" in t_style["fontFamily"] and t_style["fontSize"] == "14px"
          and t_style["fontWeight"] == "700" and t_style["color"] == "rgb(145, 23, 49)",
          f"title style {t_style} (expected Cairo 14px 700 #911731)")
    _soft(failures, "Cairo" in d_style["fontFamily"] and d_style["fontSize"] == "14px"
          and d_style["fontWeight"] == "400" and d_style["color"] == "rgb(108, 108, 107)",
          f"description style {d_style} (expected Cairo 14px 400 #6C6C6B)")
    _finish(failures)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_high
@pytest.mark.web
@pytest.mark.tc_140345
@AUTH_FREE_PAGE
def test_140345_delete_checklist_item_removes_it(page, own, base_section, anon_pages):
    """140345 — deleting one checklist item (resolved by exact text) leaves the other three."""
    admin = _login(page, ROLE_EDITOR, SLUG_CHECKLIST)
    texts = [f"QCTEST-130701 checklist keep {i}" for i in (1, 2, 3)] + ["QCTEST-130701 disposable checklist item"]
    entries = [_create(admin, own, SLUG_CHECKLIST, bg_data(SLUG_CHECKLIST, base_section.key, itemText=t,
                                                           displayOrder=(i + 1) * 100))
               for i, t in enumerate(texts)]
    _public(anon_pages, lambda m: (_row(m, base_section.title) or {}).get("checklist") == texts, "four items live")
    target = None
    for entry in entries:
        admin.open_entry_en(entry.code)
        if admin.rich_text("itemText") == texts[-1]:
            assert target is None, "two checklist items carry the disposable text"
            target = entry
    assert target is entries[-1], "the disposable item was not resolved by its exact text"
    admin.open_list_all()
    admin.adopt(target)
    assert admin.delete_disposable_entry(target), "guarded delete of the disposable item refused/failed"
    own.entries.remove(target)
    confirmed = monotonic()
    view, model = _public(anon_pages, lambda m: (_row(m, base_section.title) or {}).get("checklist") == texts[:3],
                          "three items remain", started=confirmed)
    assert texts[-1] not in view.body_text()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.tc_140346
@AUTH_FREE_PAGE
def test_140346_reorder_blocks_changes_public_order(page, own, base_section, anon_pages):
    """140346 — changing block Display Orders re-orders them on the public page."""
    admin = _login(page, ROLE_EDITOR, SLUG_SUBTOPIC)
    names = {k: _name("140346", k) for k in ("Exit permits", "Clearing passport control", "Priority processing")}
    created = {k: _create(admin, own, SLUG_SUBTOPIC, bg_data(SLUG_SUBTOPIC, names[k], base_section.key,
                                                            displayOrder=(i + 1) * 100))
               for i, k in enumerate(names)}

    def _order(m):
        return [b["heading"] for b in (_row(m, base_section.title) or {"blocks": []})["blocks"]]

    _public(anon_pages, lambda m: _order(m) == list(names.values()), "initial order")
    _publish_edit(admin, created["Priority processing"], {"displayOrder": 100})
    confirmed = _publish_edit(admin, created["Exit permits"], {"displayOrder": 300})
    expected = [names["Priority processing"], names["Clearing passport control"], names["Exit permits"]]
    _public(anon_pages, lambda m: _order(m) == expected, "new order", started=confirmed)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_high
@pytest.mark.web
@pytest.mark.tc_140348
@AUTH_FREE_PAGE
def test_140348_section_display_order_applied(page, own, anon_pages):
    """140348 — the real sections render in configured order (read-only) and a
    Display Order change re-orders sections (two QCTEST sections 510/520 swapped)."""
    view = VisasImmigrationPage(anon_pages())
    view.open_page("en")
    real_order = [h for h in view.headings_in_order() if h in REAL_TITLES]
    assert real_order == REAL_TITLES, f"real section order {real_order}"
    admin = _login(page, ROLE_EDITOR)
    first, second = _name("140348", "Section X"), _name("140348", "Section Y")
    s1 = _create(admin, own, SLUG_SECTION, bg_data(SLUG_SECTION, first, _key("140348x"), displayOrder=510))
    s2 = _create(admin, own, SLUG_SECTION, bg_data(SLUG_SECTION, second, _key("140348y"), displayOrder=520))

    def _qc(m):
        return [r["title"] for r in m["rows"] if r["title"] in (first, second)]

    _public(anon_pages, lambda m: _qc(m) == [first, second], "X before Y")
    _publish_edit(admin, s1, {"displayOrder": 520})
    confirmed = _publish_edit(admin, s2, {"displayOrder": 510})
    view, model = _public(anon_pages, lambda m: _qc(m) == [second, first], "Y before X", started=confirmed)
    assert [h for h in view.headings_in_order() if h in REAL_TITLES] == REAL_TITLES


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.web
@pytest.mark.tc_140349
@AUTH_FREE_PAGE
def test_140349_preview_and_published_agree(page, own, anon_pages, browser):
    """140349 — (user decision 2026-10-06) Author draft card heading -> Preview
    renders it, public does not; Editor publishes -> public == preview."""
    author = _login(page, ROLE_AUTHOR)
    title = _name("140349", "Departures")
    heading = "QCTEST-130701 keep your documents ready before passport control."
    entry = _create(author, own, SLUG_SECTION, bg_data(SLUG_SECTION, title, _key("140349"), displayOrder=560,
                                                       highlightCardEyebrow="Before departure",
                                                       highlightCardHeading=heading), publish=False)
    preview = author.open_preview(author.preview_url(entry.entry_id), [heading])
    author.evidence("140349 author preview")
    assert heading in preview, "the Preview does not render the draft card heading"
    _public_hold(anon_pages, lambda m: heading not in str(m), "the draft heading stays off the public page")
    ctx = new_context(browser, use_auth_state=False)
    try:
        editor = _login(ctx.new_page(), ROLE_EDITOR)
        editor.adopt(entry)
        editor.open_list_all()
        assert editor.row_status_of(entry) == STATUS_DRAFT
        confirmed = _publish_edit(editor, entry, {})
        assert editor.wait_row_status(entry, (STATUS_PUBLISHED,)) == STATUS_PUBLISHED
        _require_active(editor, entry)
        view, model = _public(anon_pages, lambda m: ((_row(m, title) or {}).get("card") or {}).get("heading") == heading,
                              "public card heading == preview heading", started=confirmed)
        preview_after = editor.open_preview(editor.preview_url(entry.entry_id), [heading])
        assert heading in preview_after, "preview and published content diverge after publishing"
    finally:
        ctx.close()


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.edge
@pytest.mark.web
@pytest.mark.tc_140350
@AUTH_FREE_PAGE
def test_140350_inactive_section_stops_rendering(page, own, anon_pages):
    """140350 — a section set Inactive (with its block and card) disappears; the real sections stay."""
    admin = _login(page, ROLE_EDITOR)
    title, key = _name("140350", "Departing section"), _key("140350")
    card = "QCTEST-130701 Before departure card"
    section = _create(admin, own, SLUG_SECTION, bg_data(SLUG_SECTION, title, key, displayOrder=530,
                                                        highlightCardEyebrow="Before departure",
                                                        highlightCardHeading=card))
    block = _name("140350", "Exit permits")
    _create(admin, own, SLUG_SUBTOPIC, bg_data(SLUG_SUBTOPIC, block, key))
    _require_active(admin, section)
    _public(anon_pages, lambda m: bool(_row(m, title)) and block in str(m) and card in str(m), "section live")
    confirmed = _publish_edit(admin, section, {"activeStatus": False})
    admin.open_entry_en(section.code)
    assert admin.active_status_stored() == "false", "Active Status was not stored as unticked"
    admin.open_list_all()
    allure.attach(admin.row_status_of(section), name="row status after deactivation")
    view, model = _public(anon_pages, lambda m: not _row(m, title), "section gone", started=confirmed)
    body = view.body_text()
    assert title not in body and block not in body and card not in body
    assert [h for h in view.headings_in_order() if h in REAL_TITLES] == REAL_TITLES


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.edge
@pytest.mark.web
@pytest.mark.tc_140351
@AUTH_FREE_PAGE
def test_140351_inactive_item_stops_rendering(page, own, base_section, anon_pages):
    """140351 — one of two link items set Inactive disappears; its sibling remains."""
    admin = _login(page, ROLE_EDITOR, SLUG_LINK)
    keep, drop = _name("140351", "Ministry of Interior"), _name("140351", "Hamad International Airport")
    drop_desc = "QCTEST-130701 Review current airport, arrival and departure guidance."
    _create(admin, own, SLUG_LINK, bg_data(SLUG_LINK, keep, base_section.key, displayOrder=100))
    target = _create(admin, own, SLUG_LINK, bg_data(SLUG_LINK, drop, base_section.key, displayOrder=200,
                                                    linkDescription=drop_desc, openBehavior=OPT_OPEN_NEW_TAB))

    def _titles(m):
        return [lk["title"] for lk in (_row(m, base_section.title) or {"links": []})["links"]]

    _public(anon_pages, lambda m: _titles(m) == [keep, drop], "both links live")
    admin.open_entry_en(target.code)
    assert admin.text_value("linkTitle") == drop
    confirmed = _publish_edit(admin, target, {"activeStatus": False})
    admin.open_entry_en(target.code)
    assert admin.active_status_stored() == "false"
    view, model = _public(anon_pages, lambda m: _titles(m) == [keep], "only the sibling remains", started=confirmed)
    assert drop not in view.body_text() and drop_desc not in view.body_text()


# ===========================================================================
# Functional-Low / audit
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_low
@pytest.mark.tc_140414
@AUTH_FREE_PAGE
def test_140414_page_cannot_be_saved_without_status(page):
    """140414 — looks for the Status control on the page record (read-only) and
    on a section form; the case cannot run without it."""
    _login(page, ROLE_EDITOR, SLUG_PAGE)
    real = BGRealPageA(page)
    real.open_real_page()
    labels = real.page.locator(f"{real.FORM} label").all_inner_texts()
    status_fields = real.page.locator(f'{real.FORM} [name="ObjectField_pageStatus"], {real.FORM} [name="ObjectField_status"]').count()
    real.evidence("140414 page record form")
    allure.attach(f"labels: {labels}\nstatus inputs: {status_fields}", name="page record controls")
    has_status = status_fields > 0 or any(" ".join(t.split()).startswith("Status") for t in labels)
    assert has_status, (
        "PRODUCT vs CASE: the Visas & Immigration page record has no Status field (no Draft / Published / "
        f"Unpublished dropdown); form labels are {[' '.join(t.split()) for t in labels]}. The workflow badge is the "
        "only status, so 'cannot be saved with no Status selected' cannot be exercised")


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_low
@pytest.mark.tc_140415
@AUTH_FREE_PAGE
def test_140415_created_and_modified_dates_automatic(page, own):
    """140415 — Created / Last Modified are set by the system and not editable."""
    admin = _login(page, ROLE_EDITOR)
    title = _name("140415", "Audit date")
    entry = _create(admin, own, SLUG_SECTION, bg_data(SLUG_SECTION, title, _key("140415"), displayOrder=550),
                    publish=False)
    import re  # noqa: PLC0415

    def _dates() -> tuple[str, str, str]:
        admin.open_entry_en(entry.code)
        bar = admin.editing_bar_text()
        match = re.search(r"Created ([\d/]+, [\d:]+), last modified ([\d/]+, [\d:]+)", bar)
        admin.open_list_all()
        row = [r for r in admin.list_rows() if r["entry_id"] == entry.entry_id]
        cells = admin.page.locator(f'tr:has([data-qc-oel-history="{entry.entry_id}"]) td').all_inner_texts()
        return (match.group(1) if match else "", match.group(2) if match else "",
                cells[2].strip() if len(cells) > 2 else "") if row else ("", "", "")

    created, modified, column = _dates()
    admin.open_entry_en(entry.code)
    inputs = admin.page.locator(f'{admin.FORM} [name*="dateCreated"], {admin.FORM} [name*="dateModified"], '
                                f'{admin.FORM} [name*="createDate"], {admin.FORM} [name*="modifiedDate"]').count()
    admin.evidence("140415 after create")
    allure.attach(f"created {created}\nmodified {modified}\nlist column {column}\ndate inputs on form {inputs}",
                  name="dates at creation")
    failures: list[str] = []
    _soft(failures, bool(created) and created == modified, f"at creation: created {created!r} / modified {modified!r}")
    _soft(failures, inputs == 0, f"{inputs} editable date inputs exist on the form")
    # Second save in a later minute (the edit bar shows minutes only).
    created_minute = created.split(":")[-1] if created else ""
    wait_until(lambda: datetime.now().strftime("%M") != created_minute, timeout=75.0, poll=1.0)
    admin.open_entry_en(entry.code)
    admin.fill_rich("sectionBody", "QCTEST-130701 audit date probe")
    admin.click_save_as_draft()
    _soft(failures, admin.save_went_through(), f"second save: {admin.refusal_evidence()}")
    created2, modified2, column2 = _dates()
    allure.attach(f"created {created2}\nmodified {modified2}\nlist column {column2}", name="dates after the edit")
    _soft(failures, created2 == created, f"Created changed {created!r} -> {created2!r}")
    _soft(failures, modified2 != modified and column2 != column, f"Last modified did not advance ({modified2!r}, {column2!r})")
    _soft(failures, False, "PRODUCT vs CASE (wording/presentation): there are no 'Created Date' / 'Last Modified "
                           "Date' fields — the dates are shown only in the edit-bar sentence and the list's LAST "
                           "MODIFIED column") if not failures else None
    # User decision 2026-10-06: the missing date fields fail the case (LOW).
    _finish(failures)


@allure.epic(EPIC)
@allure.feature(FEATURE)
@pytest.mark.functional_low
@pytest.mark.workflow
@pytest.mark.tc_140537
@AUTH_FREE_PAGE
def test_140537_every_action_in_audit_log(page, own):
    """140537 — save-as-draft, publish, unpublish are each recorded with actor,
    action and timestamp (History trail; Control Panel audit log probed)."""
    admin = _login(page, ROLE_EDITOR)
    title = _name("140537", "Audit")
    entry = _create(admin, own, SLUG_SECTION, bg_data(SLUG_SECTION, title, _key("140537"), displayOrder=540,
                                                      sectionBody="QCTEST-130701 audit log probe body"),
                    publish=False)
    failures: list[str] = []
    _publish_edit(admin, entry, {})
    admin.open_list_all()
    admin.adopt(entry)
    dialogs = admin.run_row_action(entry, "unpublish")
    allure.attach(repr(dialogs), name="unpublish dialogs")
    status = admin.wait_row_status(entry, (STATUS_UNPUBLISHED, STATUS_DRAFT))
    _soft(failures, status == STATUS_UNPUBLISHED, f"status after Unpublish {status!r} (case: Unpublished)")
    trail = _history(admin, entry)
    admin.evidence("140537 history")
    actions = [h["action"] for h in trail]
    for kind in ("draft", "publish", "unpublish"):
        _soft(failures, _has_action(trail, kind),
              f"no {kind} entry ({HISTORY_LABELS[kind]}) with actor Test Editor and a time in History: {trail!r}")
    order = [h["action"] for h in trail if any(h["action"] in v for v in HISTORY_LABELS.values())]
    _soft(failures, order[:3] == ["Unpublished", "Approved", "Created"],
          f"History order (newest first) {order}, expected Unpublished, Approved, Created")
    allure.attach("History labels the actions 'Created' (save as draft) and 'Approved' (publish) — wording only",
                  name="LOW wording note")
    # The Control Panel audit-log screen named by step 4.
    audit = BGAdminPage(page, SLUG_SECTION, "A")
    audit.open(control_panel_url("/group/control_panel/manage?p_p_id=com_liferay_portal_security_audit_web_portlet_AuditPortlet"))
    audit.evidence("140537 control panel audit log")
    audit_text = audit.rendered_body_text()[:1500]
    allure.attach(audit_text, name="Control Panel audit log as Editor")
    # User decision 2026-10-06: judged by the record History; the Control Panel
    # audit log being closed to the Editor is reported as a note only.
    allure.attach(f"Control Panel audit log open to the Editor: {title in audit_text}", name="audit log note")
    _finish(failures)
