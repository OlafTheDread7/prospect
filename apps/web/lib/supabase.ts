import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
const service = process.env.SUPABASE_SERVICE_ROLE_KEY || "";

/** Browser-safe client (anon). */
export function supabaseBrowser() {
  return createClient(url, anon);
}

/** Server-only client using the service role key. NEVER import from the client. */
export function supabaseAdmin() {
  if (!url || !service) {
    throw new Error("Supabase admin not configured. Set SUPABASE_SERVICE_ROLE_KEY.");
  }
  return createClient(url, service, { auth: { persistSession: false } });
}
