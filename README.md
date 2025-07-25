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
