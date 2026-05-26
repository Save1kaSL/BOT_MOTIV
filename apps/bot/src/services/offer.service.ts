import { prisma } from "@bot-motiv/db";

export async function getActiveOffers() {
  return prisma.offer.findMany({
    where: { active: true },
    orderBy: { sortOrder: "asc" },
  });
}

export async function getFaqArticles() {
  return prisma.knowledgeArticle.findMany({
    where: { category: "faq", active: true },
  });
}
