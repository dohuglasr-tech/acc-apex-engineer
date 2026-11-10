"use client";

import React from "react";
import Link from "next/link";
import { InputMode, VoiceMode, useTelemetry } from "@/lib/telemetry-store";
import { LiveMoTeCGauges } from "@/components/LiveMoTeCGauges";
import { LocalAIEngineerLiveRadar } from "@/components/LocalAIEngineerLiveRadar";
import { LapTelemetryChart } from "@/components/LapTelemetryChart";
import { QRMobileConnect } from "@/components/QRMobileConnect";

function formatLapTime(ms: number): string {
  if (!ms || ms <= 0) return "--:--.---";
  const min = Math.floor(ms / 60000);
  const sec = ((ms % 60000) / 1000).toFixed(3);
  return `${min}:${Number(sec) < 10 ? "0" : ""}${sec}`;
}

export default function DashboardPage() {
  const {
    frame,
    trace,
    isAccLive,
    agentConnected,
    liveAlert,
    inputMode,
    setInputMode,
    voiceMode,
    setVoiceMode,
    drivingStyle,
    setDrivingStyle,
    profile,
    setups,
    drivingErrors,
  } = useTelemetry();

  const modeLabel =
    inputMode === "keyboard"
      ? "TECLADO"
      : inputMode === "gamepad"
      ? "MANDO / CONTROLADOR"
      : "VOLANTE Y PEDALES";

  const voiceModeLabel =
    voiceMode === "companion"
      ? "ACOMPAÑANTE"
      : voiceMode === "car_state"
      ? "ESTADO DEL COCHE"
      : "SOLO TELEMETRÍA";

  const styleLabel =
    drivingStyle === "aggressive"
      ? "AGRESIVO"
      : drivingStyle === "beginner"
      ? "PRINCIPIANTE"
      : "SEGURO / CONSISTENTE";

  if (!isAccLive || !frame) {
    return (
      <div className="space-y-10">
        {/* Encabezado de la Guía Paso a Paso */}
        <div className="border-b border-zinc-800 pb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-[#E10600]">
              GUÍA DE ACTIVACIÓN PASO A PASO // FLUJO DIRECTO
            </div>
            <h1 className="text-xl font-semibold text-white mt-1">
              Cómo activar la Telemetría y Auto-Inyección en Assetto Corsa Competizione
            </h1>
            <p className="text-xs text-zinc-400 mt-1">
              Sigue estos 4 pasos en orden. Los indicadores cambian a verde automáticamente en cuanto cada paso se detecta activo.
            </p>
          </div>

          <a
            href="/downloads/ACC_Apex_Engineer.exe"
            download="ACC_Apex_Engineer.exe"
            className="px-6 py-2.5 rounded-full bg-[#E10600] hover:bg-[#b80500] text-xs font-semibold text-white tracking-wide transition"
          >
            Descargar ACC_Apex_Engineer.exe
          </a>
        </div>

        {/* Tabla/Lista de Pasos 1 -> 2 -> 3 -> 4 estilo F1 Standings */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-zinc-800 text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
                <th className="py-3 pr-4">PASO</th>
                <th className="py-3 px-4">INSTRUCCIÓN PARA EL PILOTO</th>
                <th className="py-3 px-4">ACCIÓN RÁPIDA</th>
                <th className="py-3 pl-4 text-right">ESTADO ACTUAL</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-900 text-xs">
              {/* PASO 1 */}
              <tr className="hover:bg-zinc-950/60 transition">
                <td className="py-5 pr-4 font-mono text-zinc-400 align-top">
                  PASO 01
                </td>
                <td className="py-5 px-4 align-top max-w-md">
                  <div className="font-semibold text-white text-sm">
                    1. Selecciona tu Periférico de Conducción
                  </div>
                  <p className="text-zinc-400 mt-1 leading-relaxed">
                    Elige con qué conduces para que el agente adapte el reparto de frenada, el Steer Ratio, el control de tracción y las alturas del setup a tu mando, teclado o volante.
                  </p>
                </td>
                <td className="py-5 px-4 align-top">
                  <div className="flex flex-wrap items-center gap-2">
                    {(
                      [
                        { id: "keyboard", label: "Teclado" },
                        { id: "gamepad", label: "Mando" },
                        { id: "wheel", label: "Volante" },
                      ] as { id: InputMode; label: string }[]
                    ).map((m) => {
                      const active = (inputMode || "gamepad") === m.id;
                      return (
                        <button
                          key={m.id}
                          onClick={() => setInputMode(m.id)}
                          className={`px-3.5 py-1.5 rounded-full text-xs font-medium border transition ${
                            active
                              ? "border-[#E10600] bg-[#E10600]/15 text-white"
                              : "border-zinc-800 text-zinc-400 hover:border-zinc-600 hover:text-white"
                          }`}
                        >
                          {m.label}
                        </button>
                      );
                    })}
                  </div>
                </td>
                <td className="py-5 pl-4 text-right font-mono align-top">
                  <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/40 text-emerald-400 text-[10px] uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    COMPLETADO ({modeLabel})
                  </span>
                </td>
              </tr>

              {/* PASO 01-B: COMPORTAMIENTO DEL INGENIERO POR VOZ */}
              <tr className="hover:bg-zinc-950/60 transition">
                <td className="py-5 pr-4 font-mono text-zinc-400 align-top">
                  RADIO IA
                </td>
                <td className="py-5 px-4 align-top max-w-md">
                  <div className="font-semibold text-white text-sm">
                    Comportamiento del Ingeniero por Voz (Álvaro)
                  </div>
                  <p className="text-zinc-400 mt-1 leading-relaxed">
                    Elige cómo interactúa el copiloto contigo por radio en tiempo real:
                    <br />
                    • <strong className="text-white">Acompañante:</strong> anticipa curvas, frenadas, motivación y telemetría.
                    <br />
                    • <strong className="text-white">Solo estado del coche:</strong> silencio en curvas, te alerta de presiones fuera de rango, frenos calientes y gasolina.
                    <br />
                    • <strong className="text-white">Solo telemetría:</strong> métricas puras, anuncia tiempos al cruzar meta sin comentarios.
                  </p>
                </td>
                <td className="py-5 px-4 align-top">
                  <div className="flex flex-wrap items-center gap-2">
                    {(
                      [
                        { id: "companion", label: "Acompañante" },
                        { id: "car_state", label: "Solo estado del coche" },
                        { id: "telemetry", label: "Solo telemetría" },
                      ] as { id: VoiceMode; label: string }[]
                    ).map((vm) => {
                      const active = (voiceMode || "companion") === vm.id;
                      return (
                        <button
                          key={vm.id}
                          onClick={() => setVoiceMode(vm.id)}
                          className={`px-3.5 py-1.5 rounded-full text-xs font-medium border transition ${
                            active
                              ? "border-[#E10600] bg-[#E10600]/15 text-white font-bold"
                              : "border-zinc-800 text-zinc-400 hover:border-zinc-600 hover:text-white"
                          }`}
                        >
                          {vm.label}
                        </button>
                      );
                    })}
                  </div>
                </td>
                <td className="py-5 pl-4 text-right font-mono align-top">
                  <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/40 text-emerald-400 text-[10px] uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    {voiceModeLabel}
                  </span>
                </td>
              </tr>

              {/* PASO 01-C: ESTILO Y TIPO DE CONDUCCIÓN */}
              <tr className="hover:bg-zinc-950/60 transition">
                <td className="py-5 pr-4 font-mono text-zinc-400 align-top">
                  ESTILO
                </td>
                <td className="py-5 px-4 align-top max-w-md">
                  <div className="font-semibold text-white text-sm">
                    Estilo de Conducción para el Setup Completo
                  </div>
                  <p className="text-zinc-400 mt-1 leading-relaxed">
                    El agente ajustará el coche entero (Aerodinámica, Amortiguadores, Barras, Diferencial, Electrónica y Frenos) basándose en tu estilo:
                    <br />
                    • <strong className="text-white">Agresivo:</strong> frenadas tardías (late-braking), rotación libre con menor precarga diferencial, alerón de velocidad punta y pastillas Sprint.
                    <br />
                    • <strong className="text-white">Seguro / Consistente:</strong> mayor carga aerodinámica, diferencial 60-80 Nm, frenada neutra y lineal, desgaste regular de neumáticos.
                    <br />
                    • <strong className="text-white">Principiante:</strong> subviraje preventivo ("safe understeer"), barras delanteras rígidas, ABS 5-6, TC 5-6 y altura delantera elevada para evitar trompos.
                  </p>
                </td>
                <td className="py-5 px-4 align-top">
                  <div className="flex flex-wrap items-center gap-2">
                    {(
                      [
                        { id: "aggressive", label: "Agresivo" },
                        { id: "safe", label: "Seguro / Consistente" },
                        { id: "beginner", label: "Principiante" },
                      ] as { id: typeof drivingStyle; label: string }[]
                    ).map((st) => {
                      const active = (drivingStyle || "safe") === st.id;
                      return (
                        <button
                          key={st.id}
                          onClick={() => setDrivingStyle(st.id)}
                          className={`px-3.5 py-1.5 rounded-full text-xs font-medium border transition ${
                            active
                              ? "border-[#E10600] bg-[#E10600]/15 text-white font-bold"
                              : "border-zinc-800 text-zinc-400 hover:border-zinc-600 hover:text-white"
                          }`}
                        >
                          {st.label}
                        </button>
                      );
                    })}
                  </div>
                </td>
                <td className="py-5 pl-4 text-right font-mono align-top">
                  <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/40 text-emerald-400 text-[10px] uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    {styleLabel}
                  </span>
                </td>
              </tr>

              {/* PASO 2 */}
              <tr className="hover:bg-zinc-950/60 transition">
                <td className="py-5 pr-4 font-mono text-zinc-400 align-top">
                  PASO 02
                </td>
                <td className="py-5 px-4 align-top max-w-md">
                  <div className="font-semibold text-white text-sm">
                    2. Abre el programa ACC_Apex_Engineer.exe en tu PC
                  </div>
                  <p className="text-zinc-400 mt-1 leading-relaxed">
                    Descarga y abre <code className="text-white font-mono">ACC_Apex_Engineer.exe</code>. Ya incluye tu cuenta (<span className="text-white">{profile?.discord_username || "dgvla"}</span>) pre-vinculada automáticamente.{" "}
                    <strong className="text-white">Importante:</strong> Déjalo abierto en segundo plano mientras juegas.
                  </p>
                </td>
                <td className="py-5 px-4 align-top">
                  <a
                    href="/downloads/ACC_Apex_Engineer.exe"
                    download="ACC_Apex_Engineer.exe"
                    className="inline-block px-4 py-1.5 rounded-full border border-zinc-600 hover:border-white text-xs font-medium text-white transition"
                  >
                    Descargar .EXE
                  </a>
                </td>
                <td className="py-5 pl-4 text-right font-mono align-top">
                  {agentConnected ? (
                    <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/40 text-emerald-400 text-[10px] uppercase tracking-wider">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      CONECTADO EN TU PC
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#E10600] text-white text-[10px] uppercase tracking-wider">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#E10600] animate-pulse" />
                      PENDIENTE — ABRE EL .EXE
                    </span>
                  )}
                </td>
              </tr>

              {/* PASO 3 */}
              <tr className="hover:bg-zinc-950/60 transition">
                <td className="py-5 pr-4 font-mono text-zinc-400 align-top">
                  PASO 03
                </td>
                <td className="py-5 px-4 align-top max-w-md">
                  <div className="font-semibold text-white text-sm">
                    3. Abre Assetto Corsa Competizione y pulsa CONDUCIR (DRIVE)
                  </div>
                  <p className="text-zinc-400 mt-1 leading-relaxed">
                    Inicia cualquier sesión en ACC (Práctica, Hotlap o Carrera) y entra a la pista. En el instante en que tu coche esté en pista, esta pantalla mostrará automáticamente las revoluciones, presiones Pirelli DHE y temperaturas en tiempo real.
                  </p>
                </td>
                <td className="py-5 px-4 align-top font-mono text-[11px] text-zinc-400">
                  Lectura automática a 333 Hz
                </td>
                <td className="py-5 pl-4 text-right font-mono align-top">
                  <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-zinc-700 text-zinc-400 text-[10px] uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                    ESPERANDO QUE ENTRES A PISTA
                  </span>
                </td>
              </tr>

              {/* PASO 4 */}
              <tr className="hover:bg-zinc-950/60 transition">
                <td className="py-5 pr-4 font-mono text-zinc-400 align-top">
                  PASO 04
                </td>
                <td className="py-5 px-4 align-top max-w-md">
                  <div className="font-semibold text-white text-sm">
                    4. Completa 1 vuelta para recibir tu Setup Auto-Inyectado
                  </div>
                  <p className="text-zinc-400 mt-1 leading-relaxed">
                    Al cruzar la línea de meta, el ingeniero de pista te hablará por radio y guardará automáticamente el setup optimizado{" "}
                    <code className="text-white font-mono">APEX_AUTO_LIVE.json</code> dentro de la carpeta oficial de tu juego (<code className="text-zinc-300 font-mono">Documentos\Assetto Corsa Competizione\Setups</code>).
                  </p>
                </td>
                <td className="py-5 px-4 align-top">
                  <div className="flex items-center gap-2">
                    <Link
                      href="/coach"
                      className="px-3.5 py-1.5 rounded-full border border-zinc-800 hover:border-zinc-500 text-xs text-zinc-300 hover:text-white transition"
                    >
                      Ver Diagnósticos ({drivingErrors.length})
                    </Link>
                    <Link
                      href="/setups"
                      className="px-3.5 py-1.5 rounded-full border border-zinc-800 hover:border-zinc-500 text-xs text-zinc-300 hover:text-white transition"
                    >
                      Ver Setups ({setups.length})
                    </Link>
                  </div>
                </td>
                <td className="py-5 pl-4 text-right font-mono align-top">
                  <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-zinc-800 text-zinc-500 text-[10px] uppercase tracking-wider">
                    LISTO PARA AUTO-INYECTAR
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Si ya hay una vuelta o traza previa guardada en la sesión del usuario, mostrar resumen debajo */}
        {trace && trace.length > 0 && (
          <div className="pt-4">
            <LapTelemetryChart trace={trace} />
          </div>
        )}

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

      {/* Ingeniero de Carrera IA Local - Radar de Curva y Transmisión de Radio */}
      <LocalAIEngineerLiveRadar />

      <LiveMoTeCGauges frame={frame} />

      <LapTelemetryChart trace={trace} />

      <QRMobileConnect />
    </div>
  );
}
