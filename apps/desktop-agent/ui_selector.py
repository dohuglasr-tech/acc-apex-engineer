"""
ACC Apex Engineer Pro - Ventana Inicial Obligatoria de Selección de Periférico (ui_selector.py)
Regla 3 del Plan Maestro:
  Al iniciar sesión en el ejecutable, el sistema pregunta obligatoriamente con qué periférico
  juega el usuario (Teclado, Mando o Volante) para adaptar toda la física del setup y el análisis de errores.
"""

from __future__ import annotations

import json
import os
import socket
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Callable, Dict, Any


CONFIG_PATH = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".acc_apex_engineer" / "agent_config.json"


def load_agent_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "input_mode": "",  # Vacío al inicio para obligar a elegir Teclado, Mando o Volante
        "wheel_type": "Logitech G29 / G923",
        "agent_token": "",
        "supabase_url": os.environ.get("NEXT_PUBLIC_SUPABASE_URL", ""),
        "supabase_anon_key": os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", ""),
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
    """
    Panel de control del Agente Ejecutable Local (.exe):
      - Selección obligatoria entre TECLADO, MANDO (Gamepad) o VOLANTE
      - Vinculación con cuenta privada de Discord/Supabase mediante Agent Token
      - Botón para Inyectar Setup Ahora Mismo en Documents\\Assetto Corsa Competizione\\Setups
    """

    def __init__(
        self,
        root: tk.Tk,
        config: Dict[str, Any],
        on_config_applied: Callable[[Dict[str, Any]], None],
        on_force_inject: Callable[[], str],
    ) -> None:
        self.root = root
        self.config = config
        self.on_config_applied = on_config_applied
        self.on_force_inject = on_force_inject

        self.root.title("ACC Apex Engineer Pro · Agente Local 333 Hz")
        self.root.geometry("620x610")
        self.root.configure(bg="#0B0F19")
        self.root.resizable(False, False)

        self.selected_mode = tk.StringVar(value=config.get("input_mode") or "")
        self.wheel_model_var = tk.StringVar(value=config.get("wheel_type") or "Logitech G29 / G923")
        self.token_var = tk.StringVar(value=config.get("agent_token") or "")
        self.supa_url_var = tk.StringVar(value=config.get("supabase_url") or "")
        self.supa_key_var = tk.StringVar(value=config.get("supabase_anon_key") or "")
        self.voice_var = tk.BooleanVar(value=bool(config.get("voice_enabled", True)))

        self._build_ui()

    def _build_ui(self) -> None:
        # Encabezado
        hdr = tk.Frame(self.root, bg="#111827", pady=12, padx=18)
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text="🏎️ ACC APEX ENGINEER PRO · AGENTE LOCAL 333 Hz",
            fg="#38BDF8",
            bg="#111827",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w")
        tk.Label(
            hdr,
            text="Lectura Física 333 Hz + Auto-Inyector de Setups (.json) · NUNCA modifica controls.json",
            fg="#9CA3AF",
            bg="#111827",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 0))

        # Paso 1 Obligatorio: Selección de Periférico
        step1 = tk.LabelFrame(
            self.root,
            text=" 1. SELECCIÓN OBLIGATORIA: ¿CON QUÉ PERIFÉRICO JUEGAS? ",
            fg="#FBBF24",
            bg="#0B0F19",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=10,
        )
        step1.pack(fill="x", padx=16, pady=(12, 8))

        modes = [
            (
                "keyboard",
                "⌨️  TECLADO (Keyboard)",
                "Steer Ratio suave (16-18), Brake Torque 93%, ABS 5, TC progresivo anti-pulsación binaria W/A/S/D",
            ),
            (
                "gamepad",
                "🎮  MANDO / GAMEPAD (Xbox / DualSense)",
                "Slow Rebound delantero anti-latigazo de gatillo LT/L2, Steer Ratio 15:1 y margen trasero +0.5%",
            ),
            (
                "wheel",
                "🛞  VOLANTE FFB (Direct Drive / Gear / Belt)",
                "Steer Ratio directo (12-14), Brake Torque 100%, ABS 2-3 y Rake aerodinámico agresivo",
            ),
        ]

        for val, title, desc in modes:
            row = tk.Frame(step1, bg="#161F30", pady=6, padx=10)
            row.pack(fill="x", pady=3)
            rb = tk.Radiobutton(
                row,
                text=title,
                variable=self.selected_mode,
                value=val,
                fg="#F9FAFB",
                bg="#161F30",
                selectcolor="#0B0F19",
                activebackground="#161F30",
                activeforeground="#38BDF8",
                font=("Segoe UI", 10, "bold"),
            )
            rb.pack(anchor="w")
            tk.Label(
                row,
                text=desc,
                fg="#9CA3AF",
                bg="#161F30",
                font=("Segoe UI", 8),
            ).pack(anchor="w", padx=22)

        # Paso 2: Vinculación privada con cuenta de Discord / Supabase
        step2 = tk.LabelFrame(
            self.root,
            text=" 2. VINCULACIÓN PRIVADA CON TU CUENTA DISCORD / SUPABASE (RLS) ",
            fg="#34D399",
            bg="#0B0F19",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=8,
        )
        step2.pack(fill="x", padx=16, pady=6)

        tk.Label(
            step2,
            text="Token de Agente Personal (cópialo desde la pestaña 'Descargar .exe' en la Web):",
            fg="#D1D5DB",
            bg="#0B0F19",
            font=("Segoe UI", 9),
        ).pack(anchor="w")
        tk.Entry(
            step2,
            textvariable=self.token_var,
            bg="#1F2937",
            fg="#F9FAFB",
            insertbackground="#F9FAFB",
            font=("Consolas", 10),
        ).pack(fill="x", pady=(2, 6))

        url_frame = tk.Frame(step2, bg="#0B0F19")
        url_frame.pack(fill="x")
        tk.Label(url_frame, text="Supabase URL:", fg="#9CA3AF", bg="#0B0F19", font=("Segoe UI", 8)).grid(
            row=0, column=0, sticky="w"
        )
        tk.Entry(
            url_frame,
            textvariable=self.supa_url_var,
            bg="#1F2937",
            fg="#D1D5DB",
            font=("Consolas", 8),
            width=42,
        ).grid(row=0, column=1, padx=6, pady=2, sticky="ew")

        tk.Label(url_frame, text="Supabase Anon Key:", fg="#9CA3AF", bg="#0B0F19", font=("Segoe UI", 8)).grid(
            row=1, column=0, sticky="w"
        )
        tk.Entry(
            url_frame,
            textvariable=self.supa_key_var,
            bg="#1F2937",
            fg="#D1D5DB",
            font=("Consolas", 8),
            width=42,
        ).grid(row=1, column=1, padx=6, pady=2, sticky="ew")
        url_frame.columnconfigure(1, weight=1)

        tk.Checkbutton(
            step2,
            text="Activar Ingeniero de Pista por Voz en Español (canta vueltas, errores y setups)",
            variable=self.voice_var,
            fg="#E5E7EB",
            bg="#0B0F19",
            selectcolor="#111827",
            activebackground="#0B0F19",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 0))

        # Botones de Acción
        btn_frame = tk.Frame(self.root, bg="#0B0F19")
        btn_frame.pack(fill="x", padx=16, pady=8)

        tk.Button(
            btn_frame,
            text="✅ GUARDAR MODO Y ACTIVAR TELEMETRÍA 333 Hz",
            command=self._handle_apply,
            bg="#0284C7",
            fg="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=8,
            relief="flat",
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        tk.Button(
            btn_frame,
            text="⚡ AUTO-INYECTAR SETUP AHORA",
            command=self._handle_force_inject,
            bg="#059669",
            fg="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=8,
            relief="flat",
        ).pack(side="right")

        # Estado en vivo e IP LAN para QR móvil
        lan_ip = get_local_lan_ip()
        self.lbl_status = tk.Label(
            self.root,
            text=f"Stream WebSocket 60 FPS activo en ws://{lan_ip}:8765 · Esperando selección de periférico...",
            fg="#38BDF8",
            bg="#0B0F19",
            font=("Consolas", 9),
        )
        self.lbl_status.pack(anchor="w", padx=18, pady=(2, 4))

    def _handle_apply(self) -> None:
        mode = self.selected_mode.get().strip()
        if mode not in ("keyboard", "gamepad", "wheel"):
            messagebox.showwarning(
                "Selección Obligatoria",
                "Por favor selecciona primero con qué periférico juegas:\n• Teclado\n• Mando (Gamepad)\n• Volante",
            )
            return

        self.config["input_mode"] = mode
        self.config["wheel_type"] = self.wheel_model_var.get().strip()
        self.config["agent_token"] = self.token_var.get().strip()
        self.config["supabase_url"] = self.supa_url_var.get().strip()
        self.config["supabase_anon_key"] = self.supa_key_var.get().strip()
        self.config["voice_enabled"] = bool(self.voice_var.get())
        save_agent_config(self.config)
        self.on_config_applied(self.config)

        mode_es = {"keyboard": "TECLADO", "gamepad": "MANDO", "wheel": "VOLANTE"}[mode]
        self.lbl_status.configure(
            text=f"✓ MODO {mode_es} ACTIVO · Leyendo 333 Hz y auto-inyectando en Documents\\Assetto Corsa Competizione\\Setups",
            fg="#34D399",
        )

    def _handle_force_inject(self) -> None:
        mode = self.selected_mode.get().strip()
        if mode not in ("keyboard", "gamepad", "wheel"):
            messagebox.showwarning(
                "Selección Obligatoria",
                "Selecciona primero Teclado, Mando o Volante antes de inyectar el setup.",
            )
            return
        self._handle_apply()
        path_str = self.on_force_inject()
        messagebox.showinfo(
            "Setup Auto-Inyectado en ACC",
            f"Se ha generado e inyectado exitosamente el setup para {mode.upper()} en:\n\n{path_str}\n\n"
            "Entra al garaje de ACC -> Setups y carga 'APEX_AUTO_LIVE'.",
        )

