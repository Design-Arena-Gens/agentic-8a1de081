import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Trading Data Platform",
  description: "Yahoo Finance Trading Analysis Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
