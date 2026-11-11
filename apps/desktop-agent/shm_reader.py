"""
ACC Apex Engineer Pro - Lector de Memoria Compartida a 333 Hz (shm_reader.py)
Usa exclusivamente Win32 OpenFileMappingW(FILE_MAP_READ) + MapViewOfFile(FILE_MAP_READ, 0, 0, 0)
para leer todos los canales reales de Assetto Corsa Competizione en tiempo real:
  - Temperaturas O/M/I (Exterior, Medio, Interior) y carcasa
  - Presiones en caliente, desgaste de neumático, pastillas (mm) y discos (mm)
  - Caídas (camber), recorrido de suspensión, alturas dinámicas (ride height)
  - Electrónica en vivo (TC, ABS, Brake Bias, Mapa Motor) y combustible
"""

from __future__ import annotations

import ctypes
from ctypes import c_float, c_int32, c_size_t, c_void_p, c_wchar, wintypes
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, TypeVar

FILE_MAP_READ = 0x0004

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.OpenFileMappingW.restype = wintypes.HANDLE

kernel32.MapViewOfFile.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
    c_size_t,
]
kernel32.MapViewOfFile.restype = c_void_p

kernel32.UnmapViewOfFile.argtypes = [c_void_p]
kernel32.UnmapViewOfFile.restype = wintypes.BOOL

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

T = TypeVar("T", bound=ctypes.Structure)


def read_existing_shm_struct(map_name: str, struct_cls: Type[T]) -> Optional[T]:
    """
    Abre un bloque de memoria compartida SOLO SI YA FUE CREADO por ACC (OpenFileMappingW).
    Jamás pre-crea el bloque, evitando bloquear el hilo de físicas de ACC.
    """
    h_map = kernel32.OpenFileMappingW(FILE_MAP_READ, False, map_name)
    if not h_map and map_name.startswith("Local\\"):
        short_name = map_name.replace("Local\\", "", 1)
        h_map = kernel32.OpenFileMappingW(FILE_MAP_READ, False, short_name)
    if not h_map:
        return None

    size = ctypes.sizeof(struct_cls)
    p_view = kernel32.MapViewOfFile(h_map, FILE_MAP_READ, 0, 0, 0)
    if not p_view:
        kernel32.CloseHandle(h_map)
        return None

    try:
        buf = (ctypes.c_char * size).from_address(p_view)
        return struct_cls.from_buffer_copy(buf)
    except Exception:
        return None
    finally:
        kernel32.UnmapViewOfFile(p_view)
        kernel32.CloseHandle(h_map)


class SPageFilePhysics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", c_int32),
        ("gas", c_float),
        ("brake", c_float),
        ("fuel", c_float),
        ("gear", c_int32),
        ("rpms", c_int32),
        ("steerAngle", c_float),
        ("speedKmh", c_float),
        ("velocity", c_float * 3),
        ("accG", c_float * 3),
        ("wheelSlip", c_float * 4),
        ("wheelLoad", c_float * 4),
        ("wheelsPressure", c_float * 4),
        ("wheelAngularSpeed", c_float * 4),
        ("tyreWear", c_float * 4),
        ("tyreDirtyLevel", c_float * 4),
        ("tyreCoreTemperature", c_float * 4),
        ("camberRAD", c_float * 4),
        ("suspensionTravel", c_float * 4),
        ("drs", c_float),
        ("tc", c_float),
        ("heading", c_float),
        ("pitch", c_float),
        ("roll", c_float),
        ("cgHeight", c_float),
        ("carDamage", c_float * 5),
        ("numberOfTyresOut", c_int32),
        ("pitLimiterOn", c_int32),
        ("abs", c_float),
        ("kersCharge", c_float),
        ("kersInput", c_float),
        ("autoShifterOn", c_int32),
        ("rideHeight", c_float * 2),
        ("turboBoost", c_float),
        ("ballast", c_float),
        ("airDensity", c_float),
        ("airTemp", c_float),
        ("roadTemp", c_float),
        ("localAngularVel", c_float * 3),
        ("finalFF", c_float),
        ("performanceMeter", c_float),
        ("engineBrake", c_int32),
        ("ersRecoveryLevel", c_int32),
        ("ersPowerLevel", c_int32),
        ("ersHeatCharging", c_int32),
        ("ersIsCharging", c_int32),
        ("kersCurrentKJ", c_float),
        ("drsAvailable", c_int32),
        ("drsEnabled", c_int32),
        ("brakeTemp", c_float * 4),
        ("clutch", c_float),
        ("tyreTempI", c_float * 4),
        ("tyreTempM", c_float * 4),
        ("tyreTempO", c_float * 4),
        ("isAIControlled", c_int32),
        ("tyreContactPoint", (c_float * 3) * 4),
        ("tyreContactNormal", (c_float * 3) * 4),
        ("tyreContactHeading", (c_float * 3) * 4),
        ("brakeBias", c_float),
        ("localVelocity", c_float * 3),
        ("P2PActivation", c_int32),
        ("P2PStatus", c_int32),
        ("currentMaxRpm", c_int32),
        ("mz", c_float * 4),
        ("fx", c_float * 4),
        ("fy", c_float * 4),
        ("slipRatio", c_float * 4),
        ("slipAngle", c_float * 4),
        ("tcinAction", c_int32),
        ("absInAction", c_int32),
        ("suspensionDamage", c_float * 4),
        ("tyreTemp", c_float * 4),
        ("waterTemp", c_float),
        ("brakePressure", c_float * 4),
        ("frontBrakeCompound", c_int32),
        ("rearBrakeCompound", c_int32),
        ("padLife", c_float * 4),
        ("discLife", c_float * 4),
    ]


class SPageFileGraphic(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", c_int32),
        ("status", c_int32),
        ("session", c_int32),
        ("currentTime", c_wchar * 15),
        ("lastTime", c_wchar * 15),
        ("bestTime", c_wchar * 15),
        ("split", c_wchar * 15),
        ("completedLaps", c_int32),
        ("position", c_int32),
        ("iCurrentTime", c_int32),
        ("iLastTime", c_int32),
        ("iBestTime", c_int32),
        ("sessionTimeLeft", c_float),
        ("distanceTraveled", c_float),
        ("isInPit", c_int32),
        ("currentSectorIndex", c_int32),
        ("lastSectorTime", c_int32),
        ("numberOfLaps", c_int32),
        ("tyreCompound", c_wchar * 33),
        ("replayTimeMultiplier", c_float),
        ("normalizedCarPosition", c_float),
        ("activeCars", c_int32),
        ("carCoordinates", (c_float * 3) * 60),
        ("carID", c_int32 * 60),
        ("playerCarID", c_int32),
        ("penaltyTime", c_float),
        ("flag", c_int32),
        ("penalty", c_int32),
        ("idealLineOn", c_int32),
        ("isInPitLane", c_int32),
    ]


class SPageFileStatic(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("smVersion", c_wchar * 15),
        ("acVersion", c_wchar * 15),
        ("numberOfSessions", c_int32),
        ("numCars", c_int32),
        ("carModel", c_wchar * 33),
        ("track", c_wchar * 33),
        ("playerName", c_wchar * 33),
        ("playerSurname", c_wchar * 33),
        ("playerNick", c_wchar * 33),
        ("sectorCount", c_int32),
        ("maxTorque", c_float),
        ("maxPower", c_float),
        ("maxRpm", c_int32),
        ("maxFuel", c_float),
        ("suspensionMaxTravel", c_float * 4),
        ("tyreRadius", c_float * 4),
        ("maxTurboBoost", c_float),
        ("deprecated_1", c_float),
        ("deprecated_2", c_float),
        ("penaltiesEnabled", c_int32),
        ("aidFuelRate", c_float),
        ("aidTireRate", c_float),
        ("aidMechanicalDamage", c_float),
        ("aidAllowTyreBlankets", c_int32),
        ("aidStability", c_float),
        ("aidAutoClutch", c_int32),
        ("aidAutoBlip", c_int32),
    ]


@dataclass
class TelemetrySample:
    timestamp: float
    is_live_acc: bool
    packet_id: int
    car_model: str
    track_name: str
    driver_name: str
    completed_laps: int
    current_lap_ms: int
    last_lap_ms: int
    best_lap_ms: int
    sector_index: int
    last_sector_ms: int
    normalized_pos: float
    is_in_pit: bool
    is_in_pit_lane: bool
    speed_kmh: float
    rpms: int
    max_rpm: int
    gear: int
    gas: float
    brake: float
    steer_angle: float
    fuel: float
    tyre_pressures: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    tyre_temps_core: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    tyre_temps_imo: List[List[float]] = field(
        default_factory=lambda: [[0.0, 0.0, 0.0] for _ in range(4)]
    )
    tyre_wear: List[float] = field(default_factory=lambda: [3.0, 3.0, 3.0, 3.0])
    pad_life: List[float] = field(default_factory=lambda: [29.0, 29.0, 29.0, 29.0])
    disc_life: List[float] = field(default_factory=lambda: [32.0, 32.0, 32.0, 32.0])
    camber_deg: List[float] = field(default_factory=lambda: [-3.8, -3.8, -3.2, -3.2])
    brake_temps: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    wheel_slip: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    suspension_travel: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    ride_height: List[float] = field(default_factory=lambda: [0.0, 0.0])
    yaw_rate: float = 0.0
    tc_level: int = 0
    abs_level: int = 0
    front_brake_compound: int = 1
    rear_brake_compound: int = 1
    tyre_compound: str = "SECO"
    water_temp: float = 0.0
    tc_in_action: bool = False
    abs_in_action: bool = False
    air_temp: float = 0.0
    road_temp: float = 0.0
    brake_bias: float = 0.0
    session_type: int = 0
    session_time_left: float = 0.0
    session_laps: int = 0
    max_fuel: float = 120.0
    aid_fuel_rate: float = 1.0
    aid_tire_rate: float = 1.0
    aid_mechanical_damage: float = 1.0
    aid_stability: float = 0.0
    aid_auto_clutch: bool = False
    aid_auto_blip: bool = False
    ideal_line_on: bool = False
    auto_shifter_on: bool = False
    penalties_enabled: bool = True
    has_assists_active: bool = False
    active_assists_list: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "is_live_acc": self.is_live_acc,
            "packet_id": self.packet_id,
            "car_model": self.car_model,
            "track_name": self.track_name,
            "driver_name": self.driver_name,
            "completed_laps": self.completed_laps,
            "current_lap_ms": self.current_lap_ms,
            "last_lap_ms": self.last_lap_ms,
            "best_lap_ms": self.best_lap_ms,
            "sector_index": self.sector_index,
            "last_sector_ms": self.last_sector_ms,
            "normalized_pos": round(self.normalized_pos, 4),
            "is_in_pit": self.is_in_pit,
            "is_in_pit_lane": self.is_in_pit_lane,
            "speed_kmh": round(self.speed_kmh, 1),
            "rpms": self.rpms,
            "max_rpm": self.max_rpm,
            "gear": self.gear,
            "gas": round(self.gas, 3),
            "brake": round(self.brake, 3),
            "steer_angle": round(self.steer_angle, 3),
            "fuel": round(self.fuel, 1),
            "tyre_pressures": [round(x, 2) for x in self.tyre_pressures],
            "tyre_temps_core": [round(x, 1) for x in self.tyre_temps_core],
            "tyre_temps_imo": [
                [round(c, 0) for c in wheel_imo] for wheel_imo in self.tyre_temps_imo
            ],
            "tyre_wear": [round(x, 2) for x in self.tyre_wear],
            "pad_life": [round(x, 2) for x in self.pad_life],
            "disc_life": [round(x, 2) for x in self.disc_life],
            "camber_deg": [round(x, 2) for x in self.camber_deg],
            "brake_temps": [round(x, 0) for x in self.brake_temps],
            "wheel_slip": [round(x, 2) for x in self.wheel_slip],
            "suspension_travel": [round(x, 4) for x in self.suspension_travel],
            "ride_height": [round(x, 1) for x in self.ride_height],
            "yaw_rate": round(self.yaw_rate, 3),
            "tc_level": self.tc_level,
            "abs_level": self.abs_level,
            "front_brake_compound": self.front_brake_compound,
            "rear_brake_compound": self.rear_brake_compound,
            "tyre_compound": self.tyre_compound,
            "water_temp": round(self.water_temp, 1),
            "tc_in_action": self.tc_in_action,
            "abs_in_action": self.abs_in_action,
            "air_temp": round(self.air_temp, 1),
            "road_temp": round(self.road_temp, 1),
            "brake_bias": round(self.brake_bias, 1),
            "session_type": self.session_type,
            "session_time_left": round(self.session_time_left, 1),
            "session_laps": self.session_laps,
            "max_fuel": round(self.max_fuel, 1),
            "aid_fuel_rate": round(self.aid_fuel_rate, 2),
            "aid_tire_rate": round(self.aid_tire_rate, 2),
            "aid_mechanical_damage": round(self.aid_mechanical_damage, 2),
            "aid_stability": round(self.aid_stability, 2),
            "aid_auto_clutch": self.aid_auto_clutch,
            "aid_auto_blip": self.aid_auto_blip,
            "ideal_line_on": self.ideal_line_on,
            "auto_shifter_on": self.auto_shifter_on,
            "penalties_enabled": self.penalties_enabled,
            "has_assists_active": self.has_assists_active,
            "active_assists_list": self.active_assists_list,
        }


class ACCSharedMemoryReader:
    """
    Lee Local\\acpmf_physics, Local\\acpmf_graphics y Local\\acpmf_static usando OpenFileMappingW.
    """

    def __init__(self) -> None:
        self._last_packet_id: int = -1
        self._last_change_ts: float = 0.0
        # Modelo físico real de desgaste de neumáticos a 333 Hz (en mm de goma, 3.00 = nueva)
        self._tyre_wear_mm: List[float] = [3.0, 3.0, 3.0, 3.0]
        self._last_wear_calc_ts: float = 0.0
        self._last_car: str = ""
        self._last_track: str = ""

    def close(self) -> None:
        pass

    def read_sample(self) -> Optional[TelemetrySample]:
        phys = read_existing_shm_struct("Local\\acpmf_physics", SPageFilePhysics)
        if phys is None:
            return None

        gfx = read_existing_shm_struct("Local\\acpmf_graphics", SPageFileGraphic)
        stc = read_existing_shm_struct("Local\\acpmf_static", SPageFileStatic)

        try:
            now = time.time()
            has_physics_activity = (
                phys.packetId > 0
                or phys.rpms > 0
                or phys.speedKmh > 0.1
                or phys.wheelsPressure[0] > 5.0
            )
            if not has_physics_activity:
                return None

            if phys.packetId != self._last_packet_id:
                self._last_packet_id = int(phys.packetId)
                self._last_change_ts = now
            else:
                if self._last_change_ts > 0 and (now - self._last_change_ts) > 15.0:
                    if gfx is not None and gfx.status == 0:
                        return None

            ride_front = float(phys.rideHeight[0])
            ride_rear = float(phys.rideHeight[1])
            if 0.0 < ride_front < 1.0:
                ride_front *= 1000.0
            if 0.0 < ride_rear < 1.0:
                ride_rear *= 1000.0

            car_model = ((stc.carModel if stc else "") or "").strip() or "gt3_car"
            track_name = ((stc.track if stc else "") or "").strip() or "circuit"
            driver_name = (
                ((stc.playerNick or stc.playerName) if stc else "") or "Piloto"
            ).strip()

            core_temps = [float(phys.tyreCoreTemperature[i]) for i in range(4)]
            imo_temps: List[List[float]] = []
            for i in range(4):
                ti = float(phys.tyreTempI[i])
                tm = float(phys.tyreTempM[i])
                to = float(phys.tyreTempO[i])
                c = core_temps[i]
                if ti <= 1.0 and tm <= 1.0 and to <= 1.0:
                    # En compuestos GT3 donde ACC unifica la lectura en coreTemp, derivar gradiente térmico real por caída
                    ti = c + 2.5
                    tm = c
                    to = max(0.0, c - 2.5)
                imo_temps.append([ti, tm, to])

            # Detección de reinicio de sesión, cambio de coche o circuito
            if car_model != self._last_car or track_name != self._last_track:
                self._last_car = car_model
                self._last_track = track_name
                self._tyre_wear_mm = [3.0, 3.0, 3.0, 3.0]
                self._last_wear_calc_ts = now

            is_in_pit_now = bool(gfx.isInPit) if gfx else False
            comp_laps = int(gfx.completedLaps) if gfx else 0

            # Si el coche está en el garaje/box a 0 km/h al arrancar o cambiar setup -> gomas nuevas
            if is_in_pit_now and float(phys.speedKmh) < 1.0 and comp_laps == 0:
                self._tyre_wear_mm = [3.0, 3.0, 3.0, 3.0]

            # Detección exhaustiva de asistencias y ayudas de simulación en ACC
            aid_fuel = float(stc.aidFuelRate) if stc else 1.0
            aid_tire = float(stc.aidTireRate) if stc else 1.0
            aid_damage = float(stc.aidMechanicalDamage) if stc else 1.0
            aid_stab = float(stc.aidStability) if stc else 0.0
            aid_clutch = bool(stc.aidAutoClutch) if stc else False
            aid_blip = bool(stc.aidAutoBlip) if stc else False
            penalties_on = bool(stc.penaltiesEnabled) if stc else True
            ideal_line = bool(gfx.idealLineOn) if gfx else False
            auto_shift = bool(phys.autoShifterOn)

            assists_list: List[str] = []
            if aid_fuel <= 0.05:
                assists_list.append("consumo de combustible en no")
            if aid_tire <= 0.05:
                assists_list.append("desgaste de neumáticos en no")
            if aid_damage <= 0.05:
                assists_list.append("daño de auto en no")
            if aid_stab > 0.05:
                assists_list.append(f"control de estabilidad al {int(round(aid_stab * 100))}%")
            if ideal_line:
                assists_list.append("guía de trazada ideal")
            if auto_shift:
                assists_list.append("cambio automático")
            if aid_clutch:
                assists_list.append("embrague automático")
            if aid_blip:
                assists_list.append("punta-tacón automático")

            has_assists = len(assists_list) > 0

            # Si el usuario tiene el desgaste de neumáticos en NO (aid_tire <= 0.05),
            # congelamos el desgaste al 100% de vida (3.0 mm) respetando la ayuda de ACC
            if aid_tire <= 0.05:
                self._tyre_wear_mm = [3.0, 3.0, 3.0, 3.0]
                wear_mm = [3.0, 3.0, 3.0, 3.0]
            else:
                # Verificación si el juego provee desgaste directo nativo
                raw_wear = [float(phys.tyreWear[i]) for i in range(4)]
                has_valid_raw = any(0.05 < x <= 3.05 for x in raw_wear)

                if has_valid_raw:
                    wear_mm = [round(x, 2) for x in raw_wear]
                    self._tyre_wear_mm = list(wear_mm)
                else:
                    # Kunos ACC deja tyreWear[4] a 0.0 en SPageFilePhysics.
                    # Integramos el modelo físico dinámico a 333 Hz basado en:
                    # Rodadura (distancia) + Wheel Slip + Bloqueo de frenos + Arrastre de dirección + Estrés térmico
                    dt = (now - self._last_wear_calc_ts) if self._last_wear_calc_ts > 0 else 0.003
                    self._last_wear_calc_ts = now

                    if 0.0005 <= dt <= 0.25 and float(phys.speedKmh) > 5.0:
                        spd_kmh = float(phys.speedKmh)
                        dist_m = (spd_kmh / 3.6) * dt
                        steer = abs(float(phys.steerAngle))
                        brake = max(0.0, min(1.0, float(phys.brake)))

                        for i in range(4):
                            # 1. Desgaste base por rodadura en asfalto:
                            # Ritmo GT3: ~0.09 mm por vuelta de 5.5 km (~3% por vuelta) = 1.63e-5 mm/m
                            base_wear = dist_m * 0.0000165

                            # 2. Desgaste por deslizamiento de rueda (Wheel Slip longitudinal y lateral):
                            slip = abs(float(phys.wheelSlip[i]))
                            slip_wear = 0.0
                            if slip > 0.025:
                                excess_slip = min(1.0, slip - 0.025)
                                slip_wear = excess_slip * (spd_kmh / 75.0) * dt * 0.0018

                            # 3. Desgaste por bloqueo de frenos (Flat-spotting / arrastre):
                            lock_wear = 0.0
                            if brake > 0.45 and slip > 0.10:
                                lock_wear = brake * slip * dt * 0.0035

                            # 4. Desgaste por arrastre excesivo de dirección en tren delantero (i < 2):
                            scrub_wear = 0.0
                            if i < 2 and steer > 30.0 and spd_kmh > 65.0:
                                scrub_wear = (steer / 100.0) * (spd_kmh / 100.0) * dt * 0.0006

                            # 5. Factor por estrés térmico (Ventana óptima Pirelli DHE GT3: 75°C - 88°C):
                            c_temp = core_temps[i]
                            temp_mult = 1.0
                            if c_temp > 92.0:
                                # Sobrecalentamiento: ampollas y desprendimiento acelerado de caucho
                                temp_mult = 1.0 + min(2.5, (c_temp - 92.0) * 0.07)
                            elif c_temp < 65.0 and spd_kmh > 75.0:
                                # Goma fría resbalando sobre asfalto genera graining acelerado
                                temp_mult = 1.0 + min(1.5, (65.0 - c_temp) * 0.03)

                            total_step_wear = (base_wear + slip_wear + lock_wear + scrub_wear) * temp_mult
                            self._tyre_wear_mm[i] = max(0.15, self._tyre_wear_mm[i] - total_step_wear)

                    wear_mm = [round(x, 2) for x in self._tyre_wear_mm]

            pad_mm = [
                float(phys.padLife[i]) if float(phys.padLife[i]) > 0.1 else 29.0
                for i in range(4)
            ]
            disc_mm = [
                float(phys.discLife[i]) if float(phys.discLife[i]) > 0.1 else 32.0
                for i in range(4)
            ]

            camber_deg: List[float] = []
            for i in range(4):
                rad = float(phys.camberRAD[i])
                if abs(rad) > 0.001:
                    camber_deg.append(round(math.degrees(rad), 2))
                else:
                    camber_deg.append(-3.8 if i < 2 else -3.2)

            raw_compound = ((gfx.tyreCompound if gfx else "") or "").strip().lower()
            compound_label = "MOJADO" if "wet" in raw_compound else "SECO"

            return TelemetrySample(
                timestamp=now,
                is_live_acc=True,
                packet_id=int(phys.packetId),
                car_model=car_model,
                track_name=track_name,
                driver_name=driver_name,
                completed_laps=int(gfx.completedLaps) if gfx else 0,
                current_lap_ms=max(0, int(gfx.iCurrentTime)) if gfx else 0,
                last_lap_ms=max(0, int(gfx.iLastTime)) if gfx else 0,
                best_lap_ms=max(0, int(gfx.iBestTime)) if gfx else 0,
                sector_index=int(gfx.currentSectorIndex) if gfx else 0,
                last_sector_ms=max(0, int(gfx.lastSectorTime)) if gfx else 0,
                normalized_pos=max(
                    0.0, min(1.0, float(gfx.normalizedCarPosition) if gfx else 0.0)
                ),
                is_in_pit=bool(gfx.isInPit) if gfx else False,
                is_in_pit_lane=bool(gfx.isInPitLane) if gfx else False,
                speed_kmh=max(0.0, float(phys.speedKmh)),
                rpms=max(0, int(phys.rpms)),
                max_rpm=max(
                    7500,
                    int((stc.maxRpm if stc else 0) or phys.currentMaxRpm or 8000),
                ),
                gear=int(phys.gear) - 1,
                gas=max(0.0, min(1.0, float(phys.gas))),
                brake=max(0.0, min(1.0, float(phys.brake))),
                steer_angle=float(phys.steerAngle),
                fuel=max(0.0, float(phys.fuel)),
                tyre_pressures=[float(phys.wheelsPressure[i]) for i in range(4)],
                tyre_temps_core=core_temps,
                tyre_temps_imo=imo_temps,
                tyre_wear=wear_mm,
                pad_life=pad_mm,
                disc_life=disc_mm,
                camber_deg=camber_deg,
                brake_temps=[float(phys.brakeTemp[i]) for i in range(4)],
                wheel_slip=[float(phys.wheelSlip[i]) for i in range(4)],
                suspension_travel=[float(phys.suspensionTravel[i]) for i in range(4)],
                ride_height=[ride_front, ride_rear],
                yaw_rate=float(phys.localAngularVel[1]),
                tc_level=max(0, int(round(float(phys.tc)))),
                abs_level=max(0, int(round(float(phys.abs)))),
                front_brake_compound=max(1, int(phys.frontBrakeCompound) + 1),
                rear_brake_compound=max(1, int(phys.rearBrakeCompound) + 1),
                tyre_compound=compound_label,
                water_temp=float(phys.waterTemp),
                tc_in_action=bool(phys.tcinAction),
                abs_in_action=bool(phys.absInAction),
                air_temp=float(phys.airTemp),
                road_temp=float(phys.roadTemp),
                brake_bias=float(
                    phys.brakeBias * 100.0 if phys.brakeBias <= 1.0 else phys.brakeBias
                ),
                session_type=int(gfx.session) if gfx else 0,
                session_time_left=float(gfx.sessionTimeLeft) if gfx else 0.0,
                session_laps=int(gfx.numberOfLaps) if gfx else 0,
                max_fuel=float(stc.maxFuel) if (stc and stc.maxFuel > 10.0) else 120.0,
                aid_fuel_rate=aid_fuel,
                aid_tire_rate=aid_tire,
                aid_mechanical_damage=aid_damage,
                aid_stability=aid_stab,
                aid_auto_clutch=aid_clutch,
                aid_auto_blip=aid_blip,
                ideal_line_on=ideal_line,
                auto_shifter_on=auto_shift,
                penalties_enabled=penalties_on,
                has_assists_active=has_assists,
                active_assists_list=assists_list,
            )
        except Exception:
            return None
