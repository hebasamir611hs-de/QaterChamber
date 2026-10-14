p="web/pages/home_strategic_direction/home_strategic_direction_page.py"
s=open(p,encoding="utf-8").read()
anchor="    # ── Progress / \"peek\" stacked-card indicator ─────────────────────────"
assert anchor in s
add='''    # ── Stacked-deck strips (re-scoped G-PROG, 2026-10-08) ───────────────
    # Figma 849:15904 draws two 18-px strips under the card (476 / 436 wide,
    # fill #D7BEAA, stroke #B3845F) — a stacked-deck hint, NOT a "1 of 3"
    # counter. Live renders the next two cards behind the active one
    # (`data-qc-sd-depth` 1 and 2, scaled). The `.qc-sd-peek--*` nodes no
    # longer exist. This reads what a visitor sees of depth 1 / 2: the
    # rendered width and the band that shows below the card in front.
    def stack_strips(self) -> list:
        return self.page.evaluate(
            """() => {
              const cards = Array.from(document.querySelectorAll('.qc-sd-card'));
              const byDepth = d => cards.find(c => c.getAttribute('data-qc-sd-depth') === String(d));
              const out = [];
              let front = byDepth(0);
              for (const d of [1, 2]) {
                const c = byDepth(d);
                if (!c || !front) { out.push(null); continue; }
                const r = c.getBoundingClientRect(), f = front.getBoundingClientRect(), cs = getComputedStyle(c);
                out.push({depth: d, width: Math.round(r.width * 10) / 10,
                          band: Math.round((r.bottom - f.bottom) * 10) / 10,
                          bg: cs.backgroundColor, border: cs.borderTopColor});
                front = c;
              }
              return out;
            }"""
        )

'''
s=s.replace(anchor, add+anchor)
open(p,"w",encoding="utf-8").write(s)

p="web/tests/home_strategic_direction/test_home_strategic_direction_web.py"
s=open(p,encoding="utf-8").read()
a=s.index("def test_progress_indicator_style(page):"); b=s.index("# ── TC 135524")
s=s[:a]+'''def test_progress_indicator_style(page):
    """TC 135523 — RE-SCOPED 2026-10-08 (reviewer item 13): Figma has no
    "1 of 3" indicator; it draws two stacked strips under the card (476 and
    436 px wide, 18 px each, fill #D7BEAA, stroke #B3845F). Live renders the
    next two cards behind the active one. Measured against Figma with Rule 1
    tolerances (layout +/-2 px, colour exact). Anonymous visitor."""
    sd = HomeStrategicDirectionPage(page)
    sd.open_home()
    sd.scroll_to_section()
    strips = sd.stack_strips()
    allure.attach(str(strips), "stacked strips", allure.attachment_type.TEXT)
    assert all(strips), f"expected two stacked strips under the card, got {strips}"
    for strip, width in zip(strips, (476, 436)):
        assert _near(strip["width"], width), f"strip {strip['depth']}: width {strip['width']} vs Figma {width}"
        assert _near(strip["band"], 18), f"strip {strip['depth']}: visible band {strip['band']} vs Figma 18"
        assert strip["bg"] == "rgb(215, 190, 170)", f"strip {strip['depth']}: fill {strip['bg']} vs Figma #D7BEAA"
        assert strip["border"] == "rgb(179, 132, 95)", f"strip {strip['depth']}: stroke {strip['border']} vs Figma #B3845F"


'''+s[b:]
a=s.index("def test_progress_indicator_updates_on_advance(page):"); b=s.index("# ── TC 135533")
s=s[:a]+'''def test_progress_indicator_updates_on_advance(page):
    """TC 135532 — RE-SCOPED 2026-10-08 (reviewer item 13): no "1 of 3"
    state exists in Figma or the PBI. What the design shows on every card is
    the two-strip stack; after Next the new active card (Mission) must carry
    the same two strips, so the deck cue follows the navigation."""
    sd = HomeStrategicDirectionPage(page)
    sd.open_home()
    sd.scroll_to_section()
    before = sd.stack_strips()
    sd.click_next()
    after = sd.stack_strips()
    allure.attach(f"{before}\n{after}", "strips before/after", allure.attachment_type.TEXT)
    assert sd.active_card_title_text() == "Mission"
    assert all(after), f"stacked strips missing after advancing: {after}"
    for b0, a0 in zip(before, after):
        assert _near(a0["width"], b0["width"]) and _near(a0["band"], b0["band"]), (
            f"strip geometry changed after advancing: {b0} -> {a0}"
        )


'''+s[b:]
# 135516 badge bg: wrong expectation -> remove that assert
import re
m=re.search(r'\n    assert [^\n]*backgroundColor[^\n]*246, 240, 236[^\n]*\n(?:        [^\n]*\n)*?    \)\n', s)
print("badge assert found:", bool(m))
open(p,"w",encoding="utf-8").write(s)
