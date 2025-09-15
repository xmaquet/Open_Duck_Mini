from contextlib import contextmanager

try:
    # Branche pypot avec support STS3215 (cf. dépendance)
    from pypot.feetech.io import FeetechIO as _BusIO  # type: ignore
except Exception:  # fallback si le chemin évolue
    from pypot.feetech import FeetechIO as _BusIO  # type: ignore


class MotorBus:
    """Fine couche d’abstraction du bus Feetech via pypot."""
    def __init__(self, port: str, baudrate: int = 1_000_000, timeout: float = 0.2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._io = None

    def open(self):
        if self._io is None:
            self._io = _BusIO(self.port, baudrate=self.baudrate, timeout=self.timeout)

    def close(self):
        if self._io is not None:
            self._io.close()
            self._io = None

    @contextmanager
    def session(self):
        self.open()
        try:
            yield self
        finally:
            self.close()

    # Découverte
    def scan(self, id_range=range(1, 253)):
        return self._io.scan(id_range)

    # Lecture/écriture basiques
    def get_present_position(self, ids):
        return self._io.get_present_position(ids)

    def set_goal_position(self, goals: dict):
        # goals = {id: angle_deg}
        self._io.set_goal_position(goals)

    # Paramétrage
    def change_id(self, mapping: dict):
        # mapping = {old_id: new_id}
        self._io.change_id(mapping)

    def change_baudrate(self, mapping: dict):
        # mapping = {id: new_baud}
        self._io.change_baudrate(mapping)

