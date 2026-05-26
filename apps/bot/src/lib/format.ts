import { escapeMarkdown } from "@bot-motiv/shared";

/** Экранирует текст пользователя/из БД для Telegram Markdown */
export function md(text: string | null | undefined): string {
  if (!text) return "";
  return escapeMarkdown(text);
}

/** Ссылка в моноширинном блоке — без поломки из‑за _ в ref_код */
export function mdUrl(url: string): string {
  return `\`${url.replace(/`/g, "'")}\``;
}
