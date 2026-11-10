"use client";

import React, { useState } from "react";
import { ActiveAccSetup, TelemetryFrame, useTelemetry } from "@/lib/telemetry-store";

type AccTab =
  | "neumaticos"
  | "electronica"
  | "combustible"
  | "mecanico"
  | "amortiguadores"
  | "aerodinamica";

function AccBox({
  title,
  children,
  className = "",
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`border border-zinc-500/70 bg-[#0D0D11]/95 shadow-lg ${className}`}
    >
      {title && (
        <div className="bg-black py-2 px-3 text-center text-[11px] font-semibold uppercase tracking-[0.12em] text-white border-b border-zinc-800">
          {title}
        </div>
      )}
      <div className="p-3.5 space-y-2.5">{children}</div>
    </div>
  );
}

function AccBarRow({
  label,
  valueText,
  fillPct,
  liveHighlight = false,
}: {
  label: string;
  valueText: string;
  fillPct: number;
  liveHighlight?: boolean;
}) {
  const clamped = Math.max(4, Math.min(100, fillPct));
  return (
    <div
      className={`flex items-center justify-between gap-3 py-0.5 px-1.5 ${
        liveHighlight ? "bg-[#E10600]/20 border-l-2 border-[#E10600]" : ""
      }`}
    >
      <span className="text-xs text-zinc-200 truncate">{label}</span>
      <div className="flex items-center gap-1.5 shrink-0">
        <span className="text-zinc-300 font-mono text-xs select-none">&lt;</span>
        <div className="w-28 sm:w-32 h-5 bg-zinc-900/90 relative overflow-hidden flex items-center justify-center border border-zinc-800">
          <div
            className="absolute left-0 top-0 bottom-0 bg-[#D90400] transition-all duration-150"
            style={{ width: `${clamped}%` }}
          />
          <span className="relative z-10 text-xs font-bold text-white font-mono drop-shadow">
            {valueText}
          </span>
        </div>
        <span className="text-zinc-300 font-mono text-xs select-none">&gt;</span>
      </div>
    </div>
  );
}

function AccReadingBox({
  mirror = false,
  imo,
  wear,
  hotPsi,
  padMm,
  discMm,
}: {
  mirror?: boolean;
  imo: [number, number, number];
  wear: number;
  hotPsi: number;
  padMm: number;
  discMm: number;
}) {
  const labels = mirror ? "I M O" : "O M I";
  const temps = mirror
    ? [imo[0], imo[1], imo[2]]
    : [imo[2], imo[1], imo[0]];
  const psiOptimal = hotPsi >= 26.65 && hotPsi <= 27.0;

  return (
    <div className="bg-[#16161B]/95 border border-zinc-800 p-3 space-y-2 text-xs">
      <div className="text-center text-[10px] font-semibold uppercase tracking-[0.12em] text-zinc-300 pb-1 border-b border-zinc-800">
        ÚLTIMAS LECTURAS
      </div>

      <div className="flex items-center justify-between border-b border-zinc-800/80 pb-1.5">
        <span className="text-zinc-300 font-mono text-[11px]">{labels}</span>
        <span className="font-mono font-bold text-white tracking-wider">
          {Math.round(temps[0])}&nbsp;&nbsp;{Math.round(temps[1])}&nbsp;&nbsp;
          {Math.round(temps[2])}
        </span>
      </div>

      <div className="flex items-center justify-between border-b border-zinc-800/80 pb-1.5">
        <span className="text-zinc-300 text-[11px]">desgaste</span>
        <span className="font-mono font-bold text-white">
          {wear.toFixed(1)}&nbsp;&nbsp;{wear.toFixed(1)}&nbsp;&nbsp;{wear.toFixed(1)}
        </span>
      </div>

      <div className="flex items-center justify-between border-b border-zinc-800/80 pb-1.5">
        <span className="text-zinc-300 text-[11px]">Psi en caliente</span>
        <span
          className={`font-mono font-bold ${
            psiOptimal ? "text-emerald-400" : "text-white"
          }`}
        >
          {hotPsi.toFixed(1)}
        </span>
      </div>

      <div className="flex items-center justify-between border-b border-zinc-800/80 pb-1.5">
        <span className="text-zinc-300 text-[11px]">desgaste de pastillas</span>
        <span className="font-mono font-bold text-white">{padMm.toFixed(2)}</span>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-zinc-300 text-[11px]">desgaste del disco</span>
        <span className="font-mono font-bold text-white">{discMm.toFixed(2)}</span>
      </div>
    </div>
  );
}

function TopDownGt3Car({
  carModel,
  showShockGauges = false,
  suspensionTravel = [0, 0, 0, 0],
}: {
  carModel: string;
  showShockGauges?: boolean;
  suspensionTravel?: [number, number, number, number];
}) {
  const renderShock = (travel: number, side: "left" | "right") => {
    const pct = Math.max(10, Math.min(90, Math.round((travel || 0.04) * 1000)));
    return (
      <div
        className={`flex items-center gap-1 ${
          side === "right" ? "flex-row-reverse" : ""
        }`}
      >
        <div className="w-3 h-20 bg-zinc-900 border border-zinc-600 relative flex flex-col justify-between p-0.5">
          <div className="w-full h-2 bg-zinc-300" />
          <div
            className="w-full bg-[#E10600] transition-all duration-75"
            style={{ height: `${pct}%` }}
          />
        </div>
        <div className="flex flex-col justify-between h-20 w-7">
          <div className="h-[1px] bg-[#E10600] w-full" />
          <div className="h-[1px] bg-zinc-500 w-full" />
          <div className="h-[1px] bg-amber-400 w-full" />
          <div className="h-[1px] bg-zinc-500 w-full" />
          <div className="h-[1px] bg-emerald-400 w-full" />
        </div>
      </div>
    );
  };

  return (
    <div className="relative flex items-center justify-center py-2 select-none">
      {showShockGauges && (
        <div className="flex flex-col justify-between h-[330px] mr-3">
          {renderShock(suspensionTravel[0], "left")}
          {renderShock(suspensionTravel[2], "left")}
        </div>
      )}

      {/* Silueta Cenital GT3 estilo ACC */}
      <svg
        viewBox="0 0 220 420"
        className="w-44 sm:w-52 h-auto drop-shadow-[0_12px_28px_rgba(0,0,0,0.9)]"
      >
        <defs>
          <linearGradient id="gt3Body" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#26262B" />
            <stop offset="50%" stopColor="#52525B" />
            <stop offset="100%" stopColor="#26262B" />
          </linearGradient>
          <linearGradient id="gt3Glass" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#18181B" />
            <stop offset="100%" stopColor="#27272A" />
          </linearGradient>
        </defs>

        {/* Splitter frontal */}
        <path
          d="M 45 35 Q 110 12 175 35 L 182 55 L 38 55 Z"
          fill="#18181B"
          stroke="#3F3F46"
          strokeWidth="1.5"
        />

        {/* Ruedas (4) */}
        <rect x="20" y="68" width="18" height="58" rx="4" fill="#09090B" stroke="#EAB308" strokeWidth="1" />
        <rect x="182" y="68" width="18" height="58" rx="4" fill="#09090B" stroke="#EAB308" strokeWidth="1" />
        <rect x="18" y="285" width="20" height="62" rx="4" fill="#09090B" stroke="#EAB308" strokeWidth="1" />
        <rect x="182" y="285" width="20" height="62" rx="4" fill="#09090B" stroke="#EAB308" strokeWidth="1" />

        {/* Carrocería principal GT3 */}
        <path
          d="M 42 45 Q 110 18 178 45 L 190 95 L 184 165 L 188 265 L 188 355 Q 110 375 32 355 L 32 265 L 36 165 L 30 95 Z"
          fill="url(#gt3Body)"
          stroke="#71717A"
          strokeWidth="1.5"
        />

        {/* Tomas de aire del capó */}
        <path d="M 75 62 L 145 62 L 135 98 L 85 98 Z" fill="#141417" stroke="#3F3F46" strokeWidth="1" />

        {/* Parabrisas y cabina */}
        <path
          d="M 52 135 Q 110 115 168 135 L 156 205 Q 110 215 64 205 Z"
          fill="url(#gt3Glass)"
          stroke="#52525B"
          strokeWidth="1.5"
        />

        {/* Banda superior del parabrisas */}
        <path
          d="M 56 136 Q 110 119 164 136 L 160 148 Q 110 134 60 148 Z"
          fill="#27272A"
        />
        <text
          x="110"
          y="141"
          textAnchor="middle"
          fill="#E4E4E7"
          fontSize="8.5"
          fontWeight="bold"
          fontFamily="monospace"
        >
          {carModel.split("_")[0].toUpperCase()}
        </text>

        {/* Cubierta motor trasera */}
        <path
          d="M 72 230 L 148 230 L 140 335 L 80 335 Z"
          fill="#1F1F24"
          stroke="#3F3F46"
          strokeWidth="1"
        />

        {/* Soportes y Alerón Trasero GT3 */}
        <rect x="78" y="345" width="4" height="38" fill="#18181B" />
        <rect x="138" y="345" width="4" height="38" fill="#18181B" />
        <rect
          x="24"
          y="375"
          width="172"
          height="24"
          rx="2"
          fill="#71717A"
          stroke="#D4D4D8"
          strokeWidth="1"
        />
      </svg>

      {showShockGauges && (
        <div className="flex flex-col justify-between h-[330px] ml-3">
          {renderShock(suspensionTravel[1], "right")}
          {renderShock(suspensionTravel[3], "right")}
        </div>
      )}
    </div>
  );
}

function SideAeroGt3Car({
  withCfdStreamlines = false,
  frontRh,
  rearRh,
}: {
  withCfdStreamlines?: boolean;
  frontRh: number;
  rearRh: number;
}) {
  return (
    <div className="relative w-full max-w-3xl mx-auto pt-4 pb-2 select-none">
      <svg viewBox="0 0 800 250" className="w-full h-auto">
        <defs>
          <linearGradient id="cfdTop" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#2563EB" stopOpacity="0.2" />
            <stop offset="25%" stopColor="#10B981" stopOpacity="0.85" />
            <stop offset="55%" stopColor="#FACC15" stopOpacity="0.95" />
            <stop offset="85%" stopColor="#E10600" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#E10600" stopOpacity="0.4" />
          </linearGradient>
          <linearGradient id="cfdBottom" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.3" />
            <stop offset="35%" stopColor="#22C55E" stopOpacity="0.9" />
            <stop offset="75%" stopColor="#F59E0B" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#EF4444" stopOpacity="0.85" />
          </linearGradient>
          <linearGradient id="sideBody" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#52525B" />
            <stop offset="60%" stopColor="#27272A" />
            <stop offset="100%" stopColor="#09090B" />
          </linearGradient>
        </defs>

        {/* Silueta lateral GT3 */}
        <g>
          {/* Alerón trasero */}
          <path d="M 125 90 L 165 90 L 175 130 L 155 130 Z" fill="#18181B" stroke="#52525B" />
          <rect x="105" y="82" width="68" height="10" rx="2" fill="#3F3F46" stroke="#A1A1AA" />

          {/* Cuerpo principal */}
          <path
            d="M 120 185 L 125 130 L 245 120 L 345 86 Q 430 82 510 118 L 655 142 L 690 175 L 698 195 L 110 195 Z"
            fill="url(#sideBody)"
            stroke="#71717A"
            strokeWidth="2"
          />

          {/* Ventanilla lateral */}
          <path
            d="M 350 94 Q 425 90 495 120 L 485 132 L 335 130 Z"
            fill="#18181B"
            stroke="#52525B"
            strokeWidth="1.5"
          />

          {/* Rueda Trasera */}
          <circle cx="235" cy="182" r="42" fill="#09090B" stroke="#EAB308" strokeWidth="2" />
          <circle cx="235" cy="182" r="26" fill="#18181B" stroke="#52525B" strokeWidth="2" />

          {/* Rueda Delantera */}
          <circle cx="565" cy="182" r="42" fill="#09090B" stroke="#EAB308" strokeWidth="2" />
          <circle cx="565" cy="182" r="26" fill="#18181B" stroke="#52525B" strokeWidth="2" />
        </g>

        {/* Líneas de flujo aerodinámico CFD estilo ACC (Captura 1) */}
        {withCfdStreamlines && (
          <g fill="none" strokeLinecap="round">
            <path
              d="M 55 55 Q 200 95 360 72 Q 520 55 685 155"
              stroke="url(#cfdTop)"
              strokeWidth="8"
            />
            <path
              d="M 45 105 Q 220 115 390 88 Q 545 88 695 168"
              stroke="url(#cfdTop)"
              strokeWidth="7"
            />
            <path
              d="M 65 145 Q 260 125 460 148 Q 610 165 705 182"
              stroke="url(#cfdTop)"
              strokeWidth="6"
            />
            <path
              d="M 75 180 Q 150 212 390 206 L 705 204"
              stroke="url(#cfdBottom)"
              strokeWidth="8"
            />
          </g>
        )}
      </svg>

      {withCfdStreamlines && (
        <div className="text-center mt-1">
          <span className="inline-block bg-[#18181E] border border-zinc-700 px-6 py-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-200">
            VARIACIÓN AERODINÁMICA FRONTAL // RAKE EN VIVO:{" "}
            {(rearRh - frontRh).toFixed(1)} MM
          </span>
        </div>
      )}
    </div>
  );
}

export function LiveMoTeCGauges({ frame }: { frame: TelemetryFrame }) {
  const { activeSetup, inputMode } = useTelemetry();
  const [activeTab, setActiveTab] = useState<AccTab>("neumaticos");

  const tabs: { id: AccTab; label: string }[] = [
    { id: "neumaticos", label: "NEUMÁTICOS" },
    { id: "electronica", label: "ELECTRÓNICA" },
    { id: "combustible", label: "COMBUSTIBLE Y ESTRATEGIA" },
    { id: "mecanico", label: "AGARRE MECÁNICO" },
    { id: "amortiguadores", label: "AMORTIGUADORES" },
    { id: "aerodinamica", label: "AERODINÁMICA" },
  ];

  // Extraer valores reales del setup activo o derivar del periférico + telemetría en vivo
  const setup: ActiveAccSetup = activeSetup || {};
  const coldClicks = setup.basicSetup?.tyres?.tyrePressure || [62, 62, 63, 63];
  const coldPsi = coldClicks.map((c) => (20.3 + c * 0.1).toFixed(1));
  const toeDeg = setup.basicSetup?.alignment?.toeOutLinear || [
    -0.08, -0.08, 0.12, 0.12,
  ];
  const camberDeg =
    frame.camber_deg ||
    setup.basicSetup?.alignment?.staticCamber || [-3.8, -3.8, -3.2, -3.2];
  const casterDeg = (
    8.5 +
    (setup.basicSetup?.alignment?.casterLF ?? 34) * 0.12
  ).toFixed(1);

  const imoAll: [
    [number, number, number],
    [number, number, number],
    [number, number, number],
    [number, number, number]
  ] = frame.tyre_temps_imo || [
    [
      frame.tyre_temps_core[0] + 2,
      frame.tyre_temps_core[0],
      frame.tyre_temps_core[0] - 2,
    ],
    [
      frame.tyre_temps_core[1] + 2,
      frame.tyre_temps_core[1],
      frame.tyre_temps_core[1] - 2,
    ],
    [
      frame.tyre_temps_core[2] + 2,
      frame.tyre_temps_core[2],
      frame.tyre_temps_core[2] - 2,
    ],
    [
      frame.tyre_temps_core[3] + 2,
      frame.tyre_temps_core[3],
      frame.tyre_temps_core[3] - 2,
    ],
  ];

  const wearAll = frame.tyre_wear || [3.0, 3.0, 3.0, 3.0];
  const padAll = frame.pad_life || [29.0, 29.0, 29.0, 29.0];
  const discAll = frame.disc_life || [32.0, 32.0, 32.0, 32.0];

  const tc1Val =
    frame.tc_level && frame.tc_level > 0
      ? frame.tc_level
      : setup.basicSetup?.electronics?.tC1 ??
        (inputMode === "keyboard" ? 5 : inputMode === "gamepad" ? 4 : 3);
  const absVal =
    frame.abs_level && frame.abs_level > 0
      ? frame.abs_level
      : setup.basicSetup?.electronics?.abs ??
        (inputMode === "keyboard" ? 5 : inputMode === "gamepad" ? 4 : 3);
  const tc2Val =
    setup.basicSetup?.electronics?.tC2 ??
    (inputMode === "keyboard" ? 6 : inputMode === "gamepad" ? 5 : 3);
  const ecuMapVal = (setup.basicSetup?.electronics?.eCUMap ?? 0) + 1;

  const arbFront = setup.advancedSetup?.mechanicalBalance?.aRBFront ?? 4;
  const arbRear = setup.advancedSetup?.mechanicalBalance?.aRBRear ?? 3;
  const brakeTorquePct =
    80 + (setup.advancedSetup?.mechanicalBalance?.brakeTorque ?? 17);
  const steerRatioVal =
    11 + (setup.basicSetup?.alignment?.steerRatio ?? 4);
  const preloadNm = (setup.advancedSetup?.drivetrain?.preload ?? 6) * 10;

  const bumpSlow = setup.advancedSetup?.dampers?.bumpSlow || [10, 10, 9, 9];
  const bumpFast = setup.advancedSetup?.dampers?.bumpFast || [6, 6, 5, 5];
  const reboundSlow = setup.advancedSetup?.dampers?.reboundSlow || [
    16, 16, 11, 11,
  ];
  const reboundFast = setup.advancedSetup?.dampers?.reboundFast || [7, 7, 6, 6];

  const frontRhMm =
    frame.ride_height[0] > 10
      ? Math.round(frame.ride_height[0])
      : 54 + (setup.advancedSetup?.aeroBalance?.rideHeight?.[0] ?? 2);
  const rearRhMm =
    frame.ride_height[1] > 10
      ? Math.round(frame.ride_height[1])
      : 68 + (setup.advancedSetup?.aeroBalance?.rideHeight?.[2] ?? 14);
  const rearWingVal = setup.advancedSetup?.aeroBalance?.rearWing ?? 7;
  const splitterVal = setup.advancedSetup?.aeroBalance?.splitter ?? 0;
  const brakeDucts = setup.advancedSetup?.aeroBalance?.brakeDuct || [3, 3];

  const gearLabel =
    frame.gear < 0 ? "R" : frame.gear === 0 ? "N" : String(frame.gear);
  const rpmPct = Math.min(100, Math.round((frame.rpms / frame.max_rpm) * 100));

  const getThermalGrainStatus = (coreTemp: number) => {
    if (coreTemp < 70) return "Frío";
    if (coreTemp > 98) return "Alto";
    return "None";
  };

  return (
    <div className="space-y-6">
      {/* Barra compacta de Telemetría Primaria en Vivo (Siempre visible arriba) */}
      <div className="bg-[#0B0B0F] border border-zinc-800 p-4">
        <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-400 mb-2">
          <span>
            TELEMETRÍA EN TIEMPO REAL (333 HZ) //{" "}
            <strong className="text-white">
              {frame.car_model.replace(/_/g, " ").toUpperCase()}
            </strong>{" "}
            @ {frame.track_name.toUpperCase()}
          </span>
          <span>
            AIRE {frame.air_temp.toFixed(1)}°C // ASFALTO{" "}
            {frame.road_temp.toFixed(1)}°C // AGUA{" "}
            {(frame.water_temp || 84).toFixed(0)}°C
          </span>
        </div>

        {/* Barra RPM */}
        <div className="w-full h-1.5 bg-zinc-900 overflow-hidden mb-4">
          <div
            className={`h-full transition-all duration-75 ${
              rpmPct > 92
                ? "bg-[#E10600]"
                : rpmPct > 80
                ? "bg-amber-500"
                : "bg-emerald-400"
            }`}
            style={{ width: `${rpmPct}%` }}
          />
        </div>

        <div className="grid grid-cols-3 sm:grid-cols-6 gap-4 tabular-nums font-mono">
          <div>
            <div className="text-[10px] text-zinc-500">VELOCIDAD</div>
            <div className="text-2xl font-bold text-white">
              {Math.round(frame.speed_kmh)}{" "}
              <span className="text-[10px] text-zinc-500 font-normal">KM/H</span>
            </div>
          </div>
          <div>
            <div className="text-[10px] text-zinc-500">MARCHA / RPM</div>
            <div className="text-2xl font-bold text-white">
              M{gearLabel}{" "}
              <span className="text-xs text-zinc-400 font-normal">
                {frame.rpms}
              </span>
            </div>
          </div>
          <div>
            <div className="text-[10px] text-zinc-500">ACELERADOR</div>
            <div className="text-2xl font-bold text-emerald-400">
              {Math.round(frame.gas * 100)}%
            </div>
          </div>
          <div>
            <div className="text-[10px] text-zinc-500">FRENO</div>
            <div className="text-2xl font-bold text-[#E10600]">
              {Math.round(frame.brake * 100)}%
            </div>
          </div>
          <div>
            <div className="text-[10px] text-zinc-500">DIRECCIÓN</div>
            <div className="text-2xl font-bold text-white">
              {(frame.steer_angle * 100).toFixed(0)}%
            </div>
          </div>
          <div>
            <div className="text-[10px] text-zinc-500">ELECTRÓNICA</div>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`px-2 py-0.5 text-[10px] font-bold border ${
                  frame.tc_in_action
                    ? "bg-[#E10600] border-[#E10600] text-white"
                    : "border-zinc-800 text-zinc-500"
                }`}
              >
                TC {tc1Val}
              </span>
              <span
                className={`px-2 py-0.5 text-[10px] font-bold border ${
                  frame.abs_in_action
                    ? "bg-amber-500 border-amber-500 text-black"
                    : "border-zinc-800 text-zinc-500"
                }`}
              >
                ABS {absVal}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* BARRA DE PESTAÑAS OFICIAL ESTILO GARAJE ACC (Idéntica a las capturas) */}
      <div className="bg-black border-t border-b border-zinc-800 px-3 py-2 flex items-center gap-2 sm:gap-5 overflow-x-auto">
        {tabs.map((t) => {
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`px-3.5 py-1.5 text-xs sm:text-sm font-bold uppercase tracking-wider transition whitespace-nowrap ${
                isActive
                  ? "bg-[#E10600] text-white shadow"
                  : "text-zinc-300 hover:text-white"
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {/* =====================================================================
          PESTAÑA 1: NEUMÁTICOS (Réplica exacta de Captura 4 con datos en vivo)
         ===================================================================== */}
      {activeTab === "neumaticos" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center bg-[#070709] border border-zinc-900 p-4 sm:p-6">
          {/* Columna Izquierda (Delantero Izquierdo + Trasero Izquierdo) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-start">
              <div className="sm:col-span-5">
                <AccReadingBox
                  mirror={false}
                  imo={imoAll[0]}
                  wear={wearAll[0]}
                  hotPsi={frame.tyre_pressures[0]}
                  padMm={padAll[0]}
                  discMm={discAll[0]}
                />
              </div>
              <div className="sm:col-span-7">
                <AccBox title="DELANTERO IZQUIERDO">
                  <AccBarRow
                    label="psi"
                    valueText={`${coldPsi[0]} psi`}
                    fillPct={(coldClicks[0] / 95) * 100}
                  />
                  <AccBarRow
                    label="alineación"
                    valueText={`${toeDeg[0].toFixed(2)} °`}
                    fillPct={42}
                  />
                  <AccBarRow
                    label="caída"
                    valueText={`${camberDeg[0].toFixed(1)} °`}
                    fillPct={65}
                  />
                  <AccBarRow
                    label="ángulo de avance"
                    valueText={`${casterDeg} °`}
                    fillPct={58}
                  />
                </AccBox>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-start">
              <div className="sm:col-span-5">
                <AccReadingBox
                  mirror={false}
                  imo={imoAll[2]}
                  wear={wearAll[2]}
                  hotPsi={frame.tyre_pressures[2]}
                  padMm={padAll[2]}
                  discMm={discAll[2]}
                />
              </div>
              <div className="sm:col-span-7">
                <AccBox title="TRASERO IZQUIERDO">
                  <AccBarRow
                    label="psi"
                    valueText={`${coldPsi[2]} psi`}
                    fillPct={(coldClicks[2] / 95) * 100}
                  />
                  <AccBarRow
                    label="alineación"
                    valueText={`${toeDeg[2].toFixed(2)} °`}
                    fillPct={48}
                  />
                  <AccBarRow
                    label="caída"
                    valueText={`${camberDeg[2].toFixed(1)} °`}
                    fillPct={55}
                  />
                </AccBox>
              </div>
            </div>
          </div>

          {/* Coche Central Cenital */}
          <div className="lg:col-span-2 flex justify-center">
            <TopDownGt3Car carModel={frame.car_model} />
          </div>

          {/* Columna Derecha (Delantero Derecho + Trasero Derecho) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-start">
              <div className="sm:col-span-7">
                <AccBox title="DELANTERO DERECHO">
                  <AccBarRow
                    label="psi"
                    valueText={`${coldPsi[1]} psi`}
                    fillPct={(coldClicks[1] / 95) * 100}
                  />
                  <AccBarRow
                    label="alineación"
                    valueText={`${toeDeg[1].toFixed(2)} °`}
                    fillPct={42}
                  />
                  <AccBarRow
                    label="caída"
                    valueText={`${camberDeg[1].toFixed(1)} °`}
                    fillPct={65}
                  />
                  <AccBarRow
                    label="ángulo de avance"
                    valueText={`${casterDeg} °`}
                    fillPct={58}
                  />
                </AccBox>
              </div>
              <div className="sm:col-span-5">
                <AccReadingBox
                  mirror={true}
                  imo={imoAll[1]}
                  wear={wearAll[1]}
                  hotPsi={frame.tyre_pressures[1]}
                  padMm={padAll[1]}
                  discMm={discAll[1]}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-start">
              <div className="sm:col-span-7">
                <AccBox title="TRASERO DERECHO">
                  <AccBarRow
                    label="psi"
                    valueText={`${coldPsi[3]} psi`}
                    fillPct={(coldClicks[3] / 95) * 100}
                  />
                  <AccBarRow
                    label="alineación"
                    valueText={`${toeDeg[3].toFixed(2)} °`}
                    fillPct={48}
                  />
                  <AccBarRow
                    label="caída"
                    valueText={`${camberDeg[3].toFixed(1)} °`}
                    fillPct={55}
                  />
                </AccBox>
              </div>
              <div className="sm:col-span-5">
                <AccReadingBox
                  mirror={true}
                  imo={imoAll[3]}
                  wear={wearAll[3]}
                  hotPsi={frame.tyre_pressures[3]}
                  padMm={padAll[3]}
                  discMm={discAll[3]}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          PESTAÑA 2: ELECTRÓNICA (Réplica exacta de Captura 3 con datos en vivo)
         ===================================================================== */}
      {activeTab === "electronica" && (
        <div className="bg-[#070709] border border-zinc-900 p-4 sm:p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start max-w-4xl mx-auto">
            <AccBox title="COMPONENTES ELECTRÓNICOS">
              <AccBarRow
                label="Control de tracción"
                valueText={String(tc1Val)}
                fillPct={(tc1Val / 11) * 100}
                liveHighlight={frame.tc_in_action}
              />
              <AccBarRow
                label="ABS"
                valueText={String(absVal)}
                fillPct={(absVal / 11) * 100}
                liveHighlight={frame.abs_in_action}
              />
              <AccBarRow
                label="ECUMap"
                valueText={String(ecuMapVal)}
                fillPct={(ecuMapVal / 8) * 100}
              />
              <AccBarRow
                label="vueltas de telemetría"
                valueText={String(frame.completed_laps)}
                fillPct={Math.min(100, frame.completed_laps * 5)}
              />
              <AccBarRow
                label="TC2"
                valueText={String(tc2Val)}
                fillPct={(tc2Val / 11) * 100}
                liveHighlight={frame.tc_in_action}
              />
            </AccBox>

            <div className="bg-[#16161B]/95 border border-zinc-700 p-4 space-y-3 text-xs">
              <div className="flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-zinc-200">
                <span>CONDICIONES</span>
                <span>CON GOMA</span>
                <span>VERDE (SECO)</span>
                <span>MUY MOJADO</span>
              </div>
              <div className="h-1.5 w-full bg-gradient-to-r from-[#E10600] via-emerald-400 to-sky-500" />

              <div className="flex items-center justify-between border-b border-zinc-800 pb-2 pt-1 font-mono">
                <span className="text-[11px] text-zinc-300">
                  Control de tracción
                </span>
                <span className="text-white font-bold tracking-widest">
                  1 &nbsp; 2 &nbsp; 3 &nbsp; 4 &nbsp; 5 &nbsp; 6 &nbsp; 7 &nbsp; 8
                </span>
              </div>

              <div className="flex items-center justify-between border-b border-zinc-800 pb-2 font-mono">
                <span className="text-[11px] text-zinc-300">ABS</span>
                <span className="text-white font-bold tracking-wider">
                  1 &nbsp;2 &nbsp;3 &nbsp;4 &nbsp;5 &nbsp;6 &nbsp;7 &nbsp;8 &nbsp;9
                  &nbsp;10 &nbsp;11 &nbsp;12
                </span>
              </div>

              <div className="h-1.5 w-3/4 ml-auto bg-gradient-to-r from-emerald-400 via-amber-400 to-[#E10600]" />

              <div className="flex items-center justify-between pt-1">
                <span className="text-[11px] text-zinc-300">Desgaste</span>
                <span className="text-zinc-200 font-mono text-[11px]">
                  3 mm (nuevo) &nbsp;&nbsp;&nbsp;&nbsp; 1,5 mm (consumidos)
                </span>
              </div>
            </div>
          </div>

          <SideAeroGt3Car
            withCfdStreamlines={false}
            frontRh={frontRhMm}
            rearRh={rearRhMm}
          />
        </div>
      )}

      {/* =====================================================================
          PESTAÑA 3: COMBUSTIBLE Y ESTRATEGIA (Réplica exacta de Captura 6)
         ===================================================================== */}
      {activeTab === "combustible" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start bg-[#070709] border border-zinc-900 p-4 sm:p-6">
          {/* Izquierda: Estado Neumáticos Izquierdos */}
          <div className="lg:col-span-3 space-y-6">
            {[0, 2].map((idx) => (
              <div
                key={idx}
                className="bg-[#16161B]/95 border border-zinc-800 p-3 space-y-2 text-xs"
              >
                <div className="text-[10px] font-mono uppercase text-zinc-400 border-b border-zinc-800 pb-1">
                  {idx === 0 ? "DELANTERO IZQUIERDO" : "TRASERO IZQUIERDO"}
                </div>
                <div className="flex justify-between border-b border-zinc-800/80 pb-1">
                  <span className="text-zinc-300">Desgaste</span>
                  <span className="font-mono font-bold text-white">
                    {wearAll[idx].toFixed(2)} &nbsp; {wearAll[idx].toFixed(2)}{" "}
                    &nbsp; {wearAll[idx].toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between border-b border-zinc-800/80 pb-1">
                  <span className="text-zinc-300">Quemado</span>
                  <span className="font-mono font-bold text-white">
                    {getThermalGrainStatus(frame.tyre_temps_core[idx])}
                  </span>
                </div>
                <div className="flex justify-between border-b border-zinc-800/80 pb-1">
                  <span className="text-zinc-300">Ampolla</span>
                  <span className="font-mono font-bold text-white">
                    {frame.tyre_temps_core[idx] > 102 ? "Leve" : "None"}
                  </span>
                </div>
                <div className="flex justify-between border-b border-zinc-800/80 pb-1">
                  <span className="text-zinc-300">Punto plano</span>
                  <span className="font-mono font-bold text-white">
                    {frame.wheel_slip[idx] > 3.0 ? "Detectado" : "None"}
                  </span>
                </div>
                <div className="flex justify-between border-b border-zinc-800/80 pb-1">
                  <span className="text-zinc-300">desgaste de pastillas</span>
                  <span className="font-mono font-bold text-white">
                    {padAll[idx].toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-300">desgaste del disco</span>
                  <span className="font-mono font-bold text-white">
                    {discAll[idx].toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Centro: Combustible y Estrategia de Parada en Boxes */}
          <div className="lg:col-span-6 space-y-4">
            <AccBox title="COMBUSTIBLE Y NEUMÁTICOS">
              <AccBarRow
                label="combustible (en vivo)"
                valueText={`${frame.fuel.toFixed(1)} L`}
                fillPct={(frame.fuel / 120) * 100}
                liveHighlight
              />
              <AccBarRow
                label="neumático"
                valueText={frame.tyre_compound || "SECO"}
                fillPct={100}
              />
              <AccBarRow label="juego de neumáticos" valueText="1" fillPct={20} />
              <AccBarRow
                label="frenos delanteros"
                valueText={String(frame.front_brake_compound || 1)}
                fillPct={45}
              />
              <AccBarRow
                label="frenos traseros"
                valueText={String(frame.rear_brake_compound || 1)}
                fillPct={45}
              />
              <div className="flex items-center justify-between pt-1 px-1.5 text-xs">
                <span className="text-zinc-300">combustible por vuelta</span>
                <span className="font-mono font-bold text-white">
                  2.85 L/VUELTA ({Math.max(0, Math.floor(frame.fuel / 2.85))} VUELTAS RESTANTES)
                </span>
              </div>
            </AccBox>

            <AccBox title="ESTRATEGIA DE PARADA EN BOXES // PRESIONES EN VIVO">
              <AccBarRow label="N.º de paradas en boxes" valueText="1" fillPct={25} />
              <AccBarRow
                label="neumático"
                valueText={frame.tyre_compound || "SECO"}
                fillPct={100}
              />
              <AccBarRow
                label="delantero izquierdo (en caliente)"
                valueText={`${frame.tyre_pressures[0].toFixed(1)} psi`}
                fillPct={(frame.tyre_pressures[0] / 32) * 100}
              />
              <AccBarRow
                label="delantero derecho (en caliente)"
                valueText={`${frame.tyre_pressures[1].toFixed(1)} psi`}
                fillPct={(frame.tyre_pressures[1] / 32) * 100}
              />
              <AccBarRow
                label="trasero izquierdo (en caliente)"
                valueText={`${frame.tyre_pressures[2].toFixed(1)} psi`}
                fillPct={(frame.tyre_pressures[2] / 32) * 100}
              />
              <AccBarRow
                label="trasero derecho (en caliente)"
                valueText={`${frame.tyre_pressures[3].toFixed(1)} psi`}
                fillPct={(frame.tyre_pressures[3] / 32) * 100}
              />
              <div className="pt-2 text-center text-xs font-bold uppercase tracking-wider text-white border-t border-zinc-800">
                OBJETIVO AUTO-INYECTOR PIRELLI DHE: 26.8 – 26.9 PSI
              </div>
            </AccBox>
          </div>

          {/* Derecha: Estado Neumáticos Derechos */}
          <div className="lg:col-span-3 space-y-6">
            {[1, 3].map((idx) => (
              <div
                key={idx}
                className="bg-[#16161B]/95 border border-zinc-800 p-3 space-y-2 text-xs"
              >
                <div className="text-[10px] font-mono uppercase text-zinc-400 border-b border-zinc-800 pb-1">
                  {idx === 1 ? "DELANTERO DERECHO" : "TRASERO DERECHO"}
                </div>
                <div className="flex justify-between border-b border-zinc-800/80 pb-1">
                  <span className="text-zinc-300">Desgaste</span>
                  <span className="font-mono font-bold text-white">
                    {wearAll[idx].toFixed(2)} &nbsp; {wearAll[idx].toFixed(2)}{" "}
                    &nbsp; {wearAll[idx].toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between border-b border-zinc-800/80 pb-1">
                  <span className="text-zinc-300">Quemado</span>
                  <span className="font-mono font-bold text-white">
                    {getThermalGrainStatus(frame.tyre_temps_core[idx])}
                  </span>
                </div>
                <div className="flex justify-between border-b border-zinc-800/80 pb-1">
                  <span className="text-zinc-300">Ampolla</span>
                  <span className="font-mono font-bold text-white">
                    {frame.tyre_temps_core[idx] > 102 ? "Leve" : "None"}
                  </span>
                </div>
                <div className="flex justify-between border-b border-zinc-800/80 pb-1">
                  <span className="text-zinc-300">Punto plano</span>
                  <span className="font-mono font-bold text-white">
                    {frame.wheel_slip[idx] > 3.0 ? "Detectado" : "None"}
                  </span>
                </div>
                <div className="flex justify-between border-b border-zinc-800/80 pb-1">
                  <span className="text-zinc-300">desgaste de pastillas</span>
                  <span className="font-mono font-bold text-white">
                    {padAll[idx].toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-300">desgaste del disco</span>
                  <span className="font-mono font-bold text-white">
                    {discAll[idx].toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* =====================================================================
          PESTAÑA 4: AGARRE MECÁNICO (Réplica exacta de Captura 5)
         ===================================================================== */}
      {activeTab === "mecanico" && (
        <div className="bg-[#070709] border border-zinc-900 p-4 sm:p-6 space-y-5">
          {/* Caja Superior FRONTAL */}
          <div className="max-w-md mx-auto">
            <AccBox title="FRONTAL">
              <AccBarRow
                label="barra estabilizadora"
                valueText={String(arbFront)}
                fillPct={(arbFront / 10) * 100}
              />
              <AccBarRow
                label="potencia de frenada"
                valueText={`${brakeTorquePct} %`}
                fillPct={brakeTorquePct}
              />
              <AccBarRow
                label="reparto de frenada"
                valueText={`${frame.brake_bias.toFixed(1)} %`}
                fillPct={frame.brake_bias}
                liveHighlight
              />
              <AccBarRow
                label="relación de giro del volante"
                valueText={String(steerRatioVal)}
                fillPct={(steerRatioVal / 18) * 100}
              />
            </AccBox>
          </div>

          {/* 4 Esquinas + Coche con medidores de recorrido de suspensión en vivo */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
            <div className="lg:col-span-4 space-y-6">
              <AccBox title="DELANTERO IZQUIERDO">
                <AccBarRow
                  label="índice del volante"
                  valueText="182000 N/m"
                  fillPct={75}
                />
                <AccBarRow
                  label="índice del tope de la suspensión"
                  valueText="1000 N"
                  fillPct={55}
                />
                <AccBarRow
                  label="recorrido suspensión (vivo)"
                  valueText={`${(frame.suspension_travel[0] * 1000).toFixed(1)} mm`}
                  fillPct={Math.min(100, frame.suspension_travel[0] * 1500)}
                  liveHighlight
                />
              </AccBox>

              <AccBox title="TRASERO IZQUIERDO">
                <AccBarRow
                  label="índice del volante"
                  valueText="209000 N/m"
                  fillPct={82}
                />
                <AccBarRow
                  label="índice del tope de la suspensión"
                  valueText="500 N"
                  fillPct={30}
                />
                <AccBarRow
                  label="recorrido suspensión (vivo)"
                  valueText={`${(frame.suspension_travel[2] * 1000).toFixed(1)} mm`}
                  fillPct={Math.min(100, frame.suspension_travel[2] * 1500)}
                  liveHighlight
                />
              </AccBox>
            </div>

            <div className="lg:col-span-4 flex justify-center">
              <TopDownGt3Car
                carModel={frame.car_model}
                showShockGauges={true}
                suspensionTravel={frame.suspension_travel}
              />
            </div>

            <div className="lg:col-span-4 space-y-6">
              <AccBox title="DELANTERO DERECHO">
                <AccBarRow
                  label="índice del volante"
                  valueText="182000 N/m"
                  fillPct={75}
                />
                <AccBarRow
                  label="índice del tope de la suspensión"
                  valueText="1000 N"
                  fillPct={55}
                />
                <AccBarRow
                  label="recorrido suspensión (vivo)"
                  valueText={`${(frame.suspension_travel[1] * 1000).toFixed(1)} mm`}
                  fillPct={Math.min(100, frame.suspension_travel[1] * 1500)}
                  liveHighlight
                />
              </AccBox>

              <AccBox title="TRASERO DERECHO">
                <AccBarRow
                  label="índice del volante"
                  valueText="209000 N/m"
                  fillPct={82}
                />
                <AccBarRow
                  label="índice del tope de la suspensión"
                  valueText="500 N"
                  fillPct={30}
                />
                <AccBarRow
                  label="recorrido suspensión (vivo)"
                  valueText={`${(frame.suspension_travel[3] * 1000).toFixed(1)} mm`}
                  fillPct={Math.min(100, frame.suspension_travel[3] * 1500)}
                  liveHighlight
                />
              </AccBox>
            </div>
          </div>

          {/* Caja Inferior TRASERO */}
          <div className="max-w-md mx-auto">
            <AccBox title="TRASERO">
              <AccBarRow
                label="barra estabilizadora"
                valueText={String(arbRear)}
                fillPct={(arbRear / 10) * 100}
              />
              <AccBarRow
                label="carga previa del diferencial"
                valueText={`${preloadNm} Nm`}
                fillPct={(preloadNm / 150) * 100}
              />
            </AccBox>
          </div>
        </div>
      )}

      {/* =====================================================================
          PESTAÑA 5: AMORTIGUADORES (Réplica exacta de Captura 2)
         ===================================================================== */}
      {activeTab === "amortiguadores" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center bg-[#070709] border border-zinc-900 p-4 sm:p-6">
          <div className="lg:col-span-4 space-y-6">
            <AccBox title="DELANTERO IZQUIERDO">
              <AccBarRow
                label="badén"
                valueText={String(bumpSlow[0])}
                fillPct={(bumpSlow[0] / 40) * 100}
              />
              <AccBarRow
                label="compresión rápida"
                valueText={String(bumpFast[0])}
                fillPct={(bumpFast[0] / 40) * 100}
              />
              <AccBarRow
                label="extensión"
                valueText={String(reboundSlow[0])}
                fillPct={(reboundSlow[0] / 40) * 100}
              />
              <AccBarRow
                label="extensión rápida"
                valueText={String(reboundFast[0])}
                fillPct={(reboundFast[0] / 40) * 100}
              />
            </AccBox>

            <AccBox title="TRASERO IZQUIERDO">
              <AccBarRow
                label="badén"
                valueText={String(bumpSlow[2])}
                fillPct={(bumpSlow[2] / 40) * 100}
              />
              <AccBarRow
                label="compresión rápida"
                valueText={String(bumpFast[2])}
                fillPct={(bumpFast[2] / 40) * 100}
              />
              <AccBarRow
                label="extensión"
                valueText={String(reboundSlow[2])}
                fillPct={(reboundSlow[2] / 40) * 100}
              />
              <AccBarRow
                label="extensión rápida"
                valueText={String(reboundFast[2])}
                fillPct={(reboundFast[2] / 40) * 100}
              />
            </AccBox>
          </div>

          <div className="lg:col-span-4 flex justify-center">
            <TopDownGt3Car carModel={frame.car_model} />
          </div>

          <div className="lg:col-span-4 space-y-6">
            <AccBox title="DELANTERO DERECHO">
              <AccBarRow
                label="badén"
                valueText={String(bumpSlow[1])}
                fillPct={(bumpSlow[1] / 40) * 100}
              />
              <AccBarRow
                label="compresión rápida"
                valueText={String(bumpFast[1])}
                fillPct={(bumpFast[1] / 40) * 100}
              />
              <AccBarRow
                label="extensión"
                valueText={String(reboundSlow[1])}
                fillPct={(reboundSlow[1] / 40) * 100}
              />
              <AccBarRow
                label="extensión rápida"
                valueText={String(reboundFast[1])}
                fillPct={(reboundFast[1] / 40) * 100}
              />
            </AccBox>

            <AccBox title="TRASERO DERECHO">
              <AccBarRow
                label="compresión"
                valueText={String(bumpSlow[3])}
                fillPct={(bumpSlow[3] / 40) * 100}
              />
              <AccBarRow
                label="compresión rápida"
                valueText={String(bumpFast[3])}
                fillPct={(bumpFast[3] / 40) * 100}
              />
              <AccBarRow
                label="extensión"
                valueText={String(reboundSlow[3])}
                fillPct={(reboundSlow[3] / 40) * 100}
              />
              <AccBarRow
                label="extensión rápida"
                valueText={String(reboundFast[3])}
                fillPct={(reboundFast[3] / 40) * 100}
              />
            </AccBox>
          </div>
        </div>
      )}

      {/* =====================================================================
          PESTAÑA 6: AERODINÁMICA (Réplica exacta de Captura 1 con CFD)
         ===================================================================== */}
      {activeTab === "aerodinamica" && (
        <div className="bg-[#070709] border border-zinc-900 p-4 sm:p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
            <AccBox title="TRASERO">
              <AccBarRow
                label="altura (en vivo)"
                valueText={`${rearRhMm} mm`}
                fillPct={(rearRhMm / 95) * 100}
                liveHighlight
              />
              <AccBarRow
                label="alerón trasero"
                valueText={String(rearWingVal)}
                fillPct={(rearWingVal / 12) * 100}
              />
              <AccBarRow
                label="conductos de freno"
                valueText={`${brakeDucts[1]} (${frame.brake_temps[2].toFixed(0)}°C)`}
                fillPct={(brakeDucts[1] / 6) * 100}
              />
            </AccBox>

            <AccBox title="PRUEBA DE CARGA DE COMBUSTIBLE">
              <div className="flex items-center justify-between text-xs py-1">
                <span className="text-zinc-400">combustible actual</span>
                <span className="font-mono font-bold text-white">
                  {frame.fuel.toFixed(1)} L
                </span>
              </div>
              <div className="flex items-center justify-between text-xs py-1 border-t border-zinc-800">
                <span className="text-zinc-400">estado fondo plano</span>
                <span
                  className={`font-mono font-bold ${
                    frontRhMm < 42 ? "text-[#E10600]" : "text-emerald-400"
                  }`}
                >
                  {frontRhMm < 42 ? "ROCE DETECTADO" : "SIN ROCE"}
                </span>
              </div>
            </AccBox>

            <AccBox title="DELANTERA">
              <AccBarRow
                label="altura (en vivo)"
                valueText={`${frontRhMm} mm`}
                fillPct={(frontRhMm / 85) * 100}
                liveHighlight
              />
              <AccBarRow
                label="splitter"
                valueText={String(splitterVal)}
                fillPct={Math.max(8, (splitterVal / 5) * 100)}
              />
              <AccBarRow
                label="conductos de freno"
                valueText={`${brakeDucts[0]} (${frame.brake_temps[0].toFixed(0)}°C)`}
                fillPct={(brakeDucts[0] / 6) * 100}
              />
            </AccBox>
          </div>

          <SideAeroGt3Car
            withCfdStreamlines={true}
            frontRh={frontRhMm}
            rearRh={rearRhMm}
          />
        </div>
      )}
    </div>
  );
}
