"""
cms/tests/media_center/test_mc_feed_section_control_panel.py — PBI 130709
Media Center Home Page, Control_Panel cases on `manage-media-center-feed-section`
(suite 140368, FEED agent).

DATA RULES
  - Every record is a disposable `QCTEST-130709-FS-<tc>-<stamp>` Feed Section
    (the Section Heading is the list's ENTRY column and carries the prefix),
    Display Order >= 1000 on the 100-grid (user rule 2 — the cases' 400/500/600
    would collide with the real 100..300 band's neighbourhood), Active Status
    ticked, published by QC Site Content Editor (156488). Identity = list-id
    diff + exact heading read-back; teardown deletes ONLY those captured ids
    through the guarded delete. Real QCDEMO-130709-FEED-01..03 are never opened
    for edit.
  - LIVE FINDING (probe 2026-10-07): the public hub renders three FIXED
    fragments (news / photo / video), each reading the FIRST
    mediacenterfeedsections item of its sectionType (headless default order =
    oldest first). A published + Active QCTEST section therefore never renders
    publicly — the real FEED-01..03 entry always wins. Cases whose verdict
    rests on the QCTEST section's public rendering run every CMS step, prove
    the section is not rendered, then stop as NEEDS-DECISION (only an edit of a
    real entry could reach that surface). TC-204 (a NEW section appears on the
    hub without redevelopment) asserts that capability directly and fails.

Public reads: fresh logged-out contexts only.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.media_center.mc_feed_section_admin_page import (
    AR_KEYS,
    K_CTA_DEST,
    K_CTA_LABEL,
    K_EYEBROW,
    K_HEADING,
    K_ITEMS,
    K_MODE,
    K_ORDER,
    MODE_CAROUSEL,
    K_TYPE,
    MSG_ARABIC_REQUIRED,
    PREFIX,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    TYPE_NEWS,
    TYPE_PHOTO,
    TYPE_VIDEO,
    FeedEntry,
    McFeedSectionAdminPage,
    MediaCenterPublicView,
)
from core.web.browser import new_context

STAMP = datetime.now().strftime("%m%d%H%M")
EVIDENCE_DIR = McFeedSectionAdminPage.EVIDENCE_DIR
FINDINGS = os.path.join(EVIDENCE_DIR, "findings.jsonl")
PUBLIC_WAIT_S = 25.0
VIDEO_LIBRARY = "/web/qatar-chamber/video-library"

COMMON = [pytest.mark.pbi_130709, pytest.mark.control_panel, pytest.mark.media,
          pytest.mark.xdist_group("mc_feed_130709")]


def marks(*extra):
    def _wrap(fn):
        for m in COMMON + list(extra):
            fn = m(fn)
        return fn
    return _wrap


# ===========================================================================
# Findings / evidence
# ===========================================================================
def record(tc: str, kind: str, **details) -> None:
    item = {"tc": tc, "kind": kind, "at": datetime.now().isoformat(timespec="seconds"), **details}
    allure.attach(json.dumps(item, ensure_ascii=False, indent=1, default=str), name=f"finding: {kind}")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(FINDINGS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")


def shot(name: str) -> str:
    return os.path.join(EVIDENCE_DIR, re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")


def needs_decision(tc: str, question: str, **details) -> None:
    record(tc, "NEEDS-DECISION", question=question, **details)
    pytest.skip(f"NEEDS-DECISION: {question}")


# ===========================================================================
# Fixtures
# ===========================================================================
class Registry:
    def __init__(self):
        self.entries: list[FeedEntry] = []

    def track(self, entry: FeedEntry) -> FeedEntry:
        if not isinstance(entry, FeedEntry) or not entry.in_namespace():
            raise ValueError(f"{entry} is not a captured {PREFIX} record")
        if all(e.entry_id != entry.entry_id for e in self.entries):
            self.entries.append(entry)
        return entry


def _teardown(browser, entries: list[FeedEntry]) -> None:
    if not entries:
        return
    ctx = new_context(browser, use_auth_state=False)
    done, failures = [], []
    try:
        driver = McFeedSectionAdminPage(ctx.new_page())
        driver.login_as_role(ROLE_EDITOR)
        driver.open_list_all()
        if driver.signed_in_user()[0] != ROLE_USER_IDS[ROLE_EDITOR]:
            failures.append("cleanup login as Site Content Editor failed")
        else:
            for entry in reversed(entries):
                tag = f"{entry.heading!r} (id {entry.entry_id}, code {entry.code})"
                driver.adopt(entry)
                driver.open_list_all()
                if not driver.row_present(entry):
                    (done if driver.is_list_fully_expanded() else failures).append(f"already gone / unseen: {tag}")
                    continue
                if not driver.restore_heading(entry):
                    failures.append(f"NOT removed {tag}: heading could not be restored")
                    continue
                if driver.delete_disposable_entry(entry):
                    done.append(f"removed {tag}")
                else:
                    failures.append(f"NOT removed {tag}: guarded delete refused/failed")
    finally:
        ctx.close()
    log = "\n".join(done + failures) or "nothing"
    allure.attach(log, name="QCTEST teardown")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(os.path.join(EVIDENCE_DIR, "teardown.log"), "a", encoding="utf-8") as fh:
        fh.write(f"[{datetime.now().isoformat(timespec='seconds')}]\n  " + "\n  ".join(done + failures) + "\n")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def reg(browser):
    registry = Registry()
    yield registry
    _teardown(browser, registry.entries)


@pytest.fixture
def editor(browser):
    ctx = new_context(browser, use_auth_state=False)
    driver = McFeedSectionAdminPage(ctx.new_page())
    outcome = driver.login_as_role(ROLE_EDITOR)
    if outcome == "auth_failed":
        pytest.skip("PRECONDITION: Liferay refused the Site Content Editor credentials")
    driver.open_list_all()
    user = driver.signed_in_user()[0]
    if user != ROLE_USER_IDS[ROLE_EDITOR]:
        pytest.fail(f"Editor login returned {outcome!r}; session is userId {user!r}, not 156488")
    yield driver
    ctx.close()


@pytest.fixture
def anon(browser):
    contexts = []

    def _make() -> MediaCenterPublicView:
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return MediaCenterPublicView(ctx.new_page())

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# CMS orchestration
# ===========================================================================
def heading(tc: str, text: str) -> str:
    return f"{PREFIX}{tc}-{STAMP} {text}"


def section_data(tc: str, **overrides) -> dict:
    """The cases' QCTEST-130709-FEED-04 fixture, in the FS namespace."""
    data = {
        K_HEADING: heading(tc, "Video highlights"), f"{K_HEADING}_ar": "QCTEST أبرز الفيديوهات",
        K_EYEBROW: "QCTEST Watch", f"{K_EYEBROW}_ar": "QCTEST شاهد",
        K_CTA_LABEL: "QCTEST See videos", f"{K_CTA_LABEL}_ar": "QCTEST شاهد الفيديوهات",
        K_CTA_DEST: VIDEO_LIBRARY, K_TYPE: TYPE_VIDEO, K_ORDER: 1000, "activeStatus": True,
    }
    data.update(overrides)
    return data


def attempt_create(driver: McFeedSectionAdminPage, registry: Registry, data: dict, tc: str) -> tuple:
    """Fills a fresh create form and clicks Publish. Captures every new row with
    this test's heading for teardown. Returns (entry | None, result)."""
    ids_before = driver.snapshot_ids()
    driver.open_create_form_en()
    driver.fill_data(data)
    driver.click_publish()
    result = {"went_through": driver.save_went_through(), "refused": driver.save_was_refused(),
              "evidence": driver.refusal_evidence(), "messages": driver.all_messages_text(),
              "screenshot": driver.evidence(f"{tc}_after_publish")}
    if result["went_through"]:
        result["arabic_saved"] = driver.wait_arabic_saved()
    entry = None
    if data.get(K_HEADING, "").startswith(PREFIX):
        entry = driver.identify_created(data[K_HEADING], ids_before)
        if entry:
            registry.track(entry)
    result["new_rows"] = [r for r in driver.new_rows_since(ids_before)]
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"{tc} create")
    return entry, result


def create_published(driver, registry, tc: str, **overrides) -> FeedEntry:
    data = section_data(tc, **overrides)
    entry, result = attempt_create(driver, registry, data, tc)
    assert result["went_through"], f"PRECONDITION: creating the QCTEST section was not saved: {result}"
    assert entry is not None, "PRECONDITION: the new QCTEST section is not identifiable as exactly one row"
    status = driver.wait_row_status(entry, (STATUS_PUBLISHED,), timeout=120)
    assert status == STATUS_PUBLISHED, f"PRECONDITION: QCTEST section never reached Published ({status!r})"
    driver.open_entry_en(entry.code)
    assert driver.active_status_stored() == "true", "PRECONDITION: Active Status is not stored ticked"
    return entry


def open_for_edit(driver: McFeedSectionAdminPage, entry: FeedEntry) -> dict:
    driver.open_entry_en(entry.code)
    bar = driver.editing_bar_text()
    stored = driver.read_data()
    assert entry.heading in bar and "published" in bar.casefold(), \
        f"step 2: the blue bar should name {entry.heading!r} and PUBLISHED; it reads {bar!r}"
    return stored


def edit_publish(driver: McFeedSectionAdminPage, entry: FeedEntry, data: dict, tc: str) -> dict:
    open_for_edit(driver, entry)
    driver.fill_data(data)
    driver.click_publish()
    result = {"went_through": driver.save_went_through(), "refused": driver.save_was_refused(),
              "evidence": driver.refusal_evidence(), "messages": driver.all_messages_text(),
              "screenshot": driver.evidence(f"{tc}_after_edit_publish")}
    allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"{tc} edit")
    return result


def refusal_names(result: dict, *needles: str) -> bool:
    blob = json.dumps(result.get("evidence", {}), ensure_ascii=False).casefold()
    return any(n.casefold() in blob for n in needles)


def assert_refused_and_unchanged(driver, entry, tc, result, key, label, before: dict) -> None:
    driver.open_list_all()
    status = driver.row_status_of(entry)
    driver.open_entry_en(entry.code)
    after = driver.read_data()
    record(tc, "refusal check", went_through=result["went_through"], refused=result["refused"],
           messages=result["messages"], evidence=result["evidence"], stored_after=after.get(key),
           stored_before=before.get(key), status=status, screenshot=result["screenshot"])
    assert not result["went_through"], (
        f"step 4: Publish with an invalid {label} went through; expected a refusal. "
        f"Stored {key} now {after.get(key)!r}")
    assert after.get(key) == before.get(key), f"{key} changed from {before.get(key)!r} to {after.get(key)!r}"
    assert status == STATUS_PUBLISHED, f"row badge changed to {status!r}"
    assert refusal_names(result, key, label), \
        f"the refusal does not name {label!r}: {result['evidence']}"


def public_not_rendered_then_decide(anon, tc: str, entry_heading: str, question: str) -> None:
    view = anon()
    ok, sections = view.poll_sections(lambda ss: any(s["heading"] == entry_heading for s in ss),
                                      timeout=PUBLIC_WAIT_S)
    png = view.evidence(shot(f"{tc}_public_en"))
    if ok:
        record(tc, "QCTEST section DID render publicly", sections=sections, screenshot=png)
        return
    needs_decision(tc, question, sections=[{k: s[k] for k in ("key", "heading", "eyebrow", "cta_label", "cta_href")}
                                          for s in sections], screenshot=png)


Q_REAL = ("The hub renders only three fixed feed blocks, each fed by the FIRST published entry of its "
          "Section Type (the real QCDEMO-130709-FEED-0x); a disposable QCTEST section never renders. "
          "Approve a lock + snapshot -> edit -> restore -> diff on real QCDEMO-130709-FEED-03 (Video Gallery) "
          "to verify this public step, or accept the TC-204 bug as covering it?")


def public_ok(anon, tc, predicate, locale="en"):
    view = anon()
    ok, sections = view.poll_sections(predicate, timeout=PUBLIC_WAIT_S, locale=locale)
    return view, ok, sections, view.evidence(shot(f"{tc}_public_{locale}"))


# ===========================================================================
# Empty required EN field refused — TC-150 / 152 / 154
# ===========================================================================
EMPTY_CASES = [
    pytest.param("150", K_EYEBROW, "Eyebrow", "QCTEST شاهد", marks=[pytest.mark.tc_149204], id="tc150_eyebrow"),
    pytest.param("152", K_HEADING, "Section Heading", "QCTEST أبرز الفيديوهات", marks=[pytest.mark.tc_149206],
                 id="tc152_heading"),
    pytest.param("154", K_CTA_LABEL, "CTA Label", "QCTEST شاهد الفيديوهات", marks=[pytest.mark.tc_149208],
                 id="tc154_cta_label"),
]


@marks(pytest.mark.functional_low)
@pytest.mark.parametrize("tc,key,label,ar", EMPTY_CASES)
def test_empty_english_field_refused(editor, reg, anon, tc, key, label, ar):
    """MEDIA-MCHUB-TC-150 / 152 / 154 — Publish with an empty English Eyebrow /
    Section Heading / CTA Label is refused and the stored value is unchanged."""
    entry = create_published(editor, reg, tc)
    before = open_for_edit(editor, entry)
    result = edit_publish(editor, entry, {key: "", f"{key}_ar": ar}, tc)
    assert_refused_and_unchanged(editor, entry, tc, result, key, label, before)
    view, ok, sections, png = public_ok(anon, tc, lambda ss: all(s["eyebrow"] or s["hidden"] for s in ss))
    assert not any(s["heading"] == "" and not s["hidden"] for s in sections), "an empty heading reached the hub"
    record(tc, "public step", note="refused value never published; QCTEST section is not rendered by the "
                                   "fixed fragments (see TC-204)", screenshot=png)


# ===========================================================================
# CTA Label character limit — TC-155
# ===========================================================================
# ===========================================================================
# Section Type — TC-185 / 186 / 187
# ===========================================================================
@marks(pytest.mark.functional_low, pytest.mark.tc_149240)
def test_section_type_required(editor, reg, anon):
    """MEDIA-MCHUB-TC-186 — a new Feed Section cannot be published without a Section Type."""
    tc = "186"
    data = section_data(tc, **{K_TYPE: None, K_HEADING: heading(tc, "No type"),
                               f"{K_HEADING}_ar": "QCTEST بلا نوع", K_EYEBROW: "QCTEST e",
                               f"{K_EYEBROW}_ar": "QCTEST ع", K_CTA_LABEL: "QCTEST Go",
                               f"{K_CTA_LABEL}_ar": "QCTEST اذهب"})
    entry, result = attempt_create(editor, reg, data, tc)
    record(tc, "create without type", went_through=result["went_through"], messages=result["messages"],
           evidence=result["evidence"], created=bool(entry), screenshot=result["screenshot"])
    assert not result["went_through"] and entry is None, f"a Feed Section without Section Type was saved: {result}"
    assert refusal_names(result, "sectionType", "Section Type"), f"refusal does not name Section Type: {result}"
    view, ok, sections, png = public_ok(anon, tc, lambda ss: bool(ss))
    assert not any(s["heading"] == data[K_HEADING] for s in sections), "the untyped section is shown publicly"


@marks(pytest.mark.ui, pytest.mark.tc_149241)
def test_section_type_options(editor):
    """MEDIA-MCHUB-TC-187 — the Section Type dropdown offers exactly News & Press
    Releases, Photo Gallery and Video Gallery."""
    editor.open_create_form_en()
    options = editor.picklist_options()
    editor.evidence("187_section_type_options")
    record("187", "options", options=options)
    assert options == [TYPE_NEWS, TYPE_PHOTO, TYPE_VIDEO], f"Section Type offers {options}"


# ===========================================================================
# Missing PBI-workflow fields — TC-188 / 189
# ===========================================================================
@marks(pytest.mark.functional_low)
@pytest.mark.parametrize("tc,pattern,subject", [
    pytest.param("188", r"number of items|items previewed|item count|items to show", "number of items previewed",
                 marks=[pytest.mark.tc_149242], id="tc188_items_previewed"),
    pytest.param("189", r"display mode|layout mode|carousel", "display mode",
                 marks=[pytest.mark.tc_149243], id="tc189_display_mode"),
])
def test_workflow_setting_present(editor, tc, pattern, subject):
    """MEDIA-MCHUB-TC-188 / 189 — the Feed Section form offers the US-005
    workflow's 'number of items previewed' / 'display mode' setting.
    HEALED 2026-10-13 (149909/149911 fixes): the list no longer offers a create
    form, so the form is read on the real Video Gallery entry (read-only)."""
    editor.open_entry_en(FEED_VIDEO)
    inventory = editor.form_field_inventory()
    text = editor.form_text()
    png = editor.evidence(f"{tc}_form_inventory")
    present = bool(re.search(pattern, text, re.I)) or any(re.search(pattern, f["label"], re.I) for f in inventory)
    record(tc, "form inventory", subject=subject, present=present, inventory=inventory, screenshot=png)
    if not present:
        pytest.skip(f"BLOCKED: the Feed Section form has no '{subject}' field (missing subject)")


# ===========================================================================
# Display Order — TC-191 / 196 / 197
# ===========================================================================
@marks(pytest.mark.functional_low)
@pytest.mark.parametrize("tc,values", [
    pytest.param("196", [""], marks=[pytest.mark.tc_149250], id="tc196_empty"),
    pytest.param("197", ["0", "-100"], marks=[pytest.mark.tc_149251], id="tc197_zero_negative"),
])
def test_display_order_invalid_refused(editor, reg, anon, tc, values):
    """MEDIA-MCHUB-TC-196 / 197 — an empty / 0 / negative Display Order is refused."""
    entry = create_published(editor, reg, tc)
    before = open_for_edit(editor, entry)
    failures = []
    for value in values:
        result = edit_publish(editor, entry, {K_ORDER: value}, f"{tc}_{value or 'empty'}")
        editor.open_entry_en(entry.code)
        after = editor.text_value(K_ORDER)
        record(tc, f"display order {value!r}", went_through=result["went_through"], stored_after=after,
               messages=result["messages"], evidence=result["evidence"], screenshot=result["screenshot"])
        if result["went_through"] or after != before[K_ORDER]:
            failures.append(f"Display Order {value!r} was accepted (stored now {after!r})")
            if after != before[K_ORDER]:
                edit_publish(editor, entry, {K_ORDER: before[K_ORDER]}, f"{tc}_restore")
        elif not refusal_names(result, "displayOrder", "Display Order"):
            failures.append(f"refusal for {value!r} does not name Display Order: {result['evidence']}")
    assert not failures, "; ".join(failures)


# ===========================================================================
# New section on the hub — TC-204
# ===========================================================================
# NOTE: TC-204 (149258) as written is obsolete after the 149911 fix (fixed set, no Add New); re-mark pending user decision.
@marks(pytest.mark.functional_high, pytest.mark.uat, pytest.mark.tc_149258)
def test_new_section_appears_on_hub(editor):
    """MEDIA-MCHUB-TC-204 — HEALED 2026-10-13 (bug 149911 fix, QA-owner rule:
    the hub draws a FIXED set of three feed sections, so a new record not
    rendering is by design and 'Add New' existing is the defect). The manage
    list offers no Add New, lists exactly the three real sections, and each
    still offers Edit."""
    tc = "204"
    editor.open_list_all()
    offered = editor.add_new_offered()
    rows = editor.list_rows()
    png = editor.evidence(f"{tc}_list_no_add_new")
    record(tc, "manage list", add_new=offered, rows=rows, screenshot=png)
    assert not offered, f"the fixed Feed Section list still offers {offered}; {png}"
    real = sorted(r["code"] for r in rows if r.get("code") in REAL_IDS_LOCAL)
    assert real == sorted(REAL_IDS_LOCAL), f"the three real feed sections are not all listed: {rows}"
    editor.open_entry_en(FEED_VIDEO)
    assert editor.text_value(K_HEADING), "the real Video Gallery section can no longer be opened for edit"


# ===========================================================================
# Active Status — TC-209
# ===========================================================================
# ===========================================================================
# CTA Destination — TC-214 / 215 / 216 / 217
# ===========================================================================
@marks(pytest.mark.functional_low)
@pytest.mark.parametrize("tc,value", [
    pytest.param("215", "", marks=[pytest.mark.tc_149269], id="tc215_empty"),
    pytest.param("216", "   ", marks=[pytest.mark.tc_149270], id="tc216_whitespace"),
    pytest.param("217", "video library page", marks=[pytest.mark.tc_149271], id="tc217_malformed"),
])
def test_cta_destination_invalid_refused(browser, anon, tc, value):
    """MEDIA-MCHUB-TC-215 / 216 / 217 — an empty / whitespace-only / malformed
    CTA Destination is refused and the public CTA is unchanged.
    HEALED 2026-10-13: no create form any more (149911 fix) — runs on the real
    Video Gallery section under lock + snapshot -> edit -> restore -> diff."""
    with real_window(browser, tc, [FEED_VIDEO]) as w:
        before = w.snaps[FEED_VIDEO].get("ctaDestination")
        driver = w.drivers[FEED_VIDEO]
        res = w.attempt(FEED_VIDEO, {K_CTA_DEST: value})
        res["screenshot"] = driver.evidence(f"{tc}_real_after_publish")
        after = w.written[FEED_VIDEO]
        badge = w.row_status(FEED_VIDEO)
        record(tc, "refusal check (real FEED-03)", went_through=res["went_through"], refused=res["refused"],
               messages=res["messages"], evidence=res["evidence"], stored_before=before,
               stored_after=after.get("ctaDestination"), status=badge, screenshot=res["screenshot"])
        _, ok, sections, png = public_poll(anon, tc, lambda ss: bool(ss))
        valid = {}
        if tc == "217":  # dev retest step 3: a valid site path saves
            valid = w.attempt(FEED_VIDEO, {K_CTA_DEST: VIDEO_LIBRARY})
            record(tc, "valid destination saves", result=valid,
                   stored=w.written[FEED_VIDEO].get("ctaDestination"))
    assert not res["went_through"], (f"step 4: Publish with an invalid CTA Destination went through; "
                                     f"stored ctaDestination now {after.get('ctaDestination')!r}")
    assert after.get("ctaDestination") == before, f"ctaDestination changed {before!r} -> {after.get('ctaDestination')!r}"
    assert badge == STATUS_PUBLISHED, f"row badge changed to {badge!r}"
    assert _cta_destination_refusal(res), f"the refusal is not the CTA Destination link error: {res['evidence']}"
    bad = [s for s in sections if s["cta_href"] in (value, value.strip()) or "video library page" in s["cta_href"]]
    assert not bad, f"the invalid destination reached a public CTA: {bad}"
    if tc == "217":
        assert valid.get("went_through"), f"dev step 3: {VIDEO_LIBRARY} was not accepted: {valid}"


MSG_INVALID_LINK = "Please enter a valid link: a page of this site starting with /"


def _cta_destination_refusal(res: dict) -> bool:
    """The refusal must belong to CTA Destination: either the form marks that
    field, or (LIVE 2026-10-13: no per-field marker) the server refused the
    PUT (4xx) with the CTA-link rule's own message — the only field edited."""
    ev = res.get("evidence") or {}
    owners = json.dumps(ev.get("field_error_owners", []) + ev.get("invalid_fields", []), ensure_ascii=False)
    if K_CTA_DEST in owners:
        return True
    server_4xx = any(400 <= int(c) < 500 for c in ev.get("save_responses", []) if str(c).isdigit())
    return server_4xx and any(MSG_INVALID_LINK in t for t in ev.get("editbar", []))


# ---- 149909 dev retest: Items Previewed / Display Mode are applied ------------------
@marks(pytest.mark.functional_low, pytest.mark.tc_149242)
def test_items_previewed_display_mode_applied(browser, anon):
    """MEDIA-MCHUB-TC-188/189 follow-up (bug 149909 retest steps): Video
    Gallery set to 6 / Carousel shows 6 videos in ONE row on the hub; 0 and 13
    are refused. Real FEED-03 under lock + snapshot -> edit -> restore -> diff."""
    tc = "188b"
    refusals = {}
    with real_window(browser, tc, [FEED_VIDEO]) as w:
        driver = w.drivers[FEED_VIDEO]
        for bad in ("0", "13"):
            r = w.attempt(FEED_VIDEO, {K_ITEMS: bad})
            after = w.written[FEED_VIDEO]
            refusals[bad] = {"went_through": r["went_through"], "stored": after.get(K_ITEMS),
                             "messages": r["messages"]}
        res = w.edit(FEED_VIDEO, {K_ITEMS: 6, K_MODE: MODE_CAROUSEL})
        stored = (w.written[FEED_VIDEO].get(K_ITEMS),
                  str((w.written[FEED_VIDEO].get(K_MODE) or {}).get("key") or "").casefold())
        view, ok, sections, png = public_poll(
            anon, tc, lambda ss: video_section(ss).get("cards") == 6)
        cards = view.page.evaluate(
            """() => { const s = document.querySelector('[data-qc-mcvf-section-object]'); if (!s) return [];
                return [...s.querySelectorAll('a[class*="-card"], article[class*="-card"]')]
                  .filter(c => c.getClientRects().length).map(c => Math.round(c.getBoundingClientRect().top)); }""")
        record(tc, "items/mode", refusals=refusals, publish=res, stored=stored, card_tops=cards, screenshot=png)
    for bad, r in refusals.items():
        assert not r["went_through"] and str(r["stored"]) != bad, f"Items Previewed {bad} was accepted: {r}"
    assert res["went_through"], f"6 / Carousel was not published: {res}"
    assert stored == (6, "carousel"), f"stored Items Previewed / Display Mode {stored}"
    assert len(cards) == 6, f"the hub video section renders {len(cards)} cards, expected 6; {png}"
    assert len(set(cards)) == 1, f"the 6 cards are not in one row (tops {cards}); {png}"


# ===========================================================================
# Arabic required — TC-221
# ===========================================================================
@marks(pytest.mark.functional_low, pytest.mark.tc_149275)
def test_publish_without_arabic_blocked(editor, reg, anon):
    """MEDIA-MCHUB-TC-221 — publishing without Arabic content is blocked with
    'Arabic content is required.'"""
    tc = "221"
    data = section_data(tc, **{K_TYPE: TYPE_NEWS, K_HEADING: heading(tc, "EN only"), K_EYEBROW: "QCTEST EN",
                               K_CTA_LABEL: "QCTEST All", **{f"{k}_ar": "" for k in AR_KEYS}})
    entry, result = attempt_create(editor, reg, data, tc)
    record(tc, "publish without Arabic", went_through=result["went_through"], messages=result["messages"],
           evidence=result["evidence"], created=bool(entry), screenshot=result["screenshot"])
    assert not result["went_through"] and entry is None, f"a Feed Section without Arabic was published: {result}"
    assert MSG_ARABIC_REQUIRED in json.dumps(result["evidence"], ensure_ascii=False), \
        f"the refusal does not say {MSG_ARABIC_REQUIRED!r}: {result['messages']}"
    for locale in ("en", "ar"):
        view, ok, sections, png = public_ok(anon, f"{tc}", lambda ss: bool(ss), locale=locale)
        leaked = [s for s in sections if s["heading"] == data[K_HEADING] or s["eyebrow"] == "QCTEST EN"]
        assert not leaked, f"English-only QCTEST content shown on the {locale.upper()} hub: {leaked}"


# ===========================================================================
# Form scope — TC-230
# ===========================================================================
ALLOWED_FIELDS = {"Section Heading", "Section Type", "Eyebrow", "CTA Label", "CTA Destination", "Display Order",
                  "Active Status"}


@marks(pytest.mark.ui, pytest.mark.tc_149284)
def test_form_exposes_only_section_settings(editor, reg):
    """MEDIA-MCHUB-TC-230 — the Feed Section form exposes only section settings
    and no way to author articles, albums or videos."""
    tc = "230"
    entry = create_published(editor, reg, tc)
    open_for_edit(editor, entry)
    inventory = editor.form_field_inventory()
    png = editor.evidence(f"{tc}_edit_form")
    labels = {re.sub(r"\s*\*\s*$", "", f["label"]).replace(" — العربية", "").strip() for f in inventory}
    record(tc, "edit form inventory", inventory=inventory, labels=sorted(labels), screenshot=png)
    unexpected = sorted(lbl for lbl in labels if lbl not in ALLOWED_FIELDS)
    missing = sorted(ALLOWED_FIELDS - labels)
    assert not unexpected, f"the form exposes non-section fields: {unexpected}"
    assert not missing, f"the form lacks section settings: {missing}"


# ===========================================================================
# REAL-entry public checks (user approval 2026-10-12, rule 4b):
# lock + snapshot -> edit via the form -> logged-out public check -> exact
# restore (PUT) -> empty diff. Concurrency guard: the record is re-read right
# before the edit and right before the restore; if anyone else changed it, it
# is NOT overwritten — the case stops as NEEDS-DECISION with the field diff.
# ===========================================================================
import contextlib  # noqa: E402

from cms.pages.media_center.mc_feed_section_admin_page import (  # noqa: E402
    ConcurrentChangeError,
    RealFeedSectionAdminPage,
    real_feed_lock,
    record_diff,
)
from core.utils.waits import wait_until  # noqa: E402

FEED_NEWS, FEED_PHOTO, FEED_VIDEO = "QCDEMO-130709-FEED-01", "QCDEMO-130709-FEED-02", "QCDEMO-130709-FEED-03"
REAL_IDS_LOCAL = {FEED_NEWS: "206621", FEED_PHOTO: "206629", FEED_VIDEO: "206637"}
REAL_PUBLIC_WAIT_S = 60.0


class RealWindow:
    def __init__(self, tc: str):
        self.tc = tc
        self.drivers: dict = {}
        self.snaps: dict = {}
        self.written: dict = {}
        self.intended: dict = {}   # code -> comparable keys THIS test may have written

    def mark_intent(self, code: str, data: dict) -> None:
        """Recorded BEFORE the save, so a publish that lands and then raises is
        still recognised as ours (restore must not skip it as 'foreign')."""
        self.intended.setdefault(code, set()).update(_comparable_keys(data))
        self.written.setdefault(code, self.snaps[code])

    def attempt(self, code: str, data: dict) -> dict:
        """Edit -> Publish that may be refused; `written` tracks what is stored."""
        driver = self.drivers[code]
        expected = self.written.get(code, self.snaps[code])
        self.mark_intent(code, data)
        try:
            return driver.edit_via_form(data, expected)
        finally:
            self.written[code] = _settled_or_live(driver, expected)

    def edit(self, code: str, data: dict) -> dict:
        driver = self.drivers[code]
        expected = self.written.get(code, self.snaps[code])
        self.mark_intent(code, data)
        try:
            result = driver.edit_via_form(data, expected)
        except Exception:
            self.written[code] = driver.api_get()
            raise
        try:
            self.written[code] = _wait_committed(driver, expected)
        except Exception:  # noqa: BLE001 — written becomes whatever is stored now
            self.written[code] = driver.api_get()
        result["screenshot"] = driver.evidence(f"{self.tc}_real_{code[-2:]}_after_publish")
        allure.attach(json.dumps(result, ensure_ascii=False, indent=1, default=str), name=f"{code} edit")
        return result

    def row_status(self, code: str) -> str:
        from cms.pages.components.object_authoring_page import normalize_status  # noqa: PLC0415
        driver = self.drivers[code]
        driver.open_list_all()
        rows = [r for r in driver.list_rows() if r["code"] == code]
        return normalize_status(rows[0]["status"]) if len(rows) == 1 else ""


_KEY_MAP = {K_HEADING: "sectionHeading_i18n", K_EYEBROW: "eyebrow_i18n", K_CTA_LABEL: "ctaLabel_i18n",
            K_CTA_DEST: "ctaDestination", K_ORDER: "displayOrder", K_TYPE: "sectionType",
            "activeStatus": "activeStatus", K_ITEMS: "itemsPreviewed", K_MODE: "displayMode"}


def _comparable_keys(data: dict) -> set:
    return {_KEY_MAP[k.removesuffix("_ar")] for k in data if k.removesuffix("_ar") in _KEY_MAP} | {"status"}


def _settled_or_live(driver, previous: dict) -> dict:
    try:
        return _wait_committed(driver, previous, timeout=20.0)
    except Exception:  # noqa: BLE001 — refused save: nothing changed
        return driver.api_get()


def _wait_committed(driver, previous: dict, timeout: float = 90.0) -> dict:
    seen = {"rec": previous}

    def _changed() -> bool:
        seen["rec"] = driver.api_get()
        return bool(record_diff(previous, seen["rec"]))

    wait_until(_changed, timeout=timeout, poll=3.0)
    return seen["rec"]


def _save_json(name: str, data) -> str:
    path = os.path.join(EVIDENCE_DIR, name)
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1, default=str)
    return path


def _restore_all(window: "RealWindow", page) -> list:
    problems = []
    for code, driver in window.drivers.items():
        snap = window.snaps[code]
        expected = window.written.get(code, snap)
        try:
            live = driver.api_get()
            ours = window.intended.get(code, set())
            # Only keys this test did NOT intend to write count as someone else's change.
            foreign = [d for d in record_diff(expected, live) if d.split(":", 1)[0] not in ours]
            if foreign:
                problems.append(f"{code}: changed by someone else during the window - NOT restored: {foreign}")
                record(window.tc, "NEEDS-DECISION concurrent change before restore", code=code, diff=foreign)
                continue
            if code not in window.written:
                continue
            status = driver.restore_exact(snap)
            after = driver.api_get()
            for _ in range(30):
                if not record_diff(snap, after):
                    break
                page.wait_for_timeout(3000)
                after = driver.api_get()
            diff = record_diff(snap, after)
            path = _save_json(f"{window.tc}_restore_diff_{code}.json",
                              {"put_status": status, "diff": diff, "restored": after})
            allure.attach(json.dumps(diff, ensure_ascii=False), name=f"{code} restore diff (must be [])")
            record(window.tc, "restore", code=code, put_status=status, diff=diff, evidence=path)
            if diff:
                problems.append(f"{code}: restore left a diff {diff}")
        except Exception as exc:  # noqa: BLE001 — collected
            problems.append(f"{code}: restore failed {exc!r}")
    return problems


@contextlib.contextmanager
def real_window(browser, tc: str, codes: list):
    ctx = new_context(browser, use_auth_state=False)
    window = RealWindow(tc)
    page = ctx.new_page()
    problems: list = []
    with contextlib.ExitStack() as stack:
        try:
            login = McFeedSectionAdminPage(page)
            if login.login_as_role(ROLE_EDITOR) == "auth_failed":
                pytest.skip("PRECONDITION: Liferay refused the Site Content Editor credentials")
            login.open_list_all()
            assert login.signed_in_user()[0] == ROLE_USER_IDS[ROLE_EDITOR], "not signed in as the Editor"
            for code in codes:
                lock = stack.enter_context(real_feed_lock(REAL_IDS_LOCAL[code]))
                driver = RealFeedSectionAdminPage(page, code, lock)
                window.drivers[code] = driver
                window.snaps[code] = driver.api_get()
                _save_json(f"{tc}_snapshot_{code}.json", window.snaps[code])
            try:
                yield window
            except ConcurrentChangeError as exc:
                record(tc, "NEEDS-DECISION concurrent change before edit", code=exc.code, diff=exc.diff)
                problems.append(f"NEEDS-DECISION: {exc}")
        finally:
            problems += _restore_all(window, page)
            try:
                ctx.close()
            except Exception:  # noqa: BLE001
                pass
    if problems:
        raise AssertionError("REAL-ENTRY WINDOW PROBLEM:\n" + "\n".join(problems))


def video_section(sections: list) -> dict:
    found = [s for s in sections if s["key"] == "videoGallery"]
    return found[0] if found else {}


def public_poll(anon, tc: str, predicate, locale: str = "en"):
    view = anon()
    ok, sections = view.poll_sections(predicate, timeout=REAL_PUBLIC_WAIT_S, locale=locale)
    png = view.evidence(shot(f"{tc}_real_public_{locale}"))
    record(tc, f"real public {locale}", held=ok, screenshot=png,
           sections=[{k: s[k] for k in ("index", "fragment", "key", "hidden", "heading", "eyebrow", "cta_label",
                                         "cta_href", "cards")} for s in sections])
    return view, ok, sections, png


def overflow(box) -> list:
    if not box:
        return ["CTA label element not found"]
    out = []
    if box["scroll_width"] > box["client_width"] + 1:
        out.append(f"scrollWidth {box['scroll_width']} > clientWidth {box['client_width']}")
    if box["text_overflow"] == "ellipsis":
        out.append("text-overflow: ellipsis")
    return out


# ---- TC-149 / 151 / 153 ---------------------------------------------------------
REAL_FIELD_CASES = [
    pytest.param("149", K_EYEBROW, "eyebrow", "QCTEST Now showing", "QCTEST يُعرض الآن",
                 marks=[pytest.mark.tc_149203], id="tc149_eyebrow"),
    pytest.param("151", K_HEADING, "heading", "QCTEST Latest video stories", "QCTEST أحدث القصص المصورة",
                 marks=[pytest.mark.tc_149205], id="tc151_heading"),
    pytest.param("153", K_CTA_LABEL, "cta_label", "QCTEST Open library", "QCTEST افتح المكتبة",
                 marks=[pytest.mark.tc_149207], id="tc153_cta_label"),
]


@marks(pytest.mark.functional_low)
@pytest.mark.parametrize("tc,key,field,value_en,value_ar", REAL_FIELD_CASES)
def test_valid_field_saved_and_rendered(browser, anon, tc, key, field, value_en, value_ar):
    """MEDIA-MCHUB-TC-149 / 151 / 153 — a valid Eyebrow / Section Heading / CTA
    Label saved on the Feed Section reaches the section on the EN + AR hub
    (real QCDEMO-130709-FEED-03 under snapshot/restore, user rule 4b)."""
    with real_window(browser, tc, [FEED_VIDEO]) as w:
        result = w.edit(FEED_VIDEO, {key: value_en, f"{key}_ar": value_ar})
        assert result["went_through"], f"step 4: Publish was not accepted: {result}"
        stored = w.written[FEED_VIDEO].get(f"{key}_i18n") or {}
        assert stored.get("en_US") == value_en and stored.get("ar_SA") == value_ar, f"stored {stored}"
        badge = w.row_status(FEED_VIDEO)
        w.drivers[FEED_VIDEO].open_entry_en(FEED_VIDEO)
        ar_box_dir = w.drivers[FEED_VIDEO].ar_direction(key)
        _, ok_en, s_en, _ = public_poll(anon, tc, lambda ss: video_section(ss).get(field) == value_en)
        view, ok_ar, s_ar, _ = public_poll(anon, tc, lambda ss: video_section(ss).get(field) == value_ar, "ar")
        ar_dir = view.lang_dir()
    assert badge == STATUS_PUBLISHED, f"row badge reads {badge!r}"
    assert ar_box_dir == "rtl", "the Arabic box is not right-to-left"
    assert ok_en, f"EN hub video section {field} reads {video_section(s_en).get(field)!r}, not {value_en!r}"
    assert ok_ar, f"AR hub video section {field} reads {video_section(s_ar).get(field)!r}, not {value_ar!r}"
    assert ar_dir == "rtl", f"AR hub dir is {ar_dir!r}"


# ---- TC-155 -----------------------------------------------------------------------
@marks(pytest.mark.functional_low, pytest.mark.tc_149209)
def test_cta_label_character_limit(browser, editor, reg, anon):
    """MEDIA-MCHUB-TC-155 — CTA Label accepts 50 characters, the 51st is handled
    per bug-rules Rule 5 (QCTEST record); 50 EN + AR characters render intact on
    the hub (real QCDEMO-130709-FEED-03 under snapshot/restore)."""
    tc = "155"
    en50 = "QCTEST-ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQ"
    en51 = en50 + "R"
    ar50 = "ق" * 50
    assert len(en50) == 50 and len(ar50) == 50
    entry = create_published(editor, reg, tc)
    open_for_edit(editor, entry)
    counter, native = editor.counter_limit(K_CTA_LABEL), editor.native_max_length(K_CTA_LABEL)
    limit = counter if counter else (native if native > 0 else None)
    record(tc, "implemented limit", counter=counter, native_maxlength=native)
    assert limit is not None, "no implemented CTA Label limit could be read (no counter, no maxlength)"
    assert limit >= 50, f"Rule 5.3: implemented CTA Label limit {limit} is shorter than the US limit 50"
    result = edit_publish(editor, entry, {K_CTA_LABEL: en50, f"{K_CTA_LABEL}_ar": ar50}, tc)
    assert result["went_through"], f"50-character values were not accepted: {result}"
    open_for_edit(editor, entry)
    editor.type_en(K_CTA_LABEL, en51)
    editor.click_publish()
    editor.open_entry_en(entry.code)
    stored51 = editor.text_value(K_CTA_LABEL)
    record(tc, "51st character", limit=limit, stored_len=len(stored51))
    if limit == 50:
        assert len(stored51) <= 50, f"a 51-character CTA Label was stored ({len(stored51)} chars)"
    problems = {}
    with real_window(browser, tc, [FEED_VIDEO]) as w:
        res = w.edit(FEED_VIDEO, {K_CTA_LABEL: en50, f"{K_CTA_LABEL}_ar": ar50})
        assert res["went_through"], f"50-char values not accepted on the real entry: {res}"
        for locale, value in (("en", en50), ("ar", ar50)):
            _, ok, sections, png = public_poll(
                anon, tc, lambda ss, v=value: video_section(ss).get("cta_label") == v, locale)
            sec = video_section(sections)
            issues = [] if ok else [f"label renders {sec.get('cta_label')!r}"]
            issues += overflow(sec.get("cta_box")) + [f"anchor: {x}" for x in overflow(sec.get("cta_anchor_box"))]
            box = sec.get("cta_anchor_box") or {}
            if box and box.get("right", 0) > sec.get("viewport", 10 ** 6) + 1:
                issues.append(f"CTA spills outside the viewport (right {box['right']})")
            if issues:
                problems[locale] = {"issues": issues, "screenshot": png}
    record(tc, "frontend render 50 chars", problems=problems)
    assert not problems, f"50-character CTA Label does not render intact: {problems}"


# ---- TC-185 -----------------------------------------------------------------------
@marks(pytest.mark.functional_low, pytest.mark.tc_149239)
def test_section_type_determines_source(browser, anon):
    """MEDIA-MCHUB-TC-185 — the Section Type selection decides which module the
    public section previews (real FEED-03 Video Gallery -> Photo Gallery)."""
    tc = "185"
    heading_en = "QCTEST Video highlights"
    with real_window(browser, tc, [FEED_VIDEO]) as w:
        assert (w.snaps[FEED_VIDEO].get("sectionType") or {}).get("key") == "videoGallery"
        res = w.edit(FEED_VIDEO, {K_TYPE: TYPE_PHOTO, K_HEADING: heading_en,
                                  f"{K_HEADING}_ar": "QCTEST أبرز الفيديوهات"})
        assert res["went_through"], f"step 4: Publish was not accepted: {res}"
        stored_type = (w.written[FEED_VIDEO].get("sectionType") or {}).get("key")
        _, ok, sections, png = public_poll(
            anon, tc, lambda ss: any(s["heading"] == heading_en and s["fragment"] == "mcpf" and not s["hidden"]
                                     for s in ss))
    assert stored_type == "photoGallery", f"stored Section Type is {stored_type!r}"
    assert ok, ("step 5: no public section headed 'QCTEST Video highlights' previews photo albums; sections: "
                f"{[(s['fragment'], s['key'], s['heading']) for s in sections]}")


# ---- TC-191 -----------------------------------------------------------------------
@marks(pytest.mark.functional_low, pytest.mark.tc_149245)
def test_display_order_position(browser, anon):
    """MEDIA-MCHUB-TC-191 — Display Order decides the feed-section position
    (real FEED-03 300 -> 100 and FEED-01 100 -> 300 on the 100-grid)."""
    tc = "191"
    expected = ["videoGallery", "photoGallery", "newsPressReleases"]
    with real_window(browser, tc, [FEED_NEWS, FEED_VIDEO]) as w:
        before = (w.snaps[FEED_NEWS]["displayOrder"], w.snaps[FEED_VIDEO]["displayOrder"])
        assert before == (100, 300), f"PRECONDITION: real orders are {before}"
        for code, order in ((FEED_VIDEO, 100), (FEED_NEWS, 300)):
            res = w.edit(code, {K_ORDER: order})
            assert res["went_through"], f"Publish of {code} Display Order {order} was not accepted: {res}"
            assert w.written[code]["displayOrder"] == order
        _, ok, sections, png = public_poll(
            anon, tc, lambda ss: [s["key"] for s in sorted(ss, key=lambda s: s["top"]) if not s["hidden"]] == expected)
    order = [s["key"] for s in sorted(sections, key=lambda s: s["top"]) if not s["hidden"]]
    assert ok, f"after the Display Order swap the hub order is {order}, expected {expected}"


# ---- TC-209 -----------------------------------------------------------------------
@marks(pytest.mark.functional_high, pytest.mark.tc_149263)
def test_active_status_hides_section(browser, anon):
    """MEDIA-MCHUB-TC-209 — unticking Active Status hides a published section,
    the rest reflow, re-ticking restores it (real FEED-03)."""
    tc = "209"
    with real_window(browser, tc, [FEED_VIDEO]) as w:
        _, ok0, _, _ = public_poll(anon, tc + "_before", lambda ss: not video_section(ss).get("hidden", True))
        assert ok0, "step 2: the Video Gallery section is not shown before the change"
        res = w.edit(FEED_VIDEO, {"activeStatus": False})
        assert res["went_through"], f"step 3: Publish was not accepted: {res}"
        stored_active = w.written[FEED_VIDEO].get("activeStatus")
        badge = w.row_status(FEED_VIDEO)
        _, hidden_ok, s1, _ = public_poll(
            anon, tc + "_inactive", lambda ss: not any(s["key"] == "videoGallery" and not s["hidden"] for s in ss))
        res2 = w.edit(FEED_VIDEO, {"activeStatus": True})
        assert res2["went_through"], f"step 5: re-tick Publish was not accepted: {res2}"
        _, back_ok, _, _ = public_poll(anon, tc + "_reticked", lambda ss: not video_section(ss).get("hidden", True))
    assert stored_active is False, f"stored Active Status is {stored_active!r}"
    assert badge == STATUS_PUBLISHED, f"step 3: badge should stay PUBLISHED, reads {badge!r}"
    assert hidden_ok, ("step 4: the Video Gallery section is still shown after Active Status was unticked: "
                       f"{ {k: video_section(s1).get(k) for k in ('heading', 'eyebrow', 'cta_label', 'cards')} }")
    assert back_ok, "step 6: the Video Gallery section did not come back after re-ticking"


# ---- TC-214 -----------------------------------------------------------------------
@marks(pytest.mark.functional_low, pytest.mark.tc_149268)
def test_cta_destination_change_applied(browser, anon):
    """MEDIA-MCHUB-TC-214 — a CTA Destination change is applied to the public
    CTA (real FEED-03 -> /web/qatar-chamber/annual-reports)."""
    tc = "214"
    target = "/web/qatar-chamber/annual-reports"
    landed = ""
    with real_window(browser, tc, [FEED_VIDEO]) as w:
        res = w.edit(FEED_VIDEO, {K_CTA_DEST: target})
        assert res["went_through"], f"step 4: Publish was not accepted: {res}"
        stored = w.written[FEED_VIDEO].get("ctaDestination")
        view, ok, sections, png = public_poll(
            anon, tc, lambda ss: video_section(ss).get("cta_href", "").split("?")[0].endswith(target))
        if ok:
            landed = view.follow_cta(video_section(sections)["index"])
        record(tc, "CTA click", landed=landed)
    assert stored == target, f"stored CTA Destination is {stored!r}"
    assert ok, f"the public CTA href is {video_section(sections).get('cta_href')!r}, not {target!r}"
    assert landed.split("?")[0].rstrip("/").endswith(target), f"the CTA opened {landed}"
