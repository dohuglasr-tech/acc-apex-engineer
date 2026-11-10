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
      <div className="text-center space-y-3">
        <div className="w-6 h-6 rounded-full border-2 border-[#E10600] border-t-transparent animate-spin mx-auto" />
        <p className="text-[11px] font-mono uppercase tracking-[0.14em] text-[#8E8E93]">
          Initializing Telemetry System...
        </p>
      </div>
    </div>
  );
}
