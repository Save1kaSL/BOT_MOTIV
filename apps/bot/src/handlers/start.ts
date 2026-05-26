import type { Context } from "telegraf";
import { findOrCreateUser } from "../services/user.service.js";
import { mainMenuKeyboard } from "../keyboards.js";
import { setSession } from "../session.js";
import { config, isAdmin } from "../config.js";
import { buildReferralLink } from "@bot-motiv/shared";
import { md, mdUrl } from "../lib/format.js";

export async function handleStart(ctx: Context) {
  if (!ctx.from) return;

  const payload =
    (ctx as Context & { startPayload?: string }).startPayload ??
    (ctx.message && "text" in ctx.message ? ctx.message.text.split(" ")[1] : undefined);

  const user = await findOrCreateUser({
    telegramId: BigInt(ctx.from.id),
    username: ctx.from.username,
    firstName: ctx.from.first_name,
    lastName: ctx.from.last_name,
    startPayload: payload,
  });

  setSession(ctx.from.id, { userId: user.id });

  let welcomeText = `👋 Привет, ${md(ctx.from.first_name ?? "друг")}!\n\n`;
  welcomeText += `Добро пожаловать в партнёрскую программу.\n\n`;
  welcomeText += `💰 *Как зарабатывать:*\n`;
  welcomeText += `1. Выбери оффер в меню «Офферы»\n`;
  welcomeText += `2. Получи персональную ссылку\n`;
  welcomeText += `3. Выполни шаги по инструкции\n`;
  welcomeText += `4. Получи выплату на карту\n\n`;
  welcomeText += `🔗 Твоя реферальная ссылка:\n`;
  welcomeText += mdUrl(buildReferralLink(config.botUsername, user.referralCode));

  if (isAdmin(ctx.from.id)) {
    welcomeText += `\n\n🔐 Ты админ — /admin или кнопка «Админ»`;
  }

  await ctx.replyWithMarkdown(welcomeText, mainMenuKeyboard(isAdmin(ctx.from.id)));
}
