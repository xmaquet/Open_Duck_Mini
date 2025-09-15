from contextlib import contextmanager
from pypot.feetech.sts3215_io import FeetechSTS3215IO as _BusIO

class MotorBus:
    """Abstraction simple du bus Feetech via pypot."""
    def __init__(self, port: str, baudrate: int = 1_000_000, timeout: float = 0.2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._io = None

    def open(self):
        if self._io is None:
            try:
                self._io = _BusIO(self.port, baudrate=self.baudrate, timeout=self.timeout)
            except TypeError:
                self._io = _BusIO(self.port, self.baudrate)

    def close(self):
        if self._io is not None:
            try:
                self._io.close()
            finally:
                self._io = None

    @contextmanager
    def session(self):
        self.open()
        try:
            yield self
        finally:
            self.close()

    # --- API de base ---
    def scan(self, id_range=range(1, 253)):
        return self._io.scan(id_range)

    def get_present_position(self, ids):
        return self._io.get_present_position(ids)

    def set_goal_position(self, goals: dict):
        self._io.set_goal_position(goals)

    def change_id(self, mapping: dict):
        self._io.change_id(mapping)

    def change_baudrate(self, mapping: dict):
        self._io.change_baudrate(mapping)

    # --- Réglages avancés (exposés par FeetechSTS3215IO) ---
    def set_lock(self, mapping: dict):
        self._io.set_lock(mapping)

    def set_mode(self, mapping: dict):
        # 0 = position (comme dans le script)
        self._io.set_mode(mapping)

    def set_maximum_acceleration(self, mapping: dict):
        self._io.set_maximum_acceleration(mapping)

    def set_acceleration(self, mapping: dict):
        self._io.set_acceleration(mapping)

    def set_pid(self, motor_id: int, p: int, i: int, d: int):
        self._io.set_P_coefficient({motor_id: int(p)})
        self._io.set_I_coefficient({motor_id: int(i)})
        self._io.set_D_coefficient({motor_id: int(d)})

    # --- Torque control (robuste) ---
    def torque_off(self, motor_id: int):
        self.__torque_switch(motor_id, enable=False)

    def torque_on(self, motor_id: int):
        self.__torque_switch(motor_id, enable=True)

    def __torque_switch(self, motor_id: int, enable: bool):
        """
        Essaie d'abord l'API DxlIO (enable_torque/disable_torque) qui attend une LISTE d'IDs,
        puis retombe sur les variantes set_torque_enable(...).
        """
        last_exc = None
        if enable:
            # 1) API standard
            func = getattr(self._io, "enable_torque", None)
            if func:
                try:
                    func([motor_id])           # <-- liste d'IDs
                    return
                except Exception as e:
                    last_exc = e
            # 2) Fallback: set_torque_enable = 1 / True
            f = getattr(self._io, "set_torque_enable", None)
            if f:
                for args in (
                    ({motor_id: 1},),
                    ({motor_id: True},),
                    ([motor_id], [1]),
                    ([motor_id], [True]),
                    (motor_id, 1),
                    (motor_id, True),
                ):
                    try:
                        f(*args); return
                    except Exception as e:
                        last_exc = e
        else:
            # 1) API standard
            func = getattr(self._io, "disable_torque", None)
            if func:
                try:
                    func([motor_id])           # <-- liste d'IDs
                    return
                except Exception as e:
                    last_exc = e
            # 2) Fallback: set_torque_enable = 0 / False
            f = getattr(self._io, "set_torque_enable", None)
            if f:
                for args in (
                    ({motor_id: 0},),
                    ({motor_id: False},),
                    ([motor_id], [0]),
                    ([motor_id], [False]),
                    (motor_id, 0),
                    (motor_id, False),
                ):
                    try:
                        f(*args); return
                    except Exception as e:
                        last_exc = e

        raise NotImplementedError(
            f"Contrôle du couple non supporté par cette version de pypot. Dernière erreur: {last_exc}"
        )


    # --- Zéro matériel (EEPROM) ---
    def set_hardware_zero_to_current(self, motor_id: int):
        """
        Définit la position actuelle comme 'zéro matériel' dans le servo (écriture EEPROM).
        Cette méthode essaie plusieurs noms/signatures possibles exposés par pypot.feetech.sts3215_io.
        """
        # 1) lire la position actuelle en degrés
        pos = float(self.get_present_position([motor_id])[0])
        delta = -pos  # on veut que présent + delta = 0°

        # 2) tenter différentes API possibles (selon la version)
        #    On essaie avec une valeur (delta) puis, si une API 'here' existe, sans valeur.
        import inspect

        candidates_with_value = [
            "set_origin_offset",
            "set_angle_offset",
            "set_home_offset",
            "set_zero_offset",
        ]
        candidates_here = [
            "set_zero_here",
            "calibrate_zero_here",
            "set_home_here",
            "set_origin_here",
        ]

        # helper pour essayer plusieurs signatures (dict, paire, listes)
        def _try_call(name, *args):
            func = getattr(self._io, name, None)
            if func is None:
                return False
            try:
                func(*args)  # tentative directe
                return True
            except TypeError:
                # variantes courantes
                try:
                    # dict {id: value}
                    func({motor_id: delta})
                    return True
                except Exception:
                    pass
                try:
                    # listes parallèles
                    func([motor_id], [delta])
                    return True
                except Exception:
                    pass
                try:
                    # (id, value)
                    func(motor_id, delta)
                    return True
                except Exception:
                    pass
            except Exception:
                pass
            return False

        # a) méthodes qui prennent une valeur (offset en degrés)
        for name in candidates_with_value:
            if _try_call(name, {motor_id: delta}):
                return

        # b) méthodes 'here' (utilisent la position courante)
        for name in candidates_here:
            func = getattr(self._io, name, None)
            if func is None:
                continue
            try:
                func([motor_id])  # certains prennent une liste d'IDs
                return
            except TypeError:
                try:
                    func(motor_id)  # ou un seul ID
                    return
                except Exception:
                    pass
            except Exception:
                pass

        # c) tentative générique via introspection : chercher une méthode avec 'zero' ou 'home' dans le nom
        for name, obj in inspect.getmembers(self._io, inspect.ismethod):
            low = name.lower()
            if any(k in low for k in ("zero", "home", "offset", "origin")):
                # essayer sans argument puis avec différentes signatures
                if _try_call(name):
                    return

        raise NotImplementedError(
            "Zéro matériel non supporté par cette version de pypot.feetech.sts3215_io."
        )
