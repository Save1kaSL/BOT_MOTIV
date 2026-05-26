export type Offer = {
  id: string;
  slug: string;
  title: string;
  description: string;
  ourProfit: string;
  clientProfit: string;
  steps: { order: number; title: string; content: string; collectData?: string[] }[];
  referralLink: string;
  tags: string[];
};

export type BotUser = {
  id: string;
  telegramId: bigint;
  username: string | null;
  firstName: string | null;
  referralCode: string;
  trafficSource: string | null;
  leads: Lead[];
  _count: { referrals: number };
};

export type Lead = {
  id: string;
  status: string;
  currentStep: number;
  stepData: Record<string, string>;
  offer?: Offer | null;
};
