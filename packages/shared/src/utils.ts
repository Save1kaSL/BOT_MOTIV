export function generateReferralCode(length = 8): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let code = "";
  for (let i = 0; i < length; i++) {
    code += chars[Math.floor(Math.random() * chars.length)];
  }
  return code;
}

export function buildReferralLink(botUsername: string, code: string): string {
  return `https://t.me/${botUsername}?start=ref_${code}`;
}

export function parseStartPayload(payload?: string): { type: "ref" | "source"; value: string } | null {
  if (!payload) return null;
  if (payload.startsWith("ref_")) return { type: "ref", value: payload.slice(4) };
  if (payload.startsWith("src_")) return { type: "source", value: payload.slice(4) };
  return null;
}

export function escapeMarkdown(text: string): string {
  return text.replace(/[_*[\]()~`>#+\-=|{}.!\\]/g, "\\$&");
}
