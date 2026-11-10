"""
ACC Apex Engineer Pro - Ingeniero de Pista IA con Google Gemini (gemini_race_engineer.py)
Integra la inteligencia de última generación de Google Gemini (gemini-2.0-flash / gemini-1.5-flash)
para generar comentarios de radio, diagnósticos de curva y análisis de setup
con el vocabulario, la cadencia y la personalidad de un Ingeniero de Pista de F1 / WEC en español.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore


GEMINI_SYSTEM_INSTRUCTION = """
Eres Álvaro, el Jefe e Ingeniero de Pista de Carrera (Race Engineer) de élite estilo F1 y WEC (como Bono o GP) para un piloto que conduce en Assetto Corsa Competizione (ACC).
Tu piloto está conduciendo un GT3 en pista y te comunicas con él por la RADIO DEL EQUIPO en tiempo real.

REGLAS DE COMUNICACIÓN POR RADIO:
1. Habla en ESPAÑOL fluido, amigable, respetuoso pero enérgico y enfocado en el rendimiento (100% natural, sin sonar como robot).
2. TUS TRANSMISIONES DEBEN SER BREVES Y CONCISAS:
   - Durante la vuelta / aproximación a curvas: 1 frase corta y directa (máximo 15-20 palabras) porque el piloto va a más de 200 km/h.
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

    def __init__(self, api_key: str = "", model_name: str = "gemini-2.0-flash") -> None:
        self.api_key = api_key.strip() or os.environ.get("GEMINI_API_KEY", "").strip()
        self.model_name = model_name
        self.client: Optional[Any] = None
        self._is_ready = False
        self._last_call_ts = 0.0

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
            return True
        except Exception:
            self.client = None
            self._is_ready = False
            return False

    @property
    def is_available(self) -> bool:
        return self._is_ready and self.client is not None

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
            if (now - self._last_call_ts) < 2.0:
                return
            self._last_call_ts = now

            prompt = self._build_prompt(event_type, context)
            if not prompt:
                return

            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=GEMINI_SYSTEM_INSTRUCTION,
                        temperature=0.7,
                        max_output_tokens=60,
                    ),
                )
                text = (response.text or "").strip()
                # Limpiar comillas o formato que Gemini pudiera agregar
                text = text.replace('"', "").replace("'", "").strip()
                if text and on_ready:
                    category = "anticipation" if event_type == "anticipation" else "coaching"
                    if event_type == "car_alert":
                        category = "alert"
                    elif event_type == "lap_summary":
                        category = "praise"
                    on_ready(text, category)
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True, name="GeminiRadioWorker").start()

    def _build_prompt(self, event_type: str, ctx: Dict[str, Any]) -> str:
        track = ctx.get("track_name", "Circuito")
        car = ctx.get("car_model", "GT3")
        corner = ctx.get("corner_name", "")
        dist = ctx.get("distance_m", 150)
        speed = ctx.get("speed_kmh", 0)
        gear = ctx.get("gear", 0)
        lap_time = ctx.get("lap_time_str", "")
        error = ctx.get("primary_error", "")
        setup_ver = ctx.get("setup_version", 1)

        if event_type == "anticipation":
            return (
                f"El piloto está en {track} con el {car}. Se aproxima a {corner} a {dist} metros, "
                f"velocidad actual {int(speed)} km/h. La marcha sugerida es {gear}ª marcha. "
                f"Dale una orden preventiva de radio de F1 corta y amigable diciéndole cuándo frenar y qué marcha meter."
            )
        elif event_type == "corner_exit":
            score = ctx.get("score", 85)
            speed_delta = ctx.get("speed_delta", 0)
            return (
                f"El piloto acaba de salir de {corner} en {track}. Puntuación de trazada: {score}/100. "
                f"Delta de velocidad en vértice: {speed_delta} km/h. Detalle: {error or 'paso limpio'}. "
                f"Dale un consejo amigable de 1 sola frase rápida por radio para mejorar la próxima vez o felicítalo si lo hizo perfecto."
            )
        elif event_type == "lap_summary":
            return (
                f"El piloto acaba de completar una vuelta en {track} con tiempo {lap_time}. "
                f"Se auto-inyectó el setup versión {setup_ver} en ACC. Error principal observado: {error or 'ninguno'}. "
                f"Dale un informe de radio de 1 a 2 frases enérgico, claro y amigable."
            )
        elif event_type == "car_alert":
            alert = ctx.get("alert_reason", "presiones")
            return (
                f"El coche tiene una alerta técnica en pista: {alert}. "
                f"Comunícalo por radio de forma calmada, profesional y preventiva en 1 frase corta."
            )
        return ""
