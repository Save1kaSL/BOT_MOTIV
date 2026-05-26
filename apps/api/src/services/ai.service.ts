import { prisma } from "@bot-motiv/db";
import { config } from "../config.js";
import { logger } from "../lib/logger.js";

const SYSTEM_PROMPT = `Ты — AI-ассистент партнёрской Telegram-программы по банковским офферам.
Отвечай на русском, кратко и по делу.
Помогай пользователям проходить офферы, объясняй шаги, отвечай на FAQ.
Используй только информацию из контекста. Если не знаешь — предложи связаться с менеджером.`;

export async function getAiContext(userId: string): Promise<string> {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: {
      leads: {
        orderBy: { updatedAt: "desc" },
        take: 1,
        include: { offer: true },
      },
    },
  });

  const lead = user?.leads[0];
  const offer = lead?.offer;
  const steps = offer?.steps as { order: number; title: string; content: string }[] | undefined;
  const currentStep = steps?.find((s) => s.order === (lead?.currentStep ?? 0) + 1);

  const kb = await prisma.knowledgeArticle.findMany({
    where: { active: true },
    take: 10,
    orderBy: { updatedAt: "desc" },
  });

  const parts = [
    `Статус лида: ${lead?.status ?? "NEW"}`,
    offer ? `Текущий оффер: ${offer.title}` : "Оффер не выбран",
    currentStep ? `Текущий шаг: ${currentStep.title} — ${currentStep.content}` : "",
    `База знаний:\n${kb.map((k) => `### ${k.title}\n${k.content}`).join("\n\n")}`,
  ];

  return parts.filter(Boolean).join("\n\n");
}

export async function chatWithAi(userId: string, message: string): Promise<string> {
  const context = await getAiContext(userId);

  await prisma.aiMessage.create({
    data: { userId, role: "user", content: message },
  });

  const history = await prisma.aiMessage.findMany({
    where: { userId },
    orderBy: { createdAt: "desc" },
    take: 10,
  });

  const messages = [
    { role: "system", content: `${SYSTEM_PROMPT}\n\n--- КОНТЕКСТ ---\n${context}` },
    ...history.reverse().map((m) => ({ role: m.role, content: m.content })),
  ];

  let reply: string;

  if (config.ai.provider === "openrouter" && config.ai.openrouterKey) {
    reply = await callOpenRouter(messages);
  } else if (config.ai.openaiKey) {
    reply = await callOpenAI(messages);
  } else {
    reply =
      "AI временно недоступен. Используйте меню FAQ или напишите менеджеру. " +
      "Для включения AI добавьте OPENROUTER_API_KEY или OPENAI_API_KEY.";
  }

  await prisma.aiMessage.create({
    data: { userId, role: "assistant", content: reply },
  });

  return reply;
}

async function callOpenRouter(messages: { role: string; content: string }[]): Promise<string> {
  const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.ai.openrouterKey}`,
      "Content-Type": "application/json",
      "HTTP-Referer": "https://bot-motiv.app",
      "X-Title": "BOT MOTIV",
    },
    body: JSON.stringify({
      model: config.ai.openrouterModel,
      messages,
      max_tokens: 800,
      temperature: 0.7,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    logger.error({ err }, "OpenRouter error");
    throw new Error("AI request failed");
  }

  const data = (await res.json()) as { choices: { message: { content: string } }[] };
  return data.choices[0]?.message?.content ?? "Не удалось получить ответ.";
}

async function callOpenAI(messages: { role: string; content: string }[]): Promise<string> {
  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.ai.openaiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: config.ai.openaiModel,
      messages,
      max_tokens: 800,
      temperature: 0.7,
    }),
  });

  if (!res.ok) {
    logger.error("OpenAI error");
    throw new Error("AI request failed");
  }

  const data = (await res.json()) as { choices: { message: { content: string } }[] };
  return data.choices[0]?.message?.content ?? "Не удалось получить ответ.";
}
