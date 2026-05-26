"use client";

import { useEffect, useState } from "react";
import { AdminLayout } from "@/components/AdminLayout";
import { apiFetch } from "@/lib/api";

type Analytics = {
  totalUsers: number;
  totalLeads: number;
  leadsByStatus: Record<string, number>;
  totalPayments: number;
  totalReferrals: number;
};

const STATUS_LABELS: Record<string, string> = {
  NEW: "Новые",
  OFFER_SELECTED: "Оффер выбран",
  IN_PROGRESS: "В процессе",
  WAITING_MEETING: "Ожидание встречи",
  COMPLETED: "Завершены",
  APPROVED: "Одобрены",
  PAID: "Выплачены",
  REJECTED: "Отклонены",
};

export default function DashboardPage() {
  const [data, setData] = useState<Analytics | null>(null);

  useEffect(() => {
    apiFetch<Analytics>("/admin/analytics").then(setData).catch(console.error);
  }, []);

  const gridStyle = { display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 32 } as const;

  return (
    <AdminLayout>
      <h1 style={{ fontSize: 28, marginBottom: 24 }}>Дашборд</h1>
      <section style={gridStyle}>
        <StatCard label="Пользователи" value={data?.totalUsers ?? "—"} />
        <StatCard label="Лиды" value={data?.totalLeads ?? "—"} />
        <StatCard label="Рефералы" value={data?.totalReferrals ?? "—"} />
        <StatCard label="Выплаты (₽)" value={data?.totalPayments ?? "—"} />
      </section>
      {data?.leadsByStatus && (
        <article className="card">
          <h2 style={{ marginBottom: 16 }}>Лиды по статусам</h2>
          <section style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
            {Object.entries(data.leadsByStatus).map(([status, count]) => (
              <article key={status} style={{ padding: 12, background: "var(--bg)", borderRadius: 8 }}>
                <p style={{ fontSize: 12, color: "var(--muted)" }}>{STATUS_LABELS[status] ?? status}</p>
                <p style={{ fontSize: 24, fontWeight: 700 }}>{count}</p>
              </article>
            ))}
          </section>
        </article>
      )}
    </AdminLayout>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <article className="card">
      <p style={{ fontSize: 12, color: "var(--muted)", marginBottom: 8 }}>{label}</p>
      <p style={{ fontSize: 32, fontWeight: 700 }}>{value}</p>
    </article>
  );
}
