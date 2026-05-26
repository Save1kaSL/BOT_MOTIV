import { prisma, LeadStatus } from "@bot-motiv/db";
import type { LeadStepData } from "@bot-motiv/shared";

export async function selectOffer(userId: string, offerId: string) {
  const offer = await prisma.offer.findUnique({ where: { id: offerId } });
  if (!offer?.active) throw new Error("Offer not found or inactive");

  const lead = await prisma.lead.findFirst({
    where: { userId },
    orderBy: { updatedAt: "desc" },
  });

  if (lead) {
    return prisma.lead.update({
      where: { id: lead.id },
      data: {
        offerId,
        status: LeadStatus.OFFER_SELECTED,
        currentStep: 0,
        stepData: {},
      },
      include: { offer: true },
    });
  }

  return prisma.lead.create({
    data: {
      userId,
      offerId,
      status: LeadStatus.OFFER_SELECTED,
      currentStep: 0,
    },
    include: { offer: true },
  });
}

export async function goBackStep(userId: string) {
  const lead = await getActiveLead(userId);
  if (!lead?.offer) throw new Error("No active offer");

  const prevStep = Math.max(0, lead.currentStep - 1);
  return prisma.lead.update({
    where: { id: lead.id },
    data: { currentStep: prevStep },
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

export async function updateLeadStatus(leadId: string, status: LeadStatus, notes?: string) {
  return prisma.lead.update({
    where: { id: leadId },
    data: { status, notes },
    include: { offer: true, user: true },
  });
}
