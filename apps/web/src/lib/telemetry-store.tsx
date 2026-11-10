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
  profile: UserProfile | null;
  inputMode: InputMode | null;
  setInputMode: (mode: InputMode, wheelType?: string) => Promise<void>;
  agentConnected: boolean;
  isAccLive: boolean;
  agentHost: string;
  setAgentHost: (host: string) => void;
  liveAlert: string | null;
  frame: TelemetryFrame | null;
  trace: TracePoint[];
  drivingErrors: DrivingErrorItem[];
  setups: UserSetupRecord[];
}

const TelemetryContext = createContext<TelemetryContextValue | null>(null);

export function TelemetryProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [inputMode, setInputModeState] = useState<InputMode | null>(null);
  const [agentConnected, setAgentConnected] = useState(false);
  const [isAccLive, setIsAccLive] = useState(false);
  const [agentHost, setAgentHost] = useState("localhost");
  const [liveAlert, setLiveAlert] = useState<string | null>(null);
  const [frame, setFrame] = useState<TelemetryFrame | null>(null);
  const [trace, setTrace] = useState<TracePoint[]>([]);
  const [drivingErrors, setDrivingErrors] = useState<DrivingErrorItem[]>([]);
  const [setups, setSetups] = useState<UserSetupRecord[]>([]);

  const wsRef = useRef<WebSocket | null>(null);

  // Cargar perfil real de Supabase (sin datos simulados ni pre-guardados)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const hostParam = params.get("agent");
    if (hostParam) {
      setAgentHost(hostParam);
    }

    if (!isSupabaseConfigured()) return;

    const supabase = createClient();
    supabase.auth.getUser().then(async ({ data }) => {
      if (!data?.user) {
        setProfile(null);
        return;
      }

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
            "Driver",
          avatar_url:
            prof.avatar_url || data.user.user_metadata?.avatar_url || null,
          input_mode: (prof.input_mode as InputMode) || null,
          wheel_type: prof.wheel_type || null,
          agent_token: prof.agent_token,
        });
        if (prof.input_mode) {
          setInputModeState(prof.input_mode as InputMode);
        }
      }

      // Consultar únicamente los setups y vueltas reales que el usuario haya registrado en pista
      const { data: dbSetups } = await supabase
        .from("user_setups")
        .select("*")
        .eq("user_id", data.user.id)
        .order("created_at", { ascending: false })
        .limit(20);

      if (dbSetups && dbSetups.length > 0) {
        setSetups(
          dbSetups.map((s) => ({
            id: s.id,
            version_num: s.version_num,
            file_name: s.file_name,
            full_path: `Documents\\Assetto Corsa Competizione\\Setups\\${s.car_model}\\${s.track_name}\\${s.file_name}`,
            car_model: s.car_model,
            track_name: s.track_name,
            input_mode: s.input_mode as InputMode,
            created_at: s.created_at,
            air_temp: s.air_temp || 0,
            road_temp: s.road_temp || 0,
            best_lap_ms: s.best_lap_ms || 0,
            changes_summary: Array.isArray(s.changes_summary)
              ? s.changes_summary
              : [],
            setup_json: s.setup_json || {},
          }))
        );
      }

      const { data: dbLaps } = await supabase
        .from("user_laps")
        .select("*")
        .eq("user_id", data.user.id)
        .order("created_at", { ascending: false })
        .limit(1);

      if (dbLaps && dbLaps.length > 0) {
        const lastLap = dbLaps[0];
        if (Array.isArray(lastLap.telemetry_trace)) {
          setTrace(lastLap.telemetry_trace);
        }
        if (Array.isArray(lastLap.driving_errors)) {
          setDrivingErrors(lastLap.driving_errors);
        }
      }
    });
  }, []);

  // Conexión WebSocket al Agente Local (.exe) — sin simulador de respaldo
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
            if (data.type === "telemetry_standby" || !data.is_live_acc) {
              setIsAccLive(false);
              setFrame(null);
              setLiveAlert(null);
              return;
            }

            if (data.type === "telemetry_frame" && data.sample && data.sample.is_live_acc) {
              setIsAccLive(true);
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
                  if (prev.some((s) => s.version_num === incoming.version_num))
                    return prev;
                  return [incoming, ...prev];
                });
              }
            }
          } catch {
            // Ignorar tramas corruptas
          }
        };

        ws.onclose = () => {
          if (!isUnmounted) {
            setAgentConnected(false);
            setIsAccLive(false);
            setFrame(null);
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

  const setInputMode = useCallback(
    async (mode: InputMode, wheelType?: string) => {
      setInputModeState(mode);
      setProfile((prev) =>
        prev
          ? {
              ...prev,
              input_mode: mode,
              wheel_type: wheelType ?? prev.wheel_type,
            }
          : prev
      );

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ action: "set_input_mode", input_mode: mode })
        );
      }

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
    },
    []
  );

  return (
    <TelemetryContext.Provider
      value={{
        profile,
        inputMode,
        setInputMode,
        agentConnected,
        isAccLive,
        agentHost,
        setAgentHost,
        liveAlert,
        frame,
        trace,
        drivingErrors,
        setups,
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
