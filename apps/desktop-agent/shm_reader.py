"""
ACC Apex Engineer Pro - Lector de Memoria Compartida a 333 Hz (shm_reader.py)
Lee exclusivamente en modo LECTURA (ACCESS_READ):
  - Local\\acpmf_physics
  - Local\\acpmf_graphics
  - Local\\acpmf_static
Incluye simulador físico GT3 de respaldo cuando ACC no está en ejecución para pruebas en vivo.
"""

from __future__ import annotations

import ctypes
from ctypes import c_float, c_int32, c_wchar
import math
import mmap
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    tyre_pressures: List[float] = field(default_factory=lambda: [26.8, 26.8, 26.8, 26.8])
    tyre_temps_core: List[float] = field(default_factory=lambda: [82.0, 82.0, 80.0, 80.0])
    brake_temps: List[float] = field(default_factory=lambda: [490.0, 490.0, 460.0, 460.0])
    wheel_slip: List[float] = field(default_factory=lambda: [0.2, 0.2, 0.2, 0.2])
    suspension_travel: List[float] = field(default_factory=lambda: [0.02, 0.02, 0.02, 0.02])
    ride_height: List[float] = field(default_factory=lambda: [54.0, 68.0])
    yaw_rate: float = 0.0
    tc_in_action: bool = False
    abs_in_action: bool = False
    air_temp: float = 22.0
    road_temp: float = 29.0
    brake_bias: float = 56.5

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
    Lee Local\\acpmf_physics, Local\\acpmf_graphics y Local\\acpmf_static a 333 Hz (cada 3 ms).
    NUNCA abre archivos del juego en modo escritura ni modifica configuraciones de controles.
    """

    def __init__(self, enable_demo_when_idle: bool = True) -> None:
        self.enable_demo_when_idle = enable_demo_when_idle
        self._mm_physics: Optional[mmap.mmap] = None
        self._mm_graphics: Optional[mmap.mmap] = None
        self._mm_static: Optional[mmap.mmap] = None
        self._sim_start = time.perf_counter()
        self._sim_packet = 0
        self._sim_laps = 1
        self._sim_last_lap_ms = 138420
        self._sim_best_lap_ms = 137890
        self._last_sim_norm = 0.0

    def _open_shared_memory(self) -> bool:
        try:
            if self._mm_physics is None:
                self._mm_physics = mmap.mmap(
                    -1,
                    ctypes.sizeof(SPageFilePhysics),
                    "Local\\acpmf_physics",
                    access=mmap.ACCESS_READ,
                )
            if self._mm_graphics is None:
                self._mm_graphics = mmap.mmap(
                    -1,
                    ctypes.sizeof(SPageFileGraphic),
                    "Local\\acpmf_graphics",
                    access=mmap.ACCESS_READ,
                )
            if self._mm_static is None:
                self._mm_static = mmap.mmap(
                    -1,
                    ctypes.sizeof(SPageFileStatic),
                    "Local\\acpmf_static",
                    access=mmap.ACCESS_READ,
                )
            return True
        except Exception:
            self.close()
            return False

    def close(self) -> None:
        for mm in (self._mm_physics, self._mm_graphics, self._mm_static):
            if mm is not None:
                try:
                    mm.close()
                except Exception:
                    pass
        self._mm_physics = None
        self._mm_graphics = None
        self._mm_static = None

    def read_sample(self) -> Optional[TelemetrySample]:
        if self._open_shared_memory():
            try:
                assert self._mm_physics and self._mm_graphics and self._mm_static
                self._mm_physics.seek(0)
                phys = SPageFilePhysics.from_buffer_copy(
                    self._mm_physics.read(ctypes.sizeof(SPageFilePhysics))
                )
                self._mm_graphics.seek(0)
                gfx = SPageFileGraphic.from_buffer_copy(
                    self._mm_graphics.read(ctypes.sizeof(SPageFileGraphic))
                )
                self._mm_static.seek(0)
                stc = SPageFileStatic.from_buffer_copy(
                    self._mm_static.read(ctypes.sizeof(SPageFileStatic))
                )

                # Si packetId > 0 y status != 0 (AC_OFF = 0), ACC está transmitiendo física real
                if phys.packetId > 0 and gfx.status > 0:
                    ride_front = float(phys.rideHeight[0])
                    ride_rear = float(phys.rideHeight[1])
                    # ACC entrega rideHeight en metros (ej: 0.054 -> 54 mm)
                    if 0.0 < ride_front < 1.0:
                        ride_front *= 1000.0
                    if 0.0 < ride_rear < 1.0:
                        ride_rear *= 1000.0

                    return TelemetrySample(
                        timestamp=time.time(),
                        is_live_acc=True,
                        packet_id=int(phys.packetId),
                        car_model=(stc.carModel or "mclaren_720s_gt3_evo").strip(),
                        track_name=(stc.track or "spa").strip(),
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
                        gear=int(phys.gear) - 1,  # ACC: 0=R, 1=N, 2=1st
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
                        air_temp=float(phys.airTemp or 22.0),
                        road_temp=float(phys.roadTemp or 28.0),
                        brake_bias=float(phys.brakeBias * 100.0 if phys.brakeBias <= 1.0 else phys.brakeBias),
                    )
            except Exception:
                self.close()

        if not self.enable_demo_when_idle:
            return None

        return self._generate_synthetic_sample()

    def _generate_synthetic_sample(self) -> TelemetrySample:
        """
        Genera una telemetría sintética de Spa-Francorchamps a 333 Hz cuando ACC está cerrado,
        para permitir validar en vivo el Dashboard, el Detector de Errores y el Auto-Inyector.
        """
        now = time.perf_counter()
        elapsed = now - self._sim_start
        self._sim_packet += 1

        lap_duration_s = 45.0  # Vuelta acelerada de demostración cada 45s
        norm_pos = (elapsed % lap_duration_s) / lap_duration_s
        if norm_pos < self._last_sim_norm:
            self._sim_laps += 1
            self._sim_last_lap_ms = 137650 + int(math.sin(self._sim_laps) * 650)
            self._sim_best_lap_ms = min(self._sim_best_lap_ms, self._sim_last_lap_ms)
        self._last_sim_norm = norm_pos

        # Perfil de curvas principales de Spa (La Source, Eau Rouge, Les Combes, Pouhon, Bus Stop)
        corner_zones = [0.08, 0.18, 0.34, 0.56, 0.72, 0.91]
        corner_intensity = 0.0
        corner_sign = 1.0
        for idx, cz in enumerate(corner_zones):
            dist = abs(norm_pos - cz)
            if dist < 0.045:
                local_factor = 1.0 - (dist / 0.045)
                if local_factor > corner_intensity:
                    corner_intensity = local_factor
                    corner_sign = 1.0 if idx % 2 == 0 else -1.0

        brake = max(0.0, min(1.0, (corner_intensity - 0.15) * 1.45)) if corner_intensity > 0.25 else 0.0
        gas = 1.0 - min(1.0, corner_intensity * 1.15)
        speed = 278.0 - (corner_intensity * 168.0) + 8.0 * math.sin(norm_pos * math.tau * 3)
        gear = max(1, min(6, int(speed // 43) + 1))
        rpms = int(4900 + ((speed % 43) / 43.0) * 2950)
        steer = corner_sign * (corner_intensity ** 1.2) * 0.68

        # Simular leve sobrepresión delantera izquierda y compresión en Eau Rouge (norm_pos ~ 0.18)
        eau_rouge = abs(norm_pos - 0.18) < 0.018
        ride_f = 39.5 if eau_rouge else (52.0 - brake * 9.5)
        ride_r = 56.0 if eau_rouge else (67.0 + brake * 5.0)

        slip_front = 0.35 + (1.28 if corner_intensity > 0.78 else corner_intensity * 0.7)
        slip_rear = 0.30 + (1.35 if (corner_intensity > 0.55 and gas > 0.65) else corner_intensity * 0.5)

        return TelemetrySample(
            timestamp=time.time(),
            is_live_acc=False,
            packet_id=self._sim_packet,
            car_model="mclaren_720s_gt3_evo",
            track_name="spa",
            driver_name="Demo Telemetría 333Hz",
            completed_laps=self._sim_laps,
            current_lap_ms=int(norm_pos * 137800),
            last_lap_ms=self._sim_last_lap_ms,
            best_lap_ms=self._sim_best_lap_ms,
            sector_index=0 if norm_pos < 0.33 else (1 if norm_pos < 0.66 else 2),
            last_sector_ms=44820,
            normalized_pos=norm_pos,
            is_in_pit=False,
            is_in_pit_lane=False,
            speed_kmh=speed,
            rpms=rpms,
            max_rpm=8000,
            gear=gear,
            gas=gas,
            brake=brake,
            steer_angle=steer,
            fuel=max(12.0, 62.0 - self._sim_laps * 2.8 - norm_pos * 2.8),
            tyre_pressures=[
                27.35 + 0.15 * math.sin(elapsed * 0.2),
                27.10 + 0.10 * math.cos(elapsed * 0.2),
                26.45 + 0.10 * math.sin(elapsed * 0.15),
                26.55 + 0.10 * math.cos(elapsed * 0.15),
            ],
            tyre_temps_core=[88.5, 85.0, 79.5, 80.2],
            brake_temps=[
                545.0 + brake * 120.0,
                535.0 + brake * 115.0,
                465.0 + brake * 85.0,
                460.0 + brake * 85.0,
            ],
            wheel_slip=[slip_front, slip_front * 0.92, slip_rear, slip_rear * 0.95],
            suspension_travel=[0.032, 0.030, 0.028, 0.027],
            ride_height=[ride_f, ride_r],
            yaw_rate=steer * 0.55,
            tc_in_action=bool(slip_rear > 1.25 and gas > 0.5),
            abs_in_action=bool(brake > 0.88),
            air_temp=23.0,
            road_temp=31.0,
            brake_bias=56.2,
        )

