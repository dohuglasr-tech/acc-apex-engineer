import { NextResponse } from "next/server";
import { createServerSupabase } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");

  if (code) {
    const supabase = await createServerSupabase();
    const { data, error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error && data?.user) {
      const { data: profile } = await supabase
        .from("profiles")
        .select("input_mode")
        .eq("id", data.user.id)
        .single();

      // Si el usuario aún no ha elegido periférico (Teclado, Mando o Volante), va a /onboarding
      if (!profile?.input_mode) {
        return NextResponse.redirect(`${origin}/onboarding`);
      }
      return NextResponse.redirect(`${origin}/dashboard`);
    }
  }

  return NextResponse.redirect(`${origin}/onboarding`);
}
