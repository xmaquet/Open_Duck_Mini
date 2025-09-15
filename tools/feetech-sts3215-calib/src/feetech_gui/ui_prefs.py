from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

CFG_PATH = Path.cwd() / "ui_config.json"

DEFAULTS: Dict[str, Any] = {
    "port": "COM3",
    "baud": 1_000_000,
    "auto_apply": False,
    "limits": {"min": -180, "max": 180, "tick": 90, "res": 1},
    "preset": {"P": 32, "I": 0, "D": 0, "mode": 0, "max_accel": 0, "accel": 0, "lock": 0},
}

def _deep_merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst

def load_ui_prefs() -> Dict[str, Any]:
    data = DEFAULTS.copy()
    try:
        if CFG_PATH.exists():
            with CFG_PATH.open("r", encoding="utf-8") as f:
                file_data = json.load(f)
            _deep_merge(data, file_data or {})
    except Exception:
        pass
    return data

def save_ui_prefs(prefs: Dict[str, Any]) -> None:
    # fusionne avec DEFAULTS pour garantir les clés
    to_save = _deep_merge(DEFAULTS.copy(), prefs.copy())
    try:
        with CFG_PATH.open("w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
