import type { Metadata } from "next";
import "./globals.css";
import { TelemetryProvider } from "@/lib/telemetry-store";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "APEX ENGINEER // Telemetría y Auto-Inyección ACC (333 Hz)",
  description:
    "Sistema de telemetría en tiempo real a 333 Hz, diagnóstico de conducción por curva y auto-inyección de setups para Assetto Corsa Competizione.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="dark">
      <body className="min-h-screen bg-black text-zinc-100 antialiased selection:bg-[#E10600] selection:text-white">
        <TelemetryProvider>
          <Navbar />
          <main className="max-w-6xl mx-auto px-6 py-10">{children}</main>
        </TelemetryProvider>
      </body>
    </html>
  );
}
