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
SEARCH_PAGES = 7  # ~16-20 results/page → 100+ listings
RESULTS_LIMIT = 100

# FEATURE: geo_location — lock results to US market (Oxylabs uses ZIP codes)
GEO_LOCATION = "90210"

# Batch config
BATCH_SIZE = 10  # product pages per batch
POLL_INTERVAL = 5  # seconds between status checks
POLL_TIMEOUT = 300  # max seconds to wait for a batch

# Retry config
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # exponential backoff base in seconds

# Output
OUTPUT_DIR = "output"
