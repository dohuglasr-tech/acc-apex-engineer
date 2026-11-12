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

    def __init__(
        self,
        voice_engine: Optional[Any] = None,
        input_mode: str = "gamepad",
        gemini_engine: Optional[Any] = None,
    ) -> None:
        self.voice = voice_engine
        self.gemini = gemini_engine
        self.input_mode = input_mode if input_mode in ("keyboard", "gamepad", "wheel") else "gamepad"
        self.voice_mode: str = "companion"  # "companion", "car_state", "telemetry"
        self.current_track_name: str = ""
        self.track_knowledge: Optional[TrackKnowledge] = None

        # Estado en vivo
        self.last_sample: Optional[TelemetrySample] = None
        self.current_lap_number: int = -1
        self.last_spoken_corner_id: Optional[str] = None
        self.last_spoken_lap: int = -1
        self.last_speech_ts: float = 0.0
        self._last_car_state_call_ts: float = 0.0
        self._last_car_alert_key: str = ""
        self._last_tyre_wear_call_ts: float = 0.0
        self._last_spoken_tyre_lap: int = -1
        self._last_wear_bracket: int = -1

        # Monitoreo en curva
        self.active_corner: Optional[CornerKnowledge] = None
        self.in_corner_min_speed: float = 999.0
        self.in_corner_max_brake: float = 0.0
        self.in_corner_scrub_frames: int = 0
        self.in_corner_tc_cuts: int = 0
        self.in_corner_had_trail: bool = False

        # Detección y recordatorios no invasivos de ayudas activadas
        self._assists_notified_count: int = 0
        self._last_assists_reminder_ts: float = 0.0
        self._last_assists_reminder_lap: int = -1

        # Monitoreo de límites de pista y salidas del trazado (Off-Track)
        self._is_currently_off_track: bool = False
        self._last_off_track_alert_ts: float = 0.0
        self._off_track_start_ts: float = 0.0

        # Monitoreo de coaching preventivo dinámico en carrera
        self._preventative_coaching_ts: float = 0.0
        self._recent_tips: List[str] = []

        # Datos analíticos
        self.last_corner_result: Optional[Dict[str, Any]] = None
        self.upcoming_corner_data: Optional[Dict[str, Any]] = None
        self.current_radio_event: Optional[RadioMessageEvent] = None
        self.recent_radio_calls: List[Dict[str, Any]] = []
        self._greeted_session: bool = False

    def set_input_mode(self, mode: str) -> None:
        if mode in ("keyboard", "gamepad", "wheel"):
            self.input_mode = mode

    def set_voice_mode(self, mode: str) -> None:
        """Cambia el comportamiento del agente de radio en tiempo real."""
        if mode in ("companion", "car_state", "telemetry") and mode != self.voice_mode:
            self.voice_mode = mode
            mode_names = {
                "companion": "Modo Acompañante activado. Te cantaré curvas, referencias y estado del coche.",
                "car_state": "Modo Solo Estado del Coche activado. Silencio en curvas, solo alertas mecánicas y presiones.",
                "telemetry": "Modo Solo Telemetría activado. Silencio en pista, únicamente métricas y tiempos de vuelta.",
            }
            if self._greeted_session:
                self._broadcast_radio(mode_names.get(mode, ""), "alert")

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
        if not sample.is_live_acc:
            self.upcoming_corner_data = None
            self.active_corner = None
            return self.get_state()

        self._ensure_track(sample.track_name)
        now = time.time()

        # Detección inmediata a 333 Hz de salidas de pista y límites superados
        self._check_off_track_events(sample, now)

        # Saludo de inicio de sesión por radio: inmediato al estar en pista en ACC
        if not self._greeted_session and sample.is_live_acc:
            self._greeted_session = True
            track_disp = self.track_knowledge.display_name if self.track_knowledge else sample.track_name
            greeting = f"¡Radio conectada! Hola compañero, soy Álvaro, tu ingeniero de pista en {track_disp}. Telemetría a 333 hercios activa. Te cantaré las curvas con tiempo. ¡Vamos a rodar!"
            self._broadcast_radio(greeting, "praise")
            self.last_speech_ts = now + 2.5

        if sample.speed_kmh < 15.0 or sample.is_in_pit or sample.is_in_pit_lane:
            self.upcoming_corner_data = None
            self.active_corner = None
            return self.get_state()

        if not self.track_knowledge:
            return self.get_state()

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
        if best_corner and min_dist_m <= 600.0:
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
        # Ventana de disparo predictiva: entre 260m y 460m (o 4.0s a 7.2s antes de la curva)
        # Permite que la radio hable y termine ANTES de llegar al cartel de 100/150m de frenada.
        if (
            self.voice_mode == "companion"
            and best_corner
            and (260.0 <= min_dist_m <= 460.0 or 4.0 <= min_seconds <= 7.2)
        ):
            corner_key = f"{best_corner.id}_{sample.completed_laps}"
            if self.last_spoken_corner_id != corner_key and (now - self.last_speech_ts) >= 4.0:
                self.last_spoken_corner_id = corner_key
                self.last_speech_ts = now

                # Variaciones dinámicas estilo F1 por vuelta para no repetir el mismo texto
                # REGLA OBLIGATORIA: Toda anticipación DEBE comenzar con "En la siguiente curva, [Nombre de la curva], ..."
                lap_idx = sample.completed_laps
                dist_round = int(min_dist_m)
                marker = best_corner.braking_marker
                gear = best_corner.gear

                if lap_idx <= 1:
                    advice = f"En la siguiente curva, {best_corner.name}, frena en {marker} y baja a {gear}ª."
                elif lap_idx % 3 == 0:
                    advice = f"En la siguiente curva, {best_corner.name}, a {dist_round} metros. Apura la frenada en {marker} y busca el vértice en marcha {gear}."
                elif lap_idx % 2 == 0:
                    advice = f"En la siguiente curva, {best_corner.name}, referencia en {marker}, baja a {gear}ª."
                else:
                    advice = f"En la siguiente curva, {best_corner.name}, cartel de {marker}. Modula el freno progresivo y asegura la tracción en salida."

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
                    # Entramos a una nueva curva -> purgar mensajes viejos para no emitir avisos desfasados
                    self.active_corner = corner
                    if self.voice:
                        self.voice.purge_pending()
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
                    tip_text = c.coaching_tips.get("praise") or f"¡Gran curva en {c.name}! Vértice perfecto y tracción limpia."
                    category = "praise"
                elif self.in_corner_scrub_frames > 20:
                    tip_text = c.coaching_tips.get("scrub") or f"En {c.name}, gira menos el volante en el vértice para cuidar las ruedas."
                elif not self.in_corner_had_trail and c.braking_type in ("hard", "trail"):
                    tip_text = c.coaching_tips.get("trail") or f"En {c.name}, suelta el freno más despacio hacia el vértice para meter el coche."
                elif speed_delta < -10.0:
                    tip_text = c.coaching_tips.get("early_brake") or f"Frenaste un poco pronto en {c.name}, podemos apurar diez metros más al cartel."
                elif self.in_corner_tc_cuts > 12:
                    tip_text = c.coaching_tips.get("traction") or f"Paciencia con el gas al salir de {c.name}, espera a enderezar el volante."
                else:
                    tip_text = f"Buen paso por {c.name}. Mantén ese ritmo."

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
                # Solo en modo "companion" (Acompañante)
                if (
                    self.voice_mode == "companion"
                    and (now - self.last_speech_ts) >= 5.0
                    and (score < 88 or (score >= 93 and (sample.completed_laps % 2 == 0)))
                ):
                    self.last_speech_ts = now
                    # Si Google Gemini está activo, generar consejo inteligente y adaptativo
                    if self.gemini and self.gemini.is_available:
                        ctx = {
                            "track_name": self.track_knowledge.display_name if self.track_knowledge else sample.track_name,
                            "car_model": sample.car_model,
                            "corner_name": c.name,
                            "score": score,
                            "speed_delta": speed_delta,
                            "input_mode": self.input_mode,
                            "primary_error": (
                                "frenada sin trail-braking (soltado brusco del gatillo)"
                                if not self.in_corner_had_trail
                                else "fricción excesiva de dirección (stick forzado a tope)"
                                if self.in_corner_scrub_frames > 15
                                else "corte de tracción por pisar pronto con volante girado"
                                if self.in_corner_tc_cuts > 10
                                else ""
                            ),
                        }

                        def _on_gemini_tip(g_text: str, g_cat: str) -> None:
                            self._broadcast_radio(g_text, g_cat)

                        self.gemini.generate_radio_advice_async("corner_exit", ctx, _on_gemini_tip)
                    else:
                        self._broadcast_radio(tip_text, category)

                self.active_corner = None

        # 5. MONITOREO DE ESTADO DEL COCHE, AYUDAS, DESGASTE Y COACHING PREVENTIVO
        # Silenciado en "telemetry"
        if self.voice_mode in ("companion", "car_state"):
            self._check_realism_and_assists_status(sample, now)
            self._check_car_state_alerts(sample, now)
            self._check_tyre_wear_reports(sample, now)
            self._check_preventative_coaching(sample, now)

        return self.get_state()

    def _check_realism_and_assists_status(self, sample: TelemetrySample, now: float) -> None:
        """
        Separa estrictamente la física de REALISMO (combustible, neumáticos, daños, sanciones)
        de las AYUDAS DE CONDUCCIÓN (caja automática, embrague auto, trazada ideal, estabilidad).
        Si el realismo tiene consumo y neumáticos activados, Álvaro SIEMPRE los gestiona al 100%.
        Las ayudas de conducción son asistencias de pilotaje que se aconsejan constructivamente.
        """
        realism_fuel = getattr(sample, "realism_fuel_on", True)
        realism_tire = getattr(sample, "realism_tire_on", True)
        has_assists = getattr(sample, "has_driving_assists", False) or getattr(sample, "has_assists_active", False)
        assists_summary = getattr(sample, "driving_assists_summary", "")

        # Solo hablar en rectas y condiciones de conducción estables para no desconcentrar
        if (
            self.active_corner is not None
            or sample.speed_kmh < 65.0
            or sample.is_in_pit
            or sample.is_in_pit_lane
            or sample.brake > 0.05
        ):
            return

        # Respetar silencio mínimo estricto de radio para no ser invasivo
        if (now - self.last_speech_ts) < 7.0:
            return

        # 1. Primer aviso informativo al arrancar la tanda en pista
        if self._assists_notified_count == 0:
            if (now - self._last_assists_reminder_ts) < 8.0:
                return

            if has_assists:
                if realism_fuel and realism_tire:
                    msg = (
                        f"Configuración detectada: Realismo de carrera al 100% con gestión de combustible y neumáticos activa. "
                        f"En asistencias llevas {assists_summary}. "
                        f"Monitorizaremos el consumo, presiones y gomas en cada vuelta mientras te asisto con las referencias y la trazada."
                    )
                else:
                    msg = (
                        f"Configuración detectada: En realismo tienes consumo o desgaste desactivado. "
                        f"En asistencias llevas {assists_summary}. "
                        f"Modo Contrarreloj: nos enfocamos al cien por cien en tus puntos de frenada, vértices y bajar tu tiempo por vuelta."
                    )
            else:
                if realism_fuel and realism_tire:
                    msg = (
                        "Configuración 100% Pro: Sin ayudas de conducción y realismo completo de carrera. "
                        "Control absoluto en tus manos, gestionaremos neumáticos y combustible en cada tanda."
                    )
                else:
                    msg = (
                        "Configuración detectada: Conducción manual pura sin ayudas. "
                        "Consumo o desgaste desactivados en realismo. Enfoque total en el cronómetro."
                    )

            self._assists_notified_count = 1
            self._last_assists_reminder_ts = now
            self._last_assists_reminder_lap = sample.completed_laps
            self.last_speech_ts = now
            self._broadcast_radio(msg, "alert")
            return

        # Si el piloto NO tiene ayudas de conducción activas, no emitir recordatorios de ayudas
        if not has_assists:
            return

        # 2. Recordatorios periódicos en repetidas ocasiones (No invasivos):
        # Disparo: cada 3 vueltas completadas O si transcurren más de 240 segundos (4 minutos) de rodaje
        lap_interval = (
            sample.completed_laps >= (self._last_assists_reminder_lap + 3)
            and sample.completed_laps > 0
        )
        time_interval = (now - self._last_assists_reminder_ts) >= 240.0

        if not lap_interval and not time_interval:
            return

        idx = (self._assists_notified_count - 1) % 4
        if realism_fuel and realism_tire:
            reminders = [
                f"Recordatorio de pilotaje: sigues rodando con {assists_summary}. Aprovecha para concentrarte en el cartel de frenada y morder el vértice; combustible y gomas están bajo control.",
                f"Consejo de telemetría: con las ayudas de conducción activas, anticípate al punto de giro; el desgaste de neumáticos y consumo se mantienen en ventana óptima.",
                f"Seguimos con {assists_summary}. Busca la trazada ideal y abre volante con suavidad para salir con tracción limpia hacia la recta.",
                f"Ritmo constante en pista. Asistencias de conducción activas y telemetría de neumáticos y combustible al cien por cien.",
            ]
        else:
            reminders = [
                "Modo Contrarreloj activo: sin desgaste ni consumo en el realismo. Toda la ganancia está en apurar las frenadas y arañar metros al crono.",
                f"Seguimos rodando con {assists_summary}. Trata de soltar el freno más progresivo hacia el punto de giro para maximizar la velocidad en el vértice.",
                "Sin consumo ni degradación de neumáticos: concéntrate en la línea de carrera y abrir dirección pronto al salir de curva.",
                "Modo Trazada Pura. Aprovecha el tanque y gomas infinitas para buscar el límite absoluto en cada sector.",
            ]

        msg = reminders[idx]
        self._assists_notified_count += 1
        self._last_assists_reminder_ts = now
        self._last_assists_reminder_lap = sample.completed_laps
        self.last_speech_ts = now
        self._broadcast_radio(msg, "coaching")

    def _check_tyre_wear_reports(self, sample: TelemetrySample, now: float) -> None:
        """
        Informa de forma proactiva y periódica el estado y porcentaje de desgaste
        de los neumáticos (delanteros y traseros) en rectas para mantener al piloto 100% informado.
        """
        # Si el usuario tiene desactivado el desgaste de neumáticos en el menú de realismo, silenciamos el reporte
        if getattr(sample, "realism_tire_on", getattr(sample, "aid_tire_rate", 1.0) > 0.05) is False:
            return

        if self.active_corner is not None or sample.speed_kmh < 65.0 or sample.is_in_pit or sample.is_in_pit_lane:
            return

        # Respetar silencio mínimo tras la última frase de radio para no saturar al piloto
        if (now - self.last_speech_ts) < 5.0:
            return

        w = sample.tyre_wear or [3.0, 3.0, 3.0, 3.0]
        # En ACC 3.0 mm representa el 100% de vida de goma nueva
        wear_pcts = [round(max(0.0, min(100.0, (1.0 - (val / 3.0)) * 100.0))) for val in w]
        avg_wear = int(sum(wear_pcts) / 4.0)
        avg_life = max(0, 100 - avg_wear)
        current_bracket = avg_wear // 4  # Cambios notables cada 4% de desgaste

        time_elapsed = now - self._last_tyre_wear_call_ts
        lap_changed = (sample.completed_laps > self._last_spoken_tyre_lap and sample.completed_laps > 0)
        bracket_changed = (self._last_wear_bracket != -1 and current_bracket > self._last_wear_bracket and avg_wear >= 4)

        # Disparo: cada 30 segundos en recta, al cambiar de vuelta, o cuando el desgaste sube 4%
        if time_elapsed < 30.0 and not lap_changed and not bracket_changed:
            return

        front_wear = int((wear_pcts[0] + wear_pcts[1]) / 2.0)
        rear_wear = int((wear_pcts[2] + wear_pcts[3]) / 2.0)

        tire_labels = ["delantero izquierdo", "delantero derecho", "trasero izquierdo", "trasero derecho"]
        worst_idx = wear_pcts.index(max(wear_pcts))
        worst_tire = tire_labels[worst_idx]
        worst_val = wear_pcts[worst_idx]

        if avg_wear <= 2:
            msg = f"Reporte de gomas: neumáticos nuevos al {avg_life}% de vida, desgaste mínimo al {avg_wear}%. Tienes agarre total."
        elif avg_wear <= 8:
            msg = f"Estado de neumáticos: gomas al {avg_life}% de vida, desgaste medio en {avg_wear}%. Degradación baja y ritmo estable."
        elif avg_wear <= 18:
            if abs(front_wear - rear_wear) >= 3:
                eje = "delantero" if front_wear > rear_wear else "trasero"
                val_eje = max(front_wear, rear_wear)
                msg = f"Reporte de neumáticos: desgaste medio en {avg_wear}%, vida al {avg_life}%. El tren {eje} sufre más con {val_eje}% de desgaste."
            else:
                msg = f"Reporte de gomas: desgaste en {avg_wear}%, vida al {avg_life}%. Agarre constante, el {worst_tire} está en {worst_val}%."
        elif avg_wear <= 30:
            msg = f"Atención a las gomas: desgaste medio en {avg_wear}%, vida al {avg_life}%. El neumático {worst_tire} acumula {worst_val}% de desgaste. Cuida el apoyo en curvas rápidas."
        else:
            msg = f"Alerta de degradación: gomas al {avg_life}% de vida con {avg_wear}% de desgaste. Pérdida sensible de agarre, ve planeando la parada en boxes."

        self._last_tyre_wear_call_ts = now
        self._last_spoken_tyre_lap = sample.completed_laps
        self._last_wear_bracket = current_bracket
        self.last_speech_ts = now
        self._broadcast_radio(msg, "car_state")

    def _check_car_state_alerts(self, sample: TelemetrySample, now: float) -> None:
        """
        Monitorea presiones de neumáticos, temperaturas de frenos y combustible.
        Solo emite en rectas para no desconcentrar al piloto en plena curva.
        """
        if self.active_corner is not None or sample.speed_kmh < 70.0:
            return

        if (now - self._last_car_state_call_ts) < 35.0 or (now - self.last_speech_ts) < 6.0:
            return

        # 1. Combustible crítico (solo si el consumo de combustible está activado en el simulador)
        if (
            getattr(sample, "realism_fuel_on", getattr(sample, "aid_fuel_rate", 1.0) > 0.05)
            and 0.0 < sample.fuel <= 9.0
            and self._last_car_alert_key != f"fuel_{int(sample.fuel)}"
        ):
            self._last_car_alert_key = f"fuel_{int(sample.fuel)}"
            self._last_car_state_call_ts = now
            self.last_speech_ts = now
            liters = round(sample.fuel, 1)
            msg = f"Aviso de reserva: te quedan {liters} litros de combustible. Prepara la parada en boxes."
            self._broadcast_radio(msg, "alert")
            return

        # 2. Temperatura de frenos excesiva (> 650°C)
        max_brake = max(sample.brake_temps) if sample.brake_temps else 0.0
        if max_brake > 650.0 and self._last_car_alert_key != "brakes_hot":
            self._last_car_alert_key = "brakes_hot"
            self._last_car_state_call_ts = now
            self.last_speech_ts = now
            msg = f"Atención a los frenos: temperatura en {int(max_brake)} grados. Refrigera en la recta o levanta un poco."
            self._broadcast_radio(msg, "alert")
            return

        # 3. Presiones de neumáticos fuera de ventana óptima GT3 (26.6 - 27.2 psi)
        min_p = min(sample.tyre_pressures) if sample.tyre_pressures else 0.0
        max_p = max(sample.tyre_pressures) if sample.tyre_pressures else 0.0
        if min_p > 10.0 and min_p < 25.8 and self._last_car_alert_key != "tyres_cold":
            self._last_car_alert_key = "tyres_cold"
            self._last_car_state_call_ts = now
            self.last_speech_ts = now
            msg = f"Presiones frías: mínima en {round(min_p, 1)} libras. Calienta bien los neumáticos antes de tirar."
            self._broadcast_radio(msg, "alert")
            return

        if max_p > 28.1 and self._last_car_alert_key != "tyres_hot":
            self._last_car_alert_key = "tyres_hot"
            self._last_car_state_call_ts = now
            self.last_speech_ts = now
            msg = f"Presiones altas por sobrecalentamiento: {round(max_p, 1)} libras. Cuida la goma en apoyos largos."
            self._broadcast_radio(msg, "alert")
            return

        # 4. Combustible intermedio y reporte de autonomía en carrera
        if (
            getattr(sample, "realism_fuel_on", getattr(sample, "aid_fuel_rate", 1.0) > 0.05)
            and sample.fuel > 9.0
            and (now - self._last_car_state_call_ts) >= 60.0
            and self._last_car_alert_key != f"fuel_stint_{int(sample.fuel // 8)}"
        ):
            self._last_car_alert_key = f"fuel_stint_{int(sample.fuel // 8)}"
            self._last_car_state_call_ts = now
            self.last_speech_ts = now
            liters = round(sample.fuel, 1)
            msg = f"Reporte de combustible: {liters} litros restantes en el tanque. Autonomía estable para continuar en pista."
            self._broadcast_radio(msg, "car_state")
            return

    def _check_off_track_events(self, sample: TelemetrySample, now: float) -> None:
        """
        Detecta en tiempo real cuando el piloto excede los límites del trazado o se sale de la pista.
        0 = en asfalto, 1-2 = pianos, 3 = tres ruedas fuera (límites), 4 = salida de pista total (grava/hierba).
        Emite aviso prioritario para interrumpir mensajes secundarios y alertar al piloto.
        """
        if sample.is_in_pit or sample.is_in_pit_lane or sample.speed_kmh < 26.0:
            self._is_currently_off_track = False
            return

        tyres_out = getattr(sample, "tyres_out", 0)
        is_off = getattr(sample, "is_off_track", False) or tyres_out >= 3

        if is_off:
            if not self._is_currently_off_track:
                self._is_currently_off_track = True
                self._off_track_start_ts = now

                # Cooldown de 9 segundos para no spamear en la misma excursión
                if (now - self._last_off_track_alert_ts) > 9.0:
                    self._last_off_track_alert_ts = now
                    self.last_speech_ts = now
                    if tyres_out >= 4:
                        msg = "¡Salida de pista completa! Mantén el volante recto y reincorpora con precaución."
                    else:
                        msg = "¡Cuidado, tres ruedas fuera del trazado! Cuidado con los límites de pista."
                    self._broadcast_radio(msg, "alert", priority=True)
        else:
            if self._is_currently_off_track:
                off_dur = now - self._off_track_start_ts
                self._is_currently_off_track = False
                if off_dur > 2.0 and (now - self._last_off_track_alert_ts) > 6.0:
                    self._last_off_track_alert_ts = now
                    self.last_speech_ts = now
                    self._broadcast_radio("De vuelta en el asfalto. Tracción limpia y concéntrate en la siguiente curva.", "coaching")

    def _check_preventative_coaching(self, sample: TelemetrySample, now: float) -> None:
        """
        Evalúa el modo de conducción en carrera y genera tips preventivos proactivos:
        - "Si sigues con este modo de manejo tu consumo de combustible, neumáticos o frenos se degradará..."
        - "Tienes que aumentar el ritmo y perder el miedo"
        - Cuida al usuario y lo ayuda a mejorar su rendimiento.
        """
        if self.voice_mode != "companion":
            return

        # Solo en rectas estables (> 85 km/h, volante casi recto, sin frenar y fuera de curva)
        if (
            self.active_corner is not None
            or sample.speed_kmh < 85.0
            or abs(sample.steer_angle) > 12.0
            or sample.brake > 0.05
            or sample.is_in_pit
            or sample.is_in_pit_lane
        ):
            return

        # Frecuencia evaluativa: cada 38 a 45 segundos
        if (now - self._preventative_coaching_ts) < 40.0 or (now - self.last_speech_ts) < 7.0:
            return

        w = sample.tyre_wear or [3.0, 3.0, 3.0, 3.0]
        front_wear_val = min(w[0], w[1])
        core_temps = sample.tyre_temps_core or [80.0, 80.0, 80.0, 80.0]
        max_tyre_temp = max(core_temps)
        max_brake = max(sample.brake_temps) if sample.brake_temps else 0.0

        tip_text = ""
        category = "coaching"

        # 1. Alerta preventiva de degradación de neumáticos por estrés térmico o fricción
        if max_tyre_temp > 92.5 or (front_wear_val < 2.6 and getattr(sample, "realism_tire_on", getattr(sample, "aid_tire_rate", 1.0) > 0.05)):
            tip_text = (
                "Tip preventivo: Si sigues con este modo de manejo forzando la dirección en las entradas, "
                "el desgaste de tus neumáticos delanteros aumentará más rápido. Modula más suave el freno para rotar el coche y cuidar la goma."
            )
        # 2. Alerta preventiva de degradación de frenos por temperatura alta (> 580°C)
        elif max_brake > 580.0:
            tip_text = (
                f"Tip preventivo: La temperatura de frenos ronda los {int(max_brake)} grados. Si mantienes estas frenadas tan bruscas, "
                "la degradación de frenos se disparará y perderás mordida en las curvas rápidas. Haz un poco de coasting antes del vértice."
            )
        # 3. Alerta preventiva de consumo de combustible excesivo por estirar marchas cortas
        elif sample.gear <= 2 and sample.gas > 0.88 and getattr(sample, "realism_fuel_on", getattr(sample, "aid_fuel_rate", 1.0) > 0.05):
            tip_text = (
                "Tip preventivo: Con este modo de acelerar tan a fondo en marchas bajas, tu consumo de combustible aumentará más de la cuenta. "
                "Sube de marcha antes si queremos llegar con margen al final de la tanda."
            )
        # 4. Falta de ritmo / timidez en paso por curva ("Aumentar el ritmo y perder el miedo")
        elif self.last_corner_result and self.last_corner_result.get("speed_delta_kmh", 0) < -7.0:
            c_name = self.last_corner_result.get("corner_name", "las curvas rápidas")
            options = [
                f"Compañero, en {c_name} tienes que aumentar el ritmo y perder el miedo. La telemetría muestra que el auto tiene agarre de sobra para entrar diez kilómetros por hora más rápido.",
                "Tienes margen en el paso por curva. Confía en el agarre del chasis, aumenta el ritmo y pierde el miedo: el auto va sobre raíles.",
                "Podemos apretar más en los vértices. Suelta el freno con confianza y entra con mayor velocidad; tienes estabilidad absoluta.",
            ]
            idx = int(now) % len(options)
            tip_text = options[idx]
        # 5. Manejo limpio y consistente
        else:
            options = [
                "Tip de telemetría: Con este modo de manejo suave y consistente, la degradación de neumáticos y el consumo de combustible se mantendrán mínimos. Estás cuidando el auto a la perfección.",
                "Ritmo constante y limpio. Mantén este modo de manejo para asegurar una carrera sólida y con degradación controlada.",
            ]
            idx = int(now) % len(options)
            tip_text = options[idx]
            category = "praise"

        # Anti-repetición de tips preventivos
        if tip_text and tip_text not in self._recent_tips[-3:]:
            self._recent_tips.append(tip_text)
            if len(self._recent_tips) > 10:
                self._recent_tips.pop(0)
            self._preventative_coaching_ts = now
            self.last_speech_ts = now
            self._broadcast_radio(tip_text, category)

    def _broadcast_radio(self, text: str, category: str, priority: bool = False) -> None:
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
                self.voice.speak(text, priority=priority)
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

        gemini_ready = bool(self.gemini and self.gemini.is_available)
        model_display = f"Google Gemini 3.5 Flash ({self.gemini.last_model_used})" if (gemini_ready and self.gemini) else "Motor Analítico Local (333 Hz)"
        return {
            "engineer_name": "Álvaro (Ingeniero de Pista IA)",
            "ai_model": model_display,
            "gemini_active": gemini_ready,
            "voice_mode": self.voice_mode,
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

