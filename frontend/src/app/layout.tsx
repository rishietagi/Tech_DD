import type { Metadata } from "next";
import { IBM_Plex_Mono, Inter, Inter_Tight } from "next/font/google";

import { AppShell } from "@/components/ui/app-shell";
import { ToastProvider } from "@/components/ui/toast";
import { QueryProvider } from "@/components/providers/query-provider";

import "./globals.css";

/*
 * Type (Rishi, 2026-11-19): a Helvetica-style neo-grotesque throughout. Helvetica itself is
 * licensed and absent on Windows (which silently swaps in Arial), so the app serves Inter
 * for text and Inter Tight for headings — the closest open faces, identical on every
 * machine. Plex Mono is kept only for code (the AI skills page).
 */
const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const interTight = Inter_Tight({
  variable: "--font-inter-tight",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "KPMG Tech Diligence Tool",
  description: "Technology due diligence intake and scoping platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} ${interTight.variable} ${plexMono.variable} antialiased`}
      >
        <QueryProvider>
          <ToastProvider>
            <AppShell>{children}</AppShell>
          </ToastProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
