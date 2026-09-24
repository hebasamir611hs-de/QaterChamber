"""
web/tests/sitemap/test_sitemap_web.py

Web-platform cases for PBI 131053 ("Sitemap"), suite 140391: 141703 (EN URL
variants) and 141704 (AR URL variants). HTTP-only — no browser context.

SUBSTITUTION (disclosed): the cases name a seeded page 'QCTEST-SITEMAP-01' at
/about/qatar-chamber-vision (/ar/about/qatar-chamber-vision). That page does
not exist on qcdev. The equivalent live page is
/about-us/vision-mission-objectives (EN) and
/ar/about-us/vision-mission-objectives (AR), each listed with hreflang
en-US / ar-SA alternates — it is used as the concrete example, and the seeded
URL's absence is reported as a TEST DATA note (not a failure). The general
requirement is asserted too: EN URLs without /ar/, AR URLs with /ar/, the two
variants distinct and cross-linked by hreflang alternates.

The 266 child sitemaps that currently 404 are a separate bug (TC 141691, out
of scope): URLs are collected from the children that answer 200.
"""

import allure
import pytest

from config.settings import web_url
from web.pages.sitemap.sitemap_page import SitemapFeed

PBI = "131053"
EN_EXAMPLE = web_url("/about-us/vision-mission-objectives")
AR_EXAMPLE = web_url("/about-us/vision-mission-objectives", locale="ar")
SEEDED_EN = web_url("/about/qatar-chamber-vision")
SEEDED_AR = web_url("/about/qatar-chamber-vision", locale="ar")

pytestmark = [pytest.mark.web, pytest.mark.pbi_131053, pytest.mark.global_, pytest.mark.functional_low,
              pytest.mark.bilingual, pytest.mark.regression, pytest.mark.uat]


class _Check:
    def __init__(self, title):
        self.title, self.deviations, self.notes = title, [], []

    def truthy(self, label, condition, expected, actual):
        if not condition:
            self.deviations.append(f"{label}: expected {expected!r}, got {actual!r}")

    def assert_clean(self):
        if self.notes:
            allure.attach("\n".join(self.notes), "notes (test data / tolerated)", allure.attachment_type.TEXT)
        assert not self.deviations, f"{self.title}: {len(self.deviations)} deviation(s):\n  - " + "\n  - ".join(self.deviations)


def _common(check: _Check, feed: SitemapFeed):
    check.truthy("/sitemap.xml retrieved", feed.index_status == 200, 200, feed.index_status)
    counts = feed.child_status_counts()
    check.notes.append(f"child sitemaps by status (non-200 tolerated, see TC 141691): {counts}")
    check.truthy("at least one child sitemap readable", counts.get(200, 0) > 0, ">= 1 child with 200", counts)


@allure.epic("Global")
@allure.feature("Sitemap")
@allure.story("Language variants")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Sitemap includes English (EN) language URL variants")
@allure.label("pbi", PBI)
@allure.label("testcase", "141703")
@pytest.mark.tc_141703
def test_sitemap_english_variants():
    """Azure TC 141703 | PBI 131053 — EN variant published and listed without /ar/, with an ar-SA alternate."""
    check = _Check("TC 141703")
    feed = SitemapFeed()
    _common(check, feed)
    check.truthy("EN example page published", SitemapFeed.page_status("/about-us/vision-mission-objectives") == 200,
                 200, SitemapFeed.page_status("/about-us/vision-mission-objectives"))
    urls = feed.urls()
    en = [u for u in urls if "/ar/" not in u and not u.rstrip("/").endswith("/ar")]
    check.truthy("sitemap lists EN URLs (no /ar/ prefix)", len(en) > 0, ">= 1", len(en))
    check.truthy("EN entry for the example page", EN_EXAMPLE in urls, EN_EXAMPLE, [u for u in urls if "vision" in u])
    alts = feed.alternates(EN_EXAMPLE)
    check.truthy("EN entry has an en-US self alternate", alts.get("en-US") == EN_EXAMPLE, EN_EXAMPLE, alts.get("en-US"))
    check.truthy("EN entry links its AR variant (ar-SA)", alts.get("ar-SA") == AR_EXAMPLE, AR_EXAMPLE, alts.get("ar-SA"))
    if SEEDED_EN not in urls:
        check.notes.append(f"TEST DATA — seeded page QCTEST-SITEMAP-01 ({SEEDED_EN}) is not published/listed; "
                           f"status {SitemapFeed.page_status('/about/qatar-chamber-vision')}")
    check.assert_clean()


@allure.epic("Global")
@allure.feature("Sitemap")
@allure.story("Language variants")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Sitemap includes Arabic (AR) language URL variants")
@allure.label("pbi", PBI)
@allure.label("testcase", "141704")
@pytest.mark.tc_141704
def test_sitemap_arabic_variants():
    """Azure TC 141704 | PBI 131053 — AR variant published and listed with /ar/, distinct from EN, with an
    en-US alternate."""
    check = _Check("TC 141704")
    feed = SitemapFeed()
    _common(check, feed)
    check.truthy("AR example page published", SitemapFeed.page_status("/about-us/vision-mission-objectives", "ar") == 200,
                 200, SitemapFeed.page_status("/about-us/vision-mission-objectives", "ar"))
    urls = feed.urls()
    ar = [u for u in urls if "/ar/" in u]
    check.truthy("sitemap lists AR URLs (/ar/ prefix)", len(ar) > 0, ">= 1", len(ar))
    check.truthy("AR entry for the example page", AR_EXAMPLE in urls, AR_EXAMPLE, [u for u in urls if "vision" in u])
    check.truthy("AR entry distinct from the EN entry", AR_EXAMPLE != EN_EXAMPLE and EN_EXAMPLE in urls,
                 "both present and different", (AR_EXAMPLE in urls, EN_EXAMPLE in urls))
    alts = feed.alternates(AR_EXAMPLE)
    check.truthy("AR entry has an ar-SA self alternate", alts.get("ar-SA") == AR_EXAMPLE, AR_EXAMPLE, alts.get("ar-SA"))
    check.truthy("AR entry links its EN variant (en-US)", alts.get("en-US") == EN_EXAMPLE, EN_EXAMPLE, alts.get("en-US"))
    if SEEDED_AR not in urls:
        check.notes.append(f"TEST DATA — seeded page QCTEST-SITEMAP-01 ({SEEDED_AR}) is not published/listed")
    check.assert_clean()
