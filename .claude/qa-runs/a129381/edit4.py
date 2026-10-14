p="cms/pages/home_strategic_direction/home_strategic_direction_admin_page.py"
s=open(p,encoding="utf-8").read()
a=s.index("    def _verify_code(self, code: str, title: str) -> bool:")
b=s.index("    def _remember_saved(")
new='''    def _read_title(self, code: str) -> str | None:
        """Pillar Title (EN) read off the entry's own form, or None when the
        form did not load. HEALED 2026-10-07 (run 2121): open_entry_by_code()'s
        8 s banner wait timed out under load, so a real QCTEST record read as
        "not mine" and its status came back ''. Waits on the field itself."""
        if not code or code.startswith(self.REAL_CODE_PREFIX):
            return None
        try:
            self.open(self._manage_url(edit_entry=code, locale="en"))
            self._entry_code = code
            box = self.page.get_by_role("textbox", name=self.label_pattern("Pillar Title"))
            box.first.wait_for(state="visible", timeout=30000)
            return box.first.input_value()
        except Exception:  # noqa: BLE001
            return None

    def _verify_code(self, code: str, title: str) -> bool:
        return self._read_title(code) == title

    def code_for(self, title: str, refresh: bool = False, wait: bool = True) -> str:
        """Verified entry code for `title`, or "" when no entry carries it.
        Re-lists up to 3 times when a candidate's form did not load, or (with
        `wait`) when a just-saved record has not reached the list yet."""
        import time

        if not refresh and title in self._codes:
            return self._codes[title]
        found = ""
        for attempt in range(3):
            self.open_entries_list(locale="en")
            self.filter_entries(title)
            candidates = [
                code for code, entry_id in self._row_codes()
                if code and not code.startswith(self.REAL_CODE_PREFIX) and entry_id not in REAL_PILLAR_IDS
            ]
            unreadable = False
            for code in candidates:
                got = self._read_title(code)
                if got is None:
                    unreadable = True
                elif got == title:
                    if found and found != code:
                        raise RefusedDelete(f"two entries carry Pillar Title {title!r}: {found}, {code}")
                    found = code
            if found or not (unreadable or wait):
                break
            time.sleep(5)
        if found:
            self._codes[title] = found
        else:
            self._codes.pop(title, None)
        return found

'''
s=s[:a]+new+s[b:]
s=s.replace("""    def row_visible(self, title: str) -> bool:
        return bool(self.code_for(title, refresh=True))""","""    def row_visible(self, title: str) -> bool:
        return bool(self.code_for(title, refresh=True, wait=False))""")
s=s.replace("""        self.sign_in(role)
        return bool(self.code_for(title, refresh=True))""","""        self.sign_in(role)
        return bool(self.code_for(title, refresh=True, wait=False))""")
s=s.replace("""            code = self.code_for(title, refresh=True)  # verified: form title == title""","""            code = self.code_for(title, refresh=True, wait=False)  # verified: form title == title""")
s=s.replace("""            self.open_entry_by_code(code, locale="en")
            form_title = self.value("pillar_title")
            if form_title != title:""","""            form_title = self._read_title(code)
            if form_title != title:""")
open(p,"w",encoding="utf-8").write(s)
