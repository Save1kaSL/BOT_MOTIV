import { prisma, LeadStatus } from "@bot-motiv/db";
import { generateReferralCode, parseStartPayload } from "@bot-motiv/shared";

export async function findOrCreateUser(params: {
  telegramId: bigint;
  username?: string;
  firstName?: string;
  lastName?: string;
  startPayload?: string;
}) {
  const existing = await prisma.user.findUnique({
    where: { telegramId: params.telegramId },
    include: {
      leads: { orderBy: { updatedAt: "desc" }, take: 1, include: { offer: true } },
      _count: { select: { referrals: true } },
    },
  });

  if (existing) {
    await prisma.user.update({
      where: { id: existing.id },
      data: {
        lastActiveAt: new Date(),
        username: params.username,
        firstName: params.firstName,
        lastName: params.lastName,
      },
    });
    return existing;
  }

  const parsed = parseStartPayload(params.startPayload);
  let referredById: string | undefined;
  let trafficSource: string | undefined;

  if (parsed?.type === "ref") {
    const referrer = await prisma.user.findUnique({ where: { referralCode: parsed.value } });
    referredById = referrer?.id;
  } else if (parsed?.type === "source") {
    trafficSource = parsed.value;
  }

  let referralCode = generateReferralCode();
  while (await prisma.user.findUnique({ where: { referralCode } })) {
    referralCode = generateReferralCode();
  }

  const user = await prisma.user.create({
    data: {
      telegramId: params.telegramId,
      username: params.username,
      firstName: params.firstName,
      lastName: params.lastName,
      referralCode,
      referredById,
      trafficSource,
    },
    include: {
      leads: { orderBy: { updatedAt: "desc" }, take: 1, include: { offer: true } },
      _count: { select: { referrals: true } },
    },
  });

  await prisma.lead.create({ data: { userId: user.id, status: LeadStatus.NEW } });
  return user;
}
