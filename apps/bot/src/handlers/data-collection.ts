import type { Context } from "telegraf";
import { saveStepData } from "../services/lead.service.js";
import { getSession, setSession } from "../session.js";

export function parseFormData(text: string): Record<string, string> | null {
  const fields: Record<string, string> = {};
  const patterns: [RegExp, string][] = [
    [/инн[:\s]+(.+)/i, "inn"],
    [/фио[:\s]+(.+)/i, "fullName"],
    [/телефон[:\s]+(.+)/i, "phone"],
    [/почта[:\s]+(.+)/i, "email"],
    [/email[:\s]+(.+)/i, "email"],
    [/город[:\s]+(.+)/i, "city"],
  ];

  for (const line of text.split("\n")) {
    for (const [regex, key] of patterns) {
      const match = line.match(regex);
      if (match) fields[key] = match[1].trim();
    }
  }

  return Object.keys(fields).length >= 3 ? fields : null;
}

export async function handleDataCollection(ctx: Context, text: string): Promise<boolean> {
  const telegramId = ctx.from?.id;
  if (!telegramId) return false;

  const session = getSession(telegramId);
  if (!session.awaitingData || !session.userId) return false;

  const data = parseFormData(text);
  if (!data) {
    await ctx.reply("Формат:\nИНН: ...\nФИО: ...\nТелефон: ...\nПочта: ...\nГород: ...");
    return true;
  }

  await saveStepData(session.userId, data);
  setSession(telegramId, { awaitingData: false });
  await ctx.reply("✅ Данные сохранены! Админ увидит их в CRM бота.");
  return true;
}
