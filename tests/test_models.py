import pytest
from pydantic import ValidationError
from models import SearchResult, ProductData, ScrapedProduct


def test_search_result_valid():
    result = SearchResult(
        position=1,
        asin="B0TEST123",
        title="Apple iPhone 14, 128GB",
        price=301.49,
        currency="USD",
        is_sponsored=False,
        url="https://www.amazon.com/dp/B0TEST123",
    )
    assert result.position == 1
    assert result.asin == "B0TEST123"


def test_search_result_missing_optional_fields():
    result = SearchResult(
        position=1,
        asin="B0TEST123",
        title="Apple iPhone 14",
        url="https://www.amazon.com/dp/B0TEST123",
    )
    assert result.price is None
    assert result.currency is None
    assert result.is_sponsored is False


def test_product_data_valid():
    product = ProductData(
        title="Apple iPhone 14, 128GB, Midnight - Unlocked (Renewed)",
        price=301.49,
        currency="USD",
        description="This phone has been restored to working condition.",
        specifications={"brand": "Apple", "storage": "128GB"},
        is_prime=True,
        delivery="FREE delivery Tomorrow",
    )
    assert product.is_prime is True
    assert product.specifications["brand"] == "Apple"


def test_product_data_optional_fields():
    product = ProductData(
        title="Apple iPhone 14",
    )
    assert product.price is None
    assert product.description is None
    assert product.specifications is None
    assert product.is_prime is False
    assert product.delivery is None


def test_scraped_product_merges_search_and_product():
    product = ScrapedProduct(
        position=3,
        asin="B0TEST123",
        title="Apple iPhone 14, 128GB",
        price=301.49,
        currency="USD",
        is_sponsored=False,
        is_prime=True,
        description="Restored to working condition.",
        specifications={"brand": "Apple"},
        delivery="FREE delivery Tomorrow",
        url="https://www.amazon.com/dp/B0TEST123",
    )
    assert product.position == 3
    assert product.is_prime is True
    assert product.scraped_at is not None
