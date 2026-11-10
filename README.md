# ACC Apex Engineer Pro 🏎️⚡

**Ingeniero de Pista en Tiempo Real a 333 Hz, Auto-Inyector de Setups Físicos, Detector de Errores por Curva y HUD In-Game (0 MB VRAM) para Assetto Corsa Competizione.**

Repositorio Oficial: [`dohuglasr-tech/acc-apex-engineer`](https://github.com/dohuglasr-tech/acc-apex-engineer)

---

## 🔒 Especificaciones de Seguridad y Aislamiento

1. **Cuentas 100% Individuales y Privadas (Supabase RLS):** Cada piloto inicia sesión con su cuenta y tiene su propio espacio aislado (`auth.uid() = user_id`): su perfil, su periférico (`keyboard`, `gamepad`, `wheel`), su historial de vueltas, sus errores/soluciones y sus setups individuales.
2. **Login con Discord (1 Clic):** Autenticación oficial mediante **Discord OAuth** integrada en **Supabase Auth**, tanto para la Web en **Vercel** como para vincular el **Agente Ejecutable `.exe`** mediante `agent_token`.
3. **Selector Obligatorio de Entrada (`Teclado` · `Mando` · `Volante`):** Adapta las leyes físicas del auto-inyector y los diagnósticos de conducción según el periférico real del piloto.
4. **Alcance Estricto en Archivos Locales:** El Agente `.exe` **NUNCA toca `controls.json` ni configuraciones de botones/volante**. Únicamente lee la Memoria Compartida de ACC a `333 Hz` (`Local\acpmf_physics`, `Local\acpmf_graphics`, `Local\acpmf_static`) y auto-inyecta en tiempo real archivos `.json` de setup en `Documents\Assetto Corsa Competizione\Setups\<coche>\<circuito>\APEX_AUTO_LIVE.json`.

---

## 📂 Estructura del Monorepo

```text
acc-apex-engineer/
├── apps/
│   ├── web/                        # Next.js 15 (App Router) + Tailwind CSS + Supabase Auth (Vercel)
│   └── desktop-agent/              # Agente Local de Windows (.exe) en Python 3.12 (333 Hz + HUD + Voz)
├── supabase/
│   └── migrations/
│       └── 001_schema_rls.sql      # Esquema PostgreSQL con Row-Level Security + RPCs de Agente
└── vercel.json                     # Configuración de despliegue automático en Vercel
```

