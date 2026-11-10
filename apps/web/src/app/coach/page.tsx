"use client";

import React from "react";
import { useTelemetry, InputMode } from "@/lib/telemetry-store";
import { LapTelemetryChart } from "@/components/LapTelemetryChart";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Gamepad2,
  Gauge,
  Keyboard,
  Wrench,
} from "lucide-react";

export default function CoachPage() {
  const { drivingErrors, inputMode, setInputMode, trace } = useTelemetry();
  const activeMode = inputMode || "wheel";

  const totalLostMs = drivingErrors.reduce((acc, e) => acc + e.time_lost_ms, 0);

  const modes: { id: InputMode; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: "keyboard", label: "Teclado", icon: Keyboard },
    { id: "gamepad", label: "Mando", icon: Gamepad2 },
    { id: "wheel", label: "Volante", icon: Gauge },
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-[#0F1626] border border-slate-800 p-6 flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="text-xs font-mono uppercase text-amber-400 font-bold">
            DRIVING COACH ENGINE · ANÁLISIS CURVA A CURVA (333 Hz)
          </div>
          <h1 className="text-2xl font-extrabold text-white">
            Errores Detectados y Soluciones para tu Periférico ({activeMode.toUpperCase()})
          </h1>
          <p className="text-xs text-slate-400">
            Ganancia potencial por vuelta corrigiendo estos puntos:{" "}
            <strong className="text-emerald-400 font-mono">
              -{(totalLostMs / 1000).toFixed(3)} segundos
            </strong>
          </p>
        </div>

        {/* Selector rápido para ver cómo cambian las soluciones según el periférico */}
        <div className="flex items-center gap-1.5 bg-slate-950 p-1.5 rounded-xl border border-slate-800">
          {modes.map((m) => {
            const Icon = m.icon;
            const active = activeMode === m.id;
            return (
              <button
                key={m.id}
                onClick={() => setInputMode(m.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition ${
                  active
                    ? "bg-sky-500 text-slate-950"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {m.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Lista de Errores por Curva + Solución Personalizada */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {drivingErrors.map((err, idx) => {
          const isHigh = err.severity === "Alta";
          return (
            <div
              key={idx}
              className="rounded-xl bg-[#0F1626] border border-slate-800 p-5 flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-mono font-bold text-sky-400 uppercase">
                    {err.corner}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1 text-xs font-mono text-rose-300 bg-rose-500/15 px-2 py-0.5 rounded border border-rose-500/30">
                      <Clock className="w-3 h-3" /> -{(err.time_lost_ms / 1000).toFixed(2)}s
                    </span>
                    <span
                      className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                        isHigh
                          ? "bg-rose-500/20 text-rose-300"
                          : "bg-amber-500/20 text-amber-300"
                      }`}
                    >
                      Prioridad {err.severity}
                    </span>
                  </div>
                </div>

                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                  {err.type}
                </h3>

                <div className="text-xs font-mono text-slate-400 bg-slate-950/80 px-3 py-2 rounded-lg border border-slate-800/80">
                  Telemetría 333 Hz: {err.metric}
                </div>
              </div>

              <div className="rounded-xl bg-emerald-950/20 border border-emerald-500/30 p-3.5 space-y-1.5">
                <div className="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Solución Concreta ({activeMode.toUpperCase()}) + Compensación de Setup:
                </div>
                <p className="text-xs text-slate-200 leading-relaxed">
                  {err.solution}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="rounded-xl bg-[#0F1626] border border-slate-800 p-4 flex items-center gap-3 text-xs text-slate-300">
        <Wrench className="w-5 h-5 text-sky-400 shrink-0" />
        <span>
          <strong>Sincronización Física Automática:</strong> Todos los errores de entrada,
          scrubbing y tracción detectados arriba ya han sido compensados mecánicamente en tu archivo{" "}
          <code className="text-emerald-300 font-mono">APEX_AUTO_LIVE.json</code>.
        </span>
      </div>

      <LapTelemetryChart trace={trace} />
    </div>
  );
}

