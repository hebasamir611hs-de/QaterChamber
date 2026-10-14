"""
cms/tests/business_council_membership/ne_checks.py - bodies for the 2026-10-07
batch of PBI 130719 (suite 140378) Priority-4 Control_Panel cases. Not a test
module. OFFLINE scripted, not executed.

Every write goes to a disposable "+ Add New" QCTEST Business Council Request
Page entry (Page Visible UNTICKED, the second visibility gate), reached through
_Council's guarded create path (live ids 183176 etc. are blocked from PUT /
PATCH / DELETE), and deleted BY ID in `finally`. The live entry 183176 is never
opened. Because a successful save on this drafts-off singleton type stores a
second page record immediately, the calling tests are CONDITIONAL: they run
only under reports/live-restore/live_restore.py's snapshot -> run -> restore
cycle (QC_LIVE_SINGLETON_RUN=183176), like their sibling live cases.
"""

from __future__ import annotations

import struct
import tempfile
from pathlib import Path

from cms.pages.business_council_membership.business_council_membership_admin_page import (
    BusinessCouncilMembershipRequestAdminPage as Sub,
    BusinessCouncilRequestPageAdminPage as Page,
)
from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.tests.sectoral_committees import cc_checks as cc

# Hero Image is not flagged required in FIELDS, but the live form refuses a save
# without it (tc_144520), so every QCTEST entry carries a valid one.
BASE_FILES = {"hero_image": cc.VALID_JPG}


def bmp_fixture() -> str:
    """A real 2x2 24-bit .bmp, generated in the temp dir (no committed fixture)."""
    dest = Path(tempfile.gettempdir()) / "qctest_ne_card_icon.bmp"
    if not dest.exists():
        row = b"\x00\x00\xff" * 2 + b"\x00\x00"  # 2 BGR pixels + 2 bytes padding to 4
        pixels = row * 2
        header = b"BM" + struct.pack("<IHHI", 54 + len(pixels), 0, 0, 54)
        dib = struct.pack("<IiiHHIIiiII", 40, 2, 2, 1, 24, 0, len(pixels), 2835, 2835, 0, 0)
        dest.write_bytes(header + dib + pixels)
    return str(dest)


def check_optional_empty_saves(page, tc: int, key: str, locale: str):
    """Account: Site Content Editor (cms_role_credentials). The case: `key` is
    optional, so leaving its `locale` side empty is accepted - Save succeeds,
    the field is stored empty and no validation error is shown. Every other
    required field gets its declared valid default; the other locale side of a
    bilingual field is filled, so only the case's side is empty."""
    admin = Page(page)
    spec = Page.FIELDS[key]
    title = cc.title(tc, f"empty-{locale}")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=(key,), active=False, files=BASE_FILES)
        if spec.bilingual and locale == "en":
            admin.fill(key, spec.default_ar or "قيمة اختبار", locale="ar")
        elif spec.bilingual and locale == "ar":
            admin.fill(key, spec.default or f"QCTEST {tc}")
        admin.submit_for_review()
        refused = admin.refusal_visible()
        eid = admin.id_for(title)
        assert not refused and eid, (
            f"{spec.label} {locale.upper()} left empty: the save was refused={refused}, stored id={eid} "
            f"({admin.save_counts()}) - the case expects the optional field to save empty")
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(title)
        stored = admin.value(key, locale if spec.bilingual else "en")
        assert not stored, f"{spec.label} {locale.upper()} was stored as {stored!r}, not empty"
    finally:
        cc._delete(admin, title)


def check_api_surface_absent(browser):
    """Logged-out: the feature's own object endpoints answer no data to an
    anonymous caller (401 / 403 / 404, or an empty item list), on BOTH the
    unscoped /o/c/<plural> and the site-scoped /o/c/<plural>/scopes/<groupId>
    form every fragment on this site uses. The groupId is read at run time from
    an anonymous load of the public page (Liferay.ThemeDisplay.getScopeGroupId()),
    not hard-coded. No other endpoint is guessed."""
    from config.settings import web_url
    from core.web.browser import new_context

    ctx = new_context(browser, use_auth_state=False)
    try:
        anon = ctx.new_page()
        anon.goto(web_url(cc.BCMR_PATH, locale="en"), wait_until="domcontentloaded")
        gid = anon.evaluate("() => (window.Liferay && Liferay.ThemeDisplay) ? Liferay.ThemeDisplay.getScopeGroupId() : ''")
        assert gid, "could not read the site groupId from the public page"
        seen = {}
        for path in (f"/o/c/{Sub.PLURAL}", f"/o/c/{Sub.PLURAL}/scopes/{gid}"):
            r = ctx.request.get(web_url(path), headers={"accept": "application/json"})
            body = r.text()
            items = None
            if r.status == 200:
                try:
                    items = (r.json() or {}).get("items")
                except Exception:  # noqa: BLE001 - HTML (e.g. a 'Coming Soon' page) is not an API response
                    items = None
            seen[path] = (r.status, body[:120])
            assert r.status != 200 or not items, (
                f"anonymous GET {path} returned {len(items)} record(s): {body[:200]!r}")
        print(f"[api-surface] {seen!r}")
    finally:
        ctx.close()
