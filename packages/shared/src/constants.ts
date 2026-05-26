export const LEAD_STATUS_LABELS: Record<string, string> = {
  NEW: "Новый",
  OFFER_SELECTED: "Оффер выбран",
  IN_PROGRESS: "В процессе",
  WAITING_MEETING: "Ожидание встречи",
  COMPLETED: "Завершён",
  APPROVED: "Одобрен",
  PAID: "Выплачен",
  REJECTED: "Отклонён",
};

export const REFERRAL_BONUS_AMOUNT = 500;

export const BOT_CALLBACKS = {
  OFFERS: "offers",
  OFFER_SELECT: "offer:",
  STEP_NEXT: "step:next",
  STEP_PREV: "step:prev",
  FAQ: "faq",
  REFERRAL: "referral",
  PROFILE: "profile",
  AI_HELP: "ai:help",
  MAIN_MENU: "main:menu",
} as const;
