import tkinter as tk
from tkinter import ttk
from dps_calculator import WarriorStats, calculate_dps


def compute():
    try:
        stats = WarriorStats(
            player_level=int(player_level_var.get() or 60),
            target_level=int(target_level_var.get() or 63),
            weapon_skill=int(weapon_skill_var.get() or 300),
            base_damage_mh=float(base_damage_mh_var.get() or 0),
            base_speed_mh=float(base_speed_mh_var.get() or 0),
            attack_power=float(attack_power_var.get() or 0),
            hit=float(hit_var.get() or 0),
            spellbook_crit=float(crit_var.get() or 0),
            aura_crit=float(aura_crit_var.get() or 0),
            base_damage_oh=float(base_damage_oh_var.get() or 0),
            base_speed_oh=float(base_speed_oh_var.get() or 0),
            dual_wield_spec=int(dual_wield_spec_var.get() or 0),
            impale=int(impale_var.get() or 0),
            target_armor=int(target_armor_var.get() or 0),
            target_block_value=float(target_block_value_var.get() or 45.0),
        )
        dps = calculate_dps(stats)
        result_var.set(f"Estimated DPS: {dps:.2f}")
    except ValueError:
        result_var.set("Invalid input")


root = tk.Tk()
root.title("DPS Calculator")

mainframe = ttk.Frame(root, padding="10")
mainframe.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Variables
player_level_var = tk.StringVar(value="60")
target_level_var = tk.StringVar(value="63")
weapon_skill_var = tk.StringVar(value="300")
base_damage_mh_var = tk.StringVar()
base_speed_mh_var = tk.StringVar()
attack_power_var = tk.StringVar()
hit_var = tk.StringVar(value="0")
crit_var = tk.StringVar(value="0")
aura_crit_var = tk.StringVar(value="0")
base_damage_oh_var = tk.StringVar(value="0")
base_speed_oh_var = tk.StringVar(value="0")
dual_wield_spec_var = tk.StringVar(value="0")
impale_var = tk.StringVar(value="0")

# Target armor and block value
target_armor_var = tk.StringVar(value="0")
target_block_value_var = tk.StringVar(value="45.0")

result_var = tk.StringVar(value="")

fields = [
    ("Player Level", player_level_var),
    ("Target Level", target_level_var),
    ("Weapon Skill", weapon_skill_var),
    ("Base Damage MH", base_damage_mh_var),
    ("Base Speed MH", base_speed_mh_var),
    ("Attack Power", attack_power_var),
    ("Hit %", hit_var),
    ("Crit %", crit_var),
    ("Aura Crit %", aura_crit_var),
    ("Base Damage OH", base_damage_oh_var),
    ("Base Speed OH", base_speed_oh_var),
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
