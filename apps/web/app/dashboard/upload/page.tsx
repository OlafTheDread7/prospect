"use client";

import { useState } from "react";
import Papa from "papaparse";

type Row = { domain?: string; company_name?: string; [key: string]: string | undefined };

export default function UploadPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [filename, setFilename] = useState<string>("");
  const [icp, setIcp] = useState({ name: "", industry: "", size_range: "", geo: "", pain: "", timing_cues: "" });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ inserted: number; skipped: number; message?: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFilename(f.name);
    Papa.parse<Row>(f, {
      header: true,
      skipEmptyLines: true,
      complete: (res) => {
        // Normalize headers: accept "domain", "website", "url", "company_name", "name"
        const normalized = res.data.map((r) => {
          const get = (k: string) => r[k] || r[k.toLowerCase()] || r[k.toUpperCase()];
          return {
            domain: get("domain") || get("website") || get("url") || "",
            company_name: get("company_name") || get("name") || get("company") || "",
          };
        }).filter((r) => (r.domain || "").trim().length > 0);
        setRows(normalized);
      },
    });
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const r = await fetch("/api/upload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rows, icp }),
      });
      const body = await r.json();
      if (!r.ok) throw new Error(body?.error || "upload failed");
      setResult(body);
      setRows([]);
      setFilename("");
    } catch (e: any) {
      setError(e?.message || "upload failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-brand-900">Upload accounts</h1>
        <p className="mt-1 text-sm text-slate-600">
          Drop in a CSV with a <code className="rounded bg-slate-100 px-1">domain</code> column (and optional{" "}
          <code className="rounded bg-slate-100 px-1">company_name</code>). The agent will research each account
          and deliver a brief.
        </p>
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-brand-900">1. Define your ICP</h2>
        <p className="mt-1 text-sm text-slate-600">
          Used once, reused across all accounts in this upload. Tight ICPs produce better briefs.
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {(
            [
              ["name", "e.g. Mid-market logistics"],
              ["industry", "e.g. Logistics"],
              ["size_range", "e.g. 100-500"],
              ["geo", "e.g. North America"],
            ] as const
          ).map(([k, ph]) => (
            <label key={k} className="block">
              <span className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                {k.replace("_", " ")}
              </span>
              <input
                type="text"
                value={(icp as any)[k]}
                onChange={(e) => setIcp({ ...icp, [k]: e.target.value })}
                placeholder={ph}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              />
            </label>
          ))}
        </div>
        <div className="mt-4 grid gap-4">
          <label className="block">
            <span className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Pain</span>
            <textarea
              value={icp.pain}
              onChange={(e) => setIcp({ ...icp, pain: e.target.value })}
              rows={2}
              placeholder="What pain does your offering solve? e.g. 'visibility gaps during TMS migrations'"
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            />
          </label>
          <label className="block">
            <span className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Timing cues</span>
            <textarea
              value={icp.timing_cues}
              onChange={(e) => setIcp({ ...icp, timing_cues: e.target.value })}
              rows={2}
              placeholder="What signals indicate a 'good time to reach out'? e.g. 'VP hire in ops, cloud migration'"
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            />
          </label>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-brand-900">2. Upload your CSV</h2>
        <div className="mt-3">
          <input type="file" accept=".csv" onChange={onFile} className="text-sm" />
          {filename && <span className="ml-3 text-sm text-slate-600">{filename}</span>}
        </div>
        {rows.length > 0 && (
          <div className="mt-4">
            <p className="text-sm text-slate-600">
              {rows.length} rows parsed. Previewing first 5:
            </p>
            <ul className="mt-2 space-y-1 rounded bg-slate-50 p-3 font-mono text-xs text-slate-700">
              {rows.slice(0, 5).map((r, i) => (
                <li key={i}>
                  {r.domain} {r.company_name ? `— ${r.company_name}` : ""}
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <div className="flex items-center gap-4">
        <button
          onClick={submit}
          disabled={submitting || rows.length === 0 || !icp.name}
          className="rounded-md bg-brand-700 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-900 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {submitting ? "Queueing…" : `Queue ${rows.length} accounts`}
        </button>
        {result && (
          <p className="text-sm text-green-700">
            Queued {result.inserted}. Skipped {result.skipped} (duplicates or invalid). Head to the dashboard.
          </p>
        )}
        {error && <p className="text-sm text-red-700">Error: {error}</p>}
      </div>
    </div>
  );
}
