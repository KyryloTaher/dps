import sqlite3
import json
from dataclasses import dataclass
from typing import Dict, List

DB_PATH = "items.db"


def init_db(db_path: str = DB_PATH) -> None:
    """Create the items table if it does not exist."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            name TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            required_level INTEGER NOT NULL,
            stats TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@dataclass
class Item:
    name: str
    type: str
    required_level: int
    stats: Dict[str, float]


def add_item(item: Item, db_path: str = DB_PATH) -> None:
    """Insert an item into the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO items (name, type, required_level, stats) VALUES (?, ?, ?, ?)",
        (item.name, item.type, item.required_level, json.dumps(item.stats)),
    )
    conn.commit()
    conn.close()


def get_items(names: List[str], db_path: str = DB_PATH) -> List[Item]:
    """Retrieve items by name."""
    if not names:
        return []
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    placeholders = ",".join("?" for _ in names)
    c.execute(
        f"SELECT name, type, required_level, stats FROM items WHERE name IN ({placeholders})",
        names,
    )
    rows = c.fetchall()
    conn.close()
    items = []
    for name, type_, level, stats_json in rows:
        items.append(Item(name=name, type=type_, required_level=level, stats=json.loads(stats_json)))
    return items
