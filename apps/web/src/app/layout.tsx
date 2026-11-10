import type { Metadata } from "next";
import "./globals.css";
import { TelemetryProvider } from "@/lib/telemetry-store";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "APEX ENGINEER // ACC Telemetry & Setup System",
  description:
    "333 Hz Shared Memory Telemetry, Corner Diagnostics, and Real-Time Setup Injection for Assetto Corsa Competizione.",
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
