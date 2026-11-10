"""
ACC Apex Engineer Pro - Ingeniero de Pista IA con Google Gemini (gemini_race_engineer.py)
Integra la inteligencia de última generación de Google Gemini (gemini-3.5-flash-lite / gemini-3.8-flash)
para generar comentarios de radio, diagnósticos de curva y análisis de setup
con el vocabulario, la cadencia y la personalidad de un Ingeniero de Pista de F1 / WEC en español.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore


DEFAULT_GEMINI_KEY = ""
SUPPORTED_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
]

GEMINI_SYSTEM_INSTRUCTION = """
Eres Álvaro, el Jefe e Ingeniero de Pista de Carrera (Race Engineer) de élite estilo F1 y WEC (como Bono o GP) para un piloto que conduce en Assetto Corsa Competizione (ACC).
Tu piloto está conduciendo un GT3 en pista y te comunicas con él por la RADIO DEL EQUIPO en tiempo real.

REGLAS DE COMUNICACIÓN POR RADIO:
1. Habla en ESPAÑOL fluido, amigable, respetuoso pero enérgico y enfocado en el rendimiento (100% natural, sin sonar como robot).
2. TUS TRANSMISIONES DEBEN SER BREVES Y CONCISAS:
   - Durante la vuelta / aproximación a curvas: 1 frase corta y directa (máximo 12-16 palabras) porque el piloto va a más de 200 km/h.
   - Resumen al cruzar la meta: 1 o 2 frases rápidas con el tiempo y el cambio de setup.
3. Sé predictivo y analítico: menciona referencias de frenada ("cartel de 100", "frena antes de la línea blanca"), marchas ("baja a 2ª", "sal en 3ª para traccionar") y estado del coche.
4. Jamás uses emoticonos, asteriscos ni formato markdown en los mensajes de radio (se reproducirán directamente por voz).
5. Usa números en palabras cuando sea más fácil de pronunciar ("cien metros", "segunda marcha").
"""


class GeminiRaceEngineer:
    """
    Cerebro de Inteligencia Artificial para el Ingeniero de Pista usando Google Gemini.
    Genera transmisiones de radio inteligentes y adaptativas basadas en la telemetría en vivo.
    """

    def __init__(self, api_key: str = "", model_name: str = "gemini-3.5-flash-lite") -> None:
        self.api_key = (api_key or os.environ.get("GEMINI_API_KEY", "") or DEFAULT_GEMINI_KEY).strip()
        self.model_name = model_name
        self.client: Optional[Any] = None
        self._is_ready = False
        self._last_call_ts = 0.0
        self.last_model_used = model_name
        self.last_error = ""

        if self.api_key and genai is not None:
            self._init_client()

    def set_api_key(self, api_key: str) -> bool:
        self.api_key = api_key.strip()
        return self._init_client()

    def _init_client(self) -> bool:
        if not self.api_key or genai is None:
            self.client = None
            self._is_ready = False
            return False
        try:
            self.client = genai.Client(api_key=self.api_key)
            self._is_ready = True
            self.last_error = ""
            return True
        except Exception as e:
            self.client = None
            self._is_ready = False
            self.last_error = str(e)
            return False

    @property
    def is_available(self) -> bool:
        return self._is_ready and self.client is not None

    def test_connection(self) -> Tuple[bool, str]:
        """
        Prueba la conexión real contra Google Gemini generando un saludo de radio en vivo.
        Retorna (True, texto_saludo) o (False, error).
        """
        if not self.is_available:
            ok = self._init_client()
            if not ok:
                return False, f"No se pudo inicializar el cliente: {self.last_error or 'Clave no configurada'}"

        for model in SUPPORTED_MODELS:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents="Eres Álvaro por la radio del equipo en Assetto Corsa Competizione. Di una sola frase corta de prueba diciendo que la radio está conectada.",
                    config=types.GenerateContentConfig(
                        system_instruction=GEMINI_SYSTEM_INSTRUCTION,
                        temperature=0.7,
                        max_output_tokens=40,
                    ),
                )
                text = (response.text or "").strip().replace('"', "").replace("'", "")
                if text:
                    self.model_name = model
                    self.last_model_used = model
                    self._is_ready = True
                    return True, text
            except Exception as e:
                self.last_error = str(e)
                continue

        return False, f"Error al generar con Gemini: {self.last_error}"

    def generate_radio_advice_async(
        self,
        event_type: str,
        context: Dict[str, Any],
        on_ready: Callable[[str, str], None],
    ) -> None:
        """
        Genera una instrucción de radio con Google Gemini en un hilo asíncrono.
        `event_type`: "anticipation", "corner_exit", "car_alert", "lap_summary"
        `context`: telemetría, pista, coche, velocidad, delta, etc.
        `on_ready(text, category)`: callback cuando Gemini genera la respuesta.
        """
        if not self.is_available:
            return

        def _worker() -> None:
            now = time.time()
            # En anticipación permitimos disparo rápido cada 1.5s; en otros eventos cada 2.5s
            min_interval = 1.5 if event_type == "anticipation" else 2.5
            if (now - self._last_call_ts) < min_interval:
                return
            self._last_call_ts = now

            prompt = self._build_prompt(event_type, context)
            if not prompt:
                return

            for model in [self.model_name] + [m for m in SUPPORTED_MODELS if m != self.model_name]:
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=GEMINI_SYSTEM_INSTRUCTION,
                            temperature=0.7,
                            max_output_tokens=50,
                        ),
                    )
                    text = (response.text or "").strip()
                    text = text.replace('"', "").replace("'", "").strip()
                    if text and on_ready:
                        self.model_name = model
                        self.last_model_used = model
                        category = "anticipation" if event_type == "anticipation" else "coaching"
                        if event_type == "car_alert":
                            category = "alert"
                        elif event_type == "lap_summary":
                            category = "praise"
                        on_ready(text, category)
                        break
                except Exception as e:
                    self.last_error = str(e)
                    continue

        threading.Thread(target=_worker, daemon=True, name="GeminiRadioWorker").start()

    def _build_prompt(self, event_type: str, ctx: Dict[str, Any]) -> str:
        track = ctx.get("track_name", "Circuito")
        car = ctx.get("car_model", "GT3")
        corner = ctx.get("corner_name", "")
        dist = ctx.get("distance_m", 350)
        speed = ctx.get("speed_kmh", 0)
        gear = ctx.get("gear", 0)
        lap_time = ctx.get("lap_time_str", "")
        error = ctx.get("primary_error", "")
        setup_ver = ctx.get("setup_version", 1)

        if event_type == "anticipation":
            marker = ctx.get("braking_marker", "cartel de 100")
            return (
                f"El piloto va a {int(speed)} km/h en la recta aproximándose a {corner} en {track} (a {dist} metros). "
                f"Referencia de frenada: {marker}, marcha sugerida: {gear}ª. "
                f"Cántale la curva por radio con 1 sola orden breve, urgente y natural (máximo 12 palabras)."
            )
        elif event_type == "corner_exit":
            score = ctx.get("score", 85)
            speed_delta = ctx.get("speed_delta", 0)
            return (
                f"El piloto acaba de salir de {corner} en {track}. Puntuación: {score}/100. "
                f"Delta de velocidad en vértice: {speed_delta:+.1f} km/h. Error observado: {error or 'ninguno, paso perfecto'}. "
                f"Dale 1 consejo rápido o felicitación por radio en 1 sola frase corta."
            )
        elif event_type == "lap_summary":
            return (
                f"Vuelta completada en {track} con tiempo {lap_time}. Se inyectó setup versión {setup_ver}. "
                f"Comportamiento del piloto: {error or 'vuelta sólida'}. "
                f"Dale un informe de meta por radio en 1 frase enérgica y amigable."
            )
        elif event_type == "car_alert":
            alert = ctx.get("alert_reason", "presiones")
            return (
                f"Alerta en pista: {alert}. Comunícalo en 1 frase corta y profesional de radio."
            )
        return ""
