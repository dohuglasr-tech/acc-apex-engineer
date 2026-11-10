"use client";

import React from "react";
import { useTelemetry } from "@/lib/telemetry-store";
import { LocalAIEngineerLiveRadar } from "@/components/LocalAIEngineerLiveRadar";
import { LapTelemetryChart } from "@/components/LapTelemetryChart";

export default function CoachPage() {
  const { drivingErrors, inputMode, trace, engineerState } = useTelemetry();

  const modeName =
    inputMode === "keyboard"
      ? "TECLADO"
      : inputMode === "gamepad"
      ? "MANDO"
      : "VOLANTE";

  const recentCalls = engineerState?.recent_radio_calls || [];

  return (
    <div className="space-y-10">
      {/* Banner / Radar del Ingeniero de Pista IA */}
      <LocalAIEngineerLiveRadar />

      {/* Historial de Radio del Ingeniero */}
      {recentCalls.length > 0 && (
        <div className="bg-[#0B0B0F] border border-zinc-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
            <div>
              <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#E10600]">
                COMUNICACIONES DE RADIO // INGENIERO DE PISTA
              </div>
              <h2 className="text-sm font-semibold text-white mt-0.5">
                Instrucciones preventivas y correcciones transmitidas por voz
              </h2>
            </div>
            <span className="text-[10px] font-mono text-zinc-500 uppercase">
              {recentCalls.length} MENSAJES REGISTRADOS
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {recentCalls.map((call, idx) => (
              <div
                key={idx}
                className="bg-zinc-950/80 border border-zinc-900 rounded-lg p-3 space-y-1.5"
              >
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span
                    className={`uppercase font-semibold px-2 py-0.5 rounded text-[9px] ${
                      call.category === "anticipation"
                        ? "bg-blue-950/70 text-blue-400 border border-blue-900/50"
                        : call.category === "praise"
                        ? "bg-emerald-950/70 text-emerald-400 border border-emerald-900/50"
                        : "bg-orange-950/70 text-orange-400 border border-orange-900/50"
                    }`}
                  >
                    {call.category === "anticipation"
                      ? "ANTICIPACIÓN"
                      : call.category === "praise"
                      ? "ELOGIO"
                      : "CONSEJO TÉCNICO"}
                  </span>
                  <span className="text-zinc-500">[{call.time_str}]</span>
                </div>
                <p className="text-xs text-zinc-200 leading-relaxed font-sans">
                  &ldquo;{call.text}&rdquo;
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabla de Diagnósticos de Curva y Errores Detectados */}
      <div>
        <div className="border-b border-zinc-800 pb-4 mb-4 flex items-center justify-between">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
              TELEMETRÍA COMPARATIVA // CURVA A CURVA
            </div>
            <h2 className="text-sm font-semibold text-white mt-0.5">
              Análisis de frenada, dirección y tracción para {modeName}
            </h2>
          </div>
          {drivingErrors && drivingErrors.length > 0 && (
            <span className="text-[10px] font-mono text-zinc-400 uppercase">
              {drivingErrors.length} EVENTOS ENCONTRADOS
            </span>
          )}
        </div>

        {!drivingErrors || drivingErrors.length === 0 ? (
          <div className="py-12 border border-zinc-900 rounded-lg bg-zinc-950/40 text-center space-y-2">
            <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-zinc-500">
              ESPERANDO REGISTRO DE VUELTA COMPLETA
            </div>
            <p className="text-xs text-zinc-400 max-w-md mx-auto leading-relaxed">
              Completa una vuelta en Assetto Corsa Competizione para generar el
              desglose detallado de tiempo perdido por curva.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse tabular-nums">
              <thead>
                <tr className="border-b border-zinc-800 text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
                  <th className="py-3 pr-4">POS.</th>
                  <th className="py-3 px-4">CURVA / SECTOR</th>
                  <th className="py-3 px-4">EVENTO DETECTADO</th>
                  <th className="py-3 px-4">MÉTRICA DE TELEMETRÍA</th>
                  <th className="py-3 px-4">TIEMPO PERDIDO</th>
                  <th className="py-3 pl-4">CORRECCIÓN DE PILOTAJE Y SETUP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900 text-xs">
                {drivingErrors.map((err, idx) => (
                  <tr key={idx} className="hover:bg-zinc-950/80 transition">
                    <td className="py-4 pr-4 align-top font-mono text-zinc-500">
                      {String(idx + 1).padStart(2, "0")}
                    </td>
                    <td className="py-4 px-4 align-top font-medium text-white whitespace-nowrap">
                      {err.corner}
                    </td>
                    <td className="py-4 px-4 align-top text-zinc-200">
                      {err.type}
                    </td>
                    <td className="py-4 px-4 align-top font-mono text-zinc-400">
                      {err.metric}
                    </td>
                    <td className="py-4 px-4 align-top font-mono text-[#E10600] whitespace-nowrap">
                      -{(err.time_lost_ms / 1000).toFixed(2)}s
                    </td>
                    <td className="py-4 pl-4 align-top text-zinc-300 leading-relaxed max-w-md">
                      {err.solution}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <LapTelemetryChart trace={trace} />
    </div>
  );
}
