import { redirect } from "next/navigation";

import { engagementsApi } from "@/lib/api/engagements";

export default async function NewIntakePage() {
  const engagement = await engagementsApi.create("Untitled Engagement");
  redirect(`/intake/${engagement.id}/context`);
}
