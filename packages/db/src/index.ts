export {
  PrismaClient,
  LeadStatus,
  PaymentStatus,
  NotificationType,
  NotificationStatus,
  AdminRole,
} from "@prisma/client";
export type { User, Offer, Lead, Payment, KnowledgeArticle, AdminUser } from "@prisma/client";

import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["error", "warn"] : ["error"],
  });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
