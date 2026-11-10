import type { Metadata } from "next";
import "./globals.css";
import { TelemetryProvider } from "@/lib/telemetry-store";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "ACC Apex Engineer Pro · Telemetría 333 Hz & Auto-Inyector de Setups",
  description:
    "Ingeniero de pista en tiempo real a 333 Hz, detector de errores por curva y auto-inyector de setups físicos para Assetto Corsa Competizione con cuentas aisladas en Supabase y login con Discord.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="dark">
      <body className="min-h-screen bg-[#070A12] text-slate-100 antialiased selection:bg-sky-500 selection:text-slate-950">
        <TelemetryProvider>
          <Navbar />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">{children}</main>
        </TelemetryProvider>
      </body>
    </html>
  );
}

