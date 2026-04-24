import { NextResponse } from "next/server";

// Stub for Stripe Checkout. Wire this up in week 4 of the execution plan.
//
// Once you have a Stripe account:
//   1. Create a Product per plan (Starter $199, Pro $499, Agency $1499).
//   2. Capture the price IDs and put them in env.
//   3. Replace the body below with a real stripe.checkout.sessions.create().
export const runtime = "nodejs";

export async function POST(req: Request) {
  const { plan } = (await req.json().catch(() => ({}))) as { plan?: string };
  const urls: Record<string, string> = {
    starter: "https://buy.stripe.com/test_placeholder_starter",
    pro: "https://buy.stripe.com/test_placeholder_pro",
    agency: "https://buy.stripe.com/test_placeholder_agency",
  };
  const url = urls[plan || "pro"];
  if (!url) return NextResponse.json({ error: "unknown plan" }, { status: 400 });
  return NextResponse.json({ url });
}
