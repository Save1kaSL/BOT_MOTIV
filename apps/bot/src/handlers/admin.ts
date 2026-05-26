import type { Context } from "telegraf";
import { Markup } from "telegraf";
import { LeadStatus } from "@bot-motiv/db";
import { LEAD_STATUS_LABELS } from "@bot-motiv/shared";
import { config, isAdmin } from "../config.js";
import { getAdminStats, getLeadById, listLeadsForAdmin, updateLeadStatus } from "../services/lead.service.js";
import { md } from "../lib/format.js";

const STATUSES = Object.values(LeadStatus);

export function registerAdminHandlers(bot: import("telegraf").Telegraf<Context>) {
  bot.command("admin", async (ctx) => {
    if (!ctx.from || !isAdmin(ctx.from.id)) {
      await ctx.reply("Нет доступа.");
      return;
    }
    await showAdminMenu(ctx);
  });

  bot.hears("🔐 Админ", async (ctx) => {
    if (!ctx.from || !isAdmin(ctx.from.id)) return;
    await showAdminMenu(ctx);
  });

  bot.action("adm:menu", async (ctx) => {
    await ctx.answerCbQuery();
    if (!ctx.from || !isAdmin(ctx.from.id)) return;
    await showAdminMenu(ctx, true);
  });

  bot.action("adm:stats", async (ctx) => {
    await ctx.answerCbQuery();
    if (!ctx.from || !isAdmin(ctx.from.id)) return;

    const { users, leads, byStatus } = await getAdminStats();
    let text = `📊 *Статистика*\n\n👤 Пользователей: ${users}\n📋 Лидов: ${leads}\n\n`;
    for (const row of byStatus) {
      text += `${LEAD_STATUS_LABELS[row.status] ?? row.status}: ${row._count}\n`;
    }
    await ctx.editMessageText(text, { parse_mode: "Markdown", ...adminMenuKb() });
  });

  bot.action(/^adm:leads:(\w+):(\d+)$/, async (ctx) => {
    await ctx.answerCbQuery();
    if (!ctx.from || !isAdmin(ctx.from.id)) return;

    const statusRaw = ctx.match[1];
    const statusFilter =
      statusRaw === "all" ? undefined : (STATUSES.includes(statusRaw as LeadStatus) ? (statusRaw as LeadStatus) : undefined);
    const page = parseInt(ctx.match[2], 10);
    const { items, total, pages } = await listLeadsForAdmin({
      status: statusFilter && STATUSES.includes(statusFilter) ? statusFilter : undefined,
      page,
      limit: 8,
    });

    let text = `👥 *Лиды* (${total})\n`;
    if (statusFilter) text += `Фильтр: ${LEAD_STATUS_LABELS[statusFilter] ?? statusFilter}\n`;
    text += "\n";

    const buttons: ReturnType<typeof Markup.button.callback>[][] = [];

    for (const lead of items) {
      const name = lead.user.firstName ?? lead.user.username ?? lead.user.telegramId.toString();
      const offer = lead.offer?.title ?? "—";
      text += `• ${md(name)} | ${md(offer)} | ${lead.status} | шаг ${lead.currentStep}\n`;
      buttons.push([Markup.button.callback(`📄 ${name.slice(0, 20)}`, `adm:lead:${lead.id}`)]);
    }

    const nav: ReturnType<typeof Markup.button.callback>[] = [];
    const statusKey = statusFilter ?? "all";
    if (page > 0) nav.push(Markup.button.callback("⬅️", `adm:leads:${statusKey}:${page - 1}`));
    if (page < pages - 1) nav.push(Markup.button.callback("➡️", `adm:leads:${statusKey}:${page + 1}`));
    if (nav.length) buttons.push(nav);

    buttons.push([Markup.button.callback("◀️ Админ", "adm:menu")]);

    await ctx.editMessageText(text, {
      parse_mode: "Markdown",
      ...Markup.inlineKeyboard(buttons),
    });
  });

  bot.action(/^adm:filter$/, async (ctx) => {
    await ctx.answerCbQuery();
    const rows = STATUSES.map((s) => [Markup.button.callback(LEAD_STATUS_LABELS[s] ?? s, `adm:leads:${s}:0`)]);
    rows.push([Markup.button.callback("Все", "adm:leads:all:0")]);
    rows.push([Markup.button.callback("◀️", "adm:menu")]);
    await ctx.editMessageText("Фильтр по статусу:", Markup.inlineKeyboard(rows));
  });

  bot.action(/^adm:lead:(.+)$/, async (ctx) => {
    await ctx.answerCbQuery();
    if (!ctx.from || !isAdmin(ctx.from.id)) return;

    const lead = await getLeadById(ctx.match[1]);
    if (!lead) {
      await ctx.reply("Лид не найден");
      return;
    }

    const stepData = lead.stepData as Record<string, string>;
    const dataLines = Object.entries(stepData)
      .map(([k, v]) => `${md(k)}: ${md(v)}`)
      .join("\n");

    let text =
      `📄 *Лид*\n\n` +
      `👤 ${md(lead.user.firstName ?? "—")}${lead.user.username ? ` @${md(lead.user.username)}` : ""}\n` +
      `🆔 TG: \`${lead.user.telegramId}\`\n` +
      `🎯 Оффер: ${md(lead.offer?.title ?? "—")}\n` +
      `📊 Статус: *${lead.status}*\n` +
      `📍 Шаг: ${lead.currentStep}\n` +
      `📅 ${md(lead.createdAt.toLocaleString("ru"))}\n`;

    if (dataLines) text += `\n📝 *Данные анкеты:*\n${dataLines}\n`;

    const statusButtons = STATUSES.map((s) =>
      Markup.button.callback(s, `adm:status:${lead.id}:${s}`)
    );
    const rows: ReturnType<typeof Markup.button.callback>[][] = [];
    for (let i = 0; i < statusButtons.length; i += 2) {
      rows.push(statusButtons.slice(i, i + 2));
    }
    rows.push([Markup.button.callback("◀️ К списку", "adm:leads:all:0")]);

    await ctx.editMessageText(text, { parse_mode: "Markdown", ...Markup.inlineKeyboard(rows) });
  });

  bot.action(/^adm:status:(.+):(\w+)$/, async (ctx) => {
    await ctx.answerCbQuery("Статус обновлён");
    if (!ctx.from || !isAdmin(ctx.from.id)) return;

    const leadId = ctx.match[1];
    const status = ctx.match[2];
    if (!STATUSES.includes(status as LeadStatus)) return;

    await updateLeadStatus(leadId, status as LeadStatus);
    const lead = await getLeadById(leadId);
    if (lead) {
      await ctx.reply(
        `✅ Статус изменён на *${status}* для ${md(lead.user.firstName ?? lead.user.username ?? "—")}`,
        { parse_mode: "Markdown" }
      );
    }
  });
}

async function showAdminMenu(ctx: Context, edit = false) {
  const text =
    `🔐 *Админ-панель*\n\n` +
    `Твой ID: \`${ctx.from?.id}\`\n` +
    `Админов в конфиге: ${config.adminTelegramIds.length}`;

  const kb = adminMenuKb();
  if (edit && ctx.callbackQuery) {
    await ctx.editMessageText(text, { parse_mode: "Markdown", ...kb });
  } else {
    await ctx.replyWithMarkdown(text, kb);
  }
}

function adminMenuKb() {
  return Markup.inlineKeyboard([
    [Markup.button.callback("📊 Статистика", "adm:stats")],
    [Markup.button.callback("👥 Все лиды", "adm:leads:all:0")],
    [Markup.button.callback("🔍 Фильтр по статусу", "adm:filter")],
  ]);
}

export function adminMenuButton() {
  return config.adminTelegramIds.length > 0 ? [["🔐 Админ"]] : [];
}
