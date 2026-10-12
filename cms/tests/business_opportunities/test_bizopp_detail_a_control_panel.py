"""
cms/tests/business_opportunities/test_bizopp_detail_a_control_panel.py —
CMS-authoring cases tagged Web for the public Opportunity Detail page, PBI
130697 (Agent A): 143373, 143374, 143378-143383.

The CMS step is done for real (Site Content Editor, A_PREFIX = QCTEST-130697-G- records)
and the public render is read from a fresh logged-out context.

Content model (live recon 2026-10-07): header + 01 Overview + 02 Investment
Details come from the BusinessOpportunity record itself (no separate
"section editor" exists); Key Highlights, Co-Investment rows, Project Gallery
images and Downloadable Resources are separate child objects (key-highlight,
co-investment, project-gallery-item, downloadable-resource) linked to the
opportunity by a relation picker. Gallery images are PICKED from existing
Documents & Media root files (no upload); the case's PDFs are uploaded (they
are the subject of the case) and remain in Documents & Media — reported.

Substitutions disclosed:
  - 143378 Timeline '2-3 years' is not an option of the Timeline picklist
    (Immediate / 1–3 / 3–6 / 6–12 / 12+ months) -> run with '12+ months' and
    reported as a case-vs-app mismatch.
  - 143380 "Investment Amount = 'QAR 2,000,000 - QAR 5,000,000'" is the text
    field "Investment Amount Range" (the field "Investment Amount" is a number).
"""

from __future__ import annotations

import hashlib

import allure
import pytest

from cms.pages.business_opportunities.opportunity_admin_page import (
    CO_INVESTMENT_SLUG,
    GALLERY_SLUG,
    K_AMOUNT_RANGE,
    K_BRIEF,
    K_COUNTRY,
    K_ENTITY,
    K_HERO_BANNER,
    K_HERO_SUMMARY,
    K_INVESTMENT_TYPE,
    K_LOCATION,
    K_MIN_TICKET,
    K_OVERVIEW,
    K_RISK,
    K_SECTOR,
    K_SUBMITTER,
    K_TIMELINE,
    K_TITLE,
    KEY_HIGHLIGHT_SLUG,
    MSG_SAVED_AND_PUBLISHED,
    RESOURCE_SLUG,
    ROLE_EDITOR,
    BizOppPublicView,
    OpportunityAdminPage,
)
from cms.tests.business_opportunities.a_support import (  # noqa: F401 — fixtures
    A_GROUP,
    AUTH_FREE_PAGE,
    BMP_FIXTURE,
    EPIC,
    EXISTING_ROOT_IMAGES,
    a_name,
    anon_pages,
    create_child,
    create_opportunity,
    disposable,
    has,
    login,
    make_pdf,
    pinned,
    require_active_status,
    same_session,
)
from core.utils.waits import WaitTimeoutError, wait_until

FEATURE = "Business Opportunities — CMS authoring -> public detail page"


def _markers(*tcs, regression=False):
    def deco(fn):
        marks = [pytest.mark.control_panel, pytest.mark.web, pytest.mark.invest, pytest.mark.pbi_130697,
                 pytest.mark.functional_low, A_GROUP]
        if regression:
            marks.append(pytest.mark.regression)
        for m in marks:
            fn = m(fn)
        for tc in tcs:
            fn = getattr(pytest.mark, f"tc_{tc}")(fn)
        return fn
    return deco


def _text(n: int, seed: str) -> str:
    base = (seed + " ") * (n // (len(seed) + 1) + 2)
    return base[:n].rstrip() + "." if n > 1 else base[:n]


def _publish_parent(admin, disposable, data) -> object:
    entry = create_opportunity(admin, disposable, data, publish=True)
    assert has(admin.create_banners, MSG_SAVED_AND_PUBLISHED), f"parent publish message: {admin.create_banners}"
    return entry


def _detail(anon_pages, code: str, locale: str, ready, timeout: float = 45.0) -> dict:
    """Logged-out detail read, polled until `ready(detail)`."""
    view = BizOppPublicView(anon_pages())
    seen = {"d": {}}

    def _ok() -> bool:
        view.open_detail(code, locale)
        seen["d"] = view.detail()
        return bool(ready(seen["d"]))

    try:
        wait_until(_ok, timeout=timeout, poll=3.0)
    except WaitTimeoutError:
        pass
    view.screenshot(f"public detail {code} {locale}")
    allure.attach(repr({k: v for k, v in seen["d"].items() if k != "body"}), name=f"public detail ({locale})")
    return seen["d"]


def _attempt_publish_new(admin, disposable, data: dict) -> dict:
    """Create-form Publish that may be refused; registers anything created."""
    ids_before = admin.snapshot_ids()
    admin.open_create_form_en()
    admin.fill_opportunity(data)
    pinned(admin, ROLE_EDITOR)
    admin.click_publish()
    outcome = {**admin.save_outcome(), "messages": admin.all_messages_text(),
               "field_errors": admin.field_error_owners()}
    admin.evidence(f"{data[K_TITLE]} publish attempt")
    try:
        entry = admin.identify_created_entry(data[K_TITLE], ids_before)
        if entry:
            disposable.track(entry)
        outcome["created"] = entry
    except Exception as exc:  # noqa: BLE001
        outcome["created"] = None
        allure.attach(repr(exc), name="registration failed")
    allure.attach(repr(outcome), name=f"publish attempt {data[K_TITLE]}")
    return outcome


# ===========================================================================
# 143373 — detail header (title, hero summary, derived Sector / Country tags) EN + AR
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Detail header")
@allure.title("Opportunity Detail header content authors and renders correctly on the public detail page")
@_markers("143373", regression=True)
def test_detail_header_renders(page, anon_pages, disposable):
    # Azure TC 143373 | Site Content Editor.
    admin = login(page, ROLE_EDITOR)
    title = a_name("143373", "Solar Farm Expansion – Al Khor")
    title_ar = "توسعة مزرعة الطاقة الشمسية - الخور"
    summary = _text(150, "Utility-scale solar farm expansion in Al Khor with grid storage and long-term offtake")
    summary_ar = _text(150, "توسعة مزرعة طاقة شمسية في الخور مع تخزين الشبكة")
    data = OpportunityAdminPage.default_data(title, **{f"{K_TITLE}_ar": title_ar, K_SECTOR: "Energy",
                                                       K_COUNTRY: "Qatar", f"{K_COUNTRY}_ar": "قطر",
                                                       K_HERO_SUMMARY: summary, f"{K_HERO_SUMMARY}_ar": summary_ar})
    entry = _publish_parent(admin, disposable, data)
    admin.open_entry_en(entry.code)
    stored = {"title_ar": admin.ar_value(K_TITLE), "summary": admin.rich_text(K_HERO_SUMMARY),
              "summary_ar": admin.rich_text_ar(K_HERO_SUMMARY)}
    allure.attach(repr(stored), name="stored values")
    require_active_status(admin, entry)
    en = _detail(anon_pages, entry.code, "en", lambda d: d.get("h1") == title)
    ar = _detail(anon_pages, entry.code, "ar", lambda d: d.get("h1") == title_ar)
    problems = []
    if en.get("h1") != title:
        problems.append(f"EN title {en.get('h1')!r}")
    if en.get("summary") != summary:
        problems.append(f"EN summary {en.get('summary')!r}")
    if "Energy" not in en.get("chips", []) or "Qatar" not in en.get("chips", []):
        problems.append(f"EN tags {en.get('chips')} (expected 'Energy', 'Qatar')")
    if ar.get("h1") != title_ar:
        problems.append(f"AR title {ar.get('h1')!r}")
    if ar.get("summary") != summary_ar:
        problems.append(f"AR summary {ar.get('summary')!r}")
    if "الطاقة" not in ar.get("chips", []) or "قطر" not in ar.get("chips", []):
        problems.append(f"AR tags {ar.get('chips')} (expected 'الطاقة', 'قطر')")
    assert not problems, "PRODUCT: the public detail header does not render as authored: " + "; ".join(problems)


# ===========================================================================
# 143374 — Hero Summary required + Hero Banner rejects .bmp
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Detail header validation")
@allure.title("Publish is blocked when Hero Summary is empty and Hero Banner rejects an unsupported image format")
@_markers("143374")
def test_hero_summary_required_and_bmp_rejected(page, disposable):
    # Azure TC 143374 | Site Content Editor | title only, Hero Summary empty, hero-banner.bmp.
    admin = login(page, ROLE_EDITOR)
    title = a_name("143374", "title only")
    ids_before = admin.snapshot_ids()
    admin.open_create_form_en()
    admin.fill_en(K_TITLE, title)
    upload = admin.attempt_upload(K_HERO_BANNER, BMP_FIXTURE, stem="a_qctest_hero-banner")
    upload_view = {k: upload.get(k) for k in ("file", "status", "success", "errors", "attached", "field_text",
                                              "field_errors", "picker_text")}
    allure.attach(repr(upload_view), name=".bmp upload attempt (Hero Banner)")
    admin.evidence("143374 after bmp attempt")
    pinned(admin, ROLE_EDITOR)
    admin.click_publish()
    outcome = {**admin.save_outcome(), "messages": admin.all_messages_text(), "field_errors": admin.field_error_owners()}
    admin.evidence("143374 publish attempt")
    allure.attach(repr(outcome), name="publish attempt")
    entry = admin.identify_created_entry(title, ids_before)
    if entry:
        disposable.track(entry)

    assert not upload["attached"], f"PRODUCT: the .bmp file was accepted into Hero Banner: {upload_view}"
    assert not outcome["went_through"] and entry is None, (
        f"PRODUCT: Publish with an empty Hero Summary was accepted: {outcome}")
    messages = outcome["messages"] + " " + " ".join(e["text"] for e in outcome["field_errors"])
    picker_errors = " ".join(upload_view["errors"] or [])
    assert "Hero Summary is required" in messages, f"Publish blocked, but no 'Hero Summary is required': {messages!r}"
    assert picker_errors or "valid extension" in upload_view.get("picker_text", ""), (
        f"the .bmp was not attached, but no rejection message was shown: {upload_view}")
    # Rule 6: same behaviour, different wording -> recorded as a LOW wording finding, not failed.
    expected_wording = "Unsupported file type, JPG/PNG/SVG only"
    allure.attach(f"expected {expected_wording!r}\nshown    {picker_errors!r}", name="LOW wording finding (.bmp rejection)")


# ===========================================================================
# 143378 — 01 Overview: body, brief (4800), 2 key highlights, Submitted By, stats card
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("01 Overview")
@allure.title("01 Overview content authors and the Stats Card derives correctly on the public detail page")
@_markers("143378", regression=True)
def test_overview_section_renders(page, anon_pages, disposable):
    # Azure TC 143378 | Site Content Editor | Timeline '2-3 years' -> '12+ months' (not an option).
    admin = login(page, ROLE_EDITOR)
    title = a_name("143378", "overview")
    overview = f"{title} overview body: a solar farm expansion opportunity."
    brief = _text(4800, "Investment brief for the Al Khor solar expansion covering capacity tariff offtake")
    data = OpportunityAdminPage.default_data(title, **{
        K_INVESTMENT_TYPE: "Equity", K_TIMELINE: "12+ months", K_RISK: "Medium",
        K_OVERVIEW: overview, K_BRIEF: "", K_SUBMITTER: "Al Faisal Holding", K_ENTITY: "Private",
        K_LOCATION: "Doha, Qatar"})
    del data[K_BRIEF]

    def _fill(a):
        a.fill_opportunity(data)
        a.set_rich_html(K_BRIEF, f"<p>{brief}</p>")
    from cms.tests.business_opportunities.a_support import create
    parent = create(admin, disposable, title, _fill, publish=True)
    admin.open_entry_en(parent.code)
    stored_brief = admin.rich_text(K_BRIEF)
    allure.attach(f"stored Investment Brief length {len(stored_brief)}", name="stored brief")
    hl = [_text(150, "Highlight one: 120 MW of new solar capacity with grid-scale storage and a sovereign offtake"),
          _text(150, "Highlight two: phased construction over three years with local content and job creation")]
    for i, text in enumerate(hl, start=1):
        identity = f"{a_name('143378', f'KH{i}')} {text}"[:150]
        create_child(admin, disposable, KEY_HIGHLIGHT_SLUG, parent,
                     {"itemText": identity, "itemText_ar": f"ميزة رئيسية {i} لمشروع الطاقة الشمسية",
                      "displayOrder": str(100 * i), "active_status": True}, identity)
        hl[i - 1] = identity
    require_active_status(admin, parent)
    d = _detail(anon_pages, parent.code, "en", lambda x: len(x.get("highlights", [])) >= 2)
    problems = []
    if overview not in d.get("body", ""):
        problems.append("Overview Body not rendered")
    if brief not in d.get("body", ""):
        problems.append(f"Investment Brief (4800 chars) not rendered intact (stored {len(stored_brief)} chars)")
    if d.get("highlights") != hl:
        problems.append(f"Key Highlights {d.get('highlights')} != {hl}")
    if d.get("submitter_name") != "Al Faisal Holding":
        problems.append(f"Submitted By name {d.get('submitter_name')!r}")
    if "Private" not in d.get("submitter_meta", "") or "Doha, Qatar" not in d.get("submitter_meta", ""):
        problems.append(f"Submitted By meta {d.get('submitter_meta')!r}")
    if not any(d.get("submitter_logo", [])):
        problems.append("Submitted By logo not loaded")
    stats = " | ".join(d.get("stats", []))
    for label, value in (("Type", "Equity"), ("Timeline", "12+ months"), ("Risk profile", "Medium")):
        if f"{label} {value}" not in stats:
            problems.append(f"Stats card lacks {label} = {value} ({stats})")
    assert not problems, "PRODUCT: the 01 Overview section does not render as authored: " + "; ".join(problems)


# ===========================================================================
# 143379 — Overview Body required; Investment Brief 5001 chars
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("01 Overview validation")
@allure.title("Publish is blocked when Overview Body is empty or Investment Brief exceeds 5000 characters")
@_markers("143379")
def test_overview_body_required_brief_limit(page, disposable):
    # Azure TC 143379 | Site Content Editor. Investment Brief is a RICH-TEXT field:
    # its 5000-character limit is Not Applicable (bug-rules Rule 5); the
    # required-Overview-Body rule is what this run judges.
    admin = login(page, ROLE_EDITOR)
    title = a_name("143379", "overview empty")
    data = OpportunityAdminPage.default_data(title)
    del data[K_OVERVIEW]
    del data[f"{K_OVERVIEW}_ar"]
    del data[K_BRIEF]
    brief = _text(5001, "Investment brief over the limit")
    ids_before = admin.snapshot_ids()
    admin.open_create_form_en()
    admin.fill_opportunity(data)
    admin.set_rich_html(K_BRIEF, f"<p>{brief}</p>")
    typed = len(admin.rich_text(K_BRIEF))
    pinned(admin, ROLE_EDITOR)
    admin.click_publish()
    outcome = {**admin.save_outcome(), "messages": admin.all_messages_text(), "field_errors": admin.field_error_owners(),
               "brief_len_in_editor": typed}
    admin.evidence("143379 publish attempt")
    allure.attach(repr(outcome), name="publish attempt")
    entry = admin.identify_created_entry(title, ids_before)
    if entry:
        disposable.track(entry)
    assert not outcome["went_through"] and entry is None, (
        f"PRODUCT: Publish with an EMPTY Overview Body was accepted: {outcome}")
    messages = outcome["messages"] + " " + " ".join(e["text"] for e in outcome["field_errors"])
    assert "Overview Body" in messages, f"Publish blocked, but no 'Overview Body is required' message: {messages!r}"


# ===========================================================================
# 143380 — 02 Investment Details + 2 Co-Investment rows, EN + AR
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("02 Investment Details")
@allure.title("Investment Details / Structure content authors and renders correctly on the public detail page")
@_markers("143380", regression=True)
def test_investment_details_render(page, anon_pages, disposable):
    # Azure TC 143380 | Site Content Editor.
    admin = login(page, ROLE_EDITOR)
    title = a_name("143380", "investment")
    rng, ticket = "QAR 2,000,000 - QAR 5,000,000", "QAR 250,000"
    parent = _publish_parent(admin, disposable, OpportunityAdminPage.default_data(
        title, **{K_AMOUNT_RANGE: rng, K_MIN_TICKET: ticket}))
    rows = [(a_name("143380", "Lead Investor"), "مستثمر رئيسي", "30%", "QAR 1,500,000"),
            (a_name("143380", "Co-Investor"), "مستثمر مشارك", "20%", "QAR 1,000,000")]
    for i, (label, label_ar, pct, value) in enumerate(rows, start=1):
        create_child(admin, disposable, CO_INVESTMENT_SLUG, parent,
                     {"label": label, "label_ar": label_ar, "percentage": pct, "value": value,
                      "displayOrder": str(100 * i), "active_status": True}, label)
    require_active_status(admin, parent)
    problems = []
    for locale in ("en", "ar"):
        d = _detail(anon_pages, parent.code, locale, lambda x: sum(r[0] in x.get("body", "") or r[1] in x.get("body", "")
                                                                   for r in rows) == 2)
        defs = d.get("defs", [])
        joined = " | ".join(defs)
        allure.attach(joined, name=f"Investment Details defs ({locale})")
        if rng not in joined:
            problems.append(f"{locale}: Investment amount {rng!r} missing ({joined})")
        if ticket not in joined:
            problems.append(f"{locale}: Minimum Ticket {ticket!r} missing")
        positions = []
        for label, label_ar, pct, value in rows:
            want_label = label if locale == "en" else label_ar
            match = [i for i, t in enumerate(defs) if want_label in t]
            if not match:
                problems.append(f"{locale}: co-investment row {want_label!r} missing")
                continue
            positions.append(match[0])
            row = defs[match[0]]
            if pct not in row or value not in row:
                problems.append(f"{locale}: row {want_label!r} reads {row!r} (expected {pct} / {value})")
        if positions != sorted(positions):
            problems.append(f"{locale}: co-investment rows not in the entered order ({positions})")
    assert not problems, "PRODUCT: Investment Details do not render as authored: " + "; ".join(problems)


# ===========================================================================
# 143381 — free-text Investment Amount and Percentage 130 rejected at save
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("02 Investment Details validation")
@allure.title("Investment Amount in a non-range format and a Co-Investment Percentage over 100 are rejected")
@_markers("143381")
def test_invalid_amount_and_percentage_rejected(page, disposable):
    # Azure TC 143381 | Site Content Editor | QCTEST records only (Active Status off: never public).
    admin = login(page, ROLE_EDITOR)
    amount = _attempt_publish_new(admin, disposable, OpportunityAdminPage.default_data(
        a_name("143381", "high value"), active_status=False, **{K_AMOUNT_RANGE: "high value"}))
    results = {"Investment Amount 'high value'": amount}
    parent = amount.get("created")
    if parent is None:  # amount refused: a valid parent is needed for the co-investment row
        parent = create_opportunity(admin, disposable, OpportunityAdminPage.default_data(
            a_name("143381", "parent"), active_status=False), publish=False)
    child = same_session(admin, CO_INVESTMENT_SLUG)
    child.owned_parent_ids.add(parent.entry_id)
    label = a_name("143381", "pct 130")
    ids_before = child.snapshot_ids()
    child.open_create_form_en()
    child.fill_child({"parent": parent.code, "label": label, "percentage": "130", "value": "QAR 1,000,000",
                      "displayOrder": "100", "active_status": False})
    typed = child.text_value("percentage")
    pinned(child, ROLE_EDITOR)
    child.click_publish()
    pct = {**child.save_outcome(), "messages": child.all_messages_text(), "typed": typed}
    child.evidence("143381 percentage 130 publish attempt")
    created = child.identify_created_entry(label, ids_before)
    if created:
        disposable.track(created)
    pct["created"] = created
    results["Co-Investment Percentage 130"] = pct
    allure.attach("\n".join(f"{k}: {v}" for k, v in results.items()), name="validation outcomes")
    accepted = {k: v["messages"] for k, v in results.items() if v.get("went_through") or v.get("created")}
    assert not accepted, (f"PRODUCT: invalid values were SAVED (expected 'Investment Amount must follow a valid range "
                          f"format' / 'Percentage cannot exceed 100'): {list(accepted)}")


# ===========================================================================
# 143382 — 4 gallery images + 4.8 MB PDF render; download is the exact file
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("03 Gallery & Supporting Documents")
@allure.title("Gallery images and a Downloadable Resource PDF render and the PDF downloads exactly as uploaded")
@_markers("143382", regression=True)
def test_gallery_and_resource_render_and_download(page, anon_pages, disposable):
    # Azure TC 143382 | Site Content Editor | gallery images picked from existing D&M files.
    admin = login(page, ROLE_EDITOR)
    parent = _publish_parent(admin, disposable, OpportunityAdminPage.default_data(a_name("143382", "gallery")))
    images = EXISTING_ROOT_IMAGES[:4]
    upload_sequence = []  # (image name, stored fileEntryId) in the order the items were added
    for i, image in enumerate(images, start=1):
        gal = same_session(admin, GALLERY_SLUG)
        identity = gal.gallery_identity(parent.entry_id, str(100 * i))
        item, item_admin = create_child(admin, disposable, GALLERY_SLUG, parent,
                                        {"galleryImage": f"pick:{image}", "displayOrder": str(100 * i),
                                         "active_status": True}, identity)
        item_admin.open_entry_en(item.code)
        upload_sequence.append((image, item_admin.file_field_value("galleryImage")))
    allure.attach("\n".join(f"{n}. {img} -> fileEntryId {fid}" for n, (img, fid) in enumerate(upload_sequence, 1)),
                  name="gallery upload sequence (stored file ids)")
    expected_ids = [fid for _, fid in upload_sequence]
    assert all(expected_ids) and len(set(expected_ids)) == 4, (
        f"cannot prove the gallery order: the 4 items do not store 4 distinct file ids ({upload_sequence})")
    pdf = make_pdf("g_qctest_feasibility-study.pdf", int(4.8 * 1024 * 1024))
    doc_title = a_name("143382", "Feasibility Study")
    _, res_admin = create_child(admin, disposable, RESOURCE_SLUG, parent,
                                {"documentTitle": doc_title, "documentTitle_ar": "دراسة الجدوى", "file": pdf,
                                 "file_stem": "g_qctest_feasibility-study", "displayOrder": "100",
                                 "active_status": True}, doc_title)
    uploaded_as = getattr(res_admin, "last_uploaded_name", "")
    allure.attach(uploaded_as, name="uploaded PDF name (left in Documents & Media)")
    require_active_status(admin, parent)
    problems = []
    d = _detail(anon_pages, parent.code, "en", lambda x: len(x.get("shots", [])) >= 4 and x.get("files"))
    if len(d.get("shots", [])) != 4:
        problems.append(f"gallery shows {len(d.get('shots', []))} images, not 4")
    shown_ids = [BizOppPublicView.attachment_id(src) for src in d.get("shots", [])]
    allure.attach(f"upload order {expected_ids}\npublic order {shown_ids}\nsrcs {d.get('shots')}",
                  name="gallery order: upload vs public")
    if shown_ids != expected_ids:
        problems.append(f"gallery order {shown_ids} != upload order {expected_ids}")
    row = next((f for f in d.get("files", []) if "Feasibility Study" in f["text"]), None)
    if not row:
        problems.append(f"no resource row 'Feasibility Study' ({d.get('files')})")
    else:
        if "4.8 MB" not in row["text"]:
            problems.append(f"resource row size text {row['text']!r} (expected '4.8 MB')")
        view = BizOppPublicView(anon_pages())
        view.open_detail(parent.code)
        href = next((h for h in row["hrefs"]), "")
        response = view.page.request.get(href, max_redirects=5, timeout=120000) if href else None
        body = response.body() if response else b""
        same = hashlib.sha256(body).hexdigest() == hashlib.sha256(open(pdf, "rb").read()).hexdigest()
        disposition = response.headers.get("content-disposition", "") if response else ""
        allure.attach(f"href {href}\nstatus {response.status if response else None}\nsize {len(body)}\n"
                      f"identical {same}\ncontent-disposition {disposition}", name="download check")
        if not same:
            problems.append(f"downloaded file differs from the uploaded PDF (size {len(body)} vs "
                            f"{len(open(pdf, 'rb').read())})")
        if uploaded_as and uploaded_as.split(".")[0] not in disposition and uploaded_as not in href:
            problems.append(f"downloaded file name does not match {uploaded_as!r} ({disposition!r})")
    ar = _detail(anon_pages, parent.code, "ar", lambda x: x.get("files"))
    if not any("دراسة الجدوى" in f["text"] for f in ar.get("files", [])):
        problems.append(f"AR resource title missing ({ar.get('files')})")
    assert not problems, "PRODUCT: gallery / downloadable resource do not render as authored: " + "; ".join(problems)


# ===========================================================================
# 143383 — 6 MB PDF rejected; 11th gallery image blocked
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("03 Gallery & Supporting Documents validation")
@allure.title("A Downloadable Resource over 5MB is rejected and a Gallery beyond 10 images is blocked")
@_markers("143383")
def test_resource_size_and_gallery_limit(page, anon_pages, disposable):
    # Azure TC 143383 | Site Content Editor.
    # Review re-check: the 10-image cap is exercised with PUBLISH (not only Save as Draft):
    # 10 gallery items are published on a Draft parent, the parent is published, an 11th
    # item is published on the now-Published parent and the parent is published again.
    # The 6 MB PDF is attempted exactly ONCE per run (a refused pick still lands in D&M).
    admin = login(page, ROLE_EDITOR)
    parent = create_opportunity(admin, disposable, OpportunityAdminPage.default_data(
        a_name("143383", "limits")), publish=False)
    # Step 2 — 6 MB PDF on the resource File field (nothing is saved).
    res = same_session(admin, RESOURCE_SLUG)
    res.open_create_form_en()
    big = make_pdf("g_qctest_6mb.pdf", 6 * 1024 * 1024)
    upload = res.attempt_upload_settled("file", big, stem="g_qctest_6mb")
    upload_view = {k: upload.get(k) for k in ("file", "status", "success", "errors", "attached", "field_text",
                                              "field_value", "field_errors", "body")}
    res.evidence("143383 6MB pdf attempt")
    allure.attach(repr(upload_view), name="6 MB upload attempt (one oversized PDF per run)")

    def _add_gallery(i: int) -> dict:
        gal = same_session(admin, GALLERY_SLUG)
        gal.owned_parent_ids.add(parent.entry_id)
        identity = gal.gallery_identity(parent.entry_id, str(100 * i))
        ids_before = gal.snapshot_ids()
        gal.open_create_form_en()
        gal.fill_child({"parent": parent.code,
                        "galleryImage": f"pick:{EXISTING_ROOT_IMAGES[(i - 1) % len(EXISTING_ROOT_IMAGES)]}",
                        "displayOrder": str(100 * i), "active_status": True})
        pinned(gal, ROLE_EDITOR)
        gal.click_publish()
        result = {"n": i, "went_through": gal.save_went_through(), "messages": gal.all_messages_text(),
                  "field_errors": gal.field_errors()}
        if i >= 10:
            gal.evidence(f"143383 gallery image {i} publish")
        created = gal.identify_created_entry(identity, ids_before)
        if created:
            disposable.track(created)
            gal.open_list_all()
            result["status"] = gal.row_status_of(created)
        result["created"] = bool(created)
        return result

    def _publish_parent_now(label: str) -> dict:
        admin.open_entry_en(parent.code)
        pinned(admin, ROLE_EDITOR)
        admin.click_publish()
        out = {"went_through": admin.save_went_through(), "messages": admin.all_messages_text(),
               "field_errors": admin.field_error_owners()}
        admin.evidence(f"143383 parent publish {label}")
        out["status"] = admin.wait_status(parent, ("Published", "Inactive"), timeout=60.0)
        allure.attach(repr(out), name=f"parent Publish ({label})")
        return out

    # Step 3 — 10 gallery images (Publish), parent published, then an 11th (Publish).
    outcomes = [_add_gallery(i) for i in range(1, 11)]
    allure.attach("\n".join(repr(o) for o in outcomes), name="gallery adds 1-10 (Publish)")
    failed = [o for o in outcomes if not o["created"]]
    assert not failed, f"gallery images of the first 10 could not be published: {failed}"
    parent_with_10 = _publish_parent_now("with 10 gallery items")
    eleventh = _add_gallery(11)
    allure.attach(repr(eleventh), name="11th gallery image (Publish, parent Published)")
    parent_with_11 = _publish_parent_now("with 11 gallery items")
    require_active_status(admin, parent)
    d = _detail(anon_pages, parent.code, "en", lambda x: len(x.get("shots", [])) >= 10)
    public_count = len(d.get("shots", []))
    allure.attach(f"public gallery shows {public_count} images", name="public gallery count")

    problems = []
    if upload["attached"]:
        problems.append(f"the 6 MB PDF was ACCEPTED into the File field ({upload_view['field_text']!r})")
    elif not any("5" in e and "MB" in e for e in (upload_view["errors"] or []) + (upload_view["field_errors"] or [])):
        problems.append(f"6 MB PDF not attached, but no 'File exceeds maximum size of 5MB' message: {upload_view}")
    if eleventh["created"]:
        problems.append(f"an 11th gallery image was PUBLISHED on a Published parent (no 'Maximum of 10 gallery "
                        f"images reached'): {eleventh}")
    if parent_with_11["went_through"] and eleventh["created"]:
        problems.append(f"the parent re-published with 11 active gallery items ({parent_with_11['status']}); "
                        f"public gallery shows {public_count} images")
    if not parent_with_10["went_through"]:
        problems.append(f"the parent with 10 gallery items could not be published: {parent_with_10}")
    assert not problems, "PRODUCT: " + "; ".join(problems)
