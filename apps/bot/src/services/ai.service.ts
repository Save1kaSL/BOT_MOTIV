import { prisma } from "@bot-motiv/db";
import { config } from "../config.js";

const SYSTEM_PROMPT = `Ты — AI-ассистент партнёрской Telegram-программы по банковским офферам.
Отвечай на русском, кратко и по делу.`;

export async function chatWithAi(userId: string, message: string): Promise<string> {
  const kb = await prisma.knowledgeArticle.findMany({ where: { active: true }, take: 8 });
  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: { leads: { orderBy: { updatedAt: "desc" }, take: 1, include: { offer: true } } },
  });
  const lead = user?.leads[0];

  const context = [
    lead ? `Статус: ${lead.status}, оффер: ${lead.offer?.title ?? "—"}, шаг: ${lead.currentStep}` : "",
    kb.map((k) => `${k.title}: ${k.content}`).join("\n"),
  ].join("\n");

  await prisma.aiMessage.create({ data: { userId, role: "user", content: message } });

  if (!config.ai.openrouterKey && !config.ai.openaiKey) {
    return "AI не настроен. Добавь OPENROUTER_API_KEY или OPENAI_API_KEY в .env";
  }

  const messages = [
    { role: "system", content: `${SYSTEM_PROMPT}\n\n${context}` },
    { role: "user", content: message },
  ];

  let reply: string;
  if (config.ai.provider === "openrouter" && config.ai.openrouterKey) {
    const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${config.ai.openrouterKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model: config.ai.openrouterModel, messages, max_tokens: 600 }),
    });
    const data = (await res.json()) as { choices: { message: { content: string } }[] };
    reply = data.choices[0]?.message?.content ?? "Нет ответа";
  } else {
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${config.ai.openaiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model: config.ai.openaiModel, messages, max_tokens: 600 }),
    });
    const data = (await res.json()) as { choices: { message: { content: string } }[] };
    reply = data.choices[0]?.message?.content ?? "Нет ответа";
  }

  await prisma.aiMessage.create({ data: { userId, role: "assistant", content: reply } });
  return reply;
}
