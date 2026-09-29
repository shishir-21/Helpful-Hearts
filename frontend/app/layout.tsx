import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Helpful Hearts",
  description: "Find doctors and manage appointments with Helpful Hearts.",
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
