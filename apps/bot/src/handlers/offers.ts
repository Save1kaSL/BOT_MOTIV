import type { Context } from "telegraf";
import { getActiveOffers } from "../services/offer.service.js";
import { selectOffer, advanceStep, goBackStep } from "../services/lead.service.js";
import { findOrCreateUser } from "../services/user.service.js";
import { offersInlineKeyboard, offerActionsKeyboard, stepNavigationKeyboard } from "../keyboards.js";
import { getSession, setSession } from "../session.js";
import { BOT_CALLBACKS } from "@bot-motiv/shared";
import type { Offer } from "../types.js";
import { md, mdUrl } from "../lib/format.js";

export async function showOffers(ctx: Context) {
  const offers = await getActiveOffers();
  if (!offers.length) {
    await ctx.reply("Сейчас нет активных офферов.");
    return;
  }

  let text = "📋 *Доступные офферы:*\n\n";
  for (const o of offers) {
    text += `*${md(o.title)}*\n💵 ${md(o.clientProfit)} | 📊 ${(o.steps as unknown[]).length} шагов\n\n`;
  }
  text += "Выбери оффер:";

  const kb = offersInlineKeyboard(offers as unknown as Offer[]);
  if (ctx.callbackQuery) {
    await ctx.editMessageText(text, { parse_mode: "Markdown", ...kb });
  } else {
    await ctx.replyWithMarkdown(text, kb);
  }
}

export async function selectOfferHandler(ctx: Context, offerId: string) {
  const telegramId = ctx.from?.id;
  if (!telegramId) return;

  const session = getSession(telegramId);
  if (!session.userId) {
    await ctx.answerCbQuery("Сначала /start");
    return;
  }

  const lead = await selectOffer(session.userId, offerId);
  const offer = lead.offer as unknown as Offer | null;
  if (!offer) return;

  const user = await findOrCreateUser({ telegramId: BigInt(telegramId) });
  const personalLink = offer.referralLink.replace("{ref}", user.referralCode);

  const text =
    `✅ *${md(offer.title)}*\n\n${md(offer.description)}\n\n` +
    `💰 Выплата: *${md(offer.clientProfit)}*\n🔗 ${mdUrl(personalLink)}\n\n` +
    `Нажми «Начать шаги»`;

  await ctx.editMessageText(text, { parse_mode: "Markdown", ...offerActionsKeyboard() });
}

export async function renderStep(ctx: Context, offer: Offer, stepIndex: number, edit = true) {
  const steps = [...offer.steps].sort((a, b) => a.order - b.order);
  const step = steps[stepIndex - 1] ?? steps[0];
  if (!step) {
    await ctx.reply("Все шаги пройдены! Ожидай подтверждения.");
    return;
  }

  let text = `📌 *Шаг ${stepIndex}/${steps.length}: ${md(step.title)}*\n\n${md(step.content)}`;
  if (step.collectData?.length) {
    text += `\n\n📝 Отправь:\nИНН / ФИО / Телефон / Почта / Город`;
    if (ctx.from) setSession(ctx.from.id, { awaitingData: true });
  }

  const kb = stepNavigationKeyboard(stepIndex > 1, stepIndex < steps.length);
  if (edit && ctx.callbackQuery) {
    await ctx.editMessageText(text, { parse_mode: "Markdown", ...kb });
  } else {
    await ctx.replyWithMarkdown(text, kb);
  }
}

export function registerOfferCallbacks(bot: import("telegraf").Telegraf<Context>) {
  bot.action(BOT_CALLBACKS.OFFERS, async (ctx) => {
    await ctx.answerCbQuery();
    await showOffers(ctx);
  });

  bot.action(/^offer:(.+)$/, async (ctx) => {
    await ctx.answerCbQuery();
    await selectOfferHandler(ctx, ctx.match[1]);
  });

  bot.action(BOT_CALLBACKS.STEP_PREV, async (ctx) => {
    await ctx.answerCbQuery();
    const session = getSession(ctx.from!.id);
    if (!session.userId) return;
    const lead = await goBackStep(session.userId);
    if (lead.offer) await renderStep(ctx, lead.offer as unknown as Offer, Math.max(1, lead.currentStep), true);
  });

  bot.action(BOT_CALLBACKS.STEP_NEXT, async (ctx) => {
    await ctx.answerCbQuery();
    const session = getSession(ctx.from!.id);
    if (!session.userId) return;
    const lead = await advanceStep(session.userId);
    if (lead.offer) await renderStep(ctx, lead.offer as unknown as Offer, lead.currentStep, true);
  });

  bot.action(BOT_CALLBACKS.MAIN_MENU, async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.deleteMessage().catch(() => undefined);
    const { mainMenuKeyboard } = await import("../keyboards.js");
    const { isAdmin } = await import("../config.js");
    await ctx.reply("🏠 Главное меню", mainMenuKeyboard(isAdmin(ctx.from!.id)));
  });
}
