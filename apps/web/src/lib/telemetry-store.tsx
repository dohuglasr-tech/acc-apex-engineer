"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  useCallback,
} from "react";
import { createClient, isSupabaseConfigured } from "./supabase/client";

export type InputMode = "keyboard" | "gamepad" | "wheel";

export interface TelemetryFrame {
  is_live_acc: boolean;
  packet_id: number;
  car_model: string;
  track_name: string;
  driver_name: string;
  completed_laps: number;
  current_lap_ms: number;
  last_lap_ms: number;
  best_lap_ms: number;
  sector_index: number;
  last_sector_ms: number;
  normalized_pos: number;
  speed_kmh: number;
  rpms: number;
  max_rpm: number;
  gear: number;
  gas: number;
  brake: number;
  steer_angle: number;
  fuel: number;
  tyre_pressures: [number, number, number, number];
  tyre_temps_core: [number, number, number, number];
  brake_temps: [number, number, number, number];
  wheel_slip: [number, number, number, number];
  ride_height: [number, number];
  tc_in_action: boolean;
  abs_in_action: boolean;
  air_temp: number;
  road_temp: number;
  brake_bias: number;
}

export interface DrivingErrorItem {
  corner: string;
  type: string;
  severity: "Alta" | "Media" | "Baja" | "Óptima";
  time_lost_ms: number;
  metric: string;
  solution: string;
}

export interface SetupChangeItem {
  area: string;
  parameter: string;
  before: string;
  after: string;
  reason: string;
}

export interface UserSetupRecord {
  id: string;
  version_num: number;
  file_name: string;
  full_path: string;
  car_model: string;
  track_name: string;
  input_mode: InputMode;
  created_at: string;
  air_temp: number;
  road_temp: number;
  best_lap_ms: number;
  changes_summary: SetupChangeItem[];
  setup_json: Record<string, unknown>;
}

export interface TracePoint {
  pct: number;
  speed: number;
  best_speed: number;
  gas: number;
  brake: number;
  steer: number;
  gear: number;
  slip_f: number;
  slip_r: number;
}

export interface UserProfile {
  id: string;
  discord_username: string;
  avatar_url: string | null;
  input_mode: InputMode | null;
  wheel_type: string | null;
  agent_token: string;
}

interface TelemetryContextValue {
  profile: UserProfile;
  inputMode: InputMode | null;
  setInputMode: (mode: InputMode, wheelType?: string) => Promise<void>;
  agentConnected: boolean;
  agentHost: string;
  setAgentHost: (host: string) => void;
  liveAlert: string | null;
  frame: TelemetryFrame;
  trace: TracePoint[];
  drivingErrors: DrivingErrorItem[];
  setups: UserSetupRecord[];
  triggerForceInject: () => void;
}

const DEFAULT_PROFILE: UserProfile = {
  id: "local-pilot-session",
  discord_username: "Piloto Discord (Cuenta Aislada RLS)",
  avatar_url: null,
  input_mode: null,
  wheel_type: "Logitech G29 / Fanatec CSL DD",
  agent_token: "a8f9d31b-7c4e-4b2a-9f10-333000acc992",
};

function buildInitialTrace(): TracePoint[] {
  const pts: TracePoint[] = [];
  const corners = [10, 20, 36, 56, 73, 90];
  for (let pct = 0; pct < 100; pct++) {
    let cornerFactor = 0;
    let sign = 1;
    corners.forEach((c, idx) => {
      const dist = Math.abs(pct - c);
      if (dist < 6) {
        const f = 1 - dist / 6;
        if (f > cornerFactor) {
          cornerFactor = f;
          sign = idx % 2 === 0 ? 1 : -1;
        }
      }
    });
    const bestSpeed = Math.round(274 - cornerFactor * 162);
    const speed = Math.round(bestSpeed - (cornerFactor > 0.5 ? 6 : 1));
    const brake = cornerFactor > 0.3 ? Math.round(Math.min(100, cornerFactor * 115)) : 0;
    const gas = Math.round(Math.max(0, 100 - cornerFactor * 125));
    pts.push({
      pct,
      speed,
      best_speed: bestSpeed,
      gas,
      brake,
      steer: Math.round(sign * cornerFactor * 68),
      gear: Math.max(1, Math.min(6, Math.floor(speed / 44) + 1)),
      slip_f: Number((0.3 + cornerFactor * 1.1).toFixed(2)),
      slip_r: Number((0.28 + cornerFactor * 0.95).toFixed(2)),
    });
  }
  return pts;
}

export function buildErrorsForMode(mode: InputMode): DrivingErrorItem[] {
  const trailBrakingSol =
    mode === "keyboard"
      ? "En T1 · La Source, pasaste de 100% a 0% de tecla de freno en 45 ms. Da 2 micro-pulsos rápidos (cadencia de descarga) al iniciar el giro con A/D; el Auto-Inyector ya subió +2 clics el Rebound Slow delantero y bajó el Brake Torque al 93%."
      : mode === "gamepad"
      ? "En T1 · La Source, soltaste el gatillo izquierdo (LT/L2) de golpe en 52 ms levantando el splitter. Desliza la yema del índice suavemente del 100% al 15% hacia el vértice; el Auto-Inyector endureció el Slow Rebound delantero anti-latigazo."
      : "En T1 · La Source, descargaste la célula de carga del 100% al 0% en 58 ms antes del vértice. Mantén un 18% de freno residual hasta mirar al interior; el Auto-Inyector adelantó +0.4% el Brake Bias.";

  const scrubbingSol =
    mode === "keyboard"
      ? "En T12 · Pouhon, mantuviste pulsada la tecla de giro saturando el neumático delantero izquierdo (27.4 PSI / 89°C). Usa toques modulados en mitad de curva; el Auto-Inyector suavizó el Steer Ratio a 17:1 y bajó 1 clic la ARB delantera."
      : mode === "gamepad"
      ? "En T12 · Pouhon, empujaste el stick analógico al tope lateral provocando scrubbing delantero (Slip 1.42). Apoya el stick hacia adelante a 45° y rótalo por el borde superior del anillo."
      : "En T12 · Pouhon, superaste en 11° el ángulo óptimo de deriva del Pirelli DHE delantero. Abre ligeramente la dirección en el centro de curva y usa el acelerador para mantener la rotación.";

  const tcCutSol =
    mode === "keyboard"
      ? "En T18-T19 · Bus Stop, pulsaste la tecla W al 100% con el coche aún girado, activando el corte de TC y perdiendo 0.16s en la salida. El Auto-Inyector subió TC2 +1 clic y ablandó la barra trasera."
      : mode === "gamepad"
      ? "En T18-T19 · Bus Stop, apretaste el gatillo derecho (RT/R2) a fondo antes de abrir el stick. Aplica 50% de gatillo en el vértice y llega al 100% al enderezar."
      : "En T18-T19 · Bus Stop, aplicaste 85% de acelerador con 42° de volante, haciendo saltar el TC1. Sincroniza la apertura de manos con la bajada del pedal derecho.";

  return [
    {
      corner: "T1 · La Source (Horquilla)",
      type: "Error de Trail-Braking (Soltado Brusco de Freno)",
      severity: "Alta",
      time_lost_ms: 235,
      metric: "Freno de 100% a 0% en 52 ms → Cabeceo delantero +14 mm",
      solution: trailBrakingSol,
    },
    {
      corner: "T12 · Pouhon (Doble Izquierda)",
      type: "Error de Scrubbing (Exceso de Dirección)",
      severity: "Media",
      time_lost_ms: 150,
      metric: "WheelSlip FL 1.42 sin ganancia de Yaw Rate · Temp 89°C",
      solution: scrubbingSol,
    },
    {
      corner: "T18-T19 · Chicana Bus Stop",
      type: "Aceleración Prematura (Corte de TC en Salida)",
      severity: "Media",
      time_lost_ms: 165,
      metric: "TC activo durante 310 ms al salir del segundo piano",
      solution: tcCutSol,
    },
    {
      corner: "T3-T4 · Eau Rouge / Raidillon",
      type: "Toque de Fondo Plano (Bottoming Out en Compresión)",
      severity: "Baja",
      time_lost_ms: 90,
      metric: "Altura delantera mínima 39.5 mm a 242 km/h",
      solution:
        "El splitter rozó el asfalto en la compresión de Eau Rouge. El Auto-Inyector ya subió +1 mm la altura delantera y endureció +1 clic el Bumpstop Rate en APEX_AUTO_LIVE.json.",
    },
  ];
}

export function buildSetupForMode(mode: InputMode, versionNum = 1): UserSetupRecord {
  const steerRatio = mode === "keyboard" ? "17:1 (Clic 6)" : mode === "gamepad" ? "15:1 (Clic 4)" : "13:1 (Clic 1)";
  const brakeTorque = mode === "keyboard" ? "93% (Clic 13)" : mode === "gamepad" ? "97% (Clic 17)" : "100% (Clic 20)";
  const absLevel = mode === "keyboard" ? "ABS 5" : mode === "gamepad" ? "ABS 4" : "ABS 3";

  return {
    id: `setup-v${versionNum}-${mode}`,
    version_num: versionNum,
    file_name: "APEX_AUTO_LIVE.json",
    full_path:
      "Documents\\Assetto Corsa Competizione\\Setups\\mclaren_720s_gt3_evo\\spa\\APEX_AUTO_LIVE.json",
    car_model: "mclaren_720s_gt3_evo",
    track_name: "spa",
    input_mode: mode,
    created_at: new Date().toISOString(),
    air_temp: 23.0,
    road_temp: 31.0,
    best_lap_ms: 137650,
    changes_summary: [
      {
        area: "Neumáticos Pirelli DHE (4 Ruedas)",
        parameter: "basicSetup.tyres.tyrePressure[0..3]",
        before: "FL 26.2 / FR 26.3 / RL 26.4 / RR 26.4 PSI",
        after: "Clavado en 26.85 PSI en caliente (Clics [57, 60, 66, 65])",
        reason: `Ajustado clic a clic tras medir 27.35 PSI en FL por mayor scrub en modo ${mode.toUpperCase()} y 26.45 PSI en el eje trasero.`,
      },
      {
        area: `Cinemática de Dirección y Freno (${mode.toUpperCase()})`,
        parameter: "steerRatio / brakeTorque / abs",
        before: "Base Estándar (14:1 / 100% / ABS 3)",
        after: `${steerRatio} · Torque ${brakeTorque} · ${absLevel}`,
        reason:
          mode === "keyboard"
            ? "Suaviza la respuesta ante pulsaciones binarias de teclado para no saturar el neumático delantero ni bloquear frenos."
            : mode === "gamepad"
            ? "Filtra el recorrido corto del stick analógico y protege contra bloqueos al apretar el gatillo LT/L2."
            : "Configuración directa para volante FFB con célula de carga al 100% de par de frenado.",
      },
      {
        area: "Alturas y Fondo Plano (Eau Rouge)",
        parameter: "aeroBalance.rideHeight[Front] & bumpStopRateUp",
        before: "52 mm (+2 clics) / Bumpstop 7",
        after: "53 mm (+3 clics) / Bumpstop 8",
        reason:
          "Se detectaron 2 toques de splitter (39.5 mm) en la compresión de Raidillon a 333 Hz. Se sube +1 mm para evitar pérdida súbita de carga.",
      },
      {
        area: "Balance en Entrada (Trail-Braking)",
        parameter: "dampers.reboundSlow[Front] & mechanicalBalance.aRBFront",
        before: "Rebound Slow 11 / ARB Front 5",
        after: `Rebound Slow ${mode === "wheel" ? 13 : 16} / ARB Front 4`,
        reason:
          "Contiene la subida brusca del morro al soltar el freno y mejora la rotación en el vértice de Les Combes y Pouhon.",
      },
      {
        area: "Conductos de Freno (Ventana 450°C–600°C)",
        parameter: "aeroBalance.brakeDuct[0..1]",
        before: "Delantero 3 / Trasero 3",
        after: "Delantero 4 / Trasero 3",
        reason:
          "Los discos delanteros alcanzaron picos de 625°C en La Source y Bus Stop; se abre 1 clic para estabilizar la presión de la llanta.",
      },
    ],
    setup_json: {
      carName: "mclaren_720s_gt3_evo",
      basicSetup: {
        tyres: { tyreCompound: 0, tyrePressure: [57, 60, 66, 65] },
        alignment: {
          camber: [4, 4, 6, 6],
          toe: [14, 14, 22, 22],
          casterLF: 34,
          casterRF: 34,
          steerRatio: mode === "keyboard" ? 6 : mode === "gamepad" ? 4 : 1,
        },
        electronics: {
          tC1: mode === "keyboard" ? 5 : mode === "gamepad" ? 4 : 3,
          tC2: mode === "keyboard" ? 6 : mode === "gamepad" ? 5 : 3,
          abs: mode === "keyboard" ? 5 : mode === "gamepad" ? 4 : 3,
          eCUMap: 0,
        },
      },
      advancedSetup: {
        mechanicalBalance: {
          aRBFront: 4,
          aRBRear: 2,
          wheelRate: [2, 2, 2, 2],
          bumpStopRateUp: [8, 8, 10, 10],
          bumpStopWindow: [12, 12, 18, 18],
          brakeTorque: mode === "keyboard" ? 13 : mode === "gamepad" ? 17 : 20,
          brakeBias: mode === "keyboard" ? 31 : mode === "gamepad" ? 28 : 24,
        },
        dampers: {
          bumpSlow: [10, 10, 9, 9],
          reboundSlow: [
            mode === "wheel" ? 13 : 16,
            mode === "wheel" ? 13 : 16,
            11,
            11,
          ],
        },
        aeroBalance: {
          rideHeight: [3, 0, 15, 0],
          splitter: 0,
          rearWing: mode === "keyboard" ? 8 : mode === "gamepad" ? 7 : 6,
          brakeDuct: [4, 3],
        },
        drivetrain: {
          preload: mode === "wheel" ? 5 : 8,
        },
      },
      trackBopType: 0,
    },
  };
}

const TelemetryContext = createContext<TelemetryContextValue | null>(null);

export function TelemetryProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [inputMode, setInputModeState] = useState<InputMode | null>(null);
  const [agentConnected, setAgentConnected] = useState(false);
  const [agentHost, setAgentHost] = useState("localhost");
  const [liveAlert, setLiveAlert] = useState<string | null>(null);
  const [trace, setTrace] = useState<TracePoint[]>(() => buildInitialTrace());
  const [drivingErrors, setDrivingErrors] = useState<DrivingErrorItem[]>(() =>
    buildErrorsForMode("wheel")
  );
  const [setups, setSetups] = useState<UserSetupRecord[]>(() => [
    buildSetupForMode("wheel", 1),
  ]);

  const [frame, setFrame] = useState<TelemetryFrame>({
    is_live_acc: false,
    packet_id: 1,
    car_model: "mclaren_720s_gt3_evo",
    track_name: "spa",
    driver_name: "Piloto ACC",
    completed_laps: 3,
    current_lap_ms: 48210,
    last_lap_ms: 137650,
    best_lap_ms: 137420,
    sector_index: 1,
    last_sector_ms: 44610,
    normalized_pos: 0.34,
    speed_kmh: 214.5,
    rpms: 7120,
    max_rpm: 8000,
    gear: 5,
    gas: 0.92,
    brake: 0.0,
    steer_angle: -0.14,
    fuel: 31.4,
    tyre_pressures: [26.85, 26.82, 26.88, 26.84],
    tyre_temps_core: [84.2, 83.5, 81.0, 81.4],
    brake_temps: [515, 510, 465, 460],
    wheel_slip: [0.32, 0.3, 0.29, 0.28],
    ride_height: [53.0, 68.0],
    tc_in_action: false,
    abs_in_action: false,
    air_temp: 23.0,
    road_temp: 31.0,
    brake_bias: 56.2,
  });

  const wsRef = useRef<WebSocket | null>(null);

  // Cargar modo guardado o perfil de Supabase
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const hostParam = params.get("agent");
    if (hostParam) {
      setAgentHost(hostParam);
    }

    const savedMode = window.localStorage.getItem("acc_apex_input_mode") as InputMode | null;
    const savedToken = window.localStorage.getItem("acc_apex_agent_token");
    if (savedToken) {
      setProfile((prev) => ({ ...prev, agent_token: savedToken }));
    } else {
      const generated =
        typeof crypto !== "undefined" && "randomUUID" in crypto
          ? crypto.randomUUID()
          : DEFAULT_PROFILE.agent_token;
      window.localStorage.setItem("acc_apex_agent_token", generated);
      setProfile((prev) => ({ ...prev, agent_token: generated }));
    }

    if (savedMode && ["keyboard", "gamepad", "wheel"].includes(savedMode)) {
      setInputModeState(savedMode);
      setProfile((prev) => ({ ...prev, input_mode: savedMode }));
      setDrivingErrors(buildErrorsForMode(savedMode));
      setSetups([buildSetupForMode(savedMode, 1)]);
    }

    if (isSupabaseConfigured()) {
      const supabase = createClient();
      supabase.auth.getUser().then(async ({ data }) => {
        if (data?.user) {
          const { data: prof } = await supabase
            .from("profiles")
            .select("*")
            .eq("id", data.user.id)
            .single();
          if (prof) {
            setProfile({
              id: prof.id,
              discord_username:
                prof.discord_username ||
                data.user.user_metadata?.full_name ||
                data.user.email ||
                "Piloto Discord",
              avatar_url: prof.avatar_url || data.user.user_metadata?.avatar_url || null,
              input_mode: prof.input_mode as InputMode | null,
              wheel_type: prof.wheel_type,
              agent_token: prof.agent_token,
            });
            if (prof.input_mode) {
              setInputModeState(prof.input_mode as InputMode);
              window.localStorage.setItem("acc_apex_input_mode", prof.input_mode);
              setDrivingErrors(buildErrorsForMode(prof.input_mode as InputMode));
              setSetups([buildSetupForMode(prof.input_mode as InputMode, 1)]);
            }
          }
        }
      });
    }
  }, []);

  // Conexión WebSocket a 60 FPS con el Agente Ejecutable Local (.exe)
  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let isUnmounted = false;

    function connectWs() {
      if (isUnmounted) return;
      try {
        const ws = new WebSocket(`ws://${agentHost}:8765`);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isUnmounted) setAgentConnected(true);
        };

        ws.onmessage = (evt) => {
          try {
            const data = JSON.parse(evt.data);
            if (data.type === "telemetry_frame" && data.sample) {
              setFrame(data.sample);
              setLiveAlert(data.live_alert || null);
              if (data.latest_lap?.driving_errors) {
                setDrivingErrors(data.latest_lap.driving_errors);
              }
              if (data.latest_lap?.telemetry_trace) {
                setTrace(data.latest_lap.telemetry_trace);
              }
              if (data.latest_setup) {
                const incoming: UserSetupRecord = {
                  id: `live-v${data.latest_setup.version_num}`,
                  version_num: data.latest_setup.version_num,
                  file_name: data.latest_setup.file_name,
                  full_path: data.latest_setup.full_path,
                  car_model: data.latest_setup.car_model,
                  track_name: data.latest_setup.track_name,
                  input_mode: data.latest_setup.input_mode,
                  created_at: new Date().toISOString(),
                  air_temp: data.sample.air_temp,
                  road_temp: data.sample.road_temp,
                  best_lap_ms: data.sample.best_lap_ms,
                  changes_summary: data.latest_setup.changes_summary,
                  setup_json: data.latest_setup.setup_json,
                };
                setSetups((prev) => {
                  if (prev.some((s) => s.version_num === incoming.version_num)) return prev;
                  return [incoming, ...prev];
                });
              }
            }
          } catch {
            // Ignore malformed frame
          }
        };

        ws.onclose = () => {
          if (!isUnmounted) {
            setAgentConnected(false);
            reconnectTimer = setTimeout(connectWs, 3000);
          }
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch {
        reconnectTimer = setTimeout(connectWs, 3000);
      }
    }

    connectWs();
    return () => {
      isUnmounted = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, [agentHost]);

  // Simulador fluido de respaldo a 30 FPS cuando el Agente .exe no está conectado aún
  useEffect(() => {
    if (agentConnected) return;
    let tick = 0;
    const interval = setInterval(() => {
      tick += 1;
      const norm = (tick % 900) / 900;
      const corners = [0.08, 0.18, 0.34, 0.56, 0.72, 0.91];
      let cIntensity = 0;
      let cSign = 1;
      corners.forEach((cz, idx) => {
        const d = Math.abs(norm - cz);
        if (d < 0.045) {
          const f = 1 - d / 0.045;
          if (f > cIntensity) {
            cIntensity = f;
            cSign = idx % 2 === 0 ? 1 : -1;
          }
        }
      });

      const brake = cIntensity > 0.26 ? Math.min(1, (cIntensity - 0.15) * 1.4) : 0;
      const gas = Math.max(0, 1 - cIntensity * 1.18);
      const speed = 276 - cIntensity * 165 + Math.sin(tick * 0.08) * 3;
      const gear = Math.max(1, Math.min(6, Math.floor(speed / 43) + 1));
      const rpms = Math.floor(4950 + ((speed % 43) / 43) * 2950);
      const eauRouge = Math.abs(norm - 0.18) < 0.016;

      if (eauRouge) {
        setLiveAlert("¡COMPRESIÓN EAU ROUGE (40.5mm)! Auto-Setup ajustó +1mm splitter");
      } else if (cIntensity > 0.82) {
        setLiveAlert("COACH EN VIVO: Modula liberación de freno hacia el vértice");
      } else {
        setLiveAlert(null);
      }

      setFrame((prev) => ({
        ...prev,
        packet_id: prev.packet_id + 1,
        current_lap_ms: Math.floor(norm * 137650),
        normalized_pos: Number(norm.toFixed(4)),
        sector_index: norm < 0.33 ? 0 : norm < 0.66 ? 1 : 2,
        speed_kmh: Number(speed.toFixed(1)),
        rpms,
        gear,
        gas: Number(gas.toFixed(3)),
        brake: Number(brake.toFixed(3)),
        steer_angle: Number((cSign * Math.pow(cIntensity, 1.15) * 0.65).toFixed(3)),
        tyre_pressures: [
          Number((26.86 + Math.sin(tick * 0.03) * 0.06).toFixed(2)),
          Number((26.83 + Math.cos(tick * 0.03) * 0.05).toFixed(2)),
          Number((26.85 + Math.sin(tick * 0.02) * 0.05).toFixed(2)),
          Number((26.84 + Math.cos(tick * 0.02) * 0.05).toFixed(2)),
        ],
        brake_temps: [
          Math.round(505 + brake * 115),
          Math.round(500 + brake * 110),
          Math.round(455 + brake * 80),
          Math.round(450 + brake * 80),
        ],
        ride_height: [
          Number((eauRouge ? 40.5 : 53 - brake * 8.5).toFixed(1)),
          Number((eauRouge ? 57.0 : 68 + brake * 4.5).toFixed(1)),
        ],
        tc_in_action: cIntensity > 0.55 && gas > 0.65,
        abs_in_action: brake > 0.88,
      }));
    }, 33);

    return () => clearInterval(interval);
  }, [agentConnected]);

  const setInputMode = useCallback(async (mode: InputMode, wheelType?: string) => {
    setInputModeState(mode);
    window.localStorage.setItem("acc_apex_input_mode", mode);
    setProfile((prev) => ({
      ...prev,
      input_mode: mode,
      wheel_type: wheelType ?? prev.wheel_type,
    }));
    setDrivingErrors(buildErrorsForMode(mode));
    setSetups((prev) => [buildSetupForMode(mode, prev.length + 1), ...prev]);

    // Notificar al Agente Local (.exe) si está conectado por WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "set_input_mode", input_mode: mode }));
    }

    // Persistir en Supabase (con aislamiento RLS auth.uid() = id)
    if (isSupabaseConfigured()) {
      const supabase = createClient();
      const { data } = await supabase.auth.getUser();
      if (data?.user) {
        await supabase
          .from("profiles")
          .update({
            input_mode: mode,
            wheel_type: wheelType || null,
            updated_at: new Date().toISOString(),
          })
          .eq("id", data.user.id);
      }
    }
  }, []);

  const triggerForceInject = useCallback(() => {
    const activeMode = inputMode || "wheel";
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "force_inject" }));
    }
    setSetups((prev) => [buildSetupForMode(activeMode, prev.length + 1), ...prev]);
  }, [inputMode]);

  return (
    <TelemetryContext.Provider
      value={{
        profile,
        inputMode,
        setInputMode,
        agentConnected,
        agentHost,
        setAgentHost,
        liveAlert,
        frame,
        trace,
        drivingErrors,
        setups,
        triggerForceInject,
      }}
    >
      {children}
    </TelemetryContext.Provider>
  );
}

export function useTelemetry() {
  const ctx = useContext(TelemetryContext);
  if (!ctx) {
    throw new Error("useTelemetry debe usarse dentro de TelemetryProvider");
  }
  return ctx;
}
