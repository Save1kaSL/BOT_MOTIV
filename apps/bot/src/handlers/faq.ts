import type { Context } from "telegraf";
import { getFaqArticles } from "../services/offer.service.js";
import { faqInlineKeyboard } from "../keyboards.js";
import { md } from "../lib/format.js";

export async function showFaq(ctx: Context) {
  const items = await getFaqArticles();
  if (!items.length) {
    await ctx.reply("FAQ пуст.");
    return;
  }
  await ctx.replyWithMarkdown("❓ *FAQ:*", faqInlineKeyboard(items));
}

export function registerFaqCallbacks(bot: import("telegraf").Telegraf<Context>) {
  bot.action(/^faq:(.+)$/, async (ctx) => {
    await ctx.answerCbQuery();
    const items = await getFaqArticles();
    const item = items.find((f) => f.id === ctx.match[1]);
    if (item) await ctx.replyWithMarkdown(`*${md(item.title)}*\n\n${md(item.content)}`);
  });
}
