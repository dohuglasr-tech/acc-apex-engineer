"use client";

import React, { useState } from "react";
import { useTelemetry, EngineerState } from "@/lib/telemetry-store";

export function LocalAIEngineerLiveRadar() {
  const { engineerState, frame, isAccLive } = useTelemetry();
  const [showHistory, setShowHistory] = useState(false);

  if (!isAccLive || !frame) return null;

  const eng: Partial<EngineerState> = engineerState || {};
  const upcoming = eng.upcoming_corner;
  const lastCorner = eng.last_corner_analysis;
  const radio = eng.radio_transmission;
  const recentCalls = eng.recent_radio_calls || [];
  const track = eng.track_info;

  const isTransmitting = Boolean(radio?.is_active);

  return (
    <div className="bg-[#0B0B0F] border border-zinc-800 rounded-lg overflow-hidden shadow-2xl">
      {/* Barra superior de estado del Ingeniero de Pista */}
      <div className="bg-[#121218] border-b border-zinc-800/80 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-2.5 h-2.5">
            <span
              className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
                isTransmitting
                  ? "animate-ping bg-[#E10600]"
                  : "bg-emerald-500 animate-pulse"
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                isTransmitting ? "bg-[#E10600]" : "bg-emerald-400"
              }`}
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-white">
              {eng.engineer_name || "ÁLVARO // INGENIERO DE PISTA IA LOCAL"}
            </span>
            <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-zinc-800/80 text-zinc-300 border border-zinc-700/60 uppercase">
              100% LOCAL · 333 HZ
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4 text-[11px] font-mono text-zinc-400">
          {track && (
            <div className="hidden sm:flex items-center gap-1.5">
              <span className="text-zinc-500 uppercase">CIRCUITO:</span>
              <span className="text-zinc-200 font-medium">
                {track.display_name} ({track.length_m}m)
              </span>
            </div>
          )}

          <div className="flex items-center gap-2">
            <span
              className={`text-[10px] font-mono px-2.5 py-0.5 rounded uppercase font-semibold ${
                isTransmitting
                  ? "bg-[#E10600]/20 text-[#E10600] border border-[#E10600]/40"
                  : "bg-emerald-950/40 text-emerald-400 border border-emerald-800/40"
              }`}
            >
              {isTransmitting ? "TRANSMITIENDO EN CABINA" : "CANAL DE RADIO ACTIVO"}
            </span>

            {recentCalls.length > 0 && (
              <button
                type="button"
                onClick={() => setShowHistory((prev) => !prev)}
                className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition"
              >
                {showHistory ? "OCULTAR RADIO" : `HISTORIAL (${recentCalls.length})`}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Grid Principal: Radar de Próxima Curva + Transmisión de Radio + Último Análisis */}
      <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-zinc-800">
        {/* COLUMNA 1: RADAR ANTICIPADO DE CURVA (5 cols) */}
        <div className="lg:col-span-5 p-4 space-y-3 bg-gradient-to-b from-[#0E0E14] to-[#0A0A0E]">
          <div className="flex items-center justify-between">
            <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
              RADAR DE CURVA // SPOTTER ANTICIPADO
            </div>
            {upcoming ? (
              <span className="text-[10px] font-mono text-[#E10600] uppercase font-bold tracking-wider animate-pulse">
                EN APROXIMACIÓN ({upcoming.distance_m} M)
              </span>
            ) : (
              <span className="text-[10px] font-mono text-zinc-500 uppercase">
                TRAZANDO SECTOR {frame.sector_index + 1}
              </span>
            )}
          </div>

          {upcoming ? (
            <div className="space-y-3 pt-1">
              {/* Encabezado de la curva y marcha recomendada */}
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-[#E10600] text-white text-xs font-mono font-bold">
                      {upcoming.id}
                    </span>
                    <h3 className="text-base font-semibold text-white tracking-tight">
                      {upcoming.name}
                    </h3>
                  </div>
                  <div className="text-xs text-zinc-400 mt-1 flex items-center gap-2">
                    <span>Distancia: <strong className="text-white font-mono">{upcoming.distance_m} m</strong></span>
                    <span>·</span>
                    <span>Tiempo: <strong className="text-white font-mono">{upcoming.seconds_away}s</strong></span>
                  </div>
                </div>

                {/* Marcha y velocidad objetivo */}
                <div className="text-right">
                  <div className="text-[10px] font-mono text-zinc-500 uppercase">MARCHA SUGERIDA</div>
                  <div className="text-2xl font-mono font-extrabold text-[#E10600]">
                    {upcoming.gear}ª
                  </div>
                </div>
              </div>

              {/* Barra de progreso de proximidad */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] font-mono text-zinc-500">
                  <span>ZONA DE FRENADA</span>
                  <span>{Math.max(0, upcoming.distance_m)}m para el vértice</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-yellow-500 via-orange-500 to-[#E10600] transition-all duration-150"
                    style={{
                      width: `${Math.min(100, Math.max(10, 100 - (upcoming.distance_m / 400) * 100))}%`,
                    }}
                  />
                </div>
              </div>

              {/* Referencia de frenada y velocidad objetivo */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-zinc-900/80 border border-zinc-800/80 rounded p-2">
                  <div className="text-[9px] font-mono text-zinc-500 uppercase">REFERENCIA VISUAL</div>
                  <div className="font-semibold text-zinc-200 mt-0.5 text-[11px] truncate" title={upcoming.braking_marker}>
                    {upcoming.braking_marker}
                  </div>
                </div>
                <div className="bg-zinc-900/80 border border-zinc-800/80 rounded p-2">
                  <div className="text-[9px] font-mono text-zinc-500 uppercase">VELOCIDAD EN VÉRTICE</div>
                  <div className="font-mono font-bold text-emerald-400 mt-0.5 text-xs">
                    {upcoming.target_speed_kmh} KM/H
                  </div>
                </div>
              </div>

              {/* Nota de trazada técnica */}
              <div className="bg-zinc-950 border-l-2 border-[#E10600] px-3 py-2 text-xs text-zinc-300">
                <span className="text-[9px] font-mono text-zinc-500 uppercase block">TRAZADA RECOMENDADA:</span>
                <p className="mt-0.5 leading-relaxed">{upcoming.racing_line_notes}</p>
              </div>
            </div>
          ) : (
            <div className="py-6 text-center space-y-2">
              <div className="text-zinc-600 font-mono text-xs uppercase tracking-wider">
                SIN FRENADA INMINENTE
              </div>
              <p className="text-xs text-zinc-400 max-w-sm mx-auto leading-relaxed">
                El ingeniero está calculando la telemetría en tiempo real. Te alertará por radio 3 segundos antes del cartel de frenada.
              </p>
            </div>
          )}
        </div>

        {/* COLUMNA 2: RADIO DE INGENIERO EN VIVO (4 cols) */}
        <div className="lg:col-span-4 p-4 space-y-3 bg-[#0B0B10] flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
                COMUNICACIÓN DE RADIO // VOZ NEURAL
              </div>
              {isTransmitting && (
                <div className="flex items-center gap-1">
                  <span className="w-1 h-3 bg-[#E10600] animate-pulse" />
                  <span className="w-1 h-4 bg-[#E10600] animate-pulse delay-75" />
                  <span className="w-1 h-2 bg-[#E10600] animate-pulse delay-150" />
                </div>
              )}
            </div>

            {/* Mensaje de Radio en pantalla estilo F1 Team Radio */}
            <div className="bg-zinc-950 border border-zinc-800/90 rounded-lg p-3.5 space-y-2 shadow-inner">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="text-[#E10600] font-bold uppercase tracking-wider">
                  RADIO · PIT WALL
                </span>
                <span className="text-zinc-500">
                  {radio?.time_str || "EN VIVO"}
                </span>
              </div>
              <p className="text-xs text-white leading-relaxed font-sans font-medium">
                &ldquo;{radio?.text || "Adelante, mantén el ritmo. Te avisaré de cada frenada."}&rdquo;
              </p>
            </div>
          </div>

          <div className="pt-2 text-[11px] text-zinc-500 font-mono flex items-center justify-between border-t border-zinc-800/60">
            <span>MODO DE CONDUCCIÓN:</span>
            <span className="text-zinc-300 font-semibold uppercase">
              {frame.is_in_pit ? "EN BOXES" : "EN PISTA"}
            </span>
          </div>
        </div>

        {/* COLUMNA 3: ÚLTIMO DIAGNÓSTICO DE CURVA (3 cols) */}
        <div className="lg:col-span-3 p-4 space-y-3 bg-[#09090D]">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
            ÚLTIMA CURVA // RENDIMIENTO
          </div>

          {lastCorner ? (
            <div className="space-y-3">
              <div>
                <div className="text-xs text-zinc-400 font-mono uppercase">
                  {lastCorner.corner_id}
                </div>
                <div className="text-sm font-semibold text-white truncate">
                  {lastCorner.corner_name}
                </div>
              </div>

              <div className="flex items-center justify-between bg-zinc-950 border border-zinc-800 rounded p-2.5">
                <div>
                  <div className="text-[9px] font-mono text-zinc-500 uppercase">PUNTUACIÓN</div>
                  <div className="text-xl font-mono font-bold text-white">
                    {lastCorner.score}%
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[9px] font-mono text-zinc-500 uppercase">DELTA VELOCIDAD</div>
                  <div
                    className={`text-sm font-mono font-bold ${
                      lastCorner.speed_delta_kmh >= 0
                        ? "text-emerald-400"
                        : "text-[#E10600]"
                    }`}
                  >
                    {lastCorner.speed_delta_kmh >= 0 ? "+" : ""}
                    {lastCorner.speed_delta_kmh} KM/H
                  </div>
                </div>
              </div>

              <div className="text-[11px] text-zinc-300 leading-snug">
                <span className="text-[9px] font-mono text-zinc-500 uppercase block mb-1">
                  CONSEJO DE MEJORA:
                </span>
                {lastCorner.verdict}
              </div>
            </div>
          ) : (
            <div className="py-6 text-center space-y-1">
              <div className="text-zinc-600 font-mono text-xs uppercase">SIN CURVAS COMPLETADAS</div>
              <p className="text-[11px] text-zinc-500">
                Al salir del primer vértice verás tu puntuación y velocidad vs la referencia óptima.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* HISTORIAL DESPLEGABLE DE MENSAJES DE RADIO */}
      {showHistory && recentCalls.length > 0 && (
        <div className="border-t border-zinc-800 bg-[#07070A] p-4 space-y-2">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500 mb-2">
            REGISTRO DE TRANSMISIONES DE RADIO DE ESTA SESIÓN
          </div>
          <div className="space-y-1.5 max-h-48 overflow-y-auto">
            {recentCalls.map((call, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 text-xs py-1.5 px-2.5 rounded bg-zinc-950 border border-zinc-900"
              >
                <span className="font-mono text-zinc-500 text-[10px] whitespace-nowrap mt-0.5">
                  [{call.time_str}]
                </span>
                <span
                  className={`text-[9px] font-mono uppercase px-1.5 py-0.5 rounded ${
                    call.category === "anticipation"
                      ? "bg-blue-950/60 text-blue-400 border border-blue-900/60"
                      : call.category === "praise"
                      ? "bg-emerald-950/60 text-emerald-400 border border-emerald-900/60"
                      : "bg-orange-950/60 text-orange-400 border border-orange-900/60"
                  }`}
                >
                  {call.category === "anticipation"
                    ? "ANTICIPACIÓN"
                    : call.category === "praise"
                    ? "ELOGIO"
                    : "CONSEJO"}
                </span>
                <p className="text-zinc-300 text-xs leading-relaxed flex-1">
                  {call.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

