"""
web/pages/sitemap/sitemap_page.py — SitemapFeed.

HTTP-level object for PBI 131053 ("Sitemap"). No UI is involved: the cases
inspect /sitemap.xml, so this object fetches and parses XML with the
standard library (urllib + xml.etree) — no new dependency, no browser.

Live shape (CONFIRMED 2026-09-24): /sitemap.xml is a <sitemapindex> of 347
child sitemaps (/sitemap.xml?p_l_id=…&layoutUuid=…). 81 children answer 200
with a <urlset>; 266 answer 404 (a separate bug tracked on TC 141691 — out of
scope here, so collection TOLERATES it and reads only the 200 children).
Each <url> carries <xhtml:link rel="alternate" hreflang="…"> alternates.
"""

import functools
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

from config.settings import web_url

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9", "xhtml": "http://www.w3.org/1999/xhtml"}


def _get(url: str, timeout: int = 60):
    req = urllib.request.Request(url, headers={"User-Agent": "qc-automation/sitemap-check"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, ""
    except Exception as err:  # noqa: BLE001 — network error recorded as status text
        return str(err), ""


@functools.lru_cache(maxsize=1)
def _collect() -> dict:
    status, body = _get(web_url("/sitemap.xml"))
    result = {"index_status": status, "children": [], "entries": {}}
    if status != 200:
        return result
    root = ET.fromstring(body)
    children = [e.text.strip() for e in root.findall("sm:sitemap/sm:loc", NS)]
    with ThreadPoolExecutor(max_workers=12) as pool:
        fetched = list(pool.map(lambda u: (u, *_get(u)), children))
    for url, st, text in fetched:
        result["children"].append({"url": url, "status": st})
        if st != 200 or not text:
            continue
        for node in ET.fromstring(text).findall("sm:url", NS):
            loc = node.findtext("sm:loc", default="", namespaces=NS).strip()
            alts = {l.get("hreflang"): l.get("href") for l in node.findall("xhtml:link", NS)}
            result["entries"][loc] = alts
    return result


class SitemapFeed:
    """Read-only view over the collected sitemap (cached per process)."""

    def __init__(self):
        self.data = _collect()

    @property
    def index_status(self):
        return self.data["index_status"]

    def child_status_counts(self) -> dict:
        counts = {}
        for c in self.data["children"]:
            counts[c["status"]] = counts.get(c["status"], 0) + 1
        return counts

    def urls(self) -> list:
        return list(self.data["entries"])

    def alternates(self, url: str) -> dict:
        return self.data["entries"].get(url, {})

    @staticmethod
    def page_status(path: str, locale: str = "en"):
        return _get(web_url(path, locale=locale))[0]
