"use client";

import React from "react";
import { UserSetupRecord } from "@/lib/telemetry-store";

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
    <div className="border-t border-zinc-800 pt-6 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono uppercase tracking-[0.16em] px-2.5 py-0.5 border border-[#E10600] text-white">
              REV {setup.version_num} // {setup.input_mode.toUpperCase()}
            </span>
            <h3 className="text-sm font-semibold text-white font-mono">
              {setup.file_name}
            </h3>
            <span className="text-xs text-zinc-500 font-mono">
              {setup.car_model} @ {setup.track_name}
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 font-mono mt-1">
            TARGET PATH: {setup.full_path}
          </p>
        </div>

        <button
          onClick={handleDownloadJson}
          className="px-5 py-2 rounded-full border border-zinc-600 hover:border-white text-xs font-medium text-white transition"
        >
          Export Setup JSON
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-zinc-800 text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
              <th className="py-3 pr-4">PARAMETER AREA</th>
              <th className="py-3 px-4">PREVIOUS</th>
              <th className="py-3 px-4">INJECTED</th>
              <th className="py-3 pl-4">ENGINEERING RATIONALE</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-900">
            {setup.changes_summary.map((chg, idx) => (
              <tr key={idx} className="hover:bg-zinc-950/80 transition">
                <td className="py-4 pr-4 align-top">
                  <div className="font-medium text-white">{chg.area}</div>
                  <div className="text-[11px] font-mono text-zinc-500 mt-0.5">
                    {chg.parameter}
                  </div>
                </td>
                <td className="py-4 px-4 align-top font-mono text-zinc-400">
                  {chg.before}
                </td>
                <td className="py-4 px-4 align-top font-mono font-semibold text-white">
                  {chg.after}
                </td>
                <td className="py-4 pl-4 align-top text-zinc-400 leading-relaxed">
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
