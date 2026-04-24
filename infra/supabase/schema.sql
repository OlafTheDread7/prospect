-- =====================================================
-- PROSPECT — Supabase schema
-- =====================================================
-- Run this in the Supabase SQL editor against a fresh project.
-- Idempotent: safe to re-run.
-- =====================================================

-- Required extensions
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- =====================================================
-- users (mirrors auth.users)
-- =====================================================
create table if not exists public.users (
  id            uuid primary key references auth.users(id) on delete cascade,
  email         text not null,
  plan          text not null default 'starter' check (plan in ('starter','pro','agency','byoc')),
  created_at    timestamptz not null default now()
);

-- Keep public.users in sync with auth.users
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.users (id, email) values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- =====================================================
-- icps
-- =====================================================
create table if not exists public.icps (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid not null references public.users(id) on delete cascade,
  name          text not null,
  industry      text,
  size_range    text,         -- e.g. '20-200'
  geo           text,
  pain          text,         -- free-text description
  timing_cues   text,         -- what "good timing" looks like
  created_at    timestamptz not null default now()
);
create index if not exists icps_user_idx on public.icps(user_id);

-- =====================================================
-- accounts  (target companies)
-- =====================================================
create table if not exists public.accounts (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid not null references public.users(id) on delete cascade,
  icp_id        uuid references public.icps(id) on delete set null,
  domain        text not null,                  -- e.g. 'acme.com'
  company_name  text,
  raw_input     jsonb not null default '{}'::jsonb,
  created_at    timestamptz not null default now(),
  unique (user_id, domain)
);
create index if not exists accounts_user_idx on public.accounts(user_id);

-- =====================================================
-- jobs  (one row per account × agent run)
-- =====================================================
create table if not exists public.jobs (
  id            uuid primary key default uuid_generate_v4(),
  account_id    uuid not null references public.accounts(id) on delete cascade,
  user_id       uuid not null references public.users(id) on delete cascade,
  status        text not null default 'pending'
                  check (status in ('pending','running','completed','failed')),
  attempts      int  not null default 0,
  error         text,
  created_at    timestamptz not null default now(),
  started_at    timestamptz,
  completed_at  timestamptz
);
create index if not exists jobs_status_idx on public.jobs(status, created_at);
create index if not exists jobs_user_idx on public.jobs(user_id);

-- =====================================================
-- briefs
-- =====================================================
create table if not exists public.briefs (
  id            uuid primary key default uuid_generate_v4(),
  account_id    uuid not null references public.accounts(id) on delete cascade,
  user_id       uuid not null references public.users(id) on delete cascade,
  job_id        uuid references public.jobs(id) on delete set null,
  score         int check (score between 0 and 10),
  summary       text,
  signals       jsonb not null default '[]'::jsonb,   -- [{kind, text, url, weight}]
  pain          text,
  buyers        jsonb not null default '[]'::jsonb,   -- [{name, role, quote_url}]
  opener        text,
  evidence      jsonb not null default '{}'::jsonb,
  model_version text,
  created_at    timestamptz not null default now()
);
create index if not exists briefs_user_idx on public.briefs(user_id);
create index if not exists briefs_account_idx on public.briefs(account_id);

-- =====================================================
-- feedback  (training data for LoRA)
-- =====================================================
create table if not exists public.feedback (
  id            uuid primary key default uuid_generate_v4(),
  brief_id      uuid not null references public.briefs(id) on delete cascade,
  user_id       uuid not null references public.users(id) on delete cascade,
  rating        int check (rating between 1 and 5),
  edit_text     text,                              -- the user's corrected version
  created_at    timestamptz not null default now()
);
create index if not exists feedback_user_idx on public.feedback(user_id);

-- =====================================================
-- Row-Level Security
-- =====================================================
alter table public.users     enable row level security;
alter table public.icps      enable row level security;
alter table public.accounts  enable row level security;
alter table public.jobs      enable row level security;
alter table public.briefs    enable row level security;
alter table public.feedback  enable row level security;

-- Users: a user reads their own row.
drop policy if exists users_self_read on public.users;
create policy users_self_read on public.users
  for select using (auth.uid() = id);

-- Helper: owner-only policies for a table
do $$
declare tbl text;
begin
  foreach tbl in array array['icps','accounts','jobs','briefs','feedback'] loop
    execute format('drop policy if exists %I_owner_all on public.%I', tbl, tbl);
    execute format($f$
      create policy %I_owner_all on public.%I
        for all using (user_id = auth.uid()) with check (user_id = auth.uid())
    $f$, tbl, tbl);
  end loop;
end $$;

-- NOTE: the Python worker uses the SERVICE_ROLE key which
-- bypasses RLS. Keep that key server-side only.
