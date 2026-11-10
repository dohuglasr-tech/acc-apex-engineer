"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient, isSupabaseConfigured } from "@/lib/supabase/client";
import { Lock, ShieldCheck, Sparkles, Users } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const handleDiscordLogin = async () => {
    setLoading(true);
    setStatusMsg(null);

    if (!isSupabaseConfigured()) {
      setStatusMsg(
        "Modo Local Activo: Cuando configures NEXT_PUBLIC_SUPABASE_URL y NEXT_PUBLIC_SUPABASE_ANON_KEY en Vercel, el botón abrirá Discord OAuth automáticamente. Redirigiendo a selección de periférico..."
      );
      setTimeout(() => {
        router.push("/onboarding");
      }, 1500);
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
        setStatusMsg(`Error OAuth Discord: ${error.message}`);
        setLoading(false);
      }
    } catch (err) {
      setStatusMsg(
        err instanceof Error ? err.message : "Error al conectar con Supabase Auth"
      );
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[78vh] flex items-center justify-center py-8">
      <div className="max-w-md w-full rounded-2xl bg-[#0F1626] border border-slate-800 p-7 shadow-2xl space-y-6">
        <div className="space-y-2 text-center">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-sky-500/15 text-sky-300 border border-sky-500/30">
            <ShieldCheck className="w-3.5 h-3.5" /> CUENTAS 100% INDIVIDUALES (RLS)
          </div>
          <h1 className="text-2xl font-extrabold text-white">
            ACC Apex Engineer Pro
          </h1>
          <p className="text-xs text-slate-400 leading-relaxed">
            Cada piloto inicia sesión con su cuenta de Discord y tiene su propio
            espacio privado: su periférico, sus vueltas a 333 Hz, sus errores/soluciones
            y sus setups auto-inyectados.
          </p>
        </div>

        <button
          onClick={handleDiscordLogin}
          disabled={loading}
          className="w-full py-3.5 px-5 rounded-xl font-bold text-sm bg-[#5865F2] hover:bg-[#4752C4] text-white transition flex items-center justify-center gap-2.5 shadow-lg shadow-[#5865F2]/30 disabled:opacity-50"
        >
          <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028z" />
          </svg>
          {loading ? "Conectando con Discord..." : "Iniciar Sesión con Discord (1 Clic)"}
        </button>

        {statusMsg && (
          <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/30 text-xs text-sky-300 leading-relaxed">
            {statusMsg}
          </div>
        )}

        <div className="space-y-2.5 pt-3 border-t border-slate-800 text-xs text-slate-400">
          <div className="flex items-start gap-2">
            <Lock className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>
              <strong>Aislamiento RLS (`auth.uid() = user_id`):</strong> Tus amigos pueden entrar con su Discord sin mezclar ni alterar jamás tus vueltas ni tus setups.
            </span>
          </div>
          <div className="flex items-start gap-2">
            <Users className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
            <span>
              <strong>Vinculación con tu `.exe`:</strong> Tu cuenta genera un `agent_token` privado para sincronizar automáticamente tus setups desde tu PC.
            </span>
          </div>
          <div className="flex items-start gap-2">
            <Sparkles className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <span>
              <strong>Garantía de Archivos Locales:</strong> El agente jamás toca `controls.json`, solo inyecta setups `.json` en `Documents\Assetto Corsa Competizione\Setups`.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

