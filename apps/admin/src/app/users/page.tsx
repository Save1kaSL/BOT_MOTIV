"use client";

import { useEffect, useState } from "react";
import { AdminLayout } from "@/components/AdminLayout";
import { apiFetch } from "@/lib/api";

type User = {
  id: string;
  telegramId: string;
  username?: string;
  firstName?: string;
  referralCode: string;
  trafficSource?: string;
  createdAt: string;
  _count: { referrals: number; leads: number };
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    apiFetch<{ items: User[] }>("/admin/users").then((d) => setUsers(d.items)).catch(console.error);
  }, []);

  return (
    <AdminLayout>
      <h1 style={{ fontSize: 28, marginBottom: 24 }}>Пользователи</h1>
      <article className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Имя</th>
              <th>Telegram ID</th>
              <th>Реф. код</th>
              <th>Источник</th>
              <th>Рефералы</th>
              <th>Лиды</th>
              <th>Регистрация</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.firstName ?? u.username ?? "—"}</td>
                <td>{u.telegramId}</td>
                <td><code>{u.referralCode}</code></td>
                <td>{u.trafficSource ?? "—"}</td>
                <td>{u._count.referrals}</td>
                <td>{u._count.leads}</td>
                <td>{new Date(u.createdAt).toLocaleDateString("ru")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </AdminLayout>
  );
}
