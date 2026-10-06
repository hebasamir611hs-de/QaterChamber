"""
cms/tests/visas_immigration/c_items_support.py — Agent C test-layer support
for PBI 130701 Visas & Immigration (suite 140362): checklist items, highlight
card + highlight items, sub-topic blocks.

Not a conftest (four agents share this folder): the test modules import the
fixtures below explicitly. Everything here orchestrates Page-Object calls —
no raw Playwright.

DATA RULES (user decision 2026-10-06, bg_rules.md ADDENDUM a):
  - Every record is OWN: a `QCTEST-130701-C-` BG Info Section with
    pageKey=visas-immigration, its own lower-case sectionKey and Display Order
    700 (Agent C band 700-799; 700 is the only 100-grid value in the band), plus
    QCTEST child items attached to that sectionKey. No real section / item is
    ever opened for edit.
  - Identity = list-id diff + exact read-back (BGAdminPage.identify_created);
    teardown deletes ONLY those captured ids through the guarded delete, in
    reverse creation order (children before their section). If a test emptied
    the ENTRY field of its own record and the app accepted it, the captured
    value is put back first so the guarded delete can re-verify identity.
  - Public checks only after the CMS shows Published AND the re-opened record
    stores Active Status ticked, in a fresh logged-out context.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.visas_immigration.bg_admin_page import (
    MSG_SAVED_AND_PUBLISHED,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    SLUG_SECTION,
    BGEntry,
    BGItemsAdminPageC,
    bg_data,
)
from core.web.browser import new_context
from core.web.design_tokens import font_family_contains, hex_to_rgb
from web.pages.visas_immigration.visas_immigration_page import VisasPublicViewC

AGENT = "C"
STAMP = datetime.now().strftime("%m%d%H%M")
SECTION_ORDER = 700
PUBLISH_CONFIRM_TIMEOUT = 120.0
PUBLIC_BUDGET_S = 5.0     # cms-profile.md: 5 s budget
PUBLIC_GRACE_S = 40.0     # keep polling past the budget to tell "slow" from "absent"
DESKTOP = (1920, 1080)
MOBILE = (390, 844)
EVIDENCE_DIR = os.path.join(BGItemsAdminPageC.EVIDENCE_ROOT, "130701_C")
FINDINGS_LOG = os.path.join(EVIDENCE_DIR, "findings.jsonl")
REQUIRED_RE = re.compile(r"required|mandatory|cannot be empty|must not be empty|is empty|fill", re.I)
MAXLEN_RE = re.compile(r"max|maximum|characters|too long|exceed|limit", re.I)

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)


# ===========================================================================
# Findings log (feeds the final report; one JSON object per line)
# ===========================================================================
def record_finding(tc: str, kind: str, **details) -> None:
    finding = {"tc": tc, "kind": kind, "at": datetime.now().isoformat(timespec="seconds"), **details}
    allure.attach(json.dumps(finding, ensure_ascii=False, indent=1, default=str), name=f"finding: {kind}")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(FINDINGS_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(finding, ensure_ascii=False, default=str) + "\n")


def shot_path(name: str) -> str:
    return os.path.join(EVIDENCE_DIR, re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")


# ===========================================================================
# Disposable registry + teardown
# ===========================================================================
class CRegistry:
    def __init__(self):
        self.entries: list[BGEntry] = []

    def track(self, entry: BGEntry) -> BGEntry:
        if not isinstance(entry, BGEntry) or not entry.in_namespace() or entry.prefix != "QCTEST-130701-C-":
            raise ValueError(f"{entry} is not a captured QCTEST-130701-C- record")
        if all(e.entry_id != entry.entry_id for e in self.entries):
            self.entries.append(entry)
        return entry


def editor_session(page) -> BGItemsAdminPageC:
    driver = BGItemsAdminPageC(page, SLUG_SECTION, AGENT)
    outcome = driver.login_as_role(ROLE_EDITOR)
    if outcome == "auth_failed":
        pytest.skip("PRECONDITION: Liferay refused the .env credentials for 'Site Content Editor'")
    driver.open_list_all()
    user_id, _ = driver.signed_in_user()
    if outcome != "ok" and user_id != ROLE_USER_IDS[ROLE_EDITOR]:
        pytest.fail(f"login as 'Site Content Editor' returned {outcome!r} and the session is userId {user_id!r}")
    if user_id != ROLE_USER_IDS[ROLE_EDITOR]:
        pytest.skip(f"PRECONDITION: Editor credentials sign in as userId {user_id!r}, not 156488")
    return driver


def teardown_entries(browser, entries: list[BGEntry], label: str) -> None:
    """Guarded delete of the captured ids, newest first, from a fresh Editor session."""
    if not entries:
        return
    ctx = new_context(browser, use_auth_state=False)
    done, failures = [], []
    try:
        page = ctx.new_page()
        base = BGItemsAdminPageC(page, SLUG_SECTION, AGENT)
        base.login_as_role(ROLE_EDITOR)
        base.open_list_all()
        if base.signed_in_user()[0] != ROLE_USER_IDS[ROLE_EDITOR]:
            failures.append("cleanup login as Site Content Editor failed")
        else:
            for entry in reversed(entries):
                tag = f"{entry.slug} {entry.entry_value!r} (id {entry.entry_id}, code {entry.code})"
                try:
                    driver = BGItemsAdminPageC(page, entry.slug, AGENT)
                    driver.adopt(entry)
                    driver.open_list_all()
                    if not driver.row_present(entry):
                        (done if driver.is_list_fully_expanded() else failures).append(
                            f"already gone: {tag}" if driver.is_list_fully_expanded()
                            else f"{tag}: not found and the list is NOT fully expanded")
                        continue
                    if not driver.restore_entry_value(entry):
                        failures.append(f"NOT removed {tag}: its ENTRY value could not be restored")
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
    with open(os.path.join(EVIDENCE_DIR, "teardown.log"), "a", encoding="utf-8") as handle:
        handle.write(f"[{datetime.now().isoformat(timespec='seconds')}] {label}\n  "
                     + "\n  ".join(done + failures) + "\n")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def c_disposable(browser):
    registry = CRegistry()
    yield registry
    teardown_entries(browser, registry.entries, "function")


@pytest.fixture
def anon_pages(browser):
    """Fresh logged-out contexts for every public read; `viewport` optional."""
    contexts = []

    def _make(viewport: tuple | None = None) -> VisasPublicViewC:
        ctx = new_context(browser, viewport=viewport or DESKTOP, use_auth_state=False)
        contexts.append(ctx)
        return VisasPublicViewC(ctx.new_page())

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# CMS orchestration
# ===========================================================================
def name(tc: str, suffix: str = "") -> str:
    return f"QCTEST-130701-C-{tc}-{STAMP}" + (f" {suffix}" if suffix else "")


def section_key(tc: str) -> str:
    return f"qctest-130701-c-{tc}-{STAMP}".lower()


def save_attempt(driver: BGItemsAdminPageC, publish: bool = True) -> dict:
    user_id, _ = driver.signed_in_user()
    assert user_id == ROLE_USER_IDS[ROLE_EDITOR], f"the session is now userId {user_id!r}, not the Editor"
    driver.click_publish() if publish else driver.click_save_as_draft()
    result = {"went_through": driver.save_went_through(), "refused": driver.save_was_refused(),
              "evidence": driver.refusal_evidence(), "messages": driver.all_messages_text()}
    if result["went_through"]:
        expected = MSG_SAVED_AND_PUBLISHED if publish else "Draft saved."
        result["editbar"] = driver.success_messages(expected, 10.0)
        result["success_message_shown"] = any(expected in t for t in result["editbar"])
        driver.wait_arabic_saved(15.0)
    return result


def create(driver: BGItemsAdminPageC, registry: CRegistry, data: dict, tc: str, what: str,
           publish: bool = True, before_save=None) -> tuple[BGEntry | None, dict]:
    """Creates ONE record (fills `data`, optional `before_save(driver)`), registers it
    for teardown by list-id diff, returns (entry, save evidence)."""
    value = str(data[driver.entry_field])
    ids_before = driver.snapshot_ids()
    result: dict = {}
    entry = None
    try:
        driver.open_create_form_en()
        driver.fill_data(data)
        if before_save:
            before_save(driver)
        result = save_attempt(driver, publish)
        result["screenshot"] = driver.evidence(f"{tc}_{what}_after_save")
    finally:
        try:
            entry = driver.identify_created(value, ids_before)
            if entry:
                registry.track(entry)
            else:
                extra = capture_all_new(driver, registry, value, ids_before)
                if extra:
                    result["duplicates_created"] = [e.entry_id for e in extra]
                    record_finding(tc, "duplicate records created by ONE save", what=what, value=value,
                                   entry_ids=[e.entry_id for e in extra], codes=[e.code for e in extra],
                                   screenshot=result.get("screenshot"))
        except Exception as exc:  # noqa: BLE001 — registration must not mask the result
            allure.attach(repr(exc), name=f"registration of {value!r} failed")
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"create {what}")
    _log_save(tc, f"create {what}", result)
    return entry, result


def capture_all_new(driver: BGItemsAdminPageC, registry: CRegistry, value: str, ids_before: set) -> list[BGEntry]:
    """When ONE save produced SEVERAL rows with this test's exact, stamp-unique
    ENTRY value (ids absent before the save, not QCDEMO-), capture every one of
    them so teardown removes them all through the guarded delete."""
    driver.open_list_all()
    fresh = [r for r in driver.list_rows() if r["entry_id"] not in ids_before and r["code"]
             and not r["code"].upper().startswith("QCDEMO-") and r["title"].strip() == value.strip()]
    if len(fresh) < 2:
        return []
    out = []
    for row in fresh:
        entry = BGEntry(slug=driver.slug, entry_value=row["title"].strip(), entry_id=row["entry_id"],
                        code=row["code"], prefix=driver.prefix)
        driver.adopt(entry)
        out.append(registry.track(entry))
    return out


def create_ok(driver, registry, data, tc, what, publish: bool = True, before_save=None) -> BGEntry:
    entry, result = create(driver, registry, data, tc, what, publish, before_save)
    assert result.get("went_through"), f"saving {what} did not go through: {result}"
    assert entry is not None, f"{what} went through but is not identifiable as exactly one NEW record"
    if publish:
        wait_published(driver, entry)
    return entry


def wait_published(driver: BGItemsAdminPageC, entry: BGEntry) -> None:
    status = driver.wait_row_status(entry, (STATUS_PUBLISHED,), timeout=PUBLISH_CONFIRM_TIMEOUT)
    assert status == STATUS_PUBLISHED, f"{entry.entry_value!r} never reached Published (last {status!r})"


def require_active(driver: BGItemsAdminPageC, entry: BGEntry) -> None:
    driver.open_entry_en(entry.code)
    stored = driver.active_status_stored()
    allure.attach(f"{entry.entry_value!r}: stored Active Status {stored!r}", name="Active Status precondition")
    if stored != "true":
        pytest.fail(f"PRECONDITION NOT MET — {entry.entry_value!r} stores Active Status {stored!r}; "
                    f"the public step was not run")


def section_data(tc: str, **overrides) -> dict:
    title = name(tc, "section")
    data = bg_data(SLUG_SECTION, title, section_key(tc), displayOrder=SECTION_ORDER)
    data["sectionTitle_ar"] = f"{title} ع"
    data.update(overrides)
    return data


def create_section(driver: BGItemsAdminPageC, registry: CRegistry, tc: str, **overrides) -> dict:
    """Own QCTEST section on pageKey visas-immigration (order 700), published + active."""
    sec = driver_for(driver, SLUG_SECTION)
    data = section_data(tc, **overrides)
    entry = create_ok(sec, registry, data, tc, "section")
    require_active(sec, entry)
    return {"entry": entry, "title": data["sectionTitle"], "title_ar": data["sectionTitle_ar"],
            "key": data["sectionKey"], "data": data}


def driver_for(driver: BGItemsAdminPageC, slug: str) -> BGItemsAdminPageC:
    other = BGItemsAdminPageC(driver.page, slug, AGENT)
    other.owned_entry_ids = driver.owned_entry_ids   # one owned-id set per session
    return other


def edit(driver: BGItemsAdminPageC, entry: BGEntry, tc: str, what: str, data: dict | None = None,
         rich_raw: dict | None = None) -> dict:
    result = driver.edit_and_publish(entry, data or {}, rich_raw)
    result["screenshot"] = driver.evidence(f"{tc}_{what}_after_publish")
    if result["went_through"]:
        result["editbar"] = driver.success_messages(MSG_SAVED_AND_PUBLISHED, 10.0)
        result["success_message_shown"] = any(MSG_SAVED_AND_PUBLISHED in t for t in result["editbar"])
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"edit {what}")
    _log_save(tc, f"edit {what}", result)
    return result


def _log_save(tc: str, what: str, result: dict) -> None:
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    summary = {"tc": tc, "what": what, "went_through": result.get("went_through"), "refused": result.get("refused"),
               "messages": result.get("messages"), "field_error_owners": result.get("evidence", {}).get(
                   "field_error_owners"), "native": result.get("evidence", {}).get("native_messages"),
               "screenshot": result.get("screenshot")}
    with open(os.path.join(EVIDENCE_DIR, "saves.jsonl"), "a", encoding="utf-8") as handle:
        handle.write(json.dumps(summary, ensure_ascii=False, default=str) + "\n")


def stored(driver: BGItemsAdminPageC, entry: BGEntry) -> dict:
    driver.open_entry_en(entry.code)
    driver.wait_for_rich_text_loaded()
    return driver.read_data()


def refusal_points_at(result: dict, key: str) -> bool:
    blob = json.dumps(result.get("evidence", {}), ensure_ascii=False)
    return key in blob


# ===========================================================================
# Public orchestration
# ===========================================================================
def public_row(anon_pages, title: str, predicate, locale: str = "en", viewport: tuple | None = None,
               timeout: float = PUBLIC_GRACE_S) -> tuple[VisasPublicViewC, dict | None, float, bool]:
    """Polls a fresh logged-out page until the row titled `title` satisfies
    `predicate(row)`. Returns (view, row, seconds, held)."""
    view = anon_pages(viewport)
    held, seconds = view.c_poll_row(title, predicate, timeout, locale)
    row = view.row_by_title(title)
    return view, row, seconds, held


def style_mismatches(style: dict, font_px: str | None = None, weight: str | None = None,
                     color_hex: str | None = None, width: float | None = None, family: str = "Cairo",
                     width_tol: float = 2.0) -> list[str]:
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


def rtl_aligned_right(style: dict) -> bool:
    return style.get("direction") == "rtl" and style.get("text_align") in ("start", "right")


def overflow_problems(style: dict) -> list[str]:
    """Element-level cut/overflow evidence for a char-limit render check."""
    out = []
    if style.get("scroll_width", 0) > style.get("client_width", 0) + 1:
        out.append(f"content wider than its box (scrollWidth {style['scroll_width']} > clientWidth "
                   f"{style['client_width']}, overflow {style.get('overflow')})")
    if style.get("text_overflow") == "ellipsis":
        out.append("text-overflow: ellipsis")
    if style.get("right", 0) > style.get("viewport", 10 ** 6) + 1 or style.get("left", 0) < -1:
        out.append(f"box spills outside the viewport (left {style.get('left')}, right {style.get('right')}, "
                   f"viewport {style.get('viewport')})")
    return out


def frontend_limit_check(anon_pages, tc: str, title_en: str, title_ar: str, selector: str,
                         value_en: str, value_ar: str, row_ready) -> dict:
    """Rule 6: renders the max-length value EN + AR at 1920 and 390 and
    collects cut-off / overflow evidence. Returns {combo: {...}}."""
    report = {}
    for locale, title, value in (("en", title_en, value_en), ("ar", title_ar, value_ar)):
        for vp_name, viewport in (("1920", DESKTOP), ("390", MOBILE)):
            view, row, seconds, held = public_row(anon_pages, title, row_ready, locale, viewport)
            combo = f"{locale}_{vp_name}"
            png = view.c_evidence(shot_path(f"{tc}_limit_{combo}"))
            styles = view.c_styles(title, selector) or []
            match = [s for s in styles if " ".join(s["text"].split()) == " ".join(value.split())]
            target = match[0] if match else (styles[0] if styles else {})
            layout = view.layout_report()
            problems = []
            if not held:
                problems.append("row/value never rendered")
            if not match:
                problems.append(f"no element renders the full value (rendered: "
                                f"{[s['text'][:60] + '…(' + str(len(s['text'])) + ')' for s in styles]})")
            problems += overflow_problems(target) if target else []
            if layout.get("horizontal_scroll"):
                problems.append(f"page scrolls horizontally (scrollWidth {layout['scroll_width']} > "
                                f"{layout['client_width']})")
            report[combo] = {"problems": problems, "screenshot": png, "rendered_len": len(target.get("text", "")),
                             "expected_len": len(value), "box": {k: target.get(k) for k in
                                                                 ("width", "scroll_width", "client_width",
                                                                  "left", "right", "white_space")},
                             "layout": layout, "seconds": round(seconds, 1)}
    allure.attach(json.dumps(report, ensure_ascii=False, indent=1, default=str), name=f"{tc} frontend limit check")
    bad = {k: v for k, v in report.items() if v["problems"]}
    if bad:
        record_finding(tc, "LOW char-limit frontend render problem", combos=bad)
    return report


def ar_text(length: int, head: str = "اختبار-الحد-") -> str:
    """An Arabic string of exactly `length` characters (unbroken, like the EN boundary values)."""
    return (head + "ب" * length)[:length]
