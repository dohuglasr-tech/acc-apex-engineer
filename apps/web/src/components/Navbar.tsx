"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTelemetry } from "@/lib/telemetry-store";

export function Navbar() {
  const pathname = usePathname();
  const { profile, inputMode, agentConnected, isAccLive, frame } =
    useTelemetry();

  const navItems = [
    { href: "/dashboard", label: "Telemetry" },
    { href: "/coach", label: "Diagnostics" },
    { href: "/setups", label: "Setups" },
    { href: "/onboarding", label: "Hardware" },
    { href: "/download", label: "Desktop Agent" },
  ];

  const modeLabel =
    inputMode === "keyboard"
      ? "KEYBOARD"
      : inputMode === "gamepad"
      ? "CONTROLLER"
      : inputMode === "wheel"
      ? "WHEEL"
      : "UNCONFIGURED";

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
            {profile ? (
              <div className="flex items-center gap-4">
                <span className="text-xs text-zinc-300 font-medium">
                  {profile.discord_username}
                </span>
                <form action="/auth/signout" method="post">
                  <button
                    type="submit"
                    className="text-[11px] uppercase tracking-wider text-zinc-400 hover:text-white transition"
                  >
                    Sign Out
                  </button>
                </form>
              </div>
            ) : (
              <Link
                href="/login"
                className="text-xs font-medium text-zinc-300 hover:text-white border border-zinc-700 hover:border-zinc-400 rounded-full px-4 py-1.5 transition"
              >
                Sign In
              </Link>
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
                  ? `LIVE TELEMETRY // ${frame?.car_model.replace(/_/g, " ")}`
                  : "SESSION STATUS // STANDBY"}
              </div>
              <div className="text-sm font-semibold text-white mt-0.5 flex items-center gap-2">
                <span>
                  {isAccLive && frame
                    ? frame.track_name.toUpperCase()
                    : "Waiting for Assetto Corsa Competizione"}
                </span>
                <span className="text-zinc-600">›</span>
              </div>
            </div>

            {/* Bloque derecho estilo cronometraje oficial */}
            <div className="flex items-center gap-6 text-right font-mono">
              <div className="border-r border-zinc-800 pr-6">
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider">
                  INPUT PROFILE
                </div>
                <div className="text-xs text-white font-semibold mt-0.5">
                  {modeLabel}
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
                  <span>AGENT LINK</span>
                  <span className="text-white font-semibold ml-1">
                    {isAccLive
                      ? "333 HZ ACTIVE"
                      : agentConnected
                      ? "STANDBY"
                      : "OFFLINE"}
                  </span>
                </div>
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider mt-0.5">
                  SHARED MEMORY{" "}
                  <span className="text-zinc-300 ml-1">
                    {isAccLive ? "STREAMING" : "NO SIGNAL"}
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
