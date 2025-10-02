# DPS Calculator

This repository contains a Python script to estimate Warrior DPS in World of Warcraft Classic Era. The script implements common attack table and damage formulas used in Classic.

## Requirements

- Python 3

## Usage

Run `dps_calculator.py` with your character stats. For example:

```bash
python3 dps_calculator.py \
  --base-damage-mh 100 \
  --base-speed-mh 3.6 \
  --attack-power 500 \
  --hit 6 \
  --crit 5
```

The script prints the estimated DPS based on the provided statistics.

### Graphical Interface

A unified Tkinter interface is available in `unified_gui.py`. It provides
three tabs that cover manual DPS calculations, item-based simulations, and item
database management from a single window:

```bash
python3 unified_gui.py
```

The legacy standalone GUIs (`dps_gui.py`, `dps_with_items_gui.py`, and
`item_manager_gui.py`) remain available if you prefer a focused tool for a
specific task.

## Item Database

Items can be stored in a small SQLite database. Use `item_manager.py` to
initialize the database and insert items. Stats are provided as simple
`key=value` pairs instead of a JSON blob for ease of use. Keys correspond to
the fields used in `WarriorStats` (e.g. `attack_power`, `hit`,
`base_damage_mh`). Item stats may also include `str` and `agi`, which are
automatically converted to attack power and crit chance. Run
`item_manager.py --list-stats` to see all supported stat keys. Items can only
provide `spellbook_crit` for critical strike chance.

Create the database and add an item:

```bash
python3 item_manager.py --init-db
python3 item_manager.py --add "Fiery Axe" weapon_mh 60 \
  --stat base_damage_mh=100 --stat base_speed_mh=3.6
```

Once items are stored you can perform DPS calculations using their stats with
`dps_with_items.py`:

```bash
python3 dps_with_items.py --items "Fiery Axe" --weapon-skill 300
```

This script loads the specified items, merges their stats and passes them to
`dps_calculator.py`.
