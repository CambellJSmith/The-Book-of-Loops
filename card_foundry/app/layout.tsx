import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "card_foundry — monster card editor",
  description: "Create original trading cards with custom artwork, five types, and high-resolution PNG exports.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">{children}</body>
    </html>
  );
}
