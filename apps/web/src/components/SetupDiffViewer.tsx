"use client";

import React from "react";
import { UserSetupRecord } from "@/lib/telemetry-store";
import { CheckCircle2, Download, FolderCheck, ArrowRight } from "lucide-react";

export function SetupDiffViewer({ setup }: { setup: UserSetupRecord }) {
  const handleDownloadJson = () => {
    const blob = new Blob([JSON.stringify(setup.setup_json, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = setup.file_name || "APEX_AUTO_LIVE.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="rounded-xl bg-[#0F1626] border border-slate-800 p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              v{setup.version_num} · {setup.input_mode.toUpperCase()}
            </span>
            <h3 className="text-base font-bold text-white font-mono">
              {setup.file_name}
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5 font-mono">
            <FolderCheck className="w-3.5 h-3.5 text-sky-400 shrink-0" />
            Ruta Auto-Inyectada: {setup.full_path}
          </p>
        </div>

        <button
          onClick={handleDownloadJson}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold bg-sky-500 hover:bg-sky-400 text-slate-950 transition shadow-lg shadow-sky-500/20"
        >
          <Download className="w-4 h-4" />
          Descargar .JSON para ACC
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 uppercase font-mono text-[11px]">
              <th className="py-2.5 pr-4">Área Física Medida (333 Hz)</th>
              <th className="py-2.5 px-4">Antes</th>
              <th className="py-2.5 px-4">Auto-Inyectado</th>
              <th className="py-2.5 pl-4">Diagnóstico y Razón Física</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/70">
            {setup.changes_summary.map((chg, idx) => (
              <tr key={idx} className="hover:bg-slate-900/50 transition">
                <td className="py-3 pr-4 align-top">
                  <div className="font-bold text-white flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    {chg.area}
                  </div>
                  <div className="text-[11px] font-mono text-slate-500 mt-0.5">
                    {chg.parameter}
                  </div>
                </td>
                <td className="py-3 px-4 align-top font-mono text-slate-400">
                  {chg.before}
                </td>
                <td className="py-3 px-4 align-top font-mono font-bold text-emerald-300">
                  <span className="inline-flex items-center gap-1">
                    <ArrowRight className="w-3 h-3 text-sky-400" />
                    {chg.after}
                  </span>
                </td>
                <td className="py-3 pl-4 align-top text-slate-300 leading-relaxed">
                  {chg.reason}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

