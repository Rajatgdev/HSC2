import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HS Ledger — TARIC Classifier",
  description: "Grounded 10-digit EU commodity code classification (CN 2026 + EBTI).",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Spectral:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
