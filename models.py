from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Data extracted from amazon_search results."""
    position: int
    asin: str
    title: str
    price: Optional[float] = None
    currency: Optional[str] = None
    is_sponsored: bool = False
    is_prime: bool = False
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    is_best_seller: bool = False
    is_amazons_choice: bool = False
    sales_volume: Optional[str] = None
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
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    sales_rank: Optional[List[dict]] = None
    brand: Optional[str] = None
    coupon: Optional[str] = None


class PricingOffer(BaseModel):
    """A single seller offer from amazon_pricing."""
    seller_name: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    condition: Optional[str] = None
    shipping_price: Optional[float] = None
    is_prime: bool = False
    is_fulfilled_by_amazon: bool = False


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
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    sales_rank: Optional[List[dict]] = None
    brand: Optional[str] = None
    coupon: Optional[str] = None
    is_best_seller: bool = False
    is_amazons_choice: bool = False
    sales_volume: Optional[str] = None
    pricing_offers: Optional[List[PricingOffer]] = None
    url: str
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
