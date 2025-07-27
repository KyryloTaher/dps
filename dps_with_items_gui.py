import tkinter as tk
from tkinter import ttk, messagebox
import argparse
from dps_with_items import build_stats
from dps_calculator import calculate_dps


def compute():
    try:
        items = [name.strip() for name in items_var.get().split(',') if name.strip()]
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
items_var = tk.StringVar()
dual_wield_spec_var = tk.StringVar(value="0")
impale_var = tk.StringVar(value="0")
target_armor_var = tk.StringVar(value="0")
target_block_value_var = tk.StringVar(value="45.0")
result_var = tk.StringVar()

fields = [
    ("Player Level", player_level_var),
    ("Target Level", target_level_var),
    ("Weapon Skill", weapon_skill_var),
    ("Items (comma separated)", items_var),
    ("Dual Wield Spec", dual_wield_spec_var),
    ("Impale", impale_var),
    ("Target Armor", target_armor_var),
    ("Target Block Value", target_block_value_var),
]

for i, (label, var) in enumerate(fields):
    ttk.Label(mainframe, text=label).grid(column=0, row=i, sticky=tk.W)
    ttk.Entry(mainframe, textvariable=var).grid(column=1, row=i, sticky=(tk.W, tk.E))

compute_button = ttk.Button(mainframe, text="Calculate", command=compute)
compute_button.grid(column=0, row=len(fields), columnspan=2, pady=(5, 0))

result_label = ttk.Label(mainframe, textvariable=result_var, font=("Helvetica", 12))
result_label.grid(column=0, row=len(fields)+1, columnspan=2, pady=(5, 0))

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=2)

root.mainloop()
