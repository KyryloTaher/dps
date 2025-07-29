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

A simple Tkinter based GUI is available in `dps_gui.py`. Launch it with Python
and fill in your character stats in the form. The result will be displayed in
the window when you click **Calculate**:

```bash
python3 dps_gui.py
```

GUIs are also provided for the item manager and for calculating DPS using items.

Run `item_manager_gui.py` to initialize the database or insert items through a
simple form, and `dps_with_items_gui.py` to calculate DPS using equipment from
the database. The item manager GUI now provides a separate input field for each
stat instead of a drop-down list.

```bash
python3 item_manager_gui.py
python3 dps_with_items_gui.py
```

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
