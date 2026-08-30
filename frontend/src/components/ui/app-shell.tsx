"use client";

import { useEffect, useState } from "react";

import { SidebarNav } from "@/components/ui/sidebar-nav";
import { SiteFooter } from "@/components/ui/site-footer";
import { WelcomeScreen } from "@/components/ui/welcome-screen";

const STORAGE_KEY = "techdd.welcome-seen";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [welcomeSeen, setWelcomeSeen] = useState<boolean | null>(null);

  useEffect(() => {
    let seen = false;
    try {
      seen = window.sessionStorage.getItem(STORAGE_KEY) === "1";
    } catch {
      seen = false;
    }
    setWelcomeSeen(seen);
  }, []);

  const dismiss = () => {
    try {
      window.sessionStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // sessionStorage unavailable — the welcome screen just reappears next load.
    }
    setWelcomeSeen(true);
  };

  if (welcomeSeen === null) {
    return <div className="min-h-screen bg-paper" />;
  }

  if (!welcomeSeen) {
    return <WelcomeScreen onContinue={dismiss} />;
  }

  return (
    <div className="flex min-h-screen">
      <SidebarNav />
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex-1">{children}</div>
        <SiteFooter />
      </div>
    </div>
  );
}
