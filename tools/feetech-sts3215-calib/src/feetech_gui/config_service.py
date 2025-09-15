# src/feetech_gui/config_service.py
import json
from pathlib import Path

CALIB_PATH = Path.cwd() / "motor_calibration.json"

def load_offsets() -> dict:
    try:
        if CALIB_PATH.exists():
            return json.loads(CALIB_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        pass
    return {}

def save_offsets(offsets: dict) -> None:
    try:
        CALIB_PATH.write_text(json.dumps(offsets, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def set_zero(offsets: dict, motor_id: int, current_abs_deg: float) -> dict:
    """
    Enregistre l'offset logiciel comme l'ANGLE ABSOLU mesuré (en degrés)
    au moment du zéro. Spécification:
    - goal_ui (°) -> goal_abs (°) = goal_ui + offset[motor_id]
    - Donc si goal_ui=0°, on renvoie exactement la position mesurée.
    """
    offsets[str(motor_id)] = float(current_abs_deg)
    return offsets
