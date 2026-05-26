type SessionData = {
  userId?: string;
  awaitingData?: boolean;
  aiMode?: boolean;
};

const sessions = new Map<number, SessionData>();

export function getSession(telegramId: number): SessionData {
  if (!sessions.has(telegramId)) sessions.set(telegramId, {});
  return sessions.get(telegramId)!;
}

export function setSession(telegramId: number, data: Partial<SessionData>) {
  const current = getSession(telegramId);
  sessions.set(telegramId, { ...current, ...data });
}

export function clearAiMode(telegramId: number) {
  const s = getSession(telegramId);
  s.aiMode = false;
}
