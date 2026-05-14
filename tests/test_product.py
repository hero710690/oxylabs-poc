import pytest
from unittest.mock import MagicMock
from scraper.product import scrape_products, _poll_until_done
from models import SearchResult, ProductData


MOCK_POLL_RESPONSE = {
    "id": "job_001",
    "status": "done",
}

MOCK_RESULTS_RESPONSE = {
    "results": [
        {
            "content": {
                "title": "Apple iPhone 14, 128GB, Midnight - Unlocked (Renewed)",
                "price": 301.49,
                "currency": "USD",
                "description": "This phone has been restored.",
                "product_details": {"brand": "Apple", "storage": "128GB", "color": "Midnight"},
                "is_prime_eligible": True,
                "delivery": [
                    {"type": "FREE delivery", "date": {"by": "Tomorrow, March 4"}}
                ],
            }
        }
    ],
}


def _make_search_result(asin: str, position: int) -> SearchResult:
    return SearchResult(
        position=position,
        asin=asin,
        title=f"iPhone {asin}",
        price=300.0,
        currency="USD",
        is_sponsored=False,
        url=f"https://www.amazon.com/dp/{asin}",
    )


def test_poll_until_done_returns_on_done():
    mock_client = MagicMock()
    mock_client.async_poll.return_value = MOCK_POLL_RESPONSE
    mock_client.async_get_results.return_value = MOCK_RESULTS_RESPONSE
    result = _poll_until_done(mock_client, "job_001", timeout=10, interval=0.01)
    assert "results" in result
    mock_client.async_get_results.assert_called_once_with("job_001")


def test_poll_until_done_retries_on_pending():
    mock_client = MagicMock()
    mock_client.async_poll.side_effect = [
        {"id": "job_001", "status": "pending"},
        {"id": "job_001", "status": "running"},
        {"id": "job_001", "status": "done"},
    ]
    mock_client.async_get_results.return_value = MOCK_RESULTS_RESPONSE
    result = _poll_until_done(mock_client, "job_001", timeout=30, interval=0.01)
    assert "results" in result
    assert mock_client.async_poll.call_count == 3


def test_scrape_products_batches_requests():
    mock_client = MagicMock()
    mock_client.async_submit.return_value = {"id": "job_001", "status": "pending"}
    mock_client.async_poll.return_value = MOCK_POLL_RESPONSE
    mock_client.async_get_results.return_value = MOCK_RESULTS_RESPONSE

    search_results = [_make_search_result(f"B0TEST{i:03d}", i) for i in range(1, 21)]
    products = scrape_products(search_results, client=mock_client, batch_size=10)

    # 20 products → 20 async_submit calls
    assert mock_client.async_submit.call_count == 20


def test_scrape_products_returns_product_data():
    mock_client = MagicMock()
    mock_client.async_submit.return_value = {"id": "job_001", "status": "pending"}
    mock_client.async_poll.return_value = MOCK_POLL_RESPONSE
    mock_client.async_get_results.return_value = MOCK_RESULTS_RESPONSE

    search_results = [_make_search_result("B0TEST001", 1)]
    products = scrape_products(search_results, client=mock_client, batch_size=10)

    assert len(products) == 1
    assert products[0].title == "Apple iPhone 14, 128GB, Midnight - Unlocked (Renewed)"
    assert products[0].price == 301.49
    assert products[0].is_prime is True
