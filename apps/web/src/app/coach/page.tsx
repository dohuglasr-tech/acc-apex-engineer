"use client";

import React from "react";
import { useTelemetry } from "@/lib/telemetry-store";
import { LapTelemetryChart } from "@/components/LapTelemetryChart";

export default function CoachPage() {
  const { drivingErrors, inputMode, trace } = useTelemetry();

  if (!drivingErrors || drivingErrors.length === 0) {
    return (
      <div className="py-16 border-t border-b border-zinc-900 text-center space-y-3">
        <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-zinc-500">
          NO CORNER DIAGNOSTICS RECORDED
        </div>
        <p className="text-xs text-zinc-400 max-w-md mx-auto leading-relaxed">
          Completa una vuelta en Assetto Corsa Competizione para generar el
          análisis curva a curva de frenada, dirección y tracción adaptado a tu
          periférico ({(inputMode || "wheel").toUpperCase()}).
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse tabular-nums">
          <thead>
            <tr className="border-b border-zinc-800 text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
              <th className="py-3 pr-4">POS.</th>
              <th className="py-3 px-4">CORNER / SECTOR</th>
              <th className="py-3 px-4">DETECTED EVENT</th>
              <th className="py-3 px-4">TELEMETRY METRIC</th>
              <th className="py-3 px-4">TIME LOSS</th>
              <th className="py-3 pl-4">DRIVER & SETUP CORRECTION</th>
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

      <LapTelemetryChart trace={trace} />
    </div>
  );
}
