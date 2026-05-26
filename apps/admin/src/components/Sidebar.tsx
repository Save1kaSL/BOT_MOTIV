"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const links = [
  { href: "/dashboard", label: "📊 Дашборд" },
  { href: "/leads", label: "👥 Лиды" },
  { href: "/offers", label: "📋 Офферы" },
  { href: "/users", label: "🧑 Пользователи" },
  { href: "/broadcast", label: "📢 Рассылка" },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const logout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  return (
    <aside
      style={{
        width: 240,
        minHeight: "100vh",
        background: "var(--surface)",
        borderRight: "1px solid var(--border)",
        padding: "24px 16px",
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 24, padding: "0 8px" }}>
        BOT MOTIV
      </div>
      {links.map((l) => (
        <Link
          key={l.href}
          href={l.href}
          style={{
            padding: "10px 12px",
            borderRadius: 8,
            color: pathname === l.href ? "white" : "var(--muted)",
            background: pathname === l.href ? "var(--accent)" : "transparent",
          }}
        >
          {l.label}
        </Link>
      ))}
      <button
        className="btn btn-ghost"
        style={{ marginTop: "auto" }}
        onClick={logout}
      >
        Выйти
      </button>
    </aside>
  );
}
