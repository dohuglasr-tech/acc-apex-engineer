"""
ACC Apex Engineer Pro - Ingeniero de Carrera IA Local en Tiempo Real (local_ai_engineer.py)
Opera 100% en local dentro del ejecutable/demonio sin depender de LLMs en la nube.
Calcula en tiempo real (333 Hz):
  1. Detección anticipada de curvas (lookahead por distancia/tiempo)
  2. Instrucción de radio preventiva ("Se aproxima la curva X a Y metros, frena en...")
  3. Diagnóstico de paso por curva (frenada, vértice, velocidad mínima, tracción)
  4. Consejos de radio constructivos y amigables al salir de cada curva
  5. Sincronización instantánea de estado hacia el panel web y WebSocket
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from shm_reader import TelemetrySample
from track_knowledge_base import (
    CornerKnowledge,
    TrackKnowledge,
    get_track_knowledge,
    normalize_track_key,
)


@dataclass
class RadioMessageEvent:
    text: str
    category: str  # "anticipation", "coaching", "praise", "alert"
    timestamp: float
    time_str: str


class LocalAIEngineer:
    """
    Ingeniero de pista IA local estilo F1 / WEC (Bono / GP).
    Cálculo de trayectorias en tiempo real, anticipación por radio y telemetría de curvas.
    """

    def __init__(self, voice_engine: Optional[Any] = None, input_mode: str = "gamepad") -> None:
        self.voice = voice_engine
        self.input_mode = input_mode if input_mode in ("keyboard", "gamepad", "wheel") else "gamepad"
        self.current_track_name: str = ""
        self.track_knowledge: Optional[TrackKnowledge] = None

        # Estado en vivo
        self.last_sample: Optional[TelemetrySample] = None
        self.current_lap_number: int = -1
        self.last_spoken_corner_id: Optional[str] = None
        self.last_spoken_lap: int = -1
        self.last_speech_ts: float = 0.0

        # Monitoreo en curva
        self.active_corner: Optional[CornerKnowledge] = None
        self.in_corner_min_speed: float = 999.0
        self.in_corner_max_brake: float = 0.0
        self.in_corner_scrub_frames: int = 0
        self.in_corner_tc_cuts: int = 0
        self.in_corner_had_trail: bool = False

        # Datos analíticos
        self.last_corner_result: Optional[Dict[str, Any]] = None
        self.upcoming_corner_data: Optional[Dict[str, Any]] = None
        self.current_radio_event: Optional[RadioMessageEvent] = None
        self.recent_radio_calls: List[Dict[str, Any]] = []

    def set_input_mode(self, mode: str) -> None:
        if mode in ("keyboard", "gamepad", "wheel"):
            self.input_mode = mode

    def _ensure_track(self, raw_track_name: str) -> None:
        if raw_track_name and raw_track_name != self.current_track_name:
            self.current_track_name = raw_track_name
            self.track_knowledge = get_track_knowledge(raw_track_name)
            self.last_spoken_corner_id = None
            self.active_corner = None

    def process_sample(self, sample: TelemetrySample) -> Dict[str, Any]:
        """
        Procesa una muestra de telemetría a alta frecuencia.
        Evalúa anticipación y rendimiento en curva.
        """
        self.last_sample = sample
        if not sample.is_live_acc or sample.speed_kmh < 15.0 or sample.is_in_pit or sample.is_in_pit_lane:
            self.upcoming_corner_data = None
            self.active_corner = None
            return self.get_state()

        self._ensure_track(sample.track_name)
        if not self.track_knowledge:
            return self.get_state()

        now = time.time()
        pos = sample.normalized_pos
        speed_mps = max(10.0, sample.speed_kmh / 3.6)
        track_len = float(self.track_knowledge.length_m)

        # Si cambió de vuelta, reiniciamos el seguidor de curva hablada
        if sample.completed_laps != self.current_lap_number:
            self.current_lap_number = sample.completed_laps
            self.last_spoken_corner_id = None

        # 1. ENCONTRAR LA PRÓXIMA CURVA
        best_corner: Optional[CornerKnowledge] = None
        min_dist_m = 99999.0
        min_seconds = 999.0

        for corner in self.track_knowledge.corners:
            # Distancia normalizada hacia el inicio de la curva
            diff_spline = (corner.spline_start - pos) % 1.0
            dist_m = diff_spline * track_len
            secs = dist_m / speed_mps

            # Si la curva está adelante en la vuelta (hasta 600 metros de distancia)
            if dist_m < min_dist_m and dist_m > 0:
                min_dist_m = dist_m
                min_seconds = secs
                best_corner = corner

        # 2. ACTUALIZAR RADAR DE PRÓXIMA CURVA
        if best_corner and min_dist_m <= 450.0:
            self.upcoming_corner_data = {
                "id": best_corner.id,
                "name": best_corner.name,
                "distance_m": int(min_dist_m),
                "seconds_away": round(min_seconds, 1),
                "gear": best_corner.gear,
                "target_speed_kmh": int(best_corner.target_apex_speed),
                "braking_marker": best_corner.braking_marker,
                "braking_type": best_corner.braking_type,
                "anticipation_msg": best_corner.anticipation_advice.format(dist=int(min_dist_m)),
                "racing_line_notes": best_corner.apex_technique,
                "exit_technique": best_corner.exit_technique,
            }
        else:
            self.upcoming_corner_data = None

        # 3. DETECTAR SI DEBEMOS TRANSMITIR LA ANTICIPACIÓN POR RADIO
        # Ventana de disparo: entre 130m y 220m (o 2.8s a 4.5s antes del frenado)
        if best_corner and (110.0 <= min_dist_m <= 220.0 or 2.6 <= min_seconds <= 4.2):
            corner_key = f"{best_corner.id}_{sample.completed_laps}"
            if self.last_spoken_corner_id != corner_key and (now - self.last_speech_ts) >= 4.0:
                self.last_spoken_corner_id = corner_key
                self.last_speech_ts = now

                advice = best_corner.anticipation_advice.format(dist=int(min_dist_m))
                self._broadcast_radio(advice, "anticipation")

        # 4. EVALUACIÓN DENTRO DE LA CURVA
        for corner in self.track_knowledge.corners:
            # ¿Estamos dentro de la curva?
            is_inside = False
            if corner.spline_start <= corner.spline_exit:
                is_inside = corner.spline_start <= pos <= corner.spline_exit
            else:
                # Curva que cruza la línea de meta
                is_inside = pos >= corner.spline_start or pos <= corner.spline_exit

            if is_inside:
                if self.active_corner != corner:
                    # Entramos a una nueva curva
                    self.active_corner = corner
                    self.in_corner_min_speed = sample.speed_kmh
                    self.in_corner_max_brake = sample.brake
                    self.in_corner_scrub_frames = 0
                    self.in_corner_tc_cuts = 0
                    self.in_corner_had_trail = False
                else:
                    # Actualizamos métricas en la curva
                    if sample.speed_kmh < self.in_corner_min_speed:
                        self.in_corner_min_speed = sample.speed_kmh
                    if sample.brake > self.in_corner_max_brake:
                        self.in_corner_max_brake = sample.brake
                    if sample.brake > 0.08 and abs(sample.steer_angle) > 15.0:
                        self.in_corner_had_trail = True
                    if abs(sample.steer_angle) > 55.0 and sample.speed_kmh > 70.0:
                        self.in_corner_scrub_frames += 1
                    if sample.tc_in_action:
                        self.in_corner_tc_cuts += 1
                break
        else:
            # Salimos de la curva activa -> Generar diagnóstico y consejo de radio
            if self.active_corner:
                c = self.active_corner
                min_spd = self.in_corner_min_speed
                target_spd = c.target_apex_speed
                speed_delta = round(min_spd - target_spd, 1)

                # Puntuación de curva
                score = 100
                if speed_delta < -8.0:
                    score -= 15
                if not self.in_corner_had_trail and c.braking_type in ("hard", "trail"):
                    score -= 12
                if self.in_corner_scrub_frames > 15:
                    score -= 10
                if self.in_corner_tc_cuts > 10:
                    score -= 8
                score = max(55, min(100, score))

                # Veredicto y consejo constructivo
                tip_text = ""
                category = "coaching"

                if score >= 90:
                    tip_text = c.coaching_tips.get("praise") or f"¡Gran paso por {c.name}! Vértice perfecto y tracción limpia."
                    category = "praise"
                elif self.in_corner_scrub_frames > 20:
                    tip_text = c.coaching_tips.get("scrub") or f"En {c.name}, cuida el ángulo de dirección en el vértice para no sobrecalentar gomas."
                elif not self.in_corner_had_trail and c.braking_type in ("hard", "trail"):
                    tip_text = c.coaching_tips.get("trail") or f"En {c.name}, suelta el freno más progresivo hacia el vértice para ayudar a rotar el coche."
                elif speed_delta < -10.0:
                    tip_text = c.coaching_tips.get("early_brake") or f"Frenaste un poco pronto en {c.name}, podemos ganar dos décimas frenando al {c.braking_marker}."
                elif self.in_corner_tc_cuts > 12:
                    tip_text = c.coaching_tips.get("traction") or f"Paciencia con el gas a la salida de {c.name}, espera a enderezar antes de pisar a fondo."
                else:
                    tip_text = f"Buen paso por {c.name}. Mantén ese ritmo constante."

                self.last_corner_result = {
                    "corner_id": c.id,
                    "corner_name": c.name,
                    "score": score,
                    "verdict": tip_text,
                    "apex_speed_kmh": round(min_spd, 1),
                    "target_speed_kmh": round(target_spd, 1),
                    "speed_delta_kmh": speed_delta,
                    "trail_braking": "Excelente" if self.in_corner_had_trail else "Mejorable",
                }

                # Emitir consejo por radio si es relevante y no estamos saturando la radio
                if (now - self.last_speech_ts) >= 7.0 and (score < 85 or (score >= 95 and (sample.completed_laps % 2 == 0))):
                    self.last_speech_ts = now
                    self._broadcast_radio(tip_text, category)

                self.active_corner = None

        return self.get_state()

    def _broadcast_radio(self, text: str, category: str) -> None:
        """Emite por voz y guarda en el historial de radio."""
        now = time.time()
        time_str = datetime.now().strftime("%H:%M:%S")

        event = RadioMessageEvent(
            text=text,
            category=category,
            timestamp=now,
            time_str=time_str,
        )
        self.current_radio_event = event

        # Agregar al historial reciente (máximo 10)
        self.recent_radio_calls.insert(0, {
            "text": text,
            "category": category,
            "timestamp": now,
            "time_str": time_str,
        })
        if len(self.recent_radio_calls) > 10:
            self.recent_radio_calls = self.recent_radio_calls[:10]

        # Sintetizar voz si el motor está presente
        if self.voice:
            try:
                self.voice.speak(text)
            except Exception:
                pass

    def get_state(self) -> Dict[str, Any]:
        """Estructura de datos enviada a Supabase y WebSocket para el panel web."""
        now = time.time()
        is_transmitting = bool(
            self.current_radio_event and (now - self.current_radio_event.timestamp) < 5.5
        )

        track_dict = None
        if self.track_knowledge:
            track_dict = {
                "track_id": self.track_knowledge.track_id,
                "display_name": self.track_knowledge.display_name,
                "country": self.track_knowledge.country,
                "length_m": self.track_knowledge.length_m,
                "total_corners": len(self.track_knowledge.corners),
            }

        return {
            "engineer_name": "Álvaro (Ingeniero de Pista IA)",
            "status": "transmitting" if is_transmitting else "monitoring",
            "upcoming_corner": self.upcoming_corner_data,
            "current_corner": {
                "id": self.active_corner.id if self.active_corner else None,
                "name": self.active_corner.name if self.active_corner else "Recta",
                "is_inside": bool(self.active_corner is not None),
            },
            "last_corner_analysis": self.last_corner_result,
            "radio_transmission": {
                "text": self.current_radio_event.text if self.current_radio_event else "Monitoreando telemetría en tiempo real.",
                "category": self.current_radio_event.category if self.current_radio_event else "standby",
                "timestamp": self.current_radio_event.timestamp if self.current_radio_event else 0.0,
                "time_str": self.current_radio_event.time_str if self.current_radio_event else "",
                "is_active": is_transmitting,
            },
            "recent_radio_calls": self.recent_radio_calls,
            "track_info": track_dict,
        }

