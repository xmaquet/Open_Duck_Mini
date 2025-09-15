# Paramètres par défaut
DEFAULT_PORT = "COM3"
DEFAULT_BAUD = 1_000_000

# Limites (défauts)
LIMITS_DEFAULTS = {
    "min": -180,
    "max": 180,
    "tick": 90,
    "res": 1,
}

# Preset Open Duck (défauts)
PRESET_DEFAULT = {
    "P": 32,
    "I": 0,
    "D": 0,
    "mode": 0,       # 0 = position
    "max_accel": 0,
    "accel": 0,
    "lock": 0,       # 0 = déverrouillé
}
