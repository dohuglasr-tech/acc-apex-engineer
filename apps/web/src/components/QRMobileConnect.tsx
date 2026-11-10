"use client";

import React, { useState } from "react";
import { useTelemetry } from "@/lib/telemetry-store";

export function QRMobileConnect() {
  const { agentHost, setAgentHost } = useTelemetry();
  const [lanIp, setLanIp] = useState(
    agentHost === "localhost" ? "192.168.1.9" : agentHost
  );

  const mobileUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/dashboard?agent=${encodeURIComponent(lanIp)}`
      : `http://${lanIp}:3000/dashboard?agent=${lanIp}`;

  const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=140x140&bgcolor=000000&color=FFFFFF&data=${encodeURIComponent(
    mobileUrl
  )}`;

  return (
    <div className="border-t border-zinc-800/90 pt-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
      <div className="space-y-2 max-w-xl">
        <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-zinc-500">
          SECOND SCREEN TELEMETRY // ZERO VRAM OVERHEAD
        </div>
        <h3 className="text-sm font-semibold text-white">
          Mobile Pit Wall Display (Wi-Fi Local Stream)
        </h3>
        <p className="text-xs text-zinc-400 leading-relaxed">
          Conecta un teléfono o tablet en la misma red local para visualizar los
          parámetros de pista a 60 FPS directamente desde el agente local.
        </p>

        <div className="flex flex-wrap items-center gap-3 pt-2">
          <div className="flex items-center gap-2 border border-zinc-800 bg-zinc-950 px-3 py-1.5">
            <span className="text-[10px] font-mono uppercase text-zinc-500">
              HOST IP
            </span>
            <input
              type="text"
              value={lanIp}
              onChange={(e) => setLanIp(e.target.value)}
              className="bg-transparent text-xs font-mono text-white focus:outline-none w-28"
              placeholder="192.168.1.X"
            />
          </div>
          <button
            onClick={() => setAgentHost(lanIp)}
            className="px-4 py-1.5 rounded-full border border-zinc-700 hover:border-white text-xs font-medium text-white transition"
          >
            Connect Host
          </button>
        </div>
      </div>

      <div className="p-2 border border-zinc-800 bg-black shrink-0">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={qrApiUrl}
          alt="Mobile Telemetry QR"
          width={108}
          height={108}
        />
      </div>
    </div>
  );
}
