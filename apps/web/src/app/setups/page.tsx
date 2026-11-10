"use client";

import React from "react";
import { AccSetupEngineerBay } from "@/components/AccSetupEngineerBay";

export default function SetupsPage() {
  return (
    <div className="space-y-8 pb-12">
      <div>
        <h1 className="text-xl font-bold font-mono tracking-tight text-white uppercase">
          TALLER DE INGENIERÍA // SETUP & REGLAJES COMPLETOS
        </h1>
        <p className="text-xs text-zinc-400 font-mono mt-1">
          Configuración avanzada de 6 áreas (Neumáticos, Electrónica, Combustible, Agarre Mecánico,
          Amortiguadores y Aerodinámica) adaptada a tu periférico, estilo y telemetría de pista con Google Gemini 3.5.
        </p>
      </div>

      <AccSetupEngineerBay />
    </div>
  );
}
