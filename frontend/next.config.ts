import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // A self-contained server (`.next/standalone/server.js`) for running the app on a machine
  // with Node but no `npm install` — the laptop package (2026-11-19). Harmless in dev.
  output: "standalone",
  // The packaging build writes to its own folder so it never collides with a running
  // `next dev` (NEXT_DIST_DIR=.next-laptop).
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

export default nextConfig;
