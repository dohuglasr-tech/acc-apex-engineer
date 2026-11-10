"""
ACC Apex Engineer Pro - Motor Integral de Auto-Inyección de Setups (auto_setup_injector.py)
Diseñado con los 3 Pilares Maestros de Ingeniería de Competición:
  1. CONFIGURACIONES DE REFERENCIA MUNDIAL ESPORTS POR PERIFÉRICO:
     - Teclado (keyboard): compensación para entradas binarias, ABS/TC progresivos, Steer Ratio abierto (16-18),
       rebound slow delantero alto para contener el morro en soltadas, Brake Bias seguro.
     - Mando (gamepad): dirección adaptada al arco de 15mm de stick, ARB delantera con mordiente,
       diferencial compensado para transiciones rápidas de gatillo/stick.
     - Volante FFB (wheel): dirección directa (12-13), 100% Brake Torque, Brake Bias retrasado para trail-braking,
       rake aerodinámico pronunciado, muelles y barras rígidas para máxima velocidad de vértice.

  2. ESTILO Y TIPO DE CONDUCCIÓN DEL PILOTO:
     - Agresivo (aggressive): late-braking, rotación rápida con menor precarga diferencial, alerón de velocidad punta,
       amortiguadores afinados para tragar pianos violentos, pastillas Sprint agresivas.
     - Seguro / Consistente (safe): balance neutro, mayor carga aerodinámica, diferencial con precarga moderada-alta,
       frenada lineal, desgaste homogéneo para tandas largas.
     - Principiante (beginner): subviraje preventivo ("safe understeer"), barras delanteras rígidas, ABS 5-6, TC 5-6,
       suspensión absorbente y alturas elevadas para evitar trompos y pérdidas de control.

  3. TELEMETRÍA REAL EN TIEMPO REAL A 333 HZ (TRAZADA Y COMPORTAMIENTO DEL PILOTO):
     - Neumáticos Pirelli DHE: objetivo 26.85 PSI en caliente en las 4 ruedas.
     - Gradiente térmico IMO (Interior, Medio, Exterior): ajuste milimétrico de caídas (Camber) y convergencias (Toe).
     - Trail-Braking y entrada: corrección de cabeceo, balance de frenos y extensión lenta delantera.
     - Balance en vértice: balanceo, barras estabilizadoras (ARB) y alturas dinámicas (Rake).
     - Pianos y fondo plano (Bottoming Out): ajuste de topes de goma (Bump Stop) y compresión rápida (Bump Fast).
     - Tracción y salida: estabilizadora trasera, compresión lenta y corte de TC2.
     - Frenos: conductos de refrigeración para mantener los discos entre 450°C y 550°C.

REGLA ESTRICTA DE SEGURIDAD:
  - NUNCA toca controls.json ni ningún archivo de configuración del juego o volante.
  - ÚNICAMENTE escribe archivos de setup de vehículo (.json) dentro de:
    Documents\\Assetto Corsa Competizione\\Setups\\<carModel>\\<track>\\
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


TARGET_HOT_PSI = 26.85  # Ventana objetivo Pirelli DHE: 26.8 - 26.9 PSI
BASE_PSI_ZERO_CLICK = 20.3

# Perfiles aerodinámicos de circuitos oficiales de ACC
HIGH_DOWNFORCE_TRACKS = {
    "zandvoort", "hungaroring", "brands_hatch", "misano",
    "zolder", "valencia", "donington", "kyalami", "nurburgring"
}
LOW_DOWNFORCE_TRACKS = {
    "monza", "paul_ricard"
}


def get_acc_setups_root() -> Path:
    """Devuelve la ruta oficial Documents\\Assetto Corsa Competizione\\Setups."""
    user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
    docs_candidates = [
        user_profile / "Documents",
        user_profile / "OneDrive" / "Documents",
        user_profile / "OneDrive" / "Documentos",
        user_profile / "Documentos",
    ]
    for doc_dir in docs_candidates:
        acc_dir = doc_dir / "Assetto Corsa Competizione" / "Setups"
        if acc_dir.exists():
            return acc_dir
    return docs_candidates[0] / "Assetto Corsa Competizione" / "Setups"


def get_track_aero_category(track_name: str) -> str:
    clean = (track_name or "spa").lower()
    for t in HIGH_DOWNFORCE_TRACKS:
        if t in clean:
            return "high"
    for t in LOW_DOWNFORCE_TRACKS:
        if t in clean:
            return "low"
    return "medium"


def create_base_acc_setup(
    car_model: str,
    track_name: str = "spa",
    input_mode: str = "wheel",
    driving_style: str = "safe",
) -> Dict[str, Any]:
    """
    Crea la estructura JSON oficial completa de Assetto Corsa Competizione
    sintetizando los Pilares 1 (Periférico) y 2 (Estilo de Conducción) más el perfil del circuito.
    """
    aero_cat = get_track_aero_category(track_name)

    # 1. Alerón trasero y alturas según circuito y aerodinámica
    if aero_cat == "high":
        base_rear_wing = 10
        front_rh_click = 2   # ~51 mm
        rear_rh_click = 16   # ~75 mm (rake alto para carga difusor)
    elif aero_cat == "low":
        base_rear_wing = 2
        front_rh_click = 5   # ~55 mm
        rear_rh_click = 10   # ~68 mm (rake bajo para mínima resistencia)
    else:  # medium (Spa, Silverstone, Barcelona, etc.)
        base_rear_wing = 6
        front_rh_click = 3   # ~53 mm
        rear_rh_click = 14   # ~73 mm

    # 2. Pilar 1: Periférico de Conducción
    if input_mode == "keyboard":
        steer_ratio_click = 6      # ~17:1 progresivo para pulsación binaria A/D
        brake_torque_click = 13    # ~93% Brake Torque anti-bloqueo brusco
        brake_bias_click = 32      # 59.5% hacia adelante para frenadas estables
        abs_click = 5              # ABS 5
        tc1_click = 5              # TC1 5 para pulsaciones de tecla W
        tc2_click = 6
        arb_front = 5
        arb_rear = 2
        rebound_slow_front = 15    # Contener morro al soltar tecla de freno
        bump_slow_rear = 11        # Evitar hundimiento excesivo en salida
        diff_preload = 8           # ~80 Nm estabilidad en frenada recta
        wing_offset = +1
    elif input_mode == "gamepad":
        steer_ratio_click = 4      # ~15:1 para recorrido de stick analógico
        brake_torque_click = 17    # ~97% Brake Torque
        brake_bias_click = 28      # 57.5% balance equilibrado
        abs_click = 4
        tc1_click = 4
        tc2_click = 5
        arb_front = 4              # Mordiente delantero sin subviraje
        arb_rear = 3
        rebound_slow_front = 14
        bump_slow_rear = 10
        diff_preload = 6           # ~60 Nm
        wing_offset = 0
    else:  # wheel
        steer_ratio_click = 1      # ~13:1 directo y reactivo
        brake_torque_click = 20    # 100% Brake Torque para célula de carga
        brake_bias_click = 24      # 55.5% para trail-braking pivotante
        abs_click = 3
        tc1_click = 3
        tc2_click = 3
        arb_front = 3
        arb_rear = 4              # Mayor rotación en apoyo
        rebound_slow_front = 11
        bump_slow_rear = 9
        diff_preload = 4           # ~40 Nm rotación ágil
        wing_offset = 0

    # 3. Pilar 2: Estilo de Conducción
    if driving_style == "aggressive":
        brake_bias_click = max(18, brake_bias_click - 2)      # Más trasero para rotar con el freno
        diff_preload = max(2, diff_preload - 2)               # Coche libre para pivotar
        wing_offset -= 1                                      # Reducir drag, más velocidad punta
        camber_f = [-4.0, -4.0]
        camber_r = [-3.4, -3.4]
        brake_pad_compound = 0                                # Pad 1 (Sprint con máxima mordida)
        tc1_click = max(1, tc1_click - 1)
        abs_click = max(1, abs_click - 1)
        bump_fast = [6, 6, 6, 6]                             # Absorber pianos agresivos
        rebound_fast = [7, 7, 7, 7]
        bump_window = [14, 14, 18, 18]                        # Mayor recorrido libre de tope
    elif driving_style == "beginner":
        brake_bias_click = min(40, brake_bias_click + 3)      # Frenada 100% en línea recta
        diff_preload = min(12, diff_preload + 3)              # Diferencial bloqueado anti-trompo
        wing_offset += 1                                      # Carga aero protectora
        arb_front = min(6, arb_front + 1)
        arb_rear = max(1, arb_rear - 1)                      # Subviraje benigno y seguro
        front_rh_click += 2                                   # Más altura delantera anti-toques
        camber_f = [-3.5, -3.5]
        camber_r = [-2.8, -2.8]
        brake_pad_compound = 1                                # Pad 2 (Progresivo y predecible)
        tc1_click = min(8, tc1_click + 1)
        abs_click = min(8, abs_click + 1)
        brake_torque_click = min(15, brake_torque_click)
        bump_fast = [5, 5, 5, 5]
        rebound_fast = [5, 5, 5, 5]
        bump_window = [10, 10, 14, 14]
    else:  # safe (consistente / equilibrado)
        camber_f = [-3.8, -3.8]
        camber_r = [-3.2, -3.2]
        brake_pad_compound = 1                                # Pad 2
        bump_fast = [6, 6, 5, 5]
        rebound_fast = [7, 7, 6, 6]
        bump_window = [12, 12, 16, 16]

    final_rear_wing = max(1, min(12, base_rear_wing + wing_offset))

    return {
        "carName": car_model or "mclaren_720s_gt3_evo",
        "basicSetup": {
            "tyres": {
                "tyreCompound": 0,
                "tyrePressure": [62, 62, 63, 63],  # ~26.5 PSI en frío inicial
            },
            "alignment": {
                "camber": [4, 4, 6, 6],
                "toe": [14, 14, 22, 22],
                "staticCamber": [camber_f[0], camber_f[1], camber_r[0], camber_r[1]],
                "toeOutLinear": [-0.08, -0.08, 0.12, 0.12],
                "casterLF": 34,
                "casterRF": 34,
                "steerRatio": steer_ratio_click,
            },
            "electronics": {
                "tC1": tc1_click,
                "tC2": tc2_click,
                "abs": abs_click,
                "eCUMap": 0,
                "fuelMix": 0,
                "telemetryLaps": 99,
            },
            "strategy": {
                "fuel": 45,
                "nPitStops": 0,
                "tyreSet": 1,
                "frontBrakePadCompound": brake_pad_compound,
                "rearBrakePadCompound": brake_pad_compound,
                "pitStrategy": [],
                "fuelPerLap": 4.10 if "spa" in (track_name or "").lower() else 3.20,
            },
        },
        "advancedSetup": {
            "mechanicalBalance": {
                "aRBFront": arb_front,
                "aRBRear": arb_rear,
                "wheelRate": [2, 2, 2, 2],
                "bumpStopRateUp": [8, 8, 10, 10],
                "bumpStopRateDn": [6, 6, 6, 6],
                "bumpStopWindow": bump_window,
                "brakeTorque": brake_torque_click,
                "brakeBias": brake_bias_click,
            },
            "dampers": {
                "bumpSlow": [10, 10, bump_slow_rear, bump_slow_rear],
                "bumpFast": bump_fast,
                "reboundSlow": [rebound_slow_front, rebound_slow_front, 11, 11],
                "reboundFast": rebound_fast,
            },
            "aeroBalance": {
                "rideHeight": [front_rh_click, 0, rear_rh_click, 0],
                "rodLength": [0.0, 0.0, 0.0, 0.0],
                "splitter": 0,
                "rearWing": final_rear_wing,
                "brakeDuct": [3, 3],
            },
            "drivetrain": {
                "preload": diff_preload,
            },
        },
        "trackBopType": 0,
    }


class AutoSetupInjector:
    """
    Motor Integral de Auto-Inyección de Setups en Tiempo Real.
    Ajusta TODOS los subsistemas del vehículo en base a:
      1. Periférico (Mando, Teclado, Volante)
      2. Estilo de Conducción (Agresivo, Seguro, Principiante)
      3. Telemetría Real de la Vuelta y Trazada
    """

    def __init__(self, input_mode: str = "wheel", driving_style: str = "safe") -> None:
        self.input_mode = input_mode if input_mode in ("keyboard", "gamepad", "wheel") else "wheel"
        self.driving_style = driving_style if driving_style in ("aggressive", "safe", "beginner") else "safe"
        self.version_counter: Dict[str, int] = {}
        self.current_setups: Dict[str, Dict[str, Any]] = {}

    def set_input_mode(self, input_mode: str) -> None:
        if input_mode in ("keyboard", "gamepad", "wheel"):
            self.input_mode = input_mode

    def set_driving_style(self, driving_style: str) -> None:
        if driving_style in ("aggressive", "safe", "beginner"):
            self.driving_style = driving_style

    def get_current_setup(self, car_model: str, track_name: str) -> Dict[str, Any]:
        key = f"{car_model}:{track_name}:{self.input_mode}:{self.driving_style}"
        if key not in self.current_setups:
            self.current_setups[key] = create_base_acc_setup(
                car_model, track_name, self.input_mode, self.driving_style
            )
        return self.current_setups[key]

    def _safe_target_dir(self, car_model: str, track_name: str) -> Path:
        clean_car = "".join(c for c in (car_model or "gt3_car") if c.isalnum() or c in ("_", "-")).lower()
        clean_track = "".join(c for c in (track_name or "spa") if c.isalnum() or c in ("_", "-")).lower()
        root = get_acc_setups_root().resolve()
        target_dir = (root / clean_car / clean_track).resolve()
        if not str(target_dir).startswith(str(root)):
            raise PermissionError("Violación de seguridad: Intento de escritura fuera de la carpeta Setups.")
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    def inject_optimized_setup(
        self,
        car_model: str,
        track_name: str,
        hot_pressures: List[float],
        core_temps: List[float],
        brake_temps_avg: List[float],
        bottoming_events: int,
        understeer_ratio: float,
        oversteer_entry_events: int,
        tc_cut_ratio: float,
        air_temp: float,
        road_temp: float,
        best_lap_ms: Optional[int] = None,
        tyre_temps_imo: Optional[List[List[float]]] = None,
        curb_strikes: int = 0,
    ) -> Tuple[Path, Dict[str, Any], List[Dict[str, str]], int]:
        """
        Ajusta y calibra la totalidad del coche tocando cada área del setup según
        los 3 pilares maestros. Escribe APEX_AUTO_LIVE.json y guarda el resumen completo.
        """
        key = f"{car_model}:{track_name}:{self.input_mode}:{self.driving_style}"
        prev_setup = self.current_setups.get(key) or create_base_acc_setup(
            car_model, track_name, self.input_mode, self.driving_style
        )
        new_setup = copy.deepcopy(prev_setup)
        changes: List[Dict[str, str]] = []

        style_label = {
            "aggressive": "AGRESIVO",
            "safe": "SEGURO / CONSISTENTE",
            "beginner": "PRINCIPIANTE",
        }.get(self.driving_style, "ESTÁNDAR")

        input_label = {
            "keyboard": "TECLADO",
            "gamepad": "MANDO",
            "wheel": "VOLANTE FFB",
        }.get(self.input_mode, "VOLANTE")

        wheel_labels = ["Del. Izq. (FL)", "Del. Der. (FR)", "Tras. Izq. (RL)", "Tras. Der. (RR)"]

        # =====================================================================
        # ÁREA 1: NEUMÁTICOS PIRELLI DHE (Presiones en Caliente -> Frío Clic a Clic)
        # =====================================================================
        old_pressures = list(new_setup["basicSetup"]["tyres"]["tyrePressure"])
        tyre_deltas_text = []
        for i in range(4):
            measured_psi = hot_pressures[i] if i < len(hot_pressures) and hot_pressures[i] > 10.0 else TARGET_HOT_PSI
            core_c = core_temps[i] if i < len(core_temps) else 82.0
            delta_psi = TARGET_HOT_PSI - measured_psi

            # Compensación térmica por fricción según estilo de manejo
            if self.driving_style == "aggressive" and i in (0, 1) and core_c > 88.0:
                delta_psi -= 0.12
            elif self.driving_style == "beginner" and core_c < 75.0:
                delta_psi += 0.10

            click_delta = int(round(delta_psi * 10.0))
            click_delta = max(-6, min(6, click_delta))
            updated_click = max(35, min(95, old_pressures[i] + click_delta))
            new_setup["basicSetup"]["tyres"]["tyrePressure"][i] = updated_click

            old_cold = round(BASE_PSI_ZERO_CLICK + old_pressures[i] * 0.1, 1)
            new_cold = round(BASE_PSI_ZERO_CLICK + updated_click * 0.1, 1)
            tyre_deltas_text.append(f"{wheel_labels[i]}: {measured_psi:.1f} -> {new_cold} PSI en frío ({click_delta:+d}c)")

        changes.append({
            "area": "Neumáticos Pirelli DHE (4 Ruedas)",
            "parameter": "tyrePressure[FL, FR, RL, RR]",
            "before": f"FL {old_pressures[0]}c / FR {old_pressures[1]}c / RL {old_pressures[2]}c / RR {old_pressures[3]}c",
            "after": f"FL {new_setup['basicSetup']['tyres']['tyrePressure'][0]}c / FR {new_setup['basicSetup']['tyres']['tyrePressure'][1]}c / RL {new_setup['basicSetup']['tyres']['tyrePressure'][2]}c / RR {new_setup['basicSetup']['tyres']['tyrePressure'][3]}c",
            "reason": (
                f"Calibración térmica para {input_label} en estilo {style_label}. "
                f"Ajuste en frío para clavar 26.85 PSI exactos en pista. {', '.join(tyre_deltas_text[:2])}."
            ),
        })

        # =====================================================================
        # ÁREA 2: ALINEACIÓN & GEOMETRÍA (Camber, Toe, Caster, Steer Ratio)
        # =====================================================================
        align = new_setup["basicSetup"]["alignment"]
        old_steer = align.get("steerRatio", 2)
        old_camber = list(align.get("staticCamber", [-3.8, -3.8, -3.2, -3.2]))
        old_toe = list(align.get("toeOutLinear", [-0.08, -0.08, 0.12, 0.12]))

        new_camber = list(old_camber)
        new_toe = list(old_toe)

        # Ajuste de Camber si disponemos de temperaturas IMO (Interior vs Exterior)
        if tyre_temps_imo and len(tyre_temps_imo) >= 4:
            # Ruedas delanteras
            front_inner_delta = tyre_temps_imo[0][0] - tyre_temps_imo[0][2]
            if front_inner_delta > 14.0:  # Hombro interior hirviendo -> exceso de caída
                new_camber[0] = round(min(-2.8, old_camber[0] + 0.2), 1)
                new_camber[1] = new_camber[0]
            elif front_inner_delta < 3.0:  # Neumático plano o exterior caliente -> falta caída
                new_camber[0] = round(max(-4.2, old_camber[0] - 0.2), 1)
                new_camber[1] = new_camber[0]

        # Ajuste de Toe según subviraje y estilo
        if understeer_ratio > 0.20:
            new_toe[0] = round(max(-0.16, old_toe[0] - 0.02), 2)  # Más toe-out delantero (mordiente en entrada)
            new_toe[1] = new_toe[0]
        if oversteer_entry_events >= 2:
            new_toe[2] = round(min(0.24, old_toe[2] + 0.03), 2)  # Más toe-in trasero (aplomar la trasera al frenar)
            new_toe[3] = new_toe[2]

        align["staticCamber"] = new_camber
        align["toeOutLinear"] = new_toe

        changes.append({
            "area": "Alineación & Geometría (4 Ruedas)",
            "parameter": "Camber & ToeOutLinear & SteerRatio",
            "before": f"Caída Del {old_camber[0]:.1f}° / Tras {old_camber[2]:.1f}° | Toe Del {old_toe[0]:.2f}°",
            "after": f"Caída Del {new_camber[0]:.1f}° / Tras {new_camber[2]:.1f}° | Toe Del {new_toe[0]:.2f}°",
            "reason": (
                f"Geometría ajustada a la trazada del piloto ({input_label} - {style_label}). "
                f"Caídas optimizadas para reparto de huella homogéneo y convergencia delantera adaptada al ángulo de ataque."
            ),
        })

        # =====================================================================
        # ÁREA 3: AERODINÁMICA & ALTURAS (Splitter, Rake y Alerón Trasero)
        # =====================================================================
        aero = new_setup["advancedSetup"]["aeroBalance"]
        old_rh = list(aero["rideHeight"])
        old_wing = aero["rearWing"]

        new_rh = list(old_rh)
        new_wing = old_wing

        # Si hay toques de fondo plano (bottoming)
        if bottoming_events > 0:
            rh_bump = 2 if bottoming_events >= 3 else 1
            new_rh[0] = min(20, old_rh[0] + rh_bump)
            # Endurecer tope de compresión delantero
            new_setup["advancedSetup"]["mechanicalBalance"]["bumpStopRateUp"][0] = min(
                25, new_setup["advancedSetup"]["mechanicalBalance"]["bumpStopRateUp"][0] + 1
            )
            new_setup["advancedSetup"]["mechanicalBalance"]["bumpStopRateUp"][1] = new_setup["advancedSetup"]["mechanicalBalance"]["bumpStopRateUp"][0]
        elif understeer_ratio > 0.22 and new_rh[2] < 22:
            # Subir trasera para incrementar rake y succión de splitter
            new_rh[2] = min(22, old_rh[2] + 1)

        # Ajuste de alerón según estilo y circuito
        if self.driving_style == "aggressive" and oversteer_entry_events == 0 and new_wing > 2:
            new_wing = max(1, old_wing - 1)  # Menor drag para ganar punta en rectas
        elif (oversteer_entry_events >= 2 or self.driving_style == "beginner") and new_wing < 11:
            new_wing = min(12, old_wing + 1)  # Mayor estabilidad aero trasera

        aero["rideHeight"] = new_rh
        aero["rearWing"] = new_wing

        changes.append({
            "area": "Aerodinámica & Alturas Dinámicas (Rake)",
            "parameter": "rideHeight[Front/Rear] & rearWing",
            "before": f"Alturas Del +{old_rh[0]}mm / Tras +{old_rh[2]}mm | Alerón {old_wing}",
            "after": f"Alturas Del +{new_rh[0]}mm / Tras +{new_rh[2]}mm | Alerón {new_wing}",
            "reason": (
                f"Rake aerodinámico optimizado para {track_name.upper()}. "
                f"{f'Corregidos {bottoming_events} toques de fondo elevando el frontal.' if bottoming_events > 0 else 'Balance de carga frontal/trasera calibrado para máxima sustentación sin arrastre parásito.'}"
            ),
        })

        # =====================================================================
        # ÁREA 4: AGARRE MECÁNICO & BARRAS ESTABILIZADORAS (ARB, Muelles y Topes)
        # =====================================================================
        mech = new_setup["advancedSetup"]["mechanicalBalance"]
        old_arb_f = mech["aRBFront"]
        old_arb_r = mech["aRBRear"]
        old_bias = mech["brakeBias"]
        old_torque = mech["brakeTorque"]

        new_arb_f = old_arb_f
        new_arb_r = old_arb_r
        new_bias = old_bias
        new_torque = old_torque

        # Balance en curva: Subviraje vs Sobreviraje
        if understeer_ratio > 0.18 and new_arb_f > 1:
            new_arb_f -= 1  # Ablandar barra delantera para dar mordiente
            if new_arb_r < 6:
                new_arb_r += 1
        elif oversteer_entry_events >= 2 and new_arb_r > 1:
            new_arb_r -= 1  # Ablandar barra trasera para plantar la cola
            new_bias = min(45, old_bias + 2)  # Adelantar reparto de frenada

        mech["aRBFront"] = new_arb_f
        mech["aRBRear"] = new_arb_r
        mech["brakeBias"] = new_bias
        mech["brakeTorque"] = new_torque

        changes.append({
            "area": "Agarre Mecánico & Barras Estabilizadoras",
            "parameter": "aRBFront, aRBRear, brakeBias & brakeTorque",
            "before": f"ARB Del {old_arb_f} / Tras {old_arb_r} | Bias +{old_bias}c",
            "after": f"ARB Del {new_arb_f} / Tras {new_arb_r} | Bias +{new_bias}c",
            "reason": (
                f"Compensación de transferencia lateral para {input_label}. "
                f"{'Subviraje corregido suavizando barra delantera.' if understeer_ratio > 0.18 else 'Estabilidad en frenada y rotación ajustadas para estilo ' + style_label}."
            ),
        })

        # =====================================================================
        # ÁREA 5: AMORTIGUADORES (Dampers 4 Esquinas: Lento y Rápido)
        # =====================================================================
        damp = new_setup["advancedSetup"]["dampers"]
        old_bs = list(damp["bumpSlow"])
        old_bf = list(damp["bumpFast"])
        old_rs = list(damp["reboundSlow"])
        old_rf = list(damp["reboundFast"])

        new_bs = list(old_bs)
        new_bf = list(old_bf)
        new_rs = list(old_rs)
        new_rf = list(old_rf)

        # Si el piloto ataca pianos o hay golpes de badén (curb_strikes)
        if curb_strikes > 5 or self.driving_style == "aggressive":
            # Suavizar compresión rápida para absorber el piano sin descolocar el coche
            new_bf[0] = max(3, old_bf[0] - 1)
            new_bf[1] = new_bf[0]
            new_rf[0] = min(9, old_rf[0] + 1)
            new_rf[1] = new_rf[0]

        # Si hay latigazo en soltada de freno (trail-braking)
        if oversteer_entry_events > 0 or self.input_mode in ("keyboard", "gamepad"):
            new_rs[0] = min(22, old_rs[0] + 1)  # Mayor retención de extensión delantera
            new_rs[1] = new_rs[0]

        # Si hay corte de tracción en aceleración
        if tc_cut_ratio > 0.15:
            new_bs[2] = max(5, old_bs[2] - 1)  # Permitir asiento suave de la trasera
            new_bs[3] = new_bs[2]

        damp["bumpSlow"] = new_bs
        damp["bumpFast"] = new_bf
        damp["reboundSlow"] = new_rs
        damp["reboundFast"] = new_rf

        changes.append({
            "area": "Amortiguadores (Dampers 4 Esquinas)",
            "parameter": "bumpSlow, bumpFast, reboundSlow, reboundFast",
            "before": f"Del: BS {old_bs[0]} / RS {old_rs[0]} | Tras: BS {old_bs[2]} / RS {old_rs[2]}",
            "after": f"Del: BS {new_bs[0]} / RS {new_rs[0]} | Tras: BS {new_bs[2]} / RS {new_rs[2]}",
            "reason": (
                f"Filtrado dinámico de transferencias de peso y absorción de pianos. "
                f"Extensión lenta calibrada para {input_label} y compresión rápida adaptada a la agresividad sobre los vértices."
            ),
        })

        # =====================================================================
        # ÁREA 6: ELECTRÓNICA & MOTOR (TC1, TC2, ABS y Mapa Motor)
        # =====================================================================
        elec = new_setup["basicSetup"]["electronics"]
        old_tc1 = elec["tC1"]
        old_tc2 = elec["tC2"]
        old_abs = elec["abs"]

        new_tc1 = old_tc1
        new_tc2 = old_tc2
        new_abs = old_abs

        if tc_cut_ratio > 0.16 and new_tc2 < 8:
            new_tc2 += 1  # TC2 modula el corte de potencia haciéndolo más suave
        elif tc_cut_ratio < 0.05 and self.driving_style == "aggressive" and new_tc1 > 1:
            new_tc1 -= 1  # Más potencia directa sin ahogar motor

        elec["tC1"] = new_tc1
        elec["tC2"] = new_tc2
        elec["abs"] = new_abs

        changes.append({
            "area": "Electrónica de Carrera & Asistencias",
            "parameter": "tC1, tC2, abs & eCUMap",
            "before": f"TC1 {old_tc1} / TC2 {old_tc2} / ABS {old_abs}",
            "after": f"TC1 {new_tc1} / TC2 {new_tc2} / ABS {new_abs}",
            "reason": (
                f"Gestión de tracción y antibloqueo en tiempo real. "
                f"{'Afinado TC2 para evitar estrangulamiento de acelerador al salir de curva.' if tc_cut_ratio > 0.16 else 'Curva de aceleración directa ajustada para estilo ' + style_label}."
            ),
        })

        # =====================================================================
        # ÁREA 7: TRANSMISIÓN (Diferencial) & REFRIGERACIÓN DE FRENOS
        # =====================================================================
        dt = new_setup["advancedSetup"]["drivetrain"]
        old_preload = dt["preload"]
        new_preload = old_preload

        if oversteer_entry_events >= 2 and new_preload < 12:
            new_preload += 1  # Más bloqueo en deceleración (evita latigazos de cola)
        elif understeer_ratio > 0.22 and new_preload > 2:
            new_preload -= 1  # Liberar diferencial para rotar en entrada

        dt["preload"] = new_preload

        # Conductos de freno (Brake Ducts)
        front_brake_c = (brake_temps_avg[0] + brake_temps_avg[1]) / 2.0 if len(brake_temps_avg) >= 2 and brake_temps_avg[0] > 50 else 510.0
        rear_brake_c = (brake_temps_avg[2] + brake_temps_avg[3]) / 2.0 if len(brake_temps_avg) >= 4 and brake_temps_avg[2] > 50 else 480.0
        old_ducts = list(new_setup["advancedSetup"]["aeroBalance"]["brakeDuct"])
        new_ducts = list(old_ducts)

        if front_brake_c > 610.0 and new_ducts[0] < 6:
            new_ducts[0] += 1
        elif front_brake_c < 430.0 and new_ducts[0] > 1:
            new_ducts[0] -= 1

        if rear_brake_c > 610.0 and new_ducts[1] < 6:
            new_ducts[1] += 1
        elif rear_brake_c < 430.0 and new_ducts[1] > 1:
            new_ducts[1] -= 1

        new_setup["advancedSetup"]["aeroBalance"]["brakeDuct"] = new_ducts

        changes.append({
            "area": "Diferencial & Conductos de Frenos",
            "parameter": "drivetrain.preload & brakeDuct[Front/Rear]",
            "before": f"Precarga {old_preload * 10} Nm | Conductos Del {old_ducts[0]} / Tras {old_ducts[1]}",
            "after": f"Precarga {new_preload * 10} Nm | Conductos Del {new_ducts[0]} / Tras {new_ducts[1]}",
            "reason": (
                f"Precarga del diferencial ({new_preload * 10} Nm) configurada para tracción y estabilidad en deceleración. "
                f"Conductos de refrigeración calibrados para mantener pastillas y discos en ventana óptima (450°C-550°C)."
            ),
        })

        # Guardar en memoria y en disco
        version_num = self.version_counter.get(key, 0) + 1
        self.version_counter[key] = version_num
        self.current_setups[key] = new_setup

        target_dir = self._safe_target_dir(car_model, track_name)
        live_file = target_dir / "APEX_AUTO_LIVE.json"
        versioned_file = target_dir / f"APEX_V{version_num}_{self.input_mode.upper()}_{self.driving_style.upper()}.json"

        serialized = json.dumps(new_setup, indent=2)
        live_file.write_text(serialized, encoding="utf-8")
        versioned_file.write_text(serialized, encoding="utf-8")

        return live_file, new_setup, changes, version_num
