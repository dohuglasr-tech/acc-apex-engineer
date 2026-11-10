"use client";

import React from "react";
import { TelemetryFrame } from "@/lib/telemetry-store";

export function LiveMoTeCGauges({ frame }: { frame: TelemetryFrame }) {
  const rpmPct = Math.min(100, Math.round((frame.rpms / frame.max_rpm) * 100));
  const gearLabel =
    frame.gear < 0 ? "R" : frame.gear === 0 ? "N" : String(frame.gear);

  const tyres = [
    { pos: "01", code: "DI", name: "Delantero Izquierdo", idx: 0 },
    { pos: "02", code: "DD", name: "Delantero Derecho", idx: 1 },
    { pos: "03", code: "TI", name: "Trasero Izquierdo", idx: 2 },
    { pos: "04", code: "TD", name: "Trasero Derecho", idx: 3 },
  ];

  return (
    <div className="space-y-10">
      {/* Bloque Superior de Telemetría Primaria */}
      <div className="border-t border-b border-zinc-800/90 py-6">
        <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-[0.18em] text-zinc-500 mb-3">
          <span>RÉGIMEN DE MOTOR // INDICADOR DE CAMBIO</span>
          <span>
            {frame.rpms} / {frame.max_rpm} RPM
          </span>
        </div>

        <div className="w-full h-1.5 bg-zinc-900 overflow-hidden mb-8">
          <div
            className={`h-full transition-all duration-75 ${
              rpmPct > 92
                ? "bg-[#E10600]"
                : rpmPct > 80
                ? "bg-amber-500"
                : "bg-white"
            }`}
            style={{ width: `${rpmPct}%` }}
          />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-6 gap-6 tabular-nums">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-500">
              VELOCIDAD
            </div>
            <div className="text-3xl font-semibold text-white font-mono mt-1">
              {Math.round(frame.speed_kmh)}{" "}
              <span className="text-xs text-zinc-500 font-normal">KM/H</span>
            </div>
          </div>

          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-500">
              MARCHA
            </div>
            <div className="text-3xl font-semibold text-white font-mono mt-1">
              {gearLabel}
            </div>
          </div>

          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-500">
              ACELERADOR
            </div>
            <div className="text-3xl font-semibold text-emerald-400 font-mono mt-1">
              {Math.round(frame.gas * 100)}%
            </div>
          </div>

          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-500">
              FRENO
            </div>
            <div className="text-3xl font-semibold text-[#E10600] font-mono mt-1">
              {Math.round(frame.brake * 100)}%
            </div>
          </div>

          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-500">
              ALTURA (DEL/TRAS)
            </div>
            <div className="text-2xl font-semibold text-white font-mono mt-1">
              {frame.ride_height[0].toFixed(0)} / {frame.ride_height[1].toFixed(0)}{" "}
              <span className="text-xs text-zinc-500 font-normal">MM</span>
            </div>
          </div>

          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-500">
              REPARTO FRENO
            </div>
            <div className="text-2xl font-semibold text-white font-mono mt-1">
              {frame.brake_bias.toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* Tabla estilo F1 Standings para los 4 Neumáticos Pirelli DHE y Frenos */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-white">
            TELEMETRÍA DE NEUMÁTICOS PIRELLI DHE Y FRENOS (OBJETIVO: 26.8 – 26.9 PSI)
          </div>
          <div className="text-[11px] font-mono text-zinc-400">
            AMBIENTE {frame.air_temp.toFixed(1)}°C // ASFALTO{" "}
            {frame.road_temp.toFixed(1)}°C
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse tabular-nums">
            <thead>
              <tr className="border-b border-zinc-800 text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
                <th className="py-3 pr-4">POS.</th>
                <th className="py-3 px-4">RUEDA</th>
                <th className="py-3 px-4">PRESIÓN EN CALIENTE</th>
                <th className="py-3 px-4">TEMP. CARCASA</th>
                <th className="py-3 px-4">DISCO DE FRENO</th>
                <th className="py-3 pl-4 text-right">ESTADO</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-900 text-xs">
              {tyres.map((t) => {
                const psi = frame.tyre_pressures[t.idx];
                const coreC = frame.tyre_temps_core[t.idx];
                const brakeC = frame.brake_temps[t.idx];
                const optimal = psi >= 26.7 && psi <= 26.98;
                return (
                  <tr
                    key={t.code}
                    className="hover:bg-zinc-950/80 transition font-mono"
                  >
                    <td className="py-4 pr-4 text-zinc-400">{t.pos}</td>
                    <td className="py-4 px-4 font-sans font-medium text-white flex items-center gap-2.5">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          optimal ? "bg-emerald-400" : "bg-[#E10600]"
                        }`}
                      />
                      <span>{t.name}</span>
                      <span className="text-zinc-500 font-mono text-[11px]">
                        ({t.code})
                      </span>
                    </td>
                    <td className="py-4 px-4 text-white font-semibold">
                      {psi.toFixed(2)} PSI
                    </td>
                    <td className="py-4 px-4 text-zinc-300">
                      {coreC.toFixed(1)} °C
                    </td>
                    <td className="py-4 px-4 text-zinc-300">
                      {brakeC.toFixed(0)} °C
                    </td>
                    <td className="py-4 pl-4 text-right">
                      <span
                        className={`text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-full border ${
                          optimal
                            ? "border-emerald-500/40 text-emerald-400"
                            : "border-zinc-700 text-zinc-400"
                        }`}
                      >
                        {optimal ? "VENTANA ÓPTIMA" : "AJUSTANDO EN META"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
