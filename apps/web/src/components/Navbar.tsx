"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTelemetry } from "@/lib/telemetry-store";
import {
  Activity,
  Cpu,
  Download,
  Gamepad2,
  Gauge,
  Keyboard,
  LogIn,
  ShieldCheck,
  Sliders,
  Sparkles,
} from "lucide-react";

export function Navbar() {
  const pathname = usePathname();
  const { profile, inputMode, agentConnected } = useTelemetry();

  const modeBadge =
    inputMode === "keyboard" ? (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
        <Keyboard className="w-3.5 h-3.5" /> TECLADO
      </span>
    ) : inputMode === "gamepad" ? (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-500/15 text-purple-300 border border-purple-500/30">
        <Gamepad2 className="w-3.5 h-3.5" /> MANDO
      </span>
    ) : inputMode === "wheel" ? (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-sky-500/15 text-sky-300 border border-sky-500/30">
        <Gauge className="w-3.5 h-3.5" /> VOLANTE
      </span>
    ) : (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
        SELECCIONAR PERIFÉRICO
      </span>
    );

  const navItems = [
    { href: "/dashboard", label: "MoTeC En Vivo", icon: Activity },
    { href: "/coach", label: "Errores y Soluciones", icon: Sparkles },
    { href: "/setups", label: "Auto-Setups (.json)", icon: Sliders },
    { href: "/onboarding", label: "Periférico", icon: Gamepad2 },
    { href: "/download", label: "Agente .EXE", icon: Download },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-[#070A12]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-sky-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <Cpu className="w-5 h-5 text-slate-950" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-wider text-white flex items-center gap-2">
                ACC APEX ENGINEER{" "}
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                  333 Hz PRO
                </span>
              </div>
              <div className="text-[11px] text-slate-400 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                Cuenta Privada RLS · Nunca toca controls.json
              </div>
            </div>
          </Link>
        </div>

        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`px-3 py-2 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
                  active
                    ? "bg-sky-500/15 text-sky-300 border border-sky-500/30"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2.5">
          <Link href="/onboarding" title="Cambiar periférico de entrada">
            {modeBadge}
          </Link>

          <div
            className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border ${
              agentConnected
                ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                : "bg-slate-800/80 text-slate-300 border-slate-700"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                agentConnected
                  ? "bg-emerald-400 animate-ping"
                  : "bg-sky-400 animate-pulse"
              }`}
            />
            {agentConnected ? ".EXE 333Hz Conectado" : "Stream 60 FPS Activo"}
          </div>

          <Link
            href="/login"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#5865F2]/20 hover:bg-[#5865F2]/30 text-[#99AAB5] hover:text-white border border-[#5865F2]/40 transition"
          >
            <LogIn className="w-3.5 h-3.5 text-[#5865F2]" />
            <span className="max-w-[110px] truncate">{profile.discord_username}</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
