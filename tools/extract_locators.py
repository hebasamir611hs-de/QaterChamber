#!/usr/bin/env python3
"""
extract_locators.py — CLI-first locator extractor (web / Playwright).

Purpose: the token-cheap default for locator extraction and healing (see
automation-standards.md -> "Tooling priority"). It navigates the live page in the shell,
harvests ONLY the interactive/labelled elements the flow touches, and prints a COMPACT,
RANKED candidate list with uniqueness counts. The full DOM never enters the model context.

Run it (headless by default):
    python tools/extract_locators.py --url https://uat.example.com/contact-us
    python tools/extract_locators.py --url .../login --scope "form" --find "email"
    python tools/extract_locators.py --url .../account --storage-state .auth/state.json

Auth: for pages behind login, capture a Playwright storageState once and pass it with
--storage-state (cheapest — no scripted login here). Only fall back to the Playwright MCP
when a state genuinely can't be reached by script or an element is ambiguous.

Output is one line per element, ranked best-tier first:
    [testid ] uniq=1  get_by_test_id("email")                 -> "Email address"
    [role   ] uniq=1  get_by_role("button", name="Submit")    -> "Submit"
    [id     ] uniq=1  #firstName                               -> "First name"
    [css    ] uniq=2  input[name="phone"]                      -> "Phone"
"""
import argparse
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright not installed. Run: pip install playwright && playwright install chromium")

# Best -> worst. The extractor prefers the highest tier that is UNIQUE on the page.
TIER_ORDER = ["testid", "role", "id", "css"]

# In-page harvest: collect only interactive / labelled elements, with the attributes
# needed to build a locator. Returns compact records — never the whole DOM.
JS_HARVEST = r"""
(scope) => {
  const root = scope ? document.querySelector(scope) : document;
  if (!root) return [];
  const SEL = 'a,button,input,select,textarea,[role],[data-testid],[data-test],[aria-label],[contenteditable="true"]';
  const roleFor = (el) => {
    if (el.getAttribute('role')) return el.getAttribute('role');
    const t = el.tagName.toLowerCase();
    if (t === 'a' && el.hasAttribute('href')) return 'link';
    if (t === 'button') return 'button';
    if (t === 'select') return 'combobox';
    if (t === 'textarea') return 'textbox';
    if (t === 'input') {
      const it = (el.getAttribute('type') || 'text').toLowerCase();
      return {checkbox:'checkbox',radio:'radio',button:'button',submit:'button',
              reset:'button',range:'slider',number:'spinbutton'}[it] || 'textbox';
    }
    return '';
  };
  const nameFor = (el) => {
    const aria = el.getAttribute('aria-label');
    if (aria) return aria.trim();
    if (el.id) {
      const lab = document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
      if (lab && lab.textContent.trim()) return lab.textContent.trim();
    }
    const ph = el.getAttribute('placeholder');
    if (ph) return ph.trim();
    const txt = (el.textContent || '').trim().replace(/\s+/g, ' ');
    return txt.slice(0, 80);
  };
  const out = [];
  const seen = new Set();
  root.querySelectorAll(SEL).forEach((el) => {
    if (seen.has(el)) return; seen.add(el);
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;                 // skip hidden
    const st = getComputedStyle(el);
    if (st.visibility === 'hidden' || st.display === 'none') return;
    out.push({
      tag: el.tagName.toLowerCase(),
      testid: el.getAttribute('data-testid') || el.getAttribute('data-test') || '',
      id: el.id || '',
      name: el.getAttribute('name') || '',
      type: el.getAttribute('type') || '',
      role: roleFor(el),
      label: nameFor(el),
    });
  });
  return out;
}
"""


def build_candidate(page, rec):
    """Return (tier, locator_string, count) for the best UNIQUE tier, else best available."""
    label = rec["label"]
    candidates = []

    if rec["testid"]:
        loc = page.get_by_test_id(rec["testid"])
        candidates.append(("testid", f'get_by_test_id("{rec["testid"]}")', loc))
    if rec["role"] and label:
        loc = page.get_by_role(rec["role"], name=label, exact=False)
        safe = label.replace('"', '\\"')
        candidates.append(("role", f'get_by_role("{rec["role"]}", name="{safe}")', loc))
    if rec["id"]:
        loc = page.locator(f'#{rec["id"]}')
        candidates.append(("id", f'#{rec["id"]}', loc))
    if rec["name"]:
        loc = page.locator(f'{rec["tag"]}[name="{rec["name"]}"]')
        candidates.append(("css", f'{rec["tag"]}[name="{rec["name"]}"]', loc))

    best = None
    for tier, s, loc in candidates:
        try:
            c = loc.count()
        except Exception:
            continue
        if c == 1:
            return tier, s, 1                       # unique — take the highest such tier
        if best is None:
            best = (tier, s, c)
    return best  # may be None if nothing resolved


def main():
    ap = argparse.ArgumentParser(description="CLI-first web locator extractor")
    ap.add_argument("--url", required=True)
    ap.add_argument("--scope", default=None, help="CSS to limit harvesting to a container")
    ap.add_argument("--find", default=None, help="only show candidates whose label matches this (case-insensitive)")
    ap.add_argument("--storage-state", default=None, help="Playwright storageState JSON for a pre-authed session")
    ap.add_argument("--viewport", default="1920x1080")
    ap.add_argument("--max", type=int, default=40)
    ap.add_argument("--timeout", type=int, default=15000)
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    w, h = (int(x) for x in args.viewport.lower().split("x"))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        ctx_kwargs = {"viewport": {"width": w, "height": h}}
        if args.storage_state:
            ctx_kwargs["storage_state"] = args.storage_state
        ctx = browser.new_context(**ctx_kwargs)
        page = ctx.new_page()
        page.set_default_timeout(args.timeout)
        page.goto(args.url, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass

        records = page.evaluate(JS_HARVEST, args.scope)
        rows, tier_rank = [], {t: i for i, t in enumerate(TIER_ORDER)}
        for rec in records:
            if args.find and args.find.lower() not in (rec["label"] or "").lower():
                continue
            got = build_candidate(page, rec)
            if not got:
                continue
            tier, s, count = got
            rows.append((tier_rank.get(tier, 9), count != 1, tier, count, s, rec["label"]))

        rows.sort(key=lambda r: (r[0], r[1]))          # best tier first, unique first
        rows = rows[: args.max]

        print(f'# {len(rows)} candidate locator(s) on {args.url}'
              f'{" (scope: " + args.scope + ")" if args.scope else ""}')
        print(f'# tiers: testid > role > id > css   |   uniq=1 means the locator is unique\n')
        for _, _, tier, count, s, label in rows:
            flag = "" if count == 1 else f"  ⚠ NON-UNIQUE (matches {count})"
            lab = (label or "").replace("\n", " ")
            print(f'[{tier:6}] uniq={count}  {s:<48} -> "{lab[:60]}"{flag}')
        if not rows:
            print("# (no interactive/labelled elements found — widen --scope, drop --find, "
                  "or fall back to the Playwright MCP for this state)")
        browser.close()


if __name__ == "__main__":
    main()
