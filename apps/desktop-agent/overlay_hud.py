"""
ACC Apex Engineer Pro - Overlay HUD Transparente Click-Through In-Game (overlay_hud.py)
Consume 0 MB de VRAM adicional usando GDI ligero con estilos extendidos Win32:
  WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST
Permanece oculto mientras Assetto Corsa Competizione no está en sesión activa en pista.
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
        self.last_setup_label = "STANDBY"
        self._visible = False

        self.win = tk.Toplevel(self.root)
        self.win.title("ACC Apex Telemetry Overlay")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.90)
        self.win.configure(bg="#08080A")

        screen_w = self.win.winfo_screenwidth()
        self.win.geometry(f"420x148+{screen_w - 445}+24")

        self._build_widgets()
        self.win.after(150, self._apply_click_through)
        # Iniciar oculto hasta que ACC entre en sesión activa en pista
        self.win.withdraw()

    def _apply_click_through(self) -> None:
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
        # Línea superior roja estilo F1 Broadcast
        top_bar = tk.Frame(self.win, bg="#E10600", height=3)
        top_bar.pack(fill="x")

        header_frame = tk.Frame(self.win, bg="#08080A")
        header_frame.pack(fill="x", padx=12, pady=(6, 2))

        self.lbl_title = tk.Label(
            header_frame,
            text="APEX TELEMETRY // 333 HZ",
            fg="#FFFFFF",
            bg="#08080A",
            font=("Consolas", 9, "bold"),
        )
        self.lbl_title.pack(side="left")

        self.lbl_mode = tk.Label(
            header_frame,
            text=f"{self.input_mode.upper()}",
            fg="#E10600",
            bg="#08080A",
            font=("Consolas", 9, "bold"),
        )
        self.lbl_mode.pack(side="right")

        main_frame = tk.Frame(self.win, bg="#111115", bd=1, relief="flat")
        main_frame.pack(fill="x", padx=12, pady=3)

        self.lbl_speed_gear = tk.Label(
            main_frame,
            text="000 KMH   G-N   0000 RPM",
            fg="#FFFFFF",
            bg="#111115",
            font=("Consolas", 13, "bold"),
        )
        self.lbl_speed_gear.pack(anchor="w", padx=10, pady=(5, 2))

        self.lbl_tyres = tk.Label(
            main_frame,
            text="PSI  FL --.-  FR --.-  RL --.-  RR --.-",
            fg="#A1A1AA",
            bg="#111115",
            font=("Consolas", 9),
        )
        self.lbl_tyres.pack(anchor="w", padx=10, pady=(0, 5))

        self.lbl_setup = tk.Label(
            self.win,
            text=f"SETUP: {self.last_setup_label}",
            fg="#A1A1AA",
            bg="#08080A",
            font=("Consolas", 8),
        )
        self.lbl_setup.pack(anchor="w", padx=12, pady=(2, 0))

        self.lbl_alert = tk.Label(
            self.win,
            text="STATUS: WAITING FOR TRACK SESSION",
            fg="#71717A",
            bg="#08080A",
            font=("Consolas", 8, "bold"),
        )
        self.lbl_alert.pack(anchor="w", padx=12, pady=(1, 4))

    def set_input_mode(self, mode: str) -> None:
        self.input_mode = mode
        mode_es = {"keyboard": "TECLADO", "gamepad": "MANDO", "wheel": "VOLANTE"}.get(
            mode, mode.upper()
        )
        self.lbl_mode.configure(text=mode_es)

    def set_setup_status(self, status_text: str) -> None:
        self.last_setup_label = status_text
        self.lbl_setup.configure(text=f"SETUP: {status_text}")

    def update_telemetry(
        self, sample: Optional[TelemetrySample], live_alert: Optional[str]
    ) -> None:
        if sample is None or not sample.is_live_acc:
            if self._visible:
                self.win.withdraw()
                self._visible = False
            return

        if not self._visible:
            self.win.deiconify()
            self._apply_click_through()
            self._visible = True

        gear_str = "R" if sample.gear < 0 else ("N" if sample.gear == 0 else str(sample.gear))
        self.lbl_speed_gear.configure(
            text=f"{sample.speed_kmh:03.0f} KMH   G-{gear_str}   {sample.rpms:04d} RPM"
        )

        p = sample.tyre_pressures
        in_window = all(26.65 <= x <= 27.05 for x in p)
        psi_color = "#10B981" if in_window else "#F59E0B"
        self.lbl_tyres.configure(
            text=f"PSI  FL {p[0]:.1f}  FR {p[1]:.1f}  RL {p[2]:.1f}  RR {p[3]:.1f}",
            fg=psi_color,
        )

        if live_alert:
            self.lbl_alert.configure(text=f"ALERT: {live_alert}", fg="#E10600")
        else:
            self.lbl_alert.configure(
                text=f"RH {sample.ride_height[0]:.0f}/{sample.ride_height[1]:.0f} MM  |  BIAS {sample.brake_bias:.1f}%",
                fg="#D4D4D8",
            )
