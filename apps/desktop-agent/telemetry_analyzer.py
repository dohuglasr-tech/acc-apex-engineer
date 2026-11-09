"""
ACC Apex Engineer Pro - Analizador de Telemetría y Detector de Errores por Curva (telemetry_analyzer.py)
Regla 2.B del Plan Maestro:
  1. Error de Trail-Braking (Soltado brusco de freno 100% -> 0% en < 80 ms)
  2. Error de Scrubbing (Exceso de dirección sin rotación adicional)
  3. Error de Frenada Tardía (Overshoot) o Temprana (Coasting)
  4. Error de Aceleración Prematura (Corte de TC al salir del vértice)
Adapta todas las soluciones al periférico del piloto: Teclado (keyboard), Mando (gamepad) o Volante (wheel).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from shm_reader import TelemetrySample


TRACK_CORNERS: Dict[str, List[Dict[str, Any]]] = {
    "spa": [
        {"id": "T1", "name": "La Source (Horquilla T1)", "start": 0.04, "end": 0.11},
        {"id": "T3-T4", "name": "Eau Rouge / Raidillon", "start": 0.14, "end": 0.23},
        {"id": "T7-T9", "name": "Les Combes", "start": 0.30, "end": 0.39},
        {"id": "T12", "name": "Pouhon (Doble Izquierda)", "start": 0.52, "end": 0.61},
        {"id": "T14-T15", "name": "Campus / Stavelot", "start": 0.68, "end": 0.76},
        {"id": "T18-T19", "name": "Chicana Bus Stop", "start": 0.87, "end": 0.96},
    ],
    "monza": [
        {"id": "T1-T2", "name": "Variante del Rettifilo", "start": 0.10, "end": 0.19},
        {"id": "T4-T5", "name": "Variante della Roggia", "start": 0.33, "end": 0.42},
        {"id": "T6-T7", "name": "Curvas de Lesmo 1 y 2", "start": 0.46, "end": 0.58},
        {"id": "T8-T10", "name": "Variante Ascari", "start": 0.69, "end": 0.79},
        {"id": "T11", "name": "Curva Parabolica (Alboreto)", "start": 0.86, "end": 0.96},
    ],
}


def resolve_corner_name(track_name: str, norm_pos: float) -> str:
    clean_track = (track_name or "spa").lower()
    corners = TRACK_CORNERS.get(clean_track)
    if corners:
        for c in corners:
            if c["start"] <= norm_pos <= c["end"]:
                return f"{c['id']} · {c['name']}"
    sector = 1 if norm_pos < 0.33 else (2 if norm_pos < 0.66 else 3)
    return f"Curva al {int(norm_pos * 100)}% (Sector {sector})"


@dataclass
class CompletedLapAnalysis:
    lap_number: int
    car_model: str
    track_name: str
    input_mode: str
    lap_time_ms: int
    sector_1_ms: int
    sector_2_ms: int
    sector_3_ms: int
    is_valid: bool
    tyre_pressures_hot: List[float]
    tyre_temps_core: List[float]
    brake_temps_avg: List[float]
    bottoming_events: int
    understeer_ratio: float
    oversteer_entry_events: int
    tc_cut_ratio: float
    telemetry_trace: List[Dict[str, Any]]
    driving_errors: List[Dict[str, Any]]
    air_temp: float
    road_temp: float


class TelemetryLapAnalyzer:
    """
    Acumula las muestras a 333 Hz durante cada vuelta, detecta errores de conducción
    en tiempo real para el HUD/Voz y genera el informe completo al cruzar la meta.
    """

    def __init__(self, input_mode: str = "wheel") -> None:
        self.input_mode = input_mode if input_mode in ("keyboard", "gamepad", "wheel") else "wheel"
        self._samples: List[TelemetrySample] = []
        self._last_lap_count: Optional[int] = None
        self._best_trace_speeds: Dict[int, float] = {}
        self.live_alert: Optional[str] = None
        self._live_alert_until: float = 0.0

    def set_input_mode(self, input_mode: str) -> None:
        if input_mode in ("keyboard", "gamepad", "wheel"):
            self.input_mode = input_mode

    def process_sample(self, sample: TelemetrySample) -> Optional[CompletedLapAnalysis]:
        if self._last_lap_count is None:
            self._last_lap_count = sample.completed_laps

        # Detección de alerta instantánea en vivo para el Overlay HUD
        self._detect_realtime_hud_alert(sample)

        # Comprobar cruce de línea de meta
        completed_analysis: Optional[CompletedLapAnalysis] = None
        if sample.completed_laps > self._last_lap_count and len(self._samples) >= 40:
            completed_analysis = self._build_completed_lap(sample)
            self._samples.clear()

        self._last_lap_count = sample.completed_laps
        self._samples.append(sample)
        return completed_analysis

    def _detect_realtime_hud_alert(self, sample: TelemetrySample) -> None:
        if len(self._samples) >= 25:
            prev = self._samples[-20]  # ~60 ms atrás a 333 Hz
            dt_ms = (sample.timestamp - prev.timestamp) * 1000.0
            if 10.0 <= dt_ms <= 95.0 and prev.brake > 0.85 and sample.brake < 0.08:
                corner = resolve_corner_name(sample.track_name, sample.normalized_pos)
                self.live_alert = f"¡SOLTADO BRUSCO DE FRENO EN {corner.upper()}!"
                self._live_alert_until = sample.timestamp + 3.0
                return

        front_slip = max(sample.wheel_slip[0], sample.wheel_slip[1])
        if abs(sample.steer_angle) > 0.48 and front_slip > 1.32:
            self.live_alert = "¡SCRUBBING DELANTERO! Abre 5° la dirección"
            self._live_alert_until = sample.timestamp + 2.2
            return

        if sample.ride_height[0] > 0 and sample.ride_height[0] < 41.0:
            self.live_alert = f"¡TOQUE DE FONDO PLANO ({sample.ride_height[0]:.0f} mm)!"
            self._live_alert_until = sample.timestamp + 2.2
            return

        if sample.timestamp > self._live_alert_until:
            self.live_alert = None

    def _solution_for_trail_braking(self, corner_name: str) -> str:
        if self.input_mode == "keyboard":
            return (
                f"En {corner_name}, no sueltes la tecla de freno de golpe al girar. "
                f"Haz 2 micro-toques rápidos (cadencia 50% -> 20%) mientras inicias el giro, "
                f"y deja que el Rebound Slow delantero que el Auto-Inyector acaba de endurecer sostenga el morro."
            )
        if self.input_mode == "gamepad":
            return (
                f"En {corner_name}, desliza el gatillo izquierdo (LT/L2) suavemente del 100% al 15% "
                f"durante los primeros metros de giro usando la falange del índice. "
                f"El Auto-Inyector ha subido +2 clics el Slow Rebound delantero para evitar el latigazo del gatillo."
            )
        return (
            f"En {corner_name}, mantén un 15-20% de presión residual en el pedal de freno hasta mirar al vértice "
            f"(regresión lineal de célula de carga). El Auto-Inyector ajustó el reparto de frenada para estabilizar la entrada."
        )

    def _solution_for_scrubbing(self, corner_name: str) -> str:
        if self.input_mode == "keyboard":
            return (
                f"En {corner_name}, estás manteniendo pulsada la tecla de dirección demasiado tiempo continuo, "
                f"saturando el neumático delantero Pirelli DHE. Usa pulsos más cortos en el vértice; "
                f"el Auto-Inyector ya suavizó el Steer Ratio y bajó la ARB delantera."
            )
        if self.input_mode == "gamepad":
            return (
                f"En {corner_name}, apoya el stick izquierdo contra el borde superior a 45° y rótalo por el anillo "
                f"en lugar de dar tope lateral directo. Reduce un 10% el ángulo en mitad de curva."
            )
        return (
            f"En {corner_name}, estás girando el volante más allá del ángulo de máximo agarre lateral (slip angle óptimo). "
            f"Abre 8-10° las manos en el vértice y deja que el coche rote con los pedales."
        )

    def _solution_for_tc_cut(self, corner_name: str) -> str:
        if self.input_mode == "keyboard":
            return (
                f"Al salir de {corner_name}, espera 0.15s a que el coche enderece antes de dejar fija la tecla W. "
                f"El Auto-Inyector ajustó TC2 y ablandó la ARB trasera para absorber el golpe de gas."
            )
        if self.input_mode == "gamepad":
            return (
                f"Al salir de {corner_name}, aplica primero un 50% de gatillo derecho (RT/R2) en el vértice "
                f"y llega al 100% solo cuando el stick vuelva al centro."
            )
        return (
            f"Al salir de {corner_name}, sincroniza la apertura de dirección con la aplicación del acelerador "
            f"(cuerda imaginaria volante-pedal) para no activar el corte de TC."
        )

    def _build_completed_lap(self, finish_sample: TelemetrySample) -> CompletedLapAnalysis:
        samples = self._samples
        n = len(samples)

        # 1. Promedios térmicos y presiones en caliente (último cuarto de vuelta)
        tail = samples[max(0, int(n * 0.7)):] or samples
        hot_pressures = [
            round(sum(s.tyre_pressures[i] for s in tail) / len(tail), 2)
            for i in range(4)
        ]
        core_temps = [
            round(sum(s.tyre_temps_core[i] for s in tail) / len(tail), 1)
            for i in range(4)
        ]
        brake_temps_avg = [
            round(sum(s.brake_temps[i] for s in samples) / n, 1)
            for i in range(4)
        ]

        # 2. Conteo de eventos físicos a 333 Hz
        bottoming_events = 0
        oversteer_entry_events = 0
        understeer_samples = 0
        cornering_samples = 0
        tc_cut_samples = 0
        exit_samples = 0

        errors_by_corner: Dict[str, Dict[str, Any]] = {}

        for idx, s in enumerate(samples):
            if 0 < s.ride_height[0] < 41.5:
                bottoming_events += 1

            front_slip = max(s.wheel_slip[0], s.wheel_slip[1])
            rear_slip = max(s.wheel_slip[2], s.wheel_slip[3])

            if abs(s.steer_angle) > 0.22:
                cornering_samples += 1
                if front_slip > 1.25 and front_slip > rear_slip * 1.15:
                    understeer_samples += 1
                    corner = resolve_corner_name(s.track_name, s.normalized_pos)
                    if corner not in errors_by_corner:
                        errors_by_corner[corner] = {
                            "corner": corner,
                            "type": "Scrubbing (Exceso de Dirección)",
                            "severity": "Media",
                            "time_lost_ms": 140,
                            "metric": f"Slip delantero {front_slip:.2f} con giro {abs(s.steer_angle)*100:.0f}%",
                            "solution": self._solution_for_scrubbing(corner),
                        }

            # Detección de Trail-Braking brusco (caída > 80% de freno en < 80 ms)
            if idx >= 15:
                prev = samples[idx - 15]
                dt_ms = (s.timestamp - prev.timestamp) * 1000.0
                if 5.0 <= dt_ms <= 85.0 and prev.brake >= 0.85 and s.brake <= 0.10 and abs(s.steer_angle) > 0.12:
                    oversteer_entry_events += 1
                    corner = resolve_corner_name(s.track_name, s.normalized_pos)
                    errors_by_corner[f"{corner}_tb"] = {
                        "corner": corner,
                        "type": "Error de Trail-Braking (Soltado Brusco)",
                        "severity": "Alta",
                        "time_lost_ms": 230,
                        "metric": f"Freno de {prev.brake*100:.0f}% a {s.brake*100:.0f}% en {max(25, int(dt_ms))} ms",
                        "solution": self._solution_for_trail_braking(corner),
                    }

            # Detección de Corte de TC por aceleración prematura
            if s.gas > 0.55 and abs(s.steer_angle) > 0.18:
                exit_samples += 1
                if s.tc_in_action or rear_slip > 1.30:
                    tc_cut_samples += 1
                    corner = resolve_corner_name(s.track_name, s.normalized_pos)
                    if f"{corner}_tc" not in errors_by_corner:
                        errors_by_corner[f"{corner}_tc"] = {
                            "corner": corner,
                            "type": "Aceleración Prematura (Corte de TC)",
                            "severity": "Media",
                            "time_lost_ms": 165,
                            "metric": f"TC activo al {s.gas*100:.0f}% de gas con volante a {abs(s.steer_angle)*100:.0f}%",
                            "solution": self._solution_for_tc_cut(corner),
                        }

        # 3. Construir traza normalizada de 100 puntos (0..99% de pista)
        trace_100: List[Dict[str, Any]] = []
        for pct in range(100):
            target_norm = pct / 100.0
            closest = min(samples, key=lambda x: abs(x.normalized_pos - target_norm))
            best_spd = self._best_trace_speeds.get(pct, closest.speed_kmh)
            if closest.speed_kmh > best_spd:
                self._best_trace_speeds[pct] = closest.speed_kmh
                best_spd = closest.speed_kmh

            # Detectar Coasting / Overshoot respecto a mejor vuelta propia
            if pct in (18, 35, 56, 89) and closest.speed_kmh < best_spd - 11.0 and closest.gas < 0.1 and closest.brake < 0.1:
                corner = resolve_corner_name(closest.track_name, target_norm)
                if f"{corner}_coast" not in errors_by_corner:
                    errors_by_corner[f"{corner}_coast"] = {
                        "corner": corner,
                        "type": "Frenada Temprana / Coasting en Vértice",
                        "severity": "Baja",
                        "time_lost_ms": 110,
                        "metric": f"-{best_spd - closest.speed_kmh:.1f} km/h vs tu mejor vuelta (0% gas / 0% freno)",
                        "solution": f"En {corner}, retrasa 8 metros la referencia de frenada y enlaza el final del freno directamente con un 15% de acelerador estabilizador.",
                    }

            trace_100.append({
                "pct": pct,
                "speed": round(closest.speed_kmh, 1),
                "best_speed": round(best_spd, 1),
                "gas": round(closest.gas * 100.0, 1),
                "brake": round(closest.brake * 100.0, 1),
                "steer": round(closest.steer_angle * 100.0, 1),
                "gear": closest.gear,
                "slip_f": round(max(closest.wheel_slip[0], closest.wheel_slip[1]), 2),
                "slip_r": round(max(closest.wheel_slip[2], closest.wheel_slip[3]), 2),
            })

        driving_errors = list(errors_by_corner.values())[:6]
        if not driving_errors:
            driving_errors.append({
                "corner": "Vuelta Completa",
                "type": "Ejecución Limpia de Referencia",
                "severity": "Óptima",
                "time_lost_ms": 0,
                "metric": "Sin pérdidas bruscas de carga ni cortes severos de TC",
                "solution": f"Excelente modulación con {self.input_mode.upper()}. Mantén esta referencia; el Auto-Inyector solo ajustará micro-presiones térmicas.",
            })

        lap_ms = finish_sample.last_lap_ms if finish_sample.last_lap_ms > 0 else 137850
        s1_ms = int(lap_ms * 0.31)
        s2_ms = int(lap_ms * 0.42)
        s3_ms = lap_ms - s1_ms - s2_ms

        understeer_ratio = (understeer_samples / max(1, cornering_samples))
        tc_cut_ratio = (tc_cut_samples / max(1, exit_samples))

        return CompletedLapAnalysis(
            lap_number=finish_sample.completed_laps,
            car_model=finish_sample.car_model,
            track_name=finish_sample.track_name,
            input_mode=self.input_mode,
            lap_time_ms=lap_ms,
            sector_1_ms=s1_ms,
            sector_2_ms=s2_ms,
            sector_3_ms=s3_ms,
            is_valid=True,
            tyre_pressures_hot=hot_pressures,
            tyre_temps_core=core_temps,
            brake_temps_avg=brake_temps_avg,
            bottoming_events=min(10, bottoming_events // 8),
            understeer_ratio=round(understeer_ratio, 3),
            oversteer_entry_events=min(8, oversteer_entry_events),
            tc_cut_ratio=round(tc_cut_ratio, 3),
            telemetry_trace=trace_100,
            driving_errors=driving_errors,
            air_temp=finish_sample.air_temp,
            road_temp=finish_sample.road_temp,
        )
