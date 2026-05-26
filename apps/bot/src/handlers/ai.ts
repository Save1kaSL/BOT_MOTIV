import type { Context } from "telegraf";
import { chatWithAi } from "../services/ai.service.js";
import { getSession, setSession } from "../session.js";
import { BOT_CALLBACKS } from "@bot-motiv/shared";

export async function enableAiMode(ctx: Context) {
  const telegramId = ctx.from?.id;
  if (!telegramId) return;

  const session = getSession(telegramId);
  if (!session.userId) {
    await ctx.reply("Нажми /start");
    return;
  }

  setSession(telegramId, { aiMode: true });
  await ctx.reply("🤖 AI активен. Пиши вопрос. Выход: /menu");
}

export async function handleAiMessage(ctx: Context, message: string) {
  const session = getSession(ctx.from!.id);
  if (!session.userId) return;

  const thinking = await ctx.reply("🤖 Думаю...");
  try {
    const reply = await chatWithAi(session.userId, message);
    await ctx.telegram.editMessageText(ctx.chat!.id, thinking.message_id, undefined, reply.slice(0, 4000));
  } catch {
    await ctx.telegram.editMessageText(ctx.chat!.id, thinking.message_id, undefined, "Ошибка AI");
  }
}

export function registerAiCallbacks(bot: import("telegraf").Telegraf<Context>) {
  bot.action(BOT_CALLBACKS.AI_HELP, async (ctx) => {
    await ctx.answerCbQuery();
    await enableAiMode(ctx);
  });
}
