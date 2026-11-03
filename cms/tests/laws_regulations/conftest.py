"""
cms/tests/laws_regulations/conftest.py — fixtures shared by the PBI 130699
Law Regulation modules (moved unchanged out of
test_laws_regulations_control_panel.py so the field-validation module reuses
them instead of duplicating them).

TEARDOWN: `disposable` tracks every CreatedEntry the test captured at
creation and deletes exactly those (id + exact title + QCTEST-130699- prefix
re-verified immediately before each click, inside
LawsRegulationsAdminPage.delete_disposable_entry) from a TEST_USER
setup-level context — cleanup only, never an assertion. Anything it cannot
remove fails the teardown loudly. There is no other delete path.
"""

from __future__ import annotations

import allure
import pytest

from cms.pages.laws_regulations.laws_regulations_admin_page import (
    QCTEST_PREFIX,
    CreatedEntry,
    LawsRegulationsAdminPage,
)
from core.web.browser import new_context


class DisposableRegistry:
    """Records this test created. Only these are ever deleted.

    Per entry id it keeps the SET of exact titles the record may carry: a
    test that renames its own record adds the new title BEFORE submitting,
    so teardown can still identify the row whether or not the rename saved."""

    def __init__(self):
        self._titles: dict[str, list[str]] = {}
        self._removed: set[str] = set()

    @property
    def entries(self) -> list[tuple[str, list[str]]]:
        """[(entry_id, known titles)] still owed a teardown."""
        return [(eid, titles) for eid, titles in self._titles.items() if eid not in self._removed]

    def track(self, entry: CreatedEntry) -> CreatedEntry:
        self._titles.setdefault(entry.entry_id, [])
        if entry.title not in self._titles[entry.entry_id]:
            self._titles[entry.entry_id].append(entry.title)
        return entry

    def add_title(self, entry: CreatedEntry, new_title: str) -> CreatedEntry:
        """Call BEFORE submitting a rename of the test's own record."""
        if not new_title.startswith(QCTEST_PREFIX):
            raise ValueError(f"{new_title!r} leaves the {QCTEST_PREFIX} namespace")
        return self.track(CreatedEntry(title=new_title, entry_id=entry.entry_id))

    def mark_removed(self, entry: CreatedEntry) -> None:
        """The test itself deleted its record through delete_disposable_entry()."""
        self._removed.add(entry.entry_id)


@pytest.fixture
def disposable(browser):
    registry = DisposableRegistry()
    yield registry
    if not registry.entries:
        return
    ctx = new_context(browser)  # TEST_USER storageState — cleanup only
    outcome = []
    failures = []
    try:
        cleaner = LawsRegulationsAdminPage(ctx.new_page())
        for entry_id, titles in registry.entries:
            label = f"{' / '.join(titles)} (id {entry_id})"
            try:
                cleaner.open_list()
                live_title = cleaner.row_title(CreatedEntry(title=titles[0], entry_id=entry_id))
                if not live_title:
                    if not cleaner.is_list_fully_expanded():
                        failures.append(
                            f"{label}: row not found and the list is NOT fully expanded "
                            f"({cleaner.rendered_row_count()} of {cleaner.total_entry_count()} rows) — "
                            f"cannot tell whether it still exists"
                        )
                    else:
                        outcome.append(f"NOT removed {label}: absent from the fully expanded list")
                    continue
                if live_title not in titles:
                    failures.append(f"{label}: row now reads {live_title!r}, not a known title — STOP, not deleted")
                    continue
                target = CreatedEntry(title=live_title, entry_id=entry_id)
                if not cleaner.delete_disposable_entry(target):
                    failures.append(f"NOT removed {label}: delete_disposable_entry returned False")
                elif cleaner.row_present(target) or not cleaner.is_list_fully_expanded():
                    failures.append(f"{label}: removal not confirmed on a fully expanded list")
                else:
                    outcome.append(f"removed {live_title} (id {entry_id}) -> Recycle Bin")
            except Exception as exc:  # noqa: BLE001 — collected and raised below, never swallowed
                failures.append(f"{label}: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(outcome + failures) or "nothing to remove", name="QCTEST teardown")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def anon_pages(browser):
    """Fresh logged-out contexts for every public-visibility read
    (standards.md: mandatory logged-out context)."""
    contexts = []

    def _make():
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return ctx.new_page()

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001 — teardown must never mask the real result
            pass


@pytest.fixture
def admin_reader(browser):
    """A TEST_USER context used ONLY to read list metadata (Last modified) of a
    real record — never to change anything."""
    ctx = new_context(browser)
    yield LawsRegulationsAdminPage(ctx.new_page())
    ctx.close()
