"""
ACC Apex Engineer Pro - Ventana de Configuración y Guía Paso a Paso del Agente Local (ui_selector.py)
Diseño en español estilo F1 Timing, con lista de verificación en vivo (Paso 1, Paso 2, Paso 3)
y botón directo para abrir el panel web.
"""

from __future__ import annotations

import json
import os
import socket
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox
from typing import Any, Callable, Dict, Optional, Tuple


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
DEFAULT_AGENT_TOKEN = ""
DEFAULT_GEMINI_KEY = ""
WEB_DASHBOARD_URL = "https://acc-apex-engineer.vercel.app/dashboard"


def load_agent_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if not cfg.get("supabase_url"):
                cfg["supabase_url"] = DEFAULT_SUPABASE_URL
            if not cfg.get("supabase_anon_key"):
                cfg["supabase_anon_key"] = DEFAULT_SUPABASE_ANON_KEY
            if cfg.get("agent_token") is None:
                cfg["agent_token"] = ""
            if not cfg.get("input_mode"):
                cfg["input_mode"] = "gamepad"
            if not cfg.get("driving_style"):
                cfg["driving_style"] = "safe"
            if not cfg.get("gemini_api_key"):
                cfg["gemini_api_key"] = os.environ.get("GEMINI_API_KEY", DEFAULT_GEMINI_KEY)
            return cfg
        except Exception:
            pass
    return {
        "input_mode": "gamepad",
        "driving_style": "safe",
        "wheel_type": "",
        "agent_token": "",
        "supabase_url": DEFAULT_SUPABASE_URL,
        "supabase_anon_key": DEFAULT_SUPABASE_ANON_KEY,
        "voice_enabled": True,
        "gemini_api_key": os.environ.get("GEMINI_API_KEY", DEFAULT_GEMINI_KEY),
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


MODE_NAMES_ES = {
    "keyboard": "TECLADO",
    "gamepad": "MANDO / CONTROLADOR",
    "wheel": "VOLANTE Y PEDALES FFB",
}


class InputModeSelectorWindow:
    def __init__(
        self,
        root: tk.Tk,
        config: Dict[str, Any],
        on_config_applied: Callable[[Dict[str, Any]], None],
        on_test_gemini: Callable[[], tuple[bool, str]] | None = None,
    ) -> None:
        self.root = root
        self.config = config
        self.on_config_applied = on_config_applied
        self.on_test_gemini = on_test_gemini
        self.linked_username: str = ""

        self.root.title("ACC APEX ENGINEER // AGENTE DE TELEMETRÍA")
        self.root.geometry("660x880")
        self.root.configure(bg="#08080A")
        self.root.resizable(False, False)

        self.selected_mode = tk.StringVar(value=config.get("input_mode") or "gamepad")
        self.driving_style_var = tk.StringVar(value=config.get("driving_style") or "safe")
        self.wheel_model_var = tk.StringVar(value=config.get("wheel_type") or "")
        self.token_var = tk.StringVar(
            value=config.get("agent_token") or DEFAULT_AGENT_TOKEN
        )
        self.voice_var = tk.BooleanVar(value=bool(config.get("voice_enabled", True)))
        self.gemini_key_var = tk.StringVar(
            value=config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
        )

        # Auto-guardado instantáneo de Token y Gemini Key en cada pulsación o pegado
        self.token_var.trace_add("write", self._on_field_auto_save)
        self.gemini_key_var.trace_add("write", self._on_field_auto_save)

        # Protocolo de cierre de ventana para asegurar que todo quede guardado en disco
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self._build_ui()

    def _build_ui(self) -> None:
        top_accent = tk.Frame(self.root, bg="#E10600", height=4)
        top_accent.pack(fill="x")

        hdr = tk.Frame(self.root, bg="#0E0E12", pady=12, padx=20)
        hdr.pack(fill="x")

        hdr_top = tk.Frame(hdr, bg="#0E0E12")
        hdr_top.pack(fill="x")

        tk.Label(
            hdr_top,
            text="APEX ENGINEER // MOTOR DE TELEMETRÍA A 333 HZ",
            fg="#FFFFFF",
            bg="#0E0E12",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left")

        tk.Button(
            hdr_top,
            text="ABRIR PANEL WEB",
            command=lambda: webbrowser.open(WEB_DASHBOARD_URL),
            bg="#1F1F28",
            fg="#FFFFFF",
            activebackground="#E10600",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 8, "bold"),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
        ).pack(side="right")

        tk.Label(
            hdr,
            text="Mantén esta ventana abierta mientras juegas para enviar telemetría en vivo e inyectar setups.",
            fg="#A1A1AA",
            bg="#0E0E12",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 0))

        # LISTA DE VERIFICACIÓN PASO A PASO (ARRIBA PARA MÁXIMA CLARIDAD)
        steps_frame = tk.Frame(
            self.root,
            bg="#111116",
            padx=16,
            pady=12,
            highlightthickness=1,
            highlightbackground="#27272A",
        )
        steps_frame.pack(fill="x", padx=20, pady=(12, 6))

        tk.Label(
            steps_frame,
            text="ESTADO DE ACTIVACIÓN EN TIEMPO REAL (3 PASOS)",
            fg="#FFFFFF",
            bg="#111116",
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        self.lbl_step1 = tk.Label(
            steps_frame,
            text="[1/3] CUENTA Y PERIFÉRICO: Conectando con tu cuenta...",
            fg="#F59E0B",
            bg="#111116",
            font=("Consolas", 9),
        )
        self.lbl_step1.pack(anchor="w", pady=2)

        self.lbl_step2 = tk.Label(
            steps_frame,
            text="[2/3] ENLACE CON LA WEB: Sincronizando puente en la nube...",
            fg="#F59E0B",
            bg="#111116",
            font=("Consolas", 9),
        )
        self.lbl_step2.pack(anchor="w", pady=2)

        self.lbl_step3 = tk.Label(
            steps_frame,
            text="[3/3] JUEGO ACC: EN ESPERA — Abre ACC, inicia carrera y pulsa CONDUCIR",
            fg="#A1A1AA",
            bg="#111116",
            font=("Consolas", 9, "bold"),
        )
        self.lbl_step3.pack(anchor="w", pady=2)

        # SECCIÓN 1: PERIFÉRICO
        step1 = tk.Frame(self.root, bg="#08080A", padx=20, pady=6)
        step1.pack(fill="x")

        tk.Label(
            step1,
            text="01 / ELIGE TU PERIFÉRICO DE CONDUCCIÓN",
            fg="#E10600",
            bg="#08080A",
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        modes = [
            (
                "keyboard",
                "TECLADO",
                "Dirección 16-18, Fuerza de freno 93%, ABS 5, curva de tracción progresiva.",
            ),
            (
                "gamepad",
                "MANDO / CONTROLADOR",
                "Extensión lenta delantera compensada, Dirección 15:1, margen aero +0.5%.",
            ),
            (
                "wheel",
                "VOLANTE Y PEDALES FFB",
                "Dirección directa 12-14, Fuerza de freno 100%, ABS 2-3, rotación máxima.",
            ),
        ]

        for val, title, desc in modes:
            row = tk.Frame(step1, bg="#121217", pady=6, padx=12, bd=1, relief="flat")
            row.pack(fill="x", pady=2)
            rb = tk.Radiobutton(
                row,
                text=title,
                variable=self.selected_mode,
                value=val,
                command=self._handle_apply,
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

        # SECCIÓN 1-B: ESTILO DE CONDUCCIÓN
        step1b = tk.Frame(self.root, bg="#08080A", padx=20, pady=4)
        step1b.pack(fill="x")

        tk.Label(
            step1b,
            text="01-B / ESTILO Y TIPO DE CONDUCCIÓN DEL PILOTO",
            fg="#E10600",
            bg="#08080A",
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        styles = [
            (
                "aggressive",
                "AGRESIVO (LATE-BRAKING & MÁXIMA ROTACIÓN)",
                "Rotación ágil en deceleración, menor precarga diferencial, alerón de velocidad punta, pastillas Sprint.",
            ),
            (
                "safe",
                "SEGURO / CONSISTENTE (ESTABILIDAD & EQUILIBRIO)",
                "Mayor carga aerodinámica, diferencial 60-80 Nm, frenada neutra y lineal, desgaste regular de gomas.",
            ),
            (
                "beginner",
                "PRINCIPIANTE (SUBVIRAJE PREVENTIVO & ASISTENCIAS)",
                "Anti-trompo activo, estabilizadora delantera firme, ABS 5-6, TC 5-6, altura delantera elevada.",
            ),
        ]

        for s_val, s_title, s_desc in styles:
            s_row = tk.Frame(step1b, bg="#121217", pady=4, padx=12, bd=1, relief="flat")
            s_row.pack(fill="x", pady=2)
            s_rb = tk.Radiobutton(
                s_row,
                text=s_title,
                variable=self.driving_style_var,
                value=s_val,
                command=self._handle_apply,
                fg="#FFFFFF",
                bg="#121217",
                selectcolor="#08080A",
                activebackground="#121217",
                activeforeground="#E10600",
                font=("Segoe UI", 9, "bold"),
            )
            s_rb.pack(anchor="w")
            tk.Label(
                s_row,
                text=s_desc,
                fg="#A1A1AA",
                bg="#121217",
                font=("Segoe UI", 8),
            ).pack(anchor="w", padx=22)

        # SECCIÓN 2: TOKEN
        step2 = tk.Frame(self.root, bg="#08080A", padx=20, pady=6)
        step2.pack(fill="x")

        tk.Label(
            step2,
            text="02 / TOKEN INDIVIDUAL DE VINCULACIÓN CON LA WEB",
            fg="#E10600",
            bg="#08080A",
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        self.entry_token = tk.Entry(
            step2,
            textvariable=self.token_var,
            bg="#121217",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief="flat",
            font=("Consolas", 10),
        )
        self.entry_token.pack(fill="x", ipady=5, pady=(0, 6))
        self.entry_token.bind("<Return>", lambda e: self._handle_apply())
        self.entry_token.bind("<FocusOut>", lambda e: self._handle_apply())

        tk.Checkbutton(
            step2,
            text="Ingeniero de pista por voz neuronal en español activo durante sesión en pista",
            variable=self.voice_var,
            command=self._handle_apply,
            fg="#D4D4D8",
            bg="#08080A",
            selectcolor="#121217",
            activebackground="#08080A",
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        # SECCIÓN 3: GOOGLE GEMINI AI
        step3 = tk.Frame(self.root, bg="#08080A", padx=20, pady=4)
        step3.pack(fill="x")

        gemini_hdr = tk.Frame(step3, bg="#08080A")
        gemini_hdr.pack(fill="x")

        tk.Label(
            gemini_hdr,
            text="03 / CEREBRO DE IA GOOGLE GEMINI",
            fg="#E10600",
            bg="#08080A",
            font=("Consolas", 9, "bold"),
        ).pack(side="left")

        tk.Label(
            gemini_hdr,
            text="(COACHING INTELIGENTE Y CONSEJOS EN VIVO)",
            fg="#71717A",
            bg="#08080A",
            font=("Consolas", 8),
        ).pack(side="left", padx=6)

        self.entry_gemini = tk.Entry(
            step3,
            textvariable=self.gemini_key_var,
            bg="#121217",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief="flat",
            font=("Consolas", 9),
            show="*",
        )
        self.entry_gemini.pack(fill="x", ipady=4, pady=(2, 2))
        self.entry_gemini.bind("<Return>", lambda e: self._handle_test_gemini())
        self.entry_gemini.bind("<FocusOut>", lambda e: self._handle_apply())

        gemini_test_row = tk.Frame(step3, bg="#08080A")
        gemini_test_row.pack(fill="x", pady=(4, 2))

        self.btn_test_gemini = tk.Button(
            gemini_test_row,
            text="PROBAR RADIO GEMINI",
            command=self._handle_test_gemini,
            bg="#27272A",
            fg="#FFFFFF",
            activebackground="#10B981",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 8, "bold"),
            padx=10,
            pady=3,
            relief="flat",
            cursor="hand2",
        )
        self.btn_test_gemini.pack(side="left")

        self.lbl_gemini_status = tk.Label(
            gemini_test_row,
            text="● GOOGLE GEMINI 3.5 FLASH ACTIVO" if self.gemini_key_var.get().strip() else "○ MOTOR ANALÍTICO LOCAL (SIN CLAVE)",
            fg="#10B981" if self.gemini_key_var.get().strip() else "#71717A",
            bg="#08080A",
            font=("Consolas", 8, "bold"),
        )
        self.lbl_gemini_status.pack(side="left", padx=10)

        tk.Label(
            step3,
            text="Pega tu GEMINI_API_KEY para análisis con IA de Google (o déjalo en blanco para motor analítico local).",
            fg="#71717A",
            bg="#08080A",
            font=("Segoe UI", 8),
        ).pack(anchor="w")

        btn_frame = tk.Frame(self.root, bg="#08080A", padx=20, pady=10)
        btn_frame.pack(fill="x")

        self.btn_save = tk.Button(
            btn_frame,
            text="GUARDAR Y VINCULAR CON LA WEB",
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
        )
        self.btn_save.pack(fill="x")

        lan_ip = get_local_lan_ip()
        self.lbl_status = tk.Label(
            self.root,
            text=f"STREAM LOCAL {lan_ip}:8765  |  PUENTE NUBE SUPABASE ACTIVO",
            fg="#71717A",
            bg="#08080A",
            font=("Consolas", 8),
        )
        self.lbl_status.pack(anchor="w", padx=20, pady=(2, 4))

    def _on_field_auto_save(self, *args: Any) -> None:
        """Guarda inmediatamente en disco cualquier cambio en Token o Gemini Key."""
        token = self.token_var.get().strip()
        key = self.gemini_key_var.get().strip()
        if token:
            self.config["agent_token"] = token
        self.config["gemini_api_key"] = key
        save_agent_config(self.config)

        if hasattr(self, "lbl_gemini_status"):
            if key:
                self.lbl_gemini_status.configure(
                    text="● GOOGLE GEMINI LISTO PARA CONECTAR", fg="#10B981"
                )
            else:
                self.lbl_gemini_status.configure(
                    text="○ MOTOR ANALÍTICO LOCAL (SIN CLAVE)", fg="#71717A"
                )

    def _on_window_close(self) -> None:
        """Asegura que todos los valores se guarden en disco al cerrar la ventana con la X."""
        try:
            self.config["agent_token"] = self.token_var.get().strip()
            self.config["gemini_api_key"] = self.gemini_key_var.get().strip()
            self.config["input_mode"] = self.selected_mode.get().strip() or "gamepad"
            self.config["driving_style"] = self.driving_style_var.get().strip() or "safe"
            self.config["voice_enabled"] = bool(self.voice_var.get())
            save_agent_config(self.config)
        except Exception:
            pass
        self.root.destroy()

    def _handle_test_gemini(self) -> None:
        if not self.on_test_gemini:
            return

        # Persistir la API key en disco antes de probar
        key = self.gemini_key_var.get().strip()
        self.config["gemini_api_key"] = key
        save_agent_config(self.config)

        self.btn_test_gemini.configure(text="CONECTANDO A GEMINI...", bg="#52525B")
        self.lbl_gemini_status.configure(text="Conectando con Google GenAI...", fg="#F59E0B")
        self.root.update_idletasks()

        def _bg_test() -> None:
            ok, msg = self.on_test_gemini()
            def _update() -> None:
                self.btn_test_gemini.configure(text="PROBAR RADIO GEMINI", bg="#27272A")
                if ok:
                    self.lbl_gemini_status.configure(
                        text="● GEMINI 3.5 FLASH CONECTADO Y TRANSMITIENDO", fg="#10B981"
                    )
                else:
                    self.lbl_gemini_status.configure(
                        text=f"✖ {msg[:45]}", fg="#EF4444"
                    )
            self.root.after(0, _update)

        import threading
        threading.Thread(target=_bg_test, daemon=True).start()

    def set_sync_feedback(
        self, success: bool, message: str, username: str = "", mode: str = ""
    ) -> None:
        mode_es = MODE_NAMES_ES.get(mode, mode.upper())
        if success:
            self.linked_username = username or "PILOTO"
            self.btn_save.configure(
                bg="#10B981",
                activebackground="#059669",
                text=f"CONECTADO CON LA WEB ({mode_es}) — GUARDADO",
            )
            self.lbl_step1.configure(
                text=f"[1/3] CUENTA Y PERIFÉRICO: COMPLETADO (Piloto: {self.linked_username.upper()} · {mode_es})",
                fg="#10B981",
            )
            self.lbl_step2.configure(
                text="[2/3] ENLACE CON LA WEB: CONECTADO — Sincronización en tiempo real activa",
                fg="#10B981",
            )
        else:
            self.lbl_step1.configure(
                text=f"[1/3] PERIFÉRICO: {mode_es} (Verifica el token de la web)",
                fg="#F59E0B",
            )
            self.lbl_step2.configure(
                text=f"[2/3] ENLACE CON LA WEB: {message}",
                fg="#F59E0B",
            )

    def set_live_connection_status(
        self, is_live: bool, track: str = "", car: str = "", speed_kmh: float = 0.0
    ) -> None:
        if is_live:
            self.lbl_step3.configure(
                text=f"[3/3] JUEGO ACC: EN PISTA A 333 HZ ({car.upper()} @ {track.upper()} · {speed_kmh:.0f} KM/H)",
                fg="#10B981",
            )
            self.lbl_status.configure(
                text=f"TRANSMITIENDO TELEMETRÍA EN VIVO A LA WEB  |  {car.upper()} @ {track.upper()}",
                fg="#10B981",
            )
        else:
            self.lbl_step3.configure(
                text="[3/3] JUEGO ACC: EN ESPERA — Entra a pista en ACC y pulsa CONDUCIR (DRIVE)",
                fg="#F59E0B",
            )
            lan_ip = get_local_lan_ip()
            self.lbl_status.configure(
                text=f"AGENTE LISTO ({lan_ip}:8765)  |  ESPERANDO QUE SALGAS A PISTA EN ACC",
                fg="#A1A1AA",
            )

    def _handle_apply(self) -> None:
        mode = self.selected_mode.get().strip()
        if mode not in ("keyboard", "gamepad", "wheel"):
            messagebox.showwarning(
                "Selección Requerida",
                "Selecciona tu periférico de conducción (Teclado, Mando o Volante).",
            )
            return

        self.btn_save.configure(text="SINCRONIZANDO CON LA WEB...", bg="#52525B")
        self.root.update_idletasks()

        self.config["input_mode"] = mode
        self.config["driving_style"] = self.driving_style_var.get().strip() or "safe"
        self.config["wheel_type"] = self.wheel_model_var.get().strip()
        self.config["agent_token"] = (
            self.token_var.get().strip() or DEFAULT_AGENT_TOKEN
        )
        self.config["voice_enabled"] = bool(self.voice_var.get())
        self.config["gemini_api_key"] = self.gemini_key_var.get().strip()
        save_agent_config(self.config)
        self.on_config_applied(self.config)
