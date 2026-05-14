import json
import os
import pytest
from unittest.mock import MagicMock, patch
from main import run_scrape_job, save_results
from models import SearchResult, ProductData, ScrapedProduct


@patch("main.scrape_products")
@patch("main.search_iphones")
def test_run_scrape_job_returns_scraped_products(mock_search, mock_scrape):
    mock_search.return_value = [
        SearchResult(
            position=1, asin="B0TEST001", title="iPhone 14",
            price=301.49, currency="USD", is_sponsored=False,
            url="https://www.amazon.com/dp/B0TEST001",
        )
    ]
    mock_scrape.return_value = {
        "B0TEST001": ProductData(
            title="iPhone 14 Full", price=301.49, currency="USD",
            description="Restored.", specifications={"brand": "Apple"},
            is_prime=True, delivery="FREE delivery",
        )
    }

    results = run_scrape_job()
    assert len(results) == 1
    assert results[0].position == 1
    assert results[0].is_prime is True
    assert results[0].description == "Restored."


def test_save_results_creates_json_file(tmp_path):
    products = [
        ScrapedProduct(
            position=1, asin="B0TEST001", title="iPhone 14",
            price=301.49, currency="USD", is_sponsored=False,
            is_prime=True, description="Test", specifications={"brand": "Apple"},
            delivery="FREE", url="https://www.amazon.com/dp/B0TEST001",
        )
    ]

    filepath = save_results(products, output_dir=str(tmp_path))

    assert os.path.exists(filepath)
    with open(filepath) as f:
        data = json.load(f)
    assert len(data["products"]) == 1
    assert data["products"][0]["asin"] == "B0TEST001"
    assert "metadata" in data
    assert data["metadata"]["total_products"] == 1
