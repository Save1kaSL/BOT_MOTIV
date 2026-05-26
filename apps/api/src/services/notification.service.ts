import { prisma, NotificationType, NotificationStatus } from "@bot-motiv/db";
import { config } from "../config.js";
import { logger } from "../lib/logger.js";

export async function scheduleNotification(params: {
  userId: string;
  type: NotificationType;
  scheduledAt: Date;
  payload?: Record<string, unknown>;
}) {
  return prisma.notification.create({
    data: {
      userId: params.userId,
      type: params.type,
      scheduledAt: params.scheduledAt,
      payload: (params.payload ?? {}) as object,
    },
  });
}

export async function scheduleMeetingReminder(userId: string, hoursFromNow = 24) {
  const scheduledAt = new Date(Date.now() + hoursFromNow * 60 * 60 * 1000);
  return scheduleNotification({
    userId,
    type: NotificationType.MEETING_REMINDER,
    scheduledAt,
    payload: { message: "meeting_reminder" },
  });
}

export async function processPendingNotifications(): Promise<number> {
  const pending = await prisma.notification.findMany({
    where: {
      status: NotificationStatus.PENDING,
      scheduledAt: { lte: new Date() },
    },
    take: 50,
    include: { user: true },
  });

  if (!pending.length || !config.botToken) return 0;

  let sent = 0;
  for (const n of pending) {
    try {
      const text = await resolveNotificationText(n.type, n.payload as Record<string, string>);
      await sendTelegramMessage(Number(n.user.telegramId), text);
      await prisma.notification.update({
        where: { id: n.id },
        data: { status: NotificationStatus.SENT, sentAt: new Date() },
      });
      sent++;
    } catch (err) {
      logger.error({ err, notificationId: n.id }, "Failed to send notification");
      await prisma.notification.update({
        where: { id: n.id },
        data: { status: NotificationStatus.FAILED },
      });
    }
  }
  return sent;
}

async function resolveNotificationText(type: NotificationType, payload: Record<string, string>): Promise<string> {
  const keyMap: Partial<Record<NotificationType, string>> = {
    MEETING_REMINDER: "meeting_reminder",
    REACTIVATION: "reactivation",
    COMPLETE_OFFER: "reactivation",
    NEW_OFFER: "welcome",
    REFERRAL_BONUS: "welcome",
  };

  const key = keyMap[type] ?? payload.message;
  if (key) {
    const tpl = await prisma.messageTemplate.findUnique({ where: { key } });
    if (tpl) return tpl.content;
  }

  return payload.text ?? "Уведомление от партнёрской программы.";
}

async function sendTelegramMessage(chatId: number, text: string): Promise<void> {
  const res = await fetch(`https://api.telegram.org/bot${config.botToken}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: "Markdown" }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Telegram API error: ${body}`);
  }
}

export async function broadcastMessage(telegramIds: bigint[], text: string): Promise<{ sent: number; failed: number }> {
  let sent = 0;
  let failed = 0;
  for (const id of telegramIds) {
    try {
      await sendTelegramMessage(Number(id), text);
      sent++;
      await new Promise((r) => setTimeout(r, 50));
    } catch {
      failed++;
    }
  }
  return { sent, failed };
}
