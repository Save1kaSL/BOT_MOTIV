import "dotenv/config";

function required(key: string): string {
  const val = process.env[key];
  if (!val) throw new Error(`Missing env: ${key}`);
  return val;
}

export const config = {
  port: parseInt(process.env.API_PORT ?? "3001", 10),
  nodeEnv: process.env.NODE_ENV ?? "development",
  jwtSecret: process.env.JWT_SECRET ?? "dev-secret-change-in-production",
  adminEmail: process.env.ADMIN_EMAIL ?? "admin@example.com",
  botToken: process.env.TELEGRAM_BOT_TOKEN ?? "",
  botUsername: process.env.TELEGRAM_BOT_USERNAME ?? "bot",
  ai: {
    provider: (process.env.AI_PROVIDER ?? "openrouter") as "openrouter" | "openai",
    openrouterKey: process.env.OPENROUTER_API_KEY ?? "",
    openrouterModel: process.env.OPENROUTER_MODEL ?? "openai/gpt-4o-mini",
    openaiKey: process.env.OPENAI_API_KEY ?? "",
    openaiModel: process.env.OPENAI_MODEL ?? "gpt-4o-mini",
  },
  rateLimit: {
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS ?? "60000", 10),
    max: parseInt(process.env.RATE_LIMIT_MAX ?? "100", 10),
  },
};
