import { Telegraf } from "telegraf";
import { config, isAdmin } from "./config.js";
import { rateLimitMiddleware } from "./middleware/rate-limit.js";
import { handleStart } from "./handlers/start.js";
import { showOffers, registerOfferCallbacks } from "./handlers/offers.js";
import { showProfile, showReferral } from "./handlers/profile.js";
import { showFaq, registerFaqCallbacks } from "./handlers/faq.js";
import { enableAiMode, handleAiMessage, registerAiCallbacks } from "./handlers/ai.js";
import { handleDataCollection } from "./handlers/data-collection.js";
import { registerAdminHandlers } from "./handlers/admin.js";
import { getSession, clearAiMode } from "./session.js";
import { mainMenuKeyboard } from "./keyboards.js";
import pino from "pino";

const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });

if (!config.botToken) {
  logger.error("TELEGRAM_BOT_TOKEN is required");
  process.exit(1);
}

if (!config.adminTelegramIds.length) {
  logger.warn("ADMIN_TELEGRAM_IDS пуст — админ-панель в боте недоступна");
}

const bot = new Telegraf(config.botToken);

bot.use(rateLimitMiddleware);

bot.start(async (ctx) => {
  (ctx as typeof ctx & { startPayload?: string }).startPayload = ctx.startPayload;
  await handleStart(ctx);
});

bot.command("menu", async (ctx) => {
  if (ctx.from) clearAiMode(ctx.from.id);
  await ctx.reply("🏠 Главное меню", mainMenuKeyboard(ctx.from ? isAdmin(ctx.from.id) : false));
});

bot.command("offers", showOffers);
bot.hears("📋 Офферы", showOffers);
bot.hears("👤 Профиль", showProfile);
bot.hears("❓ FAQ", showFaq);
bot.hears("🤖 AI Помощник", enableAiMode);
bot.hears("🔗 Реферальная ссылка", showReferral);

registerOfferCallbacks(bot);
registerFaqCallbacks(bot);
registerAiCallbacks(bot);
registerAdminHandlers(bot);

bot.on("text", async (ctx) => {
  if (!ctx.message || !("text" in ctx.message)) return;
  const text = ctx.message.text;
  const telegramId = ctx.from?.id;
  if (!telegramId) return;

  // не перехватывать команды (/offers и т.д.)
  if (text.startsWith("/")) return;

  if (await handleDataCollection(ctx, text)) return;

  const session = getSession(telegramId);
  if (session.aiMode) {
    await handleAiMessage(ctx, text);
    return;
  }

  await ctx.reply("Используй меню или /menu");
});

bot.catch((err, ctx) => {
  logger.error({ err }, "Bot error");
  ctx.reply("Ошибка. Попробуй /start").catch(() => undefined);
});

bot.launch().then(() => {
  logger.info("🤖 Bot started (DB direct, no API)");
});

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
