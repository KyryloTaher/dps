import os
import requests
import sqlite3

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


def fetch_all_item_ids(region='us', namespace='static-classic-us', locale='en_US', page_size=1000):
    token = get_access_token()
    item_ids = []
    page = 1
    headers = {'Authorization': f'Bearer {token}'}
    while True:
        params = {
            'namespace': namespace,
            'locale': locale,
            'page': page,
            'pageSize': page_size,
            'orderby': 'id',
        }
        url = f'https://{region}.api.blizzard.com/data/wow/search/item'
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
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
    ids = fetch_all_item_ids()
    store_in_db(ids)
    print(f'Stored {len(ids)} items in the database.')


if __name__ == '__main__':
    main()
