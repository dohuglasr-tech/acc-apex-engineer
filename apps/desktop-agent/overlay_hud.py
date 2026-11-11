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
import math
import time
import tkinter as tk
from typing import Optional
from shm_reader import TelemetrySample

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008


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
    """

    def __init__(self, root: tk.Tk, input_mode: str = "wheel") -> None:
        self.root = root
        self.input_mode = input_mode
        self.voice_mode = "companion"
        self.last_setup_label = "EN ESPERA"
        self._visible = False
        self._current_radio_text = ""
        self._is_speaking = False

        self.win = tk.Toplevel(self.root)
        self.win.title("ACC Apex Telemetría & Ingeniero IA")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.92)
        self.win.configure(bg="#08080A")

        screen_w = self.win.winfo_screenwidth()
        # Dimensiones optimizadas para acomodar el avatar y los subtítulos
        self.win.geometry(f"520x175+{screen_w - 540}+24")

        self._build_widgets()
        self.win.after(150, self._apply_click_through)
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

        # Estado del setup / alerta
        self.lbl_setup = tk.Label(
            telemetry_col,
            text=f"SETUP: {self.last_setup_label}",
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
        self.lbl_setup.configure(text=f"SETUP: {status_text}")

    def update_telemetry(
        self,
        sample: Optional[TelemetrySample],
        live_alert: Optional[str] = None,
        radio_text: str = "",
        is_speaking: bool = False,
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
            self.win.lift()
            self.win.attributes("-topmost", True)

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

        if live_alert:
            self.lbl_setup.configure(text=f"AVISO: {live_alert}", fg="#E10600")
        else:
            w = sample.tyre_wear or [3.0, 3.0, 3.0, 3.0]
            w_pct = [round(max(0.0, min(100.0, (1.0 - (val / 3.0)) * 100.0))) for val in w]
            avg_w = int(sum(w_pct) / 4.0)
            avg_life = max(0, 100 - avg_w)
            wear_color = "#10B981" if avg_w < 15 else ("#F59E0B" if avg_w < 35 else "#EF4444")
            self.lbl_setup.configure(
                text=f"DESGASTE {avg_w}% ({avg_life}% VIDA) · DI {w_pct[0]}% DD {w_pct[1]}% TI {w_pct[2]}% TD {w_pct[3]}% | {sample.fuel:.1f}L",
                fg=wear_color,
            )
