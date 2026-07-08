"""Unit tests for SessionManager tab discovery and activation."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.automation.session import SessionManager, TabInfo


def _make_page(url: str, title: str = "Test") -> MagicMock:
    page = MagicMock()
    page.url = url
    page.title = AsyncMock(return_value=title)
    page.bring_to_front = AsyncMock()
    page.screenshot = AsyncMock()
    return page


def _make_browser(contexts_pages: list[list[tuple[str, str]]]) -> MagicMock:
    """Build browser mock: list of contexts, each with (url, title) page tuples."""
    contexts = []
    for pages_data in contexts_pages:
        context = MagicMock()
        context.pages = [_make_page(url, title) for url, title in pages_data]
        contexts.append(context)

    browser = MagicMock()
    browser.contexts = contexts
    return browser


@pytest.mark.parametrize(
    ("page_url", "expected"),
    [
        ("https://railmadad.indianrail.gov.in/", True),
        ("https://railmadad.indianrail.gov.in/login", True),
        ("https://railmadad.indianrail.gov.in", True),
        ("https://sub.railmadad.example.com/home", True),
        ("https://google.com", False),
        ("about:blank", False),
        ("chrome://newtab/", False),
    ],
)
def test_is_railmadad_url(page_url: str, expected: bool):
    base = "https://railmadad.indianrail.gov.in"
    assert SessionManager.is_railmadad_url(page_url, base) is expected


@pytest.mark.asyncio
async def test_discover_tabs_lists_all_contexts_and_tabs():
    browser = _make_browser(
        [
            [("https://google.com", "Google"), ("https://railmadad.indianrail.gov.in/", "RailMadad")],
            [("https://example.com", "Example")],
        ]
    )
    session = SessionManager(railmadad_url="https://railmadad.indianrail.gov.in")

    tabs = await session.discover_tabs(browser)

    assert len(tabs) == 3
    assert tabs[0].context_index == 0
    assert tabs[0].tab_index == 0
    assert tabs[0].url == "https://google.com"
    assert tabs[0].is_railmadad is False
    assert tabs[1].context_index == 0
    assert tabs[1].tab_index == 1
    assert tabs[1].is_railmadad is True
    assert tabs[2].context_index == 1
    assert tabs[2].tab_index == 0


@pytest.mark.asyncio
async def test_find_railmadad_tab_prefers_admin_report_over_public_portal():
    public = TabInfo(
        0,
        0,
        "https://railmadad.indianrailways.gov.in/madad/final/home.jsp",
        "RailMadad Public",
        True,
        _make_page("https://railmadad.indianrailways.gov.in/madad/final/home.jsp"),
    )
    admin_report = TabInfo(
        0,
        1,
        "https://railmadad.indianrailways.gov.in/rmmis/admin/home.jsp?page=/mis_reports/report1",
        "",
        True,
        _make_page(
            "https://railmadad.indianrailways.gov.in/rmmis/admin/home.jsp?page=/mis_reports/report1"
        ),
    )
    session = SessionManager()

    found = session.find_railmadad_tab([public, admin_report])

    assert found is admin_report


@pytest.mark.asyncio
async def test_find_railmadad_tab_prefers_url_fragment_when_provided():
    admin_other = TabInfo(
        0,
        0,
        "https://railmadad.indianrailways.gov.in/rmmis/admin/home.jsp?page=/mis_reports/other",
        "",
        True,
        _make_page(
            "https://railmadad.indianrailways.gov.in/rmmis/admin/home.jsp?page=/mis_reports/other"
        ),
    )
    admin_report1 = TabInfo(
        0,
        1,
        "https://railmadad.indianrailways.gov.in/rmmis/admin/home.jsp?page=/mis_reports/report1",
        "",
        True,
        _make_page(
            "https://railmadad.indianrailways.gov.in/rmmis/admin/home.jsp?page=/mis_reports/report1"
        ),
    )
    session = SessionManager()

    found = session.find_railmadad_tab(
        [admin_other, admin_report1],
        prefer_url_fragment="mis_reports/report1",
    )

    assert found is admin_report1


@pytest.mark.asyncio
async def test_find_railmadad_tab_returns_first_match():
    page = _make_page("https://railmadad.indianrail.gov.in/dashboard")
    tabs = [
        TabInfo(0, 0, "https://google.com", "Google", False, _make_page("https://google.com")),
        TabInfo(0, 1, page.url, "RailMadad", True, page),
    ]
    session = SessionManager()

    found = session.find_railmadad_tab(tabs)

    assert found is not None
    assert found.url == page.url
    assert found.is_railmadad is True


def test_find_railmadad_tab_returns_none_when_missing():
    tabs = [
        TabInfo(0, 0, "https://google.com", "Google", False, _make_page("https://google.com")),
    ]
    session = SessionManager()

    assert session.find_railmadad_tab(tabs) is None


@pytest.mark.asyncio
async def test_activate_tab_brings_page_to_front():
    page = _make_page("https://railmadad.indianrail.gov.in/")
    session = SessionManager()

    await session.activate_tab(page)

    page.bring_to_front.assert_awaited_once()
    assert session.page is page


@pytest.mark.asyncio
async def test_capture_screenshot_saves_file(tmp_path: Path):
    page = _make_page("https://railmadad.indianrail.gov.in/")
    session = SessionManager()

    path = await session.capture_screenshot(page, tmp_path)

    assert path.startswith(str(tmp_path))
    assert path.endswith(".png")
    page.screenshot.assert_awaited_once()
    kwargs = page.screenshot.call_args.kwargs
    assert kwargs["full_page"] is True


def test_tab_info_format_line():
    tab = TabInfo(
        context_index=0,
        tab_index=1,
        url="https://railmadad.indianrail.gov.in/",
        title="RailMadad",
        is_railmadad=True,
        page=_make_page("https://railmadad.indianrail.gov.in/"),
    )
    assert tab.format_line() == "[ctx=0 tab=1] https://railmadad.indianrail.gov.in/ (RailMadad)"
