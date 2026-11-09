"use client";

import React from "react";
import { TracePoint } from "@/lib/telemetry-store";

export function LapTelemetryChart({ trace }: { trace: TracePoint[] }) {
  if (!trace || trace.length === 0) return null;

  const width = 900;
  const height = 230;
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
    <div className="rounded-xl bg-[#0F1626] border border-slate-800 p-5">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wide">
            TRAZA MO-TEC SUPERPUESTA (0% – 100% DE VUELTA NORMALIZADA)
          </h3>
          <p className="text-xs text-slate-400">
            Comparativa metro a metro contra tu propia mejor vuelta (Velocidad, Acelerador y Trail-Braking)
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-sky-400">
            <span className="w-3 h-0.5 bg-sky-400 inline-block" /> Velocidad Actual
          </span>
          <span className="flex items-center gap-1.5 text-slate-400">
            <span className="w-3 h-0.5 bg-slate-400 inline-block border-b border-dashed" /> Mejor Vuelta
          </span>
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-3 h-0.5 bg-emerald-400 inline-block" /> Gas %
          </span>
          <span className="flex items-center gap-1.5 text-rose-400">
            <span className="w-3 h-0.5 bg-rose-400 inline-block" /> Freno %
          </span>
        </div>
      </div>

      <div className="w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-56 bg-slate-950/90 rounded-lg border border-slate-800/80"
        >
          {/* Líneas horizontales guía */}
          {[0.25, 0.5, 0.75].map((r, idx) => (
            <line
              key={idx}
              x1={0}
              y1={height * r}
              x2={width}
              y2={height * r}
              stroke="#1E293B"
              strokeDasharray="4 4"
              strokeWidth="1"
            />
          ))}

          {/* Marcadores de curvas principales */}
          {[
            { pct: 0.08, label: "T1 La Source" },
            { pct: 0.18, label: "Eau Rouge" },
            { pct: 0.34, label: "Les Combes" },
            { pct: 0.56, label: "Pouhon" },
            { pct: 0.9, label: "Bus Stop" },
          ].map((c, idx) => (
            <g key={idx}>
              <line
                x1={c.pct * width}
                y1={0}
                x2={c.pct * width}
                y2={height}
                stroke="#334155"
                strokeWidth="1"
              />
              <text
                x={c.pct * width + 4}
                y={14}
                fill="#94A3B8"
                fontSize="10"
                fontFamily="monospace"
              >
                {c.label}
              </text>
            </g>
          ))}

          {/* Gas % */}
          <polyline
            fill="none"
            stroke="#10B981"
            strokeOpacity="0.45"
            strokeWidth="1.5"
            points={gasPoints}
          />

          {/* Freno % */}
          <polyline
            fill="none"
            stroke="#F43F5E"
            strokeOpacity="0.7"
            strokeWidth="1.8"
            points={brakePoints}
          />

          {/* Mejor Velocidad */}
          <polyline
            fill="none"
            stroke="#64748B"
            strokeDasharray="5 3"
            strokeWidth="1.5"
            points={bestSpeedPoints}
          />

          {/* Velocidad Actual */}
          <polyline
            fill="none"
            stroke="#38BDF8"
            strokeWidth="2.4"
            points={speedPoints}
          />
        </svg>
      </div>
    </div>
  );
}
