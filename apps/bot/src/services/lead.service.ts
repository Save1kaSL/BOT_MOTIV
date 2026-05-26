import { prisma, LeadStatus } from "@bot-motiv/db";
import type { LeadStepData } from "@bot-motiv/shared";

export async function selectOffer(userId: string, offerId: string) {
  const offer = await prisma.offer.findUnique({ where: { id: offerId } });
  if (!offer?.active) throw new Error("Offer not found");

  const lead = await prisma.lead.findFirst({
    where: { userId },
    orderBy: { updatedAt: "desc" },
  });

  if (lead) {
    return prisma.lead.update({
      where: { id: lead.id },
      data: { offerId, status: LeadStatus.OFFER_SELECTED, currentStep: 0, stepData: {} },
      include: { offer: true },
    });
  }

  return prisma.lead.create({
    data: { userId, offerId, status: LeadStatus.OFFER_SELECTED, currentStep: 0 },
    include: { offer: true },
  });
}

export async function goBackStep(userId: string) {
  const lead = await getActiveLead(userId);
  if (!lead?.offer) throw new Error("No active offer");

  return prisma.lead.update({
    where: { id: lead.id },
    data: { currentStep: Math.max(0, lead.currentStep - 1) },
    include: { offer: true },
  });
}

export async function advanceStep(userId: string) {
  const lead = await getActiveLead(userId);
  if (!lead?.offer) throw new Error("No active offer");

  const steps = lead.offer.steps as { order: number }[];
  const maxStep = steps.length;
  const nextStep = Math.min(lead.currentStep + 1, maxStep);

  let status: LeadStatus = LeadStatus.IN_PROGRESS;
  if (nextStep >= 4 && nextStep < 6) status = LeadStatus.WAITING_MEETING;
  if (nextStep >= maxStep) status = LeadStatus.COMPLETED;

  return prisma.lead.update({
    where: { id: lead.id },
    data: { currentStep: nextStep, status },
    include: { offer: true },
  });
}

export async function saveStepData(userId: string, data: LeadStepData) {
  const lead = await getActiveLead(userId);
  if (!lead) throw new Error("No active lead");

  const merged = { ...((lead.stepData as LeadStepData | null) ?? {}), ...data };
  return prisma.lead.update({
    where: { id: lead.id },
    data: { stepData: merged, status: LeadStatus.IN_PROGRESS },
    include: { offer: true },
  });
}

export async function getActiveLead(userId: string) {
  return prisma.lead.findFirst({
    where: { userId, status: { notIn: [LeadStatus.PAID, LeadStatus.REJECTED] } },
    orderBy: { updatedAt: "desc" },
    include: { offer: true },
  });
}

export async function updateLeadStatus(leadId: string, status: LeadStatus) {
  return prisma.lead.update({
    where: { id: leadId },
    data: { status },
    include: { offer: true, user: true },
  });
}

export async function listLeadsForAdmin(opts: { status?: LeadStatus; page?: number; limit?: number }) {
  const page = opts.page ?? 0;
  const limit = opts.limit ?? 10;
  const where = opts.status ? { status: opts.status } : {};

  const [items, total] = await Promise.all([
    prisma.lead.findMany({
      where,
      skip: page * limit,
      take: limit,
      orderBy: { updatedAt: "desc" },
      include: { user: true, offer: true },
    }),
    prisma.lead.count({ where }),
  ]);

  return { items, total, pages: Math.ceil(total / limit) };
}

export async function getLeadById(leadId: string) {
  return prisma.lead.findUnique({
    where: { id: leadId },
    include: { user: true, offer: true },
  });
}

export async function getAdminStats() {
  const [users, leads, byStatus] = await Promise.all([
    prisma.user.count(),
    prisma.lead.count(),
    prisma.lead.groupBy({ by: ["status"], _count: true }),
  ]);
  return { users, leads, byStatus };
}
