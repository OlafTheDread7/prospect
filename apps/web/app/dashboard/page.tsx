import Link from "next/link";
import { supabaseAdmin } from "@/lib/supabase";
import type { Brief, Account } from "@/lib/types";

export const dynamic = "force-dynamic";

type Row = Brief & { account: Account | null };

async function loadData(): Promise<{ briefs: Row[]; pending: number }> {
  try {
    const db = supabaseAdmin();
    const [briefsRes, pendingRes] = await Promise.all([
      db
        .from("briefs")
        .select("*, account:accounts(id, domain, company_name, icp_id, created_at)")
        .order("created_at", { ascending: false })
        .limit(50),
      db.from("jobs").select("id", { count: "exact", head: true }).in("status", ["pending", "running"]),
    ]);
    return {
      briefs: (briefsRes.data as any) || [],
      pending: pendingRes.count ?? 0,
    };
  } catch {
    return { briefs: [], pending: 0 };
  }
}

function scoreColor(score: number | null): string {
  if (score === null) return "bg-slate-200 text-slate-700";
  if (score >= 8) return "bg-green-100 text-green-800";
  if (score >= 5) return "bg-amber-100 text-amber-800";
  return "bg-slate-200 text-slate-700";
}

export default async function DashboardPage() {
  const { briefs, pending } = await loadData();

  return (
    <div className="space-y-8">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold text-brand-900">Briefs</h1>
          <p className="mt-1 text-sm text-slate-600">
            {briefs.length} delivered · {pending} in queue
          </p>
        </div>
        <Link
          href="/dashboard/upload"
          className="rounded-md bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-900"
        >
          Upload accounts
        </Link>
      </div>

      {briefs.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-12 text-center">
          <h2 className="text-lg font-semibold text-slate-900">No briefs yet</h2>
          <p className="mt-1 text-sm text-slate-600">
            Upload a CSV of target accounts to get started. The agent runs async and briefs land
            here as they complete.
          </p>
          <Link
            href="/dashboard/upload"
            className="mt-4 inline-block rounded-md bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-900"
          >
            Upload your first list
          </Link>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          {/* Header */}
          <div className="grid grid-cols-12 gap-4 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <div className="col-span-3">Account</div>
            <div className="col-span-1">Score</div>
            <div className="col-span-6">Summary</div>
            <div className="col-span-2">Created</div>
          </div>

          {/* Rows — each row is a <Link>, so the whole row is clickable */}
          <ul className="divide-y divide-slate-100">
            {briefs.map((b) => (
              <li key={b.id}>
                <Link
                  href={`/dashboard/briefs/${b.id}`}
                  className="grid grid-cols-12 gap-4 px-4 py-3 text-sm transition hover:bg-brand-50"
                >
                  <div className="col-span-3">
                    <div className="font-semibold text-brand-700">
                      {b.account?.company_name || b.account?.domain || "—"}
                    </div>
                    <div className="text-xs text-slate-500">{b.account?.domain}</div>
                  </div>
                  <div className="col-span-1">
                    <span
                      className={`inline-block rounded px-2 py-1 text-xs font-semibold ${scoreColor(
                        b.score
                      )}`}
                    >
                      {b.score ?? "—"}/10
                    </span>
                  </div>
                  <div className="col-span-6 text-slate-700 line-clamp-2">{b.summary}</div>
                  <div className="col-span-2 text-slate-500">
                    {new Date(b.created_at).toLocaleDateString()}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
