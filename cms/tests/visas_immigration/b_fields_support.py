"""
cms/tests/visas_immigration/b_fields_support.py — Agent B test-layer support
for PBI 130701 Visas & Immigration (suite 140362): hero fields of the BG Info
Page (Eyebrow, Page Title, Hero Description, Hero Banner), section fields
(Section Eyebrow / Title / Body, section Active Status) and the page-foot
Disclaimer.

Not a conftest (four agents share this folder): test modules import what they
need explicitly. Everything here orchestrates Page-Object calls.

DATA RULES (user decisions 2026-10-06, bg_rules.md ADDENDUM):
  - Section-level cases use OWN `QCTEST-130701-B-` BG Info Sections
    (pageKey visas-immigration, own lower-case sectionKey, Display Order 600 —
    the only 100-grid value in B's band 600-699) and own child items. Teardown
    deletes ONLY the captured ids through the guarded delete, children first.
  - Page-level cases edit the REAL page record 109104 only inside
    `real_page_session()`: hold scratchpad/locks/real_page_109104.lock, snapshot
    once per run (scratchpad/snapshots/109104_B_<ts>.json + screenshots), check
    the record still equals the snapshot BEFORE any edit, and in `finally`
    restore every changed field, re-publish, re-open + diff, and check the
    public page EN/AR. Any restore failure or remaining diff writes
    109104_B_HALT.json and halts every later B real-page / disclaimer test.
  - Disclaimer render cases (140533 / 140535) briefly publish an own section
    at Display Order 200 (on the grid; stable sort puts it after the real
    "arrivals" 200 and before "departures" 300, so the nested Official sources
    block keeps its host) under the same lock, then delete it and verify the
    real disclaimer is back.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
from dataclasses import replace
from datetime import datetime

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.visas_immigration.bg_admin_page import (
    MSG_SAVED_AND_PUBLISHED,
    REAL_SECTIONS,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    SLUG_SECTION,
    SNAPSHOT_DIR,
    BGEntry,
    BGFieldsAdminPageB,
    BGRealPageB,
    bg_data,
    real_page_lock,
)
from core.web.browser import new_context
from core.web.design_tokens import font_family_contains, hex_to_rgb
from web.pages.visas_immigration.visas_immigration_page import VisasPublicViewB

AGENT = "B"
PREFIX = "QCTEST-130701-B-"
STAMP = datetime.now().strftime("%m%d%H%M")
SECTION_ORDER = 600
DISCLAIMER_RENDER_ORDER = 200
PUBLISH_CONFIRM_TIMEOUT = 120.0
PUBLIC_BUDGET_S = 5.0      # case wording + cms-profile.md: 5 s
PUBLIC_GRACE_S = 40.0      # keep polling past the budget to tell "slow" from "absent"
DESKTOP = (1920, 1080)
MOBILE = (390, 844)
EVIDENCE_DIR = os.path.join(BGFieldsAdminPageB.EVIDENCE_ROOT, "130701_B")
FINDINGS_LOG = os.path.join(EVIDENCE_DIR, "findings.jsonl")
HALT_FILE = os.path.join(SNAPSHOT_DIR, "109104_B_HALT.json")
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
REQUIRED_RE = re.compile(r"required|mandatory|cannot be empty|must not be empty|is empty|fill|enter", re.I)
MAXLEN_RE = re.compile(r"max|maximum|characters|too long|exceed|limit", re.I)
REAL_DISCLAIMER_EN = ("Visa, entry and departure requirements can change. Verify current requirements with the "
                      "competent authority before travelling.")

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)


# ===========================================================================
# Findings / evidence
# ===========================================================================
def record_finding(tc: str, kind: str, **details) -> None:
    finding = {"tc": tc, "kind": kind, "at": datetime.now().isoformat(timespec="seconds"), **details}
    allure.attach(json.dumps(finding, ensure_ascii=False, indent=1, default=str), name=f"finding: {kind}")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(FINDINGS_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(finding, ensure_ascii=False, default=str) + "\n")


def attach(obj, name: str) -> None:
    text = json.dumps(obj, ensure_ascii=False, indent=1, default=str)
    allure.attach(text, name=name)
    os.makedirs(os.path.join(EVIDENCE_DIR, "facts"), exist_ok=True)
    with open(os.path.join(EVIDENCE_DIR, "facts", re.sub(r"[^\w.-]+", "_", name)[:100] + ".json"), "w",
              encoding="utf-8") as handle:
        handle.write(text)


# ===========================================================================
# Sessions
# ===========================================================================
def _login_editor(driver) -> None:
    outcome = driver.login_as_role(ROLE_EDITOR)
    if outcome == "auth_failed":
        pytest.skip("PRECONDITION: Liferay refused the .env credentials for 'Site Content Editor'")
    if outcome != "ok":
        pytest.fail("login as 'Site Content Editor' neither succeeded nor showed Liferay's refusal banner")


def editor_session(page, slug: str = SLUG_SECTION) -> BGFieldsAdminPageB:
    driver = BGFieldsAdminPageB(page, slug, AGENT)
    _login_editor(driver)
    driver.open_list_all()
    user_id, _ = driver.signed_in_user()
    if user_id != ROLE_USER_IDS[ROLE_EDITOR]:
        pytest.skip(f"PRECONDITION: Editor credentials sign in as userId {user_id!r}, not 156488")
    return driver


def driver_for(driver: BGFieldsAdminPageB, slug: str) -> BGFieldsAdminPageB:
    other = BGFieldsAdminPageB(driver.page, slug, AGENT)
    other.owned_entry_ids = driver.owned_entry_ids   # one owned-id set per session
    return other


def pinned(driver) -> None:
    user_id, _ = driver.signed_in_user()
    assert user_id == ROLE_USER_IDS[ROLE_EDITOR], f"the session is now userId {user_id!r}, not the Editor (156488)"


@pytest.fixture
def anon_pages(browser):
    """Fresh logged-out contexts for every public read; `viewport` optional."""
    contexts = []

    def _make(viewport: tuple | None = None) -> VisasPublicViewB:
        ctx = new_context(browser, viewport=viewport or DESKTOP, use_auth_state=False)
        contexts.append(ctx)
        return VisasPublicViewB(ctx.new_page())

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# Disposable registry + teardown (own QCTEST-130701-B- records only)
# ===========================================================================
class BRegistry:
    def __init__(self):
        self.entries: list[BGEntry] = []
        self.original_titles: dict[str, str] = {}

    def track(self, entry: BGEntry) -> BGEntry:
        if not isinstance(entry, BGEntry) or not entry.in_namespace() or entry.prefix != PREFIX:
            raise ValueError(f"{entry} is not a captured {PREFIX} record")
        for i, known in enumerate(self.entries):
            if known.entry_id == entry.entry_id:
                self.entries[i] = entry
                return entry
        self.entries.append(entry)
        self.original_titles[entry.entry_id] = entry.entry_value
        return entry

    def get(self, entry_id: str) -> BGEntry | None:
        return next((e for e in self.entries if e.entry_id == entry_id), None)


def _restore_identity(driver: BGFieldsAdminPageB, entry: BGEntry, original: str) -> BGEntry | None:
    """When a test changed the ENTRY field of its OWN record and the app stored
    it, puts the captured value back (opened by captured code only)."""
    driver.open_entry_en(entry.code)
    live = " ".join(driver.entry_value().split())
    if live == " ".join(original.split()):
        return replace(entry, entry_value=original)
    if live and live.casefold().startswith(PREFIX.casefold()) and live == entry.entry_value.strip():
        return entry   # still ours and matches the tracked identity
    driver.fill_en(driver.entry_field, original)
    driver.click_publish()
    driver.open_entry_en(entry.code)
    if " ".join(driver.entry_value().split()) == " ".join(original.split()):
        return replace(entry, entry_value=original)
    return None


def teardown_entries(browser, registry: BRegistry, label: str) -> None:
    """Guarded delete of the captured ids, newest first (children before their section)."""
    if not registry.entries:
        return
    ctx = new_context(browser, use_auth_state=False)
    done, failures = [], []
    try:
        page = ctx.new_page()
        base = BGFieldsAdminPageB(page, SLUG_SECTION, AGENT)
        if base.login_as_role(ROLE_EDITOR) != "ok":
            failures.append("cleanup login as Site Content Editor failed")
        else:
            for entry in reversed(registry.entries):
                tag = f"{entry.slug} {entry.entry_value!r} (id {entry.entry_id}, code {entry.code})"
                try:
                    driver = BGFieldsAdminPageB(page, entry.slug, AGENT)
                    driver.owned_entry_ids.add(entry.entry_id)
                    original = registry.original_titles.get(entry.entry_id, entry.entry_value)
                    if entry.entry_value != original or not entry.in_namespace():
                        fixed = _restore_identity(driver, entry, original)
                        if fixed is None:
                            failures.append(f"NOT removed {tag}: its ENTRY value could not be restored to {original!r}")
                            continue
                        entry = fixed
                    driver.adopt(entry)
                    driver.open_list_all()
                    if not driver.row_present(entry):
                        if driver.is_list_fully_expanded():
                            done.append(f"already gone: {tag}")
                        else:
                            failures.append(f"{tag}: not found and the list is NOT fully expanded")
                        continue
                    if driver.delete_disposable_entry(entry):
                        done.append(f"removed {tag}")
                    else:
                        failures.append(f"NOT removed {tag}: guarded delete refused/failed (see log)")
                except Exception as exc:  # noqa: BLE001 — collected below
                    failures.append(f"{tag}: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(done + failures) or "nothing to remove", name=f"QCTEST teardown ({label})")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(os.path.join(EVIDENCE_DIR, "teardown.log"), "a", encoding="utf-8") as handle:
        handle.write(f"[{datetime.now().isoformat(timespec='seconds')}] {label}\n  "
                     + "\n  ".join(done + failures) + "\n")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def b_disposable(browser):
    registry = BRegistry()
    yield registry
    teardown_entries(browser, registry, "function")


# ===========================================================================
# CMS orchestration (own records)
# ===========================================================================
def name(tc: str, suffix: str = "") -> str:
    return f"{PREFIX}{tc}-{STAMP}" + (f" {suffix}" if suffix else "")


def section_key(tc: str, extra: str = "") -> str:
    return f"{PREFIX}{tc}-{STAMP}{extra}".lower()


def save_attempt(driver: BGFieldsAdminPageB, publish: bool = True) -> dict:
    pinned(driver)
    driver.click_publish() if publish else driver.click_save_as_draft()
    result = {"went_through": driver.save_went_through(), "refused": driver.save_was_refused(),
              "evidence": driver.refusal_evidence(), "messages": driver.all_messages_text()}
    if result["went_through"]:
        expected = MSG_SAVED_AND_PUBLISHED if publish else "Draft saved."
        result["editbar"] = driver.success_messages(expected, 10.0)
        result["success_message_shown"] = any(expected in t for t in result["editbar"])
    else:
        result["editbar"] = driver.editbar_texts()
        result["success_message_shown"] = any(MSG_SAVED_AND_PUBLISHED in t for t in result["editbar"])
    return result


def create(driver: BGFieldsAdminPageB, registry: BRegistry, data: dict, tc: str, what: str,
           publish: bool = True) -> tuple[BGEntry | None, dict]:
    value = str(data[driver.entry_field])
    ids_before = driver.snapshot_ids()
    result: dict = {}
    entry = None
    try:
        driver.open_create_form_en()
        driver.fill_data(data)
        result = save_attempt(driver, publish)
        if result["went_through"]:
            driver.wait_arabic_saved(15.0)
        result["screenshot"] = driver.evidence(f"{tc}_{what}_after_save")
    finally:
        try:
            driver.last_identify_matches = []
            entry = driver.identify_created(value, ids_before)
            if entry:
                registry.track(entry)
            elif len(getattr(driver, "last_identify_matches", [])) > 1:
                # PRODUCT: one save created several identical NEW records (id diff + exact read-back,
                # all this save's own). Every one is tracked for the guarded teardown; the test goes
                # on with the first one and the duplication is reported.
                dupes = [driver.adopt(d) for d in driver.last_identify_matches]
                for dupe in dupes:
                    registry.track(dupe)
                entry = dupes[0]
                result["duplicates"] = [d.entry_id for d in dupes]
                record_finding(tc, "duplicate records from one save", slug=driver.slug, value=value,
                               ids=result["duplicates"], publish=publish,
                               screenshot=driver.evidence(f"{tc}_{what}_duplicates"))
        except Exception as exc:  # noqa: BLE001 — registration must not mask the result
            allure.attach(repr(exc), name=f"registration of {value!r} failed")
    attach(result, f"create {what}")
    return entry, result


def wait_status(driver: BGFieldsAdminPageB, entry: BGEntry, expected: tuple = (STATUS_PUBLISHED,)) -> str:
    return driver.wait_row_status(entry, expected, timeout=PUBLISH_CONFIRM_TIMEOUT)


def create_ok(driver, registry, data, tc, what, publish: bool = True, expect_status: tuple = (STATUS_PUBLISHED,)) -> BGEntry:
    entry, result = create(driver, registry, data, tc, what, publish)
    assert result.get("went_through"), f"saving {what} did not go through: {result}"
    assert entry is not None, f"{what} went through but is not identifiable as exactly one NEW record"
    if publish:
        status = wait_status(driver, entry, expect_status)
        assert status in expect_status, f"{entry.entry_value!r} never reached {expect_status} (last {status!r})"
    return entry


def require_active(driver: BGFieldsAdminPageB, entry: BGEntry) -> None:
    driver.open_entry_en(entry.code)
    stored = driver.active_status_stored()
    allure.attach(f"{entry.entry_value!r}: stored Active Status {stored!r}", name="Active Status precondition")
    if stored != "true":
        pytest.fail(f"PRECONDITION NOT MET — {entry.entry_value!r} stores Active Status {stored!r}; "
                    f"the public step was not run")


def section_data(tc: str, title_suffix: str = "section", order: int = SECTION_ORDER, **overrides) -> dict:
    title = name(tc, title_suffix)
    data = bg_data(SLUG_SECTION, title, section_key(tc), displayOrder=order)
    data["sectionTitle_ar"] = f"قسم اختبار {tc}"
    # a highlight card gives the row its rail, like the real sections 01-03 (a row
    # without photo/card renders full width, 1320px instead of the 760px article)
    data.update({"highlightCardEyebrow": "QCTEST card", "highlightCardEyebrow_ar": "بطاقة تجريبية",
                 "highlightCardHeading": f"QCTEST card {tc}", "highlightCardHeading_ar": "عنوان بطاقة تجريبي"})
    data.update(overrides)
    return data


def create_section(driver: BGFieldsAdminPageB, registry: BRegistry, tc: str, title_suffix: str = "section",
                   publish: bool = True, expect_status: tuple = (STATUS_PUBLISHED,), check_active: bool = True,
                   **overrides) -> dict:
    sec = driver_for(driver, SLUG_SECTION)
    data = section_data(tc, title_suffix, **overrides)
    entry = create_ok(sec, registry, data, tc, "section", publish, expect_status)
    if check_active and data.get("activeStatus", True):
        require_active(sec, entry)
    return {"entry": entry, "title": data["sectionTitle"], "title_ar": data["sectionTitle_ar"],
            "key": data["sectionKey"], "data": data, "driver": sec}


def edit_own(driver: BGFieldsAdminPageB, entry: BGEntry, tc: str, what: str, data: dict | None = None,
             typed: dict | None = None, rich_typed: dict | None = None, rich_source: dict | None = None,
             before_save=None, publish: bool = True) -> dict:
    """Re-opens ONE captured record, applies `data` (fill_data), `typed` ({key|key_ar: text}
    typed key by key), `rich_typed` / `rich_source` ({key|key_ar: text|html}), then Publish."""
    driver.open_own(entry)
    if data:
        driver.fill_data(data)
    for key, text in (typed or {}).items():
        driver.type_text(key[:-3] if key.endswith("_ar") else key, text, arabic=key.endswith("_ar"))
    for key, text in (rich_typed or {}).items():
        driver.type_rich_b(key[:-3] if key.endswith("_ar") else key, text, arabic=key.endswith("_ar"))
    for key, html in (rich_source or {}).items():
        driver.set_rich_source(key[:-3] if key.endswith("_ar") else key, html, arabic=key.endswith("_ar"))
    before = before_save(driver) if before_save else None
    result = save_attempt(driver, publish)
    result["before_save"] = before
    result["screenshot"] = driver.evidence(f"{tc}_{what}_after_publish")
    attach(result, f"edit {what}")
    return result


def sync_identity(driver: BGFieldsAdminPageB, registry: BRegistry, entry: BGEntry) -> BGEntry:
    """After an edit that may have changed the ENTRY field, re-read it and keep
    the registry's identity in step (so teardown can still verify it)."""
    driver.open_entry_en(entry.code)
    live = driver.entry_value().strip()
    if live != entry.entry_value:
        updated = replace(entry, entry_value=live)
        if updated.in_namespace():
            registry.track(updated)
            driver.owned_entry_ids.add(updated.entry_id)
            return updated
        # not verifiable any more: keep the old identity; teardown restores the original first
        registry.entries = [replace(e, entry_value=live) if e.entry_id == entry.entry_id else e
                            for e in registry.entries]
    return entry


def stored(driver: BGFieldsAdminPageB, entry: BGEntry) -> dict:
    driver.open_entry_en(entry.code)
    driver.wait_for_rich_text_loaded()
    data = driver.read_data()
    for key in ("sectionBody", "disclaimerBody"):
        if driver.slug == SLUG_SECTION:
            data[f"{key}_html"] = driver.rich_data(key)
            data[f"{key}_ar_html"] = driver.rich_data(key, arabic=True)
    return data


def refusal_points_at(result: dict, key: str) -> bool:
    return key in json.dumps(result.get("evidence", {}), ensure_ascii=False)


def required_message_for(result: dict, key: str) -> str:
    """The message(s) shown for `key` (inline owner match, else native, else all)."""
    evidence = result.get("evidence", {})
    owned = [o["text"] for o in evidence.get("field_error_owners", [])
             if {f"ObjectField_{key}", f"qc-ar-{key}"} & set(o.get("field", "").split(","))]
    native = [m for k, m in evidence.get("native_messages", {}).items() if key in k and m]
    return " | ".join(owned + native) or result.get("messages", "")


# ===========================================================================
# Public checks
# ===========================================================================
def style_mismatches(style: dict | None, font_px: str | None = None, weight: str | None = None,
                     color_hex: str | None = None, width: float | None = None, family: str = "Cairo",
                     width_tol: float = 2.0) -> list[str]:
    if not style:
        return ["element not rendered"]
    out = []
    if not font_family_contains(style.get("font_family", ""), family):
        out.append(f"font-family {style.get('font_family')!r} (expected {family})")
    if font_px and style.get("font_size") != font_px:
        out.append(f"font-size {style.get('font_size')} (expected {font_px})")
    if weight and str(style.get("font_weight")) != str(weight):
        out.append(f"font-weight {style.get('font_weight')} (expected {weight})")
    if color_hex and style.get("color") != hex_to_rgb(color_hex):
        out.append(f"color {style.get('color')} (expected {hex_to_rgb(color_hex)} = {color_hex})")
    if width is not None and abs(float(style.get("width", 0)) - width) > width_tol:
        out.append(f"box width {style.get('width')}px (expected {width}px)")
    return out


def rtl_aligned_right(style: dict | None) -> bool:
    return bool(style) and style.get("direction") == "rtl" and style.get("text_align") in ("start", "right")


def frontend_limit_check(anon_pages, tc: str, selector: str, expected: dict, row_title: dict | None = None) -> list[dict]:
    """Rule 6: the max-length value on the PUBLIC page, EN + AR, 1920 and 390.
    `expected` = {"en": text, "ar": text}; `row_title` = {"en": title, "ar": title}
    for a section field (None = hero/page-level element). Returns one result per
    (locale, viewport) with problems = [] when the text renders complete and the
    layout is intact."""
    results = []
    for locale in ("en", "ar"):
        for label, viewport in (("1920", DESKTOP), ("390", MOBILE)):
            view = anon_pages(viewport)
            view.open_page(locale)
            title = (row_title or {}).get(locale, "")
            if title and view.row_by_title(title) is None:
                view.poll_until(lambda m, t=title: any(r["title"] == t for r in m["rows"]), timeout=20.0, locale=locale)
            el = view.b_el(selector, title)
            layout = view.layout_report()
            problems = []
            want = " ".join(expected[locale].split())
            if not el:
                problems.append("element not rendered")
            else:
                got = " ".join(el["text"].split())
                if got != want:
                    problems.append(f"rendered text differs (len {len(got)} vs {len(want)}): {got[:80]!r}")
                if el["scroll_width"] > el["client_width"] + 1 and el["overflow"] != "visible":
                    problems.append(f"element clips its text (scrollWidth {el['scroll_width']} > clientWidth "
                                    f"{el['client_width']}, overflow {el['overflow']})")
                if el["text_overflow"] == "ellipsis" and el["scroll_width"] > el["client_width"] + 1:
                    problems.append("text truncated with an ellipsis")
                if el["right"] > el["viewport"] + 1 or el["left"] < -1:
                    problems.append(f"element box outside the viewport (left {el['left']}, right {el['right']}, "
                                    f"viewport {el['viewport']})")
            if layout.get("horizontal_scroll"):
                problems.append(f"page scrolls horizontally ({layout['scroll_width']} > {layout['client_width']})")
            shot = view.b_evidence(EVIDENCE_DIR, f"{tc}_public_{locale}_{label}")
            results.append({"locale": locale, "viewport": label, "problems": problems, "screenshot": shot,
                            "element": {k: el.get(k) for k in ("width", "height", "scroll_width", "client_width",
                                                               "overflow", "white_space", "left", "right")} if el else None})
    attach(results, f"{tc} frontend max-length check")
    for res in results:
        if res["problems"]:
            record_finding(tc, "char-limit frontend", locale=res["locale"], viewport=res["viewport"],
                           problems=res["problems"], screenshot=res["screenshot"])
    return results


# ===========================================================================
# REAL page 109104 — lock + snapshot + restore + diff
# ===========================================================================
_SNAPSHOT: dict = {}
DIFF_KEYS = ("pageKey", "eyebrowLabel", "pageTitle", "eyebrowLabel_ar", "pageTitle_ar", "heroDescription_html",
             "heroDescription_ar_html", "heroDescription_cke", "heroDescription_ar_cke", "heroBanner_file",
             "heroBanner_block", "heroBanner_href", "activeStatus")
PUBLIC_KEYS = ("hidden", "eyebrow", "title", "description_html", "hero_img", "disclaimer_html", "section_titles")


class RealPageHalt(AssertionError):
    pass


def _norm(value):
    if isinstance(value, str):
        return re.sub(r">\s+<", "><", " ".join(value.split())).strip()
    return value


def record_diff(before: dict, after: dict) -> list[str]:
    return [f"{k}: {before.get(k)!r} -> {after.get(k)!r}" for k in DIFF_KEYS if _norm(before.get(k)) != _norm(after.get(k))]


def public_state(browser, locale: str, shot: bool = True) -> dict:
    ctx = new_context(browser, viewport=DESKTOP, use_auth_state=False)
    try:
        view = VisasPublicViewB(ctx.new_page()).open_page(locale)
        model = view.model() or {}
        state = {k: model.get(k) for k in PUBLIC_KEYS if k != "section_titles"}
        # the REAL rows are the first three (orders 100-300; Official sources is nested into
        # the third). Other agents' QCTEST sections (>= 500) follow them; AR titles of those
        # rows do not carry the QCTEST prefix, so they are excluded by position.
        state["section_titles"] = [r["title"] for r in model.get("rows", [])][:len(REAL_ROW_TITLES)]
        if shot:
            state["screenshot"] = view.b_evidence(EVIDENCE_DIR, f"public_{locale}_{datetime.now():%H%M%S}")
        return state
    finally:
        ctx.close()


def public_diff(before: dict, after: dict) -> list[str]:
    return [f"public {k}: {before.get(k)!r} -> {after.get(k)!r}" for k in PUBLIC_KEYS
            if _norm(json.dumps(before.get(k), ensure_ascii=False)) != _norm(json.dumps(after.get(k), ensure_ascii=False))]


def halted() -> str:
    if os.path.exists(HALT_FILE):
        with open(HALT_FILE, encoding="utf-8") as handle:
            return handle.read()
    return ""


def _halt(reason: str, details) -> None:
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    payload = {"agent": AGENT, "at": datetime.now().isoformat(timespec="seconds"), "reason": reason,
               "details": details, "snapshot": _SNAPSHOT.get("path", "")}
    with open(HALT_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=1, default=str)
    attach(payload, "REAL PAGE HALT")
    raise RealPageHalt(f"REAL PAGE 109104 HALT — {reason}: {details} (snapshot {_SNAPSHOT.get('path')})")


def _ensure_snapshot(real: BGRealPageB, browser, record: dict) -> dict:
    if _SNAPSHOT:
        return _SNAPSHOT
    status = real.real_status()
    real.open_real_page()
    real.wait_for_rich_text_loaded()
    form_png = real.evidence("109104_B_snapshot_edit_form")
    public = {loc: public_state(browser, loc) for loc in ("en", "ar")}
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    path = os.path.join(SNAPSHOT_DIR, f"109104_B_{datetime.now():%Y%m%d_%H%M%S}.json")
    _SNAPSHOT.update({"record": record, "workflow_status": status, "public": public, "path": path,
                      "form_screenshot": form_png})
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_SNAPSHOT, handle, ensure_ascii=False, indent=1, default=str)
    attach(_SNAPSHOT, "109104 snapshot (B)")
    return _SNAPSHOT


def _open_and_read(real: BGRealPageB) -> dict:
    real.open_real_page()
    real.wait_for_rich_text_loaded()
    return real.read_page_record()


def restore_real_page(real: BGRealPageB, browser) -> list[str]:
    """Puts every changed field back, re-publishes, re-opens + diffs, checks
    the public page. Returns the list of remaining problems ([] = restored)."""
    snap = _SNAPSHOT["record"]
    steps: list[str] = []
    current = _open_and_read(real)
    diff = record_diff(snap, current)
    if diff:
        steps.append(f"restoring: {diff}")
        for key in ("eyebrowLabel", "pageTitle"):
            if current[key] != snap[key]:
                real.b_fill(key, snap[key])
            if current[f"{key}_ar"] != snap[f"{key}_ar"]:
                real.b_fill(key, snap[f"{key}_ar"], arabic=True)
        if _norm(current["heroDescription_cke"]) != _norm(snap["heroDescription_cke"]):
            real.b_rich_source("heroDescription", snap["heroDescription_cke"])
        if _norm(current["heroDescription_ar_cke"]) != _norm(snap["heroDescription_ar_cke"]):
            real.b_rich_source("heroDescription", snap["heroDescription_ar_cke"], arabic=True)
        if current["heroBanner_href"] != snap["heroBanner_href"] or current["heroBanner_file"] != snap["heroBanner_file"]:
            steps.append(f"banner re-selected: {real.b_select_original_banner()}")
        if current["activeStatus"] != snap["activeStatus"]:
            real.b_set_active(snap["activeStatus"] == "true")
        result = real.b_publish()
        steps.append(f"publish: went_through={result['went_through']} editbar={result['editbar']}")
        if not result["went_through"]:
            return [f"restore publish did not go through: {result}"] + steps
        current = _open_and_read(real)
    problems = record_diff(snap, current)
    status = real.wait_real_status((_SNAPSHOT["workflow_status"],), timeout=PUBLISH_CONFIRM_TIMEOUT)
    if status != _SNAPSHOT["workflow_status"]:
        problems.append(f"workflow status {status!r} != snapshot {_SNAPSHOT['workflow_status']!r}")
    for locale in ("en", "ar"):
        want = _SNAPSHOT["public"][locale]
        got = {}
        for attempt in range(8):
            got = public_state(browser, locale, shot=False)
            if not public_diff(want, got):
                break
        if public_diff(want, got):
            got = public_state(browser, locale, shot=True)
        problems += [f"{locale} {d}" for d in public_diff(want, got)]
    attach({"steps": steps, "problems": problems}, "109104 restore + diff")
    return problems


@contextlib.contextmanager
def real_page_session(browser, tc: str):
    """Lock -> login -> snapshot (once) -> pre-edit diff -> yield BGRealPageB ->
    finally restore + diff + public check -> unlock. Any restore problem halts."""
    reason = halted()
    if reason:
        pytest.fail(f"B real-page work is HALTED (restore problem earlier): {reason}")
    with real_page_lock(AGENT) as lock:
        ctx = new_context(browser, use_auth_state=False)
        try:
            real = BGRealPageB(ctx.new_page(), lock)
            _login_editor(real)
            real.open_list_all()
            user_id, _ = real.signed_in_user()
            if user_id != ROLE_USER_IDS[ROLE_EDITOR]:
                pytest.skip(f"PRECONDITION: Editor credentials sign in as userId {user_id!r}, not 156488")
            record = _open_and_read(real)
            first = not _SNAPSHOT
            _ensure_snapshot(real, browser, record)
            if not first:
                pre = record_diff(_SNAPSHOT["record"], record)
                if pre:
                    _halt(f"{tc}: record 109104 differs from the B snapshot BEFORE B edits", pre)
            body_error = None
            try:
                real.open_real_page()
                real.wait_for_rich_text_loaded()
                yield real
            except BaseException as exc:  # noqa: BLE001 — re-raised after the restore
                body_error = exc
            problems = []
            try:
                problems = restore_real_page(real, browser)
            except Exception as exc:  # noqa: BLE001
                problems = [f"restore raised {exc!r}"]
            if problems:
                _halt(f"{tc}: restore of 109104 left differences", problems)
            if body_error is not None:
                raise body_error
        finally:
            ctx.close()


def real_snapshot() -> dict:
    return _SNAPSHOT


def real_titles_in_order(model: dict) -> list[str]:
    return [r["title"] for r in model.get("rows", []) if not r["title"].upper().startswith("QCTEST")]


REAL_ROW_TITLES = [t for _, (_, _, t) in sorted(REAL_SECTIONS.items(), key=lambda kv: kv[1][0])
                   if t != "Official sources"]
