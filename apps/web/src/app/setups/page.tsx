"use client";

import React from "react";
import { useTelemetry } from "@/lib/telemetry-store";
import { SetupDiffViewer } from "@/components/SetupDiffViewer";
import { ShieldCheck, Zap } from "lucide-react";

export default function SetupsPage() {
  const { setups, inputMode, triggerForceInject } = useTelemetry();

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-[#0F1626] border border-slate-800 p-6 flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 text-xs font-mono font-bold text-emerald-400 uppercase">
            <ShieldCheck className="w-4 h-4" /> AUTO-INYECTOR DE SETUPS EN TIEMPO REAL
          </div>
          <h1 className="text-2xl font-extrabold text-white">
            Historial de Setups Auto-Inyectados (`APEX_AUTO_LIVE.json`)
          </h1>
          <p className="text-xs text-slate-400">
            Inyectados automáticamente en{" "}
            <code className="text-sky-300 font-mono">
              Documents\Assetto Corsa Competizione\Setups\&lt;coche&gt;\&lt;circuito&gt;\
            </code>{" "}
            para tu modo <strong>{(inputMode || "wheel").toUpperCase()}</strong>. Nunca toca{" "}
            <code className="text-rose-300 font-mono">controls.json</code>.
          </p>
        </div>

        <button
          onClick={triggerForceInject}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow-lg shadow-emerald-500/20"
        >
          <Zap className="w-4 h-4" />
          Generar Nueva Iteración Ahora
        </button>
      </div>

      <div className="space-y-6">
        {setups.map((setup) => (
          <SetupDiffViewer key={setup.id} setup={setup} />
        ))}
      </div>
    </div>
  );
}
