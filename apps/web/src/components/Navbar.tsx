"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTelemetry } from "@/lib/telemetry-store";

export function Navbar() {
  const pathname = usePathname();
  const {
    isAuthenticated,
    profile,
    inputMode,
    voiceMode,
    agentConnected,
    isAccLive,
    frame,
  } = useTelemetry();

  const navItems = [
    { href: "/dashboard", label: "Telemetría" },
    { href: "/coach", label: "Diagnóstico" },
    { href: "/setups", label: "Setups" },
    { href: "/onboarding", label: "Periférico" },
    { href: "/download", label: "Agente PC" },
  ];

  const modeLabel =
    inputMode === "keyboard"
      ? "TECLADO"
      : inputMode === "gamepad"
      ? "MANDO"
      : inputMode === "wheel"
      ? "VOLANTE"
      : "SIN CONFIGURAR";

  const voiceLabel =
    voiceMode === "companion"
      ? "ACOMPAÑANTE"
      : voiceMode === "car_state"
      ? "ESTADO COCHE"
      : "SOLO TELEMETRÍA";

  return (
    <header className="sticky top-0 z-40 bg-black">
      {/* Barra superior estilo F1 Broadcast con franjas diagonales sutiles */}
      <div className="f1-header-stripes border-b border-zinc-800/80">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-10">
            <Link href="/dashboard" className="flex items-center gap-3">
              <div className="flex items-center gap-1">
                <span className="w-4 h-3.5 bg-[#E10600] -skew-x-[24deg] inline-block" />
                <span className="w-1.5 h-3.5 bg-[#E10600] -skew-x-[24deg] inline-block" />
              </div>
              <span className="text-sm font-bold tracking-[0.14em] text-white uppercase">
                APEX ENGINEER
              </span>
            </Link>

            <nav className="hidden md:flex items-center gap-7">
              {navItems.map((item) => {
                const active = pathname?.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`text-xs font-medium tracking-wide transition ${
                      active ? "text-white" : "text-zinc-400 hover:text-white"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center gap-5">
            {isAuthenticated ? (
              <div className="flex items-center gap-4">
                <span className="text-xs text-zinc-300 font-medium">
                  {profile?.discord_username || "Piloto"}
                </span>
                <form action="/auth/signout" method="post">
                  <button
                    type="submit"
                    className="text-[11px] uppercase tracking-wider text-zinc-400 hover:text-white transition"
                  >
                    Cerrar sesión
                  </button>
                </form>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                {profile && (
                  <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] font-mono text-zinc-400 border border-zinc-800 bg-zinc-900/60 px-2.5 py-1 rounded">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Viendo a: <strong className="text-zinc-200">{profile.discord_username}</strong>
                  </span>
                )}
                <Link
                  href="/login"
                  className="text-xs font-medium text-zinc-300 hover:text-white border border-zinc-700 hover:border-zinc-400 rounded-full px-4 py-1.5 transition"
                >
                  Acceso Piloto
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Sub-barra de estado de sesión y pestañas con subrayado rojo #E10600 */}
      <div className="bg-[#0B0B0F] border-b border-zinc-800/90">
        <div className="max-w-6xl mx-auto px-6 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4">
            <div>
              <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-zinc-500">
                {isAccLive
                  ? `TELEMETRÍA EN VIVO // ${frame?.car_model.replace(/_/g, " ")}`
                  : "ESTADO DE SESIÓN // EN ESPERA"}
              </div>
              <div className="text-sm font-semibold text-white mt-0.5 flex items-center gap-2">
                <span>
                  {isAccLive && frame
                    ? frame.track_name.toUpperCase()
                    : "Esperando sesión activa en Assetto Corsa Competizione"}
                </span>
                <span className="text-zinc-600">›</span>
              </div>
            </div>

            {/* Bloque derecho estilo cronometraje oficial */}
            <div className="flex items-center gap-6 text-right font-mono">
              <div className="border-r border-zinc-800 pr-6">
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider">
                  PERIFÉRICO
                </div>
                <div className="text-xs text-white font-semibold mt-0.5">
                  {modeLabel}
                </div>
              </div>

              <div className="border-r border-zinc-800 pr-6 hidden sm:block">
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider">
                  RADIO IA
                </div>
                <div className="text-xs text-[#E10600] font-semibold mt-0.5">
                  {voiceLabel}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-end gap-1.5 text-[10px] uppercase tracking-wider text-zinc-400">
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      isAccLive
                        ? "bg-emerald-500"
                        : agentConnected
                        ? "bg-amber-500"
                        : "bg-[#E10600]"
                    }`}
                  />
                  <span>AGENTE LOCAL</span>
                  <span className="text-white font-semibold ml-1">
                    {isAccLive
                      ? "ACTIVO 333 HZ"
                      : agentConnected
                      ? "EN ESPERA"
                      : "DESCONECTADO"}
                  </span>
                </div>
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider mt-0.5">
                  MEMORIA COMPARTIDA{" "}
                  <span className="text-zinc-300 ml-1">
                    {isAccLive ? "RECIBIENDO DATOS" : "SIN SEÑAL"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Pestañas inferiores con indicador rojo #E10600 */}
          <div className="flex items-center gap-8 overflow-x-auto">
            {navItems.map((item) => {
              const active = pathname?.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`pb-3 text-[11px] font-semibold uppercase tracking-[0.14em] border-b-2 transition whitespace-nowrap ${
                    active
                      ? "border-[#E10600] text-white"
                      : "border-transparent text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </header>
  );
}
