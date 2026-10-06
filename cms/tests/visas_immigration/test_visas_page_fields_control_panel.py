"""
cms/tests/visas_immigration/test_visas_page_fields_control_panel.py —
Control_Panel hero-field cases of PBI 130701 "Visas & Immigration" (plan
137724 / suite 140362) on the BG Info Page object (`manage-bg-info-page`):
Hero Eyebrow Label 140355 / 140356 / 140402 / 140403, Page Title 140404-140407,
Hero Description 140408-140410, Hero Banner 140411-140413.

The BG Info Page has NO create form (recon §0), so every case runs on the
REAL page record 109104 — allowed by the user (bg_rules.md ADDENDUM b) only
inside `real_page_session()`: lock, one snapshot per run, pre-edit diff,
restore + re-publish + re-open diff + public EN/AR check in `finally`. All
assertions are evaluated AFTER the restore, so the real page is down/changed
only for the minimum time. Validation (reject) cases click Publish on an
invalid value and nothing is saved when the app refuses it; the restore step
still re-reads and diffs the record.

Substitutions disclosed (case literal -> what runs):
  - "currently holds QCTEST-130701 Business Gateway / Visas and Immigration /
    QCTEST-130701-HERO.jpg" (preconditions left by an earlier case): every
    case is restored to the real baseline, so the baseline is the snapshot
    value ("Business Gateway", "Visas & Immigration", the original banner
    visas-hero-passport-3d-1254x1254.png).
  - Uploads carry the B namespace + a unique suffix:
    QCTEST-130701-B-HERO-<uuid8>.jpg (850 KB, 1920x600), QCTEST-130701-B-HERO-
    <uuid8>.gif (~300 KB), QCTEST-130701-B-HERO-UNDER-<uuid8>.jpg (2,097,000 B),
    QCTEST-130701-B-HERO-OVER-<uuid8>.jpg (2,097,500 B).
  - 140408 heading / bullets / link are entered through the editor's own
    Source control (toolbar "Source"), not the Styles combo.
  - Max-length cases also fill the Arabic twin with a max-length Arabic value
    for the public EN/AR 1920/390 check (rule 6).
"""

from __future__ import annotations

import os
import re

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.visas_immigration.bg_admin_page import B_ORIGINAL_BANNER_NAME, MSG_SAVED_AND_PUBLISHED
from cms.tests.visas_immigration.b_fields_support import (  # noqa: F401 — anon_pages is a fixture
    EVIDENCE_DIR,
    FIXTURES,
    MAXLEN_RE,
    PUBLIC_BUDGET_S,
    REQUIRED_RE,
    anon_pages,
    attach,
    frontend_limit_check,
    real_page_session,
    real_snapshot,
    record_finding,
    rtl_aligned_right,
    style_mismatches,
)

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130701,
              pytest.mark.functional_low, pytest.mark.xdist_group("visas_b_real_page")]

HERO_JPG = os.path.join(FIXTURES, "b_qctest_hero_850kb.jpg")
HERO_GIF = os.path.join(FIXTURES, "b_qctest_hero_300kb.gif")
HERO_UNDER = os.path.join(FIXTURES, "b_qctest_hero_under_2mb.jpg")
HERO_OVER = os.path.join(FIXTURES, "b_qctest_hero_over_2mb.jpg")
EYEBROW = "[data-qc-visas-eyebrow]"
TITLE = "[data-qc-visas-title]"
DESC = "[data-qc-visas-desc]"


def _ar_max(n: int) -> str:
    base = ("اختبار الحد الأقصى لطول النص " * 10)[: n - 1].rstrip()
    return base + "ب" * (n - len(base))


def _poll(view, predicate, locale: str = "en") -> dict:
    return view.b_poll(predicate, PUBLIC_BUDGET_S, locale=locale)


def _refusal_checks(tc: str, key: str, result: dict, field_label: str) -> list[str]:
    """Problems with a refusal that should have happened (empty list = refused as expected)."""
    problems = []
    if result["went_through"]:
        problems.append(f"PRODUCT: Publish went through with {field_label} — the value was SAVED "
                        f"(editbar {result['editbar']})")
        return problems
    if not result["refused"]:
        problems.append(f"Publish was neither refused with validation evidence nor saved: {result['evidence']}")
    if result.get("success_message_shown"):
        problems.append("a success message was shown although the save was refused")
    return problems


def _message_check(tc: str, key: str, result: dict, real_errors: list[str], pattern, expected: str) -> None:
    shown = " | ".join(real_errors) or result["messages"]
    if not result["went_through"] and not pattern.search(shown):
        record_finding(tc, "wording (block works)", field=key, expected=expected, shown=shown)


# ===========================================================================
# Hero Eyebrow Label
# ===========================================================================
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Hero Eyebrow Label")
@allure.title("Hero Eyebrow Label accepts a valid bilingual value and renders it on the public page")
@pytest.mark.bilingual
@pytest.mark.tc_140355
def test_140355_eyebrow_valid_bilingual(browser, anon_pages):
    en, ar = "QCTEST-130701 Business Gateway", "بوابة الأعمال"
    facts: dict = {}
    with real_page_session(browser, "140355") as real:
        snap = real_snapshot()["record"]
        facts["shown"] = (real.text_value("eyebrowLabel"), real.ar_value("eyebrowLabel"))
        real.b_fill("eyebrowLabel", en).b_fill("eyebrowLabel", ar, arabic=True)
        facts["counters"] = (real.counter_reading("eyebrowLabel"), real.counter_reading("eyebrowLabel", True))
        facts["errors_before"] = real.errors_for("eyebrowLabel")
        facts["result"] = real.b_publish()
        facts["status"] = real.wait_real_status((STATUS_PUBLISHED,))
        view = anon_pages()
        facts["poll_en"] = _poll(view, lambda m: m["eyebrow"] == en)
        facts["style_en"] = view.b_el(EYEBROW)
        facts["shot_en"] = view.b_evidence(EVIDENCE_DIR, "140355_public_en")
        view_ar = anon_pages()
        facts["poll_ar"] = _poll(view_ar, lambda m: m["eyebrow"] == ar, "ar")
        facts["style_ar"] = view_ar.b_el(EYEBROW)
        facts["dir_ar"] = (view_ar.model() or {}).get("dir")
        facts["shot_ar"] = view_ar.b_evidence(EVIDENCE_DIR, "140355_public_ar")
    attach(facts, "140355 facts")
    assert facts["shown"] == (snap["eyebrowLabel"], snap["eyebrowLabel_ar"]), f"form shows {facts['shown']}"
    assert not facts["errors_before"], f"validation message on a valid value: {facts['errors_before']}"
    if facts["counters"] != ((len(en), 60), (len(ar), 60)):
        pytest.fail(f"character counters read {facts['counters']}, expected ({len(en)}/60, {len(ar)}/60)")
    if facts["counters"][0][0] != 31:
        record_finding("140355", "case data", note=f"case expects counter 31 but {en!r} is {len(en)} characters; "
                       f"the counter correctly reads {facts['counters'][0][0]}")
    assert facts["result"]["went_through"], f"Publish did not go through: {facts['result']}"
    assert any(MSG_SAVED_AND_PUBLISHED in t for t in facts["result"]["editbar"]), facts["result"]["editbar"]
    assert facts["status"] == STATUS_PUBLISHED, f"record status after the save: {facts['status']!r}"
    assert facts["poll_en"]["ok"], "EN hero eyebrow never showed the new value"
    assert facts["poll_en"]["within_budget"], f"EN eyebrow appeared after {facts['poll_en']['seen_at']} s (> 5 s)"
    problems = style_mismatches(facts["style_en"], "12px", "400", "#911731")
    assert facts["poll_ar"]["ok"], "AR hero eyebrow never showed the new value"
    problems += [f"AR {p}" for p in style_mismatches(facts["style_ar"], "12px", "400", "#911731")]
    if facts["dir_ar"] != "rtl":
        problems.append(f"AR page dir={facts['dir_ar']!r}")
    assert not problems, f"style/layout differs from the case: {problems}"


@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Hero Eyebrow Label")
@allure.title("Hero Eyebrow Label rejects an empty mandatory value")
@pytest.mark.tc_140356
def test_140356_eyebrow_empty_rejected(browser, anon_pages):
    _empty_or_blank_text_case(browser, anon_pages, "140356", "eyebrowLabel", "", "eyebrow", "an empty Eyebrow Label EN")


@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Hero Eyebrow Label")
@allure.title("Hero Eyebrow Label rejects a whitespace-only value")
@pytest.mark.tc_140403
def test_140403_eyebrow_whitespace_rejected(browser, anon_pages):
    _empty_or_blank_text_case(browser, anon_pages, "140403", "eyebrowLabel", "   ", "eyebrow",
                              "a whitespace-only Eyebrow Label EN")


@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Hero Eyebrow Label")
@allure.title("Hero Eyebrow Label enforces its 60-character maximum at the boundary")
@pytest.mark.tc_140402
def test_140402_eyebrow_60_boundary(browser, anon_pages):
    value = "QCTEST-130701-EYEBROW-60-" + "A" * 35
    _boundary_text_case(browser, anon_pages, "140402", "eyebrowLabel", value, 60, EYEBROW, "eyebrow")


# ===========================================================================
# Page Title
# ===========================================================================
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Page Title")
@allure.title("Page Title accepts a valid bilingual value and renders it on the public page")
@pytest.mark.bilingual
@pytest.mark.tc_140404
def test_140404_title_valid_bilingual(browser, anon_pages):
    en, ar = "QCTEST-130701 Visas and Immigration", "التأشيرات والجوازات"
    facts: dict = {}
    with real_page_session(browser, "140404") as real:
        snap = real_snapshot()["record"]
        facts["shown"] = (real.text_value("pageTitle"), real.ar_value("pageTitle"))
        real.b_fill("pageTitle", en).b_fill("pageTitle", ar, arabic=True)
        facts["errors_before"] = real.errors_for("pageTitle")
        facts["result"] = real.b_publish()
        facts["status"] = real.wait_real_status((STATUS_PUBLISHED,))
        view = anon_pages()
        facts["poll_en"] = _poll(view, lambda m: m["title"] == en)
        facts["style_en"] = view.b_el(TITLE)
        facts["shot_en"] = view.b_evidence(EVIDENCE_DIR, "140404_public_en")
        view_ar = anon_pages()
        facts["poll_ar"] = _poll(view_ar, lambda m: m["title"] == ar, "ar")
        facts["style_ar"] = view_ar.b_el(TITLE)
        facts["dir_ar"] = (view_ar.model() or {}).get("dir")
        facts["shot_ar"] = view_ar.b_evidence(EVIDENCE_DIR, "140404_public_ar")
    attach(facts, "140404 facts")
    assert facts["shown"] == (snap["pageTitle"], snap["pageTitle_ar"]), f"form shows {facts['shown']}"
    assert not facts["errors_before"], f"validation message on a valid value: {facts['errors_before']}"
    assert facts["result"]["went_through"], f"Publish did not go through: {facts['result']}"
    assert any(MSG_SAVED_AND_PUBLISHED in t for t in facts["result"]["editbar"]), facts["result"]["editbar"]
    assert facts["status"] == STATUS_PUBLISHED, f"record status after the save: {facts['status']!r}"
    assert facts["poll_en"]["ok"], "EN hero title never showed the new value"
    assert facts["poll_en"]["within_budget"], f"EN title appeared after {facts['poll_en']['seen_at']} s (> 5 s)"
    problems = style_mismatches(facts["style_en"], "48px", "700", "#1D1D1B", width=872)
    assert facts["poll_ar"]["ok"], "AR hero title never showed the new value"
    problems += [f"AR {p}" for p in style_mismatches(facts["style_ar"], "48px", "700", "#1D1D1B")]
    if facts["dir_ar"] != "rtl":
        problems.append(f"AR page dir={facts['dir_ar']!r}")
    assert not problems, f"style/layout differs from the case: {problems}"


@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Page Title")
@allure.title("Page Title rejects an empty mandatory value")
@pytest.mark.tc_140405
def test_140405_title_empty_rejected(browser, anon_pages):
    _empty_or_blank_text_case(browser, anon_pages, "140405", "pageTitle", "", "title", "an empty Page Title EN")


@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Page Title")
@allure.title("Page Title rejects a whitespace-only value")
@pytest.mark.tc_140407
def test_140407_title_whitespace_rejected(browser, anon_pages):
    _empty_or_blank_text_case(browser, anon_pages, "140407", "pageTitle", "   ", "title",
                              "a whitespace-only Page Title EN")


@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Page Title")
@allure.title("Page Title enforces its 120-character maximum at the boundary")
@pytest.mark.tc_140406
def test_140406_title_120_boundary(browser, anon_pages):
    value = "QCTEST-130701-TITLE-120-" + "A" * 96
    _boundary_text_case(browser, anon_pages, "140406", "pageTitle", value, 120, TITLE, "title", box_width=872)


# ===========================================================================
# Hero Description
# ===========================================================================
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Hero Description")
@allure.title("Hero Description rich text accepts headings, bullets and links and renders them on the public page")
@pytest.mark.tc_140408
def test_140408_description_rich_text(browser, anon_pages):
    href = "https://portal.moi.gov.qa"
    en_html = (f"<h2>QCTEST-130701 hero heading</h2><ul><li>first bullet</li><li>second bullet</li></ul>"
               f"<p><a href=\"{href}\">official sources</a></p>")
    ar_html = (f"<h2>عنوان الواجهة QCTEST-130701</h2><ul><li>النقطة الأولى</li><li>النقطة الثانية</li></ul>"
               f"<p><a href=\"{href}\">المصادر الرسمية</a></p>")
    facts: dict = {}
    with real_page_session(browser, "140408") as real:
        facts["editor_present"] = bool(real.cke_name("heroDescription"))
        real.b_rich_source("heroDescription", en_html).b_rich_source("heroDescription", ar_html, arabic=True)
        facts["editor_html_en"] = real.rich_data("heroDescription")
        facts["editor_html_ar"] = real.rich_data("heroDescription", arabic=True)
        facts["result"] = real.b_publish()
        facts["status"] = real.wait_real_status((STATUS_PUBLISHED,))
        view = anon_pages()
        facts["poll_en"] = _poll(view, lambda m: "QCTEST-130701 hero heading" in m["description"])
        facts["style_en"] = view.b_el(DESC)
        facts["markup_en"] = view.b_markup(DESC)
        facts["shot_en"] = view.b_evidence(EVIDENCE_DIR, "140408_public_en")
        view_ar = anon_pages()
        facts["poll_ar"] = _poll(view_ar, lambda m: "النقطة الأولى" in m["description"], "ar")
        facts["markup_ar"] = view_ar.b_markup(DESC)
        facts["shot_ar"] = view_ar.b_evidence(EVIDENCE_DIR, "140408_public_ar")
    attach(facts, "140408 facts")
    assert facts["editor_present"], "no rich-text editor on Hero Description EN"
    for needle in ("<h2>", "<li>first bullet</li>", "official sources"):
        assert needle in facts["editor_html_en"], f"the editor did not keep {needle!r}: {facts['editor_html_en']}"
    assert facts["result"]["went_through"], f"Publish did not go through: {facts['result']}"
    assert facts["status"] == STATUS_PUBLISHED, f"record status after the save: {facts['status']!r}"
    assert facts["poll_en"]["ok"], "EN hero description never showed the new value"
    assert facts["poll_en"]["within_budget"], f"EN description appeared after {facts['poll_en']['seen_at']} s"
    markup = facts["markup_en"] or {}
    problems = style_mismatches(facts["style_en"], "16px", "400", "#6C6C6B")
    if not any(h["text"] == "QCTEST-130701 hero heading" for h in markup.get("headings", [])):
        problems.append(f"no heading element reading 'QCTEST-130701 hero heading': {markup.get('headings')}")
    if markup.get("lists") != [["first bullet", "second bullet"]]:
        problems.append(f"unordered list items: {markup.get('lists')}")
    if not any(a["text"] == "official sources" and a["href"] == href for a in markup.get("anchors", [])):
        problems.append(f"anchor 'official sources' -> {href} missing: {markup.get('anchors')}")
    if re.search(r"</?(h\d|ul|li|p|a)\b", markup.get("text", "")):
        problems.append("raw HTML tags are shown as visible text")
    assert not problems, f"public hero description differs from the case: {problems}"


@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Hero Description")
@allure.title("Hero Description rejects an empty mandatory value")
@pytest.mark.tc_140409
def test_140409_description_empty_rejected(browser, anon_pages):
    _empty_or_blank_rich_case(browser, anon_pages, "140409", "", "an empty Hero Description EN")


@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Hero Description")
@allure.title("Hero Description rejects a whitespace-only value")
@pytest.mark.tc_140410
def test_140410_description_whitespace_rejected(browser, anon_pages):
    _empty_or_blank_rich_case(browser, anon_pages, "140410", "   ", "a whitespace-only Hero Description EN")


# ===========================================================================
# Hero Banner
# ===========================================================================
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Hero Banner")
@allure.title("Hero Banner accepts a valid JPG under 2 MB and renders it on the public page")
@pytest.mark.tc_140411
def test_140411_banner_valid_jpg(browser, anon_pages):
    facts: dict = {}
    with real_page_session(browser, "140411") as real:
        facts["upload"] = real.b_attempt_banner(HERO_JPG, "QCTEST-130701-B-HERO")
        facts["thumbnail"] = real.has_thumbnail("heroBanner")
        facts["field_errors"] = real.errors_for("heroBanner")
        stem = os.path.splitext(facts["upload"]["file"])[0]
        facts["result"] = real.b_publish() if facts["upload"]["attached"] else {"went_through": False}
        if facts["result"]["went_through"]:
            facts["status"] = real.wait_real_status((STATUS_PUBLISHED,))
            view = anon_pages()
            facts["poll_en"] = _poll(view, lambda m: stem.lower() in (m["hero_img"] or "").lower())
            view.b_scroll_hero_into_view()
            facts["img"] = view.b_hero_img()
            facts["http"] = view.b_fetch_status(facts["img"]["src"]) if facts["img"] else None
            facts["shot_en"] = view.b_evidence(EVIDENCE_DIR, "140411_public_en")
    attach(facts, "140411 facts")
    record_finding("140411", "D&M file left on qcdev", file=facts["upload"].get("file"),
                   note="uploaded through the Hero Banner picker; the real banner was re-selected afterwards")
    assert facts["upload"]["attached"], f"the JPG was not accepted: {facts['upload']}"
    assert not facts["field_errors"], f"validation message on a valid JPG: {facts['field_errors']}"
    assert facts["result"]["went_through"], f"Publish did not go through: {facts['result']}"
    assert facts["status"] == STATUS_PUBLISHED, f"record status after the save: {facts['status']!r}"
    assert facts["poll_en"]["ok"], "the public hero banner never resolved to the uploaded JPG"
    assert facts["http"] and facts["http"]["status"] == 200, f"hero banner request: {facts['http']}"
    assert facts["poll_en"]["within_budget"], f"the new banner appeared after {facts['poll_en']['seen_at']} s"
    img = facts["img"]
    problems = []
    if (img["natural_w"], img["natural_h"]) != (1920, 600):
        problems.append(f"natural size {img['natural_w']}x{img['natural_h']} (expected 1920x600)")
    if img["object_fit"] in ("fill", "") and img["h"] and img["natural_h"]:
        ratio, natural = img["w"] / img["h"], img["natural_w"] / img["natural_h"]
        if abs(ratio - natural) / natural > 0.02:
            problems.append(f"distorted: rendered {img['w']}x{img['h']} vs natural ratio {natural:.2f}")
    if not (img.get("alt") or "").strip():
        problems.append(f"the hero banner <img> has an EMPTY alt attribute (alt={img.get('alt')!r}); the BG Info "
                        f"Page has no alt-text field")
    assert not problems, f"public hero banner differs from the case: {problems} (screenshot {facts['shot_en']})"


@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Hero Banner")
@allure.title("Hero Banner rejects a file type outside JPG, PNG and SVG")
@pytest.mark.tc_140412
def test_140412_banner_gif_rejected(browser, anon_pages):
    facts: dict = {}
    with real_page_session(browser, "140412") as real:
        snap = real_snapshot()
        facts["upload"] = real.b_attempt_banner(HERO_GIF, "QCTEST-130701-B-HERO")
        facts["field_errors"] = real.errors_for("heroBanner")
        facts["block"] = real.upload_block_text("heroBanner")
        facts["shot_form"] = real.evidence("140412_after_gif_attempt")
        facts["result"] = real.b_publish()
        real.open_real_page()
        facts["stored_file"] = real.stored_file_name("heroBanner")
        facts["stored_href"] = real.file_preview_href("heroBanner")
        view = anon_pages()
        view.open_page("en")
        facts["public_src"] = (view.model() or {}).get("hero_img")
    attach(facts, "140412 facts")
    assert not facts["upload"]["attached"], f"PRODUCT: the GIF was attached to Hero Banner: {facts['upload']}"
    assert facts["stored_file"] == B_ORIGINAL_BANNER_NAME and facts["stored_href"] == snap["record"]["heroBanner_href"], (
        f"PRODUCT: the stored banner changed to {facts['stored_file']!r} ({facts['stored_href']})")
    assert facts["public_src"] == snap["public"]["en"]["hero_img"], f"public hero banner now {facts['public_src']!r}"
    shown = " | ".join(facts["upload"].get("errors", []) + facts["field_errors"]) or facts["upload"].get("picker_text", "")
    if not re.search(r"jpe?g|png|svg|extension|type|format", shown, re.I):
        record_finding("140412", "wording (block works)", field="heroBanner",
                       expected="a validation error stating only JPG, PNG and SVG are allowed", shown=shown[:400],
                       screenshot=facts["upload"].get("picker_evidence") or facts["shot_form"])
    assert shown.strip(), (f"the GIF was not attached, but NO validation message was shown "
                           f"(picker {facts['upload'].get('picker_evidence')})")


@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Hero Banner")
@allure.title("Hero Banner enforces the 2 MB size limit at the boundary")
@pytest.mark.tc_140413
def test_140413_banner_2mb_boundary(browser, anon_pages):
    facts: dict = {"sizes": (os.path.getsize(HERO_UNDER), os.path.getsize(HERO_OVER))}
    with real_page_session(browser, "140413") as real:
        facts["under"] = real.b_attempt_banner(HERO_UNDER, "QCTEST-130701-B-HERO-UNDER")
        under_stem = os.path.splitext(facts["under"]["file"])[0]
        facts["under_errors"] = real.errors_for("heroBanner")
        facts["result_under"] = real.b_publish() if facts["under"]["attached"] else {"went_through": False}
        if facts["result_under"]["went_through"]:
            view = anon_pages()
            facts["poll_under"] = _poll(view, lambda m: under_stem.lower() in (m["hero_img"] or "").lower())
            img = view.b_hero_img()
            facts["http_under"] = view.b_fetch_status(img["src"]) if img else None
            real.open_real_page()
            facts["over"] = real.b_attempt_banner(HERO_OVER, "QCTEST-130701-B-HERO-OVER")
            facts["over_errors"] = real.errors_for("heroBanner")
            facts["shot_over"] = real.evidence("140413_after_over_attempt")
            facts["result_over"] = real.b_publish()
            real.open_real_page()
            facts["stored_after_over"] = real.stored_file_name("heroBanner")
            view2 = anon_pages()
            view2.open_page("en")
            facts["public_after_over"] = (view2.model() or {}).get("hero_img")
    attach(facts, "140413 facts")
    record_finding("140413", "D&M file left on qcdev", file=facts["under"].get("file"),
                   note="under-limit upload; the real banner was re-selected afterwards")
    assert facts["sizes"] == (2_097_000, 2_097_500), facts["sizes"]
    assert facts["under"]["attached"], f"the 2,097,000-byte JPG was not accepted: {facts['under']}"
    assert facts["result_under"]["went_through"], f"Publish with the under-limit file failed: {facts['result_under']}"
    assert facts["poll_under"]["ok"], "the public banner never resolved to the under-limit file"
    assert facts["http_under"] and facts["http_under"]["status"] == 200, facts["http_under"]
    assert facts["poll_under"]["within_budget"], f"under-limit banner appeared after {facts['poll_under']['seen_at']} s"
    over = facts["over"]
    publish_msgs = facts["result_over"].get("evidence", {}).get("field_errors", [])
    assert facts["stored_after_over"] == facts["under"]["file"], (
        f"PRODUCT: stored banner after the oversized attempt is {facts['stored_after_over']!r}")
    assert under_stem.lower() in (facts["public_after_over"] or "").lower(), facts["public_after_over"]
    assert not facts["result_over"]["went_through"], f"PRODUCT: Publish with the oversized banner went through"
    if over["attached"]:
        record_finding("140413", "D&M file left on qcdev", file=over.get("file"),
                       note="oversized file was accepted by the picker upload and stored in Documents & Media")
        pytest.fail(f"PRODUCT: the 2,097,500-byte JPG ({over['file']}) was NOT rejected at upload — the picker "
                    f"accepted it, stored it in Documents & Media and attached it to Hero Banner without a message; "
                    f"only Publish was then refused with {publish_msgs} (stored banner stayed "
                    f"{facts['stored_after_over']!r}). Screenshot {facts.get('shot_over')}")
    shown = " | ".join(over.get("errors", []) + facts["over_errors"]) or over.get("picker_text", "")
    assert shown.strip(), f"oversized file not attached, but NO validation message shown ({over.get('picker_evidence')})"
    if not re.search(r"2\s*MB|size|large|exceed", shown, re.I):
        record_finding("140413", "wording (block works)", field="heroBanner",
                       expected="a validation error stating the maximum file size is 2 MB", shown=shown[:400],
                       screenshot=over.get("picker_evidence") or facts.get("shot_over"))


# ===========================================================================
# shared case bodies
# ===========================================================================
def _empty_or_blank_text_case(browser, anon_pages, tc: str, key: str, value: str, model_key: str, what: str) -> None:
    facts: dict = {}
    with real_page_session(browser, tc) as real:
        snap = real_snapshot()
        facts["shown"] = real.text_value(key)
        real.b_fill(key, value)
        facts["field_value"] = real.text_value(key)
        facts["flags"] = real.field_flags(key)
        facts["result"] = real.b_publish()
        facts["field_errors"] = real.errors_for(key)
        facts["shot"] = real.evidence(f"{tc}_after_publish")
        view = anon_pages()
        view.open_page("en")
        facts["public"] = (view.model() or {}).get(model_key)
        facts["public_el"] = view.b_el(EYEBROW if key == "eyebrowLabel" else TITLE)
    attach(facts, f"{tc} facts")
    assert facts["shown"] == snap["record"][key], f"the form showed {facts['shown']!r}"
    assert facts["field_value"] == value, f"the field holds {facts['field_value']!r}"
    problems = _refusal_checks(tc, key, facts["result"], what)
    if not (facts["flags"]["label_star"] or facts["flags"]["required_attr"] or facts["flags"]["aria_required"]):
        problems.append(f"the field is not marked mandatory: {facts['flags']}")
    if not facts["result"]["went_through"] and not facts["field_errors"]:
        problems.append(f"no field-level validation message against {key}: {facts['result']['evidence']}")
    if facts["public"] != snap["public"]["en"][model_key]:
        problems.append(f"public {model_key} now {facts['public']!r} (expected {snap['public']['en'][model_key]!r})")
    _message_check(tc, key, facts["result"], facts["field_errors"], REQUIRED_RE, "the field is required")
    assert not problems, f"{what}: {problems} (screenshot {facts['shot']})"


def _empty_or_blank_rich_case(browser, anon_pages, tc: str, text: str, what: str) -> None:
    key = "heroDescription"
    facts: dict = {}
    with real_page_session(browser, tc) as real:
        snap = real_snapshot()
        facts["shown"] = real.rich_data(key)
        real.b_rich_type(key, text)
        facts["editor_html"] = real.rich_data(key)
        facts["result"] = real.b_publish()
        facts["field_errors"] = real.errors_for(key)
        facts["block"] = real.rich_block_text(key)
        facts["shot"] = real.evidence(f"{tc}_after_publish")
        view = anon_pages()
        view.open_page("en")
        model = view.model() or {}
        facts["public_html"] = model.get("description_html")
    attach(facts, f"{tc} facts")
    assert re.sub(r"\s+", " ", facts["shown"]).strip() == re.sub(r"\s+", " ", snap["record"]["heroDescription_cke"]).strip(), (
        f"the editor was not populated with the baseline: {facts['shown']!r}")
    problems = _refusal_checks(tc, key, facts["result"], what)
    if not facts["result"]["went_through"] and not facts["field_errors"]:
        problems.append(f"no field-level validation message against Hero Description EN: {facts['result']['evidence']}")
    if " ".join((facts["public_html"] or "").split()) != " ".join((snap["public"]["en"]["description_html"] or "").split()):
        problems.append(f"public hero description now {facts['public_html']!r}")
    _message_check(tc, key, facts["result"], facts["field_errors"], REQUIRED_RE, "the field is required")
    assert not problems, f"{what}: {problems} (screenshot {facts['shot']})"


def _boundary_text_case(browser, anon_pages, tc: str, key: str, value: str, limit: int, selector: str,
                        model_key: str, box_width: float | None = None) -> None:
    assert len(value) == limit, f"test data: {len(value)} != {limit}"
    ar_value = _ar_max(limit)
    over = value + "A"
    facts: dict = {}
    with real_page_session(browser, tc) as real:
        real.b_fill(key, value).b_fill(key, ar_value, arabic=True)
        facts["counter"] = real.counter_reading(key)
        facts["errors_max"] = real.errors_for(key)
        facts["result_max"] = real.b_publish()
        if facts["result_max"]["went_through"]:
            view = anon_pages()
            facts["poll"] = _poll(view, lambda m: m[model_key] == value)
            facts["el"] = view.b_el(selector)
            facts["frontend"] = frontend_limit_check(anon_pages, tc, selector, {"en": value, "ar": ar_value})
        real.open_real_page()
        real.b_type(key, over)
        facts["typed_over_value"] = real.text_value(key)
        facts["counter_over"] = real.counter_reading(key)
        facts["errors_over"] = real.errors_for(key)
        facts["result_over"] = real.b_publish()
        facts["shot_over"] = real.evidence(f"{tc}_after_over_publish")
        real.open_real_page()
        facts["stored_after_over"] = real.text_value(key)
    attach(facts, f"{tc} facts")
    assert facts["result_max"]["went_through"], f"Publish with the {limit}-character value failed: {facts['result_max']}"
    assert not facts["errors_max"], f"validation message on {limit} characters: {facts['errors_max']}"
    assert any(MSG_SAVED_AND_PUBLISHED in t for t in facts["result_max"]["editbar"]), facts["result_max"]["editbar"]
    assert facts["counter"] == (limit, limit), f"character counter reads {facts['counter']} (expected {limit}/{limit})"
    assert facts["poll"]["ok"], f"the public {model_key} never showed the full {limit}-character value"
    assert facts["poll"]["within_budget"], f"the public {model_key} appeared after {facts['poll']['seen_at']} s"
    problems = []
    el = facts["el"] or {}
    if box_width is not None and el and el["width"] > box_width + 2:
        problems.append(f"{model_key} box {el['width']}px wider than {box_width}px")
    if box_width is not None and el and el["scroll_width"] > el["client_width"] + 1:
        problems.append(f"the {limit}-character {model_key} does NOT wrap inside the {box_width}px box (content "
                        f"{el['scroll_width']}px wide, overflowing the box)")
    for res in facts.get("frontend", []):
        if res["problems"]:
            problems.append(f"public {res['locale'].upper()} @{res['viewport']}: {res['problems']} ({res['screenshot']})")
    stored = facts["stored_after_over"]
    if len(stored) > limit:
        problems.append(f"PRODUCT: {len(stored)} characters were STORED (limit {limit})")
    elif stored != value:
        problems.append(f"stored value after the over-limit attempt is {stored!r}, not the {limit}-character string")
    if len(facts["typed_over_value"]) > limit and facts["result_over"]["went_through"]:
        problems.append(f"PRODUCT: the field held {len(facts['typed_over_value'])} characters and Publish went through")
    if len(facts["typed_over_value"]) > limit and not facts["result_over"]["went_through"]:
        _message_check(tc, key, facts["result_over"], facts["errors_over"], MAXLEN_RE, "a maximum-length error")
    assert not problems, f"{limit}-character boundary: {problems} (screenshot {facts['shot_over']})"
