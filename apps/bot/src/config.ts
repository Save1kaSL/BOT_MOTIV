import "dotenv/config";

function parseAdminIds(): number[] {
  const raw = process.env.ADMIN_TELEGRAM_IDS ?? "";
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .map(Number)
    .filter((n) => !Number.isNaN(n));
}

function cleanEnv(value: string | undefined): string {
  return (value ?? "").trim().replace(/^['"]|['"]$/g, "");
}

export const config = {
  botToken: cleanEnv(process.env.TELEGRAM_BOT_TOKEN),
  botUsername: cleanEnv(process.env.TELEGRAM_BOT_USERNAME).replace(/^@/, "") || "bot",
  adminTelegramIds: parseAdminIds(),
  rateLimitMax: parseInt(process.env.BOT_RATE_LIMIT_MAX ?? "20", 10),
  rateLimitWindowMs: 60_000,
  ai: {
    provider: (process.env.AI_PROVIDER ?? "openrouter") as "openrouter" | "openai",
    openrouterKey: process.env.OPENROUTER_API_KEY ?? "",
    openrouterModel: process.env.OPENROUTER_MODEL ?? "openai/gpt-4o-mini",
    openaiKey: process.env.OPENAI_API_KEY ?? "",
    openaiModel: process.env.OPENAI_MODEL ?? "gpt-4o-mini",
  },
};

export function isAdmin(telegramId: number): boolean {
  return config.adminTelegramIds.includes(telegramId);
}
