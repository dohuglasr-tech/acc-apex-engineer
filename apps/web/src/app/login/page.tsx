"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient, isSupabaseConfigured } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const handleDiscordLogin = async () => {
    setLoading(true);
    setStatusMsg(null);

    if (!isSupabaseConfigured()) {
      router.push("/onboarding");
      return;
    }

    try {
      const supabase = createClient();
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "discord",
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      if (error) {
        setStatusMsg(error.message);
        setLoading(false);
      }
    } catch (err) {
      setStatusMsg(
        err instanceof Error ? err.message : "Authentication failed"
      );
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[65vh] flex items-center justify-center">
      <div className="max-w-md w-full border border-zinc-800 bg-[#08080A] p-8 space-y-8">
        <div className="space-y-2 border-l-2 border-[#E10600] pl-4">
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-zinc-500">
            DRIVER AUTHENTICATION // RLS ISOLATED
          </div>
          <h1 className="text-xl font-semibold text-white">
            Apex Engineer Telemetry
          </h1>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Inicia sesión con tu cuenta de Discord para acceder a tu perfil de
            telemetría privado, historial de vueltas y vinculación con el agente
            de escritorio.
          </p>
        </div>

        <button
          onClick={handleDiscordLogin}
          disabled={loading}
          className="w-full py-3 px-6 rounded-full border border-zinc-600 hover:border-white text-xs font-medium text-white transition flex items-center justify-center gap-3 disabled:opacity-50"
        >
          <span>
            {loading ? "Redirecting to Discord..." : "Continue with Discord"}
          </span>
        </button>

        {statusMsg && (
          <div className="border-l-2 border-[#E10600] pl-3 text-xs text-zinc-300 font-mono">
            {statusMsg}
          </div>
        )}

        <div className="border-t border-zinc-900 pt-5 space-y-2 text-[11px] font-mono text-zinc-500">
          <div>01 // 100% ISOLATED ACCOUNT DATA (SUPABASE RLS)</div>
          <div>02 // 333 HZ SHARED MEMORY TELEMETRY</div>
          <div>03 // ZERO MODIFICATION TO CONTROLS.JSON</div>
        </div>
      </div>
    </div>
  );
}
