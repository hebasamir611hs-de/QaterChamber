"""
cms/tests/publications/conftest.py — fixtures for the PBI 130711 Publication
Control_Panel module (mirrors cms/tests/laws_regulations/conftest.py).

TEARDOWN: `disposable` deletes ONLY the records the test registered at
creation (entry id + exact QCTEST- title), through
PublicationAdminPage.delete_disposable_entry — the guarded path that
re-verifies prefix, full list expansion, exactly-one exact-title row and the
delete link's own label immediately before the click. Cleanup runs from a
TEST_USER setup context (cleanup only, never an assertion). Anything it cannot
remove fails the teardown loudly; nothing else is ever deleted.
"""

from __future__ import annotations

import allure
import pytest

from cms.pages.publications.publication_admin_page import (
    QCTEST_PREFIX,
    CreatedEntry,
    PublicationAdminPage,
)
from core.web.browser import new_context


class DisposableRegistry:
    """Records this test created. Per entry id it keeps every exact title the
    record may carry (a rename adds the new title BEFORE it is submitted)."""

    def __init__(self):
        self._titles: dict[str, list[str]] = {}
        self._removed: set[str] = set()

    @property
    def entries(self) -> list[tuple[str, list[str]]]:
        return [(eid, titles) for eid, titles in self._titles.items() if eid not in self._removed]

    def track(self, entry: CreatedEntry) -> CreatedEntry:
        if not entry.title.startswith(QCTEST_PREFIX):
            raise ValueError(f"{entry.title!r} is not a {QCTEST_PREFIX} record")
        self._titles.setdefault(entry.entry_id, [])
        if entry.title not in self._titles[entry.entry_id]:
            self._titles[entry.entry_id].append(entry.title)
        return entry

    def add_title(self, entry: CreatedEntry, new_title: str) -> CreatedEntry:
        return self.track(CreatedEntry(title=new_title, entry_id=entry.entry_id))

    def mark_removed(self, entry: CreatedEntry) -> None:
        self._removed.add(entry.entry_id)


@pytest.fixture
def disposable(browser):
    registry = DisposableRegistry()
    yield registry
    if not registry.entries:
        return
    ctx = new_context(browser)  # TEST_USER storageState — cleanup only
    outcome, failures = [], []
    try:
        cleaner = PublicationAdminPage(ctx.new_page())
        for entry_id, titles in registry.entries:
            label = f"{' / '.join(titles)} (id {entry_id})"
            try:
                cleaner.open_entries_list()
                live_title = cleaner.row_title(CreatedEntry(title=titles[0], entry_id=entry_id))
                if not live_title:
                    if cleaner.is_list_fully_expanded():
                        outcome.append(f"already gone: {label}")
                    else:
                        failures.append(f"{label}: not found and the list is NOT fully expanded")
                    continue
                if live_title not in titles:
                    failures.append(f"{label}: row now reads {live_title!r} — STOP, not deleted")
                    continue
                if cleaner.delete_disposable_entry(CreatedEntry(title=live_title, entry_id=entry_id)):
                    outcome.append(f"removed {live_title} (id {entry_id}) -> Recycle Bin")
                else:
                    failures.append(f"NOT removed {label}: guarded delete refused/failed (see log)")
            except Exception as exc:  # noqa: BLE001 — collected and raised below
                failures.append(f"{label}: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(outcome + failures) or "nothing to remove", name="QCTEST teardown")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def anon_pages(browser):
    """Fresh logged-out contexts for every public-visibility read."""
    contexts = []

    def _make():
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return ctx.new_page()

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


@pytest.fixture
def role_session(browser):
    """Factory: a fresh auth-free context as a PublicationAdminPage for a
    second account inside one test (e.g. the Editor-side setup of an Author
    test). The caller signs in with pub_support.pinned_login(admin, role)."""
    contexts = []

    def _make(role: str) -> PublicationAdminPage:
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return PublicationAdminPage(ctx.new_page())

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass
