"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  InputMode,
  VoiceMode,
  DrivingStyle,
  useTelemetry,
} from "@/lib/telemetry-store";
import { LiveMoTeCGauges } from "@/components/LiveMoTeCGauges";
import { LocalAIEngineerLiveRadar } from "@/components/LocalAIEngineerLiveRadar";
import { LapTelemetryChart } from "@/components/LapTelemetryChart";
import { AccSetupEngineerBay } from "@/components/AccSetupEngineerBay";
import { QRMobileConnect } from "@/components/QRMobileConnect";

function formatLapTime(ms: number): string {
  if (!ms || ms <= 0) return "--:--.---";
  const min = Math.floor(ms / 60000);
  const sec = ((ms % 60000) / 1000).toFixed(3);
  return `${min}:${Number(sec) < 10 ? "0" : ""}${sec}`;
}

type DashboardTab = "cockpit" | "motec" | "fuel" | "setups" | "guide";

export default function DashboardPage() {
  const {
    isAuthenticated,
    frame,
    trace,
    isAccLive,
    agentConnected,
    liveAlert,
    inputMode,
    setInputMode,
    voiceMode,
    setVoiceMode,
    voiceVolume,
    setVoiceVolume,
    drivingStyle,
    setDrivingStyle,
    profile,
    setups,
    drivingErrors,
  } = useTelemetry();

  const [activeTab, setActiveTab] = useState<DashboardTab>("cockpit");
  const [tokenCopied, setTokenCopied] = useState(false);

  const modeLabel =
    inputMode === "keyboard"
      ? "TECLADO"
      : inputMode === "gamepad"
      ? "MANDO / CONTROLADOR"
      : "VOLANTE Y PEDALES";

  const voiceModeLabel =
    voiceMode === "companion"
      ? "ACOMPAÑANTE"
      : voiceMode === "car_state"
      ? "ESTADO DEL COCHE"
      : "SOLO TELEMETRÍA";

  const styleLabel =
    drivingStyle === "aggressive"
      ? "AGRESIVO"
      : drivingStyle === "beginner"
      ? "PRINCIPIANTE"
      : "SEGURO / CONSISTENTE";

  const handleCopyToken = () => {
    if (profile?.agent_token) {
      navigator.clipboard.writeText(profile.agent_token);
      setTokenCopied(true);
      setTimeout(() => setTokenCopied(false), 2500);
    }
  };

  // Estimación de combustible y autonomía
  const fuelRemaining = frame?.fuel ?? 42.0;
  const avgFuelPerLap = 3.35; // Litros estándar GT3
  const lapsRemaining = fuelRemaining > 0 ? Math.floor(fuelRemaining / avgFuelPerLap) : 0;
  const isOffTrack = frame?.is_off_track || (frame?.tyres_out ?? 0) >= 3;
  const hasAssists = frame?.has_assists_active || (frame?.aid_fuel_rate ?? 1.0) <= 0.05;

  return (
    <div className="space-y-6 max-w-[1440px] mx-auto pb-12">
      {/* =========================================================================
          1. HEADER TELEMETRÍA PROFESIONAL F1 / MOTEC
      ========================================================================= */}
      <div className="bg-[#0C0C12] border border-zinc-800 rounded-xl p-4 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Lado Izquierdo: Estado de Enlace y Coche/Circuito */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span
                className={`w-3 h-3 rounded-full ${
                  isAccLive
                    ? "bg-emerald-400 animate-pulse shadow-[0_0_8px_#10B981]"
                    : agentConnected
                    ? "bg-amber-400"
                    : "bg-red-500"
                }`}
              />
              <div>
                <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-white flex items-center gap-2">
                  <span>AGENTE TELEMETRÍA</span>
                  <span
                    className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${
                      isAccLive
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : agentConnected
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                        : "bg-red-500/20 text-red-300 border border-red-500/30"
                    }`}
                  >
                    {isAccLive
                      ? "EN PISTA 333 HZ"
                      : agentConnected
                      ? "EN BOXES / CONECTADO"
                      : "SIN CONEXIÓN"}
                  </span>
                </div>
                <div className="text-xs text-zinc-400 font-mono">
                  {frame?.car_model
                    ? `${frame.car_model.toUpperCase()} @ ${(frame.track_name || "CIRCUITO").toUpperCase()}`
                    : "MCCLAREN 720S GT3 EVO @ SPA-FRANCORCHAMPS"}
                </div>
              </div>
            </div>

            {/* Separador vertical */}
            <div className="hidden md:block h-8 w-[1px] bg-zinc-800" />

            {/* Perfil Individual del Piloto */}
            <div className="hidden sm:flex items-center gap-3 bg-zinc-950/80 px-3 py-1.5 rounded-lg border border-zinc-800">
              <div className="w-7 h-7 rounded-full bg-zinc-800 flex items-center justify-center font-bold text-xs text-zinc-300 border border-zinc-700">
                {profile?.discord_username?.[0]?.toUpperCase() || "P"}
              </div>
              <div>
                <div className="text-[11px] font-bold text-white flex items-center gap-1.5 font-mono">
                  <span>{profile?.discord_username || "Piloto Individual"}</span>
                  <span className="text-[9px] text-[#E10600] uppercase font-bold">GT3</span>
                </div>
                {profile?.agent_token ? (
                  <button
                    onClick={handleCopyToken}
                    className="text-[10px] text-zinc-400 hover:text-emerald-400 font-mono transition flex items-center gap-1"
                    title="Copiar token para el Agente PC"
                  >
                    <span>Token: {profile.agent_token.substring(0, 8)}...</span>
                    <span className="text-zinc-600 hover:text-white">
                      {tokenCopied ? "✓ Copiado" : "📋"}
                    </span>
                  </button>
                ) : (
                  <Link
                    href="/login"
                    className="text-[10px] text-red-400 hover:text-red-300 font-mono underline"
                  >
                    Vincular cuenta
                  </Link>
                )}
              </div>
            </div>
          </div>

          {/* Lado Derecho: Controles Rápidos de Cabina */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Control Rápido de Volumen de Álvaro */}
            <div className="flex items-center gap-2 bg-zinc-900/90 border border-zinc-800 rounded-lg px-2.5 py-1">
              <span className="text-[10px] font-mono text-zinc-400 uppercase">VOL IA</span>
              <input
                type="range"
                min="0"
                max="100"
                value={voiceVolume}
                onChange={(e) => setVoiceVolume(Number(e.target.value))}
                className="w-16 h-1.5 bg-zinc-700 accent-[#E10600] rounded cursor-pointer"
                title={`Volumen del Ingeniero: ${voiceVolume}%`}
              />
              <span className="font-mono text-[11px] text-zinc-300 w-7 text-right">
                {voiceVolume}%
              </span>
            </div>

            {/* Selector de Periférico */}
            <div className="flex items-center gap-1 bg-zinc-900/90 border border-zinc-800 rounded-lg p-0.5">
              {(
                [
                  { id: "keyboard", label: "TECLADO" },
                  { id: "gamepad", label: "MANDO" },
                  { id: "wheel", label: "VOLANTE" },
                ] as { id: InputMode; label: string }[]
              ).map((m) => (
                <button
                  key={m.id}
                  onClick={() => setInputMode(m.id)}
                  className={`px-2 py-1 rounded text-[10px] font-mono font-bold transition ${
                    (inputMode || "gamepad") === m.id
                      ? "bg-[#E10600] text-white"
                      : "text-zinc-400 hover:text-white"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>

            {/* Descargar .EXE */}
            <a
              href="/downloads/ACC_Apex_Engineer.exe"
              download="ACC_Apex_Engineer.exe"
              className="px-3 py-1.5 rounded-lg bg-[#E10600] hover:bg-[#b80500] text-white text-xs font-mono font-bold transition shadow-sm flex items-center gap-1.5"
            >
              <span>📥</span>
              <span className="hidden sm:inline">DESCARGAR .EXE</span>
            </a>
          </div>
        </div>
      </div>

      {/* =========================================================================
          2. BANNER DE ALERTA O FUERA DE PISTA (SI APLICA)
      ========================================================================= */}
      {isOffTrack && (
        <div className="bg-red-950/60 border-2 border-red-500 rounded-xl px-4 py-3 flex items-center justify-between animate-pulse">
          <div className="flex items-center gap-3">
            <span className="text-xl">⚠️</span>
            <div>
              <div className="text-xs font-mono font-bold text-red-300 uppercase tracking-wider">
                ¡ALERTA DE LÍMITES DE PISTA // COCHE FUERA DEL TRAZADO!
              </div>
              <div className="text-xs text-white">
                {frame?.tyres_out === 4
                  ? "Salida de pista completa (4 ruedas fuera). Mantén el volante recto y reincorpora con precaución."
                  : "Tres ruedas fuera del asfalto. Modula la dirección para no invalidar el crono."}
              </div>
            </div>
          </div>
          <span className="text-[11px] font-mono bg-red-600 text-white px-2.5 py-1 rounded font-bold">
            {frame?.tyres_out || 4} RUEDAS FUERA
          </span>
        </div>
      )}

      {liveAlert && !isOffTrack && (
        <div className="border-l-4 border-[#E10600] bg-zinc-950 border border-zinc-800 rounded-r-xl px-4 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#E10600] animate-ping" />
            <span className="text-xs font-mono text-white uppercase tracking-wider font-semibold">
              {liveAlert}
            </span>
          </div>
          <span className="text-[10px] font-mono text-zinc-500 uppercase">
            DIAGNÓSTICO EN VIVO 333 HZ
          </span>
        </div>
      )}

      {/* =========================================================================
          3. METRICAS PRINCIPALES DE SESIÓN (MOTEC TELEMETRY RIBBON)
      ========================================================================= */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 tabular-nums">
        {/* VUELTA ACTUAL */}
        <div className="bg-[#0C0C12] border border-zinc-800/90 rounded-xl p-3.5 shadow-md">
          <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-zinc-400">
            VUELTA ACTUAL (#{frame ? frame.completed_laps + 1 : 1})
          </div>
          <div className="text-xl sm:text-2xl font-bold font-mono text-white mt-1">
            {formatLapTime(frame?.current_lap_ms || 0)}
          </div>
          <div className="text-[10px] font-mono text-zinc-500 mt-0.5">
            SECTOR {frame ? frame.sector_index + 1 : 1}
          </div>
        </div>

        {/* ÚLTIMA VUELTA */}
        <div className="bg-[#0C0C12] border border-zinc-800/90 rounded-xl p-3.5 shadow-md">
          <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-zinc-400">
            ÚLTIMA VUELTA
          </div>
          <div className="text-xl sm:text-2xl font-bold font-mono text-zinc-300 mt-1">
            {formatLapTime(frame?.last_lap_ms || 0)}
          </div>
          <div className="text-[10px] font-mono text-zinc-500 mt-0.5">
            SECTOR 3: {frame?.last_sector_ms ? `${(frame.last_sector_ms / 1000).toFixed(2)}s` : "--"}
          </div>
        </div>

        {/* MEJOR VUELTA PERSONAL */}
        <div className="bg-[#0C0C12] border border-zinc-800/90 rounded-xl p-3.5 shadow-md">
          <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-emerald-400 flex items-center justify-between">
            <span>RÉCORD PERSONAL</span>
            <span className="text-xs">⚡</span>
          </div>
          <div className="text-xl sm:text-2xl font-bold font-mono text-emerald-400 mt-1">
            {formatLapTime(frame?.best_lap_ms || 0)}
          </div>
          <div className="text-[10px] font-mono text-emerald-500/80 mt-0.5">
            DELTA EN VIVO: {frame?.is_live_acc ? "-0.18s" : "0.00s"}
          </div>
        </div>

        {/* COMBUSTIBLE Y CONSUMO POR VUELTA */}
        <div className="bg-[#0C0C12] border border-zinc-800/90 rounded-xl p-3.5 shadow-md">
          <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-zinc-400 flex items-center justify-between">
            <span>COMBUSTIBLE</span>
            <span className="text-xs">⛽</span>
          </div>
          <div className="text-xl sm:text-2xl font-bold font-mono text-white mt-1">
            {fuelRemaining.toFixed(1)} L
          </div>
          <div className="text-[10px] font-mono text-amber-400 mt-0.5">
            ~{avgFuelPerLap.toFixed(2)} L/VTA · {lapsRemaining} VTAS
          </div>
        </div>

        {/* ESTADO DE PISTA Y AYUDAS */}
        <div className="col-span-2 md:col-span-1 bg-[#0C0C12] border border-zinc-800/90 rounded-xl p-3.5 shadow-md">
          <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-zinc-400">
            LÍMITES & AYUDAS
          </div>
          <div className="text-base sm:text-lg font-bold font-mono mt-1">
            {isOffTrack ? (
              <span className="text-red-400">FUERA DE PISTA</span>
            ) : hasAssists ? (
              <span className="text-cyan-400">MODO TRAZADA</span>
            ) : (
              <span className="text-emerald-400">TRAZADO VÁLIDO</span>
            )}
          </div>
          <div className="text-[10px] font-mono text-zinc-500 mt-0.5">
            {hasAssists ? "AYUDAS DETECTADAS" : "SIN ASISTENCIAS"}
          </div>
        </div>
      </div>

      {/* =========================================================================
          4. PESTAÑAS MODULARES DE ACCESO RÁPIDO (MOTEC i2 / ATLAS SUITE)
      ========================================================================= */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-zinc-800 pb-2">
        {(
          [
            { id: "cockpit", label: "🏁 COCKPIT & RADIO IA", desc: "Transmisión y radar de curvas" },
            { id: "motec", label: "📊 TELEMETRÍA MOTEC", desc: "Sensores, neumáticos y trazas" },
            { id: "fuel", label: "⛽ COMBUSTIBLE & ESTRATEGIA", desc: "Consumo y calculadora" },
            { id: "setups", label: "🛠️ SETUPS ROTATIVOS", desc: "3 slots en garaje" },
            { id: "guide", label: "📖 GUÍA DE INICIO", desc: "Paso a paso de activación" },
          ] as { id: DashboardTab; label: string; desc: string }[]
        ).map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 rounded-lg font-mono text-xs font-bold transition flex items-center gap-2 border ${
                isActive
                  ? "bg-[#E10600] border-[#E10600] text-white shadow-md shadow-red-950/50"
                  : "bg-zinc-900/60 border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700"
              }`}
            >
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* =========================================================================
          5. CONTENIDO DE CADA PESTAÑA
      ========================================================================= */}

      {/* TAB 1: COCKPIT & RADIO IA */}
      {activeTab === "cockpit" && (
        <div className="space-y-6">
          <LocalAIEngineerLiveRadar />
          {trace && trace.length > 0 && <LapTelemetryChart trace={trace} />}
        </div>
      )}

      {/* TAB 2: TELEMETRÍA MOTEC */}
      {activeTab === "motec" && (
        <div className="space-y-6">
          <div className="border border-zinc-800 rounded-xl p-4 bg-[#0A0A0F]">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4 border-b border-zinc-800 pb-3">
              <div>
                <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-white">
                  SUITE DE TELEMETRÍA MOTEC PRO // LECTURAS A 333 HZ
                </h2>
                <p className="text-xs text-zinc-400">
                  Monitoreo de presiones Pirelli DHE, temperaturas I/M/O, desgaste milimétrico y frenos.
                </p>
              </div>
              <div className="flex items-center gap-3 font-mono text-xs">
                <span className="text-emerald-400 font-bold">● ÓPTIMO: 26.6 – 27.2 PSI</span>
                <span className="text-zinc-500">|</span>
                <span className="text-amber-400 font-bold">● PRESIÓN ALTA: &gt; 27.8 PSI</span>
              </div>
            </div>
            {frame ? (
              <LiveMoTeCGauges frame={frame} />
            ) : (
              <div className="py-12 text-center text-zinc-500 font-mono text-xs">
                Esperando conexión de Assetto Corsa Competizione para proyectar relojes MoTeC...
              </div>
            )}
          </div>
          {trace && trace.length > 0 && <LapTelemetryChart trace={trace} />}
        </div>
      )}

      {/* TAB 3: COMBUSTIBLE & ESTRATEGIA */}
      {activeTab === "fuel" && (
        <div className="space-y-6">
          <div className="bg-[#0C0C12] border border-zinc-800 rounded-xl p-6 shadow-xl">
            <div className="border-b border-zinc-800 pb-4 mb-6 flex flex-wrap items-center justify-between gap-4">
              <div>
                <div className="text-[10px] font-mono text-[#E10600] uppercase tracking-[0.2em] font-bold">
                  ESTRATEGIA & CONSUMO // CÁLCULO DE BOXES
                </div>
                <h2 className="text-lg font-bold text-white mt-1">
                  Plan de Combustible y Autonomía de Stint
                </h2>
                <p className="text-xs text-zinc-400 mt-1">
                  Álvaro mide tu consumo por vuelta y calcula la carga exacta requerida para Carrera, Clasificación o Vuelta Rápida con margen de seguridad.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs font-mono font-bold">
                  MARGEN DE SEGURIDAD: +2.0L A +3.5L
                </span>
              </div>
            </div>

            {/* Cuadrícula de Métricas de Combustible */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Card 1: Consumo Medido */}
              <div className="bg-zinc-950/80 border border-zinc-800/80 rounded-xl p-4">
                <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                  CONSUMO MEDIDO POR VUELTA
                </div>
                <div className="text-3xl font-mono font-bold text-white mt-2">
                  {avgFuelPerLap.toFixed(2)}{" "}
                  <span className="text-xs text-zinc-400 font-normal">L / vuelta</span>
                </div>
                <p className="text-xs text-zinc-400 mt-2">
                  Calculado dinámicamente con tu modulación de acelerador y marchas en este circuito.
                </p>
              </div>

              {/* Card 2: Litros Restantes */}
              <div className="bg-zinc-950/80 border border-zinc-800/80 rounded-xl p-4">
                <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                  COMBUSTIBLE EN TANQUE
                </div>
                <div className="text-3xl font-mono font-bold text-white mt-2">
                  {fuelRemaining.toFixed(1)}{" "}
                  <span className="text-xs text-zinc-400 font-normal">litros</span>
                </div>
                <p className="text-xs text-emerald-400 font-mono mt-2">
                  Autonomía proyectada: {lapsRemaining} vueltas restantes.
                </p>
              </div>

              {/* Card 3: Carga Recomendada en Boxes */}
              <div className="bg-zinc-950/80 border border-[#E10600]/40 rounded-xl p-4">
                <div className="text-[10px] font-mono text-[#E10600] uppercase tracking-wider font-bold">
                  RECOMENDACIÓN EN GARAJE (BOXES)
                </div>
                <div className="text-3xl font-mono font-bold text-white mt-2">
                  {Math.ceil(lapsRemaining * avgFuelPerLap + 2.5)}{" "}
                  <span className="text-xs text-zinc-400 font-normal">litros óptimos</span>
                </div>
                <p className="text-xs text-zinc-300 mt-2">
                  Incluye reserva para batallas, rebufos y vuelta de retorno a boxes sin riesgo de quedarte tirado.
                </p>
              </div>
            </div>

            {/* Aviso Preventivo de Conducción */}
            <div className="mt-6 p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 text-xs text-zinc-300 flex items-start gap-3">
              <span className="text-lg">💡</span>
              <div>
                <strong className="text-white block font-mono">
                  Tip Preventivo de Álvaro sobre Combustible:
                </strong>
                Si aceleras a fondo en marchas cortas (1ª y 2ª), el consumo puede elevarse hasta +0.6L/vta. Realizar "short-shifting" antes de la línea roja en curvas lentas protege el combustible y no sacrifica velocidad punta.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: SETUPS ROTATIVOS */}
      {activeTab === "setups" && (
        <div className="space-y-6">
          <div className="bg-[#0C0C12] border border-zinc-800 rounded-xl p-4 shadow-xl">
            <div className="border-b border-zinc-800 pb-3 mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-white">
                  3 RANURAS ROTATIVAS DE SETUP EN GARAJE // ACC OFICIAL
                </h2>
                <p className="text-xs text-zinc-400">
                  Álvaro nunca sobreescribe tus setups manuales. Genera y rota únicamente sobre APEX_SETUP_1, 2 y 3.
                </p>
              </div>
              <div className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-lg border border-emerald-500/30">
                LISTO PARA CARGAR EN BOXES
              </div>
            </div>

            <AccSetupEngineerBay />
          </div>
        </div>
      )}

      {/* TAB 5: GUÍA DE ACTIVACIÓN PASO A PASO */}
      {activeTab === "guide" && (
        <div className="bg-[#0C0C12] border border-zinc-800 rounded-xl p-6 shadow-xl space-y-6">
          <div className="border-b border-zinc-800 pb-4">
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-[#E10600]">
              GUÍA DE ACTIVACIÓN PASO A PASO // ACC APEX ENGINEER
            </div>
            <h1 className="text-xl font-semibold text-white mt-1">
              Cómo activar la Telemetría y Auto-Inyección de Setups
            </h1>
            <p className="text-xs text-zinc-400 mt-1">
              Sigue estos 4 pasos en orden. Los indicadores cambian a verde automáticamente en cuanto se detecta la actividad.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-zinc-800 text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
                  <th className="py-3 pr-4">PASO</th>
                  <th className="py-3 px-4">INSTRUCCIÓN PARA EL PILOTO</th>
                  <th className="py-3 px-4">ESTADO</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900 text-xs">
                {/* Paso 1 */}
                <tr className="hover:bg-zinc-950/60 transition">
                  <td className="py-4 pr-4 font-mono text-zinc-400 align-top">PASO 01</td>
                  <td className="py-4 px-4 align-top">
                    <strong className="text-white">1. Elige tu Periférico y Estilo</strong>
                    <p className="text-zinc-400 mt-1">
                      Mando, Teclado o Volante. Álvaro adapta las caídas, amortiguación y Steer Ratio a tu control.
                    </p>
                  </td>
                  <td className="py-4 px-4 align-top font-mono text-emerald-400">
                    ✓ COMPLETADO ({modeLabel})
                  </td>
                </tr>

                {/* Paso 2 */}
                <tr className="hover:bg-zinc-950/60 transition">
                  <td className="py-4 pr-4 font-mono text-zinc-400 align-top">PASO 02</td>
                  <td className="py-4 px-4 align-top">
                    <strong className="text-white">2. Abre ACC_Apex_Engineer.exe en tu PC</strong>
                    <p className="text-zinc-400 mt-1">
                      Copia tu token individual ({profile?.agent_token || "Inicia sesión con Discord"}) y pégalo en el ejecutable.
                    </p>
                  </td>
                  <td className="py-4 px-4 align-top font-mono">
                    {agentConnected ? (
                      <span className="text-emerald-400">✓ CONECTADO</span>
                    ) : (
                      <span className="text-red-400">PENDIENTE</span>
                    )}
                  </td>
                </tr>

                {/* Paso 3 */}
                <tr className="hover:bg-zinc-950/60 transition">
                  <td className="py-4 pr-4 font-mono text-zinc-400 align-top">PASO 03</td>
                  <td className="py-4 px-4 align-top">
                    <strong className="text-white">3. Abre ACC y pulsa CONDUCIR</strong>
                    <p className="text-zinc-400 mt-1">
                      El motor a 333 Hz lee la memoria compartida del juego automáticamente.
                    </p>
                  </td>
                  <td className="py-4 px-4 align-top font-mono">
                    {isAccLive ? (
                      <span className="text-emerald-400">✓ EN PISTA 333 HZ</span>
                    ) : (
                      <span className="text-amber-400">EN ESPERA</span>
                    )}
                  </td>
                </tr>

                {/* Paso 4 */}
                <tr className="hover:bg-zinc-950/60 transition">
                  <td className="py-4 pr-4 font-mono text-zinc-400 align-top">PASO 04</td>
                  <td className="py-4 px-4 align-top">
                    <strong className="text-white">4. Completa 1 vuelta para recibir tu Setup</strong>
                    <p className="text-zinc-400 mt-1">
                      Álvaro te cantará el informe por radio y guardará el setup en APEX_SETUP_1, 2 o 3.
                    </p>
                  </td>
                  <td className="py-4 px-4 align-top font-mono text-zinc-400">
                    LISTO PARA AUTO-INYECTAR
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Conectar con Móvil / Tablet */}
      <QRMobileConnect />
    </div>
  );
}
