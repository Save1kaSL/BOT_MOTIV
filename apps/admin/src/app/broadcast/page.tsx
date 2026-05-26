"use client";

import { useState } from "react";
import { AdminLayout } from "@/components/AdminLayout";
import { apiFetch } from "@/lib/api";

export default function BroadcastPage() {
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<{ sent: number; failed: number } | null>(null);
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!message.trim()) return;
    setLoading(true);
    try {
      const res = await apiFetch<{ sent: number; failed: number }>("/admin/broadcast", {
        method: "POST",
        body: JSON.stringify({ message }),
      });
      setResult(res);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AdminLayout>
      <h1 style={{ fontSize: 28, marginBottom: 24 }}>Массовая рассылка</h1>
      <article className="card" style={{ maxWidth: 600 }}>
        <p style={{ color: "var(--muted)", marginBottom: 16 }}>
          Сообщение будет отправлено всем активным пользователям бота.
        </p>
        <textarea
          rows={6}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Текст сообщения (Markdown)"
          style={{ marginBottom: 16 }}
        />
        <button className="btn btn-primary" onClick={send} disabled={loading}>
          {loading ? "Отправка..." : "Отправить"}
        </button>
        {result && (
          <p style={{ marginTop: 16, color: "var(--success)" }}>
            Отправлено: {result.sent}, ошибок: {result.failed}
          </p>
        )}
      </article>
    </AdminLayout>
  );
}
