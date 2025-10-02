# Warrior DPS Toolkit

This project provides a single Tkinter application, `unified_gui.py`, that brings
together every tool required to evaluate a Classic Era warrior. The legacy
command line utilities and standalone GUIs have been removed so the entire
workflow now lives in one window.

The application supports three major tasks:

1. **Equipment-based DPS** – Select items from the SQLite database to build your
   character and evaluate white hit DPS. Supplemental inputs let you provide
   rage, block value, improved cleave ranks and the normalized weapon speed so
   the calculator can report damage for every major warrior ability.
2. **Warrior skills breakdown** – After running a calculation the UI lists the
   expected damage for Bloodthirst, Mortal Strike, Execute, Whirlwind, Slam and
   every other yellow ability supported by the simulator.
3. **Item management** – Items can be created, updated and stored directly from
   the "Item Manager" tab without leaving the application.

## Requirements

- Python 3

## Running the application

Launch the Tkinter UI with:

```bash
python3 unified_gui.py
```

The first tab lets you enter target information, ability modifiers and select
your equipment. Press **Calculate** to compute DPS and populate the warrior
skills table.

The "Item Manager" tab provides controls to initialise the SQLite database,
insert new items and define their stats. Supported stat keys include attack
power, hit, crit, aura crit, weapon damage and ability modifiers such as block
value, rage, improved cleave ranks and bonus execute rage. Strength and agility
will automatically convert into the relevant derived stats when items are
loaded.

The database file (`items.db`) is created automatically in the project
directory when you first run the application or press **Initialize DB**.
