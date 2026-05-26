"use client";

import { useEffect, useState } from "react";
import { AdminLayout } from "@/components/AdminLayout";
import { apiFetch } from "@/lib/api";

type Offer = {
  id: string;
  slug: string;
  title: string;
  description: string;
  ourProfit: string;
  clientProfit: string;
  active: boolean;
  tags: string[];
  steps: { order: number; title: string }[];
};

export default function OffersPage() {
  const [offers, setOffers] = useState<Offer[]>([]);

  useEffect(() => {
    apiFetch<Offer[]>("/admin/offers").then(setOffers).catch(console.error);
  }, []);

  const toggleActive = async (offer: Offer) => {
    await apiFetch(`/admin/offers/${offer.id}`, {
      method: "PATCH",
      body: JSON.stringify({ active: !offer.active }),
    });
    const updated = await apiFetch<Offer[]>("/admin/offers");
    setOffers(updated);
  };

  return (
    <AdminLayout>
      <h1 style={{ fontSize: 28, marginBottom: 24 }}>Офферы</h1>
      <section style={{ display: "grid", gap: 16 }}>
        {offers.map((offer) => (
          <article key={offer.id} className="card">
            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <section>
                <h2 style={{ fontSize: 20 }}>{offer.title}</h2>
                <p style={{ color: "var(--muted)", fontSize: 13 }}>{offer.slug}</p>
              </section>
              <button className="btn btn-ghost" onClick={() => toggleActive(offer)}>
                {offer.active ? "✅ Активен" : "⛔ Неактивен"}
              </button>
            </header>
            <p style={{ margin: "12px 0" }}>{offer.description}</p>
            <p>
              <strong>Наш профит:</strong> {offer.ourProfit} &nbsp;|&nbsp;
              <strong>Выплата клиенту:</strong> {offer.clientProfit}
            </p>
            <p style={{ marginTop: 8, fontSize: 13, color: "var(--muted)" }}>
              Шаги: {offer.steps.length} | Теги: {offer.tags.join(", ")}
            </p>
          </article>
        ))}
      </section>
    </AdminLayout>
  );
}
