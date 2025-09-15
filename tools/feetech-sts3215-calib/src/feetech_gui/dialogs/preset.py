import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.simpledialog import Dialog
from ..config_defaults import PRESET_DEFAULT

class PresetDialog(Dialog):
    FIELDS = ["P", "I", "D", "mode", "max_accel", "accel", "lock"]

    def __init__(self, parent, current: dict):
        self._cur = current.copy()
        super().__init__(parent, title="Preset Open Duck")

    def body(self, master):
        self.vars = {k: tk.IntVar(value=int(self._cur[k])) for k in self.FIELDS}
        for r, k in enumerate(self.FIELDS):
            ttk.Label(master, text=k).grid(row=r, column=0, sticky="e", padx=6, pady=6)
            ttk.Spinbox(master, textvariable=self.vars[k], width=10,
                        from_=-32768, to=32767, increment=1).grid(row=r, column=1, padx=6, pady=6)
        btns = ttk.Frame(master); btns.grid(row=len(self.FIELDS), column=0, columnspan=2, pady=(10, 2))
        ttk.Button(btns, text="Défauts", command=self._defaults).pack(side="left", padx=4)

    def _defaults(self):
        for k, v in PRESET_DEFAULT.items():
            self.vars[k].set(int(v))

    def validate(self):
        try:
            self.result = {k: int(v.get()) for k, v in self.vars.items()}
            return True
        except Exception as e:
            messagebox.showerror("Valeurs invalides", str(e), parent=self)
            return False
