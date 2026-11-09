"use client";

import React, { useState } from "react";
import { useTelemetry } from "@/lib/telemetry-store";
import {
  Check,
  Copy,
  Download,
  FileCode2,
  Lock,
  ShieldCheck,
  Terminal,
} from "lucide-react";

export default function DownloadPage() {
  const { profile, inputMode } = useTelemetry();
  const [copied, setCopied] = useState(false);

  const handleCopyToken = () => {
    navigator.clipboard.writeText(profile.agent_token);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-2">
      <div className="rounded-2xl bg-[#0F1626] border border-slate-800 p-6 sm:p-8 space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2 max-w-xl">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
              <ShieldCheck className="w-3.5 h-3.5" /> EJECUTABLE OFICIAL WINDOWS 10/11 (0 MB VRAM)
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
              Descargar Agente Local `ACC_Apex_Engineer.exe`
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Ejecuta el lector nativo a <strong>333 Hz</strong> en tu PC. Pregunta al abrir si
              juegas con <strong>Teclado, Mando o Volante</strong>, proyecta el{" "}
              <strong>Overlay HUD Click-Through</strong> sobre ACC, activa el{" "}
              <strong>Ingeniero de Voz en Español</strong> y auto-inyecta tus setups `.json` en
              tiempo real.
            </p>
          </div>

          <a
            href="/downloads/ACC_Apex_Engineer.exe"
            download="ACC_Apex_Engineer.exe"
            className="inline-flex items-center gap-2.5 px-6 py-4 rounded-xl font-bold text-sm bg-gradient-to-r from-sky-500 to-emerald-500 hover:from-sky-400 hover:to-emerald-400 text-slate-950 shadow-xl shadow-sky-500/20 transition shrink-0"
          >
            <Download className="w-5 h-5" />
            Descargar ACC_Apex_Engineer.exe
          </a>
        </div>

        {/* Token de Vinculación Personal (Supabase RLS) */}
        <div className="rounded-xl bg-slate-950 border border-slate-800 p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-sky-400 uppercase font-mono flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5" /> TU CÓDIGO DE VINCULACIÓN PRIVADO (`agent_token`)
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Modo actual: {(inputMode || "wheel").toUpperCase()}
            </span>
          </div>

          <p className="text-xs text-slate-400">
            Copia este token único y pégalo en la ventana de <code>ACC_Apex_Engineer.exe</code> para
            que tus vueltas y setups se guarden exclusivamente en tu cuenta privada de Supabase:
          </p>

          <div className="flex items-center gap-2">
            <code className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3.5 py-2.5 text-xs sm:text-sm font-mono text-emerald-300 select-all">
              {profile.agent_token}
            </code>
            <button
              onClick={handleCopyToken}
              className="px-4 py-2.5 rounded-lg text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 flex items-center gap-1.5 transition"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-emerald-400" /> Copiado
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" /> Copiar Token
                </>
              )}
            </button>
          </div>
        </div>

        {/* Garantías de Seguridad Local */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-4 space-y-1.5">
            <div className="text-xs font-bold text-white flex items-center gap-1.5">
              <FileCode2 className="w-4 h-4 text-emerald-400" />
              Alcance Estricto y Seguro en Archivos
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              El ejecutable <strong>NUNCA toca `controls.json`</strong> ni tus asignaciones de
              botones o Force Feedback. Solo lee Memoria Compartida (`Local\acpmf_*`) y escribe en{" "}
              <code>Documents\Assetto Corsa Competizione\Setups\</code>.
            </p>
          </div>

          <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-4 space-y-1.5">
            <div className="text-xs font-bold text-white flex items-center gap-1.5">
              <Terminal className="w-4 h-4 text-sky-400" />
              Ejecución desde Código Fuente (Opcional)
            </div>
            <p className="text-xs text-slate-400 leading-relaxed font-mono">
              cd apps/desktop-agent
              <br />
              .\build_exe.ps1
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
