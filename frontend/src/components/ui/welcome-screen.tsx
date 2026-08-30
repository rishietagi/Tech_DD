"use client";

import Image from "next/image";

export function WelcomeScreen({ onContinue }: { onContinue: () => void }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-paper px-8 py-20 text-center">
      <Image
        src="/kpmg-logo.png"
        alt="KPMG"
        width={751}
        height={332}
        priority
        className="mb-12 h-auto w-[168px]"
      />
      <h1 className="mb-4 max-w-[24ch] font-display text-[clamp(28px,4vw,40px)] leading-[1.2] font-semibold text-text">
        Welcome to KPMG Tech Diligence Tool
      </h1>
      <p className="mb-10 max-w-[48ch] font-sans text-[16px] leading-[1.6] text-muted">
        A one-stop solution for all your diligence work.
      </p>
      <button
        type="button"
        onClick={onContinue}
        className="rounded-full bg-kpmg-blue px-9 py-3.5 font-sans text-[14px] font-medium text-white transition-colors hover:bg-kpmg-blue-dark"
      >
        Continue
      </button>
    </div>
  );
}
