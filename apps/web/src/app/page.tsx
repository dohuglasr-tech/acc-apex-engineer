"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTelemetry } from "@/lib/telemetry-store";

export default function HomePage() {
  const router = useRouter();
  const { inputMode } = useTelemetry();

  useEffect(() => {
    if (!inputMode) {
      router.replace("/onboarding");
    } else {
      router.replace("/dashboard");
    }
  }, [inputMode, router]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center space-y-2">
        <div className="w-8 h-8 rounded-full border-2 border-sky-400 border-t-transparent animate-spin mx-auto" />
        <p className="text-xs font-mono text-slate-400">
          Iniciando ACC Apex Engineer Pro (333 Hz)...
        </p>
      </div>
    </div>
  );
}

