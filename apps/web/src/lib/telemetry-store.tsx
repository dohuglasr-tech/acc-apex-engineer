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
export type VoiceMode = "companion" | "car_state" | "telemetry";
export type DrivingStyle = "aggressive" | "safe" | "beginner";

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
  is_in_pit?: boolean;
  is_in_pit_lane?: boolean;
  speed_kmh: number;
  rpms: number;
  max_rpm: number;
  gear: number;
  gas: number;
  brake: number;
  steer_angle: number;
  fuel: number;
  fuel_per_lap?: number;
  tyre_pressures: [number, number, number, number];
  tyre_temps_core: [number, number, number, number];
  tyre_temps_imo?: [
    [number, number, number],
    [number, number, number],
    [number, number, number],
    [number, number, number]
  ];
  tyre_wear?: [number, number, number, number];
  pad_life?: [number, number, number, number];
  disc_life?: [number, number, number, number];
  camber_deg?: [number, number, number, number];
  brake_temps: [number, number, number, number];
  wheel_slip: [number, number, number, number];
  suspension_travel: [number, number, number, number];
  ride_height: [number, number];
  tc_level?: number;
  abs_level?: number;
  front_brake_compound?: number;
  rear_brake_compound?: number;
  tyre_compound?: string;
  water_temp?: number;
  tc_in_action: boolean;
  abs_in_action: boolean;
  air_temp: number;
  road_temp: number;
  brake_bias: number;
  session_type?: number;
  session_time_left?: number;
  session_laps?: number;
  tyres_out?: number;
  is_off_track?: boolean;
  tyre_dirty_level?: [number, number, number, number];
  is_in_dirt?: boolean;
  // Realismo de simulación ACC
  realism_fuel_on?: boolean;
  realism_tire_on?: boolean;
  realism_damage_pct?: number;
  realism_penalties_on?: boolean;
  realism_summary?: string;
  aid_fuel_rate?: number;
  aid_tire_rate?: number;
  aid_mechanical_damage?: number;
  penalties_enabled?: boolean;
  // Ayudas de conducción ACC
  has_driving_assists?: boolean;
  driving_assists_list?: string[];
  driving_assists_summary?: string;
  assist_auto_gearbox?: boolean;
  assist_auto_clutch?: boolean;
  assist_ideal_line?: boolean;
  assist_stability_pct?: number;
  assist_auto_blip?: boolean;
  auto_shifter_on?: boolean;
  aid_auto_clutch?: boolean;
  aid_auto_blip?: boolean;
  ideal_line_on?: boolean;
  aid_stability?: number;
  has_assists_active?: boolean;
  active_assists_list?: string[];
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
  voice_mode?: VoiceMode | null;
}

export interface ActiveAccSetup {
  basicSetup?: {
    tyres?: {
      tyreCompound?: number;
      tyrePressure?: [number, number, number, number];
    };
    alignment?: {
      camber?: [number, number, number, number];
      toe?: [number, number, number, number];
      staticCamber?: [number, number, number, number];
      toeOutLinear?: [number, number, number, number];
      casterLF?: number;
      casterRF?: number;
      steerRatio?: number;
    };
    electronics?: {
      tC1?: number;
      tC2?: number;
      abs?: number;
      eCUMap?: number;
      fuelMix?: number;
      telemetryLaps?: number;
    };
    strategy?: {
      fuel?: number;
      nPitStops?: number;
      tyreSet?: number;
      frontBrakePadCompound?: number;
      rearBrakePadCompound?: number;
      fuelPerLap?: number;
    };
  };
  advancedSetup?: {
    mechanicalBalance?: {
      aRBFront?: number;
      aRBRear?: number;
      wheelRate?: [number, number, number, number];
      bumpStopRateUp?: [number, number, number, number];
      bumpStopRateDn?: [number, number, number, number];
      bumpStopWindow?: [number, number, number, number];
      brakeTorque?: number;
      brakeBias?: number;
    };
    dampers?: {
      bumpSlow?: [number, number, number, number];
      bumpFast?: [number, number, number, number];
      reboundSlow?: [number, number, number, number];
      reboundFast?: [number, number, number, number];
    };
    aeroBalance?: {
      rideHeight?: [number, number, number, number];
      splitter?: number;
      rearWing?: number;
      brakeDuct?: [number, number];
    };
    drivetrain?: {
      preload?: number;
    };
  };
}

export interface UpcomingCornerInfo {
  id: string;
  name: string;
  distance_m: number;
  seconds_away: number;
  gear: number;
  target_speed_kmh: number;
  braking_marker: string;
  braking_type: string;
  anticipation_msg: string;
  racing_line_notes: string;
  exit_technique: string;
}

export interface LastCornerAnalysis {
  corner_id: string;
  corner_name: string;
  score: number;
  verdict: string;
  apex_speed_kmh: number;
  target_speed_kmh: number;
  speed_delta_kmh: number;
  trail_braking: string;
}

export interface RadioTransmission {
  text: string;
  category: string;
  timestamp: number;
  time_str: string;
  is_active: boolean;
}

export interface RecentRadioCall {
  text: string;
  category: string;
  timestamp: number;
  time_str: string;
}

export interface TrackInfo {
  track_id: string;
  display_name: string;
  country: string;
  length_m: number;
  total_corners: number;
}

export interface EngineerState {
  engineer_name: string;
  voice_mode?: VoiceMode;
  status: "transmitting" | "monitoring" | "standby";
  upcoming_corner: UpcomingCornerInfo | null;
  current_corner: {
    id: string | null;
    name: string;
    is_inside: boolean;
  };
  last_corner_analysis: LastCornerAnalysis | null;
  radio_transmission: RadioTransmission;
  recent_radio_calls: RecentRadioCall[];
  track_info: TrackInfo | null;
}

interface TelemetryContextValue {
  isAuthenticated: boolean;
  profile: UserProfile | null;
  inputMode: InputMode | null;
  setInputMode: (mode: InputMode, wheelType?: string) => Promise<void>;
  voiceMode: VoiceMode;
  setVoiceMode: (mode: VoiceMode) => Promise<void>;
  voiceVolume: number;
  setVoiceVolume: (volume: number) => Promise<void>;
  drivingStyle: DrivingStyle;
  setDrivingStyle: (style: DrivingStyle) => Promise<void>;
  agentConnected: boolean;
  isAccLive: boolean;
  agentHost: string;
  setAgentHost: (host: string) => void;
  liveAlert: string | null;
  frame: TelemetryFrame | null;
  activeSetup: ActiveAccSetup | null;
  engineerState: EngineerState | null;
  trace: TracePoint[];
  drivingErrors: DrivingErrorItem[];
  setups: UserSetupRecord[];
  trackRecords: Record<string, number>;
}

const TelemetryContext = createContext<TelemetryContextValue | null>(null);

export function TelemetryProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [inputMode, setInputModeState] = useState<InputMode | null>("gamepad");
  const [voiceMode, setVoiceModeState] = useState<VoiceMode>("companion");
  const [voiceVolume, setVoiceVolumeState] = useState<number>(65);
  const [drivingStyle, setDrivingStyleState] = useState<DrivingStyle>("safe");
  const [wsConnected, setWsConnected] = useState(false);
  const [cloudHeartbeatActive, setCloudHeartbeatActive] = useState(false);
  const [isAccLive, setIsAccLive] = useState(false);
  const [agentHost, setAgentHost] = useState("localhost");
  const [liveAlert, setLiveAlert] = useState<string | null>(null);
  const [frame, setFrame] = useState<TelemetryFrame | null>(null);
  const [activeSetup, setActiveSetup] = useState<ActiveAccSetup | null>(null);
  const [trackRecords, setTrackRecords] = useState<Record<string, number>>({});
  const [engineerState, setEngineerState] = useState<EngineerState | null>(null);
  const [trace, setTrace] = useState<TracePoint[]>([]);
  const [drivingErrors, setDrivingErrors] = useState<DrivingErrorItem[]>([]);
  const [setups, setSetups] = useState<UserSetupRecord[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const wsActiveRef = useRef(false);

  useEffect(() => {
    if (!isSupabaseConfigured()) return;
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      setIsAuthenticated(Boolean(data?.user));
    });
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setIsAuthenticated(Boolean(session?.user));
    });
    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const fetchCloudState = useCallback(async () => {
    if (!isSupabaseConfigured()) return;
    try {
      const supabase = createClient();
      const { data: authData } = await supabase.auth.getUser();
      const userId = authData?.user?.id || null;
      setIsAuthenticated(Boolean(userId));

      if (!userId) {
        // Aislamiento total: Si no hay sesión autenticada en el navegador,
        // jamás consultar datos de otros pilotos ni mezclar telemetría.
        setProfile(null);
        setCloudHeartbeatActive(false);
        if (!wsActiveRef.current) {
          setIsAccLive(false);
          setFrame(null);
          setActiveSetup(null);
          setEngineerState(null);
          setLiveAlert(null);
          setTrace([]);
          setDrivingErrors([]);
          setSetups([]);
        }
        return;
      }

      const { data: state } = await supabase.rpc("get_active_telemetry_state", {
        p_user_id: userId,
      });

      if (!state || !state.found || !state.profile) {
        if (!wsActiveRef.current) {
          setIsAccLive(false);
          setCloudHeartbeatActive(false);
        }
        return;
      }

      const prof = state.profile;
      const remoteVoiceMode = (prof.voice_mode as VoiceMode) || "companion";
      setProfile({
        id: prof.id,
        discord_username: prof.discord_username || "Piloto",
        avatar_url: prof.avatar_url || null,
        input_mode: (prof.input_mode as InputMode) || "gamepad",
        wheel_type: prof.wheel_type || null,
        agent_token: prof.agent_token,
        voice_mode: remoteVoiceMode,
      });

      if (prof.input_mode) {
        setInputModeState(prof.input_mode as InputMode);
      }
      if (
        prof.voice_mode &&
        ["companion", "car_state", "telemetry"].includes(prof.voice_mode)
      ) {
        setVoiceModeState(prof.voice_mode as VoiceMode);
      }

      const secSinceSeen = Number(prof.seconds_since_seen ?? 999);
      const isAgentRecentlySeen = secSinceSeen < 25;
      setCloudHeartbeatActive(isAgentRecentlySeen);

      if (!wsActiveRef.current) {
        if (
          isAgentRecentlySeen &&
          prof.is_live_acc &&
          prof.live_telemetry?.sample
        ) {
          setIsAccLive(true);
          setFrame(prof.live_telemetry.sample as TelemetryFrame);
          if (prof.live_telemetry.active_setup) {
            setActiveSetup(prof.live_telemetry.active_setup as ActiveAccSetup);
          }
          if (prof.live_telemetry.engineer_state) {
            setEngineerState(prof.live_telemetry.engineer_state as EngineerState);
          }
          setLiveAlert(prof.live_telemetry.live_alert || null);
          if (
            Array.isArray(prof.live_telemetry.live_trace) &&
            prof.live_telemetry.live_trace.length > 0
          ) {
            setTrace(prof.live_telemetry.live_trace);
          }
          if (
            Array.isArray(prof.live_telemetry.live_errors) &&
            prof.live_telemetry.live_errors.length > 0
          ) {
            setDrivingErrors(prof.live_telemetry.live_errors);
          }
        } else {
          setIsAccLive(false);
          // Conservamos el último sample de telemetría para que un amigo o espectador
          // pueda ver la telemetría, presiones y setup de la última sesión sin pantalla en blanco
          if (prof.live_telemetry?.sample) {
            setFrame(prof.live_telemetry.sample as TelemetryFrame);
          }
          if (prof.live_telemetry?.active_setup) {
            setActiveSetup(prof.live_telemetry.active_setup as ActiveAccSetup);
          }
          if (prof.live_telemetry?.engineer_state) {
            setEngineerState(prof.live_telemetry.engineer_state as EngineerState);
          }
          setLiveAlert(null);
        }
      }

      if (Array.isArray(state.setups) && state.setups.length > 0) {
        setSetups(
          state.setups.map((s: Record<string, unknown>) => ({
            id: String(s.id),
            version_num: Number(s.version_num || 1),
            file_name: String(s.file_name || "APEX_SETUP_1.json"),
            full_path: `Documents\\Assetto Corsa Competizione\\Setups\\${s.car_model}\\${s.track_name}\\${s.file_name}`,
            car_model: String(s.car_model || "gt3"),
            track_name: String(s.track_name || "circuit"),
            input_mode: (s.input_mode as InputMode) || "gamepad",
            created_at: String(s.created_at || ""),
            air_temp: Number(s.air_temp || 0),
            road_temp: Number(s.road_temp || 0),
            best_lap_ms: Number(s.best_lap_ms || 0),
            changes_summary: Array.isArray(s.changes_summary)
              ? (s.changes_summary as SetupChangeItem[])
              : [],
            setup_json: (s.setup_json as Record<string, unknown>) || {},
          }))
        );
      }

      if (state.track_records && typeof state.track_records === "object") {
        setTrackRecords(state.track_records);
      }

      if (state.last_lap) {
        if (
          Array.isArray(state.last_lap.telemetry_trace) &&
          state.last_lap.telemetry_trace.length > 0
        ) {
          setTrace((prev) =>
            prev.length > 0 ? prev : state.last_lap.telemetry_trace
          );
        }
        if (
          Array.isArray(state.last_lap.driving_errors) &&
          state.last_lap.driving_errors.length > 0
        ) {
          setDrivingErrors((prev) =>
            prev.length > 0 ? prev : state.last_lap.driving_errors
          );
        }
      }
    } catch {
      // Ignorar errores transitorios
    }
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const hostParam = params.get("agent");
    if (hostParam) {
      setAgentHost(hostParam);
    }

    fetchCloudState();
    const interval = setInterval(fetchCloudState, 1500);
    return () => clearInterval(interval);
  }, [fetchCloudState]);

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let isUnmounted = false;

    function connectWs() {
      if (isUnmounted) return;
      try {
        const ws = new WebSocket(`ws://${agentHost}:8765`);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isUnmounted) {
            setWsConnected(true);
            wsActiveRef.current = true;
          }
        };

        ws.onmessage = (evt) => {
          try {
            const data = JSON.parse(evt.data);
            if (
              data.input_mode &&
              ["keyboard", "gamepad", "wheel"].includes(data.input_mode)
            ) {
              setInputModeState(data.input_mode as InputMode);
            }
            if (
              data.voice_mode &&
              ["companion", "car_state", "telemetry"].includes(data.voice_mode)
            ) {
              setVoiceModeState(data.voice_mode as VoiceMode);
            }
            if (typeof data.voice_volume === "number") {
              setVoiceVolumeState(data.voice_volume);
            }

            if (data.type === "telemetry_standby" || !data.is_live_acc) {
              setIsAccLive(false);
              setFrame(null);
              setEngineerState(null);
              setLiveAlert(null);
              return;
            }

            if (
              data.type === "telemetry_frame" &&
              data.sample &&
              data.sample.is_live_acc
            ) {
              setIsAccLive(true);
              setFrame(data.sample);
              if (data.active_setup) {
                setActiveSetup(data.active_setup as ActiveAccSetup);
              }
              if (data.engineer_state) {
                setEngineerState(data.engineer_state as EngineerState);
              }
              setLiveAlert(data.live_alert || null);

              if (
                Array.isArray(data.live_errors) &&
                data.live_errors.length > 0
              ) {
                setDrivingErrors(data.live_errors);
              } else if (data.latest_lap?.driving_errors) {
                setDrivingErrors(data.latest_lap.driving_errors);
              }

              if (
                Array.isArray(data.live_trace) &&
                data.live_trace.length > 0
              ) {
                setTrace(data.live_trace);
              } else if (data.latest_lap?.telemetry_trace) {
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
          wsActiveRef.current = false;
          if (!isUnmounted) {
            setWsConnected(false);
            reconnectTimer = setTimeout(connectWs, 3500);
          }
        };

        ws.onerror = () => {
          wsActiveRef.current = false;
          ws.close();
        };
      } catch {
        wsActiveRef.current = false;
        reconnectTimer = setTimeout(connectWs, 3500);
      }
    }

    connectWs();
    return () => {
      isUnmounted = true;
      wsActiveRef.current = false;
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

      if (isSupabaseConfigured() && profile?.agent_token) {
        const supabase = createClient();
        await supabase.rpc("update_agent_input_mode", {
          p_agent_token: profile.agent_token,
          p_input_mode: mode,
          p_wheel_type: wheelType || null,
        });
      }
    },
    [profile?.agent_token]
  );

  const setVoiceMode = useCallback(
    async (mode: VoiceMode) => {
      setVoiceModeState(mode);
      setProfile((prev) => (prev ? { ...prev, voice_mode: mode } : prev));

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ action: "set_voice_mode", voice_mode: mode })
        );
      }

      if (isSupabaseConfigured() && profile?.agent_token) {
        try {
          const supabase = createClient();
          await supabase.rpc("update_agent_voice_mode", {
            p_agent_token: profile.agent_token,
            p_voice_mode: mode,
          });
        } catch {
          // ignore
        }
      }
    },
    [profile?.agent_token]
  );

  const setVoiceVolume = useCallback(
    async (vol: number) => {
      const clamped = Math.max(0, Math.min(100, Math.round(vol)));
      setVoiceVolumeState(clamped);
      if (typeof window !== "undefined") {
        localStorage.setItem("acc_apex_voice_volume", String(clamped));
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ action: "set_voice_volume", voice_volume: clamped })
        );
      }
    },
    []
  );

  const setDrivingStyle = useCallback(
    async (style: DrivingStyle) => {
      setDrivingStyleState(style);
      if (typeof window !== "undefined") {
        localStorage.setItem("acc_apex_driving_style", style);
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ action: "set_driving_style", driving_style: style })
        );
      }
    },
    []
  );

  const agentConnected = wsConnected || cloudHeartbeatActive;

  return (
    <TelemetryContext.Provider
      value={{
        isAuthenticated,
        profile,
        inputMode,
        setInputMode,
        voiceMode,
        setVoiceMode,
        voiceVolume,
        setVoiceVolume,
        drivingStyle,
        setDrivingStyle,
        agentConnected,
        isAccLive,
        agentHost,
        setAgentHost,
        liveAlert,
        frame,
        activeSetup,
        engineerState,
        trace,
        drivingErrors,
        setups,
        trackRecords,
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
