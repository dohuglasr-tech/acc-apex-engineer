"use client";

import React, { useState } from "react";
import { useTelemetry } from "@/lib/telemetry-store";

export default function DownloadPage() {
  const { profile, inputMode } = useTelemetry();
  const [copied, setCopied] = useState(false);

  const tokenValue = profile?.agent_token || "SIGN IN TO GENERATE AGENT TOKEN";

  const handleCopyToken = () => {
    if (!profile?.agent_token) return;
    navigator.clipboard.writeText(profile.agent_token);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-12">
      <div className="flex flex-wrap items-center justify-between gap-6 border-b border-zinc-800 pb-8">
        <div className="space-y-1.5 max-w-xl">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-zinc-500">
            WINDOWS 10 / 11 X64 // NATIVE TELEMETRY DAEMON
          </div>
          <h1 className="text-xl font-semibold text-white">
            ACC_Apex_Engineer.exe
          </h1>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Agente local ligero que lee la memoria compartida de Assetto Corsa
            Competizione a 333 Hz, proyecta el HUD solo cuando estás en pista e
            inyecta los ajustes de setup en tu carpeta oficial de Setups.
          </p>
        </div>

        <a
          href="/downloads/ACC_Apex_Engineer.exe"
          download="ACC_Apex_Engineer.exe"
          className="px-7 py-2.5 rounded-full border border-zinc-500 hover:border-white text-xs font-medium text-white transition"
        >
          Download Executable (.EXE)
        </a>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
          <span>PERSONAL AGENT LINK TOKEN</span>
          <span>ACTIVE PROFILE: {(inputMode || "wheel").toUpperCase()}</span>
        </div>

        <div className="flex items-center justify-between gap-4 border border-zinc-800 bg-[#08080A] px-4 py-3">
          <code className="text-xs font-mono text-white select-all truncate">
            {tokenValue}
          </code>
          {profile?.agent_token && (
            <button
              onClick={handleCopyToken}
              className="px-4 py-1 rounded-full border border-zinc-700 hover:border-white text-[11px] font-mono text-zinc-300 hover:text-white transition shrink-0"
            >
              {copied ? "COPIED" : "COPY TOKEN"}
            </button>
          )}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-zinc-800 text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
              <th className="py-3 pr-4">SPEC.</th>
              <th className="py-3 px-4">SUBSYSTEM</th>
              <th className="py-3 pl-4">BEHAVIOR</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-900 font-mono text-zinc-400">
            <tr>
              <td className="py-4 pr-4 text-zinc-500">01</td>
              <td className="py-4 px-4 text-white font-sans font-medium">
                Shared Memory Reader
              </td>
              <td className="py-4 pl-4">
                Read-only access to Local\acpmf_physics, acpmf_graphics,
                acpmf_static at 333 Hz
              </td>
            </tr>
            <tr>
              <td className="py-4 pr-4 text-zinc-500">02</td>
              <td className="py-4 px-4 text-white font-sans font-medium">
                Setup File Scope
              </td>
              <td className="py-4 pl-4">
                Writes exclusively to Documents\Assetto Corsa
                Competizione\Setups (Never touches controls.json)
              </td>
            </tr>
            <tr>
              <td className="py-4 pr-4 text-zinc-500">03</td>
              <td className="py-4 px-4 text-white font-sans font-medium">
                Neural Pit Radio
              </td>
              <td className="py-4 pl-4">
                es-ES-AlvaroNeural voice synthesis — active only during live
                track sessions
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
