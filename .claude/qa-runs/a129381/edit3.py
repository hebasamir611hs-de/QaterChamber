p="web/pages/home_strategic_direction/home_strategic_direction_page.py"
s=open(p,encoding="utf-8").read()
old_open='''    def open_home(self) -> "HomeStrategicDirectionPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        return self

    def open_home_arabic(self) -> "HomeStrategicDirectionPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        return self
'''
new_open='''    def open_home(self) -> "HomeStrategicDirectionPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        self.pause_autoplay()
        return self

    def open_home_arabic(self) -> "HomeStrategicDirectionPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        self.pause_autoplay()
        return self

    def pause_autoplay(self) -> "HomeStrategicDirectionPage":
        """CONFIRMED LIVE 2026-10-07 (.claude/qa-runs/a129381/probe2/3.json):
        the carousel AUTO-ADVANCES about 6 s after load (Vision -> Mission,
        EN and AR), and stays put while the pointer is over `.qc-sd-stage`
        (24 samples over 18 s, all Vision). Tests that read "the card shown
        on load" or step with the arrows hover the stage first so autoplay
        cannot move the carousel under them."""
        try:
            self.page.locator(self.STAGE).scroll_into_view_if_needed()
            self.page.locator(self.STAGE).hover()
        except Exception:  # noqa: BLE001 — best effort; assertions stay strict
            pass
        return self
'''
assert old_open in s; s=s.replace(old_open,new_open)
old_vis='''        return self.page.locator(self.CARD).evaluate_all(
            "els => els.filter(el => parseFloat(getComputedStyle(el).opacity) > 0)"
            ".map(el => el.querySelector('.qc-sd-card-title')?.textContent || null)"
        )'''
new_vis='''        # HEALED 2026-10-07: all 3 cards now compute opacity 1 and are
        # STACKED (probe2.json + manual-repro-129381-carousel-en-t0.png show
        # one card in front, two "peek" edges behind), so opacity no longer
        # separates the shown card. The shown card is the one carrying
        # `.is-active`; that is what a visitor sees in front.
        return self.page.locator(f"{self.CARD}.is-active").evaluate_all(
            "els => els.map(el => el.querySelector('.qc-sd-card-title')?.textContent || null)"
        )'''
assert old_vis in s; s=s.replace(old_vis,new_vis)
old_click='''        old_title = self.active_card_title_text()
        self.click(arrow_locator)
        self.page.wait_for_function(
            "(old) => { const t = document.querySelector('.qc-sd-card.is-active .qc-sd-card-title'); "
            "return t && t.textContent !== old; }",
            arg=old_title,
        )'''
new_click=old_click+'''
        self.pause_autoplay()  # pointer left the stage for the arrow click'''
assert old_click in s; s=s.replace(old_click,new_click)
open(p,"w",encoding="utf-8").write(s)
