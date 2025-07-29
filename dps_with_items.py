import argparse
from typing import Dict
from item_database import get_items
from dps_calculator import calculate_dps, WarriorStats


def merge_stats(base: Dict[str, float], item_stats: Dict[str, float]) -> None:
    for k, v in item_stats.items():
        base[k] = base.get(k, 0) + v


def build_stats(args: argparse.Namespace) -> WarriorStats:
    items = get_items(args.items)
    stats_dict: Dict[str, float] = {
        "player_level": args.player_level,
        "target_level": args.target_level,
        "weapon_skill": args.weapon_skill,
        "attack_power": 0,
        "hit": 0,
        "spellbook_crit": 0,
        "strength": 0,
        "agility": 0,
        "base_damage_mh": 0,
        "base_speed_mh": 0,
        "base_damage_oh": 0,
        "base_speed_oh": 0,
        "dual_wield_spec": args.dual_wield_spec,
        "impale": args.impale,
        "target_armor": args.target_armor,
        "target_block_value": args.target_block_value,
    }

    for item in items:
        merge_stats(stats_dict, item.stats)
    strength = stats_dict.pop("str", 0) + stats_dict.pop("strength", 0)
    agility = stats_dict.pop("agi", 0) + stats_dict.pop("agility", 0)
    stats_dict["strength"] = strength
    stats_dict["agility"] = agility
    stats_dict["attack_power"] += strength * 2
    stats_dict["spellbook_crit"] += agility / 20
    return WarriorStats(**stats_dict)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Calculate DPS using items from the database")
    p.add_argument("--player-level", type=int, default=60)
    p.add_argument("--target-level", type=int, default=63)
    p.add_argument("--weapon-skill", type=int, default=300)
    p.add_argument("--items", nargs="*", default=[], help="Item names to equip")
    p.add_argument("--dual-wield-spec", type=int, default=0)
    p.add_argument("--impale", type=int, default=0)
    p.add_argument("--target-armor", type=int, default=0)
    p.add_argument("--target-block-value", type=float, default=45.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    stats = build_stats(args)
    dps = calculate_dps(stats)
    print(f"Estimated DPS: {dps:.2f}")


if __name__ == "__main__":
    main()
