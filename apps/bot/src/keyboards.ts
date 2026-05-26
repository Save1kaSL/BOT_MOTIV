import { Markup } from "telegraf";
import type { Offer } from "./types.js";
import { BOT_CALLBACKS } from "@bot-motiv/shared";

export const mainMenuKeyboard = (isAdminUser = false) =>
  Markup.keyboard([
    ["📋 Офферы", "👤 Профиль"],
    ["❓ FAQ", "🤖 AI Помощник"],
    ["🔗 Реферальная ссылка"],
    ...(isAdminUser ? [["🔐 Админ"]] : []),
  ]).resize();

export const offersInlineKeyboard = (offers: Offer[]) =>
  Markup.inlineKeyboard(
    offers.map((o) => [
      Markup.button.callback(`${o.title} — ${o.clientProfit}`, `${BOT_CALLBACKS.OFFER_SELECT}${o.id}`),
    ])
  );

export const offerActionsKeyboard = () =>
  Markup.inlineKeyboard([
    [Markup.button.callback("▶️ Начать шаги", BOT_CALLBACKS.STEP_NEXT)],
    [Markup.button.callback("◀️ К офферам", BOT_CALLBACKS.OFFERS)],
    [Markup.button.callback("🏠 Меню", BOT_CALLBACKS.MAIN_MENU)],
  ]);

export const stepNavigationKeyboard = (hasPrev: boolean, hasNext: boolean) => {
  const row: ReturnType<typeof Markup.button.callback>[] = [];
  if (hasPrev) row.push(Markup.button.callback("⬅️ Назад", BOT_CALLBACKS.STEP_PREV));
  if (hasNext) row.push(Markup.button.callback("✅ Далее", BOT_CALLBACKS.STEP_NEXT));
  return Markup.inlineKeyboard([
    row.length ? row : [Markup.button.callback("✅ Далее", BOT_CALLBACKS.STEP_NEXT)],
    [Markup.button.callback("🤖 AI", BOT_CALLBACKS.AI_HELP)],
    [Markup.button.callback("🏠 Меню", BOT_CALLBACKS.MAIN_MENU)],
  ]);
};

export const faqInlineKeyboard = (items: { id: string; title: string }[]) =>
  Markup.inlineKeyboard(items.map((f) => [Markup.button.callback(f.title, `faq:${f.id}`)]));
