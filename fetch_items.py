import os
import re
import requests
import sqlite3
import argparse

CLIENT_ID = os.getenv('BLIZZARD_CLIENT_ID', '111c95f387d14e02b43c751d9187000d')
CLIENT_SECRET = os.getenv('BLIZZARD_CLIENT_SECRET', '0WbrQzxKQA5r3WgpiZwCqz85vD8lGDeH')


def get_access_token():
    resp = requests.post(
        'https://oauth.battle.net/token',
        data={'grant_type': 'client_credentials'},
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['access_token']


def _auto_namespace(base_namespace: str, region: str, locale: str, token: str) -> str:
    """Detect the full static namespace with patch version."""
    url = f"https://{region}.api.blizzard.com/data/wow/item-class/index"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        url,
        params={"namespace": base_namespace, "locale": locale},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    href = resp.json().get("_links", {}).get("self", {}).get("href", "")
    match = re.search(r"namespace=([^&]+)", href)
    return match.group(1) if match else base_namespace


def fetch_all_item_ids(region="us", namespace="static-classic-us", locale="en_US", page_size=1000):
    token = get_access_token()
    if namespace in ("static-classic-us", "static-classic1x-us"):
        namespace = _auto_namespace(namespace, region, locale, token)
    item_ids = []
    page = 1
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        params = {
            'namespace': namespace,
            'locale': locale,
            '_page': page,
            '_pageSize': page_size,
            'orderby': 'id',
        }
        url = f'https://{region}.api.blizzard.com/data/wow/search/item'
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data.get('results'):
            print('Warning: no results returned for page', page)
            break
        for result in data.get('results', []):
            item_id = result['data']['id']
            item_ids.append(item_id)
        if page >= data.get('pageCount', 0):
            break
        page += 1
    return item_ids


def store_in_db(item_ids, db_path='items.db'):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY)')
    cur.executemany('INSERT OR IGNORE INTO items(id) VALUES (?)', [(i,) for i in item_ids])
    conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Fetch WoW item IDs")
    parser.add_argument("--region", default="us", help="API region")
    parser.add_argument(
        "--namespace",
        default="static-classic-us",
        help="Static namespace, e.g. static-classic-us or static-classic1x-us",
    )
    parser.add_argument("--locale", default="en_US", help="Locale")
    parser.add_argument(
        "--db-path", default="items.db", help="Path to output SQLite database"
    )
    args = parser.parse_args()

    ids = fetch_all_item_ids(
        region=args.region, namespace=args.namespace, locale=args.locale
    )
    store_in_db(ids, db_path=args.db_path)
    print(f"Stored {len(ids)} items in the database.")


if __name__ == '__main__':
    main()
