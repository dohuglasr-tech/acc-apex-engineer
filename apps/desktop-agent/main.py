"""
ACC Apex Engineer Pro - Orquestador Principal del Agente Ejecutable Local (main.py)
  - Bucle de lectura de Memoria Compartida de ACC a 333 Hz (cada 3 ms)
  - Servidor WebSocket Local a 60 FPS (ws://0.0.0.0:8765) para Web Dashboard en PC y Celular (vía QR)
  - Auto-Inyector de Setups en tiempo real en Documents\\Assetto Corsa Competizione\\Setups
  - Sincronización Cloud 100% privada por usuario en Supabase (vía RPC con agent_token)
  - Overlay HUD Transparente (0 MB VRAM) + Ingeniero de Voz en Español
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
import tkinter as tk
from typing import Any, Dict, List, Optional, Set

import requests
import websockets

from auto_setup_injector import AutoSetupInjector
from overlay_hud import OverlayHUD
from shm_reader import ACCSharedMemoryReader, TelemetrySample
from telemetry_analyzer import CompletedLapAnalysis, TelemetryLapAnalyzer
from ui_selector import InputModeSelectorWindow, load_agent_config
from voice_engineer import VoiceEngineer


class SupabaseCloudSync:
    """
    Sincroniza de forma asíncrona los setups auto-inyectados y las vueltas del usuario
    hacia su cuenta privada de Supabase usando su agent_token único (con RLS).
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.update_config(config)

    def update_config(self, config: Dict[str, Any]) -> None:
        self.supabase_url = (config.get("supabase_url") or "").rstrip("/")
        self.supabase_key = config.get("supabase_anon_key") or ""
        self.agent_token = config.get("agent_token") or ""

    @property
    def is_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_key and self.agent_token)

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
        }

    def sync_input_mode_async(self, input_mode: str, wheel_type: str = "") -> None:
        if not self.is_configured:
            return

        def _task() -> None:
            try:
                requests.post(
                    f"{self.supabase_url}/rest/v1/rpc/update_agent_input_mode",
                    headers=self._headers(),
                    json={
                        "p_agent_token": self.agent_token,
                        "p_input_mode": input_mode,
                        "p_wheel_type": wheel_type,
                    },
                    timeout=5,
                )
            except Exception:
                pass

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
                # 1. Insertar setup auto-inyectado en public.user_setups
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

                # 2. Insertar vuelta y diagnóstico de errores en public.user_laps
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
        initial_mode = self.config.get("input_mode") or "wheel"

        self.shm_reader = ACCSharedMemoryReader(enable_demo_when_idle=True)
        self.analyzer = TelemetryLapAnalyzer(input_mode=initial_mode)
        self.injector = AutoSetupInjector(input_mode=initial_mode)
        self.voice = VoiceEngineer(enabled=bool(self.config.get("voice_enabled", True)))
        self.cloud_sync = SupabaseCloudSync(self.config)

        self.latest_sample: Optional[TelemetrySample] = None
        self.latest_setup_event: Optional[Dict[str, Any]] = None
        self.latest_lap_event: Optional[Dict[str, Any]] = None
        self.running = True
        self._ws_clients: Set[Any] = set()

        # Interfaz Tkinter (Selector Obligatorio + Overlay HUD Click-Through)
        self.root = tk.Tk()
        self.selector_ui = InputModeSelectorWindow(
            root=self.root,
            config=self.config,
            on_config_applied=self._on_config_applied,
            on_force_inject=self._force_inject_now,
        )
        self.hud = OverlayHUD(self.root, input_mode=initial_mode)

        # Hilo de lectura física a 333 Hz (cada 3 ms)
        self._physics_thread = threading.Thread(
            target=self._physics_loop_333hz, daemon=True, name="Physics333HzThread"
        )
        self._physics_thread.start()

        # Hilo de servidor WebSocket a 60 FPS para Web Dashboard (PC y Celular vía QR)
        self._ws_thread = threading.Thread(
            target=self._run_websocket_server, daemon=True, name="WebSocket60FpsThread"
        )
        self._ws_thread.start()

        # Refresco visual del Overlay HUD a ~30 FPS en el hilo principal
        self.root.after(33, self._refresh_hud_loop)

    def _on_config_applied(self, updated_cfg: Dict[str, Any]) -> None:
        mode = updated_cfg.get("input_mode") or "wheel"
        self.analyzer.set_input_mode(mode)
        self.injector.set_input_mode(mode)
        self.hud.set_input_mode(mode)
        self.voice.enabled = bool(updated_cfg.get("voice_enabled", True))
        self.cloud_sync.update_config(updated_cfg)
        self.cloud_sync.sync_input_mode_async(mode, updated_cfg.get("wheel_type", ""))

        mode_es = {"keyboard": "teclado", "gamepad": "mando", "wheel": "volante"}.get(mode, mode)
        self.voice.speak(f"Modo {mode_es} activado. Telemetría a 333 hercios y auto inyector listos.")

    def _force_inject_now(self) -> str:
        sample = self.latest_sample or self.shm_reader.read_sample()
        assert sample is not None
        live_path, setup_json, changes, version_num = self.injector.inject_optimized_setup(
            car_model=sample.car_model,
            track_name=sample.track_name,
            hot_pressures=sample.tyre_pressures,
            core_temps=sample.tyre_temps_core,
            brake_temps_avg=sample.brake_temps,
            bottoming_events=1 if sample.ride_height[0] < 43.0 else 0,
            understeer_ratio=0.25,
            oversteer_entry_events=1,
            tc_cut_ratio=0.20,
            air_temp=sample.air_temp,
            road_temp=sample.road_temp,
            best_lap_ms=sample.best_lap_ms,
        )
        self.latest_setup_event = {
            "version_num": version_num,
            "file_name": live_path.name,
            "full_path": str(live_path),
            "car_model": sample.car_model,
            "track_name": sample.track_name,
            "input_mode": self.injector.input_mode,
            "changes_summary": changes,
            "setup_json": setup_json,
        }
        self.hud.set_setup_status(f"APEX_AUTO_LIVE.json (v{version_num}) INYECTADO")
        self.voice.speak(f"Setup automático versión {version_num} inyectado en tu carpeta de Assetto Corsa Competizione.")
        return str(live_path)

    def _physics_loop_333hz(self) -> None:
        target_dt = 1.0 / 333.0  # 0.003003 segundos (333 Hz)
        while self.running:
            t0 = time.perf_counter()
            sample = self.shm_reader.read_sample()
            if sample is not None:
                self.latest_sample = sample
                # Solo procesar vuelta si el usuario ya eligió periférico
                if self.config.get("input_mode") in ("keyboard", "gamepad", "wheel"):
                    completed_lap = self.analyzer.process_sample(sample)
                    if completed_lap is not None:
                        self._handle_completed_lap(completed_lap)
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

        self.hud.set_setup_status(f"APEX_AUTO_LIVE.json (v{version_num}) INYECTADO")
        primary_err = lap.driving_errors[0]["type"] if lap.driving_errors else None
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
        if self.latest_sample is not None:
            self.hud.update_telemetry(self.latest_sample, self.analyzer.live_alert)
        if self.running:
            self.root.after(33, self._refresh_hud_loop)

    def _run_websocket_server(self) -> None:
        async def handler(websocket: Any) -> None:
            self._ws_clients.add(websocket)
            try:
                async for raw_msg in websocket:
                    try:
                        cmd = json.loads(raw_msg)
                        if cmd.get("action") == "set_input_mode" and cmd.get("input_mode") in (
                            "keyboard",
                            "gamepad",
                            "wheel",
                        ):
                            self.config["input_mode"] = cmd["input_mode"]
                            self._on_config_applied(self.config)
                        elif cmd.get("action") == "force_inject":
                            self._force_inject_now()
                    except Exception:
                        pass
            except Exception:
                pass
            finally:
                self._ws_clients.discard(websocket)

        async def broadcaster() -> None:
            while self.running:
                if self._ws_clients and self.latest_sample is not None:
                    payload = json.dumps({
                        "type": "telemetry_frame",
                        "input_mode": self.config.get("input_mode") or "wheel",
                        "live_alert": self.analyzer.live_alert,
                        "sample": self.latest_sample.to_dict(),
                        "latest_setup": self.latest_setup_event,
                        "latest_lap": self.latest_lap_event,
                    })
                    stale = set()
                    for ws in list(self._ws_clients):
                        try:
                            await ws.send(payload)
                        except Exception:
                            stale.add(ws)
                    self._ws_clients -= stale
                await asyncio.sleep(1.0 / 60.0)  # Stream a 60 FPS

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
        finally:
            self.running = False
            self.shm_reader.close()
            self.voice.stop()


if __name__ == "__main__":
    app = ApexDesktopAgentApp()
    app.run()
