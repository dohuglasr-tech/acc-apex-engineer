"use client";

import React from "react";
import { TracePoint } from "@/lib/telemetry-store";

export function LapTelemetryChart({ trace }: { trace: TracePoint[] }) {
  if (!trace || trace.length === 0) return null;

  const width = 960;
  const height = 220;
  const maxSpeed = 300;

  const speedPoints = trace
    .map((pt, i) => {
      const x = (i / (trace.length - 1)) * width;
      const y = height - (pt.speed / maxSpeed) * (height - 30) - 15;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const bestSpeedPoints = trace
    .map((pt, i) => {
      const x = (i / (trace.length - 1)) * width;
      const y = height - (pt.best_speed / maxSpeed) * (height - 30) - 15;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const brakePoints = trace
    .map((pt, i) => {
      const x = (i / (trace.length - 1)) * width;
      const y = height - (pt.brake / 100) * (height - 40) - 10;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const gasPoints = trace
    .map((pt, i) => {
      const x = (i / (trace.length - 1)) * width;
      const y = height - (pt.gas / 100) * (height - 40) - 10;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <div className="border-t border-zinc-800/90 pt-8">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div className="text-xs font-semibold uppercase tracking-[0.14em] text-white">
          TRAZA DE TELEMETRÍA DE VUELTA (0% – 100% DISTANCIA DE PISTA)
        </div>

        <div className="flex items-center gap-6 text-[11px] font-mono text-zinc-400">
          <span className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-white inline-block" /> VELOCIDAD
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-zinc-600 inline-block" /> REFERENCIA
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-emerald-500 inline-block" /> ACELERADOR
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-[#E10600] inline-block" /> FRENO
          </span>
        </div>
      </div>

      <div className="w-full overflow-x-auto border border-zinc-900 bg-[#060608]">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-56">
          {[0.25, 0.5, 0.75].map((r, idx) => (
            <line
              key={idx}
              x1={0}
              y1={height * r}
              x2={width}
              y2={height * r}
              stroke="#18181B"
              strokeWidth="1"
            />
          ))}

          <polyline
            fill="none"
            stroke="#10B981"
            strokeOpacity="0.45"
            strokeWidth="1.4"
            points={gasPoints}
          />
          <polyline
            fill="none"
            stroke="#E10600"
            strokeOpacity="0.8"
            strokeWidth="1.6"
            points={brakePoints}
          />
          <polyline
            fill="none"
            stroke="#52525B"
            strokeDasharray="4 4"
            strokeWidth="1.4"
            points={bestSpeedPoints}
          />
          <polyline
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="2"
            points={speedPoints}
          />
        </svg>
      </div>
    </div>
  );
}
