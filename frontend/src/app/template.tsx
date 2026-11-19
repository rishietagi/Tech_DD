/**
 * Re-mounted on every navigation (unlike a layout), so each screen eases in. The sidebar
 * lives in the layout and stays put. Reduced-motion users get no animation (globals.css).
 */
export default function Template({ children }: { children: React.ReactNode }) {
  return <div className="animate-page-in">{children}</div>;
}
