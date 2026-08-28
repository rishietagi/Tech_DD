import { IntakeShell } from "@/components/intake/intake-shell";

export default async function IntakeLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <IntakeShell engagementId={id}>{children}</IntakeShell>;
}
