"""Unified Tkinter interface for all DPS tools."""


from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from types import SimpleNamespace

from dps_calculator import WarriorStats, calculate_dps
from dps_with_items import build_stats
from item_database import init_db, add_item, list_item_names, Item
from item_manager import STAT_KEYS, ITEM_TYPES


class UnifiedApp:
    """Main application window grouping every GUI utility into a single place."""

    MANUAL_FIELDS = (
        ("Player Level", "player_level", 60),
        ("Target Level", "target_level", 63),
        ("Weapon Skill", "weapon_skill", 300),
        ("Base Damage MH", "base_damage_mh", 0.0),
        ("Base Speed MH", "base_speed_mh", 0.0),
        ("Attack Power", "attack_power", 0.0),
        ("Hit %", "hit", 0.0),
        ("Crit %", "spellbook_crit", 0.0),
        ("Aura Crit %", "aura_crit", 0.0),
        ("Base Damage OH", "base_damage_oh", 0.0),
        ("Base Speed OH", "base_speed_oh", 0.0),
        ("Dual Wield Spec", "dual_wield_spec", 0),
        ("Impale", "impale", 0),
        ("Target Armor", "target_armor", 0),
        ("Target Block Value", "target_block_value", 45.0),
    )

    ITEM_FIELDS = (
        ("Player Level", "player_level", 60),
        ("Target Level", "target_level", 63),
        ("Weapon Skill", "weapon_skill", 300),
        ("Dual Wield Spec", "dual_wield_spec", 0),
        ("Impale", "impale", 0),
        ("Target Armor", "target_armor", 0),
        ("Target Block Value", "target_block_value", 45.0),
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

        # Make sure the database exists before trying to read from it.
        init_db()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.manual_vars: dict[str, tk.StringVar] = {}
        self.item_vars: dict[str, tk.StringVar] = {}
        self.slot_vars: dict[str, tk.StringVar] = {}
        self.item_comboboxes: list[ttk.Combobox] = []

        self.result_manual = tk.StringVar(value="")
        self.result_items = tk.StringVar(value="")

        self._create_manual_tab()
        self._create_item_tab()
        self._create_manager_tab()

        self.refresh_items()

    # ------------------------------------------------------------------
    # Manual DPS tab
    def _create_manual_tab(self) -> None:
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Manual DPS")

        for row, (label, key, default) in enumerate(self.MANUAL_FIELDS):
            ttk.Label(frame, text=label).grid(column=0, row=row, sticky=tk.W, pady=2)
            var = tk.StringVar(value=str(default))
            entry = ttk.Entry(frame, textvariable=var)
            entry.grid(column=1, row=row, sticky=(tk.W, tk.E), pady=2)
            self.manual_vars[key] = var

        calc_button = ttk.Button(frame, text="Calculate", command=self.calculate_manual_dps)
        calc_button.grid(column=0, row=len(self.MANUAL_FIELDS), columnspan=2, pady=(6, 0))

        result_label = ttk.Label(
            frame,
            textvariable=self.result_manual,
            font=("Helvetica", 12),
        )
        result_label.grid(column=0, row=len(self.MANUAL_FIELDS) + 1, columnspan=2, pady=(6, 0))

        frame.columnconfigure(1, weight=1)

    def calculate_manual_dps(self) -> None:
        try:
            stats_kwargs = {
                key: self._coerce_value(self.manual_vars[key].get(), default)
                for _, key, default in self.MANUAL_FIELDS
            }
            stats = WarriorStats(**stats_kwargs)
        except ValueError:
            self.result_manual.set("Invalid input")
            return

        dps = calculate_dps(stats)
        self.result_manual.set(f"Estimated DPS: {dps:.2f}")

    # ------------------------------------------------------------------
    # Item-based DPS tab
    def _create_item_tab(self) -> None:
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Items DPS")

        for row, (label, key, default) in enumerate(self.ITEM_FIELDS):
            ttk.Label(frame, text=label).grid(column=0, row=row, sticky=tk.W, pady=2)
            var = tk.StringVar(value=str(default))
            entry = ttk.Entry(frame, textvariable=var)
            entry.grid(column=1, row=row, sticky=(tk.W, tk.E), pady=2)
            self.item_vars[key] = var

        equip_frame = ttk.LabelFrame(frame, text="Equipment", padding=10)
        equip_frame.grid(column=2, row=0, rowspan=len(self.ITEM_FIELDS), padx=(20, 0), sticky=tk.N)

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
        compute_button.grid(column=0, row=len(self.ITEM_FIELDS), columnspan=2, pady=(6, 0))

        result_label = ttk.Label(
            frame,
            textvariable=self.result_items,
            font=("Helvetica", 12),
        )
        result_label.grid(column=0, row=len(self.ITEM_FIELDS) + 1, columnspan=2, pady=(6, 0))

        refresh_button = ttk.Button(frame, text="Refresh Items", command=self.refresh_items)
        refresh_button.grid(column=2, row=len(self.ITEM_FIELDS), padx=(20, 0), sticky=tk.E)

        frame.columnconfigure(1, weight=1)

    def calculate_item_dps(self) -> None:
        try:
            args = {
                key: self._coerce_value(self.item_vars[key].get(), default)
                for _, key, default in self.ITEM_FIELDS
            }
            args["items"] = [var.get() for var in self.slot_vars.values() if var.get()]
            namespace = SimpleNamespace(**args)
            stats = build_stats(namespace)
        except ValueError:
            self.result_items.set("Invalid input")
            return
        except Exception as exc:  # Database issues and alike
            messagebox.showerror("Error", str(exc))
            return

        dps = calculate_dps(stats)
        self.result_items.set(f"Estimated DPS: {dps:.2f}")

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
