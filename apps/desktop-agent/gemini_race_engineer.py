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
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
]

GEMINI_SYSTEM_INSTRUCTION = """
Eres Álvaro, el Jefe e Ingeniero de Pista de Carrera (Race Engineer) de élite estilo F1 y WEC (como Bono o GP) para un piloto en Assetto Corsa Competizione (ACC).
Te comunicas con él exclusivamente por la RADIO DEL EQUIPO durante la sesión en pista.

REGLAS DE COMUNICACIÓN POR RADIO:
1. Habla en ESPAÑOL fluido, amigable, respetuoso pero enérgico, técnico y enfocado en ganar décimas (100% natural, como en la F1 real).
2. TUS TRANSMISIONES DEBEN SER BREVES Y DIRECTAS:
   - Durante la vuelta / frenada: 1 frase corta y clara (máximo 14 palabras) para no desconcentrar al piloto a alta velocidad.
   - Resumen al cruzar la meta: 2 frases rápidas informando el tiempo/delta, el setup creado en garaje para boxes y el consejo de manejo.
3. Sé analítico con el mando: cuando veas sobreviraje, bloqueo o subviraje, aconseja sobre la suavidad del stick analógico y el recorrido de los gatillos.
4. Jamás uses emoticonos, asteriscos, comillas ni formato markdown en los mensajes de radio (se reproducirán directamente por voz).
5. Usa números en palabras cuando sea más fácil de pronunciar ("cien metros", "segunda marcha", "dos veintiséis").
6. REGLA FUNDAMENTAL DE SETUPS (ASSETTO CORSA COMPETIZIONE):
   El simulador ACC NO permite montar ni cambiar setups en pista mientras se conduce.
   El sistema de ingeniería genera el setup en el garaje en 3 ranuras rotativas: APEX_SETUP_1, APEX_SETUP_2 o APEX_SETUP_3.
   JAMÁS digas "setup montado", "setup inyectado en el coche" ni "setup aplicado automáticamente".
   Debes decirle al piloto:
   a) Que has creado y guardado el setup en su garaje (por ejemplo: "He creado el setup APEX SETUP 1 en tu garaje").
   b) Que fue adaptado a su modo de manejo (mando o volante), a las condiciones de pista (temperatura de asfalto/clima) y a su telemetría.
   c) Que lo cargue manualmente en el menú de garaje cuando entre a boxes.
"""


class GeminiRaceEngineer:
    """
    Cerebro de Inteligencia Artificial para el Ingeniero de Pista usando Google Gemini.
    Genera transmisiones de radio inteligentes y adaptativas basadas en la telemetría en vivo.
    """

    def __init__(self, api_key: str = "", model_name: str = "gemini-3.1-flash-lite") -> None:
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

            max_tok = 95 if event_type == "lap_summary" else 50
            for model in [self.model_name] + [m for m in SUPPORTED_MODELS if m != self.model_name]:
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=GEMINI_SYSTEM_INSTRUCTION,
                            temperature=0.7,
                            max_output_tokens=max_tok,
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
                f"El piloto va a {int(speed)} km/h aproximándose a {corner} en {track} (a {dist} metros). "
                f"Referencia de frenada: {marker}, marcha: {gear}ª. Conduce con: {ctx.get('input_mode', 'mando')}. "
                f"Cántale la curva por radio con 1 sola orden breve, urgente y natural (máximo 12 palabras)."
            )
        elif event_type == "corner_exit":
            score = ctx.get("score", 85)
            speed_delta = ctx.get("speed_delta", 0)
            return (
                f"El piloto salió de {corner} en {track}. Puntuación: {score}/100. "
                f"Delta de velocidad: {speed_delta:+.1f} km/h. Conduce con: {ctx.get('input_mode', 'mando')}. "
                f"Error observado: {error or 'ninguno, trazada perfecta'}. "
                f"Dale 1 consejo constructivo o felicitación por radio en 1 sola frase corta (máximo 14 palabras)."
            )
        elif event_type == "lap_summary":
            delta_str = ctx.get("delta_str", "")
            tyres = ctx.get("tyre_wear_pct", "")
            slot_name = ctx.get("slot_name", f"APEX_SETUP_{((setup_ver - 1) % 3) + 1}")
            input_mode_es = ctx.get("input_mode_es", "mando")
            track_cond = ctx.get("track_cond", "condiciones de pista")
            setup_reason = ctx.get("setup_reason", "calibración térmica y estabilidad")
            return (
                f"El piloto completó vuelta en {track} con tiempo {lap_time} ({delta_str}). "
                f"Desgaste de gomas: {tyres}. Condiciones de pista: {track_cond}. Periférico: {input_mode_es}. "
                f"Has creado y guardado en su garaje el setup '{slot_name}' adaptado a su {input_mode_es}, a los {track_cond} y a su telemetría ({setup_reason}). "
                f"Comunícale por radio como ingeniero de pista de F1 (en 2 frases enérgicas, profesionales y directas): "
                f"1) Su tiempo y si mejoró o no ({delta_str}). "
                f"2) Que le creaste '{slot_name}' en su garaje adaptado a su {input_mode_es} y a la pista, y que lo cargue cuando entre a boxes."
            )
        elif event_type == "car_alert":
            alert = ctx.get("alert_reason", "presiones")
            return (
                f"Alerta en pista: {alert}. Comunícalo en 1 frase corta y profesional de radio."
            )
        return ""
