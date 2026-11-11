"""
ACC Apex Engineer Pro - Calculador de Estrategia de Combustible y Consumo por Vuelta (fuel_strategy.py)
Mide el consumo real de combustible por vuelta a 333 Hz, calcula la carga óptima para
Carrera, Vuelta Rápida (Hotlap) o Clasificación con margen de seguridad dinámico,
y genera la comunicación por radio en boxes antes de que el piloto salga a pista.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
from shm_reader import TelemetrySample


@dataclass
class FuelStrategyResult:
    session_name: str          # "Carrera", "Clasificación", "Vuelta Rápida", "Entrenamientos"
    session_type: int          # 0..3
    avg_fuel_per_lap: float    # Litros por vuelta promedio medidos
    estimated_laps: int        # Vueltas requeridas para la sesión
    safety_liters: float       # Margen de seguridad añadido
    recommended_fuel_l: int    # Litros recomendados en el tanque (entero para el setup de ACC)
    current_fuel_l: float      # Combustible actual en el tanque
    speech_text: str           # Mensaje de radio listo para ser emitido por voz de Álvaro


# Consumo medio estimado por circuito para GT3 (litros por vuelta) como base inicial
DEFAULT_GT3_FUEL_PER_LAP: Dict[str, float] = {
    "spa": 3.45,
    "monza": 2.95,
    "silverstone": 3.15,
    "nurburgring": 2.80,
    "brands_hatch": 2.10,
    "misano": 2.50,
    "paul_ricard": 3.10,
    "zandvoort": 2.45,
    "barcelona": 2.85,
    "hungaroring": 2.55,
    "kyalami": 2.90,
    "suzuka": 3.10,
    "mount_panorama": 3.35,
    "laguna_seca": 2.25,
    "imola": 2.75,
    "donington": 2.40,
    "oulton_park": 2.30,
    "snetterton": 2.40,
    "cota": 3.20,
    "indianapolis": 2.40,
    "watkins_glen": 2.65,
    "valencia": 2.35,
    "red_bull_ring": 2.30,
}
DEFAULT_FALLBACK_FUEL = 3.10


class FuelStrategyCalculator:
    def __init__(self) -> None:
        # Historial de consumos medidos por coche y circuito: "carmodel:track" -> [l1, l2, ...]
        self._fuel_history: Dict[str, List[float]] = {}
        # Control del anuncio en boxes
        self._pit_announced: bool = False
        self._in_pit_since: float = 0.0
        self._last_announced_ts: float = 0.0
        self._last_announced_target_fuel: int = -1

    def record_lap_consumption(self, car_model: str, track_name: str, fuel_used: float) -> float:
        """
        Registra el consumo de una vuelta completada y calcula el promedio ponderado.
        Filtra anomalías como paradas en boxes o vueltas incompletas.
        """
        if fuel_used < 0.6 or fuel_used > 14.0:
            return self.get_avg_fuel(car_model, track_name)

        key = f"{car_model.lower()}:{track_name.lower()}"
        if key not in self._fuel_history:
            self._fuel_history[key] = []

        history = self._fuel_history[key]
        history.append(fuel_used)
        if len(history) > 10:
            history.pop(0)

        return round(sum(history) / len(history), 2)

    def get_avg_fuel(self, car_model: str, track_name: str) -> float:
        """Devuelve el consumo medio medido del piloto o el consumo base del circuito."""
        key = f"{car_model.lower()}:{track_name.lower()}"
        history = self._fuel_history.get(key)
        if history:
            return round(sum(history) / len(history), 2)

        track_clean = track_name.lower().replace(" ", "_").replace("-", "_")
        for k, v in DEFAULT_GT3_FUEL_PER_LAP.items():
            if k in track_clean:
                return v
        return DEFAULT_FALLBACK_FUEL

    def check_and_evaluate_pit_strategy(
        self, sample: TelemetrySample, best_lap_ms: int = 0, last_lap_ms: int = 0
    ) -> Optional[FuelStrategyResult]:
        """
        Evalúa si el coche está en boxes antes de salir a pista y genera la estrategia.
        Dispara el cálculo exactamente UNA vez por visita a boxes, con tiempo para que
        el piloto ajuste el combustible en el menú de setup.
        """
        now = time.time()
        in_pit = sample.is_in_pit or (sample.is_in_pit_lane and sample.speed_kmh < 12.0)

        # Si el coche está rodando en pista a alta velocidad, reseteamos el disparador
        if not in_pit and sample.speed_kmh > 45.0:
            self._pit_announced = False
            self._in_pit_since = 0.0
            return None

        # Si entra o está en boxes
        if in_pit:
            if self._in_pit_since == 0.0:
                self._in_pit_since = now

            # Esperar 1.8 segundos detenido en el box para asegurar que esté en el garaje
            if (now - self._in_pit_since) >= 1.8 and not self._pit_announced:
                if (now - self._last_announced_ts) > 30.0:  # No repetir en menos de 30s
                    strat = self._calculate_strategy(sample, best_lap_ms, last_lap_ms)
                    self._pit_announced = True
                    self._last_announced_ts = now
                    self._last_announced_target_fuel = strat.recommended_fuel_l
                    return strat

        return None

    def _calculate_strategy(
        self, sample: TelemetrySample, best_lap_ms: int = 0, last_lap_ms: int = 0
    ) -> FuelStrategyResult:
        session_type = sample.session_type
        avg_fuel = self.get_avg_fuel(sample.car_model, sample.track_name)
        tank_max = max(100.0, sample.max_fuel if sample.max_fuel > 10.0 else 120.0)

        # Determinar tiempo de vuelta de referencia (en segundos)
        ref_lap_ms = best_lap_ms if best_lap_ms > 45000 else (last_lap_ms if last_lap_ms > 45000 else 135000)
        lap_sec = ref_lap_ms / 1000.0

        # Identificar tipo de sesión:
        # ACC: 0=PRACTICE, 1=QUALIFY, 2=RACE, 3=HOTLAP
        if session_type == 3 or (sample.session_time_left <= 0.0 and sample.session_laps <= 0 and session_type != 2):
            # =================================================================
            # VUELTA RÁPIDA (HOTLAP) - Mínimo peso posible
            # =================================================================
            session_name = "Vuelta Rápida"
            est_laps = 3  # 1 salida + 2 lanzadas
            safety_l = 2.0
            rec_fuel = min(int(tank_max), max(10, math.ceil(est_laps * avg_fuel + safety_l)))
            speech = (
                f"Estamos en boxes para Vuelta Rápida. Te recomiendo cargar exactamente {rec_fuel} litros de combustible: "
                f"3 vueltas a {avg_fuel:.1f} litros por vuelta, con 2 litros de margen de seguridad para salir al mínimo peso."
            )

        elif session_type == 1:
            # =================================================================
            # CLASIFICACIÓN (QUALIFYING) - Tanda de ataque de 4-5 vueltas
            # =================================================================
            session_name = "Clasificación"
            est_laps = 4  # 1 salida + 2 lanzadas + 1 retorno
            safety_l = 2.5
            rec_fuel = min(int(tank_max), max(14, math.ceil(est_laps * avg_fuel + safety_l)))
            speech = (
                f"Estamos en boxes para Clasificación. Para tu tanda de ataque necesitas exactamente {rec_fuel} litros de combustible: "
                f"4 vueltas con {safety_l:.1f} litros de reserva de seguridad."
            )

        elif session_type == 2:
            # =================================================================
            # CARRERA (RACE) - Duración en minutos o número de vueltas
            # =================================================================
            session_name = "Carrera"
            if sample.session_time_left > 10.0:
                # Carrera por tiempo (ej. 20m, 30m, 60m)
                time_laps = sample.session_time_left / lap_sec
                # +1 porque el líder cruza la meta tras el 0:00 + 1 vuelta de formación
                est_laps = math.ceil(time_laps) + 1
                duration_mins = int(round(sample.session_time_left / 60.0))
                duration_str = f"los {duration_mins} minutos de carrera"
            elif sample.session_laps > 0:
                # Carrera por vueltas fijas
                remaining = sample.session_laps - sample.completed_laps
                est_laps = max(1, remaining)
                duration_str = f"las {est_laps} vueltas restantes de carrera"
            else:
                est_laps = 12
                duration_str = "la carrera"

            # Margen de seguridad: 1.5 vueltas de consumo extra para batallas, rebufo o ritmo elevado
            safety_l = round(avg_fuel * 1.5, 1)
            raw_target = (est_laps * avg_fuel) + safety_l
            rec_fuel = min(int(tank_max), math.ceil(raw_target))

            speech = (
                f"Estamos en boxes para la Carrera. Para {duration_str} necesitas exactamente {rec_fuel} litros en el tanque: "
                f"{est_laps} vueltas a {avg_fuel:.1f} litros por vuelta, incluyendo {safety_l:.1f} litros de margen de seguridad."
            )

        else:
            # =================================================================
            # ENTRENAMIENTOS / PRÁCTICA
            # =================================================================
            session_name = "Entrenamientos"
            est_laps = 6
            safety_l = 3.0
            rec_fuel = min(int(tank_max), math.ceil(est_laps * avg_fuel + safety_l))
            speech = (
                f"Estamos en boxes para Entrenamientos. Te recomiendo salir con {rec_fuel} litros de combustible "
                f"para una tanda de 6 vueltas con margen de seguridad."
            )

        return FuelStrategyResult(
            session_name=session_name,
            session_type=session_type,
            avg_fuel_per_lap=avg_fuel,
            estimated_laps=est_laps,
            safety_liters=safety_l,
            recommended_fuel_l=rec_fuel,
            current_fuel_l=round(sample.fuel, 1),
            speech_text=speech,
        )
