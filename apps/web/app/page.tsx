export default function Home() {
  return (
    <div className="space-y-16 py-8">
      <section className="space-y-6">
        <p className="text-sm font-semibold uppercase tracking-wider text-brand-500">
          Private-by-default sales intelligence
        </p>
        <h1 className="text-5xl font-bold leading-tight text-brand-900">
          Your B2B account research,
          <br />
          on AI you actually control.
        </h1>
        <p className="max-w-2xl text-lg text-slate-600">
          PROSPECT turns a CSV of target accounts into outbound-ready sales briefs. Every
          inference runs on open-weights models (Qwen 2.5, Llama 3.3) on infrastructure we
          host for you — or in your own cloud. No OpenAI. No Anthropic. No third-party LLM
          ever sees your prospect or client data.
        </p>
        <div className="flex gap-4">
          <a
            href="/dashboard/upload"
            className="rounded-md bg-brand-700 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-900"
          >
            Upload accounts
          </a>
          <a
            href="/dashboard"
            className="rounded-md border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 hover:border-brand-500"
          >
            View briefs
          </a>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-3">
        {[
          {
            h: "1. Upload a CSV",
            p: "Drop in a list of target companies. We normalize domains, dedupe, and queue them for the agent.",
          },
          {
            h: "2. The agent researches",
            p: "Seven nodes crawl, enrich, scan for signals, synthesize a brief, score the account, and draft a personalized opener.",
          },
          {
            h: "3. Paste-ready briefs",
            p: "Every account gets a one-page brief and a 55-word opening line. Export to CSV or integrate with Smartlead/Instantly.",
          },
        ].map((c) => (
          <div
            key={c.h}
            className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
          >
            <h3 className="text-base font-semibold text-brand-900">{c.h}</h3>
            <p className="mt-2 text-sm text-slate-600">{c.p}</p>
          </div>
        ))}
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
        <h2 className="text-2xl font-bold text-brand-900">Why self-hosted, not a GPT wrapper</h2>
        <ul className="mt-4 grid gap-3 text-sm text-slate-700 md:grid-cols-2">
          <li>Prospect and client data never leaves infrastructure you or we control.</li>
          <li>Per-account inference costs ~$0.02. Gross margins above 85%.</li>
          <li>A domain-specific LoRA fine-tune improves brief quality monthly.</li>
          <li>BYOC: enterprise customers can run the whole agent inside their own AWS/GCP account.</li>
        </ul>
      </section>
    </div>
  );
}
