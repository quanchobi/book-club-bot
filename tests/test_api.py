import pytest
from src.bot import search_by_title, search_by_isbn

class TestAPI:
    def test_search_by_isbn(self):
        book_title, authors, isbn = search_by_isbn('9780670033041')
        assert book_title == "East of Eden"
        assert authors == ["John Steinbeck"]
        assert isbn == '9780670033041'

    def test_search_by_title(self):
        book_title, authors, isbn = search_by_title('East of Eden')
        assert book_title == "East of Eden"
        assert authors == ["John Steinbeck"]
        assert isbn == '9780670033041'
