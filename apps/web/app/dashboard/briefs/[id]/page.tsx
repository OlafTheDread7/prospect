import Link from "next/link";
import { notFound } from "next/navigation";
import { supabaseAdmin } from "@/lib/supabase";
import type { Brief, Account, Signal, Buyer } from "@/lib/types";

export const dynamic = "force-dynamic";

async function loadBrief(id: string): Promise<(Brief & { account: Account | null }) | null> {
  try {
    const db = supabaseAdmin();
    const { data } = await db
      .from("briefs")
      .select("*, account:accounts(id, domain, company_name, icp_id, created_at)")
      .eq("id", id)
      .limit(1)
      .single();
    return (data as any) || null;
  } catch {
    return null;
  }
}

function scoreBadge(score: number | null) {
  const color =
    score === null
      ? "bg-slate-200 text-slate-700"
      : score >= 8
      ? "bg-green-100 text-green-800"
      : score >= 5
      ? "bg-amber-100 text-amber-800"
      : "bg-slate-200 text-slate-700";
  return (
    <span className={`inline-block rounded px-3 py-1 text-sm font-semibold ${color}`}>
      {score ?? "—"}/10
    </span>
  );
}

export default async function BriefPage({ params }: { params: { id: string } }) {
  const brief = await loadBrief(params.id);
  if (!brief) notFound();

  const signals = (brief.signals || []) as Signal[];
  const buyers = (brief.buyers || []) as Buyer[];

  return (
    <div className="space-y-8">
      <div>
        <Link href="/dashboard" className="text-sm text-brand-700 hover:underline">
          ← All briefs
        </Link>
      </div>

      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-brand-900">
            {brief.account?.company_name || brief.account?.domain}
          </h1>
          <p className="mt-1 text-sm text-slate-600">{brief.account?.domain}</p>
        </div>
        {scoreBadge(brief.score)}
      </header>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Summary</h2>
        <p className="mt-2 text-slate-800">{brief.summary}</p>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Pain hypothesis</h2>
        <p className="mt-2 text-slate-800">{brief.pain}</p>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Top signals</h2>
          <ul className="mt-3 space-y-3">
            {signals.length === 0 && <li className="text-sm text-slate-500">No signals.</li>}
            {signals.map((s, i) => (
              <li key={i} className="rounded border border-slate-100 bg-slate-50 p-3">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase text-brand-500">
                  {s.kind}
                  <span className="text-slate-400">weight {s.weight.toFixed(2)}</span>
                </div>
                <div className="mt-1 text-sm text-slate-800">{s.text}</div>
                {s.url && (
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1 block text-xs text-brand-700 hover:underline"
                  >
                    {s.url}
                  </a>
                )}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Likely buyers</h2>
          <ul className="mt-3 space-y-3">
            {buyers.length === 0 && <li className="text-sm text-slate-500">No buyers identified.</li>}
            {buyers.map((b, i) => (
              <li key={i} className="rounded border border-slate-100 bg-slate-50 p-3">
                <div className="font-semibold text-slate-900">{b.name}</div>
                <div className="text-xs uppercase tracking-wide text-slate-500">{b.role}</div>
                {b.note && <div className="mt-1 text-sm text-slate-700">{b.note}</div>}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="rounded-lg border-2 border-brand-500 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-brand-500">Opening line</h2>
        <p className="mt-3 text-lg text-slate-900">{brief.opener}</p>
        <button
          className="mt-4 rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:border-brand-500"
          type="button"
        >
          Copy to clipboard
        </button>
      </section>

      <footer className="text-xs text-slate-500">
        Model: {brief.model_version} · Created {new Date(brief.created_at).toLocaleString()}
      </footer>
    </div>
  );
}
