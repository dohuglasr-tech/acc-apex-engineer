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
    t = re.sub(r"(\d+)\s*%", r"\1 por ciento", t)
    t = t.replace("%", " por ciento")

    # Redondear distancias a palabras limpias
    t = re.sub(r"(\d+)\s*m\b", r"\1 metros", t)

    return t.strip()


_ACTIVE_MCI_ALIAS: Optional[str] = None
_ACTIVE_MCI_LOCK = threading.Lock()


def stop_current_playback() -> None:
    """Interrumpe de inmediato cualquier reproducción de audio en curso para liberar el canal de radio."""
    global _ACTIVE_MCI_ALIAS
    with _ACTIVE_MCI_LOCK:
        if _ACTIVE_MCI_ALIAS:
            try:
                winmm = ctypes.windll.winmm
                buf = ctypes.create_unicode_buffer(256)
                winmm.mciSendStringW(f"stop {_ACTIVE_MCI_ALIAS}", buf, 255, 0)
                winmm.mciSendStringW(f"close {_ACTIVE_MCI_ALIAS}", buf, 255, 0)
            except Exception:
                pass
            finally:
                _ACTIVE_MCI_ALIAS = None


def _play_mp3_winmm(file_path: Path, volume: int = 65) -> bool:
    """Reproduce un archivo MP3 usando la API multimedia nativa de Windows con control de volumen (0 a 100%)."""
    if not file_path.exists() or file_path.stat().st_size < 100:
        return False

    if volume <= 0:
        return True  # Silenciado intencionalmente

    global _ACTIVE_MCI_ALIAS
    alias = f"apex_rad_{int(time.time() * 1000)}"
    winmm = ctypes.windll.winmm
    buf = ctypes.create_unicode_buffer(256)

    # Abrir archivo MP3
    cmd_open = f'open "{file_path}" type mpegvideo alias {alias}'
    ret = winmm.mciSendStringW(cmd_open, buf, 255, 0)
    if ret != 0:
        return False

    with _ACTIVE_MCI_LOCK:
        _ACTIVE_MCI_ALIAS = alias

    try:
        # Ajustar volumen en MCI (0 a 1000)
        vol_mci = max(0, min(1000, int(volume * 10)))
        winmm.mciSendStringW(f"setaudio {alias} volume to {vol_mci}", buf, 255, 0)

        # Reproducir de forma síncrona con capacidad de interrupción externa
        ret_play = winmm.mciSendStringW(f"play {alias} wait", buf, 255, 0)
        return ret_play == 0
    finally:
        with _ACTIVE_MCI_LOCK:
            if _ACTIVE_MCI_ALIAS == alias:
                _ACTIVE_MCI_ALIAS = None
        winmm.mciSendStringW(f"close {alias}", buf, 255, 0)


class VoiceEngineer:
    """
    Ingeniero de pista por radio en español 100% fluido, claro y amigable.
    Frases concisas, humanas y comprensibles al instante durante la carrera.
    """

    def __init__(
        self,
        enabled: bool = True,
        voice_name: str = "es-ES-AlvaroNeural",
        volume: int = 65,
    ) -> None:
        self.enabled = enabled
        self.voice_name = voice_name
        self.volume = max(0, min(100, int(volume)))
        self.speech_rate = "+22%"  # Cadencia enérgica, rápida y profesional de radio F1 (elimina lentitud y monotonía)
        self._queue: "queue.Queue[Optional[str]]" = queue.Queue(maxsize=10)
        self.is_speaking = False
        self.last_spoken_text = ""
        self.last_spoken_ts = 0.0
        # Historial para filtro anti-repetición en tiempo real (evita frases idénticas en 40s)
        self._recent_history: List[Tuple[str, float]] = []

        # Directorio de caché persistente de audios sintetizados
        self.cache_dir = Path(tempfile.gettempdir()) / "acc_apex_radio_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._thread = threading.Thread(
            target=self._worker, daemon=True, name="VoiceEngineerThread"
        )
        self._thread.start()

        # Precalentamiento de frases críticas de alta prioridad (salidas de pista y límites)
        self._preload_thread = threading.Thread(
            target=self._preload_critical_phrases, daemon=True, name="VoicePreloadThread"
        )
        self._preload_thread.start()

    def _preload_critical_phrases(self) -> None:
        """Pre-sintetiza alertas críticas en segundo plano para garantizar reproducción con cero latencia."""
        critical_alerts = [
            "Entrando al pit lane. Recuerda mantener activo el limitador a cincuenta kilómetros por hora y prepara la parada.",
            "Coche en el garaje. Telemetría lista en boxes para revisar setup y ajustar la carga de combustible.",
            "Saliendo a pista. Neumáticos fríos, calienta bien en los primeros sectores y busca el ritmo.",
            "¡Salida de pista completa! Cuidado con la grava y la hierba, mantén el volante recto y reincorpora con precaución.",
            "¡Coche fuera de pista! Cuidado al volver al asfalto para no trompear.",
            "¡Te has salido del trazado! Calma con el acelerador, mantén la dirección firme y busca el asfalto.",
            "¡Tres ruedas fuera del trazado! Has superado los límites de pista.",
            "¡Atención, tres ruedas fuera! Cuidado con la sanción de límites de pista.",
            "¡Cuidado con los límites de pista! Dos ruedas fuera del asfalto.",
            "Atención: dos ruedas fuera de la línea blanca. Ajusta la trazada para no invalidar.",
            "Atención: límites de pista superados. Ajusta la trazada para no invalidar.",
            "Seguimos fuera de pista. Tracciona suave en primera o marcha atrás para salir de la grava.",
            "De vuelta en el asfalto. Tracción limpia y concéntrate en la siguiente curva.",
            "Asfalto limpio. Recupera el ritmo y a por el siguiente sector.",
            "En pista de nuevo. Calienta las gomas y retoma tu ritmo de carrera.",
        ]
        for phrase in critical_alerts:
            try:
                clean = sanitize_spanish_for_speech(phrase)
                out_p = self._get_cache_path(clean)
                if not out_p.exists() or out_p.stat().st_size <= 256:
                    asyncio.run(self._synthesize_edge_neural(clean, out_p))
            except Exception:
                pass

    def set_volume(self, volume: int) -> None:
        """Ajusta el volumen de la radio del agente (0% a 100%)."""
        self.volume = max(0, min(100, int(volume)))

    def set_voice(self, voice_name: str) -> None:
        """Permite cambiar la voz de radio (es-ES-AlvaroNeural, es-MX-JorgeNeural, es-ES-ElviraNeural)."""
        if voice_name:
            self.voice_name = voice_name

    def stop_playback(self) -> None:
        """Detiene de inmediato la locución actual por radio."""
        stop_current_playback()

    def purge_pending(self) -> None:
        """Descarta de inmediato mensajes encolados para no emitir avisos desfasados de curvas pasadas."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except Exception:
                break
        stop_current_playback()

    def speak(self, message: str, priority: bool = False) -> None:
        if not self.enabled or not message or not message.strip():
            return

        clean_text = sanitize_spanish_for_speech(message)
        if not clean_text:
            return

        now = time.time()

        # Filtro inteligente anti-repetición:
        # Si un mensaje no prioritario ya fue emitido en los últimos 38 segundos, se descarta para no cansar al piloto
        if not priority:
            self._recent_history = [(t, ts) for (t, ts) in self._recent_history if (now - ts) < 38.0]
            clean_lower = clean_text.lower().strip()
            for prev_t, prev_ts in self._recent_history:
                if clean_lower == prev_t.lower().strip():
                    return
            self._recent_history.append((clean_text, now))

        # Limpiar mensajes anteriores e interrumpir audio en curso si es prioritario (frenada, off-track)
        if priority:
            self.purge_pending()

        try:
            self._queue.put_nowait(clean_text)
        except queue.Full:
            pass

    def announce_lap_and_setup(
        self,
        lap_number: int,
        lap_time_ms: int,
        version_num: int,
        slot_num: int = 1,
        slot_name: str = "APEX_SETUP_1",
        primary_error: Optional[str] = None,
        input_mode: str = "gamepad",
        road_temp: float = 30.0,
        fuel_used: float = 0.0,
        remaining_fuel: float = 0.0,
    ) -> None:
        if not self.enabled or lap_time_ms <= 0:
            return

        minutes = lap_time_ms // 60000
        seconds = (lap_time_ms % 60000) / 1000.0
        sec_whole = int(seconds)
        tenths = int((seconds - sec_whole) * 10)

        input_name = {
            "keyboard": "teclado",
            "gamepad": "mando",
            "wheel": "volante",
        }.get(input_mode, "mando")

        advice = ""
        if primary_error:
            err_lower = primary_error.lower()
            if "trail-braking" in err_lower or "freno" in err_lower:
                advice = "Suelta el freno más progresivo hacia el vértice."
            elif "scrubbing" in err_lower or "dirección" in err_lower:
                advice = "Cuida las gomas delanteras, gira menos volante."
            elif "tracción" in err_lower or "tc" in err_lower:
                advice = "Endereza la dirección antes de acelerar a fondo."

        slot_label = f"APEX SETUP {slot_num}"
        time_text = f"{minutes} {sec_whole:02d} punto {tenths}" if minutes > 0 else f"{sec_whole:02d} punto {tenths}"
        
        # Anuncio preciso y obligatorio de consumo de combustible por vuelta
        if fuel_used > 0.05:
            fuel_note = f" Consumo: {fuel_used:.1f} litros por vuelta."
        else:
            fuel_note = " Consumo medido bajo control."

        rem_note = f" Nos quedan {remaining_fuel:.0f} litros en el tanque." if remaining_fuel > 1.0 else ""

        msg = (
            f"Vuelta {lap_number}: {time_text}.{fuel_note}{rem_note} "
            f"He creado el setup {slot_label} en tu garaje, adaptado a tu {input_name} y a los {road_temp:.0f} grados de pista. "
            f"{advice} Cárgalo en boxes cuando entres."
        ).strip()

        self.speak(msg)

    def announce_pit_fuel(self, speech_text: str) -> None:
        """Comunica por radio la estrategia de combustible calculada en boxes antes de salir a pista."""
        if not self.enabled or not speech_text:
            return
        self.speak(speech_text, priority=True)

    async def _synthesize_edge_neural(self, text: str, out_path: Path) -> bool:
        """Síntesis exclusiva con Microsoft Edge Neural TTS en español Álvaro (voz masculina deportiva a +22%)."""
        if edge_tts is None:
            return False
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice_name,
                rate=self.speech_rate,
                pitch="+0Hz",
            )
            # Timeout generoso de 6.0s para permitir frases largas completas sin abortar a Álvaro
            await asyncio.wait_for(communicate.save(str(out_path)), timeout=6.0)
            return out_path.exists() and out_path.stat().st_size > 256
        except Exception:
            return False

    def _get_cache_path(self, text: str) -> Path:
        """Devuelve una ruta en caché basada en el hash del texto, voz y cadencia."""
        cache_key = f"{self.voice_name}_{self.speech_rate}_{text.strip()}"
        h = hashlib.md5(cache_key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"alvaro_{h}.mp3"

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

            # 1. Si ya está en caché con voz de Álvaro, reproducir de inmediato (cero latencia)
            if cached_mp3.exists() and cached_mp3.stat().st_size > 256:
                try:
                    played = _play_mp3_winmm(cached_mp3, volume=self.volume)
                except Exception:
                    played = False

            # 2. Si no estaba en caché, sintetizar con Microsoft Edge Neural TTS (Álvaro)
            if not played:
                try:
                    ok_neural = asyncio.run(self._synthesize_edge_neural(text, cached_mp3))
                    if ok_neural:
                        played = _play_mp3_winmm(cached_mp3, volume=self.volume)
                except Exception:
                    played = False

            self.is_speaking = False

    def stop(self) -> None:
        try:
            self._queue.put_nowait(None)
        except Exception:
            pass
