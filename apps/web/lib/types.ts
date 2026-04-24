export type Buyer = { name: string; role: string; quote_url?: string; note?: string };

export type Signal = {
  kind: string;
  text: string;
  url?: string;
  weight: number;
};

export type Brief = {
  id: string;
  account_id: string;
  job_id: string | null;
  score: number | null;
  summary: string | null;
  pain: string | null;
  signals: Signal[];
  buyers: Buyer[];
  opener: string | null;
  evidence: Record<string, unknown>;
  model_version: string | null;
  created_at: string;
};

export type Account = {
  id: string;
  domain: string;
  company_name: string | null;
  icp_id: string | null;
  created_at: string;
};

export type Job = {
  id: string;
  account_id: string;
  status: "pending" | "running" | "completed" | "failed";
  attempts: number;
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
};
