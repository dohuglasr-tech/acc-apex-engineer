"""
ACC Apex Engineer Pro - Ingeniero de Radio Neural en Español Fluido y Amigable (voice_engineer.py)
Usa síntesis neuronal de alta fidelidad:
  1. Primario: Microsoft Edge Neural TTS (es-ES-AlvaroNeural, cadencia 100% humana y natural)
  2. Secundario: Google Text-to-Speech (gTTS en español nativo)
  3. Memoria caché local para reproducción instantánea (0 ms)
  4. Sanitizador fonético: convierte "2da", "3ra", "T1", "150m" en palabras completas en español.
  5. Desactiva por completo motores SAPI en inglés (Zira/David) para garantizar que jamás hable raro.
"""

from __future__ import annotations

import asyncio
import ctypes
import hashlib
import os
import queue
import re
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
    from gtts import gTTS
except ImportError:
    gTTS = None


def sanitize_spanish_for_speech(text: str) -> str:
    """
    Convierte abreviaturas técnicas, números y ordinales en palabras españolas completas
    para que la voz suene 100% natural, fluida y humana sin fallos de pronunciación.
    """
    if not text:
        return ""

    t = text

    # Reemplazar números ordinales de marchas
    t = re.sub(r"\b1ra\b|\b1ª\b|\b1ro\b", "primera", t, flags=re.IGNORECASE)
    t = re.sub(r"\b2da\b|\b2ª\b|\b2do\b", "segunda", t, flags=re.IGNORECASE)
    t = re.sub(r"\b3ra\b|\b3ª\b|\b3ro\b", "tercera", t, flags=re.IGNORECASE)
    t = re.sub(r"\b4ta\b|\b4ª\b|\b4to\b", "cuarta", t, flags=re.IGNORECASE)
    t = re.sub(r"\b5ta\b|\b5ª\b|\b5to\b", "quinta", t, flags=re.IGNORECASE)
    t = re.sub(r"\b6ta\b|\b6ª\b|\b6to\b", "sexta", t, flags=re.IGNORECASE)

    # Reemplazar referencias de carteles
    t = re.sub(r"\bcartel de 200\b", "cartel de doscientos", t, flags=re.IGNORECASE)
    t = re.sub(r"\bcartel de 150\b", "cartel de ciento cincuenta", t, flags=re.IGNORECASE)
    t = re.sub(r"\bcartel de 100\b", "cartel de cien", t, flags=re.IGNORECASE)
    t = re.sub(r"\bcartel de 50\b", "cartel de cincuenta", t, flags=re.IGNORECASE)
    t = re.sub(r"\ben el 150\b", "en el cartel de ciento cincuenta", t, flags=re.IGNORECASE)
    t = re.sub(r"\ben el 100\b", "en el cartel de cien", t, flags=re.IGNORECASE)
    t = re.sub(r"\ben el 50\b", "en el cartel de cincuenta", t, flags=re.IGNORECASE)

    # Reemplazar identificadores de curvas comunes
    t = re.sub(r"\bT1\b", "curva uno", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT2\b", "curva dos", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT3\b", "curva tres", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT4\b", "curva cuatro", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT5\b", "curva cinco", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT6\b", "curva seis", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT7\b", "curva siete", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT8\b", "curva ocho", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT9\b", "curva nueve", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT10\b", "curva diez", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT11\b", "curva once", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT12\b", "curva doce", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT13\b", "curva trece", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT14\b", "curva catorce", t, flags=re.IGNORECASE)
    t = re.sub(r"\bT15\b", "curva quince", t, flags=re.IGNORECASE)

    # Reemplazar unidades y siglas
    t = re.sub(r"\bkm/h\b|\bkmh\b", "kilómetros por hora", t, flags=re.IGNORECASE)
    t = re.sub(r"\b333\s*hz\b|\b333hz\b", "trescientos treinta y tres hercios", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgt3\b", "ge te tres", t, flags=re.IGNORECASE)
    t = re.sub(r"\btc\b", "control de tracción", t, flags=re.IGNORECASE)
    t = re.sub(r"\babs\b", "a be ese", t, flags=re.IGNORECASE)
    t = re.sub(r"\bpsi\b", "libras", t, flags=re.IGNORECASE)

    # Redondear distancias a palabras limpias
    t = re.sub(r"(\d+)\s*m\b", r"\1 metros", t)

    return t.strip()


def _play_mp3_winmm(file_path: Path) -> bool:
    """Reproduce un archivo MP3 usando la API multimedia nativa de Windows sin abrir reproductores externos."""
    if not file_path.exists() or file_path.stat().st_size < 100:
        return False

    alias = f"apex_rad_{int(time.time() * 1000)}"
    winmm = ctypes.windll.winmm
    buf = ctypes.create_unicode_buffer(256)

    # Abrir archivo MP3
    cmd_open = f'open "{file_path}" type mpegvideo alias {alias}'
    ret = winmm.mciSendStringW(cmd_open, buf, 255, 0)
    if ret != 0:
        return False

    try:
        # Reproducir de forma síncrona
        ret_play = winmm.mciSendStringW(f"play {alias} wait", buf, 255, 0)
        return ret_play == 0
    finally:
        winmm.mciSendStringW(f"close {alias}", buf, 255, 0)


class VoiceEngineer:
    """
    Ingeniero de pista por radio en español 100% fluido, claro y amigable.
    Frases concisas, humanas y comprensibles al instante durante la carrera.
    """

    def __init__(self, enabled: bool = True, voice_name: str = "es-ES-AlvaroNeural") -> None:
        self.enabled = enabled
        self.voice_name = voice_name
        self.speech_rate = "+22%"  # Cadencia enérgica, rápida y profesional de radio F1 (elimina lentitud y monotonía)
        self._queue: "queue.Queue[Optional[str]]" = queue.Queue(maxsize=10)
        self.is_speaking = False
        self.last_spoken_text = ""
        self.last_spoken_ts = 0.0

        # Directorio de caché persistente de audios sintetizados
        self.cache_dir = Path(tempfile.gettempdir()) / "acc_apex_radio_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._thread = threading.Thread(
            target=self._worker, daemon=True, name="VoiceEngineerThread"
        )
        self._thread.start()

    def set_voice(self, voice_name: str) -> None:
        """Permite cambiar la voz de radio (es-ES-AlvaroNeural, es-MX-JorgeNeural, es-ES-ElviraNeural)."""
        if voice_name:
            self.voice_name = voice_name

    def speak(self, message: str, priority: bool = False) -> None:
        if not self.enabled or not message or not message.strip():
            return

        clean_text = sanitize_spanish_for_speech(message)
        if not clean_text:
            return

        # Limpiar mensajes anteriores si es una instrucción prioritaria de frenada
        if priority:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except Exception:
                    break

        try:
            self._queue.put_nowait(clean_text)
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

        # Frases amigables y concisas en español natural
        msg = f"¡Buena vuelta! {minutes} {sec_whole:02d} punto {tenths}. Setup actualizado en garaje."

        if primary_error:
            err_lower = primary_error.lower()
            if "trail-braking" in err_lower or "freno" in err_lower:
                msg += " Suelta el freno más despacio hacia el vértice."
            elif "scrubbing" in err_lower or "dirección" in err_lower:
                msg += " Cuida las gomas delanteras, gira menos el volante."
            elif "tracción" in err_lower or "tc" in err_lower:
                msg += " Espera a enderezar antes de pisar a fondo."

        self.speak(msg)

    async def _synthesize_edge_neural(self, text: str, out_path: Path) -> bool:
        """Síntesis con Microsoft Edge Neural TTS en español fluido, rápido y natural."""
        if edge_tts is None:
            return False
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice_name,
                rate=self.speech_rate,
                pitch="+0Hz",
            )
            await asyncio.wait_for(communicate.save(str(out_path)), timeout=4.5)
            return out_path.exists() and out_path.stat().st_size > 256
        except Exception:
            return False

    def _synthesize_gtts(self, text: str, out_path: Path) -> bool:
        """Síntesis de respaldo con Google Text-to-Speech en español nativo."""
        if gTTS is None:
            return False
        try:
            tts = gTTS(text=text, lang="es", tld="es")
            tts.save(str(out_path))
            return out_path.exists() and out_path.stat().st_size > 256
        except Exception:
            return False

    def _get_cache_path(self, text: str) -> Path:
        """Devuelve una ruta en caché basada en el hash del texto, voz y cadencia."""
        cache_key = f"{self.voice_name}_{self.speech_rate}_{text.strip()}"
        h = hashlib.md5(cache_key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"voice_{h}.mp3"

    def _worker(self) -> None:
        while True:
            text = self._queue.get()
            if text is None:
                break
            if not self.enabled or not text.strip():
                continue

            self.is_speaking = True
            self.last_spoken_text = text
            self.last_spoken_ts = time.time()

            cached_mp3 = self._get_cache_path(text)
            played = False

            # 1. Si ya está en caché, reproducir de inmediato (cero latencia)
            if cached_mp3.exists() and cached_mp3.stat().st_size > 256:
                try:
                    played = _play_mp3_winmm(cached_mp3)
                except Exception:
                    played = False

            # 2. Si no estaba en caché, sintetizar con Microsoft Edge Neural TTS
            if not played:
                try:
                    ok_neural = asyncio.run(self._synthesize_edge_neural(text, cached_mp3))
                    if ok_neural:
                        played = _play_mp3_winmm(cached_mp3)
                except Exception:
                    played = False

            # 3. Si Edge Neural falló, usar Google TTS en español nativo (0.5s de síntesis)
            if not played:
                try:
                    ok_gtts = self._synthesize_gtts(text, cached_mp3)
                    if ok_gtts:
                        played = _play_mp3_winmm(cached_mp3)
                except Exception:
                    played = False

            self.is_speaking = False

    def stop(self) -> None:
        try:
            self._queue.put_nowait(None)
        except Exception:
            pass
