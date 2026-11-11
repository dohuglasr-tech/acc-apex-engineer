"""
ACC Apex Engineer Pro - Orquestador Principal del Agente Ejecutable Local (main.py)
  - Bucle de lectura de Memoria Compartida de ACC a 333 Hz (cada 3 ms) usando OpenFileMappingW
  - Puente híbrido: WebSocket local 60 FPS + Sincronización Cloud en vivo cada 1.2s vía Supabase
    (garantiza que la web en https://*.vercel.app reciba telemetría en vivo sin bloqueos HTTPS)
  - Auto-Inyector de Setups en tiempo real en Documents\\Assetto Corsa Competizione\\Setups
  - Cerebro de IA con Google Gemini y síntesis por voz neural de alta velocidad
  - Mutex de instancia única: impide que dos procesos hablen a la vez
"""

from __future__ import annotations

import asyncio
import ctypes
import json
import os
import sys
import threading
import time
import tkinter as tk
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Mutex único para evitar que dos instancias del agente se ejecuten simultáneamente
# y hablen con dos voces al mismo tiempo.
ERROR_ALREADY_EXISTS = 183
_SINGLE_INSTANCE_MUTEX = ctypes.windll.kernel32.CreateMutexW(
    None, False, "ACC_Apex_Engineer_SingleInstance_Mutex_v2"
)
if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
    # Ya hay otra instancia de ACC Apex Engineer ejecutándose.
    # Salimos inmediatamente para no sobreponer voces ni duplicar procesos.
    sys.exit(0)

import requests
import websockets

from auto_setup_injector import AutoSetupInjector
from gemini_race_engineer import GeminiRaceEngineer
from local_ai_engineer import LocalAIEngineer
from overlay_hud import OverlayHUD
from shm_reader import ACCSharedMemoryReader, TelemetrySample
from telemetry_analyzer import CompletedLapAnalysis, TelemetryLapAnalyzer
from ui_selector import InputModeSelectorWindow, load_agent_config, save_agent_config
from voice_engineer import VoiceEngineer


class SupabaseCloudSync:
    def __init__(self, config: Dict[str, Any]) -> None:
        self._push_in_flight = False
        self.update_config(config)

    def update_config(self, config: Dict[str, Any]) -> None:
        self.supabase_url = (config.get("supabase_url") or "").rstrip("/")
        self.supabase_key = config.get("supabase_anon_key") or ""
        self.agent_token = (config.get("agent_token") or "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_key and self.agent_token)

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
        }

    def sync_input_mode_async(
        self,
        input_mode: str,
        wheel_type: str = "",
        on_done: Optional[Callable[[bool, str, str], None]] = None,
    ) -> None:
        if not self.is_configured:
            if on_done:
                on_done(
                    True,
                    "Agente activo en modo local (333 Hz).",
                    "",
                )
            return

        def _task() -> None:
            try:
                resp = requests.post(
                    f"{self.supabase_url}/rest/v1/rpc/update_agent_input_mode",
                    headers=self._headers(),
                    json={
                        "p_agent_token": self.agent_token,
                        "p_input_mode": input_mode,
                        "p_wheel_type": wheel_type,
                    },
                    timeout=6,
                )
                if resp.ok:
                    data = resp.json() if resp.text else {}
                    username = (
                        data.get("discord_username", "")
                        if isinstance(data, dict)
                        else ""
                    )
                    if on_done:
                        on_done(
                            True,
                            "Sincronizado con la web. Abre ACC y entra a pista.",
                            username,
                        )
                else:
                    if on_done:
                        on_done(
                            False,
                            "Token no encontrado en Supabase. Copia el token desde la web.",
                            "",
                        )
            except Exception:
                if on_done:
                    on_done(
                        True,
                        "Configuración activa localmente.",
                        "",
                    )

        threading.Thread(target=_task, daemon=True).start()

    def push_live_state_async(
        self,
        is_live: bool,
        input_mode: str,
        live_payload: Optional[Dict[str, Any]],
        on_response: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        if not self.is_configured or self._push_in_flight:
            return

        self._push_in_flight = True

        def _task() -> None:
            try:
                resp = requests.post(
                    f"{self.supabase_url}/rest/v1/rpc/agent_push_live_state",
                    headers=self._headers(),
                    json={
                        "p_agent_token": self.agent_token,
                        "p_is_live": is_live,
                        "p_input_mode": input_mode,
                        "p_live_telemetry": live_payload if is_live else None,
                    },
                    timeout=4,
                )
                if resp.ok and on_response:
                    data = resp.json() if resp.text else {}
                    if isinstance(data, dict):
                        on_response(data)
            except Exception:
                pass
            finally:
                self._push_in_flight = False

        threading.Thread(target=_task, daemon=True).start()

    def sync_lap_and_setup_async(
        self,
        lap: CompletedLapAnalysis,
        setup_file_name: str,
        setup_json: Dict[str, Any],
        changes_summary: List[Dict[str, str]],
        version_num: int,
    ) -> None:
        if not self.is_configured:
            return

        def _task() -> None:
            try:
                resp_setup = requests.post(
                    f"{self.supabase_url}/rest/v1/rpc/agent_insert_setup",
                    headers=self._headers(),
                    json={
                        "p_agent_token": self.agent_token,
                        "p_car_model": lap.car_model,
                        "p_track_name": lap.track_name,
                        "p_input_mode": lap.input_mode,
                        "p_version_num": version_num,
                        "p_file_name": setup_file_name,
                        "p_setup_json": setup_json,
                        "p_changes_summary": changes_summary,
                        "p_air_temp": lap.air_temp,
                        "p_road_temp": lap.road_temp,
                        "p_best_lap_ms": lap.lap_time_ms,
                    },
                    timeout=6,
                )
                setup_id = resp_setup.json() if resp_setup.ok else None

                requests.post(
                    f"{self.supabase_url}/rest/v1/rpc/agent_insert_lap",
                    headers=self._headers(),
                    json={
                        "p_agent_token": self.agent_token,
                        "p_setup_id": setup_id,
                        "p_car_model": lap.car_model,
                        "p_track_name": lap.track_name,
                        "p_input_mode": lap.input_mode,
                        "p_lap_number": lap.lap_number,
                        "p_lap_time_ms": lap.lap_time_ms,
                        "p_sector_1_ms": lap.sector_1_ms,
                        "p_sector_2_ms": lap.sector_2_ms,
                        "p_sector_3_ms": lap.sector_3_ms,
                        "p_is_valid": lap.is_valid,
                        "p_tyre_pressures_hot": lap.tyre_pressures_hot,
                        "p_tyre_temps_core": lap.tyre_temps_core,
                        "p_brake_temps_avg": lap.brake_temps_avg,
                        "p_bottoming_events": lap.bottoming_events,
                        "p_telemetry_trace": lap.telemetry_trace,
                        "p_driving_errors": lap.driving_errors,
                    },
                    timeout=6,
                )
            except Exception:
                pass

        threading.Thread(target=_task, daemon=True).start()


class ApexDesktopAgentApp:
    def __init__(self) -> None:
        self.config = load_agent_config()
        save_agent_config(self.config)
        initial_mode = self.config.get("input_mode") or "gamepad"
        initial_style = self.config.get("driving_style") or "safe"

        self.shm_reader = ACCSharedMemoryReader()
        self.analyzer = TelemetryLapAnalyzer(input_mode=initial_mode)
        self.injector = AutoSetupInjector(input_mode=initial_mode, driving_style=initial_style)
        self.voice = VoiceEngineer(enabled=bool(self.config.get("voice_enabled", True)))
        gemini_key = self.config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
        self.gemini = GeminiRaceEngineer(api_key=gemini_key)
        self.ai_engineer = LocalAIEngineer(
            voice_engine=self.voice,
            input_mode=initial_mode,
            gemini_engine=self.gemini,
        )
        initial_voice = self.config.get("voice_mode") or "companion"
        self.ai_engineer.set_voice_mode(initial_voice)
        self.cloud_sync = SupabaseCloudSync(self.config)

        self.latest_sample: Optional[TelemetrySample] = None
        self.latest_setup_event: Optional[Dict[str, Any]] = None
        self.latest_lap_event: Optional[Dict[str, Any]] = None
        self._last_completed_lap_ms: int = 0
        self.running = True
        self._ws_clients: Set[Any] = set()
        self._last_cloud_push_ts: float = 0.0
        self._was_live_last_push: bool = False

        self.root = tk.Tk()
        self.selector_ui = InputModeSelectorWindow(
            root=self.root,
            config=self.config,
            on_config_applied=self._on_config_applied,
            on_test_gemini=self._on_test_gemini,
        )
        self.hud = OverlayHUD(self.root, input_mode=initial_mode)
        self.hud.set_voice_mode(initial_voice)

        self._physics_thread = threading.Thread(
            target=self._physics_loop_333hz, daemon=True, name="Physics333HzThread"
        )
        self._physics_thread.start()

        self._ws_thread = threading.Thread(
            target=self._run_websocket_server, daemon=True, name="WebSocket60FpsThread"
        )
        self._ws_thread.start()

        # Validar y vincular automáticamente al iniciar
        self._on_config_applied(self.config)

        self.root.after(50, self._refresh_hud_loop)

    def _on_test_gemini(self) -> Tuple[bool, str]:
        key = self.selector_ui.gemini_key_var.get().strip() or self.config.get("gemini_api_key", "")
        if key:
            self.gemini.set_api_key(key)
            self.config["gemini_api_key"] = key
            save_agent_config(self.config)
        ok, msg = self.gemini.test_connection()
        if ok and self.voice:
            self.voice.speak(f"Radio comprobada: {msg}", priority=True)
        return ok, msg

    def _on_config_applied(self, updated_cfg: Dict[str, Any]) -> None:
        mode = updated_cfg.get("input_mode") or "gamepad"
        style = updated_cfg.get("driving_style") or "safe"
        self.analyzer.set_input_mode(mode)
        self.injector.set_input_mode(mode)
        self.injector.set_driving_style(style)
        self.ai_engineer.set_input_mode(mode)
        self.hud.set_input_mode(mode)
        if updated_cfg.get("voice_mode"):
            self.ai_engineer.set_voice_mode(updated_cfg["voice_mode"])
            self.hud.set_voice_mode(updated_cfg["voice_mode"])
        if updated_cfg.get("gemini_api_key") is not None:
            self.gemini.set_api_key(updated_cfg["gemini_api_key"])
        self.voice.enabled = bool(updated_cfg.get("voice_enabled", True))
        self.cloud_sync.update_config(updated_cfg)

        def _ui_callback(success: bool, msg: str, username: str) -> None:
            try:
                self.root.after(
                    0,
                    lambda: self.selector_ui.set_sync_feedback(
                        success, msg, username, mode
                    ),
                )
            except Exception:
                pass

        self.cloud_sync.sync_input_mode_async(
            mode, updated_cfg.get("wheel_type", ""), on_done=_ui_callback
        )

    def _physics_loop_333hz(self) -> None:
        target_dt = 1.0 / 333.0
        while self.running:
            t0 = time.perf_counter()
            try:
                sample = self.shm_reader.read_sample()
                self.latest_sample = sample
                if sample is not None and sample.is_live_acc:
                    self.ai_engineer.process_sample(sample)
                    completed_lap = self.analyzer.process_sample(sample)
                    if completed_lap is not None:
                        self._handle_completed_lap(completed_lap)
            except Exception as e:
                try:
                    with open("agent_err.log", "a", encoding="utf-8") as f:
                        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Physics error: {e}\n")
                except Exception:
                    pass
            elapsed = time.perf_counter() - t0
            sleep_for = target_dt - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

    def _handle_completed_lap(self, lap: CompletedLapAnalysis) -> None:
        live_path, setup_json, changes, version_num = self.injector.inject_optimized_setup(
            car_model=lap.car_model,
            track_name=lap.track_name,
            hot_pressures=lap.tyre_pressures_hot,
            core_temps=lap.tyre_temps_core,
            brake_temps_avg=lap.brake_temps_avg,
            bottoming_events=lap.bottoming_events,
            understeer_ratio=lap.understeer_ratio,
            oversteer_entry_events=lap.oversteer_entry_events,
            tc_cut_ratio=lap.tc_cut_ratio,
            air_temp=lap.air_temp,
            road_temp=lap.road_temp,
            best_lap_ms=lap.lap_time_ms,
            tyre_temps_imo=lap.tyre_temps_imo,
            curb_strikes=lap.curb_strikes,
        )

        self.latest_setup_event = {
            "version_num": version_num,
            "file_name": live_path.name,
            "full_path": str(live_path),
            "car_model": lap.car_model,
            "track_name": lap.track_name,
            "input_mode": lap.input_mode,
            "changes_summary": changes,
            "setup_json": setup_json,
        }
        self.latest_lap_event = {
            "lap_number": lap.lap_number,
            "lap_time_ms": lap.lap_time_ms,
            "sector_1_ms": lap.sector_1_ms,
            "sector_2_ms": lap.sector_2_ms,
            "sector_3_ms": lap.sector_3_ms,
            "tyre_pressures_hot": lap.tyre_pressures_hot,
            "driving_errors": lap.driving_errors,
            "telemetry_trace": lap.telemetry_trace,
        }

        self.hud.set_setup_status(f"APEX_AUTO_LIVE.json (v{version_num})")
        if self.ai_engineer.voice_mode == "telemetry":
            lap_sec = round(lap.lap_time_ms / 1000.0, 3)
            mins = int(lap_sec // 60)
            secs = int(lap_sec % 60)
            tenths = int(round((lap_sec - int(lap_sec)) * 10))
            if mins > 0:
                lap_msg = f"Vuelta {lap.lap_number}: {mins} minuto{'s' if mins != 1 else ''}, {secs} segundos y {tenths} décimas."
            else:
                lap_msg = f"Vuelta {lap.lap_number}: {secs} segundos y {tenths} décimas."
            self.voice.speak(lap_msg)
        elif self.ai_engineer.voice_mode == "companion":
            primary_err = lap.driving_errors[0]["type"] if lap.driving_errors else None
            # Si Google Gemini está activo, genera el informe de vuelta con IA avanzada
            if self.gemini and self.gemini.is_available:
                lap_sec = round(lap.lap_time_ms / 1000.0, 3)
                mins = int(lap_sec // 60)
                secs = int(lap_sec % 60)
                tenths = int(round((lap_sec - int(lap_sec)) * 10))
                time_str = f"{mins}:{secs:02d}.{tenths}"
                w = self.latest_sample.tyre_wear if self.latest_sample else [3.0, 3.0, 3.0, 3.0]
                wear_pcts = [round(max(0.0, min(100.0, (1.0 - (val / 3.0)) * 100.0))) for val in w]
                avg_wear = int(sum(wear_pcts) / 4.0)

                delta_str = ""
                if self._last_completed_lap_ms > 0:
                    d_sec = round((lap.lap_time_ms - self._last_completed_lap_ms) / 1000.0, 2)
                    if d_sec < 0:
                        delta_str = f"mejorando {abs(d_sec):.2f} segundos"
                    else:
                        delta_str = f"+{d_sec:.2f} segundos más lento"
                self._last_completed_lap_ms = lap.lap_time_ms

                ctx = {
                    "track_name": lap.track_name,
                    "car_model": lap.car_model,
                    "lap_time_str": time_str,
                    "delta_str": delta_str,
                    "setup_version": version_num,
                    "input_mode": lap.input_mode,
                    "primary_error": primary_err or "trazada constante",
                    "tyre_wear_pct": f"{avg_wear}% (DI {wear_pcts[0]}%, DD {wear_pcts[1]}%, TI {wear_pcts[2]}%, TD {wear_pcts[3]}%)",
                }

                def _on_gemini_lap(g_text: str, g_cat: str) -> None:
                    self.ai_engineer._broadcast_radio(g_text, g_cat)

                self.gemini.generate_radio_advice_async("lap_summary", ctx, _on_gemini_lap)
            else:
                self.voice.announce_lap_and_setup(
                    lap_number=lap.lap_number,
                    lap_time_ms=lap.lap_time_ms,
                    version_num=version_num,
                    primary_error=primary_err,
                    input_mode=lap.input_mode,
                )
        self.cloud_sync.sync_lap_and_setup_async(
            lap=lap,
            setup_file_name=live_path.name,
            setup_json=setup_json,
            changes_summary=changes,
            version_num=version_num,
        )

    def _refresh_hud_loop(self) -> None:
        sample = self.latest_sample
        is_live = bool(sample is not None and sample.is_live_acc)
        is_speaking = bool(getattr(self.voice, "is_speaking", False))
        current_speech = ""
        if self.ai_engineer and self.ai_engineer.current_radio_event:
            current_speech = self.ai_engineer.current_radio_event.text
        elif getattr(self.voice, "last_spoken_text", ""):
            current_speech = self.voice.last_spoken_text

        self.hud.update_telemetry(
            sample=sample,
            live_alert=self.analyzer.live_alert if is_live else None,
            radio_text=current_speech,
            is_speaking=is_speaking,
        )

        if is_live and sample is not None:
            self.selector_ui.set_live_connection_status(
                True, sample.track_name, sample.car_model, sample.speed_kmh
            )
        else:
            self.selector_ui.set_live_connection_status(False)

        # Puente Cloud en vivo hacia Supabase:
        # - Cada 1.2s cuando el coche está en pista (transmite telemetría en vivo a Vercel HTTPS)
        # - Cada 10s cuando está en espera (mantiene el estado AGENTE CONECTADO en la web)
        now = time.time()
        interval = 1.2 if is_live else 10.0
        if (now - self._last_cloud_push_ts) >= interval or (
            is_live != self._was_live_last_push
        ):
            self._last_cloud_push_ts = now
            self._was_live_last_push = is_live
            mode = self.config.get("input_mode") or "gamepad"
            live_payload = None
            if is_live and sample is not None:
                live_payload = {
                    "sample": sample.to_dict(),
                    "active_setup": self.injector.get_current_setup(
                        sample.car_model, sample.track_name
                    ),
                    "live_alert": self.analyzer.live_alert,
                    "live_trace": self.analyzer.live_trace,
                    "live_errors": self.analyzer.live_errors,
                    "engineer_state": self.ai_engineer.get_state(),
                }

            def _on_cloud_push_resp(data: Dict[str, Any]) -> None:
                remote_voice = data.get("voice_mode")
                if remote_voice and remote_voice in ("companion", "car_state", "telemetry"):
                    if self.ai_engineer.voice_mode != remote_voice:
                        self.config["voice_mode"] = remote_voice
                        save_agent_config(self.config)
                        self.ai_engineer.set_voice_mode(remote_voice)
                        self.hud.set_voice_mode(remote_voice)

            self.cloud_sync.push_live_state_async(
                is_live, mode, live_payload, on_response=_on_cloud_push_resp
            )

        if self.running:
            self.root.after(50, self._refresh_hud_loop)

    def _run_websocket_server(self) -> None:
        async def handler(websocket: Any) -> None:
            self._ws_clients.add(websocket)
            try:
                async for raw_msg in websocket:
                    try:
                        cmd = json.loads(raw_msg)
                        if cmd.get("action") == "set_input_mode" and cmd.get(
                            "input_mode"
                        ) in ("keyboard", "gamepad", "wheel"):
                            self.config["input_mode"] = cmd["input_mode"]
                            if cmd.get("agent_token"):
                                self.config["agent_token"] = cmd["agent_token"]
                            save_agent_config(self.config)
                            self._on_config_applied(self.config)
                        elif cmd.get("action") == "set_voice_mode" and cmd.get(
                            "voice_mode"
                        ) in ("companion", "car_state", "telemetry"):
                            mode = cmd["voice_mode"]
                            self.config["voice_mode"] = mode
                            save_agent_config(self.config)
                            self.ai_engineer.set_voice_mode(mode)
                            self.hud.set_voice_mode(mode)
                        elif cmd.get("action") == "set_driving_style" and cmd.get(
                            "driving_style"
                        ) in ("aggressive", "safe", "beginner"):
                            style = cmd["driving_style"]
                            self.config["driving_style"] = style
                            save_agent_config(self.config)
                            self.injector.set_driving_style(style)
                    except Exception:
                        pass
            except Exception:
                pass
            finally:
                self._ws_clients.discard(websocket)

        async def broadcaster() -> None:
            while self.running:
                if self._ws_clients:
                    sample = self.latest_sample
                    if sample is not None and sample.is_live_acc:
                        payload = json.dumps(
                            {
                                "type": "telemetry_frame",
                                "is_live_acc": True,
                                "input_mode": self.config.get("input_mode") or "gamepad",
                                "voice_mode": self.ai_engineer.voice_mode,
                                "live_alert": self.analyzer.live_alert,
                                "sample": sample.to_dict(),
                                "active_setup": self.injector.get_current_setup(
                                    sample.car_model, sample.track_name
                                ),
                                "live_trace": self.analyzer.live_trace,
                                "live_errors": self.analyzer.live_errors,
                                "engineer_state": self.ai_engineer.get_state(),
                                "latest_setup": self.latest_setup_event,
                                "latest_lap": self.latest_lap_event,
                            }
                        )
                    else:
                        payload = json.dumps(
                            {
                                "type": "telemetry_standby",
                                "is_live_acc": False,
                                "input_mode": self.config.get("input_mode") or "gamepad",
                                "voice_mode": self.ai_engineer.voice_mode,
                            }
                        )
                    stale = set()
                    for ws in list(self._ws_clients):
                        try:
                            await ws.send(payload)
                        except Exception:
                            stale.add(ws)
                    self._ws_clients -= stale
                await asyncio.sleep(1.0 / 60.0)

        async def main_ws() -> None:
            async with websockets.serve(handler, "0.0.0.0", 8765):
                await broadcaster()

        try:
            asyncio.run(main_ws())
        except Exception:
            pass

    def run(self) -> None:
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            try:
                save_agent_config(self.config)
            except Exception:
                pass
            self.shm_reader.close()
            self.voice.stop()


if __name__ == "__main__":
    app = ApexDesktopAgentApp()
    app.run()
