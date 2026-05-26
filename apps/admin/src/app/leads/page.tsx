"use client";

import { useEffect, useState } from "react";
import { AdminLayout } from "@/components/AdminLayout";
import { apiFetch } from "@/lib/api";

type Lead = {
  id: string;
  status: string;
  currentStep: number;
  createdAt: string;
  user: { firstName?: string; username?: string; telegramId: string; referralCode: string };
  offer?: { title: string } | null;
};

const STATUSES = ["NEW", "OFFER_SELECTED", "IN_PROGRESS", "WAITING_MEETING", "COMPLETED", "APPROVED", "PAID", "REJECTED"];

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [filter, setFilter] = useState("");

  const load = () => {
    const q = filter ? `?status=${filter}` : "";
    apiFetch<{ items: Lead[] }>(`/admin/leads${q}`).then((d) => setLeads(d.items)).catch(console.error);
  };

  useEffect(() => {
    load();
  }, [filter]);

  const updateStatus = async (id: string, status: string) => {
    await apiFetch(`/admin/leads/${id}/status`, {
      method: "POST",
      body: JSON.stringify({ status }),
    });
    load();
  };

  return (
    <AdminLayout>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 style={{ fontSize: 28 }}>Лиды</h1>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} style={{ width: 200 }}>
          <option value="">Все статусы</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </header>
      <article className="card" style={{ overflow: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Пользователь</th>
              <th>Оффер</th>
              <th>Статус</th>
              <th>Шаг</th>
              <th>Дата</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id}>
                <td>
                  {lead.user.firstName ?? lead.user.username ?? lead.user.telegramId}
                  <br />
                  <small style={{ color: "var(--muted)" }}>{lead.user.referralCode}</small>
                </td>
                <td>{lead.offer?.title ?? "—"}</td>
                <td><span className={`badge badge-${badgeClass(lead.status)}`}>{lead.status}</span></td>
                <td>{lead.currentStep}</td>
                <td>{new Date(lead.createdAt).toLocaleDateString("ru")}</td>
                <td>
                  <select
                    defaultValue={lead.status}
                    onChange={(e) => updateStatus(lead.id, e.target.value)}
                    style={{ width: 140, padding: 6 }}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </AdminLayout>
  );
}

function badgeClass(status: string) {
  if (status === "NEW") return "new";
  if (["PAID", "APPROVED", "COMPLETED"].includes(status)) return "done";
  if (status === "REJECTED") return "rejected";
  return "progress";
}
