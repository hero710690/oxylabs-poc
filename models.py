from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Data extracted from amazon_search results."""
    position: int
    asin: str
    title: str
    price: Optional[float] = None
    currency: Optional[str] = None
    is_sponsored: bool = False
    url: str


class ProductData(BaseModel):
    """Data extracted from amazon_product page."""
    title: str
    price: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[dict] = None
    is_prime: bool = False
    delivery: Optional[str] = None


class ScrapedProduct(BaseModel):
    """Final merged output: search metadata + product page data."""
    position: int
    asin: str
    title: str
    price: Optional[float] = None
    currency: Optional[str] = None
    is_sponsored: bool = False
    is_prime: bool = False
    description: Optional[str] = None
    specifications: Optional[dict] = None
    delivery: Optional[str] = None
    url: str
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
