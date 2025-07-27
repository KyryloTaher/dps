import tkinter as tk
from tkinter import ttk, messagebox
import argparse
from dps_with_items import build_stats
from dps_calculator import calculate_dps
from item_database import list_item_names


def compute():
    try:
        items = [var.get() for var in slot_vars.values() if var.get()]
        args = argparse.Namespace(
            player_level=int(player_level_var.get() or 60),
            target_level=int(target_level_var.get() or 63),
            weapon_skill=int(weapon_skill_var.get() or 300),
            items=items,
            dual_wield_spec=int(dual_wield_spec_var.get() or 0),
            impale=int(impale_var.get() or 0),
            target_armor=int(target_armor_var.get() or 0),
            target_block_value=float(target_block_value_var.get() or 45.0),
        )
        stats = build_stats(args)
        dps = calculate_dps(stats)
        result_var.set(f"Estimated DPS: {dps:.2f}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


root = tk.Tk()
root.title("DPS with Items")

mainframe = ttk.Frame(root, padding="10")
mainframe.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

player_level_var = tk.StringVar(value="60")
target_level_var = tk.StringVar(value="63")
weapon_skill_var = tk.StringVar(value="300")
dual_wield_spec_var = tk.StringVar(value="0")
impale_var = tk.StringVar(value="0")
target_armor_var = tk.StringVar(value="0")
target_block_value_var = tk.StringVar(value="45.0")
result_var = tk.StringVar()

fields = [
    ("Player Level", player_level_var),
    ("Target Level", target_level_var),
    ("Weapon Skill", weapon_skill_var),
    ("Dual Wield Spec", dual_wield_spec_var),
    ("Impale", impale_var),
    ("Target Armor", target_armor_var),
    ("Target Block Value", target_block_value_var),
]

for i, (label, var) in enumerate(fields):
    ttk.Label(mainframe, text=label).grid(column=0, row=i, sticky=tk.W)
    ttk.Entry(mainframe, textvariable=var).grid(column=1, row=i, sticky=(tk.W, tk.E))

# Item selection
slot_names = [
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
]
slot_vars = {name: tk.StringVar() for name in slot_names}

try:
    all_items = list_item_names()
except Exception:
    all_items = []

equip_frame = ttk.Frame(mainframe, padding="5")
equip_frame.grid(column=2, row=0, rowspan=len(fields), padx=(20, 0))

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

for name, var in slot_vars.items():
    r, c = layout.get(name, (0, 0))
    ttk.Label(equip_frame, text=name).grid(row=r * 2, column=c, sticky=tk.W)
    ttk.Combobox(equip_frame, textvariable=var, values=all_items, width=20).grid(
        row=r * 2 + 1, column=c, sticky=(tk.W, tk.E)
    )

compute_button = ttk.Button(mainframe, text="Calculate", command=compute)
compute_button.grid(column=0, row=len(fields), columnspan=2, pady=(5, 0))

result_label = ttk.Label(mainframe, textvariable=result_var, font=("Helvetica", 12))
result_label.grid(column=0, row=len(fields)+1, columnspan=2, pady=(5, 0))

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=2)

root.mainloop()
