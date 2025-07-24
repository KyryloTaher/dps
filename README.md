# DPS

This repository contains a script to fetch all item IDs from the World of Warcraft Classic API and store them in a SQLite database.

## Requirements

- Python 3
- `requests` library (install with `pip install requests`)

## Usage

Set the Blizzard API credentials as environment variables or edit them in `fetch_items.py`:

```
export BLIZZARD_CLIENT_ID="111c95f387d14e02b43c751d9187000d"
export BLIZZARD_CLIENT_SECRET="0WbrQzxKQA5r3WgpiZwCqz85vD8lGDeH"
```

Run the script (by default it fetches Cataclysm Classic data):

```
python3 fetch_items.py
```

To fetch Classic Era data pass the Classic Era namespace:

```
python3 fetch_items.py --namespace static-classic1x-us
```

The script will create `items.db` (or the path you provide via `--db-path`) containing an `items` table with all fetched item IDs.
