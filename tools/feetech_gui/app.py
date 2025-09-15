import tkinter as tk
from tkinter import ttk, messagebox
from .io_adapter import MotorBus
from .config_service import load_offsets, save_offsets, set_zero

DEFAULT_PORT = "/dev/ttyACM0"   # adapte si besoin
DEFAULT_BAUD = 1_000_000


class MotorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Feetech STS3215 Config")
        self.geometry("560x420")

        self.port_var = tk.StringVar(value=DEFAULT_PORT)
        self.baud_var = tk.IntVar(value=DEFAULT_BAUD)

        self.ids = []
        self.selected_id = tk.IntVar(value=1)
        self.goal_var = tk.DoubleVar(value=0.0)
        self.new_id_var = tk.IntVar(value=10)
        self.new_baud_var = tk.IntVar(value=1_000_000)

        self.offsets = load_offsets()
        self._build_ui()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=10); frm.pack(fill="both", expand=True)

        row = ttk.Frame(frm); row.pack(fill="x", pady=4)
        ttk.Label(row, text="Port").pack(side="left")
        ttk.Entry(row, textvariable=self.port_var, width=18).pack(side="left", padx=6)
        ttk.Label(row, text="Baud").pack(side="left")
        ttk.Entry(row, textvariable=self.baud_var, width=10).pack(side="left", padx=6)
        ttk.Button(row, text="Scanner", command=self.scan).pack(side="right")

        row2 = ttk.Frame(frm); row2.pack(fill="x", pady=8)
        ttk.Label(row2, text="Moteur ID").pack(side="left")
        self.id_combo = ttk.Combobox(row2, textvariable=self.selected_id, width=8, values=[])
        self.id_combo.pack(side="left", padx=6)

        grp = ttk.LabelFrame(frm, text="Contrôle position (deg)")
        grp.pack(fill="x", pady=8)
        ttk.Scale(grp, from_=-180, to=180, variable=self.goal_var).pack(fill="x", padx=10, pady=6)
        ttk.Button(grp, text="Appliquer", command=self.move_to).pack(pady=4)

        z = ttk.Frame(frm); z.pack(fill="x", pady=6)
        ttk.Button(z, text="Définir zéro (position actuelle)", command=self.set_zero).pack(side="left")

        cfg = ttk.LabelFrame(frm, text="Paramétrage"); cfg.pack(fill="x", pady=8)
        left = ttk.Frame(cfg); left.pack(side="left", padx=10, pady=6)
        ttk.Label(left, text="Nouvel ID").pack()
        ttk.Entry(left, textvariable=self.new_id_var, width=8).pack()
        ttk.Button(left, text="Appliquer ID", command=self.apply_new_id).pack(pady=4)

        right = ttk.Frame(cfg); right.pack(side="left", padx=20, pady=6)
        ttk.Label(right, text="Nouveau Baud").pack()
        ttk.Entry(right, textvariable=self.new_baud_var, width=12).pack()
        ttk.Button(right, text="Appliquer Baud", command=self.apply_new_baud).pack(pady=4)

        self.status = tk.StringVar(value="Prêt.")
        ttk.Label(frm, textvariable=self.status).pack(anchor="w", pady=6)

    def _bus(self):
        return MotorBus(self.port_var.get(), self.baud_var.get())

    def scan(self):
        try:
            with self._bus().session() as bus:
                self.ids = bus.scan(range(1, 60))
            self.id_combo["values"] = self.ids
            if self.ids:
                self.selected_id.set(self.ids[0])
                self.status.set(f"Trouvé : {self.ids}")
            else:
                self.status.set("Aucun moteur détecté.")
        except Exception as e:
            messagebox.showerror("Scan", str(e))

    def move_to(self):
        mid = int(self.selected_id.get()); goal = float(self.goal_var.get())
        try:
            with self._bus().session() as bus:
                bus.set_goal_position({mid: goal})
            self.status.set(f"ID {mid} -> {goal:.2f}°")
        except Exception as e:
            messagebox.showerror("Mouvement", str(e))

    def set_zero(self):
        mid = int(self.selected_id.get())
        try:
            with self._bus().session() as bus:
                pos = bus.get_present_position([mid])[0]
            self.offsets = set_zero(self.offsets, mid, pos)
            save_offsets(self.offsets)
            self.status.set(f"Zéro logiciel défini pour ID {mid} (pos={pos:.2f}°)")
        except Exception as e:
            messagebox.showerror("Zéro", str(e))

    def apply_new_id(self):
        mid = int(self.selected_id.get()); new_id = int(self.new_id_var.get())
        try:
            with self._bus().session() as bus:
                bus.change_id({mid: new_id})
            self.status.set(f"ID {mid} → {new_id}. Re-scan recommandé.")
        except Exception as e:
            messagebox.showerror("Changer ID", str(e))

    def apply_new_baud(self):
        mid = int(self.selected_id.get()); new_baud = int(self.new_baud_var.get())
        try:
            with self._bus().session() as bus:
                bus.change_baudrate({mid: new_baud})
            self.status.set(f"Baud de l’ID {mid} → {new_baud}. Mets à jour le champ Baud puis re-scan.")
        except Exception as e:
            messagebox.showerror("Changer Baud", str(e))


def main():
    MotorGUI().mainloop()

if __name__ == "__main__":
    main()

