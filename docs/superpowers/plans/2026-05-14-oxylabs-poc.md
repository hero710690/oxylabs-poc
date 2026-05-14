# Oxylabs Web Scraper API PoC — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working Python PoC that scrapes the top 100 iPhone listings on Amazon US using Oxylabs Web Scraper API, visits each product page for detailed data, runs hourly, and outputs timestamped JSON.

**Architecture:** Two-phase pipeline (search → product pages) with batch async/polling for product scraping. APScheduler for hourly runs. Pydantic for data validation. Retry with exponential backoff.

**Tech Stack:** Python 3.11+, requests, pydantic, apscheduler, python-dotenv, tenacity (retry)

---

## File Structure

| File | Responsibility |
|------|---------------|
| `config.py` | Load env vars, define constants (batch size, retry params, search query) |
| `models.py` | Pydantic models for search results and product data |
| `scraper/__init__.py` | Package init |
| `scraper/client.py` | Low-level Oxylabs API wrapper (POST, polling, retry) |
| `scraper/search.py` | Phase 1: paginated amazon_search, extract ASINs + metadata |
| `scraper/product.py` | Phase 2: batch amazon_product with async/polling |
| `main.py` | Entry point, orchestration, scheduler, JSON output |
| `tests/test_models.py` | Model validation tests |
| `tests/test_client.py` | API client tests (mocked HTTP) |
| `tests/test_search.py` | Search phase tests |
| `tests/test_product.py` | Product phase tests |
| `tests/test_main.py` | Integration/orchestration tests |
| `.env.example` | Template for credentials |
| `requirements.txt` | Dependencies |

---

### Task 1: Project Setup + Config

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `config.py`

- [ ] **Step 1: Create requirements.txt**

```
requests>=2.31.0
pydantic>=2.5.0
apscheduler>=3.10.4
python-dotenv>=1.0.0
tenacity>=8.2.0
pytest>=7.4.0
pytest-mock>=3.12.0
responses>=0.24.0
```

- [ ] **Step 2: Create .env.example**

```
OXYLABS_USERNAME=your_username
OXYLABS_PASSWORD=your_password
```

- [ ] **Step 3: Create config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

# FEATURE: Oxylabs API credentials
OXYLABS_USERNAME = os.getenv("OXYLABS_USERNAME")
OXYLABS_PASSWORD = os.getenv("OXYLABS_PASSWORD")

# API endpoints
REALTIME_URL = "https://realtime.oxylabs.io/v1/queries"
ASYNC_URL = "https://data.oxylabs.io/v1/queries"

# Search config
SEARCH_QUERY = "iPhone"
SEARCH_DOMAIN = "com"
SEARCH_PAGES = 3  # ~48 results/page → 100+ listings
RESULTS_LIMIT = 100

# FEATURE: geo_location — lock results to US market
GEO_LOCATION = "United States"

# Batch config
BATCH_SIZE = 10  # product pages per batch
POLL_INTERVAL = 5  # seconds between status checks
POLL_TIMEOUT = 300  # max seconds to wait for a batch

# Retry config
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # exponential backoff base in seconds

# Output
OUTPUT_DIR = "output"
```

- [ ] **Step 4: Install dependencies**

Run: `pip install -r requirements.txt`

- [ ] **Step 5: Commit**

```bash
git init
git add requirements.txt .env.example config.py
git commit -m "feat: project setup with config and dependencies"
```

---

### Task 2: Pydantic Models

**Files:**
- Create: `models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for models**

Create `tests/__init__.py` (empty) and `tests/test_models.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — `models` module not found

- [ ] **Step 3: Implement models**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add models.py tests/__init__.py tests/test_models.py
git commit -m "feat: add Pydantic models for search results and product data"
```

---

### Task 3: Oxylabs API Client (with retry)

**Files:**
- Create: `scraper/__init__.py`
- Create: `scraper/client.py`
- Create: `tests/test_client.py`

- [ ] **Step 1: Write failing tests for the client**

```python
import pytest
import responses
from responses import matchers
from scraper.client import OxylabsClient


@responses.activate
def test_realtime_request_success():
    responses.post(
        "https://realtime.oxylabs.io/v1/queries",
        json={"results": [{"content": {"results": {"organic": []}}}]},
        status=200,
    )
    client = OxylabsClient(username="test", password="test")
    payload = {"source": "amazon_search", "query": "iPhone", "parse": True}
    result = client.realtime(payload)
    assert result == {"results": [{"content": {"results": {"organic": []}}}]}


@responses.activate
def test_realtime_request_retries_on_500():
    responses.post(
        "https://realtime.oxylabs.io/v1/queries",
        json={"error": "server error"},
        status=500,
    )
    responses.post(
        "https://realtime.oxylabs.io/v1/queries",
        json={"results": [{"content": {}}]},
        status=200,
    )
    client = OxylabsClient(username="test", password="test")
    payload = {"source": "amazon_search", "query": "iPhone"}
    result = client.realtime(payload)
    assert result == {"results": [{"content": {}}]}


@responses.activate
def test_async_submit_returns_job_id():
    responses.post(
        "https://data.oxylabs.io/v1/queries",
        json={"id": "job_123", "status": "pending"},
        status=200,
    )
    client = OxylabsClient(username="test", password="test")
    payload = {"source": "amazon_product", "query": "B0TEST123", "parse": True}
    job = client.async_submit(payload)
    assert job["id"] == "job_123"


@responses.activate
def test_async_poll_returns_done():
    responses.get(
        "https://data.oxylabs.io/v1/queries/job_123",
        json={"id": "job_123", "status": "done", "results": [{"content": {}}]},
        status=200,
    )
    client = OxylabsClient(username="test", password="test")
    result = client.async_poll("job_123")
    assert result["status"] == "done"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_client.py -v`
Expected: FAIL — `scraper.client` not found

- [ ] **Step 3: Implement the client**

Create `scraper/__init__.py` (empty) and `scraper/client.py`:

```python
import logging
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_result

import config

logger = logging.getLogger(__name__)


def _is_server_error(response):
    return response is not None and isinstance(response, requests.Response) and response.status_code >= 500


class OxylabsClient:
    """Low-level wrapper around Oxylabs Web Scraper API."""

    def __init__(self, username: str = None, password: str = None):
        self.username = username or config.OXYLABS_USERNAME
        self.password = password or config.OXYLABS_PASSWORD
        self.auth = (self.username, self.password)

    # FEATURE: Realtime endpoint — synchronous request/response
    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(multiplier=config.RETRY_BACKOFF_BASE),
        reraise=True,
    )
    def realtime(self, payload: dict) -> dict:
        """Send a synchronous request to the realtime endpoint."""
        logger.info(f"Realtime request: source={payload.get('source')}")
        response = requests.post(
            config.REALTIME_URL,
            json=payload,
            auth=self.auth,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    # FEATURE: Async endpoint — submit job for background processing
    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(multiplier=config.RETRY_BACKOFF_BASE),
        reraise=True,
    )
    def async_submit(self, payload: dict) -> dict:
        """Submit an async job. Returns job metadata including ID."""
        logger.info(f"Async submit: source={payload.get('source')}")
        response = requests.post(
            config.ASYNC_URL,
            json=payload,
            auth=self.auth,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    # FEATURE: Async polling — check job status
    def async_poll(self, job_id: str) -> dict:
        """Poll for async job status/results."""
        url = f"{config.ASYNC_URL}/{job_id}"
        response = requests.get(url, auth=self.auth, timeout=30)
        response.raise_for_status()
        return response.json()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_client.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scraper/__init__.py scraper/client.py tests/test_client.py
git commit -m "feat: add Oxylabs API client with retry and async support"
```

---

### Task 4: Search Phase (Phase 1)

**Files:**
- Create: `scraper/search.py`
- Create: `tests/test_search.py`

- [ ] **Step 1: Write failing tests for search**

```python
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


@patch("scraper.search.OxylabsClient")
def test_search_iphones_returns_search_results(mock_client_cls):
    mock_client = MagicMock()
    mock_client.realtime.return_value = MOCK_SEARCH_RESPONSE
    mock_client_cls.return_value = mock_client

    results = search_iphones(client=mock_client)

    assert len(results) == 3
    assert results[0].asin == "B0TEST001"
    assert results[0].position == 1
    assert results[0].is_sponsored is False
    assert results[2].asin == "B0SPONSOR"
    assert results[2].is_sponsored is True


@patch("scraper.search.OxylabsClient")
def test_search_iphones_paginates(mock_client_cls):
    mock_client = MagicMock()
    mock_client.realtime.return_value = MOCK_SEARCH_RESPONSE
    mock_client_cls.return_value = mock_client

    results = search_iphones(client=mock_client, pages=3)

    assert mock_client.realtime.call_count == 3


@patch("scraper.search.OxylabsClient")
def test_search_iphones_limits_to_100(mock_client_cls):
    mock_client = MagicMock()
    # Return 50 organic results per page
    big_response = {
        "results": [
            {
                "content": {
                    "results": {
                        "organic": [
                            {
                                "pos": i,
                                "asin": f"B0TEST{i:03d}",
                                "title": f"iPhone {i}",
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
    mock_client_cls.return_value = mock_client

    results = search_iphones(client=mock_client, pages=3, limit=100)

    assert len(results) == 100
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_search.py -v`
Expected: FAIL — `scraper.search` not found

- [ ] **Step 3: Implement search phase**

```python
import logging
from typing import List

from scraper.client import OxylabsClient
from models import SearchResult
import config

logger = logging.getLogger(__name__)


def search_iphones(
    client: OxylabsClient = None,
    pages: int = config.SEARCH_PAGES,
    limit: int = config.RESULTS_LIMIT,
) -> List[SearchResult]:
    """
    Phase 1: Search Amazon for iPhones using paginated requests.
    Returns up to `limit` SearchResult objects with position and sponsored metadata.
    """
    if client is None:
        client = OxylabsClient()

    all_results: List[SearchResult] = []

    for page_num in range(1, pages + 1):
        if len(all_results) >= limit:
            break

        # FEATURE: amazon_search source — structured search results
        # FEATURE: parse: true — auto-parsed JSON output
        # FEATURE: geo_location — lock to US market
        # FEATURE: Pagination (start_page) — collect across multiple pages
        payload = {
            "source": "amazon_search",
            "query": config.SEARCH_QUERY,
            "domain": config.SEARCH_DOMAIN,
            "start_page": page_num,
            "parse": True,
            "geo_location": config.GEO_LOCATION,
        }

        logger.info(f"Searching page {page_num}/{pages}")
        response = client.realtime(payload)

        page_results = _parse_search_response(response, len(all_results))
        all_results.extend(page_results)

    return all_results[:limit]


def _parse_search_response(response: dict, offset: int) -> List[SearchResult]:
    """Parse Oxylabs search response into SearchResult models."""
    results = []
    content = response["results"][0]["content"]["results"]

    # Parse organic results
    for item in content.get("organic", []):
        results.append(
            SearchResult(
                position=offset + len(results) + 1,
                asin=item["asin"],
                title=item.get("title", ""),
                price=item.get("price"),
                currency=item.get("currency"),
                is_sponsored=False,
                url=f"https://www.amazon.com/dp/{item['asin']}",
            )
        )

    # Parse sponsored/paid results
    for item in content.get("paid", []):
        results.append(
            SearchResult(
                position=offset + len(results) + 1,
                asin=item["asin"],
                title=item.get("title", ""),
                price=item.get("price"),
                currency=item.get("currency"),
                is_sponsored=True,
                url=f"https://www.amazon.com/dp/{item['asin']}",
            )
        )

    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_search.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scraper/search.py tests/test_search.py
git commit -m "feat: add search phase with pagination and geo_location"
```

---

### Task 5: Product Phase (Phase 2 — Async/Polling + Batch)

**Files:**
- Create: `scraper/product.py`
- Create: `tests/test_product.py`

- [ ] **Step 1: Write failing tests for product scraping**

```python
import pytest
from unittest.mock import MagicMock, patch, call
import time
from scraper.product import scrape_products, _poll_until_done
from models import SearchResult, ProductData


MOCK_PRODUCT_RESPONSE = {
    "id": "job_001",
    "status": "done",
    "results": [
        {
            "content": {
                "title": "Apple iPhone 14, 128GB, Midnight - Unlocked (Renewed)",
                "price": 301.49,
                "currency": "USD",
                "description": "This phone has been restored.",
                "specifications": {"brand": "Apple", "storage": "128GB", "color": "Midnight"},
                "is_prime": True,
                "delivery_info": "FREE delivery Tomorrow, March 4",
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
    mock_client.async_poll.return_value = {"id": "job_001", "status": "done", "results": []}
    result = _poll_until_done(mock_client, "job_001", timeout=10, interval=1)
    assert result["status"] == "done"


def test_poll_until_done_retries_on_pending():
    mock_client = MagicMock()
    mock_client.async_poll.side_effect = [
        {"id": "job_001", "status": "pending"},
        {"id": "job_001", "status": "running"},
        {"id": "job_001", "status": "done", "results": []},
    ]
    result = _poll_until_done(mock_client, "job_001", timeout=30, interval=0.01)
    assert result["status"] == "done"
    assert mock_client.async_poll.call_count == 3


def test_scrape_products_batches_requests():
    mock_client = MagicMock()
    mock_client.async_submit.return_value = {"id": "job_001", "status": "pending"}
    mock_client.async_poll.return_value = MOCK_PRODUCT_RESPONSE

    search_results = [_make_search_result(f"B0TEST{i:03d}", i) for i in range(1, 21)]
    products = scrape_products(search_results, client=mock_client, batch_size=10)

    # 20 products, batch_size=10 → 20 async_submit calls (one per product)
    assert mock_client.async_submit.call_count == 20


def test_scrape_products_returns_product_data():
    mock_client = MagicMock()
    mock_client.async_submit.return_value = {"id": "job_001", "status": "pending"}
    mock_client.async_poll.return_value = MOCK_PRODUCT_RESPONSE

    search_results = [_make_search_result("B0TEST001", 1)]
    products = scrape_products(search_results, client=mock_client, batch_size=10)

    assert len(products) == 1
    assert products[0].title == "Apple iPhone 14, 128GB, Midnight - Unlocked (Renewed)"
    assert products[0].price == 301.49
    assert products[0].is_prime is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_product.py -v`
Expected: FAIL — `scraper.product` not found

- [ ] **Step 3: Implement product phase**

```python
import logging
import time
from typing import List, Optional

from scraper.client import OxylabsClient
from models import SearchResult, ProductData
import config

logger = logging.getLogger(__name__)


def scrape_products(
    search_results: List[SearchResult],
    client: OxylabsClient = None,
    batch_size: int = config.BATCH_SIZE,
) -> List[ProductData]:
    """
    Phase 2: Scrape individual product pages using async/polling mode.
    Submits requests in batches, polls for completion, returns ProductData list.
    """
    if client is None:
        client = OxylabsClient()

    all_products: List[ProductData] = []

    # FEATURE: Batch submission — process products in chunks
    for i in range(0, len(search_results), batch_size):
        batch = search_results[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(search_results) + batch_size - 1) // batch_size
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} products)")

        batch_products = _process_batch(client, batch)
        all_products.extend(batch_products)

    logger.info(f"Scraped {len(all_products)}/{len(search_results)} products successfully")
    return all_products


def _process_batch(client: OxylabsClient, batch: List[SearchResult]) -> List[ProductData]:
    """Submit a batch of product requests and poll for results."""
    jobs = []

    for item in batch:
        # FEATURE: amazon_product source — individual product page data
        # FEATURE: parse: true — structured auto-parsed output
        # FEATURE: geo_location — US market
        # FEATURE: Async/Polling mode — non-blocking product scraping
        payload = {
            "source": "amazon_product",
            "query": item.asin,
            "domain": config.SEARCH_DOMAIN,
            "parse": True,
            "geo_location": config.GEO_LOCATION,
        }

        try:
            job = client.async_submit(payload)
            jobs.append({"job_id": job["id"], "search_result": item})
        except Exception as e:
            logger.warning(f"Failed to submit job for ASIN {item.asin}: {e}")

    # Poll all jobs for completion
    products = []
    for job_info in jobs:
        try:
            result = _poll_until_done(
                client,
                job_info["job_id"],
                timeout=config.POLL_TIMEOUT,
                interval=config.POLL_INTERVAL,
            )
            product = _parse_product_response(result)
            if product:
                products.append(product)
        except Exception as e:
            asin = job_info["search_result"].asin
            logger.warning(f"Failed to get product data for ASIN {asin}: {e}")

    return products


def _poll_until_done(
    client: OxylabsClient,
    job_id: str,
    timeout: int = config.POLL_TIMEOUT,
    interval: int = config.POLL_INTERVAL,
) -> dict:
    """Poll an async job until status is 'done' or timeout."""
    start_time = time.time()

    while True:
        result = client.async_poll(job_id)
        status = result.get("status")

        if status == "done":
            return result
        if status == "faulted":
            raise RuntimeError(f"Job {job_id} faulted: {result}")

        elapsed = time.time() - start_time
        if elapsed >= timeout:
            raise TimeoutError(f"Job {job_id} timed out after {timeout}s")

        time.sleep(interval)


def _parse_product_response(response: dict) -> Optional[ProductData]:
    """Parse Oxylabs product response into ProductData model."""
    try:
        content = response["results"][0]["content"]
        return ProductData(
            title=content.get("title", "Unknown"),
            price=content.get("price"),
            currency=content.get("currency"),
            description=content.get("description"),
            specifications=content.get("specifications"),
            is_prime=content.get("is_prime", False),
            delivery=content.get("delivery_info"),
        )
    except (KeyError, IndexError) as e:
        logger.warning(f"Failed to parse product response: {e}")
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_product.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scraper/product.py tests/test_product.py
git commit -m "feat: add product phase with async/polling and batch processing"
```

---

### Task 6: Main Orchestration + Scheduler

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write failing tests for orchestration**

```python
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
    mock_scrape.return_value = [
        ProductData(
            title="iPhone 14 Full", price=301.49, currency="USD",
            description="Restored.", specifications={"brand": "Apple"},
            is_prime=True, delivery="FREE delivery",
        )
    ]

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_main.py -v`
Expected: FAIL — `main` imports not found

- [ ] **Step 3: Implement main.py**

```python
import json
import logging
import os
from datetime import datetime, timezone
from typing import List

from apscheduler.schedulers.blocking import BlockingScheduler

from scraper.client import OxylabsClient
from scraper.search import search_iphones
from scraper.product import scrape_products
from models import SearchResult, ProductData, ScrapedProduct
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_scrape_job() -> List[ScrapedProduct]:
    """Execute the full scraping pipeline: search → product pages → merge."""
    logger.info("=== Starting scrape job ===")
    client = OxylabsClient()

    # Phase 1: Search
    logger.info("Phase 1: Searching for top iPhone listings...")
    search_results = search_iphones(client=client)
    logger.info(f"Found {len(search_results)} listings from search")

    # Phase 2: Product pages
    logger.info("Phase 2: Scraping individual product pages...")
    product_data = scrape_products(search_results, client=client)
    logger.info(f"Scraped {len(product_data)} product pages")

    # Merge search metadata with product data
    merged = _merge_results(search_results, product_data)
    logger.info(f"Merged {len(merged)} complete product records")

    return merged


def _merge_results(
    search_results: List[SearchResult],
    product_data: List[ProductData],
) -> List[ScrapedProduct]:
    """Merge search-level metadata with product page data."""
    merged = []

    for i, (search, product) in enumerate(zip(search_results, product_data)):
        merged.append(
            ScrapedProduct(
                position=search.position,
                asin=search.asin,
                title=product.title or search.title,
                price=product.price or search.price,
                currency=product.currency or search.currency,
                is_sponsored=search.is_sponsored,
                is_prime=product.is_prime,
                description=product.description,
                specifications=product.specifications,
                delivery=product.delivery,
                url=search.url,
            )
        )

    return merged


def save_results(products: List[ScrapedProduct], output_dir: str = config.OUTPUT_DIR) -> str:
    """Save scraped products to a timestamped JSON file."""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"iphones_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    output = {
        "metadata": {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total_products": len(products),
            "query": config.SEARCH_QUERY,
            "geo_location": config.GEO_LOCATION,
        },
        "products": [p.model_dump(mode="json") for p in products],
    }

    with open(filepath, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"Results saved to {filepath}")
    return filepath


def scheduled_job():
    """Wrapper for the scheduler — runs the pipeline and saves output."""
    try:
        results = run_scrape_job()
        save_results(results)
        logger.info(f"=== Job complete: {len(results)} products scraped ===")
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)


def main():
    """Entry point: run once immediately, then schedule hourly."""
    logger.info("Oxylabs PoC — Amazon iPhone Scraper")
    logger.info("Running initial scrape...")
    scheduled_job()

    logger.info("Starting hourly scheduler...")
    scheduler = BlockingScheduler()
    scheduler.add_job(scheduled_job, "interval", hours=1)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_main.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add main orchestration with scheduler and JSON output"
```

---

### Task 7: Callback Mode (Documented Alternative)

**Files:**
- Create: `scraper/callback.py`

- [ ] **Step 1: Create callback module as documented alternative**

This file demonstrates the callback approach but is not used in the main flow. It shows the client how they could receive results via webhook instead of polling.

```python
"""
FEATURE: Async/Callback mode — alternative to polling.

Instead of polling for job completion, Oxylabs can POST results directly
to a callback URL when the job finishes. This is more efficient for
production workloads as it eliminates polling overhead.

Usage:
    1. Set up a webhook endpoint (e.g., Flask/FastAPI server)
    2. Pass callback_url in the payload
    3. Oxylabs POSTs results to your endpoint when done

This module is a documented alternative — the main PoC uses polling mode.
See scraper/product.py for the primary implementation.
"""

import logging
from typing import Optional

from scraper.client import OxylabsClient
import config

logger = logging.getLogger(__name__)


def submit_with_callback(
    asin: str,
    callback_url: str,
    client: OxylabsClient = None,
) -> dict:
    """
    Submit an async product scrape with a callback URL.

    FEATURE: Async/Callback mode
    Instead of polling, Oxylabs will POST results to callback_url when done.

    Example callback_url: "https://your-server.com/webhooks/oxylabs"

    The callback payload will contain the same structure as a poll response
    with status "done" and the results array.
    """
    if client is None:
        client = OxylabsClient()

    # FEATURE: callback_url — Oxylabs sends results to this URL when job completes
    payload = {
        "source": "amazon_product",
        "query": asin,
        "domain": config.SEARCH_DOMAIN,
        "parse": True,
        "geo_location": config.GEO_LOCATION,
        "callback_url": callback_url,
    }

    logger.info(f"Submitting ASIN {asin} with callback to {callback_url}")
    return client.async_submit(payload)


# Example Flask webhook handler (for documentation purposes):
#
# from flask import Flask, request
#
# app = Flask(__name__)
#
# @app.route("/webhooks/oxylabs", methods=["POST"])
# def handle_oxylabs_callback():
#     data = request.json
#     job_id = data["id"]
#     results = data["results"]
#     # Process and store results...
#     return "", 200
```

- [ ] **Step 2: Commit**

```bash
git add scraper/callback.py
git commit -m "feat: add callback mode as documented alternative"
```

---

### Task 8: Documentation — FEATURES.md

**Files:**
- Create: `docs/FEATURES.md`

- [ ] **Step 1: Write FEATURES.md**

```markdown
# Oxylabs Web Scraper API — Features Used

This document maps every Oxylabs feature used in this PoC to its location in the code.

## Feature Matrix

| # | Feature | File | Line/Function | Purpose |
|---|---------|------|---------------|---------|
| 1 | `amazon_search` source | `scraper/search.py` | `search_iphones()` | Paginated search results for "iPhone" on Amazon US |
| 2 | `amazon_product` source | `scraper/product.py` | `_process_batch()` | Individual product page data extraction |
| 3 | `parse: true` | `scraper/search.py`, `scraper/product.py` | Both payload constructions | Structured auto-parsed JSON output (no manual HTML parsing) |
| 4 | `geo_location` | `scraper/search.py`, `scraper/product.py` | Both payloads | Locks results to United States market |
| 5 | Pagination (`start_page`) | `scraper/search.py` | `search_iphones()` loop | Collects 100 results across 3 pages |
| 6 | Async/Polling mode | `scraper/product.py` | `_poll_until_done()` | Non-blocking batch product scraping |
| 7 | Async/Callback mode | `scraper/callback.py` | `submit_with_callback()` | Documented alternative — webhook-based results delivery |
| 8 | Batch submission | `scraper/product.py` | `scrape_products()` | Processes 100 products in chunks of 10 |
| 9 | Realtime endpoint | `scraper/client.py` | `realtime()` | Synchronous search requests |
| 10 | Async endpoint | `scraper/client.py` | `async_submit()` | Background job submission |

## Feature Details

### 1. amazon_search (Realtime)
Used for the search phase. Sends a synchronous request to get paginated search results.
The `parse: true` flag means Oxylabs returns structured JSON with organic/paid results already
separated — no HTML parsing needed.

### 2. amazon_product (Async)
Used for product page scraping. Each product is submitted as an async job to avoid
blocking. Results are polled in parallel across the batch.

### 3. Structured Parsing
By setting `parse: true`, Oxylabs handles all the anti-bot logic AND returns clean
structured data. Without this, we'd need to parse raw HTML ourselves.

### 4. Geo-targeting
`geo_location: "United States"` ensures we see US-specific pricing, Prime eligibility,
and delivery estimates — critical for TechNovaAI's US market analysis.

### 5. Pagination
Amazon shows ~48 results per page. We request 3 pages (`start_page: 1, 2, 3`) to
collect 100+ results, then trim to exactly 100.

### 6. Async/Polling
For 100 product pages, synchronous requests would be too slow. Async mode lets us
submit all jobs quickly, then poll for completion. Jobs run in parallel on Oxylabs' side.

### 7. Async/Callback (Alternative)
For production, a callback URL eliminates polling overhead entirely. Oxylabs POSTs
results to your endpoint when each job completes. See `scraper/callback.py`.

### 8. Batch Processing
We chunk 100 products into groups of 10. This balances throughput with manageability —
we can track progress, handle failures per-batch, and avoid overwhelming the API.
```

- [ ] **Step 2: Commit**

```bash
git add docs/FEATURES.md
git commit -m "docs: add FEATURES.md mapping all Oxylabs features to code"
```

---

### Task 9: Documentation — PRICING.md

**Files:**
- Create: `docs/PRICING.md`

- [ ] **Step 1: Write PRICING.md**

```markdown
# Pricing Calculation for TechNovaAI

## Usage Estimate

### Per Scraping Run
| Request Type | Count | Source |
|---|---|---|
| Search pages (amazon_search) | 3 | 3 pages × 1 request each |
| Product pages (amazon_product) | 100 | 1 request per product |
| **Total per run** | **103** | |

### Monthly Volume
| Metric | Value |
|---|---|
| Runs per day | 24 (hourly) |
| Runs per month | 720 |
| Requests per month | **74,160** |

## Pricing Tiers (Web Scraper API)

*Note: Verify current pricing at oxylabs.io — rates below are based on publicly available information.*

### Pay As You Go
- Amazon search: ~$3.00 per 1,000 requests
- Amazon product: ~$3.00 per 1,000 requests

**Estimated monthly cost:**
- Search: 3 × 720 = 2,160 requests → ~$6.48
- Product: 100 × 720 = 72,000 requests → ~$216.00
- **Total: ~$222.48/month**

### Subscription Plans
Higher volume plans typically offer discounts:
- Starter plans may reduce per-request cost by 20-30%
- Enterprise plans offer custom pricing for sustained high volume

## Recommendation

**Recommended plan: Subscription (Starter or Growth tier)**

Rationale:
- 74K requests/month is consistent and predictable
- Subscription plans offer better per-request rates
- TechNovaAI's use case is long-running (competitive monitoring), not one-off

**Cost optimization tips:**
1. If only hourly data is needed during business hours (8am-6pm), reduce to 10 runs/day → ~30,900 requests/month
2. Consider if all 100 products need hourly refresh, or if top 20 could be hourly with rest daily
3. Ask Oxylabs sales for volume discount at 74K/month sustained

## ROI Context

For a company entering the smartphone resale market, $200-250/month for real-time competitive
intelligence on 100 listings is minimal compared to:
- Potential pricing mistakes from stale data
- Engineering cost of building/maintaining a custom scraper
- Anti-bot evasion engineering (Oxylabs handles this entirely)
```

- [ ] **Step 2: Commit**

```bash
git add docs/PRICING.md
git commit -m "docs: add PRICING.md with cost breakdown and plan recommendation"
```

---

### Task 10: Documentation — FEEDBACK.md + PRESENTATION_NOTES.md

**Files:**
- Create: `docs/FEEDBACK.md`
- Create: `docs/PRESENTATION_NOTES.md`

- [ ] **Step 1: Write FEEDBACK.md template**

```markdown
# Product & Developer Feedback

Feedback collected during PoC implementation for the Oxylabs product team.

## API Usability / Developer Experience

*To be filled during implementation*

## Documentation

*To be filled during implementation*

## Parsing Accuracy (`parse: true`)

*To be filled during implementation — did structured parsing miss any fields?*

## Feature Requests

*To be filled during implementation*

## Error Messages / Debugging

*To be filled during implementation*

## Overall Impressions

*To be filled during implementation*
```

- [ ] **Step 2: Write PRESENTATION_NOTES.md**

```markdown
# Presentation Notes — TechNovaAI Demo

## Agenda
1. Problem recap: top 100 iPhone listings, hourly, structured data
2. Live demo: run the scraper, show output
3. Code walkthrough: highlight each Oxylabs feature (see FEATURES.md)
4. Pricing: walk through PRICING.md
5. Next steps & alternative products
6. Q&A

## Key Talking Points

### Why Oxylabs Web Scraper API?
- No anti-bot engineering needed — Oxylabs handles CAPTCHAs, IP rotation, fingerprinting
- Structured parsing (`parse: true`) eliminates HTML parsing maintenance
- Async mode enables scraping at scale without blocking
- Geo-targeting ensures US-specific data

### Demo Flow
1. Show `.env.example` — simple credential setup
2. Run `python main.py` — watch logs show search → product phases
3. Open output JSON — show structured data for all 100 products
4. Show scheduler running (or explain APScheduler config)

## Alternative Oxylabs Products

### E-Commerce Scraper API
- Purpose-built for e-commerce sites (Amazon, eBay, etc.)
- May offer higher-level abstractions for product data
- Worth evaluating if TechNovaAI expands to multiple marketplaces

### SERP Scraper API
- Optimized for search engine results pages
- Relevant if TechNovaAI also wants Google Shopping data
- Lower cost if only search-level data is needed

### Residential Proxies + Custom Scraper
- Full control over parsing logic
- Higher complexity and maintenance burden
- Only recommended if Oxylabs' parsed output doesn't meet specific needs

### Web Unblocker
- Proxy-like service that handles anti-bot for any URL
- Client builds their own parser
- More flexibility but more engineering effort

## Next Steps (Future Enhancements)

### Database Storage
- PostgreSQL or TimescaleDB for time-series price data
- Enables querying trends, deduplication, powering dashboards

### Production Deployment
- Docker container + docker-compose (cloud-agnostic)
- Works on AWS, GCP, Azure, or self-hosted
- Oxylabs built-in Scheduler as alternative to APScheduler

### Dashboard
- Market overview: all 100 listings at a glance
- Price monitoring: alerts on significant price drops
- Tools: Grafana, Metabase, or custom lightweight UI

### Historical Trend Analysis
Full competitive intelligence:
- Price fluctuation patterns (best times to buy/list)
- Ranking shifts (who's rising/falling)
- Delivery & Prime changes
- Sponsored spend patterns
```

- [ ] **Step 3: Commit**

```bash
git add docs/FEEDBACK.md docs/PRESENTATION_NOTES.md
git commit -m "docs: add FEEDBACK template and PRESENTATION_NOTES"
```

---

### Task 11: Final Integration Test + .env.example

**Files:**
- Modify: `main.py` (add `--once` flag for single-run mode)

- [ ] **Step 1: Add CLI argument for single-run mode**

Add to the bottom of `main.py`, replacing the existing `main()`:

```python
def main():
    """Entry point: run once or start hourly scheduler."""
    import argparse

    parser = argparse.ArgumentParser(description="Oxylabs Amazon iPhone Scraper PoC")
    parser.add_argument("--once", action="store_true", help="Run once and exit (no scheduler)")
    args = parser.parse_args()

    logger.info("Oxylabs PoC — Amazon iPhone Scraper")

    if args.once:
        logger.info("Single run mode (--once)")
        scheduled_job()
    else:
        logger.info("Running initial scrape...")
        scheduled_job()
        logger.info("Starting hourly scheduler...")
        scheduler = BlockingScheduler()
        scheduler.add_job(scheduled_job, "interval", hours=1)
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add --once flag for single-run mode"
```

---

### Task 12: Final Verification

- [ ] **Step 1: Verify project structure**

Run: `find . -type f | grep -v __pycache__ | grep -v .git | sort`

Expected output should match the spec's project structure.

- [ ] **Step 2: Run full test suite one final time**

Run: `pytest tests/ -v --tb=short`
Expected: All tests PASS (13+ tests)

- [ ] **Step 3: Test with real credentials (manual)**

```bash
cp .env.example .env
# Edit .env with real Oxylabs credentials
python main.py --once
# Verify output/ contains a JSON file with scraped data
```

- [ ] **Step 4: Final commit with all files**

```bash
git status
# If any files were missed, add them
git add -A
git commit -m "chore: final cleanup and verification"
```

---

## Summary

| Task | What It Builds | Tests |
|------|---------------|-------|
| 1 | Project setup, config, dependencies | — |
| 2 | Pydantic data models | 5 tests |
| 3 | Oxylabs API client (retry, async) | 4 tests |
| 4 | Search phase (pagination, geo) | 3 tests |
| 5 | Product phase (batch, polling) | 4 tests |
| 6 | Main orchestration + scheduler | 2 tests |
| 7 | Callback mode (documented alternative) | — |
| 8 | FEATURES.md | — |
| 9 | PRICING.md | — |
| 10 | FEEDBACK.md + PRESENTATION_NOTES.md | — |
| 11 | CLI --once flag | — |
| 12 | Final verification | Full suite |
