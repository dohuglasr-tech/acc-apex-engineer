"""
ACC Apex Engineer Pro - Calculador de Estrategia de Combustible y Consumo por Vuelta (fuel_strategy.py)
Mide el consumo real de combustible por vuelta a 333 Hz, calcula la carga óptima para
Carrera, Vuelta Rápida (Hotlap), Clasificación o Entrenamientos con margen de seguridad dinámico,
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


# Consumo medio base por circuito para coches GT3 (litros por vuelta)
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
DEFAULT_FALLBACK_FUEL = 3.05

# Tiempos de vuelta de referencia representativos para coches GT3 en cada circuito (en segundos)
DEFAULT_GT3_LAP_TIME_SEC: Dict[str, float] = {
    "spa": 138.0,            # ~2:18
    "monza": 108.0,          # ~1:48
    "silverstone": 119.0,    # ~1:59
    "nurburgring": 114.0,    # ~1:54
    "brands_hatch": 84.0,    # ~1:24
    "misano": 94.0,          # ~1:34
    "paul_ricard": 114.0,    # ~1:54
    "zandvoort": 96.0,       # ~1:36
    "barcelona": 104.0,      # ~1:44
    "hungaroring": 104.0,    # ~1:44
    "kyalami": 102.0,        # ~1:42
    "suzuka": 121.0,         # ~2:01
    "mount_panorama": 122.0, # ~2:02
    "laguna_seca": 83.0,     # ~1:23
    "imola": 102.0,          # ~1:42
    "donington": 88.0,       # ~1:28
    "oulton_park": 94.0,     # ~1:34
    "snetterton": 107.0,     # ~1:47
    "cota": 125.0,           # ~2:05
    "indianapolis": 97.0,    # ~1:37
    "watkins_glen": 105.0,   # ~1:45
    "valencia": 91.0,        # ~1:31
    "red_bull_ring": 89.0,   # ~1:29
}
DEFAULT_FALLBACK_LAP_SEC = 106.0


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

    def get_default_lap_time_sec(self, track_name: str) -> float:
        """Devuelve el tiempo de vuelta estándar en segundos para el circuito."""
        track_clean = track_name.lower().replace(" ", "_").replace("-", "_")
        for k, v in DEFAULT_GT3_LAP_TIME_SEC.items():
            if k in track_clean:
                return v
        return DEFAULT_FALLBACK_LAP_SEC

    def get_avg_fuel(self, car_model: str, track_name: str, sample_fuel_per_lap: float = 0.0) -> float:
        """
        Devuelve el consumo medio por vuelta:
        1. Historial medido real del piloto si existe.
        2. Consumo nativo reportado por el motor de física de ACC (fuelXLap).
        3. Base de datos por circuito GT3.
        """
        key = f"{car_model.lower()}:{track_name.lower()}"
        history = self._fuel_history.get(key)
        if history and len(history) >= 2:
            return round(sum(history) / len(history), 2)

        if sample_fuel_per_lap and 0.8 <= sample_fuel_per_lap <= 8.5:
            return round(sample_fuel_per_lap, 2)

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
        fuel_xlap = getattr(sample, "fuel_per_lap", 0.0)
        avg_fuel = self.get_avg_fuel(sample.car_model, sample.track_name, fuel_xlap)
        tank_max = max(100.0, sample.max_fuel if sample.max_fuel > 10.0 else 120.0)

        # Determinar tiempo de vuelta de referencia real (en segundos)
        if best_lap_ms > 45000 and best_lap_ms < 600000:
            lap_sec = best_lap_ms / 1000.0
        elif last_lap_ms > 45000 and last_lap_ms < 600000:
            lap_sec = last_lap_ms / 1000.0
        else:
            lap_sec = self.get_default_lap_time_sec(sample.track_name)

        current_f = round(sample.fuel, 1)

        # =====================================================================
        # CLASIFICACIÓN DE SESIÓN EN ASSETTO CORSA COMPETIZIONE:
        # 0 = AC_PRACTICE (Entrenamientos libres / Práctica)
        # 1 = AC_QUALIFY (Clasificación)
        # 2 = AC_RACE (Carrera)
        # 3 = AC_HOTLAP (Vuelta Rápida en solitario)
        # =====================================================================

        if session_type == 3:
            # -----------------------------------------------------------------
            # 1. VUELTA RÁPIDA (HOTLAP) - Mínimo peso para vuelta lanzada
            # -----------------------------------------------------------------
            session_name = "Vuelta Rápida"
            est_laps = 3  # 1 salida + 2 lanzadas
            safety_l = 2.0
            rec_fuel = min(int(tank_max), max(10, math.ceil(est_laps * avg_fuel + safety_l)))
            
            diff = rec_fuel - int(current_f)
            if diff > 1:
                action_str = f"Actualmente tienes {current_f:.0f}L; añade {diff} litros en el setup."
            elif diff < -3:
                action_str = f"Tienes {current_f:.0f}L en el tanque; llevas {-diff} litros de más para hotlap, baja la carga para reducir peso."
            else:
                action_str = f"Tienes {current_f:.0f}L en el tanque, peso óptimo para salir a marcar tiempo."

            speech = (
                f"Estamos en boxes para Vuelta Rápida. Carga recomendada: {rec_fuel} litros en el tanque "
                f"para 3 vueltas a {avg_fuel:.1f} litros por vuelta. {action_str}"
            )

        elif session_type == 1:
            # -----------------------------------------------------------------
            # 2. CLASIFICACIÓN (QUALIFYING) - Tanda de ataque de 4 a 5 vueltas
            # -----------------------------------------------------------------
            session_name = "Clasificación"
            est_laps = 5  # 1 de salida + 3 vueltas lanzadas + 1 de regreso a boxes
            safety_l = 2.5
            rec_fuel = min(int(tank_max), max(14, math.ceil(est_laps * avg_fuel + safety_l)))

            diff = rec_fuel - int(current_f)
            if diff > 1:
                action_str = f"Actualmente tienes {current_f:.0f}L; necesitas {diff} litros más para la tanda completa."
            elif diff < -4:
                action_str = f"Tienes {current_f:.0f}L; vas pesado por {-diff} litros extras, baja la carga en el setup para mejorar aceleración."
            else:
                action_str = f"Tienes {current_f:.0f}L en el tanque, carga adecuada para tu tanda de clasificación."

            speech = (
                f"Estamos en boxes para Clasificación. Para tu tanda de ataque de 5 vueltas necesitas {rec_fuel} litros en el tanque "
                f"a {avg_fuel:.1f} litros por vuelta con reserva de seguridad. {action_str}"
            )

        elif session_type == 2:
            # -----------------------------------------------------------------
            # 3. CARRERA (RACE) - Cálculo exacto por tiempo o número de vueltas
            # -----------------------------------------------------------------
            session_name = "Carrera"
            if sample.session_time_left > 15.0:
                # Carrera por tiempo (ej: 20m, 30m, 60m)
                time_laps = sample.session_time_left / lap_sec
                # +1 porque el líder cruza la meta tras el 0:00 + 1 vuelta de formación
                est_laps = math.ceil(time_laps) + 1
                duration_mins = int(round(sample.session_time_left / 60.0))
                duration_str = f"los {duration_mins} minutos de carrera"
            elif sample.session_laps > 0:
                # Carrera por vueltas fijas
                remaining = sample.session_laps - sample.completed_laps
                est_laps = max(1, remaining)
                duration_str = f"las {est_laps} vueltas de carrera"
            else:
                # Si estamos en parrilla o garaje antes de que arranque el reloj oficial de carrera
                est_laps = math.ceil(1200.0 / lap_sec) + 1  # Sprint estándar de 20 minutos
                duration_str = "la carrera (sprint proyectado de 20 minutos)"

            # Margen de seguridad: 1.5 vueltas de consumo extra para batallas, rebufos y vuelta de honor
            safety_l = round(avg_fuel * 1.5, 1)
            raw_target = (est_laps * avg_fuel) + safety_l
            rec_fuel = min(int(tank_max), math.ceil(raw_target))

            diff = rec_fuel - int(current_f)
            if diff > 1:
                action_str = f"Actualmente tienes {current_f:.0f}L; te faltan {diff} litros para llegar al final sin quedarte tirado."
            elif diff < -5:
                action_str = f"Tienes {current_f:.0f}L en el tanque; vas sobrado por {-diff} litros de combustible."
            else:
                action_str = f"Tienes {current_f:.0f}L en el tanque, carga exacta para completar la carrera."

            speech = (
                f"Estamos en boxes para la Carrera. Para {duration_str} ({est_laps} vueltas a {avg_fuel:.1f} L/vta) "
                f"necesitas exactamente {rec_fuel} litros en el tanque, incluyendo {safety_l:.1f}L de margen de seguridad. {action_str}"
            )

        else:
            # -----------------------------------------------------------------
            # 4. ENTRENAMIENTOS / PRÁCTICA (PRACTICE) - Tanda estándar de 8 vueltas
            # -----------------------------------------------------------------
            session_name = "Entrenamientos"
            if sample.session_time_left > 180.0:
                mins_left = int(round(sample.session_time_left / 60.0))
                # Tanda de práctica: entre 6 y 10 vueltas para testear setup y presiones
                est_laps = min(10, max(6, math.ceil(sample.session_time_left / lap_sec * 0.4)))
                duration_str = f"una tanda de {est_laps} vueltas ({mins_left} min restantes en sesión)"
            else:
                est_laps = 8
                duration_str = "una tanda de 8 vueltas"

            safety_l = 3.0
            rec_fuel = min(int(tank_max), math.ceil(est_laps * avg_fuel + safety_l))

            diff = rec_fuel - int(current_f)
            if diff > 1:
                action_str = f"Actualmente tienes {current_f:.0f}L; te faltan {diff} litros para el stint completo."
            elif diff < -5:
                action_str = f"Tienes {current_f:.0f}L en el tanque; tienes combustible suficiente para continuar rodando."
            else:
                action_str = f"Tienes {current_f:.0f}L en el tanque, carga ideal para rodar y calentar gomas."

            speech = (
                f"Estamos en boxes para Entrenamientos. Te recomiendo salir con {rec_fuel} litros en el tanque "
                f"para {duration_str} a {avg_fuel:.1f} litros por vuelta. {action_str}"
            )

        return FuelStrategyResult(
            session_name=session_name,
            session_type=session_type,
            avg_fuel_per_lap=avg_fuel,
            estimated_laps=est_laps,
            safety_liters=safety_l,
            recommended_fuel_l=rec_fuel,
            current_fuel_l=current_f,
            speech_text=speech,
        )
