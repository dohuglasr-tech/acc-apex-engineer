"""
ACC Apex Engineer Pro - Ingeniero de Pista por Voz en Español (voice_engineer.py)
Canta tiempos de vuelta, errores críticos detectados y confirma cuando el Auto-Inyector
actualiza APEX_AUTO_LIVE.json en Documents\\Assetto Corsa Competizione\\Setups.
Ejecuta en un hilo secundario dedicado sin bloquear jamás la lectura a 333 Hz.
"""

from __future__ import annotations

import queue
import threading
from typing import Optional

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


class VoiceEngineer:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._queue: "queue.Queue[Optional[str]]" = queue.Queue(maxsize=15)
        self._thread = threading.Thread(target=self._worker, daemon=True, name="VoiceEngineerThread")
        self._thread.start()

    def speak(self, message: str) -> None:
        if not self.enabled or not message:
            return
        try:
            self._queue.put_nowait(message)
        except queue.Full:
            pass

    def announce_lap_and_setup(
        self,
        lap_number: int,
        lap_time_ms: int,
        version_num: int,
        primary_error: Optional[str],
        input_mode: str,
    ) -> None:
        minutes = lap_time_ms // 60000
        seconds = (lap_time_ms % 60000) / 1000.0
        mode_es = {"keyboard": "teclado", "gamepad": "mando", "wheel": "volante"}.get(input_mode, input_mode)
        msg = (
            f"Vuelta {lap_number} completada en {minutes} minuto {seconds:.1f} segundos. "
            f"Setup automático versión {version_num} para {mode_es} inyectado en tu carpeta de Assetto Corsa Competizione."
        )
        if primary_error:
            msg += f" Atención en pista: {primary_error}."
        self.speak(msg)

    def _worker(self) -> None:
        engine = None
        if pyttsx3 is not None:
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", 185)
                engine.setProperty("volume", 0.92)
                # Intentar seleccionar voz en español si está instalada en Windows
                voices = engine.getProperty("voices") or []
                for v in voices:
                    v_id = (getattr(v, "id", "") or "").lower()
                    v_name = (getattr(v, "name", "") or "").lower()
                    if "spanish" in v_name or "español" in v_name or "es-" in v_id or "es_" in v_id or "helena" in v_name or "sabina" in v_name:
                        engine.setProperty("voice", v.id)
                        break
            except Exception:
                engine = None

        while True:
            text = self._queue.get()
            if text is None:
                break
            if engine is not None:
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception:
                    pass

    def stop(self) -> None:
        try:
            self._queue.put_nowait(None)
        except Exception:
            pass
