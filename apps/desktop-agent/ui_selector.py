"""
ACC Apex Engineer Pro - Ventana de Configuración del Agente Local (ui_selector.py)
Diseño limpio de ingeniería de pista sin emojis ni simulaciones artificiales.
"""

from __future__ import annotations

import json
import os
import socket
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Any, Callable, Dict


CONFIG_PATH = (
    Path(os.environ.get("USERPROFILE", str(Path.home())))
    / ".acc_apex_engineer"
    / "agent_config.json"
)

DEFAULT_SUPABASE_URL = "https://kggynqougcnkjssryctw.supabase.co"
DEFAULT_SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtnZ3lucW91Z2Nua2pzc3J5Y3R3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQyNTgwMjAsImV4cCI6MjEwOTgzNDAyMH0."
    "pccwkvHf1YLH5yPu8xn_WS5iLK9ZHZulfT87BX_KJuY"
)


def load_agent_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if not cfg.get("supabase_url"):
                cfg["supabase_url"] = DEFAULT_SUPABASE_URL
            if not cfg.get("supabase_anon_key"):
                cfg["supabase_anon_key"] = DEFAULT_SUPABASE_ANON_KEY
            return cfg
        except Exception:
            pass
    return {
        "input_mode": "",
        "wheel_type": "",
        "agent_token": "",
        "supabase_url": DEFAULT_SUPABASE_URL,
        "supabase_anon_key": DEFAULT_SUPABASE_ANON_KEY,
        "voice_enabled": True,
    }


def save_agent_config(cfg: Dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def get_local_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class InputModeSelectorWindow:
    def __init__(
        self,
        root: tk.Tk,
        config: Dict[str, Any],
        on_config_applied: Callable[[Dict[str, Any]], None],
    ) -> None:
        self.root = root
        self.config = config
        self.on_config_applied = on_config_applied

        self.root.title("ACC APEX ENGINEER // DESKTOP TELEMETRY AGENT")
        self.root.geometry("600x540")
        self.root.configure(bg="#08080A")
        self.root.resizable(False, False)

        self.selected_mode = tk.StringVar(value=config.get("input_mode") or "")
        self.wheel_model_var = tk.StringVar(value=config.get("wheel_type") or "")
        self.token_var = tk.StringVar(value=config.get("agent_token") or "")
        self.voice_var = tk.BooleanVar(value=bool(config.get("voice_enabled", True)))

        self._build_ui()

    def _build_ui(self) -> None:
        top_accent = tk.Frame(self.root, bg="#E10600", height=4)
        top_accent.pack(fill="x")

        hdr = tk.Frame(self.root, bg="#0E0E12", pady=14, padx=20)
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text="APEX ENGINEER // 333 HZ TELEMETRY DAEMON",
            fg="#FFFFFF",
            bg="#0E0E12",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")
        tk.Label(
            hdr,
            text="Lectura directa de memoria compartida ACC y auto-inyeccion en carpeta Setups.",
            fg="#71717A",
            bg="#0E0E12",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 0))

        step1 = tk.Frame(self.root, bg="#08080A", padx=20, pady=12)
        step1.pack(fill="x")

        tk.Label(
            step1,
            text="01 / PERIFERICO DE ENTRADA",
            fg="#E10600",
            bg="#08080A",
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        modes = [
            (
                "keyboard",
                "TECLADO (KEYBOARD)",
                "Steer Ratio 16-18, Brake Torque 93%, ABS 5, curva de traccion progresiva.",
            ),
            (
                "gamepad",
                "MANDO (CONTROLLER / GAMEPAD)",
                "Slow Rebound delantero compensado, Steer Ratio 15:1, margen aero +0.5%.",
            ),
            (
                "wheel",
                "VOLANTE FFB (WHEEL & PEDALS)",
                "Steer Ratio directo 12-14, Brake Torque 100%, ABS 2-3, rake maximo.",
            ),
        ]

        for val, title, desc in modes:
            row = tk.Frame(step1, bg="#121217", pady=8, padx=12, bd=1, relief="flat")
            row.pack(fill="x", pady=3)
            rb = tk.Radiobutton(
                row,
                text=title,
                variable=self.selected_mode,
                value=val,
                fg="#FFFFFF",
                bg="#121217",
                selectcolor="#08080A",
                activebackground="#121217",
                activeforeground="#E10600",
                font=("Segoe UI", 9, "bold"),
            )
            rb.pack(anchor="w")
            tk.Label(
                row,
                text=desc,
                fg="#A1A1AA",
                bg="#121217",
                font=("Segoe UI", 8),
            ).pack(anchor="w", padx=22)

        step2 = tk.Frame(self.root, bg="#08080A", padx=20, pady=8)
        step2.pack(fill="x")

        tk.Label(
            step2,
            text="02 / VINCULACION DE CUENTA (AGENT TOKEN)",
            fg="#E10600",
            bg="#08080A",
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        tk.Entry(
            step2,
            textvariable=self.token_var,
            bg="#121217",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief="flat",
            font=("Consolas", 10),
        ).pack(fill="x", ipady=6, pady=(0, 8))

        tk.Checkbutton(
            step2,
            text="Ingeniero de radio por voz neural activo durante sesion en pista",
            variable=self.voice_var,
            fg="#D4D4D8",
            bg="#08080A",
            selectcolor="#121217",
            activebackground="#08080A",
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        btn_frame = tk.Frame(self.root, bg="#08080A", padx=20, pady=14)
        btn_frame.pack(fill="x")

        tk.Button(
            btn_frame,
            text="GUARDAR CONFIGURACION",
            command=self._handle_apply,
            bg="#E10600",
            fg="#FFFFFF",
            activebackground="#B80500",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            padx=16,
            pady=9,
            relief="flat",
            cursor="hand2",
        ).pack(fill="x")

        lan_ip = get_local_lan_ip()
        self.lbl_status = tk.Label(
            self.root,
            text=f"STANDBY  |  WS STREAM {lan_ip}:8765  |  ESPERANDO ASSETTO CORSA COMPETIZIONE",
            fg="#71717A",
            bg="#08080A",
            font=("Consolas", 8),
        )
        self.lbl_status.pack(anchor="w", padx=20, pady=(4, 4))

    def set_live_connection_status(self, is_live: bool, track: str = "", car: str = "") -> None:
        if is_live:
            self.lbl_status.configure(
                text=f"ONLINE 333 HZ  |  {car.upper()} @ {track.upper()}",
                fg="#10B981",
            )
        else:
            lan_ip = get_local_lan_ip()
            self.lbl_status.configure(
                text=f"STANDBY  |  WS STREAM {lan_ip}:8765  |  ESPERANDO SESION EN PISTA DE ACC",
                fg="#71717A",
            )

    def _handle_apply(self) -> None:
        mode = self.selected_mode.get().strip()
        if mode not in ("keyboard", "gamepad", "wheel"):
            messagebox.showwarning(
                "Seleccion Requerida",
                "Selecciona tu periferico de entrada (Teclado, Mando o Volante).",
            )
            return

        self.config["input_mode"] = mode
        self.config["wheel_type"] = self.wheel_model_var.get().strip()
        self.config["agent_token"] = self.token_var.get().strip()
        self.config["voice_enabled"] = bool(self.voice_var.get())
        save_agent_config(self.config)
        self.on_config_applied(self.config)
