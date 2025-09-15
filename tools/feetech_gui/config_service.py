import json
from pathlib import Path

CONFIG_PATH = Path("./motor_calibration.json")

def load_offsets() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}

def save_offsets(offsets: dict):
    CONFIG_PATH.write_text(json.dumps(offsets, indent=2))

def set_zero(offsets: dict, motor_id: int, present_deg: float):
    # zero logiciel : offset = -position courante
    offsets[str(motor_id)] = -float(present_deg)
    return offsets

def apply_offset(raw_positions: dict, offsets: dict) -> dict:
    out = {}
    for mid, pos in raw_positions.items():
        out[mid] = pos + float(offsets.get(str(mid), 0.0))
    return out

