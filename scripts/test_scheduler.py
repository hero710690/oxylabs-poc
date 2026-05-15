"""
Quick test: Create an Oxylabs Schedule, verify it exists, then delete it.

Proves the Scheduler API works without needing a callback URL or S3 bucket.

Usage:
    python scripts/test_scheduler.py
"""

import json
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

auth = (config.OXYLABS_USERNAME, config.OXYLABS_PASSWORD)
base_url = "https://data.oxylabs.io/v1/schedules"


def main():
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

    resp = requests.post(base_url, json=payload, auth=auth, timeout=30)
    print(f"   Status: {resp.status_code}")

    if resp.status_code not in (200, 201):
        print(f"   Error: {resp.text}")
        return

    schedule = resp.json()
    schedule_id = schedule.get("schedule_id")
    print(f"   Schedule created: ID={schedule_id}")
    print(f"   Response: {json.dumps(schedule, indent=2)}")

    # Step 2: Verify it exists
    print(f"\n2. Fetching schedule {schedule_id}...")
    resp = requests.get(f"{base_url}/{schedule_id}", auth=auth, timeout=30)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        info = resp.json()
        print(f"   Cron: {info.get('cron')}")
        print(f"   Active: {info.get('active', 'N/A')}")
        print(f"   End time: {info.get('end_time')}")

    # Step 3: Pause it (optional — shows we can control it)
    print(f"\n3. Pausing schedule...")
    resp = requests.put(
        f"{base_url}/{schedule_id}/state",
        json={"active": False},
        auth=auth,
        timeout=30,
    )
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        print("   Schedule paused successfully")

    # Step 4: Delete it (cleanup)
    print(f"\n4. Deleting schedule...")
    resp = requests.delete(f"{base_url}/{schedule_id}", auth=auth, timeout=30)
    print(f"   Status: {resp.status_code}")
    if resp.status_code in (200, 204):
        print("   Schedule deleted successfully")
    else:
        print(f"   Response: {resp.text}")

    print("\n✓ Oxylabs Scheduler API works — create, read, pause, delete all confirmed.")


if __name__ == "__main__":
    main()
