p="cms/pages/home_strategic_direction/home_strategic_direction_admin_page.py"
s=open(p,encoding="utf-8").read()
a=s.index("    def delete_disposable(self, title: str, role: str = ROLE_EDITOR) -> bool:")
b=s.index("    # ---- conveniences ---------------------------------------------------")
new='''    def _delete_verified_code(self, code: str, title: str) -> bool:
        """Delete ONE entry by its code after re-proving it is `title` (a
        QCTEST title): form re-read, single row, label == code, id not real."""
        if not title.startswith(DISPOSABLE_PREFIX):
            raise RefusedDelete(f"refusing to delete non-QCTEST record {title!r}")
        if not code or code.startswith(self.REAL_CODE_PREFIX):
            raise RefusedDelete(f"{title!r} resolved to real/empty code {code!r}")
        form_title = self._read_title(code)
        if form_title != title:
            raise RefusedDelete(f"{code}: form Pillar Title {form_title!r} != {title!r}")
        self.open_entries_list(locale="en")
        self.filter_entries(code)
        rows = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{code}")')
        if rows.count() != 1:
            raise RefusedDelete(f"{rows.count()} rows match code {code!r}")
        delete_link = rows.first.locator("a[data-qc-oel-delete]").first
        entry_id = delete_link.get_attribute("data-qc-oel-delete") or ""
        label = delete_link.get_attribute("data-qc-oel-label") or ""
        if not entry_id or entry_id in REAL_PILLAR_IDS or label != code:
            raise RefusedDelete(f"{code}: delete link id={entry_id!r} label={label!r}; refusing")
        link = self.page.locator(f'a[data-qc-oel-delete="{entry_id}"]')
        if link.count() != 1:
            raise RefusedDelete(f"{link.count()} delete links for id {entry_id}")
        self.page.once("dialog", lambda d: d.accept())
        link.click(force=True)
        try:
            link.wait_for(state="detached", timeout=15000)
        except Exception:  # noqa: BLE001 — verified below by re-listing
            pass
        # Verify by re-listing: teardown "delete failed" warnings have been false before.
        self.open_entries_list(locale="en")
        self.filter_entries(code)
        return self.page.locator(f'a[data-qc-oel-delete="{entry_id}"]').count() == 0

    def _codes_with_title(self, title: str) -> list:
        self.open_entries_list(locale="en")
        self.filter_entries(title)
        out = []
        for code, entry_id in self._row_codes():
            if code and not code.startswith(self.REAL_CODE_PREFIX) and entry_id not in REAL_PILLAR_IDS:
                if code not in self._UNTITLED and self._read_title(code) == title:
                    out.append(code)
        return out

    def delete_disposable(self, title: str, role: str = ROLE_EDITOR) -> bool:
        """Guarded delete — see the module docstring's SAFETY CONTRACT.
        Deletes EVERY entry whose own form reads exactly this QCTEST title
        (Save as Draft can leave two copies — see report), each by its own
        verified code. Raises RefusedDelete on any identity doubt; returns
        False when nothing carrying the title was found or a click did not
        stick."""
        if not title or not title.startswith(DISPOSABLE_PREFIX):
            raise RefusedDelete(f"refusing to delete non-QCTEST record {title!r}")
        try:
            self.sign_in(role)
            codes = self._codes_with_title(title)
            if not codes:
                return False
            ok = all([self._delete_verified_code(code, title) for code in codes])
            if ok:
                self._codes.pop(title, None)
            return ok
        except RefusedDelete:
            raise
        except Exception:  # noqa: BLE001 — teardown never masks the test result
            return False

'''
s=s[:a]+new+s[b:]
# code_for: duplicates -> pick first but don't raise (deletion handles all copies)
s=s.replace('''                    if found and found != code:
                        raise RefusedDelete(f"two entries carry Pillar Title {title!r}: {found}, {code}")
                    found = code''','''                    # Save as Draft can leave two copies with the same title (see
                    # report); reads use the first, delete_disposable() removes all.
                    found = found or code''')
open(p,"w",encoding="utf-8").write(s)
