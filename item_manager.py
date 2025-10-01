import argparse
from typing import List
from item_database import init_db, add_item, Item

# Common stat keys that can be stored for an item. These correspond to fields
# used in `WarriorStats` and can be referenced later when calculating DPS.
STAT_KEYS: List[str] = [
    "attack_power",
    "hit",
    "spellbook_crit",
    "str",
    "agi",
    "base_damage_mh",
    "base_speed_mh",
    "base_damage_oh",
    "base_speed_oh",
]

# Predefined item types for each equipment slot. These strings are used when
# inserting items through the GUI so users can pick a slot from a drop-down
# rather than typing it manually.
ITEM_TYPES: List[str] = [
    "Helm",
    "Neck",
    "Chest",
    "Bracers",
    "Hands",
    "Belt",
    "Legs",
    "Boots",
    "Ring",
    "Trinket",
    "Main Hand",
    "Off Hand",
    "Ranged",
    "Ammo",
]


def parse_stat_pairs(pairs):
    stats = {}
    for pair in pairs:
        if "=" not in pair:
            raise argparse.ArgumentTypeError(f"Invalid stat format: {pair}")
        key, value = pair.split("=", 1)
        if key not in STAT_KEYS:
            raise argparse.ArgumentTypeError(
                f"Unknown stat '{key}'. Use --list-stats to see valid options"
            )
        try:
            stats[key] = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Value for {key} must be numeric")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the items database")
    parser.add_argument("--init-db", action="store_true", help="Initialize database")
    parser.add_argument(
        "--list-stats",
        action="store_true",
        help="Print available stat keys and exit",
    )
    parser.add_argument(
        "--add",
        nargs=3,
        metavar=("NAME", "TYPE", "LEVEL"),
        help="Add an item with stats"
    )
    parser.add_argument(
        "--stat",
        dest="stats",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Stat pair, may be used multiple times",
    )

    args = parser.parse_args()

    if args.init_db:
        init_db()
        print("Database initialized")

    if args.list_stats:
        for key in STAT_KEYS:
            print(key)
        return

    if args.add:
        name, type_, level = args.add
        stats = parse_stat_pairs(args.stats)
        add_item(Item(name=name, type=type_, required_level=int(level), stats=stats))
        print(f"Inserted {name}")


if __name__ == "__main__":
    main()
