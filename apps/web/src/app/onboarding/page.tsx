"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { InputMode, useTelemetry } from "@/lib/telemetry-store";

export default function OnboardingPage() {
  const router = useRouter();
  const { inputMode, setInputMode, profile } = useTelemetry();
  const [selected, setSelected] = useState<InputMode>(inputMode || "wheel");
  const [wheelModel, setWheelModel] = useState(profile?.wheel_type || "");
  const [saving, setSaving] = useState(false);

  const options: {
    code: string;
    id: InputMode;
    title: string;
    subtitle: string;
    specs: string;
  }[] = [
    {
      code: "01",
      id: "keyboard",
      title: "Keyboard",
      subtitle: "Digital Binary Actuation",
      specs:
        "Steer Ratio 16–18 // Brake Torque 93% // ABS 5 // Progressive TC curve",
    },
    {
      code: "02",
      id: "gamepad",
      title: "Controller / Gamepad",
      subtitle: "Analog Thumbstick & Triggers",
      specs:
        "Stiffened Front Slow Rebound // Steer Ratio 15:1 // +0.5% Rear Aero Balance",
    },
    {
      code: "03",
      id: "wheel",
      title: "Steering Wheel & Pedals",
      subtitle: "Force Feedback & Load-Cell",
      specs:
        "Direct Steer Ratio 12–14 // 100% Brake Torque // ABS 2–3 // Maximum Rake",
    },
  ];

  const handleConfirm = async () => {
    setSaving(true);
    await setInputMode(selected, selected === "wheel" ? wheelModel : undefined);
    setSaving(false);
    router.push("/dashboard");
  };

  return (
    <div className="space-y-10">
      <div className="space-y-1">
        <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-zinc-500">
          HARDWARE CALIBRATION // PHYSICS ADAPTATION
        </div>
        <h1 className="text-lg font-semibold text-white">
          Select Primary Input Device
        </h1>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse tabular-nums">
          <thead>
            <tr className="border-b border-zinc-800 text-[10px] font-mono uppercase tracking-[0.16em] text-zinc-500">
              <th className="py-3 pr-4">ID</th>
              <th className="py-3 px-4">HARDWARE PROFILE</th>
              <th className="py-3 px-4">CONTROL TYPE</th>
              <th className="py-3 px-4">PHYSICS & SETUP PARAMETERS</th>
              <th className="py-3 pl-4 text-right">STATE</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-900 text-xs">
            {options.map((opt) => {
              const isSelected = selected === opt.id;
              return (
                <tr
                  key={opt.id}
                  onClick={() => setSelected(opt.id)}
                  className={`cursor-pointer transition ${
                    isSelected ? "bg-zinc-950" : "hover:bg-zinc-950/60"
                  }`}
                >
                  <td className="py-5 pr-4 font-mono text-zinc-500">
                    {opt.code}
                  </td>
                  <td className="py-5 px-4 font-medium text-white flex items-center gap-3">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        isSelected ? "bg-[#E10600]" : "bg-zinc-700"
                      }`}
                    />
                    <span>{opt.title}</span>
                  </td>
                  <td className="py-5 px-4 text-zinc-400">{opt.subtitle}</td>
                  <td className="py-5 px-4 font-mono text-zinc-400">
                    {opt.specs}
                  </td>
                  <td className="py-5 pl-4 text-right font-mono">
                    <span
                      className={`text-[10px] uppercase tracking-wider px-3 py-1 rounded-full border ${
                        isSelected
                          ? "border-[#E10600] text-white"
                          : "border-zinc-800 text-zinc-500"
                      }`}
                    >
                      {isSelected ? "SELECTED" : "SELECT"}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {selected === "wheel" && (
        <div className="border-t border-zinc-900 pt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="text-xs text-zinc-400">
            Wheel Base / Pedals Model (Optional)
          </div>
          <input
            type="text"
            value={wheelModel}
            onChange={(e) => setWheelModel(e.target.value)}
            className="w-full sm:w-80 bg-zinc-950 border border-zinc-800 px-3.5 py-2 text-xs text-white font-mono focus:outline-none focus:border-zinc-500"
            placeholder="e.g. Fanatec CSL DD / Moza R9 / G29"
          />
        </div>
      )}

      <div className="pt-4 flex justify-center">
        <button
          onClick={handleConfirm}
          disabled={saving}
          className="px-8 py-2.5 rounded-full border border-zinc-500 hover:border-white text-xs font-medium text-white transition"
        >
          {saving ? "Saving Profile..." : "Apply Hardware Profile"}
        </button>
      </div>
    </div>
  );
}
