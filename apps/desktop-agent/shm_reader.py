"""
ACC Apex Engineer Pro - Lector de Memoria Compartida a 333 Hz (shm_reader.py)
Usa exclusivamente Win32 OpenFileMappingW(FILE_MAP_READ) + MapViewOfFile(FILE_MAP_READ)
para NUNCA crear ni bloquear los bloques de memoria antes que Assetto Corsa Competizione:
  - Local\\acpmf_physics
  - Local\\acpmf_graphics
  - Local\\acpmf_static
Esto evita por completo el crash EXCEPTION_ACCESS_VIOLATION (0x0000000000000000) en AC Physics Thread
cuando el agente se abre antes de iniciar carrera en ACC.
"""

from __future__ import annotations

import ctypes
from ctypes import c_float, c_int32, c_size_t, c_void_p, c_wchar, wintypes
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
    Jamás llama a CreateFileMappingW, evitando dejar secciones PAGE_READONLY que hagan
    crachear al hilo AC Physics Thread al iniciar sesión.
    """
    h_map = kernel32.OpenFileMappingW(FILE_MAP_READ, False, map_name)
    if not h_map:
        return None

    size = ctypes.sizeof(struct_cls)
    p_view = kernel32.MapViewOfFile(h_map, FILE_MAP_READ, 0, 0, size)
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
    brake_temps: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    wheel_slip: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    suspension_travel: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    ride_height: List[float] = field(default_factory=lambda: [0.0, 0.0])
    yaw_rate: float = 0.0
    tc_in_action: bool = False
    abs_in_action: bool = False
    air_temp: float = 0.0
    road_temp: float = 0.0
    brake_bias: float = 0.0

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
            "brake_temps": [round(x, 0) for x in self.brake_temps],
            "wheel_slip": [round(x, 2) for x in self.wheel_slip],
            "suspension_travel": [round(x, 4) for x in self.suspension_travel],
            "ride_height": [round(x, 1) for x in self.ride_height],
            "yaw_rate": round(self.yaw_rate, 3),
            "tc_in_action": self.tc_in_action,
            "abs_in_action": self.abs_in_action,
            "air_temp": round(self.air_temp, 1),
            "road_temp": round(self.road_temp, 1),
            "brake_bias": round(self.brake_bias, 1),
        }


class ACCSharedMemoryReader:
    """
    Lee Local\\acpmf_physics, Local\\acpmf_graphics y Local\\acpmf_static usando OpenFileMappingW.
    Nunca pre-crea los segmentos de memoria en modo lectura, permitiendo abrir el agente
    antes o después de Assetto Corsa Competizione sin provocar fallos en AC Physics Thread.
    """

    def __init__(self) -> None:
        self._last_packet_id: int = -1
        self._stale_count: int = 0

    def close(self) -> None:
        pass

    def read_sample(self) -> Optional[TelemetrySample]:
        phys = read_existing_shm_struct("Local\\acpmf_physics", SPageFilePhysics)
        if phys is None:
            return None

        gfx = read_existing_shm_struct("Local\\acpmf_graphics", SPageFileGraphic)
        if gfx is None:
            return None

        stc = read_existing_shm_struct("Local\\acpmf_static", SPageFileStatic)
        if stc is None:
            return None

        try:
            # AC_OFF = 0: El juego no está en sesión activa
            if phys.packetId <= 0 or gfx.status <= 0:
                return None

            # Verificar que el paquete de física esté avanzando (juego en pista, no congelado)
            if phys.packetId == self._last_packet_id:
                self._stale_count += 1
                if self._stale_count > 1000:  # ~3 segundos sin paquetes nuevos
                    return None
            else:
                self._stale_count = 0
                self._last_packet_id = int(phys.packetId)

            ride_front = float(phys.rideHeight[0])
            ride_rear = float(phys.rideHeight[1])
            if 0.0 < ride_front < 1.0:
                ride_front *= 1000.0
            if 0.0 < ride_rear < 1.0:
                ride_rear *= 1000.0

            car_model = (stc.carModel or "").strip()
            track_name = (stc.track or "").strip()
            if not car_model or not track_name:
                return None

            return TelemetrySample(
                timestamp=time.time(),
                is_live_acc=True,
                packet_id=int(phys.packetId),
                car_model=car_model,
                track_name=track_name,
                driver_name=(stc.playerNick or stc.playerName or "Piloto").strip(),
                completed_laps=int(gfx.completedLaps),
                current_lap_ms=max(0, int(gfx.iCurrentTime)),
                last_lap_ms=max(0, int(gfx.iLastTime)),
                best_lap_ms=max(0, int(gfx.iBestTime)),
                sector_index=int(gfx.currentSectorIndex),
                last_sector_ms=max(0, int(gfx.lastSectorTime)),
                normalized_pos=max(0.0, min(1.0, float(gfx.normalizedCarPosition))),
                is_in_pit=bool(gfx.isInPit),
                is_in_pit_lane=bool(gfx.isInPitLane),
                speed_kmh=max(0.0, float(phys.speedKmh)),
                rpms=max(0, int(phys.rpms)),
                max_rpm=max(7500, int(stc.maxRpm or phys.currentMaxRpm or 8000)),
                gear=int(phys.gear) - 1,
                gas=max(0.0, min(1.0, float(phys.gas))),
                brake=max(0.0, min(1.0, float(phys.brake))),
                steer_angle=float(phys.steerAngle),
                fuel=max(0.0, float(phys.fuel)),
                tyre_pressures=[float(phys.wheelsPressure[i]) for i in range(4)],
                tyre_temps_core=[float(phys.tyreCoreTemperature[i]) for i in range(4)],
                brake_temps=[float(phys.brakeTemp[i]) for i in range(4)],
                wheel_slip=[float(phys.wheelSlip[i]) for i in range(4)],
                suspension_travel=[float(phys.suspensionTravel[i]) for i in range(4)],
                ride_height=[ride_front, ride_rear],
                yaw_rate=float(phys.localAngularVel[1]),
                tc_in_action=bool(phys.tcinAction),
                abs_in_action=bool(phys.absInAction),
                air_temp=float(phys.airTemp),
                road_temp=float(phys.roadTemp),
                brake_bias=float(
                    phys.brakeBias * 100.0 if phys.brakeBias <= 1.0 else phys.brakeBias
                ),
            )
        except Exception:
            return None
