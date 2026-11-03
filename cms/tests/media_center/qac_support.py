"""
cms/tests/media_center/qac_support.py — test-layer support for the Media
Center Quick Access Card Control_Panel cases (PBI 130709, agent QAC).

Not a conftest (four agents share this folder): the QAC test modules import
these fixtures explicitly. Orchestration of Page-Object calls only.

DATA RULES (p3_rules_130709.md):
  - Real cards QCDEMO-130709-CARD-01..06 are read, never saved/unpublished/deleted.
  - Every created card is a disposable QCTEST card, captured by list-id diff +
    exact Card Title read back by code, and deleted in teardown through the
    guarded single-record delete from a fresh Editor session.
  - Position expectations are computed from the live real cards' Display Orders
    (read once per module): expected index = number of visible real cards with
    a lower Display Order.
  - Public reads use a fresh logged-out context; the stored Active Status of the
    card is checked before a "visible" assertion.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from time import monotonic

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.media_center.mc_quick_access_card_admin_page import (
    EVIDENCE_DIR,
    K_ORDER,
    MSG_ARABIC_SAVED,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    MediaCenterHubView,
    QacAdminPage,
    QacEntry,
)
from config.settings import PROJECT_ROOT
from core.web.browser import new_context

FIXTURES = os.path.join(str(PROJECT_ROOT), "cms", "tests", "media_center", "qac_fixtures")
ICON_SVG = os.path.join(FIXTURES, "qctest-qac-icon.svg")
ICON_PNG = os.path.join(FIXTURES, "qctest-qac-icon.png")
ICON_JPG = os.path.join(FIXTURES, "qctest-qac-icon.jpg")
VIDEO_LIBRARY = "/web/qatar-chamber/video-library"
PUBLIC_BUDGET_S = 5.0
PUBLIC_GRACE_S = 45.0
PUBLISH_CONFIRM_TIMEOUT = 120.0
FINDINGS_LOG = os.path.join(EVIDENCE_DIR, "findings.jsonl")
OUTCOME_LOG = os.path.join(EVIDENCE_DIR, "teardown.log")
STAMP = datetime.now().strftime("%m%d%H%M")

QAC01 = {
    "cardTitle": "QCTEST Media Kit", "cardTitle_ar": "QCTEST الحقيبة الإعلامية",
    "cardDescription": "QCTEST Download logos and media assets.",
    "cardDescription_ar": "QCTEST حمّل الشعارات والمواد الإعلامية.",
    "destinationLink": VIDEO_LIBRARY, "displayOrder": 700, "activeStatus": True,
    "icon_file": ICON_SVG, "icon_stem": "qctest-qac-icon",
}


def card_data(title: str, title_ar: str, desc: str, desc_ar: str, order: int, **overrides) -> dict:
    data = {"cardTitle": title, "cardTitle_ar": title_ar, "cardDescription": desc, "cardDescription_ar": desc_ar,
            "destinationLink": VIDEO_LIBRARY, "displayOrder": order, "activeStatus": True,
            "icon_file": ICON_SVG, "icon_stem": "qctest-qac-icon"}
    data.update(overrides)
    return data


# ===========================================================================
# findings / evidence
# ===========================================================================
def record_finding(tc: str, kind: str, **details) -> None:
    finding = {"tc": tc, "kind": kind, "at": datetime.now().isoformat(timespec="seconds"), **details}
    allure.attach(json.dumps(finding, ensure_ascii=False, indent=1, default=str), name=f"finding: {kind}")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(FINDINGS_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(finding, ensure_ascii=False, default=str) + "\n")


def attach(name: str, value) -> None:
    allure.attach(json.dumps(value, ensure_ascii=False, indent=1, default=str), name=name)


# ===========================================================================
# sessions
# ===========================================================================
class Sessions:
    """Fresh logged-out contexts, one per role / visitor; closed at teardown."""

    def __init__(self, browser):
        self.browser = browser
        self.contexts = []

    def _ctx(self, viewport=None):
        ctx = new_context(self.browser, viewport=viewport, use_auth_state=False)
        self.contexts.append(ctx)
        return ctx

    def admin(self, role: str, open_list: bool = True) -> QacAdminPage:
        try:
            from config.settings import cms_role_credentials  # noqa: PLC0415
            cms_role_credentials(role)
        except RuntimeError as exc:
            pytest.skip(f"BLOCKED: {exc}")
        admin = QacAdminPage(self._ctx().new_page())
        outcome = admin.login_as_role(role)
        if outcome == "auth_failed":
            pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for {role!r}")
        if open_list:
            admin.open_manage_page_raw()
        require_role(admin, role)
        return admin

    def visitor(self, viewport=None) -> MediaCenterHubView:
        return MediaCenterHubView(self._ctx(viewport).new_page())

    def close(self):
        for ctx in self.contexts:
            try:
                ctx.close()
            except Exception:  # noqa: BLE001
                pass


def require_role(admin: QacAdminPage, role: str) -> None:
    """The session must still be the named account (a dropped session would be
    silently re-authenticated as TEST_USER by the framework's session guard)."""
    user_id, name = admin.signed_in_user()
    if user_id != ROLE_USER_IDS[role]:
        pytest.fail(f"PRECONDITION: the session is userId {user_id!r} ({name}), not {role!r} "
                    f"({ROLE_USER_IDS[role]}) — role outcome not asserted")


class Registry:
    def __init__(self):
        self.entries: list[QacEntry] = []

    def track(self, entry: QacEntry | None) -> QacEntry | None:
        if entry is not None:
            if not entry.in_namespace():
                raise ValueError(f"{entry} is not a QCTEST card")
            if all(e.entry_id != entry.entry_id for e in self.entries):
                self.entries.append(entry)
        return entry


def teardown_cards(browser, entries: list[QacEntry]) -> list[str]:
    if not entries:
        return []
    ctx = new_context(browser, use_auth_state=False)
    done, failures = [], []
    try:
        admin = QacAdminPage(ctx.new_page())
        admin.login_as_role(ROLE_EDITOR)
        admin.open_list_all()
        if admin.signed_in_user()[0] != ROLE_USER_IDS[ROLE_EDITOR]:
            failures.append("cleanup login as Site Content Editor failed")
        else:
            for entry in reversed(entries):
                tag = f"{entry.title!r} (id {entry.entry_id}, code {entry.code})"
                try:
                    admin.adopt(entry)
                    admin.open_list_all()
                    if not admin.row_present(entry):
                        (done if admin.is_list_fully_expanded() else failures).append(f"already gone: {tag}")
                        continue
                    if admin.delete_disposable_entry(entry):
                        done.append("removed " + tag)
                    else:
                        failures.append("NOT removed (guarded delete refused/failed) " + tag)
                except Exception as exc:  # noqa: BLE001 — collected
                    failures.append(f"{tag}: {exc!r}")
    finally:
        ctx.close()
    lines = done + failures
    allure.attach("\n".join(lines) or "nothing", name="QCTEST teardown")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(OUTCOME_LOG, "a", encoding="utf-8") as handle:
        handle.write(f"[{datetime.now().isoformat(timespec='seconds')}]\n  " + "\n  ".join(lines) + "\n")
    return failures


@pytest.fixture
def qac(browser):
    """(sessions, registry): every QCTEST card tracked here is deleted afterwards."""
    sessions, registry = Sessions(browser), Registry()
    yield sessions, registry
    sessions.close()
    failures = teardown_cards(browser, registry.entries)
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture(scope="module")
def real_cards(browser):
    """The six real cards as stored right now (read-only) + public order baseline."""
    ctx = new_context(browser, use_auth_state=False)
    try:
        admin = QacAdminPage(ctx.new_page())
        admin.login_as_role(ROLE_EDITOR)
        cards = admin.real_cards()
        leftovers = admin.qctest_rows()
    finally:
        ctx.close()
    attach("real cards (read-only baseline)", cards)
    if leftovers:
        attach("QCTEST rows present before this module", leftovers)
    return {"cards": cards, "leftovers": leftovers}


def visible_real(real_cards: dict) -> list[dict]:
    return [c for c in real_cards["cards"] if c["active"] and c["status"] == "PUBLISHED"]


def expected_index(real_cards: dict, order: int, others: list[int] = ()) -> int:
    """0-based slot of a card with `order` among the visible real cards (and
    `others` = this test's other visible QCTEST orders)."""
    return sum(1 for c in visible_real(real_cards) if c["order"] < order) + sum(1 for o in others if o < order)


# ===========================================================================
# CMS orchestration
# ===========================================================================
def save(admin: QacAdminPage, role: str, publish: bool = True) -> dict:
    require_role(admin, role)
    admin.click_publish() if publish else admin.click_save_as_draft()
    result = {"went_through": admin.save_went_through(), "refused": admin.save_was_refused(),
              "evidence": admin.refusal_evidence(), "messages": admin.all_messages_text()}
    if result["went_through"]:
        result["editbar"] = admin.success_messages("saved", 10.0)
        result["arabic_saved"] = admin.wait_arabic_saved(15.0)
    else:
        result["page_text"] = admin.wait_body_contains(("required", "Unsupported", "valid", "positive"), 3.0)[:3000]
    return result


def create(admin: QacAdminPage, registry: Registry, data: dict, tc: str, role: str = ROLE_EDITOR,
           publish: bool = True, before_save=None) -> tuple[QacEntry | None, dict]:
    title = data["cardTitle"]
    ids_before = admin.snapshot_ids()
    result: dict = {}
    entry = None
    try:
        admin.open_create_form()
        admin.fill_card(data)
        if before_save:
            before_save(admin)
        result = save(admin, role, publish)
        result["screenshot"] = admin.evidence(f"{tc}_create_after_save")
    finally:
        try:
            if title.strip().startswith("QCTEST"):
                entry = admin.identify_created(title, ids_before)
                registry.track(entry)
                for extra in getattr(admin, "last_identify_matches", []):
                    registry.track(admin.adopt(extra))
            new = [r for r in admin.new_rows_since(ids_before)
                   if r["title"].strip().startswith("QCTEST") and r["code"]]
            for row in new:
                registry.track(admin.adopt(QacEntry(row["title"].strip(), row["entry_id"], row["code"])))
            result["new_rows"] = admin.new_rows_since(ids_before)
        except Exception as exc:  # noqa: BLE001 — registration must not mask the result
            allure.attach(repr(exc), name="capture failed")
    attach(f"create {title}", result)
    return entry, result


def create_ok(admin, registry, data, tc, role=ROLE_EDITOR, publish=True) -> QacEntry:
    entry, result = create(admin, registry, data, tc, role, publish)
    assert result.get("went_through"), f"PRECONDITION: creating {data['cardTitle']!r} did not go through: {result}"
    assert entry is not None, f"PRECONDITION: {data['cardTitle']!r} saved but not identifiable as ONE new record"
    if publish and role == ROLE_EDITOR:
        status = admin.wait_row_status(entry, (STATUS_PUBLISHED,), PUBLISH_CONFIRM_TIMEOUT)
        assert status == STATUS_PUBLISHED, f"PRECONDITION: {entry.title!r} never reached Published ({status!r})"
    return entry


def edit(admin: QacAdminPage, entry: QacEntry, data: dict, tc: str, role: str = ROLE_EDITOR,
         prepare=None) -> dict:
    """Opens the captured card, applies `data` (+ optional prepare(admin)), clicks
    Publish/Submit and returns the save evidence + the before/after values."""
    admin.open_entry(entry.code)
    before = admin.read_card()
    banner = admin.editing_bar_text()
    admin.fill_card(data)
    if prepare:
        prepare(admin)
    filled = admin.read_card()
    result = save(admin, role, True)
    result.update({"before": before, "filled": filled, "banner": banner,
                   "screenshot": admin.evidence(f"{tc}_edit_after_save")})
    attach(f"edit {entry.title}", result)
    return result


def sync_identity(admin: QacAdminPage, registry: Registry, entry: QacEntry, role: str = ROLE_EDITOR) -> QacEntry:
    """After an edit: keep the teardown identity equal to the STORED title. A
    stored title outside the QCTEST namespace (e.g. an accepted blank) is put
    back to the captured title first, so the guarded delete can re-verify it."""
    values = stored(admin, entry)
    title = values["cardTitle"].strip()
    if title == entry.title:
        return entry
    if not title.startswith("QCTEST"):
        admin.fill_en("cardTitle", entry.title)
        save(admin, role, True)
        record_finding("identity", "restored blank/foreign title for teardown", entry=entry.code, stored=title)
        return entry
    new = QacEntry(title, entry.entry_id, entry.code)
    admin.adopt(new)
    registry.entries = [new if e.entry_id == entry.entry_id else e for e in registry.entries]
    return new


def stored(admin: QacAdminPage, entry: QacEntry) -> dict:
    admin.open_entry(entry.code)
    return admin.read_card()


def require_active(admin: QacAdminPage, entry: QacEntry) -> None:
    values = stored(admin, entry)
    if values["activeStatus"] != "true":
        pytest.fail(f"PRECONDITION: {entry.title!r} stores Active Status {values['activeStatus']!r}")


def message_check(tc: str, expected: str, result: dict, context: str) -> bool:
    """Exact expected message present? If a refusal happened with another
    wording, a WORDING finding is recorded (behaviour judged separately)."""
    blob = " | ".join([result.get("messages", ""), result.get("page_text", ""),
                       json.dumps(result.get("evidence", {}), ensure_ascii=False)])
    if expected in blob:
        return True
    record_finding(tc, "WORDING", context=context, expected=expected,
                   shown=result.get("messages") or result.get("evidence"), screenshot=result.get("screenshot"))
    return False


# ===========================================================================
# public orchestration
# ===========================================================================
def public_until(visitor: MediaCenterHubView, predicate, message: str, tc: str, locale: str = "en",
                 started: float | None = None, budget: bool = True) -> list[dict]:
    """Polls the logged-out hub until predicate(cards); fails if never seen; a
    sighting later than the 5 s budget is a PROPAGATION finding + failure."""
    held, cards, seconds = visitor.poll(predicate, locale, PUBLIC_GRACE_S)
    shot = visitor.evidence(f"{tc}_public_{locale}_{re.sub(r'[^A-Za-z0-9]+', '_', message)[:40]}")
    attach(f"public {locale}: {message}", {"held": held, "seconds": round(seconds, 1), "cards": cards})
    cfg = {}
    if not held:
        try:
            cfg = visitor.grid_config()
            attach("hub fragment config", cfg)
            attach("anonymous delivery entries", visitor.delivery_entries())
        except Exception as exc:  # noqa: BLE001 — evidence only
            allure.attach(repr(exc), name="delivery evidence failed")
    assert held, f"{message}: not seen on the logged-out {locale.upper()} hub within {PUBLIC_GRACE_S:.0f}s " \
                 f"(cards: {[(c['title'], c['erc']) for c in cards]}; grid config {cfg}); evidence {shot}"
    if budget and started is not None:
        latency = monotonic() - started
        if seconds > PUBLIC_BUDGET_S:
            record_finding(tc, "PROPAGATION", message=message, seconds=round(seconds, 1), screenshot=shot)
            pytest.fail(f"{message}: first seen {seconds:.1f}s after the save (> {PUBLIC_BUDGET_S:.0f}s budget)")
        allure.attach(f"{latency:.1f}s", name="latency")
    return cards


def find(cards: list[dict], erc: str) -> dict:
    for card in cards:
        if card["erc"] == erc:
            return card
    return {}


def text_intact(box: dict | None) -> list[str]:
    if not box:
        return ["element not rendered"]
    out = []
    if box["sw"] > box["cw"] + 1 and ("hidden" in box["overflow"] or box["text_overflow"] == "ellipsis"):
        out.append(f"clipped horizontally (scrollWidth {box['sw']} > clientWidth {box['cw']}, "
                   f"overflow {box['overflow']}, text-overflow {box['text_overflow']})")
    if box["sh"] > box["ch"] + 1 and ("hidden" in box["overflow"] or box["clamp"] not in ("none", "")):
        out.append(f"clipped vertically (scrollHeight {box['sh']} > clientHeight {box['ch']}, clamp {box['clamp']})")
    if box["text_overflow"] == "ellipsis":
        out.append("text-overflow: ellipsis")
    return out


def overflow_outside(card: dict) -> list[str]:
    out = []
    c = card.get("card") or {}
    for key in ("title_box", "desc_box"):
        b = card.get(key)
        if b and c and (b["right"] > c["right"] + 2 or b["left"] < c["left"] - 2 or b["bottom"] > c["bottom"] + 2):
            out.append(f"{key} spills outside its card ({b} vs card {c})")
    return out


# ===========================================================================
# real cards under snapshot -> edit -> restore (user decision 2026-10-12)
# ===========================================================================
from cms.pages.media_center.mc_quick_access_card_admin_page import (  # noqa: E402
    RealCardConflict,
    RealCardGuard,
)


@pytest.fixture
def real_guard(browser):
    """A RealCardGuard on its own Editor session; every snapshotted card is
    restored (PUT) in teardown and must diff empty; a foreign change is never
    overwritten (reported as NEEDS-DECISION)."""
    ctx = new_context(browser, use_auth_state=False)
    api = QacAdminPage(ctx.new_page())
    api.login_as_role(ROLE_EDITOR)
    api.open_manage_page_raw()
    require_role(api, ROLE_EDITOR)
    guard = RealCardGuard(api)
    yield guard
    problems = []
    try:
        for code in list(guard.snapshots):
            try:
                problems += guard.restore(code)
            except Exception as exc:  # noqa: BLE001 — reported below
                problems.append(f"restore {code} raised {exc!r}")
    finally:
        os.makedirs(EVIDENCE_DIR, exist_ok=True)
        with open(os.path.join(EVIDENCE_DIR, "real_restore.log"), "a", encoding="utf-8") as handle:
            handle.write(f"[{datetime.now().isoformat(timespec='seconds')}]\n  " + "\n  ".join(guard.log) + "\n")
        allure.attach("\n".join(guard.log), name="real card snapshot / restore diff")
        ctx.close()
    if problems:
        raise AssertionError("REAL CARD RESTORE PROBLEM: " + " || ".join(problems))


def guarded_edit(guard: RealCardGuard, admin: QacAdminPage, ref, data: dict, tc: str, prepare=None) -> dict:
    """Concurrency check -> UI edit + Publish as the Editor -> record what was written."""
    guard.check_before_edit(ref.code)
    try:
        return edit(admin, ref, data, tc, prepare=prepare)
    finally:
        guard.record_written(ref.code)


def real_session(qac, guard: RealCardGuard, code: str = "QCDEMO-130709-CARD-01"):
    sessions, _ = qac
    admin = sessions.admin(ROLE_EDITOR)
    ref = guard.take(code)
    return sessions, admin, ref
