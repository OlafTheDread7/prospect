import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PROSPECT — Self-hosted B2B account intelligence",
  description:
    "Upload target accounts. Get one-page sales briefs. Powered by open-weights LLMs on infrastructure you control.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-slate-200 bg-white">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
              <a href="/" className="text-xl font-bold text-brand-700">
                PROSPECT
              </a>
              <nav className="flex gap-6 text-sm font-medium text-slate-600">
                <a href="/dashboard" className="hover:text-brand-700">
                  Dashboard
                </a>
                <a href="/dashboard/upload" className="hover:text-brand-700">
                  Upload
                </a>
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
