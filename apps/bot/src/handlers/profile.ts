import type { Context } from "telegraf";
import { findOrCreateUser } from "../services/user.service.js";
import { getSession } from "../session.js";
import { config } from "../config.js";
import { buildReferralLink, LEAD_STATUS_LABELS } from "@bot-motiv/shared";
import { md, mdUrl } from "../lib/format.js";

export async function showProfile(ctx: Context) {
  const telegramId = ctx.from?.id;
  if (!telegramId) return;

  const session = getSession(telegramId);
  if (!session.userId) {
    await ctx.reply("Нажми /start");
    return;
  }

  const user = await findOrCreateUser({ telegramId: BigInt(telegramId) });
  const lead = user.leads[0];

  let text = `👤 *Профиль*\n\n🔑 Код: \`${user.referralCode}\`\n👥 Рефералов: ${user._count.referrals}\n`;
  if (lead) {
    text += `\n📋 ${md(LEAD_STATUS_LABELS[lead.status] ?? lead.status)}\n`;
    if (lead.offer) text += `🎯 ${md(lead.offer.title)}\n📍 Шаг ${lead.currentStep}\n`;
  }

  await ctx.replyWithMarkdown(text);
}

export async function showReferral(ctx: Context) {
  const telegramId = ctx.from?.id;
  if (!telegramId) return;

  const user = await findOrCreateUser({ telegramId: BigInt(telegramId) });
  const link = buildReferralLink(config.botUsername, user.referralCode);

  await ctx.replyWithMarkdown(
    `🔗 *Реферальная ссылка*\n\n${mdUrl(link)}\n\n👥 Приглашено: ${user._count.referrals}`
  );
}
