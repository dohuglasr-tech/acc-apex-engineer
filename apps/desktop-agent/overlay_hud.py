"""
ACC Apex Engineer Pro - Overlay HUD In-Game con Avatar Animado en Tiempo Real (overlay_hud.py)
Incluye:
  1. Avatar animado con ojos parpadeantes y boca que modula al hablar (lip-sync en vivo)
  2. Transcripción y subtítulos en pantalla de lo que dice el Ingeniero de Pista IA
  3. Telemetría esencial en vivo (Velocidad, Marcha, RPM, Presiones PSI, Setup)
  4. Ventana transparente click-through con estilos extendidos Win32
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import math
import time
import tkinter as tk
from typing import Optional
from shm_reader import TelemetrySample

user32 = ctypes.windll.user32

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

HWND_TOPMOST = wintypes.HWND(-1)
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

if hasattr(user32, "SetWindowLongPtrW"):
    user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
else:
    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
    user32.SetWindowLongW.restype = ctypes.c_long
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = ctypes.c_long

user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_uint,
]
user32.SetWindowPos.restype = wintypes.BOOL

if hasattr(user32, "GetAncestor"):
    user32.GetAncestor.argtypes = [wintypes.HWND, ctypes.c_uint]
    user32.GetAncestor.restype = wintypes.HWND

if hasattr(user32, "GetParent"):
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND

if hasattr(user32, "FindWindowW"):
    user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.FindWindowW.restype = wintypes.HWND

if hasattr(user32, "GetForegroundWindow"):
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND

if hasattr(user32, "GetDesktopWindow"):
    user32.GetDesktopWindow.argtypes = []
    user32.GetDesktopWindow.restype = wintypes.HWND

if hasattr(user32, "MonitorFromWindow"):
    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.MonitorFromWindow.restype = wintypes.HMONITOR

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]

class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]

if hasattr(user32, "GetMonitorInfoW"):
    user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
    user32.GetMonitorInfoW.restype = wintypes.BOOL


class AgentAvatarCanvas(tk.Canvas):
    """
    Avatar dinámico del Ingeniero de Pista con ojos parpadeantes
    y boca que modula y gesticula en tiempo real cuando habla por radio.
    """

    def __init__(self, parent: tk.Widget, size: int = 76, **kwargs) -> None:
        super().__init__(
            parent,
            width=size,
            height=size,
            bg="#08080A",
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self.size = size
        self._center_x = size / 2.0
        self._center_y = size / 2.0

        # Estado de animación
        self._blink_start_ts = 0.0
        self._next_blink_ts = time.time() + 2.5
        self._is_blinking = False

    def draw_frame(self, is_speaking: bool, steer_angle: float = 0.0) -> None:
        self.delete("all")
        cx, cy = self._center_x, self._center_y
        now = time.time()

        # 1. Parpadeo de ojos natural
        if now >= self._next_blink_ts:
            self._is_blinking = True
            self._blink_start_ts = now
            self._next_blink_ts = now + 3.0 + (math.sin(now) * 1.2)

        blink_ratio = 1.0
        if self._is_blinking:
            dt = now - self._blink_start_ts
            if dt < 0.12:
                # Ojo cerrándose
                blink_ratio = max(0.1, 1.0 - (dt / 0.06))
            elif dt < 0.24:
                # Ojo abriéndose
                blink_ratio = min(1.0, (dt - 0.06) / 0.06)
            else:
                self._is_blinking = False
                blink_ratio = 1.0

        # Desplazamiento de pupilas con la dirección (-2 a +2 px)
        eye_steer_offset = max(-2.5, min(2.5, steer_angle / 30.0))

        # 2. Base de la cabeza (círculo digital de alta tecnología)
        head_radius = 22.0
        head_fill = "#14141E" if not is_speaking else "#1A1A28"
        head_outline = "#2A2A3E" if not is_speaking else "#E10600"

        self.create_oval(
            cx - head_radius,
            cy - head_radius,
            cx + head_radius,
            cy + head_radius,
            fill=head_fill,
            outline=head_outline,
            width=2,
        )

        # 3. Auriculares / Diadema de Ingeniero de Pista (Racing Headset)
        # Arco superior
        self.create_arc(
            cx - head_radius - 5,
            cy - head_radius - 8,
            cx + head_radius + 5,
            cy + head_radius - 4,
            start=15,
            extent=150,
            style="arc",
            outline="#3F3F46",
            width=3,
        )

        # Auricular izquierdo y derecho
        self.create_oval(
            cx - head_radius - 5,
            cy - 7,
            cx - head_radius + 2,
            cy + 9,
            fill="#09090D",
            outline="#E10600" if is_speaking else "#27272A",
            width=2,
        )
        self.create_oval(
            cx + head_radius - 2,
            cy - 7,
            cx + head_radius + 5,
            cy + 9,
            fill="#09090D",
            outline="#E10600" if is_speaking else "#27272A",
            width=2,
        )

        # LED de estado en auricular (Verde = Escuchando/Standby, Rojo Pulsante = Hablando)
        led_color = "#10B981"
        if is_speaking:
            led_color = "#EF4444" if int(now * 8) % 2 == 0 else "#DC2626"

        self.create_oval(
            cx - head_radius - 3,
            cy - 2,
            cx - head_radius + 1,
            cy + 2,
            fill=led_color,
            outline="",
        )

        # Brazo del micrófono que baja hacia la boca
        self.create_line(
            cx - head_radius + 1,
            cy + 5,
            cx - 8,
            cy + 13,
            cx - 3,
            cy + 12,
            fill="#71717A",
            width=2,
            smooth=True,
        )
        # Cápsula del micrófono
        mic_color = "#EF4444" if is_speaking else "#A1A1AA"
        self.create_oval(
            cx - 5,
            cy + 10,
            cx - 1,
            cy + 14,
            fill=mic_color,
            outline="",
        )

        # Si está hablando, ondas de sonido sutiles saliendo del micrófono
        if is_speaking:
            wave_phase = (now * 5.0) % 1.0
            wave_radius = 4 + wave_phase * 7
            self.create_arc(
                cx - 3 - wave_radius,
                cy + 12 - wave_radius,
                cx - 3 + wave_radius,
                cy + 12 + wave_radius,
                start=290,
                extent=100,
                style="arc",
                outline="#EF4444",
                width=1,
            )

        # 4. OJOS DINÁMICOS
        eye_y = cy - 4.0
        eye_w = 4.5
        eye_h = max(0.8, 5.0 * blink_ratio)

        left_eye_x = cx - 8.0
        right_eye_x = cx + 8.0

        # Ojo izquierdo
        self.create_oval(
            left_eye_x - eye_w,
            eye_y - eye_h,
            left_eye_x + eye_w,
            eye_y + eye_h,
            fill="#38BDF8" if not is_speaking else "#60A5FA",
            outline="",
        )
        # Ojo derecho
        self.create_oval(
            right_eye_x - eye_w,
            eye_y - eye_h,
            right_eye_x + eye_w,
            eye_y + eye_h,
            fill="#38BDF8" if not is_speaking else "#60A5FA",
            outline="",
        )

        # Pupilas (si el ojo está suficientemente abierto)
        if blink_ratio > 0.4:
            pupil_r = 1.8
            self.create_oval(
                left_eye_x + eye_steer_offset - pupil_r,
                eye_y - pupil_r,
                left_eye_x + eye_steer_offset + pupil_r,
                eye_y + pupil_r,
                fill="#0369A1",
                outline="",
            )
            self.create_oval(
                right_eye_x + eye_steer_offset - pupil_r,
                eye_y - pupil_r,
                right_eye_x + eye_steer_offset + pupil_r,
                eye_y + pupil_r,
                fill="#0369A1",
                outline="",
            )

        # 5. BOCA ANIMADA EN TIEMPO REAL (LIP-SYNC)
        mouth_y = cy + 9.0
        if is_speaking:
            # Modulación dinámica de apertura según tiempo y frecuencias de voz
            osc1 = abs(math.sin(now * 16.0))
            osc2 = abs(math.sin(now * 27.0))
            open_factor = 0.6 * osc1 + 0.4 * osc2

            m_half_w = 6.0 + 2.0 * osc1
            m_half_h = max(1.2, 5.5 * open_factor)

            # Cavidad bucal animada
            self.create_oval(
                cx - m_half_w,
                mouth_y - m_half_h,
                cx + m_half_w,
                mouth_y + m_half_h,
                fill="#7F1D1D",
                outline="#EF4444",
                width=1.5,
            )
            # Diente/brillo superior sutil
            if m_half_h > 2.5:
                self.create_line(
                    cx - m_half_w * 0.6,
                    mouth_y - m_half_h + 1,
                    cx + m_half_w * 0.6,
                    mouth_y - m_half_h + 1,
                    fill="#FFFFFF",
                    width=1.5,
                )
        else:
            # Boca en reposo: sonrisa amigable y atenta
            self.create_line(
                cx - 7.0,
                mouth_y,
                cx,
                mouth_y + 2.2,
                cx + 7.0,
                mouth_y,
                smooth=True,
                fill="#38BDF8",
                width=2,
            )


class OverlayHUD:
    """
    Overlay HUD In-Game click-through con avatar animado y transcripción
    de radio en tiempo real sobre Assetto Corsa Competizione.
    Diseñado con prioridad de hardware Z para sobreponerse sin importar
    la configuración de pantalla (Pantalla Completa, Borderless, 1080p, 1440p, 4K, Ultrawide).
    """

    def __init__(
        self,
        root: tk.Tk,
        input_mode: str = "gamepad",
        hud_enabled: bool = True,
        hud_position: str = "top_right",
    ) -> None:
        self.root = root
        self.input_mode = input_mode
        self.voice_mode = "companion"
        self.last_setup_label = "EN ESPERA"
        self.hud_enabled = hud_enabled
        self.hud_position = hud_position  # "top_right", "top_left", "bottom_center", "bottom_right"
        self._visible = False
        self._current_radio_text = ""
        self._is_speaking = False
        self._preview_until: float = 0.0
        self._last_topmost_reinforce: float = 0.0
        self._last_reposition_ts: float = 0.0

        self.win = tk.Toplevel(self.root)
        self.win.title("ACC Apex Telemetría & Ingeniero IA")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.94)
        self.win.configure(bg="#08080A")
        try:
            self.win.transient(None)
        except Exception:
            pass

        self._build_widgets()
        self.reposition_on_game_screen(force=True)
        self.win.after(100, self._apply_click_through)
        self.win.withdraw()

    def set_hud_enabled(self, enabled: bool) -> None:
        """Activa o desactiva la visibilidad del HUD in-game."""
        self.hud_enabled = bool(enabled)
        if not self.hud_enabled and self._visible:
            self.win.withdraw()
            self._visible = False

    def set_hud_position(self, position: str) -> None:
        """Cambia la ubicación del HUD en la pantalla (top_right, top_left, bottom_center, bottom_right)."""
        if position in ("top_right", "top_left", "bottom_center", "bottom_right"):
            self.hud_position = position
            self.reposition_on_game_screen(force=True)

    def _get_toplevel_hwnd(self) -> int:
        """Obtiene de manera segura el HWND raíz del contenedor Win32 de Tkinter."""
        try:
            self.win.update_idletasks()
            w_id = self.win.winfo_id()
            if hasattr(user32, "GetAncestor"):
                root_h = user32.GetAncestor(w_id, 2)  # GA_ROOT
                if root_h:
                    return root_h
            if hasattr(user32, "GetParent"):
                p_id = user32.GetParent(w_id)
                if p_id:
                    return p_id
            return w_id
        except Exception:
            return 0

    def show_preview(self, duration_sec: float = 6.0) -> None:
        """Muestra una vista previa temporal del HUD para verificar posición y sobreposición en pantalla."""
        self._preview_until = time.time() + duration_sec
        self.reposition_on_game_screen(force=True)
        if not self._visible:
            self.win.deiconify()
            self.win.update_idletasks()
            self._apply_click_through()
            self._visible = True
        self.enforce_topmost()

    def reposition_on_game_screen(self, force: bool = False) -> None:
        """
        Detecta en qué monitor corre Assetto Corsa Competizione (o el escritorio principal)
        y posiciona el HUD en las coordenadas exactas de esa pantalla (1080p, 1440p, 4K, Ultrawide).
        """
        now = time.time()
        if not force and (now - self._last_reposition_ts) < 2.5:
            return
        self._last_reposition_ts = now

        try:
            hwnd_target = user32.FindWindowW(None, "Assetto Corsa Competizione")
            if not hwnd_target:
                hwnd_target = user32.GetForegroundWindow() or user32.GetDesktopWindow()

            h_mon = user32.MonitorFromWindow(hwnd_target, 2)  # MONITOR_DEFAULTTONEAREST
            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            res = user32.GetMonitorInfoW(h_mon, ctypes.byref(mi))

            if res and (mi.rcMonitor.right > mi.rcMonitor.left):
                mon_l = mi.rcMonitor.left
                mon_t = mi.rcMonitor.top
                mon_w = mi.rcMonitor.right - mi.rcMonitor.left
                mon_h = mi.rcMonitor.bottom - mi.rcMonitor.top
            else:
                mon_l = 0
                mon_t = 0
                try:
                    mon_w = max(1280, self.win.winfo_screenwidth())
                    mon_h = max(720, self.win.winfo_screenheight())
                except Exception:
                    mon_w = 1920
                    mon_h = 1080

            hud_w = 520
            hud_h = 194

            pos = self.hud_position
            if pos == "top_left":
                x = mon_l + 24
                y = mon_t + 24
            elif pos == "bottom_center":
                x = mon_l + max(24, (mon_w - hud_w) // 2)
                y = mon_t + max(24, mon_h - hud_h - 40)
            elif pos == "bottom_right":
                x = mon_l + max(24, mon_w - hud_w - 24)
                y = mon_t + max(24, mon_h - hud_h - 40)
            else:  # "top_right" por defecto
                x = mon_l + max(24, mon_w - hud_w - 24)
                y = mon_t + 24

            self.win.geometry(f"{hud_w}x{hud_h}+{x}+{y}")
        except Exception:
            pass

    def enforce_topmost(self) -> None:
        """
        Refuerza periódicamente la prioridad Z de hardware para mantener el HUD
        permanentemente sobre la ventana de ACC incluso en pantalla completa exclusiva o borderless.
        """
        now = time.time()
        if (now - self._last_topmost_reinforce) < 0.30:
            return
        self._last_topmost_reinforce = now

        try:
            self.win.lift()
            root_h = self._get_toplevel_hwnd()
            if root_h:
                user32.SetWindowPos(
                    root_h,
                    HWND_TOPMOST,
                    0,
                    0,
                    0,
                    0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
                )
        except Exception:
            pass

    def _apply_click_through(self) -> None:
        """
        Aplica estilos extendidos Win32 transparentes y de click-through a nivel de hardware.
        Se aplica exclusivamente a la ventana raíz para no afectar el renderizado de los widgets internos.
        """
        try:
            root_h = self._get_toplevel_hwnd()
            if not root_h:
                return

            if hasattr(user32, "GetWindowLongPtrW"):
                cur = user32.GetWindowLongPtrW(root_h, GWL_EXSTYLE)
            else:
                cur = user32.GetWindowLongW(root_h, GWL_EXSTYLE)

            new_style = (
                cur
                | WS_EX_LAYERED
                | WS_EX_TRANSPARENT
                | WS_EX_TOPMOST
                | WS_EX_TOOLWINDOW
                | WS_EX_NOACTIVATE
            )

            if hasattr(user32, "SetWindowLongPtrW"):
                user32.SetWindowLongPtrW(root_h, GWL_EXSTYLE, new_style)
            else:
                user32.SetWindowLongW(root_h, GWL_EXSTYLE, new_style)

            user32.SetWindowPos(
                root_h,
                HWND_TOPMOST,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
            )
        except Exception:
            pass

    def _build_widgets(self) -> None:
        # Barra superior roja de acento
        top_bar = tk.Frame(self.win, bg="#E10600", height=3)
        top_bar.pack(fill="x")

        # Contenedor superior: Avatar a la izquierda + Telemetría a la derecha
        top_container = tk.Frame(self.win, bg="#08080A")
        top_container.pack(fill="x", padx=10, pady=(6, 2))

        # 1. Columna del Avatar
        avatar_col = tk.Frame(top_container, bg="#08080A")
        avatar_col.pack(side="left", padx=(0, 10))

        self.avatar_canvas = AgentAvatarCanvas(avatar_col, size=74)
        self.avatar_canvas.pack()

        self.lbl_avatar_tag = tk.Label(
            avatar_col,
            text="ÁLVARO // IA",
            fg="#A1A1AA",
            bg="#08080A",
            font=("Consolas", 8, "bold"),
        )
        self.lbl_avatar_tag.pack(pady=(2, 0))

        # 2. Columna de Telemetría
        telemetry_col = tk.Frame(top_container, bg="#08080A")
        telemetry_col.pack(side="left", fill="both", expand=True)

        header_row = tk.Frame(telemetry_col, bg="#08080A")
        header_row.pack(fill="x")

        self.lbl_title = tk.Label(
            header_row,
            text="APEX INGENIERO // 333 HZ",
            fg="#FFFFFF",
            bg="#08080A",
            font=("Consolas", 9, "bold"),
        )
        self.lbl_title.pack(side="left")

        mode_es = {"keyboard": "TECLADO", "gamepad": "MANDO", "wheel": "VOLANTE"}.get(
            self.input_mode, "VOLANTE"
        )
        self.lbl_mode = tk.Label(
            header_row,
            text=mode_es,
            fg="#E10600",
            bg="#08080A",
            font=("Consolas", 9, "bold"),
        )
        self.lbl_mode.pack(side="right")

        # Métricas de velocidad, marcha y rpm
        self.lbl_speed_gear = tk.Label(
            telemetry_col,
            text="000 KMH   M-N   0000 RPM",
            fg="#FFFFFF",
            bg="#08080A",
            font=("Consolas", 12, "bold"),
        )
        self.lbl_speed_gear.pack(anchor="w", pady=(2, 0))

        # Presiones en caliente
        self.lbl_tyres = tk.Label(
            telemetry_col,
            text="PSI  DI --.-  DD --.-  TI --.-  TD --.-",
            fg="#A1A1AA",
            bg="#08080A",
            font=("Consolas", 8),
        )
        self.lbl_tyres.pack(anchor="w")

        # Desgaste de neumáticos y combustible
        self.lbl_wear = tk.Label(
            telemetry_col,
            text="GOMAS: 0% DESGASTE (100% VIDA) | --.-L",
            fg="#10B981",
            bg="#08080A",
            font=("Consolas", 8),
        )
        self.lbl_wear.pack(anchor="w")

        # Estado del setup rotativo en garaje / alerta
        self.lbl_setup = tk.Label(
            telemetry_col,
            text=f"GARAJE: {self.last_setup_label}",
            fg="#A1A1AA",
            bg="#08080A",
            font=("Consolas", 8),
        )
        self.lbl_setup.pack(anchor="w")

        # 3. Contenedor Inferior: Subtítulo de lo que dice el Ingeniero en Vivo
        self.speech_card = tk.Frame(
            self.win,
            bg="#111116",
            highlightthickness=1,
            highlightbackground="#27272A",
            padx=8,
            pady=4,
        )
        self.speech_card.pack(fill="x", padx=10, pady=(4, 6))

        speech_hdr = tk.Frame(self.speech_card, bg="#111116")
        speech_hdr.pack(fill="x")

        self.lbl_radio_status = tk.Label(
            speech_hdr,
            text="RADIO EN VIVO // ÁLVARO",
            fg="#E10600",
            bg="#111116",
            font=("Consolas", 8, "bold"),
        )
        self.lbl_radio_status.pack(side="left")

        self.lbl_radio_sub = tk.Label(
            self.speech_card,
            text="Adelante, mantén el ritmo. Te avisaré de cada frenada.",
            fg="#FFFFFF",
            bg="#111116",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=485,
        )
        self.lbl_radio_sub.pack(fill="x", pady=(2, 0))

    def set_input_mode(self, mode: str) -> None:
        self.input_mode = mode
        mode_es = {"keyboard": "TECLADO", "gamepad": "MANDO", "wheel": "VOLANTE"}.get(
            mode, mode.upper()
        )
        self.lbl_mode.configure(text=mode_es)

    def set_voice_mode(self, mode: str) -> None:
        if mode in ("companion", "car_state", "telemetry"):
            self.voice_mode = mode
            mode_text = {
                "companion": "RADIO // ACOMPAÑANTE",
                "car_state": "RADIO // ESTADO COCHE",
                "telemetry": "RADIO // SOLO TELEMETRÍA",
            }.get(mode, "RADIO // ÁLVARO")
            self.lbl_radio_status.configure(text=mode_text)

    def set_setup_status(self, status_text: str) -> None:
        self.last_setup_label = status_text
        self.lbl_setup.configure(text=f"GARAJE: {status_text}", fg="#10B981")

    def update_telemetry(
        self,
        sample: Optional[TelemetrySample],
        live_alert: Optional[str] = None,
        radio_text: str = "",
        is_speaking: bool = False,
        avg_fuel_per_lap: float = 0.0,
    ) -> None:
        now = time.time()

        # Si el usuario solicitó vista previa desde el panel (botón 'PROBAR HUD')
        if now < self._preview_until:
            if not self._visible:
                self.win.deiconify()
                self.win.update_idletasks()
                self._apply_click_through()
                self._visible = True
            self.enforce_topmost()
            self.reposition_on_game_screen()

            self.avatar_canvas.draw_frame(is_speaking=True, steer_angle=15.0)
            self.lbl_avatar_tag.configure(text="HABLANDO...", fg="#E10600")
            self.lbl_radio_status.configure(text="VISTA PREVIA // HUD ACTIVO", fg="#E10600")
            self.speech_card.configure(highlightbackground="#E10600")
            self.lbl_radio_sub.configure(
                text="HUD sobrepuesto sobre pantalla completa. Transmisión de radio y telemetría 333 Hz en vivo."
            )
            self.lbl_speed_gear.configure(text="182 KMH   M-4   7210 RPM")
            self.lbl_tyres.configure(
                text="PSI  DI 26.8  DD 26.9  TI 26.8  TD 26.8", fg="#10B981"
            )
            self.lbl_wear.configure(
                text="GOMAS: 3% DESGASTE (97% VIDA) · DI 97% DD 97% TI 97% TD 97% | 42.0L (-3.4L/vta)",
                fg="#10B981",
            )
            self.lbl_setup.configure(text="GARAJE: APEX_SETUP_1 (ESTABLE)", fg="#10B981")
            return

        if not self.hud_enabled or sample is None or not sample.is_live_acc:
            if self._visible:
                self.win.withdraw()
                self._visible = False
            return

        if not self._visible:
            self.reposition_on_game_screen(force=True)
            self.win.deiconify()
            self.win.update_idletasks()
            self._apply_click_through()
            self._visible = True

        # Mantener sobrepuesto y en la posición del monitor de ACC
        self.enforce_topmost()
        self.reposition_on_game_screen()

        self._is_speaking = is_speaking

        # Actualizar animación de avatar (ojos + boca)
        self.avatar_canvas.draw_frame(
            is_speaking=is_speaking,
            steer_angle=sample.steer_angle,
        )

        # Actualizar etiqueta bajo el avatar
        if is_speaking:
            self.lbl_avatar_tag.configure(text="HABLANDO...", fg="#E10600")
            self.lbl_radio_status.configure(text="TRANSMITIENDO EN CABINA", fg="#E10600")
            self.speech_card.configure(highlightbackground="#E10600")
        else:
            self.lbl_avatar_tag.configure(text="ÁLVARO · IA", fg="#A1A1AA")
            self.lbl_radio_status.configure(text="RADIO EN VIVO // ÁLVARO", fg="#10B981")
            self.speech_card.configure(highlightbackground="#27272A")

        # Actualizar transcripción de subtítulos
        if radio_text:
            self._current_radio_text = radio_text
            self.lbl_radio_sub.configure(text=radio_text)
        elif not self._current_radio_text:
            self.lbl_radio_sub.configure(
                text="Adelante compañero, acelerador a fondo. Te cantaré las curvas."
            )

        # Telemetría básica
        gear_str = "R" if sample.gear < 0 else ("N" if sample.gear == 0 else str(sample.gear))
        self.lbl_speed_gear.configure(
            text=f"{sample.speed_kmh:03.0f} KMH   M-{gear_str}   {sample.rpms:04d} RPM"
        )

        p = sample.tyre_pressures
        in_window = all(26.65 <= x <= 27.05 for x in p)
        psi_color = "#10B981" if in_window else "#F59E0B"
        self.lbl_tyres.configure(
            text=f"PSI  DI {p[0]:.1f}  DD {p[1]:.1f}  TI {p[2]:.1f}  TD {p[3]:.1f}",
            fg=psi_color,
        )

        w = sample.tyre_wear or [3.0, 3.0, 3.0, 3.0]
        w_pct = [round(max(0.0, min(100.0, (1.0 - (val / 3.0)) * 100.0))) for val in w]
        avg_w = int(sum(w_pct) / 4.0)
        avg_life = max(0, 100 - avg_w)
        wear_color = "#10B981" if avg_w < 15 else ("#F59E0B" if avg_w < 35 else "#EF4444")
        fuel_str = (
            f"{sample.fuel:.1f}L (-{avg_fuel_per_lap:.1f}L/vta)"
            if avg_fuel_per_lap > 0
            else f"{sample.fuel:.1f}L"
        )
        self.lbl_wear.configure(
            text=f"GOMAS: {avg_w}% DESGASTE ({avg_life}% VIDA) · DI {w_pct[0]}% DD {w_pct[1]}% TI {w_pct[2]}% TD {w_pct[3]}% | {fuel_str}",
            fg=wear_color,
        )

        if live_alert:
            self.lbl_setup.configure(text=f"AVISO: {live_alert}", fg="#E10600")
        else:
            self.lbl_setup.configure(text=f"GARAJE: {self.last_setup_label}", fg="#A1A1AA")
