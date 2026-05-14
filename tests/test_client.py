import pytest
import responses
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
