import { NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

type Row = { domain?: string; company_name?: string };
type ICP = {
  name: string;
  industry?: string;
  size_range?: string;
  geo?: string;
  pain?: string;
  timing_cues?: string;
};

export const runtime = "nodejs";

export async function POST(req: Request) {
  let body: { rows: Row[]; icp: ICP };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }
  const rows = Array.isArray(body?.rows) ? body.rows : [];
  const icp = body?.icp;
  if (!icp?.name) return NextResponse.json({ error: "icp.name required" }, { status: 400 });
  if (rows.length === 0) return NextResponse.json({ error: "no rows" }, { status: 400 });

  let db;
  try {
    db = supabaseAdmin();
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }

  // TODO: pull user_id from an auth cookie. For MVP we accept a single-tenant
  // dev user. Replace with a real auth check before production.
  const { data: users, error: userErr } = await db.from("users").select("id").limit(1);
  if (userErr || !users || users.length === 0) {
    return NextResponse.json(
      { error: "no user found; sign up via supabase auth first" },
      { status: 400 }
    );
  }
  const userId = users[0].id;

  // Insert ICP
  const { data: icpRow, error: icpErr } = await db
    .from("icps")
    .insert({ ...icp, user_id: userId })
    .select()
    .single();
  if (icpErr) return NextResponse.json({ error: icpErr.message }, { status: 500 });

  let inserted = 0;
  let skipped = 0;
  for (const r of rows) {
    const domain = normalizeDomain(r.domain || "");
    if (!domain) {
      skipped++;
      continue;
    }
    const { data: acct, error: acctErr } = await db
      .from("accounts")
      .upsert(
        {
          user_id: userId,
          icp_id: icpRow.id,
          domain,
          company_name: r.company_name || null,
          raw_input: r,
        },
        { onConflict: "user_id,domain" }
      )
      .select()
      .single();
    if (acctErr || !acct) {
      skipped++;
      continue;
    }
    const { error: jobErr } = await db
      .from("jobs")
      .insert({ user_id: userId, account_id: acct.id, status: "pending" });
    if (jobErr) {
      skipped++;
      continue;
    }
    inserted++;
  }

  return NextResponse.json({ inserted, skipped, icp_id: icpRow.id });
}

function normalizeDomain(s: string): string {
  s = (s || "").trim().toLowerCase();
  if (!s) return "";
  s = s.replace(/^https?:\/\//, "").replace(/^www\./, "");
  s = s.split("/")[0];
  if (!s.includes(".")) return "";
  return s;
}
