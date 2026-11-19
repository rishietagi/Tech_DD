import { redirect } from "next/navigation";

import { engagementsApi } from "@/lib/api/engagements";

// Creates an engagement, so it must run per request — never be prerendered. Without this a
// production build calls the API at build time (found packaging for the laptop, 2026-11-19).
export const dynamic = "force-dynamic";

export default async function NewIntakePage() {
  const engagement = await engagementsApi.create("Untitled Engagement");
  redirect(`/intake/${engagement.id}/context`);
}
