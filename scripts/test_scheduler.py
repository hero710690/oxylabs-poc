"""
Quick test: Create an Oxylabs Schedule, verify it exists, then delete it.

Proves the Scheduler API works without needing a callback URL or S3 bucket.

Usage:
    python scripts/test_scheduler.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.client import OxylabsClient
import config


def main():
    client = OxylabsClient()

    # Step 1: Create a schedule
    print("1. Creating schedule...")
    payload = {
        "cron": "0 * * * *",
        "end_time": "2026-05-16 00:00:00",
        "items": [
            {
                "source": "amazon_search",
                "query": config.SEARCH_QUERY,
                "domain": config.SEARCH_DOMAIN,
                "parse": True,
                "geo_location": config.GEO_LOCATION,
            }
        ],
    }

    schedule = client.create_schedule(payload)
    schedule_id = schedule.get("schedule_id")
    print(f"   Schedule created: ID={schedule_id}")
    print(f"   Response: {json.dumps(schedule, indent=2)}")

    # Step 2: Verify it exists
    print(f"\n2. Fetching schedule {schedule_id}...")
    info = client.get_schedule(schedule_id)
    print(f"   Cron: {info.get('cron')}")
    print(f"   Active: {info.get('active', 'N/A')}")
    print(f"   End time: {info.get('end_time')}")

    # Step 3: Pause it
    print(f"\n3. Pausing schedule...")
    client.pause_schedule(schedule_id)
    print("   Schedule paused successfully")

    # Step 4: Delete it (cleanup)
    print(f"\n4. Deleting schedule...")
    client.delete_schedule(schedule_id)
    print("   Schedule deleted successfully")

    print("\nOxylabs Scheduler API works — create, read, pause, delete all confirmed.")


if __name__ == "__main__":
    main()
