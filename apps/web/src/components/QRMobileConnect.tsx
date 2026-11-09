"use client";

import React, { useState } from "react";
import { QrCode, Smartphone, Wifi } from "lucide-react";
import { useTelemetry } from "@/lib/telemetry-store";

export function QRMobileConnect() {
  const { agentHost, setAgentHost } = useTelemetry();
  const [lanIp, setLanIp] = useState(
    agentHost === "localhost" ? "192.168.1.100" : agentHost
  );

  const mobileUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/dashboard?agent=${encodeURIComponent(lanIp)}`
      : `http://${lanIp}:3000/dashboard?agent=${lanIp}`;

  const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=160x160&bgcolor=0F1626&color=38BDF8&data=${encodeURIComponent(
    mobileUrl
  )}`;

  return (
    <div className="rounded-xl bg-[#0F1626] border border-slate-800 p-5 flex flex-col sm:flex-row items-center justify-between gap-5">
      <div className="space-y-2.5 flex-1">
        <div className="inline-flex items-center gap-1.5 text-xs font-bold text-sky-400 uppercase tracking-wider">
          <Smartphone className="w-4 h-4" />
          PANTALLA SECUNDARIA MO-TEC EN CELULAR / TABLET (0 MB VRAM)
        </div>
        <h3 className="text-base font-bold text-white">
          Escanea el QR para ver tu Telemetría a 60 FPS en el Móvil vía Wi-Fi
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          Conecta tu teléfono a la misma red Wi-Fi de tu PC para usar el celular como
          display en el volante o escritorio sin consumir recursos gráficos de tu tarjeta de video.
        </p>

        <div className="flex flex-wrap items-center gap-2 pt-1">
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5">
            <Wifi className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-xs text-slate-400">IP Local del PC:</span>
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
            className="px-3 py-1.5 rounded-lg text-xs font-bold bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/30 transition"
          >
            Vincular Stream Local
          </button>
        </div>
      </div>

      <div className="flex flex-col items-center bg-slate-950 p-3 rounded-xl border border-slate-800 shrink-0">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={qrApiUrl}
          alt="QR Mobile Dashboard"
          width={128}
          height={128}
          className="rounded-lg"
        />
        <span className="text-[10px] font-mono text-slate-400 mt-1.5 flex items-center gap-1">
          <QrCode className="w-3 h-3 text-sky-400" /> Escanea con tu cámara
        </span>
      </div>
    </div>
  );
}
