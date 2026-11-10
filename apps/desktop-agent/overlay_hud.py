"""
ACC Apex Engineer Pro - Overlay HUD Transparente Click-Through In-Game (overlay_hud.py)
Consume 0 MB de VRAM adicional usando GDI ligero con estilos extendidos Win32:
  WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST
Permite hacer clic a través del HUD directamente hacia Assetto Corsa Competizione.
"""

from __future__ import annotations

import ctypes
import tkinter as tk
from typing import Optional
from shm_reader import TelemetrySample


GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008


class OverlayHUD:
    def __init__(self, root: tk.Tk, input_mode: str = "wheel") -> None:
        self.root = root
        self.input_mode = input_mode
        self.last_setup_label = "APEX_AUTO_LIVE.json [LISTO]"

        self.win = tk.Toplevel(self.root)
        self.win.title("ACC Apex Engineer HUD")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.88)
        self.win.configure(bg="#090D16")

        # Posicionar arriba a la derecha sin tapar el retrovisor virtual de ACC
        screen_w = self.win.winfo_screenwidth()
        self.win.geometry(f"430x165+{screen_w - 455}+24")

        self._build_widgets()
        self.win.after(150, self._apply_click_through)

    def _apply_click_through(self) -> None:
        """Aplica WS_EX_TRANSPARENT | WS_EX_LAYERED en Windows para que no capture el ratón ni el foco de ACC."""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.win.winfo_id())
            if not hwnd:
                hwnd = self.win.winfo_id()
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd,
                GWL_EXSTYLE,
                style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST,
            )
        except Exception:
            pass

    def _build_widgets(self) -> None:
        header_frame = tk.Frame(self.win, bg="#090D16")
        header_frame.pack(fill="x", padx=10, pady=(6, 2))

        self.lbl_title = tk.Label(
            header_frame,
            text="⚡ ACC APEX ENGINEER · 333 Hz",
            fg="#38BDF8",
            bg="#090D16",
            font=("Consolas", 10, "bold"),
        )
        self.lbl_title.pack(side="left")

        self.lbl_mode = tk.Label(
            header_frame,
            text=f"[{self.input_mode.upper()}]",
            fg="#10B981",
            bg="#090D16",
            font=("Consolas", 10, "bold"),
        )
        self.lbl_mode.pack(side="right")

        # Fila principal: Velocidad, Marcha, RPM y Presiones Pirelli DHE
        main_frame = tk.Frame(self.win, bg="#111827", bd=1, relief="solid")
        main_frame.pack(fill="x", padx=10, pady=3)

        self.lbl_speed_gear = tk.Label(
            main_frame,
            text="000 km/h | N | 0000 RPM",
            fg="#F9FAFB",
            bg="#111827",
            font=("Consolas", 13, "bold"),
        )
        self.lbl_speed_gear.pack(anchor="w", padx=8, pady=(4, 2))

        self.lbl_tyres = tk.Label(
            main_frame,
            text="PSI: FL 26.8 | FR 26.8 | RL 26.8 | RR 26.8",
            fg="#34D399",
            bg="#111827",
            font=("Consolas", 9, "bold"),
        )
        self.lbl_tyres.pack(anchor="w", padx=8, pady=(0, 4))

        # Estado del Auto-Setup
        self.lbl_setup = tk.Label(
            self.win,
            text=f"AUTO-SETUP: {self.last_setup_label}",
            fg="#A78BFA",
            bg="#090D16",
            font=("Consolas", 9),
        )
        self.lbl_setup.pack(anchor="w", padx=12, pady=(2, 1))

        # Alerta de Coaching en Vivo
        self.lbl_alert = tk.Label(
            self.win,
            text="COACH: Trazada limpia · Objetivo Pirelli 26.8-26.9 PSI",
            fg="#FBBF24",
            bg="#090D16",
            font=("Consolas", 9, "bold"),
        )
        self.lbl_alert.pack(anchor="w", padx=12, pady=(1, 4))

    def set_input_mode(self, mode: str) -> None:
        self.input_mode = mode
        mode_es = {"keyboard": "TECLADO", "gamepad": "MANDO", "wheel": "VOLANTE"}.get(mode, mode.upper())
        self.lbl_mode.configure(text=f"[{mode_es}]")

    def set_setup_status(self, status_text: str) -> None:
        self.last_setup_label = status_text
        self.lbl_setup.configure(text=f"AUTO-SETUP: {status_text}")

    def update_telemetry(self, sample: TelemetrySample, live_alert: Optional[str]) -> None:
        gear_str = "R" if sample.gear < 0 else ("N" if sample.gear == 0 else str(sample.gear))
        self.lbl_speed_gear.configure(
            text=f"{sample.speed_kmh:03.0f} km/h | M{gear_str} | {sample.rpms:04d} RPM"
        )

        p = sample.tyre_pressures
        in_window = all(26.65 <= x <= 27.05 for x in p)
        psi_color = "#34D399" if in_window else "#FBBF24"
        self.lbl_tyres.configure(
            text=f"PSI: FL {p[0]:.1f} | FR {p[1]:.1f} | RL {p[2]:.1f} | RR {p[3]:.1f}",
            fg=psi_color,
        )

        if live_alert:
            self.lbl_alert.configure(text=f"⚠️ {live_alert}", fg="#F87171")
        else:
            src_tag = "ACC 333Hz EN VIVO" if sample.is_live_acc else "SIMULADOR 333Hz ACTIVO"
            self.lbl_alert.configure(
                text=f"✓ {src_tag} · Alturas {sample.ride_height[0]:.0f}/{sample.ride_height[1]:.0f}mm",
                fg="#34D399",
            )

