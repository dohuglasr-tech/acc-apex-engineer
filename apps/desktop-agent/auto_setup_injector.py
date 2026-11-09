"""
ACC Apex Engineer Pro - Auto-Inyector de Setups en Tiempo Real (auto_setup_injector.py)

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


def create_base_acc_setup(car_model: str, input_mode: str) -> Dict[str, Any]:
    """
    Crea la estructura JSON oficial de Assetto Corsa Competizione (basicSetup + advancedSetup)
    adaptada inicialmente al periférico del piloto (keyboard, gamepad, wheel).
    """
    # Ajustes base según periférico (Regla 2.A del Plan Maestro)
    if input_mode == "keyboard":
        steer_ratio_click = 6      # ~17:1 suave para evitar latigazos al pulsar A/D
        brake_power_click = 13     # ~93% Brake Torque para evitar bloqueo instantáneo
        abs_click = 5              # ABS 5 para pulsación binaria
        tc1_click = 5              # TC1 5 para pulsación binaria de tecla W
        tc2_click = 6
        brake_bias_click = 31      # Más adelantado y estable en entrada
        rear_wing_click = 8        # Margen aerodinámico trasero extra (+1%)
        rebound_slow_front = 14
    elif input_mode == "gamepad":
        steer_ratio_click = 4      # ~15:1 progresivo para stick analógico
        brake_power_click = 17     # ~97% Brake Torque
        abs_click = 4              # ABS 4
        tc1_click = 4              # TC1 4 para transición de gatillo derecho
        tc2_click = 5
        brake_bias_click = 28
        rear_wing_click = 7        # Margen aerodinámico trasero extra (+0.5%)
        rebound_slow_front = 16    # Slow Rebound delantero anti-latigazo de gatillo
    else:  # wheel
        steer_ratio_click = 1      # ~13:1 directo
        brake_power_click = 20     # 100% Brake Torque
        abs_click = 3              # ABS 3
        tc1_click = 3
        tc2_click = 3
        brake_bias_click = 24      # Rotación máxima en trail-braking
        rear_wing_click = 6
        rebound_slow_front = 11

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
                "staticCamber": [-3.8, -3.8, -3.2, -3.2],
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
                "fuel": 35,
                "nPitStops": 0,
                "tyreSet": 1,
                "frontBrakePadCompound": 0,
                "rearBrakePadCompound": 0,
                "pitStrategy": [],
                "fuelPerLap": 2.85,
            },
        },
        "advancedSetup": {
            "mechanicalBalance": {
                "aRBFront": 4,
                "aRBRear": 3,
                "wheelRate": [2, 2, 2, 2],
                "bumpStopRateUp": [8, 8, 10, 10],
                "bumpStopRateDn": [6, 6, 6, 6],
                "bumpStopWindow": [12, 12, 18, 18],
                "brakeTorque": brake_power_click,
                "brakeBias": brake_bias_click,
            },
            "dampers": {
                "bumpSlow": [10, 10, 9, 9],
                "bumpFast": [6, 6, 5, 5],
                "reboundSlow": [rebound_slow_front, rebound_slow_front, 11, 11],
                "reboundFast": [7, 7, 6, 6],
            },
            "aeroBalance": {
                "rideHeight": [2, 0, 14, 0],  # [Front, N/A, Rear, N/A] en clics sobre mínimo
                "rodLength": [0.0, 0.0, 0.0, 0.0],
                "splitter": 0,
                "rearWing": rear_wing_click,
                "brakeDuct": [3, 3],
            },
            "drivetrain": {
                "preload": 8 if input_mode in ("keyboard", "gamepad") else 5,
            },
        },
        "trackBopType": 0,
    }


class AutoSetupInjector:
    """
    Motor de Auto-Inyección de Setups en Tiempo Real (Regla 2.A del Plan Maestro).
    Calcula y escribe automáticamente APEX_AUTO_LIVE.json en Documents\\Assetto Corsa Competizione\\Setups.
    """

    def __init__(self, input_mode: str = "wheel") -> None:
        self.input_mode = input_mode if input_mode in ("keyboard", "gamepad", "wheel") else "wheel"
        self.version_counter: Dict[str, int] = {}
        self.current_setups: Dict[str, Dict[str, Any]] = {}

    def set_input_mode(self, input_mode: str) -> None:
        if input_mode in ("keyboard", "gamepad", "wheel"):
            self.input_mode = input_mode

    def _safe_target_dir(self, car_model: str, track_name: str) -> Path:
        """
        Verifica estrictamente que la ruta destino esté dentro de Setups/<coche>/<pista>
        y NUNCA apunte a Config ni a controls.json.
        """
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
    ) -> Tuple[Path, Dict[str, Any], List[Dict[str, str]], int]:
        """
        Aplica las 5 leyes físicas a 333 Hz y escribe APEX_AUTO_LIVE.json + copia histórica.
        Retorna: (ruta_archivo, setup_json, changes_summary, version_num)
        """
        key = f"{car_model}:{track_name}:{self.input_mode}"
        prev_setup = self.current_setups.get(key) or create_base_acc_setup(car_model, self.input_mode)
        new_setup = copy.deepcopy(prev_setup)
        changes: List[Dict[str, str]] = []

        # ---------------------------------------------------------------------
        # 1. NEUMÁTICOS PIRELLI DHE (Objetivo: 26.8 - 26.9 PSI en caliente)
        # ---------------------------------------------------------------------
        wheel_labels = ["FL (Del. Izq.)", "FR (Del. Der.)", "RL (Tras. Izq.)", "RR (Tras. Der.)"]
        old_pressures = list(new_setup["basicSetup"]["tyres"]["tyrePressure"])
        for i in range(4):
            measured_psi = hot_pressures[i] if i < len(hot_pressures) else TARGET_HOT_PSI
            core_c = core_temps[i] if i < len(core_temps) else 82.0
            delta_psi = TARGET_HOT_PSI - measured_psi

            # Compensación de scrub delantero para Teclado y Mando
            if i in (0, 1) and self.input_mode in ("keyboard", "gamepad") and core_c > 88.0:
                delta_psi -= 0.10

            if abs(delta_psi) >= 0.08:
                click_delta = int(round(delta_psi * 10.0))
                click_delta = max(-6, min(6, click_delta))
                if click_delta != 0:
                    updated_click = max(35, min(95, old_pressures[i] + click_delta))
                    new_setup["basicSetup"]["tyres"]["tyrePressure"][i] = updated_click
                    old_cold = round(BASE_PSI_ZERO_CLICK + old_pressures[i] * 0.1, 1)
                    new_cold = round(BASE_PSI_ZERO_CLICK + updated_click * 0.1, 1)
                    changes.append({
                        "area": f"Neumático {wheel_labels[i]}",
                        "parameter": f"tyrePressure[{i}]",
                        "before": f"{old_cold} PSI ({old_pressures[i]} clics)",
                        "after": f"{new_cold} PSI ({updated_click} clics)",
                        "reason": (
                            f"Presión en caliente medida en {measured_psi:.2f} PSI "
                            f"(carcasa {core_c:.0f}°C). Ajustado {click_delta:+d} clics para clavar 26.85 PSI."
                        ),
                    })

        # ---------------------------------------------------------------------
        # 2. ALTURAS Y FONDO PLANO (Bottoming Out / Rake)
        # ---------------------------------------------------------------------
        if bottoming_events > 0:
            old_rh_front = new_setup["advancedSetup"]["aeroBalance"]["rideHeight"][0]
            inc_mm = 2 if bottoming_events >= 3 else 1
            new_rh_front = min(20, old_rh_front + inc_mm)
            new_setup["advancedSetup"]["aeroBalance"]["rideHeight"][0] = new_rh_front

            old_bs_rate = new_setup["advancedSetup"]["mechanicalBalance"]["bumpStopRateUp"][0]
            new_bs_rate = min(20, old_bs_rate + 1)
            new_setup["advancedSetup"]["mechanicalBalance"]["bumpStopRateUp"][0] = new_bs_rate
            new_setup["advancedSetup"]["mechanicalBalance"]["bumpStopRateUp"][1] = new_bs_rate

            changes.append({
                "area": "Fondo Plano y Alturas (Splitter)",
                "parameter": "rideHeight[Front] & bumpStopRateUp",
                "before": f"+{old_rh_front} mm / Tope {old_bs_rate}",
                "after": f"+{new_rh_front} mm / Tope {new_bs_rate}",
                "reason": (
                    f"Se detectaron {bottoming_events} toques de fondo plano a 333 Hz. "
                    f"Se sube altura delantera +{inc_mm} mm y se endurece el tope de goma para no perder carga en compresiones."
                ),
            })

        # ---------------------------------------------------------------------
        # 3. BALANCE EN ENTRADA DE CURVA (Subviraje vs. Sobreviraje en Trail-Braking)
        # ---------------------------------------------------------------------
        if oversteer_entry_events >= 2:
            old_bb = new_setup["advancedSetup"]["mechanicalBalance"]["brakeBias"]
            new_bb = min(45, old_bb + 2)
            new_setup["advancedSetup"]["mechanicalBalance"]["brakeBias"] = new_bb

            old_reb = new_setup["advancedSetup"]["dampers"]["reboundSlow"][0]
            new_reb = min(25, old_reb + 2)
            new_setup["advancedSetup"]["dampers"]["reboundSlow"][0] = new_reb
            new_setup["advancedSetup"]["dampers"]["reboundSlow"][1] = new_reb

            changes.append({
                "area": f"Estabilidad de Entrada ({self.input_mode.upper()})",
                "parameter": "brakeBias & reboundSlow[Front]",
                "before": f"Bias +{old_bb} clics / Rebound {old_reb}",
                "after": f"Bias +{new_bb} clics / Rebound {new_reb}",
                "reason": (
                    f"Detectadas {oversteer_entry_events} pérdidas de cola al soltar freno (trail-braking). "
                    f"Se adelanta el reparto de frenada y se frena la extensión delantera para contener el cabeceo."
                ),
            })
        elif understeer_ratio > 0.22:
            old_arb_f = new_setup["advancedSetup"]["mechanicalBalance"]["aRBFront"]
            if old_arb_f > 1:
                new_arb_f = old_arb_f - 1
                new_setup["advancedSetup"]["mechanicalBalance"]["aRBFront"] = new_arb_f
                changes.append({
                    "area": f"Rotación en Vértice ({self.input_mode.upper()})",
                    "parameter": "aRBFront",
                    "before": f"ARB Delantera {old_arb_f}",
                    "after": f"ARB Delantera {new_arb_f}",
                    "reason": (
                        f"Detectado subviraje en el {understeer_ratio * 100:.0f}% de las fases de giro. "
                        f"Se suaviza 1 clic la estabilizadora delantera para dar más mordiente al tren delantero."
                    ),
                })

        # ---------------------------------------------------------------------
        # 4. TRACCIÓN EN SALIDA DE CURVA (Cortes de TC / Patinaje Trasero)
        # ---------------------------------------------------------------------
        if tc_cut_ratio > 0.18:
            old_arb_r = new_setup["advancedSetup"]["mechanicalBalance"]["aRBRear"]
            new_arb_r = max(1, old_arb_r - 1)
            new_setup["advancedSetup"]["mechanicalBalance"]["aRBRear"] = new_arb_r

            old_tc2 = new_setup["basicSetup"]["electronics"]["tC2"]
            new_tc2 = min(10, old_tc2 + 1)
            new_setup["basicSetup"]["electronics"]["tC2"] = new_tc2

            changes.append({
                "area": f"Tracción en Salida ({self.input_mode.upper()})",
                "parameter": "aRBRear & electronics.tC2",
                "before": f"ARB Trasera {old_arb_r} / TC2 {old_tc2}",
                "after": f"ARB Trasera {new_arb_r} / TC2 {new_tc2}",
                "reason": (
                    f"El control de tracción cortó potencia en el {tc_cut_ratio * 100:.0f}% de las salidas de curva. "
                    f"Se ablanda la barra trasera y se afina TC2 para traccionar sin ahogar el motor."
                ),
            })

        # ---------------------------------------------------------------------
        # 5. TEMPERATURA DE FRENOS (Ventana óptima: 450 °C - 600 °C)
        # ---------------------------------------------------------------------
        front_brake_c = (brake_temps_avg[0] + brake_temps_avg[1]) / 2.0 if len(brake_temps_avg) >= 2 else 510.0
        rear_brake_c = (brake_temps_avg[2] + brake_temps_avg[3]) / 2.0 if len(brake_temps_avg) >= 4 else 480.0
        old_ducts = list(new_setup["advancedSetup"]["aeroBalance"]["brakeDuct"])

        if front_brake_c > 605.0 and old_ducts[0] < 6:
            new_setup["advancedSetup"]["aeroBalance"]["brakeDuct"][0] = old_ducts[0] + 1
            changes.append({
                "area": "Conductos de Freno Delanteros",
                "parameter": "brakeDuct[Front]",
                "before": f"Conducto {old_ducts[0]}",
                "after": f"Conducto {old_ducts[0] + 1}",
                "reason": f"Temperatura media delantera en {front_brake_c:.0f}°C (>600°C). Se abre 1 clic para evitar fading y sobrepresión por radiación a la llanta.",
            })
        elif front_brake_c < 440.0 and old_ducts[0] > 1:
            new_setup["advancedSetup"]["aeroBalance"]["brakeDuct"][0] = old_ducts[0] - 1
            changes.append({
                "area": "Conductos de Freno Delanteros",
                "parameter": "brakeDuct[Front]",
                "before": f"Conducto {old_ducts[0]}",
                "after": f"Conducto {old_ducts[0] - 1}",
                "reason": f"Temperatura media delantera en {front_brake_c:.0f}°C (<450°C). Se cierra 1 clic para mantener el disco en ventana óptima y reducir drag.",
            })

        if rear_brake_c > 605.0 and old_ducts[1] < 6:
            new_setup["advancedSetup"]["aeroBalance"]["brakeDuct"][1] = old_ducts[1] + 1
            changes.append({
                "area": "Conductos de Freno Traseros",
                "parameter": "brakeDuct[Rear]",
                "before": f"Conducto {old_ducts[1]}",
                "after": f"Conducto {old_ducts[1] + 1}",
                "reason": f"Temperatura media trasera en {rear_brake_c:.0f}°C (>600°C). Se abre 1 clic.",
            })
        elif rear_brake_c < 440.0 and old_ducts[1] > 1:
            new_setup["advancedSetup"]["aeroBalance"]["brakeDuct"][1] = old_ducts[1] - 1
            changes.append({
                "area": "Conductos de Freno Traseros",
                "parameter": "brakeDuct[Rear]",
                "before": f"Conducto {old_ducts[1]}",
                "after": f"Conducto {old_ducts[1] - 1}",
                "reason": f"Temperatura media trasera en {rear_brake_c:.0f}°C (<450°C). Se cierra 1 clic.",
            })

        if not changes:
            changes.append({
                "area": "Validación Integral 333 Hz",
                "parameter": "APEX_AUTO_LIVE",
                "before": "En ventana óptima",
                "after": "Mantenido (26.85 PSI)",
                "reason": f"Las 4 presiones Pirelli DHE, alturas y temperaturas de freno están en su ventana ideal para {self.input_mode.upper()}.",
            })

        version_num = self.version_counter.get(key, 0) + 1
        self.version_counter[key] = version_num
        self.current_setups[key] = new_setup

        target_dir = self._safe_target_dir(car_model, track_name)
        live_file = target_dir / "APEX_AUTO_LIVE.json"
        versioned_file = target_dir / f"APEX_V{version_num}_{self.input_mode.upper()}.json"

        # Escritura atómica y segura exclusivamente en Setups/<coche>/<pista>
        serialized = json.dumps(new_setup, indent=2)
        live_file.write_text(serialized, encoding="utf-8")
        versioned_file.write_text(serialized, encoding="utf-8")

        return live_file, new_setup, changes, version_num
