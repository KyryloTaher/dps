"""Unified Tkinter interface for the Warrior DPS toolkit.

This module now contains the full implementation for calculating damage,
loading equipment from the SQLite database and managing items. The legacy
standalone scripts were removed so the project can be maintained from a single
entry point.
"""

from __future__ import annotations

import json
import sqlite3
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import Dict, Iterable, List, Optional


# ---------------------------------------------------------------------------
# Data models and calculations

DB_PATH = "items.db"


@dataclass
class Item:
    """Representation of an item stored in the SQLite database."""

    name: str
    type: str
    required_level: int
    stats: Dict[str, float]


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
    dual_wield_spec: int = 0
    impale: int = 0
    target_level: int = 63
    target_armor: int = 0
    target_block_value: float = 45.0
    block_value: float = 0.0
    rage: float = 0.0
    imp_cleave: int = 0
    imp_execute_rage: float = 0.0


def init_db(db_path: str = DB_PATH) -> None:
    """Create the items table if it does not exist."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
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


def add_item(item: Item, db_path: str = DB_PATH) -> None:
    """Insert or update an item in the database."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO items (name, type, required_level, stats) VALUES (?, ?, ?, ?)",
        (item.name, item.type, item.required_level, json.dumps(item.stats)),
    )
    conn.commit()
    conn.close()


def list_item_names(item_type: str | None = None, db_path: str = DB_PATH) -> List[str]:
    """Return all item names, optionally filtered by type."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if item_type is None:
        cursor.execute("SELECT name FROM items ORDER BY name")
    else:
        cursor.execute("SELECT name FROM items WHERE type = ? ORDER BY name", (item_type,))
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return names


def get_items(names: Iterable[str], db_path: str = DB_PATH) -> List[Item]:
    """Load a sequence of items from the database."""

    names = [name for name in names if name]
    if not names:
        return []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in names)
    cursor.execute(
        f"SELECT name, type, required_level, stats FROM items WHERE name IN ({placeholders})",
        names,
    )
    rows = cursor.fetchall()
    conn.close()
    items = []
    for name, type_, level, stats_json in rows:
        items.append(Item(name=name, type=type_, required_level=level, stats=json.loads(stats_json)))
    return items


def attack_table(stats: WarriorStats, *, dual_wield: bool = False) -> Dict[str, float]:
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
    return base_damage + stats.attack_power / 14 * speed


def expected_damage(base_damage: float, speed: float, table: Dict[str, float], stats: WarriorStats) -> float:
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
    rage = stats.rage if rage is None else rage
    imp_cleave = stats.imp_cleave if imp_cleave is None else imp_cleave
    imp_execute_rage = stats.imp_execute_rage if imp_execute_rage is None else imp_execute_rage

    normalized_component = stats.attack_power / 14 * normalized_speed
    damage_mh = white_damage(stats.base_damage_mh, stats.base_speed_mh, stats)
    cleave_bonus = 50 * (1 + 0.4 * imp_cleave)

    return {
        "Bloodthirst": stats.attack_power * 0.45,
        "Mortal Strike": stats.base_damage_mh + 160 + normalized_component,
        "Shield Slam": 350 + stats.block_value,
        "Whirlwind": stats.base_damage_mh + normalized_component,
        "Overpower": stats.base_damage_mh + 35 + normalized_component,
        "Execute": 600 + max(rage - 15 + imp_execute_rage, 0) * 15,
        "Heroic Strike (Rank 8)": damage_mh + 138,
        "Heroic Strike (Rank 9)": damage_mh + 157,
        "Cleave": damage_mh + cleave_bonus,
        "Slam": damage_mh + 87,
    }


# ---------------------------------------------------------------------------
# Helper utilities for building stats from the database

IGNORED_ITEM_STATS = {"dual_wield_spec", "impale"}

STAT_KEYS: List[str] = [
    "attack_power",
    "hit",
    "spellbook_crit",
    "aura_crit",
    "str",
    "agi",
    "base_damage_mh",
    "base_speed_mh",
    "base_damage_oh",
    "base_speed_oh",
    "block_value",
    "rage",
    "imp_cleave",
    "imp_execute_rage",
]

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


def merge_stats(base: Dict[str, float], item_stats: Dict[str, float]) -> None:
    for key, value in item_stats.items():
        if key in IGNORED_ITEM_STATS:
            continue
        base[key] = base.get(key, 0) + value


def build_stats(params: Dict[str, float]) -> WarriorStats:
    items = get_items(params.get("items", []))

    stats_dict: Dict[str, float] = {
        "player_level": params.get("player_level", 60),
        "target_level": params.get("target_level", 63),
        "weapon_skill": params.get("weapon_skill", 300),
        "attack_power": params.get("attack_power", 0.0),
        "hit": params.get("hit", 0.0),
        "spellbook_crit": params.get("spellbook_crit", 0.0),
        "aura_crit": params.get("aura_crit", 0.0),
        "strength": params.get("strength", 0.0),
        "agility": params.get("agility", 0.0),
        "base_damage_mh": params.get("base_damage_mh", 0.0),
        "base_speed_mh": params.get("base_speed_mh", 0.0),
        "base_damage_oh": params.get("base_damage_oh", 0.0),
        "base_speed_oh": params.get("base_speed_oh", 0.0),
        "dual_wield_spec": int(params.get("dual_wield_spec", 0)),
        "impale": int(params.get("impale", 0)),
        "target_armor": params.get("target_armor", 0),
        "target_block_value": params.get("target_block_value", 45.0),
        "block_value": params.get("block_value", 0.0),
        "rage": params.get("rage", 0.0),
        "imp_cleave": int(params.get("imp_cleave", 0)),
        "imp_execute_rage": params.get("imp_execute_rage", 0.0),
    }

    for item in items:
        merge_stats(stats_dict, item.stats)

    strength = stats_dict.pop("str", 0) + stats_dict.pop("strength", 0)
    agility = stats_dict.pop("agi", 0) + stats_dict.pop("agility", 0)
    stats_dict["strength"] = strength
    stats_dict["agility"] = agility
    stats_dict["attack_power"] += strength * 2
    stats_dict["spellbook_crit"] += agility / 20

    # Ensure block value and rage stay in sync with potential item additions.
    stats_dict["block_value"] = float(stats_dict.get("block_value", 0.0))
    stats_dict["rage"] = float(stats_dict.get("rage", 0.0))
    stats_dict["imp_cleave"] = int(stats_dict.get("imp_cleave", 0))
    stats_dict["imp_execute_rage"] = float(stats_dict.get("imp_execute_rage", 0.0))

    return WarriorStats(**stats_dict)


class UnifiedApp:
    """Main application window for the Warrior DPS toolkit."""

    CORE_FIELDS = (
        ("Player Level", "player_level", 60),
        ("Target Level", "target_level", 63),
        ("Weapon Skill", "weapon_skill", 300),
        ("Dual Wield Spec", "dual_wield_spec", 0),
        ("Impale", "impale", 0),
        ("Target Armor", "target_armor", 0),
        ("Target Block Value", "target_block_value", 45.0),
        ("Aura Crit %", "aura_crit", 0.0),
    )

    ABILITY_FIELDS = (
        ("Normalized Speed", "normalized_speed", 3.3),
        ("Rage", "rage", 30.0),
        ("Block Value", "block_value", 0.0),
        ("Improved Cleave Ranks", "imp_cleave", 0),
        ("Execute Bonus Rage", "imp_execute_rage", 0.0),
    )

    ITEM_SLOTS = (
        "Helm",
        "Neck",
        "Chest",
        "Bracers",
        "Hands",
        "Belt",
        "Legs",
        "Boots",
        "Ring 1",
        "Ring 2",
        "Trinket 1",
        "Trinket 2",
        "Main Hand",
        "Off Hand",
        "Ranged",
        "Ammo",
    )

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Warrior DPS Toolkit")

        init_db()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.item_vars: dict[str, tk.StringVar] = {}
        self.extra_vars: dict[str, tk.StringVar] = {}
        self.slot_vars: dict[str, tk.StringVar] = {}
        self.item_comboboxes: list[ttk.Combobox] = []

        self.result_items = tk.StringVar(value="")
        self.skill_tree: ttk.Treeview | None = None

        self._create_item_tab()
        self._create_manager_tab()

        self.refresh_items()

    # ------------------------------------------------------------------
    # Item-based DPS tab
    def _create_item_tab(self) -> None:
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Equipment DPS")

        for row, (label, key, default) in enumerate(self.CORE_FIELDS):
            ttk.Label(frame, text=label).grid(column=0, row=row, sticky=tk.W, pady=2)
            var = tk.StringVar(value=str(default))
            entry = ttk.Entry(frame, textvariable=var)
            entry.grid(column=1, row=row, sticky=(tk.W, tk.E), pady=2)
            self.item_vars[key] = var

        ability_frame = ttk.LabelFrame(frame, text="Ability Inputs", padding=10)
        ability_frame.grid(
            column=0,
            row=len(self.CORE_FIELDS),
            columnspan=2,
            sticky=(tk.W, tk.E),
            pady=(10, 0),
        )

        for idx, (label, key, default) in enumerate(self.ABILITY_FIELDS):
            ttk.Label(ability_frame, text=label).grid(column=0, row=idx, sticky=tk.W, pady=2)
            var = tk.StringVar(value=str(default))
            entry = ttk.Entry(ability_frame, textvariable=var)
            entry.grid(column=1, row=idx, sticky=(tk.W, tk.E), pady=2)
            self.extra_vars[key] = var

        equip_frame = ttk.LabelFrame(frame, text="Equipment", padding=10)
        equip_frame.grid(column=2, row=0, rowspan=len(self.CORE_FIELDS) + 3, padx=(20, 0), sticky=tk.N)

        layout = {
            "Helm": (0, 1),
            "Neck": (1, 1),
            "Ring 1": (1, 2),
            "Bracers": (2, 0),
            "Chest": (2, 1),
            "Trinket 1": (2, 2),
            "Hands": (3, 0),
            "Belt": (3, 1),
            "Ring 2": (3, 2),
            "Main Hand": (3, 3),
            "Legs": (4, 1),
            "Trinket 2": (4, 2),
            "Boots": (5, 1),
            "Off Hand": (6, 3),
            "Ranged": (7, 3),
            "Ammo": (8, 3),
        }

        for slot in self.ITEM_SLOTS:
            row, col = layout.get(slot, (0, 0))
            ttk.Label(equip_frame, text=slot).grid(row=row * 2, column=col, sticky=tk.W)
            var = tk.StringVar()
            combo = ttk.Combobox(equip_frame, textvariable=var, values=(), width=20)
            combo.grid(row=row * 2 + 1, column=col, sticky=(tk.W, tk.E))
            self.slot_vars[slot] = var
            self.item_comboboxes.append(combo)

        compute_button = ttk.Button(frame, text="Calculate", command=self.calculate_item_dps)
        compute_button.grid(column=0, row=len(self.CORE_FIELDS) + len(self.ABILITY_FIELDS), columnspan=2, pady=(10, 0))

        result_label = ttk.Label(frame, textvariable=self.result_items, font=("Helvetica", 12))
        result_label.grid(column=0, row=len(self.CORE_FIELDS) + len(self.ABILITY_FIELDS) + 1, columnspan=2, pady=(6, 0))

        refresh_button = ttk.Button(frame, text="Refresh Items", command=self.refresh_items)
        refresh_button.grid(column=2, row=len(self.CORE_FIELDS) + len(self.ABILITY_FIELDS), padx=(20, 0), sticky=tk.E)

        skill_frame = ttk.LabelFrame(frame, text="Warrior Skills", padding=10)
        skill_frame.grid(
            column=0,
            row=len(self.CORE_FIELDS) + len(self.ABILITY_FIELDS) + 2,
            columnspan=3,
            sticky=(tk.W, tk.E),
            pady=(15, 0),
        )

        tree = ttk.Treeview(skill_frame, columns=("ability", "damage"), show="headings", height=10)
        tree.heading("ability", text="Ability")
        tree.heading("damage", text="Average Damage")
        tree.column("ability", anchor=tk.W, width=200)
        tree.column("damage", anchor=tk.E, width=140)
        tree.grid(column=0, row=0, sticky=(tk.W, tk.E))

        scrollbar = ttk.Scrollbar(skill_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.grid(column=1, row=0, sticky=(tk.N, tk.S))
        tree.configure(yscrollcommand=scrollbar.set)

        self.skill_tree = tree

        frame.columnconfigure(1, weight=1)
        skill_frame.columnconfigure(0, weight=1)

    def calculate_item_dps(self) -> None:
        try:
            params = {
                key: self._coerce_value(self.item_vars[key].get(), default)
                for _, key, default in self.CORE_FIELDS
            }
            extras = {
                key: self._coerce_value(self.extra_vars[key].get(), default)
                for _, key, default in self.ABILITY_FIELDS
            }
            normalized_speed = extras.pop("normalized_speed")
            params.update(extras)
            params["items"] = [var.get() for var in self.slot_vars.values() if var.get()]
            stats = build_stats(params)
        except ValueError:
            self.result_items.set("Invalid input")
            return
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        dps = calculate_dps(stats)
        self.result_items.set(f"Estimated DPS: {dps:.2f}")

        abilities = yellow_attack_damage(
            stats,
            normalized_speed=normalized_speed,
            rage=params.get("rage"),
            imp_cleave=int(params.get("imp_cleave", stats.imp_cleave)),
            imp_execute_rage=params.get("imp_execute_rage"),
        )
        self._populate_skill_tree(abilities)

    def _populate_skill_tree(self, abilities: Dict[str, float]) -> None:
        if not self.skill_tree:
            return
        tree = self.skill_tree
        for row in tree.get_children():
            tree.delete(row)
        for ability, damage in abilities.items():
            tree.insert("", tk.END, values=(ability, f"{damage:.2f}"))

    def refresh_items(self) -> None:
        try:
            items = list_item_names()
        except Exception as exc:
            items = []
            messagebox.showwarning("Database", f"Could not load items: {exc}")
        for combo in self.item_comboboxes:
            combo["values"] = items

    # ------------------------------------------------------------------
    # Item manager tab
    def _create_manager_tab(self) -> None:
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Item Manager")

        name_var = tk.StringVar()
        type_var = tk.StringVar()
        level_var = tk.StringVar(value="0")
        stat_vars = {key: tk.StringVar() for key in STAT_KEYS}
        self.manager_stat_vars = stat_vars

        ttk.Label(frame, text="Name").grid(column=0, row=0, sticky=tk.W, pady=2)
        ttk.Entry(frame, textvariable=name_var, width=40).grid(column=1, row=0, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(frame, text="Type").grid(column=0, row=1, sticky=tk.W, pady=2)
        type_combo = ttk.Combobox(frame, textvariable=type_var, values=ITEM_TYPES, width=37)
        type_combo.grid(column=1, row=1, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(frame, text="Required Level").grid(column=0, row=2, sticky=tk.W, pady=2)
        ttk.Entry(frame, textvariable=level_var, width=40).grid(column=1, row=2, sticky=(tk.W, tk.E), pady=2)

        start_row = 3
        for offset, key in enumerate(STAT_KEYS):
            ttk.Label(frame, text=key).grid(column=0, row=start_row + offset, sticky=tk.W, pady=2)
            ttk.Entry(frame, textvariable=stat_vars[key], width=40).grid(
                column=1, row=start_row + offset, sticky=(tk.W, tk.E), pady=2
            )

        init_button = ttk.Button(frame, text="Initialize DB", command=self._init_db_clicked)
        init_button.grid(column=0, row=start_row + len(STAT_KEYS), pady=(6, 0), sticky=tk.W)

        add_button = ttk.Button(
            frame,
            text="Add Item",
            command=lambda: self._add_item_clicked(name_var, type_var, level_var),
        )
        add_button.grid(column=1, row=start_row + len(STAT_KEYS), pady=(6, 0), sticky=tk.E)

        frame.columnconfigure(1, weight=1)

        self.manager_name_var = name_var
        self.manager_type_var = type_var
        self.manager_level_var = level_var

    def _init_db_clicked(self) -> None:
        init_db()
        messagebox.showinfo("Database", "Database initialized")
        self.refresh_items()

    def _add_item_clicked(
        self,
        name_var: tk.StringVar,
        type_var: tk.StringVar,
        level_var: tk.StringVar,
    ) -> None:
        try:
            name = name_var.get().strip()
            type_ = type_var.get().strip()
            level = int(level_var.get() or 0)
            if not name or not type_:
                raise ValueError("Name and type are required")
            stats = {}
            for key, var in self.manager_stat_vars.items():
                raw = var.get().strip()
                if raw:
                    stats[key] = float(raw)
            add_item(Item(name=name, type=type_, required_level=level, stats=stats))
        except ValueError:
            messagebox.showerror("Error", "Level and stats must be numeric")
            return
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        messagebox.showinfo("Success", f"Inserted {name}")
        name_var.set("")
        type_var.set("")
        level_var.set("0")
        for var in self.manager_stat_vars.values():
            var.set("")
        self.refresh_items()

    # ------------------------------------------------------------------
    @staticmethod
    def _coerce_value(value: str, default) -> int | float:
        if isinstance(default, int):
            return int(value) if value.strip() else int(default)
        return float(value) if value.strip() else float(default)


def main() -> None:
    root = tk.Tk()
    UnifiedApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
