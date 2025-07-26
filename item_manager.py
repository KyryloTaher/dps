import argparse
import json
from item_database import init_db, add_item, Item


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the items database")
    parser.add_argument("--init-db", action="store_true", help="Initialize database")
    parser.add_argument(
        "--add",
        nargs=4,
        metavar=("NAME", "TYPE", "STATS_JSON", "LEVEL"),
        help="Add an item as JSON stats"
    )

    args = parser.parse_args()

    if args.init_db:
        init_db()
        print("Database initialized")

    if args.add:
        name, type_, stats_json, level = args.add
        stats = json.loads(stats_json)
        add_item(Item(name=name, type=type_, required_level=int(level), stats=stats))
        print(f"Inserted {name}")


if __name__ == "__main__":
    main()
