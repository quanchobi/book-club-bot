import pytest
from unittest.mock import MagicMock, patch
import src.bot
from src.bot import BookSearchResult, search_books, grab_author

def test_search_books_empty():
    """Ensure it returns an empty list if no title or author provided"""
    assert search_books(None,None) == []

@patch('src.bot.requests.get')
def test_search_books_success(mock_get):
    """Test API parsing"""
    mock_response = MagicMock
    mock_response.json.return_value = {
        'docs': [
            {
                'title': 'El Silmarillion',
                'key': '/works/OL38403651W',
                'authors': [{'key': '/authors/OL456A'}]
            }
        ]
    }
    mock_get.return_value = mock_response
    results = search_books(title="Hobbit")
    assert len(results) == 1
    assert results[0].title == "The Hobbit"
    assert results[0].olid == "OL123W"
    assert "OL456A" in results[0].author_olids
