# src/feetech_gui/docs_sts3215.py
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

def _add_tab(nb: ttk.Notebook, title: str, text: str):
    frame = ttk.Frame(nb)
    nb.add(frame, text=title)
    st = scrolledtext.ScrolledText(frame, wrap="word", height=24)
    st.pack(fill="both", expand=True, padx=10, pady=10)
    st.insert("1.0", text.strip() + "\n")
    st.configure(state="disabled")
    return frame

def open_window(parent: tk.Tk | tk.Toplevel):
    """Ouvre une fenêtre Toplevel avec un Notebook d'explications STS3215."""
    win = tk.Toplevel(parent)
    win.title("Aide STS3215 — fonctionnement & réglages")
    win.geometry("900x650")
    try:
        win.minsize(720, 520)
    except Exception:
        pass

    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True)

    # --- Contenus (courts, pratiques) ---
    _add_tab(nb, "Vue d’ensemble", """
Le Feetech STS3215 est un servo bus série (TTL half-duplex) « intelligent » :
• Moteur DC + réducteur + capteur de position
• Microcontrôleur interne avec registres RAM/EEPROM
• Communication par une seule ligne Signal (TTL), plus V+ et GND partagés

Notions clés :
• ID unique par servo (configuration initiale)
• Baudrate partagé entre PC et servo (par défaut 1 000 000)
• 0° = repère interne du servo (peut être déplacé via zéro matériel)
""")

    _add_tab(nb, "Bus & Registres", """
Bus série (TTL half-duplex) :
• Signal, V+, GND (masse commune entre alim et interface USB-TTL)
• Ping/scan : on interroge les IDs 1..N pour trouver les servos présents

Registres :
• EEPROM : ID, baudrate, offset de zéro matériel, paramètres par défaut (persistants)
• RAM : goal position, present position, torque enable, etc. (volatiles)

Bonnes pratiques :
• Éviter d'écrire en boucle dans l'EEPROM (ID/baud/zéro matériel)
• N'effectuer la configuration qu'avec un seul servo connecté au bus
""")

    _add_tab(nb, "Modes & PID", """
Modes courants :
• Position (joint) : vous envoyez un angle cible en degrés
• Vitesse (wheel) selon modèle/config (moins utilisé en calibration)

Boucle interne :
• Le servo lit « present position », calcule l’erreur vers « goal position »
• PID interne : P (raideur), I (biais), D (amortissement)
• Limites d'accélération (max_accel/accel) pour adoucir les trajectoires

Conseils :
• Débuter avec P moyen (ex. 32), I=0, D=0 ; n’ajuster D qu’en cas d’oscillation
• Vérifier l’alimentation : une tension faible crée du « mou » perceptible
""")

    _add_tab(nb, "Zéro (matériel vs logiciel)", """
Zéro matériel (EEPROM) :
• Écrit un offset dans la mémoire du servo → 0° « absolu » correspond
  mécaniquement à la position où vous l’avez défini
• Effet persistant, indépendant du PC/outils
• Votre outil propose un « zéro matériel sans bouger » + vérification par lecture
  et fallback automatique en zéro logiciel si non effectif

Zéro logiciel (dans l’outil) :
• On mémorise la position absolue mesurée et on l’ADDITIONNE à la consigne :
  goal_abs = goal_logique + offset_logiciel
• Réversible, aucune écriture EEPROM, idéal pour la mise au point rapide
""")

    _add_tab(nb, "Procédure de calibration", """
1) Désactiver couple → positionner mécaniquement la référence à la main
2) Zéro matériel OU zéro logiciel :
   • Matériel : le servo mémorise cette position comme 0° absolu
   • Logiciel : l’outil mémorise l’offset et recentre le slider
3) Réactiver couple → Centrer (0°) → vérifier le retour capteur ~= 0°
4) Ajuster P (et éventuellement D) si la tenue est molle / oscillante
5) Définir les limites min/max utiles (butées mécaniques, montage), sauvegarder

Tests utiles :
• Envoyer ±60° puis Centrer → doit revenir exactement au repère choisi
• Vérifier « Présent abs » vs « logique » dans l’onglet Retour capteur
""")

    _add_tab(nb, "Dépannage rapide", """
• Rien détecté au scan : mauvais port COM, mauvais baudrate, port occupé
• Mouvements décalés : repère de zéro incohérent → refaire zéro (matériel ou logiciel)
• Écart constant (ex. +10°) : signe d’offset → refaire zéro logiciel propre
• Servo « tremble » : réduire P, augmenter légèrement D, vérifier l’alimentation
• Parfois bouge après zéro matériel : normal, le repère interne a changé
""")

    # Focus sur le premier onglet
    nb.select(0)
    win.transient(parent)
    win.grab_set()  # modal « douce »
    win.focus_set()
    return win
