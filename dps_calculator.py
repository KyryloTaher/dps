import argparse
from dataclasses import dataclass


@dataclass
class WarriorStats:
    player_level: int
    weapon_skill: int
    base_damage_mh: float
    base_speed_mh: float
    attack_power: float
    hit: float = 0.0
    spellbook_crit: float = 0.0
    aura_crit: float = 0.0
    base_damage_oh: float = 0.0
    base_speed_oh: float = 0.0
    dual_wield_spec: int = 0  # talent ranks
    impale: int = 0  # talent ranks
    target_level: int = 63
    target_armor: int = 0
    target_block_value: float = 45.0


def attack_table(stats: WarriorStats):
    target_defense = stats.target_level * 5
    skill_diff = target_defense - stats.weapon_skill
    capped_skill = min(stats.weapon_skill, stats.player_level * 5)
    extra_skill = max(0, stats.weapon_skill - stats.player_level * 5)
    base_crit = stats.spellbook_crit - extra_skill * 0.04

    if skill_diff > 10:
        base_miss = 5 + skill_diff * 0.2
    else:
        base_miss = 5 + skill_diff * 0.1

    dodge = 5 + skill_diff * 0.1
    block = min(5.0, 5 + skill_diff * 0.1)
    if stats.target_level - stats.player_level > 2:
        parry = 14.0
    else:
        parry = 5 + skill_diff * 0.1

    glancing = 10 + (target_defense - capped_skill) * 2

    if capped_skill - target_defense < 0:
        crit = base_crit + (capped_skill - target_defense) * 0.2
    else:
        crit = base_crit + (capped_skill - target_defense) * 0.04

    if stats.target_level - stats.player_level > 2 and stats.aura_crit > 0:
        crit -= min(1.8, stats.aura_crit)

    if skill_diff > 10:
        miss = base_miss - (stats.hit - 1)
    else:
        miss = base_miss - stats.hit

    crit = min(100 - miss - parry - dodge - block - glancing, crit)
    hit = max(100 - miss - parry - dodge - block - glancing - crit, 0)

    return {
        "miss": miss,
        "parry": parry,
        "dodge": dodge,
        "block": block,
        "glancing": glancing,
        "crit": crit,
        "hit": hit,
    }


def armor_mitigation(target_armor: int, attacker_level: int) -> float:
    return target_armor / (target_armor + 400 + 85 * attacker_level)


def white_damage(base_damage: float, speed: float, stats: WarriorStats) -> float:
    dmg = base_damage + stats.attack_power / 14 * speed
    return dmg


def expected_damage(base_damage: float, speed: float, table: dict, stats: WarriorStats) -> float:
    damage = white_damage(base_damage, speed, stats)

    glancing_low = min(1.3 - 0.05 * (stats.target_level * 5 - stats.weapon_skill), 0.91)
    glancing_high = max(min(1.2 - 0.03 * (stats.target_level * 5 - stats.weapon_skill), 0.99), 0.2)
    glancing_avg = damage * (glancing_low + glancing_high) / 2

    crit_multiplier = 2 + 0.1 * stats.impale

    avg = (
        table["hit"] * damage
        + table["crit"] * damage * crit_multiplier
        + table["block"] * (damage - stats.target_block_value)
        + table["glancing"] * glancing_avg
    ) / 100
    return avg / speed * (1 - armor_mitigation(stats.target_armor, stats.player_level))


def calculate_dps(stats: WarriorStats) -> float:
    table = attack_table(stats)
    dps_mh = expected_damage(stats.base_damage_mh, stats.base_speed_mh, table, stats)
    dps_total = dps_mh
    if stats.base_damage_oh > 0 and stats.base_speed_oh > 0:
        oh_damage = white_damage(stats.base_damage_oh, stats.base_speed_oh, stats)
        stats_oh = stats  # same stats
        dps_oh = expected_damage(stats.base_damage_oh, stats.base_speed_oh, table, stats_oh)
        dps_total += dps_oh * (0.5 + 0.025 * stats.dual_wield_spec)
    return dps_total


def parse_args() -> WarriorStats:
    p = argparse.ArgumentParser(description="Calculate Warrior DPS for Classic Era")
    p.add_argument("--player-level", type=int, default=60)
    p.add_argument("--target-level", type=int, default=63)
    p.add_argument("--weapon-skill", type=int, default=300)
    p.add_argument("--base-damage-mh", type=float, required=True)
    p.add_argument("--base-speed-mh", type=float, required=True)
    p.add_argument("--attack-power", type=float, required=True)
    p.add_argument("--hit", type=float, default=0.0, help="Hit percent")
    p.add_argument("--crit", type=float, default=0.0, help="Base crit from gear and talents")
    p.add_argument("--aura-crit", type=float, default=0.0)
    p.add_argument("--base-damage-oh", type=float, default=0.0)
    p.add_argument("--base-speed-oh", type=float, default=0.0)
    p.add_argument("--dual-wield-spec", type=int, default=0, help="Dual Wield Specialization talent points")
    p.add_argument("--impale", type=int, default=0, help="Impale talent points")
    p.add_argument("--target-armor", type=int, default=0)
    p.add_argument("--target-block-value", type=float, default=45.0)
    args = p.parse_args()
    return WarriorStats(
        player_level=args.player_level,
        target_level=args.target_level,
        weapon_skill=args.weapon_skill,
        base_damage_mh=args.base_damage_mh,
        base_speed_mh=args.base_speed_mh,
        base_damage_oh=args.base_damage_oh,
        base_speed_oh=args.base_speed_oh,
        attack_power=args.attack_power,
        hit=args.hit,
        spellbook_crit=args.crit,
        aura_crit=args.aura_crit,
        dual_wield_spec=args.dual_wield_spec,
        impale=args.impale,
        target_armor=args.target_armor,
        target_block_value=args.target_block_value,
    )


if __name__ == "__main__":
    stats = parse_args()
    dps = calculate_dps(stats)
    print(f"Estimated DPS: {dps:.2f}")
