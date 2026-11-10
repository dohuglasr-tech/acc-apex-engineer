"use client";

import React from "react";
import Link from "next/link";
import { useTelemetry } from "@/lib/telemetry-store";
import { LiveMoTeCGauges } from "@/components/LiveMoTeCGauges";
import { LapTelemetryChart } from "@/components/LapTelemetryChart";
import { QRMobileConnect } from "@/components/QRMobileConnect";

function formatLapTime(ms: number): string {
  if (!ms || ms <= 0) return "--:--.---";
  const min = Math.floor(ms / 60000);
  const sec = ((ms % 60000) / 1000).toFixed(3);
  return `${min}:${Number(sec) < 10 ? "0" : ""}${sec}`;
}

export default function DashboardPage() {
  const { frame, trace, isAccLive, agentConnected, liveAlert } = useTelemetry();

  if (!isAccLive || !frame) {
    return (
      <div className="space-y-12">
        {/* Tabla limpia en espera estilo F1 Standings */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse tabular-nums">
            <thead>
              <tr className="border-b border-zinc-800 text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
                <th className="py-3 pr-4">CANAL</th>
                <th className="py-3 px-4">MÓDULO DE TELEMETRÍA</th>
                <th className="py-3 px-4">ORIGEN</th>
                <th className="py-3 px-4">FRECUENCIA</th>
                <th className="py-3 pl-4 text-right">ESTADO</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-900 text-xs">
              <tr>
                <td className="py-4 pr-4 font-mono text-zinc-500">01</td>
                <td className="py-4 px-4 font-medium text-white">
                  Agente de Escritorio (.EXE)
                </td>
                <td className="py-4 px-4 font-mono text-zinc-400">
                  ws://localhost:8765
                </td>
                <td className="py-4 px-4 font-mono text-zinc-400">60 FPS</td>
                <td className="py-4 pl-4 text-right font-mono">
                  <span
                    className={
                      agentConnected ? "text-emerald-400" : "text-zinc-500"
                    }
                  >
                    {agentConnected ? "CONECTADO" : "ESPERANDO AGENTE"}
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-4 pr-4 font-mono text-zinc-500">02</td>
                <td className="py-4 px-4 font-medium text-white">
                  Memoria Compartida de Físicas ACC
                </td>
                <td className="py-4 px-4 font-mono text-zinc-400">
                  Local\acpmf_physics
                </td>
                <td className="py-4 px-4 font-mono text-zinc-400">333 HZ</td>
                <td className="py-4 pl-4 text-right font-mono text-zinc-500">
                  EN ESPERA (ABRE ACC)
                </td>
              </tr>
              <tr>
                <td className="py-4 pr-4 font-mono text-zinc-500">03</td>
                <td className="py-4 px-4 font-medium text-white">
                  Auto-Inyector de Setups en Tiempo Real
                </td>
                <td className="py-4 px-4 font-mono text-zinc-400">
                  Documents\Assetto Corsa Competizione\Setups
                </td>
                <td className="py-4 px-4 font-mono text-zinc-400">AL CERRAR VUELTA</td>
                <td className="py-4 pl-4 text-right font-mono text-zinc-500">
                  LISTO
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="py-12 border-t border-b border-zinc-900 text-center space-y-5">
          <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-zinc-500">
            SIN SESIÓN DE PISTA ACTIVA DETECTADA
          </div>
          <p className="text-sm text-zinc-300 max-w-lg mx-auto leading-relaxed">
            La aplicación se encuentra en espera limpia. Ejecuta el agente local y
            entra a pista en Assetto Corsa Competizione para iniciar la lectura en
            tiempo real a 333 Hz.
          </p>
          <div className="pt-2 flex items-center justify-center gap-4">
            <Link
              href="/download"
              className="px-6 py-2.5 rounded-full border border-zinc-600 hover:border-white text-xs font-medium text-white transition"
            >
              Descargar Agente PC
            </Link>
            <Link
              href="/onboarding"
              className="px-6 py-2.5 rounded-full border border-zinc-800 hover:border-zinc-500 text-xs font-medium text-zinc-300 hover:text-white transition"
            >
              Configurar Periférico
            </Link>
          </div>
        </div>

        <QRMobileConnect />
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Cabecera de tiempos de sesión en vivo */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 border-b border-zinc-800 pb-6 tabular-nums">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
            VUELTA ACTUAL (#{frame.completed_laps + 1})
          </div>
          <div className="text-2xl font-semibold font-mono text-white mt-1">
            {formatLapTime(frame.current_lap_ms)}
          </div>
        </div>

        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
            ÚLTIMA VUELTA
          </div>
          <div className="text-2xl font-semibold font-mono text-zinc-300 mt-1">
            {formatLapTime(frame.last_lap_ms)}
          </div>
        </div>

        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
            MEJOR VUELTA PERSONAL
          </div>
          <div className="text-2xl font-semibold font-mono text-emerald-400 mt-1">
            {formatLapTime(frame.best_lap_ms)}
          </div>
        </div>

        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
            COMBUSTIBLE RESTANTE
          </div>
          <div className="text-2xl font-semibold font-mono text-white mt-1">
            {frame.fuel.toFixed(1)} L
          </div>
        </div>
      </div>

      {liveAlert && (
        <div className="border-l-2 border-[#E10600] bg-zinc-950 px-4 py-3 flex items-center justify-between">
          <span className="text-xs font-mono text-white uppercase tracking-wider">
            {liveAlert}
          </span>
          <span className="text-[10px] font-mono text-zinc-500 uppercase">
            DIAGNÓSTICO EN VIVO 333 HZ
          </span>
        </div>
      )}

      <LiveMoTeCGauges frame={frame} />

      <LapTelemetryChart trace={trace} />

      <QRMobileConnect />
    </div>
  );
}
