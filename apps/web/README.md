# PROSPECT web

The Next.js 14 (App Router) frontend. Handles CSV upload, ICP definition, and the briefs dashboard.

## Run locally

```bash
cp ../../.env.example ../../.env
# Fill in NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY

npm install
npm run dev
```

Open http://localhost:3000.

## Routes

| Path                              | What it does                                       |
| --------------------------------- | -------------------------------------------------- |
| `/`                               | Marketing landing                                  |
| `/dashboard`                      | List of briefs (newest first), queue depth         |
| `/dashboard/upload`               | ICP form + CSV upload                              |
| `/dashboard/briefs/[id]`          | Full brief detail with copy-to-clipboard opener    |
| `/api/upload` (POST)              | Accepts `{ rows, icp }`, inserts accounts + jobs   |
| `/api/briefs` (GET)               | Returns briefs JSON                                |
| `/api/billing/checkout` (POST)    | Stripe checkout (stubbed — replace in week 4)      |

## Auth

MVP uses a single-tenant dev user (picks the first row from `public.users`). Before letting real users in:

1. Wire Supabase auth with email magic links in `/app/login`.
2. Replace the TODO in `app/api/upload/route.ts` to derive `user_id` from the session cookie.
3. Keep `SUPABASE_SERVICE_ROLE_KEY` server-side only — it bypasses RLS.
