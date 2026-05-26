import type { Context, MiddlewareFn } from "telegraf";
import { config } from "../config.js";

const buckets = new Map<number, { count: number; resetAt: number }>();

export const rateLimitMiddleware: MiddlewareFn<Context> = async (ctx, next) => {
  const userId = ctx.from?.id;
  if (!userId) return next();

  const now = Date.now();
  let bucket = buckets.get(userId);

  if (!bucket || now > bucket.resetAt) {
    bucket = { count: 0, resetAt: now + config.rateLimitWindowMs };
    buckets.set(userId, bucket);
  }

  bucket.count++;
  if (bucket.count > config.rateLimitMax) {
    await ctx.reply("⚠️ Слишком много запросов. Подождите минуту.");
    return;
  }

  return next();
};

// Cleanup old buckets every 5 min
setInterval(() => {
  const now = Date.now();
  for (const [id, b] of buckets) {
    if (now > b.resetAt) buckets.delete(id);
  }
}, 300_000);
