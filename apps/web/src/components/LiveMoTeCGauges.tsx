"use client";

import React from "react";
import { TelemetryFrame } from "@/lib/telemetry-store";

export function LiveMoTeCGauges({ frame }: { frame: TelemetryFrame }) {
  const rpmPct = Math.min(100, Math.round((frame.rpms / frame.max_rpm) * 100));
  const gearLabel =
    frame.gear < 0 ? "R" : frame.gear === 0 ? "N" : String(frame.gear);

  const wheelLabels = [
    "FL · Del. Izq.",
    "FR · Del. Der.",
    "RL · Tras. Izq.",
    "RR · Tras. Der.",
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
      {/* Panel Central Velocímetro GT3, Marcha, RPM y Pedales */}
      <div className="lg:col-span-5 rounded-xl bg-[#0F1626] border border-slate-800 p-5 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="font-mono uppercase tracking-wider text-sky-400">
              TELEMETRÍA GT3 · 60 FPS
            </span>
            <span className="font-mono">
              {frame.car_model.toUpperCase()} @ {frame.track_name.toUpperCase()}
            </span>
          </div>

          {/* Barra de luces de cambio (Shift Lights) */}
          <div className="w-full h-3 bg-slate-900 rounded-full overflow-hidden border border-slate-800 mb-4 p-0.5">
            <div
              className={`h-full rounded-full transition-all duration-75 ${
                rpmPct > 92
                  ? "bg-rose-500"
                  : rpmPct > 80
                  ? "bg-amber-400"
                  : "bg-emerald-400"
              }`}
              style={{ width: `${rpmPct}%` }}
            />
          </div>

          <div className="grid grid-cols-3 items-center gap-3 my-2">
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 text-center">
              <div className="text-[11px] text-slate-400 uppercase">Velocidad</div>
              <div className="text-3xl font-extrabold font-mono text-white">
                {Math.round(frame.speed_kmh)}
              </div>
              <div className="text-[11px] text-sky-400 font-mono">km/h</div>
            </div>

            <div className="bg-slate-950 border-2 border-sky-500/40 rounded-xl p-3 text-center shadow-inner">
              <div className="text-[10px] text-slate-400 uppercase">Marcha</div>
              <div className="text-4xl font-black font-mono text-sky-400">
                {gearLabel}
              </div>
              <div className="text-[10px] text-slate-500 font-mono">SEQ</div>
            </div>

            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 text-center">
              <div className="text-[11px] text-slate-400 uppercase">Motor</div>
              <div className="text-2xl font-bold font-mono text-white">
                {frame.rpms}
              </div>
              <div className="text-[11px] text-amber-400 font-mono">RPM</div>
            </div>
          </div>
        </div>

        {/* Pedales: Gas, Freno y Ángulo de Dirección */}
        <div className="space-y-2.5 mt-4 pt-3 border-t border-slate-800/80">
          <div>
            <div className="flex justify-between text-xs font-mono mb-1">
              <span className="text-emerald-400">ACELERADOR (GAS)</span>
              <span className="text-white">{Math.round(frame.gas * 100)}%</span>
            </div>
            <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 transition-all duration-75"
                style={{ width: `${Math.round(frame.gas * 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs font-mono mb-1">
              <span className="text-rose-400">
                FRENO (BIAS {frame.brake_bias.toFixed(1)}%)
              </span>
              <span className="text-white">{Math.round(frame.brake * 100)}%</span>
            </div>
            <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden">
              <div
                className="h-full bg-rose-500 transition-all duration-75"
                style={{ width: `${Math.round(frame.brake * 100)}%` }}
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-1 text-xs font-mono">
            <span className="text-slate-400">
              DIRECCIÓN: {(frame.steer_angle * 100).toFixed(0)}%
            </span>
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                  frame.tc_in_action
                    ? "bg-amber-500 text-slate-950"
                    : "bg-slate-800 text-slate-500"
                }`}
              >
                TC
              </span>
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                  frame.abs_in_action
                    ? "bg-rose-500 text-white"
                    : "bg-slate-800 text-slate-500"
                }`}
              >
                ABS
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Panel 4 Gomas Pirelli DHE (26.8 - 26.9 PSI Objetivo) + Temperaturas de Freno + Alturas */}
      <div className="lg:col-span-7 rounded-xl bg-[#0F1626] border border-slate-800 p-5 flex flex-col justify-between">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div>
            <h3 className="text-sm font-bold text-white">
              VENTANA PIRELLI DHE (OBJETIVO: 26.8 – 26.9 PSI EN CALIENTE)
            </h3>
            <p className="text-xs text-slate-400">
              El Auto-Inyector corrige cada rueda a 0.1 PSI por clic al cruzar meta o entrar al Pitlane
            </p>
          </div>
          <div className="text-xs font-mono bg-slate-900 px-3 py-1 rounded-lg border border-slate-800 text-slate-300">
            Aire {frame.air_temp}°C · Asfalto {frame.road_temp}°C
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {[0, 1, 2, 3].map((idx) => {
            const psi = frame.tyre_pressures[idx];
            const coreC = frame.tyre_temps_core[idx];
            const brakeC = frame.brake_temps[idx];
            const optimal = psi >= 26.7 && psi <= 26.98;
            return (
              <div
                key={idx}
                className={`rounded-xl p-3.5 border transition ${
                  optimal
                    ? "bg-emerald-950/20 border-emerald-500/40"
                    : "bg-amber-950/20 border-amber-500/40"
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-bold text-slate-200">
                    {wheelLabels[idx]}
                  </span>
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                      optimal
                        ? "bg-emerald-500/20 text-emerald-300"
                        : "bg-amber-500/20 text-amber-300"
                    }`}
                  >
                    {optimal ? "ÓPTIMO" : "AUTO-AJUSTANDO"}
                  </span>
                </div>

                <div className="text-2xl font-black font-mono text-white">
                  {psi.toFixed(2)}{" "}
                  <span className="text-xs font-normal text-slate-400">PSI</span>
                </div>

                <div className="mt-2 flex items-center justify-between text-xs font-mono text-slate-300">
                  <span>Carcasa: {coreC.toFixed(0)}°C</span>
                  <span
                    className={
                      brakeC > 600
                        ? "text-rose-400 font-bold"
                        : "text-sky-300"
                    }
                  >
                    Freno: {brakeC.toFixed(0)}°C
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Alturas dinámicas (Ride Height) y Fondo Plano */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-4">
            <span className="text-slate-300">
              ALTURA DELANTERA (SPLITTER):{" "}
              <strong
                className={
                  frame.ride_height[0] < 42
                    ? "text-rose-400"
                    : "text-emerald-400"
                }
              >
                {frame.ride_height[0].toFixed(1)} mm
              </strong>
            </span>
            <span className="text-slate-300">
              ALTURA TRASERA (DIFUSOR):{" "}
              <strong className="text-sky-400">
                {frame.ride_height[1].toFixed(1)} mm
              </strong>
            </span>
          </div>
          <span className="text-slate-400">
            Combustible: <strong className="text-white">{frame.fuel} L</strong>
          </span>
        </div>
      </div>
    </div>
  );
}
