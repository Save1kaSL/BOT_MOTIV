export type OfferStep = {
  order: number;
  title: string;
  content: string;
  collectData?: string[];
};

export type LeadStepData = Record<string, string>;

export type AnalyticsSummary = {
  totalUsers: number;
  totalLeads: number;
  leadsByStatus: Record<string, number>;
  totalPayments: number;
  totalReferrals: number;
};

export type ApiResponse<T> = {
  success: boolean;
  data?: T;
  error?: string;
};
