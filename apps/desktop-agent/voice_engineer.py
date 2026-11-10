"""
ACC Apex Engineer Pro - Ingeniero de Radio Neural (voice_engineer.py)
Usa síntesis neuronal natural (Microsoft Edge Neural TTS: es-ES-AlvaroNeural)
reproducida mediante MCI nativo de Windows (winmm.dll) sin abrir reproductores externos.
Solo transmite mensajes cortos y precisos de ingeniero de pista cuando ACC está activo.
"""

from __future__ import annotations

import asyncio
import ctypes
import os
import queue
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


def _play_mp3_winmm(file_path: Path) -> None:
    """Reproduce un archivo MP3 de forma síncrona usando la API nativa winmm.dll de Windows."""
    alias = f"apex_radio_{int(time.time() * 1000)}"
    winmm = ctypes.windll.winmm
    buf = ctypes.create_unicode_buffer(256)

    cmd_open = f'open "{file_path}" type mpegvideo alias {alias}'
    if winmm.mciSendStringW(cmd_open, buf, 255, 0) != 0:
        return
    try:
        winmm.mciSendStringW(f"play {alias} wait", buf, 255, 0)
    finally:
        winmm.mciSendStringW(f"close {alias}", buf, 255, 0)


class VoiceEngineer:
    """
    Ingeniero de pista por radio con voz neuronal humana (es-ES-AlvaroNeural).
    Frases concisas estilo F1/GT3; nunca habla si el juego no está en sesión activa.
    """

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._queue: "queue.Queue[Optional[str]]" = queue.Queue(maxsize=8)
        self._thread = threading.Thread(
            target=self._worker, daemon=True, name="VoiceEngineerThread"
        )
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
        if not self.enabled or lap_time_ms <= 0:
            return

        minutes = lap_time_ms // 60000
        seconds = (lap_time_ms % 60000) / 1000.0
        sec_whole = int(seconds)
        tenths = int((seconds - sec_whole) * 10)

        msg = f"Vuelta en {minutes} {sec_whole:02d} punto {tenths}. Setup actualizado en garaje."

        if primary_error:
            err_lower = primary_error.lower()
            if "trail-braking" in err_lower or "freno" in err_lower:
                msg += " Suelta el freno más progresivo al entrar al vértice."
            elif "scrubbing" in err_lower or "dirección" in err_lower:
                msg += " Cuida las gomas delanteras, no sobre-gires en mitad de curva."
            elif "tracción" in err_lower or "tc" in err_lower:
                msg += " Espera a enderezar antes de dar gas a fondo."

        self.speak(msg)

    async def _synthesize_neural(self, text: str, out_path: Path) -> bool:
        if edge_tts is None:
            return False
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice="es-ES-AlvaroNeural",
                rate="+5%",
                pitch="-2Hz",
            )
            await communicate.save(str(out_path))
            return out_path.exists() and out_path.stat().st_size > 256
        except Exception:
            return False

    def _worker(self) -> None:
        fallback_engine = None
        tmp_dir = Path(tempfile.gettempdir()) / "acc_apex_radio"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        while True:
            text = self._queue.get()
            if text is None:
                break
            if not self.enabled:
                continue

            mp3_file = tmp_dir / f"radio_{int(time.time() * 1000)}.mp3"
            played_neural = False
            if edge_tts is not None:
                try:
                    played_neural = asyncio.run(self._synthesize_neural(text, mp3_file))
                    if played_neural:
                        _play_mp3_winmm(mp3_file)
                except Exception:
                    played_neural = False
                finally:
                    try:
                        if mp3_file.exists():
                            os.remove(mp3_file)
                    except Exception:
                        pass

            if not played_neural and pyttsx3 is not None:
                try:
                    if fallback_engine is None:
                        fallback_engine = pyttsx3.init()
                        fallback_engine.setProperty("rate", 178)
                        fallback_engine.setProperty("volume", 0.9)
                    fallback_engine.say(text)
                    fallback_engine.runAndWait()
                except Exception:
                    pass

    def stop(self) -> None:
        try:
            self._queue.put_nowait(None)
        except Exception:
            pass
