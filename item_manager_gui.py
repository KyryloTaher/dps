import tkinter as tk
from tkinter import ttk, messagebox
from item_database import init_db, add_item, Item
from item_manager import STAT_KEYS, ITEM_TYPES


def init_db_action():
    init_db()
    messagebox.showinfo("Success", "Database initialized")


def add_item_action():
    try:
        name = name_var.get()
        type_ = type_var.get()
        level = int(level_var.get())
        stats = {}
        for key, var in stat_vars.items():
            value = var.get().strip()
            if value:
                stats[key] = float(value)
        add_item(Item(name=name, type=type_, required_level=level, stats=stats))
        messagebox.showinfo("Success", f"Inserted {name}")
        for var in stat_vars.values():
            var.set("")
    except ValueError:
        messagebox.showerror("Error", "Stat values must be numeric")
    except Exception as e:
        messagebox.showerror("Error", str(e))


root = tk.Tk()
root.title("Item Manager")

mainframe = ttk.Frame(root, padding="10")
mainframe.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

name_var = tk.StringVar()
type_var = tk.StringVar()
level_var = tk.StringVar(value="0")

stat_vars = {key: tk.StringVar() for key in STAT_KEYS}

fields = [
    ("Name", name_var),
    ("Type", type_var),
    ("Required Level", level_var),
]
fields += [(key, stat_vars[key]) for key in STAT_KEYS]

for i, (label, var) in enumerate(fields):
    ttk.Label(mainframe, text=label).grid(column=0, row=i, sticky=tk.W)
    if label == "Type":
        ttk.Combobox(mainframe, textvariable=var, values=ITEM_TYPES, width=37).grid(
            column=1, row=i, sticky=(tk.W, tk.E)
        )
    else:
        ttk.Entry(mainframe, textvariable=var, width=40).grid(
            column=1, row=i, sticky=(tk.W, tk.E)
        )

init_button = ttk.Button(mainframe, text="Initialize DB", command=init_db_action)
init_button.grid(column=0, row=len(fields), pady=(5, 0))

add_button = ttk.Button(mainframe, text="Add Item", command=add_item_action)
add_button.grid(column=1, row=len(fields), pady=(5, 0))

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=2)

root.mainloop()
