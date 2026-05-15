import pytest
from unittest.mock import MagicMock, patch
from scraper.search import search_iphones
from models import SearchResult


MOCK_SEARCH_RESPONSE = {
    "results": [
        {
            "content": {
                "results": {
                    "organic": [
                        {
                            "pos": 1,
                            "asin": "B0TEST001",
                            "title": "Apple iPhone 14, 128GB",
                            "price": 301.49,
                            "currency": "USD",
                            "url": "/dp/B0TEST001",
                            "is_sponsored": False,
                        },
                        {
                            "pos": 2,
                            "asin": "B0TEST002",
                            "title": "Apple iPhone 15, 256GB",
                            "price": 599.99,
                            "currency": "USD",
                            "url": "/dp/B0TEST002",
                            "is_sponsored": False,
                        },
                    ],
                    "paid": [
                        {
                            "pos": 3,
                            "asin": "B0SPONSOR",
                            "title": "Apple iPhone 13 Sponsored",
                            "price": 249.99,
                            "currency": "USD",
                            "url": "/dp/B0SPONSOR",
                        },
                    ],
                }
            }
        }
    ]
}


def test_search_iphones_returns_search_results():
    mock_client = MagicMock()
    mock_client.realtime.return_value = MOCK_SEARCH_RESPONSE

    results = search_iphones(client=mock_client, pages=1)

    assert len(results) == 3
    assert results[0].asin == "B0TEST001"
    assert results[0].position == 1
    assert results[0].is_sponsored is False
    assert results[2].asin == "B0SPONSOR"
    assert results[2].is_sponsored is True


def test_search_iphones_paginates():
    """Each page is a separate API call."""
    mock_client = MagicMock()
    mock_client.realtime.return_value = MOCK_SEARCH_RESPONSE

    results = search_iphones(client=mock_client, pages=3)

    assert mock_client.realtime.call_count == 3


def test_search_iphones_limits_to_100():
    mock_client = MagicMock()
    big_response = {
        "results": [
            {
                "content": {
                    "results": {
                        "organic": [
                            {
                                "pos": i,
                                "asin": f"B0TEST{i:03d}",
                                "title": f"Apple iPhone {i}",
                                "price": 300.0 + i,
                                "currency": "USD",
                                "url": f"/dp/B0TEST{i:03d}",
                                "is_sponsored": False,
                            }
                            for i in range(1, 51)
                        ],
                        "paid": [],
                    }
                }
            }
        ]
    }
    mock_client.realtime.return_value = big_response

    results = search_iphones(client=mock_client, pages=3, limit=100)

    assert len(results) == 100
