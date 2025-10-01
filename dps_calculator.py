import argparse
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class WarriorStats:
    player_level: int
    weapon_skill: int
    base_damage_mh: float
    base_speed_mh: float
    attack_power: float
    strength: float = 0.0
    agility: float = 0.0
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
    block_value: float = 0.0
    rage: float = 0.0
    imp_cleave: int = 0
    imp_execute_rage: float = 0.0


def attack_table(stats: WarriorStats, *, dual_wield: bool = False):
    target_defense = stats.target_level * 5
    skill_diff = target_defense - stats.weapon_skill
    capped_skill = min(stats.weapon_skill, stats.player_level * 5)
    extra_skill = max(0, stats.weapon_skill - stats.player_level * 5)
    base_crit = stats.spellbook_crit - extra_skill * 0.04

    if skill_diff > 10:
        base_miss = 5 + skill_diff * 0.2
    else:
        base_miss = 5 + skill_diff * 0.1

    base_miss = min(max(base_miss, 0.0), 100.0)
    dual_wield_base_miss = min(max(base_miss + 19, 0.0), 100.0)
    applied_base_miss = dual_wield_base_miss if dual_wield else base_miss

    dodge = min(max(5 + skill_diff * 0.1, 0.0), 100.0)
    block = min(5.0, max(5 + skill_diff * 0.1, 0.0))
    if stats.target_level - stats.player_level > 2:
        parry = 14.0
    else:
        parry = max(5 + skill_diff * 0.1, 0.0)
    parry = min(parry, 100.0)

    glancing = min(max(0.0, 10 + (target_defense - capped_skill) * 2), 100.0)

    if capped_skill - target_defense < 0:
        crit = base_crit + (capped_skill - target_defense) * 0.2
    else:
        crit = base_crit + (capped_skill - target_defense) * 0.04

    if stats.target_level - stats.player_level > 2 and stats.aura_crit > 0:
        crit -= min(1.8, stats.aura_crit)

    crit = max(crit, 0.0)

    if skill_diff > 10:
        hit_reduction = max(stats.hit - 1, 0.0)
    else:
        hit_reduction = max(stats.hit, 0.0)

    miss = max(applied_base_miss - hit_reduction, 0.0)

    available_for_crit = max(100 - miss - parry - dodge - block - glancing, 0.0)
    crit = min(crit, available_for_crit)
    hit = max(100 - miss - parry - dodge - block - glancing - crit, 0.0)

    return {
        "miss": miss,
        "parry": parry,
        "dodge": dodge,
        "block": block,
        "glancing": glancing,
        "crit": crit,
        "hit": hit,
        "base_miss_chance": base_miss,
        "dual_wield_base_miss_chance": dual_wield_base_miss,
    }


def armor_mitigation(target_armor: int, attacker_level: int) -> float:
    return target_armor / (target_armor + 400 + 85 * attacker_level)


def white_damage(base_damage: float, speed: float, stats: WarriorStats) -> float:
    dmg = base_damage + stats.attack_power / 14 * speed
    return dmg


def expected_damage(base_damage: float, speed: float, table: dict, stats: WarriorStats) -> float:
    damage = white_damage(base_damage, speed, stats)
    skill_gap = stats.target_level * 5 - stats.weapon_skill

    glancing_low_multiplier = min(1.3 - 0.05 * skill_gap, 0.91)
    glancing_high_multiplier = max(min(1.2 - 0.03 * skill_gap, 0.99), 0.2)
    glancing_low = damage * glancing_low_multiplier
    glancing_high = damage * glancing_high_multiplier
    glancing_avg = (glancing_low + glancing_high) / 2

    crit_multiplier = 2 + 0.1 * stats.impale
    blocked_damage = max(damage - stats.target_block_value, 0.0)

    avg = (
        table["hit"] * damage
        + table["crit"] * damage * crit_multiplier
        + table["block"] * blocked_damage
        + table["glancing"] * glancing_avg
    ) / 100
    mitigation = armor_mitigation(stats.target_armor, stats.player_level)
    return avg / speed * (1 - mitigation)


def calculate_dps(stats: WarriorStats) -> float:
    is_dual_wield = stats.base_damage_oh > 0 and stats.base_speed_oh > 0
    table = attack_table(stats, dual_wield=is_dual_wield)
    dps_mh = expected_damage(stats.base_damage_mh, stats.base_speed_mh, table, stats)
    dps_total = dps_mh
    if is_dual_wield:
        dps_oh = expected_damage(stats.base_damage_oh, stats.base_speed_oh, table, stats)
        dual_wield_modifier = 0.5 + 0.025 * stats.dual_wield_spec
        dps_total += dps_oh * dual_wield_modifier
    return dps_total


def yellow_attack_damage(
    stats: WarriorStats,
    *,
    normalized_speed: float,
    rage: Optional[float] = None,
    imp_cleave: Optional[int] = None,
    imp_execute_rage: Optional[float] = None,
) -> Dict[str, float]:
    """Return the raw damage for common yellow abilities.

    The formulas implement the Classic Era values documented in the
    specification for the project.
    """

    rage = stats.rage if rage is None else rage
    imp_cleave = stats.imp_cleave if imp_cleave is None else imp_cleave
    imp_execute_rage = (
        stats.imp_execute_rage if imp_execute_rage is None else imp_execute_rage
    )

    normalized_component = stats.attack_power / 14 * normalized_speed
    damage_mh = white_damage(stats.base_damage_mh, stats.base_speed_mh, stats)
    cleave_bonus = 50 * (1 + 0.4 * imp_cleave)

    abilities = {
        "bloodthirst": stats.attack_power * 0.45,
        "mortal_strike": stats.base_damage_mh + 160 + normalized_component,
        "shield_slam": 350 + stats.block_value,
        "whirlwind": stats.base_damage_mh + normalized_component,
        "overpower": stats.base_damage_mh + 35 + normalized_component,
        "execute": 600 + max(rage - 15 + imp_execute_rage, 0) * 15,
        "heroic_strike_rank_8": damage_mh + 138,
        "heroic_strike_rank_9": damage_mh + 157,
        "cleave": damage_mh + cleave_bonus,
        "slam": damage_mh + 87,
    }
    return abilities


def rage_conversion_factor(player_level: int) -> float:
    return (
        0.0091107836 * player_level**2
        + 3.225598133 * player_level
        + 4.2652911
    )


def rage_from_damage(player_level: int, damage_done: float) -> float:
    return damage_done / rage_conversion_factor(player_level) * 7.5


def rage_from_damage_taken(player_level: int, damage_taken: float) -> float:
    return damage_taken / rage_conversion_factor(player_level) * 2.5


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
