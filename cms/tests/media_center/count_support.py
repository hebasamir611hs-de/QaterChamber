"""
cms/tests/media_center/count_support.py — COUNT-agent test-layer support for
PBI 130709 (Media Center Count Widget, Control_Panel). Not a conftest (four
agents share this folder): the test module imports these fixtures explicitly.
Orchestrates Page-Object calls only — no raw Playwright.

DATA RULES
  - Every record this module creates is a disposable QCTEST-130709-CW-0n
    widget (Display Name in the "QCTEST" namespace), captured by list-id diff
    + exact read-back, and deleted ONLY through the guarded single-record
    delete in a fresh Editor session at teardown. The five real widgets
    (QCDEMO-130709-COUNT-01..05) are never opened for edit.
  - Display Order: the cases' "6th widget" slot = 600 (next 100-grid slot after
    the live 100..500); CW-02 700, CW-03 800, CW-04 900 as the cases state.
  - Public reads only in fresh logged-out contexts, after the CMS shows
    Published and the reopened record stores Active Status ticked.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.media_center.mc_count_widget_admin_page import (
    EVIDENCE_DIR,
    K_ACTIVE,
    K_NAME,
    K_ORDER,
    K_TYPE,
    K_UNIT,
    MSG_ARABIC_SAVED,
    MSG_DRAFT_SAVED,
    MSG_SAVED_AND_PUBLISHED,
    ROLE_EDITOR,
    CWEntry,
    McCountsPublicView,
    McCountWidgetAdminPage,
)
from config.settings import PROJECT_ROOT
from core.web.browser import new_context

FIXTURES = os.path.join(str(PROJECT_ROOT), "cms", "tests", "media_center", "count_fixtures")
ICON_1 = os.path.join(FIXTURES, "qctest-cw-icon.svg")
ICON_2 = os.path.join(FIXTURES, "qctest-cw-icon-2.svg")

ROLE_AUTHOR = "Site Content Author"
USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492"}
PUBLISH_CONFIRM_TIMEOUT = 120.0
PUBLIC_TIMEOUT_S = 30.0
DESKTOP = (1920, 1080)
FINDINGS_LOG = os.path.join(EVIDENCE_DIR, "findings.jsonl")
LEDGER = os.path.join(EVIDENCE_DIR, "qctest_ledger.jsonl")
LIFERAY_SUCCESS = "Your request completed successfully."
REQUIRED_RE = re.compile(r"required|mandatory|cannot be empty|must not be empty|fill", re.I)

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)

CW01 = "QCTEST-130709-CW-01"
CW01_DATA = {K_TYPE: "Videos", K_NAME: "QCTEST Clips", f"{K_NAME}_ar": "QCTEST مقاطع",
             K_UNIT: "QCTEST clips", f"{K_UNIT}_ar": "QCTEST مقطع", "icon_file": ICON_1,
             K_ORDER: 600, K_ACTIVE: True}

CAP_NOTE = ("the public strip renders at most data-qc-mcc-max=5 widgets (fragment 'maxWidgets': '5', "
            "active entries sorted by displayOrder then sliced to 5), so a published+active widget "
            "after the five real ones (100..500) is delivered by the guest API but never shown")


# ===========================================================================
# Findings / ledger
# ===========================================================================
def record_finding(tc: str, kind: str, **details) -> None:
    finding = {"tc": tc, "kind": kind, "at": datetime.now().isoformat(timespec="seconds"), **details}
    allure.attach(json.dumps(finding, ensure_ascii=False, indent=1, default=str), name=f"finding: {kind}")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(FINDINGS_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(finding, ensure_ascii=False, default=str) + "\n")


def _ledger(event: str, entry: CWEntry, **extra) -> None:
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": datetime.now().isoformat(timespec="seconds"), "event": event,
                                 "logical": entry.logical, "id": entry.entry_id, "code": entry.code,
                                 "value": entry.value, **extra}, ensure_ascii=False) + "\n")


# ===========================================================================
# Registry + teardown
# ===========================================================================
class CWRegistry:
    def __init__(self):
        self.entries: list[CWEntry] = []

    def track(self, entry: CWEntry) -> CWEntry:
        if not isinstance(entry, CWEntry) or not entry.in_namespace():
            raise ValueError(f"{entry} is not a captured QCTEST-130709-CW- record")
        if all(e.entry_id != entry.entry_id for e in self.entries):
            self.entries.append(entry)
            _ledger("created", entry)
        return entry


def teardown_entries(browser, entries: list[CWEntry], label: str) -> None:
    if not entries:
        return
    ctx = new_context(browser, use_auth_state=False)
    done, failures = [], []
    try:
        drv = McCountWidgetAdminPage(ctx.new_page())
        drv.login_as_role(ROLE_EDITOR)
        drv.open_list_all()
        if drv.signed_in_user()[0] != USER_IDS[ROLE_EDITOR]:
            failures.append("cleanup login as Site Content Editor failed")
        else:
            for entry in reversed(entries):
                tag = f"{entry.logical} (id {entry.entry_id}, code {entry.code})"
                try:
                    drv.adopt_cw(entry)
                    drv.open_list_all()
                    if not drv.row_of(entry):
                        done.append(f"already gone: {tag}")
                        continue
                    if not drv.make_identity_deletable(entry):
                        failures.append(f"NOT removed {tag}: Display Name could not be put back in QCTEST namespace")
                        continue
                    if drv.delete_disposable_entry(entry):
                        done.append(f"removed {tag}")
                        _ledger("deleted", entry)
                    else:
                        failures.append(f"NOT removed {tag}: guarded delete refused/failed")
                except Exception as exc:  # noqa: BLE001 — collected below
                    failures.append(f"{tag}: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(done + failures) or "nothing to remove", name=f"QCTEST teardown ({label})")
    with open(os.path.join(EVIDENCE_DIR, "teardown.log"), "a", encoding="utf-8") as handle:
        handle.write(f"[{datetime.now().isoformat(timespec='seconds')}] {label}\n  " + "\n  ".join(done + failures) + "\n")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def cw_disposable(browser):
    registry = CWRegistry()
    yield registry
    teardown_entries(browser, registry.entries, "function")


@pytest.fixture
def anon_view(browser):
    """Fresh logged-out contexts for every public read."""
    contexts = []

    def _make(viewport: tuple | None = None) -> McCountsPublicView:
        ctx = new_context(browser, viewport=viewport or DESKTOP, use_auth_state=False)
        contexts.append(ctx)
        return McCountsPublicView(ctx.new_page())

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# CMS orchestration
# ===========================================================================
def role_session(page, role: str = ROLE_EDITOR) -> McCountWidgetAdminPage:
    drv = McCountWidgetAdminPage(page)
    outcome = drv.login_as_role(role)
    if outcome == "auth_failed":
        pytest.fail(f"PRECONDITION: Liferay refused the .env credentials for {role!r}")
    drv.open_list_all()
    user_id, _ = drv.signed_in_user()
    assert user_id == USER_IDS[role], f"login as {role!r} gave userId {user_id!r} (expected {USER_IDS[role]})"
    return drv


def save(drv: McCountWidgetAdminPage, publish: bool = True, role: str = ROLE_EDITOR) -> dict:
    user_id, _ = drv.signed_in_user()
    assert user_id == USER_IDS[role], f"the session is now userId {user_id!r}, not {role}"
    drv.click_publish() if publish else drv.click_save_as_draft()
    result = {"went_through": drv.save_went_through(), "refused": drv.save_was_refused(),
              "evidence": drv.refusal_evidence(), "messages": drv.all_messages_text()}
    if result["went_through"]:
        expected = MSG_SAVED_AND_PUBLISHED if publish else MSG_DRAFT_SAVED
        result["editbar"] = drv.success_messages(expected, 10.0)
        # The cases ask for "the Liferay success toast". LIVE 2026-10-12 the
        # Editor's Publish shows Liferay's standard "Your request completed
        # successfully." (earlier builds: "Saved and published."); either is it.
        result["success_message_shown"] = any(expected in t or LIFERAY_SUCCESS in t for t in result["editbar"])
    return result


def create(drv: McCountWidgetAdminPage, registry: CWRegistry, logical: str, data: dict, tc: str,
           publish: bool = True, role: str = ROLE_EDITOR) -> tuple[CWEntry | None, dict]:
    value = str(data[K_NAME]) if data.get(K_NAME) else ""
    ids_before = drv.snapshot_ids()
    result: dict = {}
    entry = None
    try:
        drv.open_create_form_en()
        drv.fill_widget(data)
        result["filled"] = drv.read_widget()
        result["filled_shot"] = drv.evidence(f"{tc}_{logical}_filled")
        result.update(save(drv, publish, role))
        if result["went_through"]:
            result["arabic_saved"] = drv.wait_arabic_saved(15.0)
            result["arabic_msg"] = MSG_ARABIC_SAVED
        result["screenshot"] = drv.evidence(f"{tc}_{logical}_after_save")
    finally:
        try:
            if value.upper().startswith("QCTEST"):
                entry = drv.identify_created(logical, value, ids_before)
                if entry:
                    registry.track(entry)
            result["new_rows"] = drv.new_rows_since(ids_before)
            for row in result["new_rows"]:
                if not entry or row["entry_id"] != entry.entry_id:
                    record_finding(tc, "unexpected new row after save", row=row)
        except Exception as exc:  # noqa: BLE001 — registration must not mask the result
            allure.attach(repr(exc), name=f"registration of {value!r} failed")
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"create {logical}")
    return entry, result


def create_cw01(drv, registry, tc: str, **overrides) -> CWEntry:
    data = dict(CW01_DATA, **overrides)
    entry, result = create(drv, registry, CW01, data, tc)
    assert result.get("went_through"), f"PRECONDITION: creating {CW01} did not go through: {result}"
    assert entry is not None, f"PRECONDITION: {CW01} saved but not identifiable as one new record"
    wait_published(drv, entry)
    require_active(drv, entry)
    return entry


def wait_published(drv, entry: CWEntry) -> None:
    status = drv.wait_row_status(entry, (STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT)
    assert status == STATUS_PUBLISHED, f"{entry.logical} never reached Published (last {status!r})"


def require_active(drv, entry: CWEntry) -> None:
    drv.open_entry_en(entry.code)
    stored = drv.active_status_stored()
    if stored != "true":
        pytest.fail(f"PRECONDITION NOT MET — {entry.logical} stores Active Status {stored!r}")


def edit(drv: McCountWidgetAdminPage, entry: CWEntry, tc: str, what: str, data: dict | None = None,
         typed: dict | None = None, publish: bool = True) -> dict:
    """Opens the captured record, fills `data` / types `typed` ({key or key_ar: text}), saves."""
    drv.open_entry_en(entry.code)
    before_row = _row(drv, entry)
    drv.open_entry_en(entry.code)
    if data:
        drv.fill_widget(data)
    for key, text in (typed or {}).items():
        drv.type_text(key.removesuffix("_ar"), text, arabic=key.endswith("_ar"))
    result = {"before_row": before_row, "filled": drv.read_widget()}
    result.update(save(drv, publish))
    result["screenshot"] = drv.evidence(f"{tc}_{what}_after_save")
    result["after_row"] = _row(drv, entry)
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"edit {what}")
    return result


def _row(drv, entry: CWEntry) -> dict:
    drv.open_list_all()
    return drv.row_of(entry)


def stored(drv, entry: CWEntry) -> dict:
    drv.open_entry_en(entry.code)
    return drv.read_widget()


def refusal_points_at(result: dict, key: str, label: str) -> bool:
    blob = json.dumps(result.get("evidence", {}), ensure_ascii=False)
    return key in blob or label.lower() in (result.get("messages") or "").lower()


# ===========================================================================
# Public orchestration
# ===========================================================================
def card_by_label(state: dict, label: str) -> dict | None:
    for card in state.get("cards", []):
        if " ".join(card["label"].split()) == label:
            return card
    return None


def public_card(anon_view, tc: str, label: str, locale: str = "en", predicate=None,
                timeout: float = PUBLIC_TIMEOUT_S) -> dict:
    """Polls a fresh logged-out hub for the card labelled `label` (+ `predicate(card)`).
    Returns {card, state, guest, seconds, held, shot, cap}."""
    view = anon_view()

    def _ok(state):
        card = card_by_label(state, label)
        return card is not None and (predicate is None or predicate(card))

    state, secs, held = view.poll(_ok, timeout=timeout, locale=locale)
    shot = view.strip_evidence(f"{tc}_public_{locale}_{label[:20]}")
    guest = view.guest_entries(locale)
    mine = [g for g in guest if " ".join(str(g.get(K_NAME) or "").split()) == label]
    cap = bool(mine and not held and state.get("max") and len(state.get("cards", [])) >= int(state["max"]))
    out = {"card": card_by_label(state, label), "state_cards": [(c["label"], c["value"]) for c in state.get("cards", [])],
           "max": state.get("max"), "dir": state.get("dir"), "guest_match": mine, "seconds": round(secs, 1),
           "held": held, "shot": shot, "cap": cap, "full_state": state}
    allure.attach(json.dumps({k: v for k, v in out.items() if k != "full_state"}, ensure_ascii=False, indent=1,
                             default=str), name=f"public {locale} {label}")
    if cap:
        record_finding(tc, "public strip 5-widget cap hides the QCTEST widget", locale=locale, label=label,
                       strip=out["state_cards"], guest=mine, screenshot=shot)
    return out


def public_absent(anon_view, tc: str, label_contains: str, locale: str = "en") -> dict:
    view = anon_view()
    view.open_hub(locale)
    state = view.read()
    shot = view.strip_evidence(f"{tc}_public_{locale}_absent")
    guest = view.guest_entries(locale)
    shown = [c for c in state.get("cards", []) if label_contains in c["label"]]
    delivered = [g for g in guest if label_contains in str(g.get(K_NAME) or "")]
    out = {"shown": shown, "guest_delivered": delivered, "cards": [(c["label"], c["value"]) for c in state.get("cards", [])],
           "shot": shot}
    allure.attach(json.dumps(out, ensure_ascii=False, indent=1, default=str), name=f"public absent {locale}")
    return out


REAL_VIDEOS = "QCDEMO-130709-COUNT-03"   # real widget used for the public steps (type Videos, like CW-01)


def real_edit(window, tc: str, what: str, data: dict | None = None, typed: dict | None = None) -> dict:
    """ONE UI edit + Publish on the REAL widget inside its guarded window
    (concurrency re-check first, settled state recorded after)."""
    drv = window.drv
    window.open_for_edit()
    if data:
        drv.fill_widget(data)
    for key, text in (typed or {}).items():
        drv.type_text(key.removesuffix("_ar"), text, arabic=key.endswith("_ar"))
    window.mark_intent({**(data or {}), **(typed or {})})
    result = {"filled": drv.read_widget()}
    try:
        result.update(save(drv))
    except Exception:
        window.after_edit()
        raise
    result["screenshot"] = drv.evidence(f"{tc}_REAL_{what}_after_save")
    window.after_edit()
    result["stored_after"] = {k: window.last_ours.get(k) for k in (K_NAME, K_UNIT, K_ORDER, K_ACTIVE)}
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"REAL edit {what}")
    return result


def card_index(state: dict, label: str) -> int:
    for card in state.get("cards", []):
        if " ".join(card["label"].split()) == label:
            return card["index"]
    return -1


def reflow_gaps(state: dict) -> list[float]:
    """Horizontal gaps between consecutive cards (equal gaps = no hole)."""
    boxes = sorted((c["card_box"] for c in state.get("cards", [])), key=lambda b: b.get("left", 0))
    return [round(b2["left"] - b1["right"], 1) for b1, b2 in zip(boxes, boxes[1:])]


def cap_message(pub: dict) -> str:
    return (f"PUBLIC: the QCTEST widget is not in the summary counts strip — {CAP_NOTE}. "
            f"Strip shows {pub['state_cards']}; guest API delivers {pub['guest_match']}; screenshot {pub['shot']}")
