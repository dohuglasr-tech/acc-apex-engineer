"use client";

import React from "react";
import { useTelemetry } from "@/lib/telemetry-store";
import { SetupDiffViewer } from "@/components/SetupDiffViewer";

export default function SetupsPage() {
  const { setups } = useTelemetry();

  if (!setups || setups.length === 0) {
    return (
      <div className="py-16 border-t border-b border-zinc-900 text-center space-y-3">
        <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-zinc-500">
          SIN SETUPS INYECTADOS EN EL HISTORIAL ACTUAL
        </div>
        <p className="text-xs text-zinc-400 max-w-md mx-auto leading-relaxed">
          Los archivos de setup (.json) se calculan e inyectan automáticamente en
          Documents\Assetto Corsa Competizione\Setups al completar vueltas en
          pista.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {setups.map((setup) => (
        <SetupDiffViewer key={setup.id} setup={setup} />
      ))}
    </div>
  );
}
