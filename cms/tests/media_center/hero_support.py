"""
cms/tests/media_center/hero_support.py — HERO agent test-layer support for
PBI 130709 (Media Center Hero, singleton QCDEMO-130709-HERO-MAIN).

Not a conftest (four agents share this folder): the hero test module imports
what it needs explicitly. Everything here orchestrates Page-Object calls.

HERO RULE (user decision 2026-10-07): the live hero is edited ONLY inside
`hero_session()`:
  lock -> Editor login -> read the stored record (API GET) -> it must equal the
  run BASELINE (scratchpad/hero/baseline_snapshot.json) before any edit ->
  public EN/AR snapshot -> yield -> finally: diff, restore (exact snapshot body
  through the authoring page's own PUT endpoint), re-read + diff, status must be
  Published, public EN/AR must match the snapshot again -> restore diff written
  to reports/mc130709/HERO/restore_<tc>.json and attached. A remaining diff
  writes HERO_HALT.json and fails every later hero test.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
from datetime import datetime

import allure
import pytest

from cms.pages.media_center.mc_hero_admin_page import (
    EDITOR_USER_ID,
    EVIDENCE_ROOT,
    HERO_ID,
    ROLE_EDITOR,
    MCHeroAdminPage,
    MCHeroPublicView,
    hero_lock,
    record_diff,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

SCRATCH = os.getenv(
    "QC_MC_HERO_SCRATCH_DIR",
    r"C:\Users\HP\AppData\Local\Temp\claude\d--Qatar-Chamber-QaterChamber-main"
    r"\de2eae66-6f02-4a22-8869-a22476b25d22\scratchpad",
)
BASELINE_PATH = os.path.join(SCRATCH, "hero", "baseline_snapshot.json")
HALT_FILE = os.path.join(SCRATCH, "hero", "HERO_HALT.json")
FINDINGS_LOG = os.path.join(EVIDENCE_ROOT, "findings.jsonl")
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "hero")
DESKTOP = (1920, 1080)
PUBLIC_TIMEOUT_S = 60.0
PUBLIC_KEYS = ("label", "headline", "desc", "placeholder", "bg_file", "section_dir")


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------
def attach(obj, name: str) -> str:
    text = json.dumps(obj, ensure_ascii=False, indent=1, default=str)
    allure.attach(text, name=name)
    os.makedirs(os.path.join(EVIDENCE_ROOT, "facts"), exist_ok=True)
    path = os.path.join(EVIDENCE_ROOT, "facts", re.sub(r"[^\w.-]+", "_", name)[:100] + ".json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def record_finding(tc: str, kind: str, **details) -> None:
    finding = {"tc": tc, "kind": kind, "at": datetime.now().isoformat(timespec="seconds"), **details}
    allure.attach(json.dumps(finding, ensure_ascii=False, indent=1, default=str), name=f"finding: {kind}")
    os.makedirs(EVIDENCE_ROOT, exist_ok=True)
    with open(FINDINGS_LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(finding, ensure_ascii=False, default=str) + "\n")


def admin_shot(driver: MCHeroAdminPage, name: str) -> str:
    return driver.evidence(name)


# ---------------------------------------------------------------------------
# Public reads (fresh logged-out context every time)
# ---------------------------------------------------------------------------
def public_flat(state: dict) -> dict:
    """The comparable part of a public hero state."""
    def _t(key):
        node = state.get(key) or {}
        return " ".join((node.get("text") or "").split()) if node else None
    return {"label": _t("label"), "headline": _t("headline"), "desc": _t("desc"),
            "placeholder": state.get("placeholder"), "bg_file": state.get("bg_file"),
            "section_dir": state.get("section_dir")}


def public_read(browser, locale: str, predicate=None, timeout: float = PUBLIC_TIMEOUT_S,
                shot: str | None = None) -> dict:
    """Opens the public Media Center page in a fresh anonymous context; polls
    with fresh reloads until predicate(state) (if given). Returns
    {state, flat, seconds, ok, screenshot}."""
    ctx = new_context(browser, viewport=DESKTOP, use_auth_state=False)
    try:
        view = MCHeroPublicView(ctx.new_page())
        if predicate is None:
            view.open_page(locale)
            state, secs, ok = view.state(), 0.0, True
        else:
            state, secs, ok = view.poll(predicate, locale, timeout=timeout)
        out = {"state": state, "flat": public_flat(state), "seconds": round(secs, 1), "ok": ok, "screenshot": ""}
        if shot:
            out["screenshot"] = view.evidence(shot)
        return out
    finally:
        ctx.close()


def layout_problems(state: dict, key: str, expected_text: str | None = None) -> list[str]:
    """Clipping / overflow / truncation checks for one public hero element."""
    node = state.get(key)
    problems = []
    if not node:
        return [f"{key} not rendered"]
    if expected_text is not None and " ".join(node["text"].split()) != " ".join(expected_text.split()):
        problems.append(f"{key} text differs (len {len(node['text'])} vs {len(expected_text)})")
    if node["scroll_width"] > node["client_width"] + 1 and node["overflow"] not in ("visible", "visible visible"):
        problems.append(f"{key} clips horizontally (scrollWidth {node['scroll_width']} > {node['client_width']})")
    if node["scroll_height"] > node["client_height"] + 1 and "hidden" in node["overflow"]:
        problems.append(f"{key} clips vertically (scrollHeight {node['scroll_height']} > {node['client_height']})")
    if node["text_overflow"] == "ellipsis" and node["scroll_width"] > node["client_width"] + 1:
        problems.append(f"{key} truncated with an ellipsis")
    if node["right"] > state["viewport"] + 1 or node["left"] < -1:
        problems.append(f"{key} box outside the viewport ({node['left']:.0f}..{node['right']:.0f})")
    if state["doc_scroll_width"] > state["doc_client_width"] + 1:
        problems.append(f"page scrolls horizontally ({state['doc_scroll_width']} > {state['doc_client_width']})")
    return problems


def placeholder_problems(state: dict, expected: str) -> list[str]:
    """A placeholder renders inside the input: compare the text width with the box."""
    problems = []
    if state.get("placeholder") != expected:
        problems.append(f"placeholder differs: {state.get('placeholder')!r}")
    node = state.get("input")
    if not node:
        return problems + ["search input not rendered"]
    if state.get("placeholder_text_width") and state["placeholder_text_width"] > node["client_width"]:
        problems.append(f"placeholder text ({state['placeholder_text_width']:.0f}px) wider than the input "
                        f"({node['client_width']}px) - cut off")
    if state["doc_scroll_width"] > state["doc_client_width"] + 1:
        problems.append("page scrolls horizontally")
    return problems


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
def login_editor(driver: MCHeroAdminPage) -> None:
    outcome = driver.login_as_role(ROLE_EDITOR)
    if outcome == "auth_failed":
        pytest.skip("PRECONDITION: Liferay refused the .env credentials for 'Site Content Editor'")
    if outcome != "ok":
        pytest.fail("login as 'Site Content Editor' neither succeeded nor showed Liferay's refusal banner")
    user_id, _ = driver.signed_in_user()
    if user_id != EDITOR_USER_ID:
        pytest.skip(f"PRECONDITION: Editor credentials sign in as userId {user_id!r}, not {EDITOR_USER_ID}")


def _baseline() -> dict:
    with open(BASELINE_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def halted() -> str:
    if os.path.exists(HALT_FILE):
        with open(HALT_FILE, encoding="utf-8") as handle:
            return handle.read()
    return ""


def _halt(tc: str, problems: list[str]) -> None:
    payload = {"tc": tc, "at": datetime.now().isoformat(timespec="seconds"), "problems": problems}
    with open(HALT_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=1)
    attach(payload, "HERO HALT")
    raise AssertionError(f"HERO RESTORE FAILED ({tc}): {problems}")


class HeroSession:
    def __init__(self, driver: MCHeroAdminPage, snapshot: dict, public: dict, tc: str):
        self.driver = driver
        self.snapshot = snapshot
        self.public = public  # {"en": flat, "ar": flat}
        self.tc = tc


def restore(session: HeroSession, browser) -> dict:
    """Puts the snapshot back and proves it (record diff + status + public EN/AR)."""
    driver, snap = session.driver, session.snapshot
    report: dict = {"tc": session.tc, "at": datetime.now().isoformat(timespec="seconds")}
    driver.open_hero()
    before = driver.api_get()
    report["diff_before_restore"] = record_diff(snap, before)
    if report["diff_before_restore"]:
        report["put_status"] = driver.restore_exact(snap)
    # The PUT runs through the editorial workflow: the stored status reads
    # "pending" for a short while before the Editor's privileged path
    # approves it (live 2026-10-08) — poll, never assume.
    seen = {"after": driver.api_get()}

    def _restored() -> bool:
        seen["after"] = driver.api_get()
        return not record_diff(snap, seen["after"])

    try:
        wait_until(_restored, timeout=180.0, poll=5.0)
    except WaitTimeoutError:
        pass
    after = seen["after"]
    report["diff_after_restore"] = record_diff(snap, after)
    report["diff_vs_run_baseline"] = record_diff(_baseline(), after)
    driver.open_list()
    report["row_status"] = driver.row_status()
    report["row_count"] = driver.row_count()
    report["public"] = {}
    for locale in ("en", "ar"):
        want = session.public[locale]
        res = public_read(browser, locale, lambda s, w=want: public_flat(s) == w, timeout=90.0)
        report["public"][locale] = {"ok": res["ok"], "seconds": res["seconds"],
                                    "diff": {k: (want.get(k), res["flat"].get(k)) for k in want
                                             if want.get(k) != res["flat"].get(k)}}
    problems = list(report["diff_after_restore"]) + list(report["diff_vs_run_baseline"])
    if report["row_status"] != "Published":
        problems.append(f"row status {report['row_status']!r} (snapshot Published)")
    if report["row_count"] != 1:
        problems.append(f"{report['row_count']} rows on the hero page (expected 1)")
    for locale in ("en", "ar"):
        if not report["public"][locale]["ok"]:
            problems.append(f"public {locale} differs: {report['public'][locale]['diff']}")
    report["problems"] = problems
    os.makedirs(EVIDENCE_ROOT, exist_ok=True)
    path = os.path.join(EVIDENCE_ROOT, f"restore_{session.tc}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=1, default=str)
    allure.attach(json.dumps(report, ensure_ascii=False, indent=1, default=str), name="hero restore + diff")
    return report


@contextlib.contextmanager
def hero_session(browser, tc: str, locale: str = "en"):
    """lock -> login -> baseline check -> snapshot -> yield -> restore + diff."""
    reason = halted()
    if reason:
        pytest.fail(f"HERO work is HALTED (an earlier restore failed): {reason}")
    with hero_lock() as lock:
        ctx = new_context(browser, viewport=DESKTOP, use_auth_state=False)
        try:
            driver = MCHeroAdminPage(ctx.new_page(), lock)
            login_editor(driver)
            driver.open_list()
            snapshot = driver.api_get()
            pre = record_diff(_baseline(), snapshot)
            if pre:
                _halt(tc, [f"hero differs from the run baseline BEFORE {tc} edits"] + pre)
            if str(snapshot.get("id")) != HERO_ID:
                pytest.fail("hero record id mismatch")
            public = {loc: public_read(browser, loc)["flat"] for loc in ("en", "ar")}
            session = HeroSession(driver, snapshot, public, tc)
            attach({"record": snapshot, "public": public}, f"{tc} hero snapshot")
            body_error = None
            try:
                driver.open_hero(locale)
                yield session
            except BaseException as exc:  # noqa: BLE001 — re-raised after the restore
                body_error = exc
            try:
                if locale != "en":
                    from config.settings import control_panel_url  # noqa: PLC0415
                    driver.open(control_panel_url("/c/portal/update_language?languageId=en_US&redirect=%2Fhome"))
                report = restore(session, browser)
                problems = report["problems"]
            except Exception as exc:  # noqa: BLE001
                problems = [f"restore raised {exc!r}"]
            if problems:
                _halt(tc, problems)
            if body_error is not None:
                raise body_error
        finally:
            ctx.close()


# ---------------------------------------------------------------------------
# Shared case shapes
# ---------------------------------------------------------------------------
def editbar_names_published(driver: MCHeroAdminPage) -> str:
    bar = driver.editing_bar_text()
    return bar if ("Media Center" in bar and "(Published)" in bar) else ""


def refusal_names(result: dict, driver: MCHeroAdminPage, key: str, label: str) -> bool:
    text = " ".join([result.get("messages", ""), " ".join(driver.errors_for(key)),
                     json.dumps(result.get("evidence", {}), ensure_ascii=False)])
    return label in text or key in text
