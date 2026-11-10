"use client";

import React from "react";
import Link from "next/link";
import { useTelemetry } from "@/lib/telemetry-store";
import { LiveMoTeCGauges } from "@/components/LiveMoTeCGauges";
import { LapTelemetryChart } from "@/components/LapTelemetryChart";
import { QRMobileConnect } from "@/components/QRMobileConnect";
import { AlertTriangle, Sparkles, Sliders, Zap } from "lucide-react";

function formatLapTime(ms: number): string {
  const min = Math.floor(ms / 60000);
  const sec = ((ms % 60000) / 1000).toFixed(3);
  return `${min}:${Number(sec) < 10 ? "0" : ""}${sec}`;
}

export default function DashboardPage() {
  const {
    frame,
    trace,
    inputMode,
    liveAlert,
    setups,
    drivingErrors,
    triggerForceInject,
  } = useTelemetry();

  const latestSetup = setups[0];

  return (
    <div className="space-y-6">
      {/* Barra superior de estado de sesión, tiempos de vuelta y botón de Auto-Inyección */}
      <div className="rounded-xl bg-[#0F1626] border border-slate-800 p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-6">
          <div>
            <div className="text-[11px] font-mono text-slate-400 uppercase">
              Vuelta Actual (#{frame.completed_laps + 1})
            </div>
            <div className="text-xl font-black font-mono text-sky-400">
              {formatLapTime(frame.current_lap_ms)}
            </div>
          </div>

          <div>
            <div className="text-[11px] font-mono text-slate-400 uppercase">
              Última Vuelta
            </div>
            <div className="text-xl font-bold font-mono text-white">
              {formatLapTime(frame.last_lap_ms)}
            </div>
          </div>

          <div>
            <div className="text-[11px] font-mono text-slate-400 uppercase">
              Mejor Vuelta Personal
            </div>
            <div className="text-xl font-bold font-mono text-emerald-400">
              {formatLapTime(frame.best_lap_ms)}
            </div>
          </div>

          <div className="hidden lg:block pl-4 border-l border-slate-800">
            <div className="text-[11px] font-mono text-slate-400 uppercase">
              Último Setup Auto-Inyectado
            </div>
            <div className="text-xs font-mono font-bold text-purple-300">
              {latestSetup?.file_name} (v{latestSetup?.version_num} ·{" "}
              {(inputMode || "wheel").toUpperCase()})
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={triggerForceInject}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow-lg shadow-emerald-500/20"
          >
            <Zap className="w-4 h-4" />
            Auto-Inyectar Setup Ahora
          </button>
          <Link
            href="/coach"
            className="inline-flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 transition"
          >
            <Sparkles className="w-4 h-4 text-amber-400" />
            Ver {drivingErrors.length} Errores/Soluciones
          </Link>
        </div>
      </div>

      {/* Alerta en vivo de 333 Hz */}
      {liveAlert && (
        <div className="rounded-xl bg-rose-500/15 border border-rose-500/40 px-4 py-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 text-xs sm:text-sm font-bold text-rose-200 font-mono">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
            <span>{liveAlert}</span>
          </div>
          <span className="text-[11px] font-mono text-rose-300 uppercase">
            Detector 333 Hz Activo
          </span>
        </div>
      )}

      {/* Relojes MoTeC en vivo a 60 FPS */}
      <LiveMoTeCGauges frame={frame} />

      {/* Gráfica superpuesta de la vuelta */}
      <LapTelemetryChart trace={trace} />

      {/* Resumen rápido de último ajuste de setup + QR Móvil */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-5 rounded-xl bg-[#0F1626] border border-slate-800 p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-emerald-400 uppercase font-mono flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5" /> Auto-Inyector en Tiempo Real
              </span>
              <Link
                href="/setups"
                className="text-xs text-sky-400 hover:underline font-mono"
              >
                Ver tabla completa →
              </Link>
            </div>
            <h3 className="text-sm font-bold text-white mb-2">
              Cambios aplicados en `{latestSetup?.file_name}`
            </h3>
            <ul className="space-y-2">
              {latestSetup?.changes_summary.slice(0, 3).map((c, i) => (
                <li
                  key={i}
                  className="text-xs bg-slate-900/90 border border-slate-800 rounded-lg p-2.5"
                >
                  <div className="font-bold text-slate-200">{c.area}</div>
                  <div className="font-mono text-emerald-400 text-[11px] mt-0.5">
                    {c.before} → {c.after}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="lg:col-span-7">
          <QRMobileConnect />
        </div>
      </div>
    </div>
  );
}

