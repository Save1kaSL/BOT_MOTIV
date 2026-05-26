import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BOT MOTIV — Admin",
  description: "CRM панель партнёрской программы",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
