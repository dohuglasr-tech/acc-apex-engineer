"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { InputMode, useTelemetry } from "@/lib/telemetry-store";
import { CheckCircle2, Gamepad2, Gauge, Keyboard, ShieldAlert } from "lucide-react";

export default function OnboardingPage() {
  const router = useRouter();
  const { inputMode, setInputMode, profile } = useTelemetry();
  const [selected, setSelected] = useState<InputMode>(inputMode || "wheel");
  const [wheelModel, setWheelModel] = useState(
    profile.wheel_type || "Logitech G29 / G923 / Fanatec CSL DD"
  );
  const [saving, setSaving] = useState(false);

  const options: {
    id: InputMode;
    title: string;
    subtitle: string;
    icon: React.ComponentType<{ className?: string }>;
    specs: string[];
  }[] = [
    {
      id: "keyboard",
      title: "Teclado (Keyboard)",
      subtitle: "Pulsación digital W / A / S / D o flechas",
      icon: Keyboard,
      specs: [
        "Steer Ratio suave (16–18) para evitar saturar las gomas delanteras",
        "Brake Torque 92–95% y ABS 4–6 para impedir bloqueos instantáneos",
        "Margen aerodinámico trasero +1.0% y TC progresivo al pulsar W al 100%",
        "Compensación automática de sobrecalentamiento delantero (scrub) en PSI",
      ],
    },
    {
      id: "gamepad",
      title: "Mando / Gamepad (Xbox · DualSense)",
      subtitle: "Stick analógico corto + gatillos LT/RT (L2/R2)",
      icon: Gamepad2,
      specs: [
        "Slow Rebound delantero endurecido anti-latigazo al soltar el gatillo izquierdo",
        "Steer Ratio progresivo (15–16) adaptado al recorrido del stick",
        "Margen aerodinámico trasero +0.5% para evitar pérdidas súbitas de cola",
        "Guías de modulación de gatillo y apoyo de stick a 45° en cada curva",
      ],
    },
    {
      id: "wheel",
      title: "Volante FFB (Direct Drive / Belt / Gear)",
      subtitle: "Volante Force Feedback + Pedales (Potenciómetro o Célula de Carga)",
      icon: Gauge,
      specs: [
        "Steer Ratio directo (12–14) para máxima precisión en vértice",
        "Brake Torque al 100% y ABS 2–3 para aprovechar el trail-braking real",
        "Rake aerodinámico agresivo para máxima rotación en curvas rápidas",
        "Diagnóstico de regresión de pedal de freno y ángulo óptimo de deriva",
      ],
    },
  ];

  const handleConfirm = async () => {
    setSaving(true);
    await setInputMode(selected, selected === "wheel" ? wheelModel : undefined);
    setSaving(false);
    router.push("/dashboard");
  };

  return (
    <div className="max-w-4xl mx-auto py-4 space-y-6">
      <div className="rounded-2xl bg-[#0F1626] border border-slate-800 p-6 space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
          <ShieldAlert className="w-3.5 h-3.5" /> PASO OBLIGATORIO DE CALIBRACIÓN FÍSICA
        </div>
        <h1 className="text-2xl font-extrabold text-white">
          ¿Con qué periférico conduces en Assetto Corsa Competizione?
        </h1>
        <p className="text-xs sm:text-sm text-slate-400">
          Tanto el <strong>Auto-Inyector de Setups (`APEX_AUTO_LIVE.json`)</strong> como el{" "}
          <strong>Detector de Errores por Curva</strong> adaptan todas sus leyes físicas a 333 Hz
          según si juegas con <strong>Teclado</strong>, <strong>Mando</strong> o{" "}
          <strong>Volante</strong>.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {options.map((opt) => {
          const Icon = opt.icon;
          const isSelected = selected === opt.id;
          return (
            <button
              key={opt.id}
              type="button"
              onClick={() => setSelected(opt.id)}
              className={`text-left rounded-2xl p-5 border transition flex flex-col justify-between ${
                isSelected
                  ? "bg-sky-950/30 border-sky-400 ring-2 ring-sky-400/30"
                  : "bg-[#0F1626] border-slate-800 hover:border-slate-700"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div
                    className={`w-11 h-11 rounded-xl flex items-center justify-center ${
                      isSelected
                        ? "bg-sky-500 text-slate-950"
                        : "bg-slate-900 text-sky-400"
                    }`}
                  >
                    <Icon className="w-6 h-6" />
                  </div>
                  {isSelected && (
                    <span className="inline-flex items-center gap-1 text-xs font-bold text-sky-400">
                      <CheckCircle2 className="w-4 h-4" /> Seleccionado
                    </span>
                  )}
                </div>

                <h2 className="text-base font-bold text-white">{opt.title}</h2>
                <p className="text-xs text-slate-400 mt-1 mb-4">{opt.subtitle}</p>

                <ul className="space-y-2 border-t border-slate-800/80 pt-3">
                  {opt.specs.map((sp, i) => (
                    <li
                      key={i}
                      className="text-xs text-slate-300 flex items-start gap-1.5 leading-relaxed"
                    >
                      <span className="text-emerald-400 font-bold">•</span>
                      <span>{sp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </button>
          );
        })}
      </div>

      {selected === "wheel" && (
        <div className="rounded-xl bg-[#0F1626] border border-slate-800 p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-xs text-slate-300">
            <strong>Modelo de tu Volante (opcional):</strong> Se guarda en tu perfil privado de Supabase.
          </div>
          <input
            type="text"
            value={wheelModel}
            onChange={(e) => setWheelModel(e.target.value)}
            className="w-full sm:w-80 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono"
            placeholder="Ej: Logitech G29, Moza R9, Fanatec CSL DD"
          />
        </div>
      )}

      <div className="flex justify-end">
        <button
          onClick={handleConfirm}
          disabled={saving}
          className="px-6 py-3.5 rounded-xl font-bold text-sm bg-gradient-to-r from-sky-500 to-emerald-500 hover:from-sky-400 hover:to-emerald-400 text-slate-950 shadow-lg shadow-sky-500/20 transition"
        >
          {saving
            ? "Aplicando Física Personalizada..."
            : `Confirmar Modo ${selected.toUpperCase()} e Ir al Dashboard 333 Hz →`}
        </button>
      </div>
    </div>
  );
}

