from app.core.pagination import CursorPage, OffsetPage


def test_cursor_page_no_more():
    page = CursorPage(data=["a", "b"], next_cursor=None, has_more=False)
    assert not page.has_more
    assert page.next_cursor is None


def test_cursor_page_has_more():
    page = CursorPage(data=["a", "b"], next_cursor="cursor123", has_more=True)
    assert page.has_more
    assert page.next_cursor == "cursor123"


def test_offset_page_create():
    page = OffsetPage.create(data=list(range(10)), page=2, page_size=10, total=25)
    assert page.total_pages == 3
    assert page.page == 2
    assert len(page.data) == 10
