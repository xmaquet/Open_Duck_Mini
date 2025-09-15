import time
import math
import tkinter as tk
from tkinter import ttk, messagebox

import serial
from serial.tools import list_ports

from .io_adapter import MotorBus
from .config_service import load_offsets, save_offsets, set_zero
from .config_defaults import DEFAULT_PORT, DEFAULT_BAUD, LIMITS_DEFAULTS, PRESET_DEFAULT
from .tooltips import attach_tooltip
from .dialogs.limits import LimitsDialog
from .dialogs.preset import PresetDialog
from .ui_prefs import load_ui_prefs, save_ui_prefs


# --------- Helpers ports série ---------
def available_ports() -> list[str]:
    try:
        return [p.device for p in list_ports.comports()]
    except Exception:
        return []


def port_is_connected(port: str) -> bool:
    return bool(port) and port in available_ports()


class MotorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Feetech STS3215 - Calibration")
        # Thème & styles colorés pour boutons
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")  # plus permissif pour recolorer
        except Exception:
            pass

        # Bleu moyen = Primary
        self.style.configure(
            "Primary.TButton",
            background="#3B82F6",  # bleu
            foreground="white",
            padding=(10, 4)
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", "#2563EB"), ("disabled", "#93C5FD")],
            foreground=[("disabled", "#e5e7eb")]  # gris clair
        )

        # Orange = Warning
        self.style.configure(
            "Warning.TButton",
            background="#F59E0B",
            foreground="black",
            padding=(10, 4)
        )
        self.style.map(
            "Warning.TButton",
            background=[("active", "#D97706"), ("disabled", "#FDE68A")],
            foreground=[("disabled", "#374151")]  # gris foncé lisible
        )

        # UI large (option A)
        self.geometry("1500x900")
        try:
            self.minsize(1200, 620)
        except Exception:
            pass

        # Menu
        self._build_menubar()

        # Variables UI
        self.port_var = tk.StringVar(value=DEFAULT_PORT)
        self.baud_var = tk.IntVar(value=DEFAULT_BAUD)

        self.selected_id = tk.IntVar(value=0)
        self.goal_var = tk.DoubleVar(value=0.0)
        self.goal_display = tk.StringVar(value="0°")
        self.auto_apply = tk.BooleanVar(value=False)

        self.new_id_var = tk.IntVar(value=10)
        self.new_baud_var = tk.IntVar(value=1_000_000)

        # Données
        self.offsets = load_offsets()
        self.limits = LIMITS_DEFAULTS.copy()
        self.preset = PRESET_DEFAULT.copy()

        # Charger préférences UI et appliquer
        prefs = load_ui_prefs()
        try:
            self.port_var.set(prefs.get("port", self.port_var.get()))
            self.baud_var.set(int(prefs.get("baud", self.baud_var.get())))
            self.auto_apply.set(bool(prefs.get("auto_apply", False)))
            self.limits.update(prefs.get("limits", {}))
            self.preset.update(prefs.get("preset", {}))
        except Exception:
            pass

        # Références widgets
        self.port_combo = self.btn_refresh = self.entry_baud = self.btn_scan = None
        self.goal_scale = self.btn_move = self.btn_center = self.chk_auto = None
        self.btn_zero_soft = self.btn_zero_hw = self.btn_verify_zero = None
        self.btn_torque_off = self.btn_torque_on = None
        self.entry_new_id = self.btn_apply_id = None
        self.entry_new_baud = self.btn_apply_baud = None
        self.btn_preset = self.id_entry = None

        self.status = tk.StringVar(value="Prêt.")

        # Spinner
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self._busy = False

        # Auto-apply
        self._apply_job = None

        # Monitoring (retour capteur)
        self.present_abs_var = tk.StringVar(value="—")
        self.present_log_var = tk.StringVar(value="—")
        self._monitor_job = None
        self._monitor_active = False

        # Canvas servo + jauge
        self._servo_canvas: tk.Canvas | None = None
        self._cx = self._cy = self._r = None  # centre + rayon palonnier
        self._horn_item = None
        self._gauge = {
            "radius": None,
            "ring": None,
            "ticks": [],
            "labels": [],
            "active_arc": None,
        }

        self._build_ui()
        self._apply_limits_to_scale()

        # post-init
        self.after(100, lambda: self.refresh_ports(select_current=True))
        self.set_controls_enabled(False)

        # sauvegarde à la fermeture
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # --------- Menus ---------
    def _build_menubar(self):
        menubar = tk.Menu(self)

        cfg = tk.Menu(menubar, tearoff=0)
        cfg.add_command(label="Limites du servo…", command=self.open_limits_dialog)
        cfg.add_command(label="Preset Open Duck…", command=self.open_preset_dialog)
        cfg.add_separator()
        cfg.add_command(label="Restaurer valeurs par défaut", command=self.reset_limits_defaults)
        menubar.add_cascade(label="Configuration", menu=cfg)

        self.config(menu=menubar)

    def open_limits_dialog(self):
        dlg = LimitsDialog(self, current=self.limits)
        if getattr(dlg, "result", None):
            self.limits.update(dlg.result)
            self._apply_limits_to_scale()
            self._redraw_gauge_active_range()
            save_ui_prefs(self._current_prefs())

    def open_preset_dialog(self):
        dlg = PresetDialog(self, current=self.preset)
        if getattr(dlg, "result", None):
            self.preset.update(dlg.result)
            save_ui_prefs(self._current_prefs())

    def reset_limits_defaults(self):
        self.limits = LIMITS_DEFAULTS.copy()
        self._apply_limits_to_scale()
        self._redraw_gauge_active_range()
        save_ui_prefs(self._current_prefs())

    def _apply_limits_to_scale(self):
        if self.goal_scale is not None:
            self.goal_scale.config(
                from_=self.limits["min"],
                to=self.limits["max"],
                tickinterval=self.limits["tick"],
                resolution=self.limits["res"],
                length=1300,  # largeur fixe (option A)
            )
            v = max(self.limits["min"], min(self.limits["max"], float(self.goal_var.get())))
            step = self.limits["res"]
            v = round(v / step) * step
            self.goal_var.set(v)
            self._update_goal_display()

    def refresh_ports(self, select_current: bool = True):
        """Rafraîchit la liste des ports et met à jour le champ Port + statut."""
        ports = available_ports()

        # Mets à jour la combobox
        if self.port_combo is not None:
            self.port_combo["values"] = ports

        if ports:
            current = (self.port_var.get() or "").strip()
            # si select_current=True, on garde le port courant s'il est présent
            if not (select_current and current in ports):
                # sinon on sélectionne le premier trouvé
                self.port_var.set(ports[0])
            self.status.set(f"Ports détectés : {', '.join(ports)}")
        else:
            # aucun port -> on désactive les contrôles de mouvement
            self.status.set("Aucun port série détecté. Branche l’USB puis clique « ↻ ».")
            self.set_controls_enabled(False)

    # --------- Construction UI ---------
    def _build_ui(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        self._root_frame = frm

        # Ligne: Port / Rafraîchir / Baud / Scanner
        row = ttk.Frame(frm); row.pack(fill="x", pady=4)
        ttk.Label(row, text="Port").pack(side="left")
        self.port_combo = ttk.Combobox(row, textvariable=self.port_var, width=30, values=[], state="readonly")
        self.port_combo.pack(side="left", padx=6)
        self.btn_refresh = ttk.Button(row, text="↻", width=3, command=lambda: self.refresh_ports(select_current=False))
        self.btn_refresh.pack(side="left", padx=(0, 8))

        ttk.Label(row, text="Baud").pack(side="left")
        self.entry_baud = ttk.Entry(row, textvariable=self.baud_var, width=16)
        self.entry_baud.pack(side="left", padx=6)

        self.btn_scan = ttk.Button(row, text="Scanner", command=self.scan, style="Primary.TButton")
        self.btn_scan.pack(side="right")

        # ... après self.entry_baud.pack(...)
        self.btn_help = ttk.Button(row, text="Aide STS3215", command=self.open_docs)
        self.btn_help.pack(side="right", padx=(8, 0))

        # Sauvegarde prefs à chaque changement simple
        self.port_combo.bind("<<ComboboxSelected>>", lambda e: save_ui_prefs(self._current_prefs()))
        self.entry_baud.bind("<FocusOut>", lambda e: save_ui_prefs(self._current_prefs()))

        # Ligne: ID (lecture seule)
        row2 = ttk.Frame(frm); row2.pack(fill="x", pady=8)
        ttk.Label(row2, text="Moteur ID").pack(side="left")
        self.id_entry = ttk.Entry(row2, textvariable=self.selected_id, width=8, state="readonly", justify="center")
        self.id_entry.pack(side="left", padx=6)

        # Groupe: Contrôle position
        grp = ttk.LabelFrame(frm, text="Contrôle position (deg)")
        grp.pack(fill="x", pady=8)

        self.goal_scale = tk.Scale(
            grp,
            from_=self.limits["min"],
            to=self.limits["max"],
            orient="horizontal",
            resolution=self.limits["res"],
            tickinterval=self.limits["tick"],
            showvalue=False,
            length=1300,  # large
            variable=self.goal_var,
            command=self._on_scale_cmd,  # auto-apply fluide
        )
        self.goal_scale.pack(fill="x", padx=10, pady=(6, 2))

        rowg = ttk.Frame(grp); rowg.pack(fill="x", padx=10, pady=4)
        self.goal_display_lbl = ttk.Label(rowg, textvariable=self.goal_display, width=8, anchor="center")
        self.goal_display_lbl.pack(side="left")
        self.chk_auto = ttk.Checkbutton(rowg, text="Appliquer automatiquement", variable=self.auto_apply,
                                        command=lambda: save_ui_prefs(self._current_prefs()))
        self.chk_auto.pack(side="left", padx=(8, 12))
        self.btn_center = ttk.Button(rowg, text="Centrer (0°)", command=self.center_and_apply, style="Warning.TButton")
        self.btn_center.pack(side="left", padx=(8, 12))

        self.btn_move = ttk.Button(rowg, text="Appliquer", command=self.move_to, style="Primary.TButton")
        self.btn_move.pack(side="left")

        # --- Retour capteur + Illustration ---
        fb = ttk.LabelFrame(frm, text="Retour capteur")
        fb.pack(fill="x", pady=8)

        vals = ttk.Frame(fb); vals.pack(anchor="w", padx=10, pady=(6, 4))
        ttk.Label(vals, text="Présent abs :").pack(side="left")
        ttk.Label(vals, textvariable=self.present_abs_var, width=10).pack(side="left", padx=(4, 16))
        ttk.Label(vals, text="logique :").pack(side="left")
        ttk.Label(vals, textvariable=self.present_log_var, width=10).pack(side="left", padx=4)

        cwrap = ttk.Frame(fb); cwrap.pack(fill="x", padx=10, pady=(4, 8))
        self._servo_canvas = tk.Canvas(cwrap, width=520, height=260, bg="#f7f7f7",
                                       highlightthickness=1, relief="sunken")
        self._servo_canvas.pack(side="left")
        self._init_servo_canvas()
        attach_tooltip(self._servo_canvas,
                       "Illustration du servo STS3215. Le palonnier suit l'angle LU (présent).\n"
                       "La jauge montre la plage active (arc) et les graduations (-180..+180).")

        # Zéro + Couple
        z = ttk.LabelFrame(frm, text="Zéro / Couple")
        z.pack(fill="x", pady=6)
        self.btn_zero_soft = ttk.Button(z, text="Zéro logiciel (fichier)", command=self.set_zero_soft)
        self.btn_zero_soft.pack(side="left", padx=(8, 6), pady=4)
        self.btn_zero_hw = ttk.Button(z, text="Zéro matériel (EEPROM)", command=self.set_zero_hardware)
        self.btn_zero_hw.pack(side="left", padx=6, pady=4)
        self.btn_verify_zero = ttk.Button(z, text="Vérifier 0° (abs)", command=self.verify_zero_abs)
        self.btn_verify_zero.pack(side="left", padx=(6, 16), pady=4)
        self.btn_torque_off = ttk.Button(z, text="Désactiver couple", command=self.torque_off)
        self.btn_torque_off.pack(side="left", padx=(16, 6), pady=4)
        self.btn_torque_on = ttk.Button(z, text="Réactiver couple", command=self.torque_on)
        self.btn_torque_on.pack(side="left", padx=6, pady=4)

        # Paramétrage: ID / Baud
        cfg = ttk.LabelFrame(frm, text="Paramétrage")
        cfg.pack(fill="x", pady=8)

        left = ttk.Frame(cfg); left.pack(side="left", padx=10, pady=6)
        ttk.Label(left, text="Nouvel ID").pack()
        self.entry_new_id = ttk.Entry(left, textvariable=self.new_id_var, width=8)
        self.entry_new_id.pack()
        self.btn_apply_id = ttk.Button(left, text="Appliquer ID", command=self.apply_new_id, style="Warning.TButton")
        self.btn_apply_id.pack(pady=4)

        right = ttk.Frame(cfg); right.pack(side="left", padx=20, pady=6)
        ttk.Label(right, text="Nouveau Baud").pack()
        self.entry_new_baud = ttk.Entry(right, textvariable=self.new_baud_var, width=12)
        self.entry_new_baud.pack()
        self.btn_apply_baud = ttk.Button(right, text="Appliquer Baud", command=self.apply_new_baud)
        self.btn_apply_baud.pack(pady=4)

        # Preset Open Duck
        preset_row = ttk.Frame(frm); preset_row.pack(fill="x", pady=(6, 2))
        self.btn_preset = ttk.Button(preset_row, text="Configurer (preset Open Duck)", command=self.apply_preset_open_duck)
        self.btn_preset.pack(side="left")

        ttk.Label(frm, textvariable=self.status).pack(anchor="w", pady=6)

        # Spinner (caché au départ)
        self.progress.pack(fill="x", side="bottom"); self.progress.pack_forget()

        # Tooltips
        attach_tooltip(self.port_combo, "Port série de l’adaptateur USB-TTL.")
        attach_tooltip(self.btn_refresh, "Rafraîchir la liste des ports détectés.")
        attach_tooltip(self.entry_baud, "Vitesse du bus (bauds). Ex : 1000000, 500000, 115200.")
        attach_tooltip(self.btn_scan, "Scanner le bus (exactement 1 servo attendu).")
        attach_tooltip(self.id_entry, "Identifiant détecté du servo (lecture seule).")
        attach_tooltip(self.goal_scale,
                       f"Plage : {self.limits['min']}° … {self.limits['max']}°, ticks {self.limits['tick']}°.")
        attach_tooltip(self.chk_auto, "Si coché, la consigne est envoyée en temps réel quand vous bougez le slider.")
        attach_tooltip(self.btn_center, "Place et ENVOIE 0° immédiatement (zéro logiciel pris en compte).")
        attach_tooltip(self.btn_move, "Envoyer la consigne d’angle au servo (zéro logiciel pris en compte).")
        attach_tooltip(self.btn_zero_soft, "Définit la position actuelle comme zéro logiciel (fichier). Curseur centré.")
        attach_tooltip(self.btn_zero_hw, "Écrit le zéro en EEPROM SANS bouger. Validation par lecture seule.")
        attach_tooltip(self.btn_verify_zero, "Envoie 0° ABSOLU pour vérifier le zéro matériel (peut bouger).")
        attach_tooltip(self.btn_torque_off, "Coupe le couple (torque) pour déplacer le servo à la main.")
        attach_tooltip(self.btn_torque_on, "Réactive le couple (torque).")
        attach_tooltip(self.entry_new_id, "Saisir le nouvel ID (1–252).")
        attach_tooltip(self.btn_apply_id, "Change l’ID du servo. Re-scan recommandé.")
        attach_tooltip(self.entry_new_baud, "Saisir une nouvelle vitesse (ex : 1000000, 500000, 115200).")
        attach_tooltip(self.btn_apply_baud, "Change la vitesse du servo. Mets à jour Baud puis re-scan.")
        attach_tooltip(self.btn_preset, "Applique le preset courant (éditable via Configuration → Preset Open Duck…).")

    # --------- Busy / Spinner ---------
    def start_busy(self, text: str):
        if self._busy:
            return
        self._busy = True
        self.status.set(text)
        try:
            self.progress.pack(fill="x", side="bottom"); self.progress.start(8)
        except Exception:
            pass
        self.configure(cursor="watch")
        self._set_global_enabled(False)
        self.update_idletasks()

    def stop_busy(self, text: str | None = None):
        if not self._busy:
            return
        self._busy = False
        try:
            self.progress.stop(); self.progress.pack_forget()
        except Exception:
            pass
        self.configure(cursor="")
        self._set_global_enabled(True)
        if text is not None:
            self.status.set(text)

    def _set_global_enabled(self, enabled: bool):
        st = 'normal' if enabled else 'disabled'
        for w in (self.port_combo, self.btn_refresh, self.entry_baud, self.btn_scan, self.btn_preset):
            try:
                w.configure(state=st)
            except Exception:
                try:
                    w.state(['!disabled'] if enabled else ['disabled'])
                except Exception:
                    pass
        self.set_controls_enabled(enabled and int(self.selected_id.get()) > 0)

    # --------- Persistance ---------
    def _current_prefs(self) -> dict:
        return {
            "port": self.port_var.get(),
            "baud": int(self.baud_var.get()),
            "auto_apply": bool(self.auto_apply.get()),
            "limits": self.limits.copy(),
            "preset": self.preset.copy(),
        }

    def _on_close(self):
        try:
            save_ui_prefs(self._current_prefs())
            self._stop_monitor()
        finally:
            self.destroy()

    # --------- Utils UI ---------
    def _update_goal_display(self):
        try:
            self.goal_display.set(f"{int(round(float(self.goal_var.get())))}°")
        except Exception:
            pass

    def _on_scale_cmd(self, _val):
        self._update_goal_display()
        if self.auto_apply.get() and int(self.selected_id.get()) > 0 and self.goal_scale['state'] == 'normal':
            self.move_to()  # envoi immédiat

    def set_controls_enabled(self, enabled: bool):
        st = 'normal' if enabled else 'disabled'
        widgets = [
            self.goal_scale, self.btn_move, self.btn_center, self.chk_auto,
            self.btn_zero_soft, self.btn_zero_hw, self.btn_verify_zero,
            self.btn_torque_off, self.btn_torque_on,
            self.btn_apply_id, self.btn_apply_baud,
            self.entry_new_id, self.entry_new_baud,
        ]
        for w in widgets:
            if w is None:
                continue
            try:
                w.configure(state=st)
            except Exception:
                try:
                    w.state(['!disabled'] if enabled else ['disabled'])
                except Exception:
                    pass

    # --------- Canvas & jauge ---------
    def _init_servo_canvas(self):
        """Dessine boîtier + pivot + palonnier + jauge circulaire."""
        if not self._servo_canvas:
            return
        c = self._servo_canvas
        w = int(c['width']);  h = int(c['height'])
        cx, cy = w // 2, h // 2
        self._cx, self._cy = cx, cy
        self._r = min(w, h) // 3  # longueur du palonnier (~1/3 de la plus petite dimension)

        # Boîtier
        c.create_rectangle(cx - 140, cy - 50, cx + 140, cy + 50,
                           fill="#333333", outline="#111111")
        # Pivot
        c.create_oval(cx - 12, cy - 12, cx + 12, cy + 12,
                      fill="#bbbbbb", outline="#666666")
        # Palonnier
        self._horn_item = c.create_line(cx, cy, cx + self._r, cy,
                                        width=6, capstyle="round")

        # Jauge
        self._draw_gauge()

    def _draw_gauge(self):
        if not self._servo_canvas:
            return
        c = self._servo_canvas
        cx, cy = self._cx, self._cy
        if cx is None:
            return

        # Nettoyage ancien
        if self._gauge["ring"]:
            try: c.delete(self._gauge["ring"])
            except Exception: pass
        for it in self._gauge["ticks"]:
            try: c.delete(it)
            except Exception: pass
        for it in self._gauge["labels"]:
            try: c.delete(it)
            except Exception: pass
        if self._gauge["active_arc"]:
            try: c.delete(self._gauge["active_arc"])
            except Exception: pass
        self._gauge["ticks"] = []
        self._gauge["labels"] = []

        # Rayons
        r_tick = int(self._r) + 22
        r_ring = r_tick + 10
        self._gauge["radius"] = r_ring

        # Cercle extérieur (anneau)
        self._gauge["ring"] = c.create_oval(cx - r_ring, cy - r_ring, cx + r_ring, cy + r_ring,
                                            outline="#cfcfcf", width=2)

        # Ticks -180..+180 (0° à droite, sens trigonométrique)
        for deg in range(-180, 181, 10):
            rad = math.radians(deg)
            # longs tous les 30°, courts sinon
            long = (deg % 30 == 0)
            r1 = r_tick - (14 if long else 7)
            r2 = r_tick + (2 if long else 0)

            x1 = cx + r1 * math.cos(rad)
            y1 = cy - r1 * math.sin(rad)
            x2 = cx + r2 * math.cos(rad)
            y2 = cy - r2 * math.sin(rad)
            it = c.create_line(x1, y1, x2, y2, width=2)
            self._gauge["ticks"].append(it)

            if long:
                # Label tous les 30°
                rl = r_tick + 18
                xt = cx + rl * math.cos(rad)
                yt = cy - rl * math.sin(rad)
                lab = c.create_text(xt, yt, text=str(deg), font=("TkDefaultFont", 9))
                self._gauge["labels"].append(lab)

        # Arc de plage active (min..max)
        self._redraw_gauge_active_range()

    def _redraw_gauge_active_range(self):
        """Dessine l'arc [min,max] en surbrillance sur la jauge."""
        if not self._servo_canvas or self._cx is None:
            return
        c = self._servo_canvas
        cx, cy = self._cx, self._cy
        r_ring = self._gauge["radius"] or (int(self._r) + 32)

        # Nettoyer ancien arc
        if self._gauge["active_arc"]:
            try: c.delete(self._gauge["active_arc"])
            except Exception: pass

        mn = float(self.limits["min"])
        mx = float(self.limits["max"])
        # Tkinter: start=angle° à partir de 3h, extent=angle CCW positif
        start = mn
        extent = mx - mn
        bbox = (cx - r_ring, cy - r_ring, cx + r_ring, cy + r_ring)
        self._gauge["active_arc"] = c.create_arc(
            *bbox, start=start, extent=extent, outline="#2e7d32", width=4, style="arc"
        )

    def _update_servo_canvas(self, angle_abs_deg: float):
        """Met à jour l'orientation du palonnier selon l'angle ABSOLU (°)."""
        if not (self._servo_canvas and self._horn_item and self._cx is not None and self._r is not None):
            return
        rad = math.radians(angle_abs_deg)
        x2 = self._cx + self._r * math.cos(rad)
        y2 = self._cy - self._r * math.sin(rad)  # Y écran vers le bas
        self._servo_canvas.coords(self._horn_item, self._cx, self._cy, x2, y2)

    # --------- Monitoring (lecture périodique) ---------
    def _start_monitor(self):
        if not self._monitor_active:
            self._monitor_active = True
            self._monitor_loop()

    def _stop_monitor(self):
        self._monitor_active = False
        if self._monitor_job:
            try:
                self.after_cancel(self._monitor_job)
            except Exception:
                pass
            self._monitor_job = None

    def _monitor_loop(self):
        """Lit la position présente et met à jour labels + canvas, ~8 Hz."""
        if not self._monitor_active:
            return

        mid = int(self.selected_id.get())
        ok = mid > 0 and port_is_connected(self.port_var.get().strip())
        if not ok:
            self.present_abs_var.set("—")
            self.present_log_var.set("—")
            self._monitor_job = self.after(250, self._monitor_loop)
            return

        try:
            with self._bus().session() as bus:
                pos_abs = float(bus.get_present_position([mid])[0])
            offset = 0.0
            if str(mid) in self.offsets:
                offset = float(self.offsets[str(mid)])
            elif mid in self.offsets:
                offset = float(self.offsets[mid])
            pos_log = pos_abs - offset

            self.present_abs_var.set(f"{pos_abs:6.2f}°")
            self.present_log_var.set(f"{pos_log:6.2f}°")
            self._update_servo_canvas(pos_abs)

        except Exception:
            self.present_abs_var.set("—")
            self.present_log_var.set("—")

        self._monitor_job = self.after(120, self._monitor_loop)

    # --------- Accès bus ---------
    def _bus(self) -> MotorBus:
        return MotorBus(self.port_var.get(), self.baud_var.get())

    # --------- Actions ---------
    def scan(self):
        port = self.port_var.get().strip()
        baud = int(self.baud_var.get())

        if not port_is_connected(port):
            ports = available_ports()
            msg = f"Aucun adaptateur série détecté sur « {port or '(non défini)'} ».\n"
            msg += "Ports détectés : " + (", ".join(ports) if ports else "aucun")
            messagebox.showwarning("Port non détecté", msg)
            self.status.set("Port absent : branche l’USB puis « ↻ » et « Scanner ».")  # noqa
            self.set_controls_enabled(False)
            self._stop_monitor()
            return

        self.start_busy(f"Scan en cours… (port {port}, {baud} bauds)")
        try:
            with self._bus().session() as bus:
                ids = bus.scan(range(1, 60))

            if not ids:
                self.selected_id.set(0)
                self.stop_busy(f"Aucun moteur détecté (port {port}, {baud} bauds).")
                self._stop_monitor()
                return

            if len(ids) > 1:
                self.selected_id.set(0)
                self.stop_busy(f"Plusieurs servos détectés : {ids}. Branchez-en un seul.")
                messagebox.showwarning("Plusieurs servos détectés",
                                       f"IDs trouvés : {ids}\nBranche un seul servo pour la config initiale.")
                self._stop_monitor()
                return

            self.selected_id.set(ids[0])
            self.stop_busy(f"Servo détecté: ID {ids[0]} (port {port}, {baud} bauds)")
            self.set_controls_enabled(True)
            self._start_monitor()

        except serial.SerialException as e:
            self.selected_id.set(0)
            self.stop_busy(f"Erreur série sur {port}.")
            messagebox.showerror("Connexion série",
                                 f"Impossible d’ouvrir {port} (occupé, introuvable ou droits insuffisants).\n\n{e}")
            self._stop_monitor()
        except Exception as e:
            self.selected_id.set(0)
            self.stop_busy("Erreur pendant le scan.")
            messagebox.showerror("Scan", str(e))
            self._stop_monitor()

    def center_and_apply(self):
        self.goal_var.set(0.0)
        self.move_to()

    def move_to(self):
        mid = int(self.selected_id.get())
        mn, mx = self.limits["min"], self.limits["max"]
        goal = max(mn, min(mx, float(self.goal_var.get())))

        # Offset logiciel (stocké en degrés absolus mesurés lors du zéro logiciel)
        offset = 0.0
        if str(mid) in self.offsets:
            offset = float(self.offsets[str(mid)])
        elif mid in self.offsets:
            offset = float(self.offsets[mid])

        abs_goal = goal + offset  # on AJOUTE l’offset

        try:
            with self._bus().session() as bus:
                bus.set_goal_position({mid: abs_goal})
            self.status.set(f"ID {mid} → {goal:.0f}° (abs {abs_goal:.0f}°, offset {offset:+.2f}°)")
        except Exception as e:
            messagebox.showerror("Mouvement", str(e))

    def verify_zero_abs(self):
        """Envoie 0° ABSOLU (sans offset logiciel). Sert à vérifier le zéro matériel."""
        mid = int(self.selected_id.get())
        try:
            with self._bus().session() as bus:
                bus.set_goal_position({mid: 0.0})
            self.status.set(f"Vérification 0° ABS envoyée (ID {mid}).")
        except Exception as e:
            messagebox.showerror("Vérifier 0°", str(e))

    def torque_off(self):
        mid = int(self.selected_id.get())
        try:
            with self._bus().session() as bus:
                bus.torque_off(mid)
            # geler les commandes de mouvement
            self.auto_apply.set(False)
            save_ui_prefs(self._current_prefs())
            for w in (self.goal_scale, self.btn_move, self.btn_center, self.chk_auto):
                try:
                    w.configure(state='disabled')
                except Exception:
                    try:
                        w.state(['disabled'])
                    except Exception:
                        pass
            self.status.set(f"Couple désactivé (ID {mid}).")
        except Exception as e:
            messagebox.showerror("Désactiver couple", str(e))

    def torque_on(self):
        mid = int(self.selected_id.get())
        try:
            with self._bus().session() as bus:
                bus.torque_on(mid)
            for w in (self.goal_scale, self.btn_move, self.btn_center, self.chk_auto):
                try:
                    w.configure(state='normal')
                except Exception:
                    try:
                        w.state(['!disabled'])
                    except Exception:
                        pass
            self.status.set(f"Couple réactivé (ID {mid}).")
        except Exception as e:
            messagebox.showerror("Réactiver couple", str(e))

    def set_zero_soft(self):
        mid = int(self.selected_id.get())
        try:
            with self._bus().session() as bus:
                pos = bus.get_present_position([mid])[0]
            self.offsets = set_zero(self.offsets, mid, pos)  # stocke l'angle absolu mesuré
            save_offsets(self.offsets)
            self.goal_var.set(0.0)  # recentre le slider (sans envoyer)
            self.status.set(f"Zéro logiciel défini pour ID {mid} (pos={pos:.2f}°). Curseur centré.")
        except Exception as e:
            messagebox.showerror("Zéro logiciel", str(e))

    def set_zero_hardware(self) -> bool:
        """
        Zéro matériel SANS déplacer le servo.
        Valide par lecture seule ; en cas d'échec, applique un zéro logiciel équivalent.
        Retourne True si OK, False sinon.
        """
        mid = int(self.selected_id.get())
        if not messagebox.askyesno(
            "Zéro matériel (EEPROM)",
            "Cette opération écrit en EEPROM dans le servo et est persistante.\n"
            "Définir la position ACTUELLE comme zéro matériel ?"
        ):
            return False

        TOL = 2.0  # tolérance en degrés
        try:
            with self._bus().session() as bus:
                # Position actuelle (référence choisie)
                pos_before = float(bus.get_present_position([mid])[0])

                # Tentative zéro matériel
                try:
                    bus.set_hardware_zero_to_current(mid)
                except NotImplementedError:
                    # Fallback immédiat : zéro logiciel équivalent
                    self.offsets[str(mid)] = pos_before
                    save_offsets(self.offsets)
                    self.goal_var.set(0.0)
                    self.status.set(
                        f"Zéro matériel non supporté → Zéro logiciel appliqué (offset={pos_before:.2f}°)."
                    )
                    self.bell()
                    messagebox.showwarning(
                        "Zéro matériel non supporté",
                        "La bibliothèque ne gère pas le zéro matériel.\n"
                        "J’ai appliqué un zéro logiciel équivalent pour conserver le centrage."
                    )
                    return False

                # Stabilisation puis lecture seule (pas de mouvement envoyé)
                time.sleep(0.4)
                reads = []
                for _ in range(3):
                    reads.append(float(bus.get_present_position([mid])[0]))
                    time.sleep(0.08)
                pos_after = sum(reads) / len(reads)

            delta = abs(pos_after - 0.0)
            if delta <= TOL:
                # Succès matériel : offset logiciel = 0
                self.offsets[str(mid)] = 0.0
                save_offsets(self.offsets)
                self.goal_var.set(0.0)
                msg = f"Zéro matériel OK — pos lue = {pos_after:.2f}° (≤ {TOL}°). Offset logiciel remis à 0. Aucun mouvement envoyé."
                self.status.set(msg)
                messagebox.showinfo("Zéro matériel confirmé", msg)
                return True
            else:
                # Échec matériel : fallback logiciel (offset = pos_before)
                self.offsets[str(mid)] = pos_before
                save_offsets(self.offsets)
                self.goal_var.set(0.0)
                msg = (
                    "Zéro matériel non effectif.\n\n"
                    f"Lecture après écriture = {pos_after:.2f}° (écart {delta:.2f}° > {TOL}°).\n"
                    f"Un zéro logiciel équivalent a été appliqué (offset = {pos_before:.2f}°)."
                )
                self.status.set("Zéro matériel non effectif → Zéro logiciel appliqué (voir détails).")
                self.bell()
                messagebox.showwarning("Zéro matériel non effectif", msg)
                return False

        except Exception as e:
            messagebox.showerror("Zéro matériel", str(e))
            return False

    def apply_new_id(self):
        mid = int(self.selected_id.get()); new_id = int(self.new_id_var.get())
        try:
            with self._bus().session() as bus:
                bus.change_id({mid: new_id})
            self.status.set(f"ID {mid} → {new_id}. Re-scan recommandé.")
            self.set_controls_enabled(False)
        except Exception as e:
            messagebox.showerror("Changer ID", str(e))

    def apply_new_baud(self):
        mid = int(self.selected_id.get()); new_baud = int(self.new_baud_var.get())
        try:
            with self._bus().session() as bus:
                bus.change_baudrate({mid: new_baud})
            self.status.set(f"Baud de l’ID {mid} → {new_baud}. Mets à jour Baud puis re-scan.")
            self.set_controls_enabled(False)
            # la mise à jour visuelle du champ principal Baud sauvegardera les prefs via <FocusOut>
        except Exception as e:
            messagebox.showerror("Changer Baud", str(e))

    def apply_preset_open_duck(self):
        mid = int(self.selected_id.get())
        if mid <= 0:
            messagebox.showwarning("Aucun servo", "Scannez d'abord (un seul servo connecté).")
            return
        p = self.preset
        try:
            with self._bus().session() as bus:
                bus.set_lock({mid: int(p["lock"])})
                bus.set_mode({mid: int(p["mode"])})
                bus.set_maximum_acceleration({mid: int(p["max_accel"])})
                bus.set_acceleration({mid: int(p["accel"])})
                bus.set_pid(mid, p=int(p["P"]), i=int(p["I"]), d=int(p["D"]))
            self.status.set(
                f"Preset appliqué sur ID {mid} (lock={p['lock']}, mode={p['mode']}, "
                f"max_accel={p['max_accel']}, accel={p['accel']}, PID={p['P']}/{p['I']}/{p['D']})."
            )
            messagebox.showinfo("Preset appliqué", "Réglages appliqués.")
        except Exception as e:
            messagebox.showerror("Preset Open Duck", str(e))

    def open_docs(self):
        """Import paresseux pour ne charger la doc qu’à la demande."""
        try:
            from .docs_sts3215 import open_window as _open_docs
        except Exception as e:
            messagebox.showerror("Aide STS3215", f"Impossible de charger l’aide :\n{e}")
            return
        try:
            _open_docs(self)
        except Exception as e:
            messagebox.showerror("Aide STS3215", str(e))
