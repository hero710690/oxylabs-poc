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
SEARCH_PAGES = 5  # ~24 results/page → 120+ listings (need 100)
# Amazon filtered URL: Cell Phones category + Apple brand only
SEARCH_URL = "https://www.amazon.com/s?k=iphone&i=mobile&rh=n%3A7072561011%2Cp_123%3A110955&dc&rnid=85457740011"
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
