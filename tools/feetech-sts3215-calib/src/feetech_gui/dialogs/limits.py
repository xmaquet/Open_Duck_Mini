import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.simpledialog import Dialog
from ..config_defaults import LIMITS_DEFAULTS

class LimitsDialog(Dialog):
    def __init__(self, parent, current: dict):
        self._cur = current.copy()
        super().__init__(parent, title="Limites du servo")

    def body(self, master):
        ttk.Label(master, text="Min (°)").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ttk.Label(master, text="Max (°)").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        ttk.Label(master, text="Graduations (°)").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        ttk.Label(master, text="Résolution (°)").grid(row=3, column=0, sticky="e", padx=6, pady=6)

        self.min_var = tk.IntVar(value=self._cur["min"])
        self.max_var = tk.IntVar(value=self._cur["max"])
        self.tick_var = tk.IntVar(value=self._cur["tick"])
        self.res_var = tk.IntVar(value=self._cur["res"])

        self.sp_min  = ttk.Spinbox(master, from_=-360, to=0,    increment=1, textvariable=self.min_var,  width=8)
        self.sp_max  = ttk.Spinbox(master, from_=0,    to=360,  increment=1, textvariable=self.max_var,  width=8)
        self.sp_tick = ttk.Spinbox(master, from_=5,    to=180,  increment=5, textvariable=self.tick_var, width=8)
        self.sp_res  = ttk.Spinbox(master, from_=1,    to=10,   increment=1, textvariable=self.res_var,  width=8)

        self.sp_min.grid(row=0, column=1, padx=6, pady=6)
        self.sp_max.grid(row=1, column=1, padx=6, pady=6)
        self.sp_tick.grid(row=2, column=1, padx=6, pady=6)
        self.sp_res.grid(row=3, column=1, padx=6, pady=6)

        btns = ttk.Frame(master); btns.grid(row=4, column=0, columnspan=2, pady=(10, 2))
        ttk.Button(btns, text="Défauts", command=self._defaults).pack(side="left", padx=4)
        return self.sp_min

    def _defaults(self):
        self.min_var.set(LIMITS_DEFAULTS["min"])
        self.max_var.set(LIMITS_DEFAULTS["max"])
        self.tick_var.set(LIMITS_DEFAULTS["tick"])
        self.res_var.set(LIMITS_DEFAULTS["res"])

    def validate(self):
        try:
            mn = int(self.min_var.get()); mx = int(self.max_var.get())
            tkc = int(self.tick_var.get()); rs = int(self.res_var.get())
            if mn >= mx:                     raise ValueError("Min doit être < Max")
            if tkc <= 0 or rs <= 0:          raise ValueError("Graduations et Résolution doivent être > 0")
            self.result = {"min": mn, "max": mx, "tick": tkc, "res": rs}
            return True
        except Exception as e:
            messagebox.showerror("Valeurs invalides", str(e), parent=self)
            return False
