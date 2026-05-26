import { Router } from "express";
import { z } from "zod";
import { prisma, LeadStatus } from "@bot-motiv/db";
import { LEAD_STATUS_LABELS } from "@bot-motiv/shared";
import { authMiddleware, requireRole } from "../lib/auth.js";
import { updateLeadStatus } from "../services/lead.service.js";
import { broadcastMessage } from "../services/notification.service.js";

const router = Router();
router.use(authMiddleware);

router.get("/analytics", async (_req, res) => {
  const [totalUsers, totalLeads, leadsByStatus, payments, referrals] = await Promise.all([
    prisma.user.count(),
    prisma.lead.count(),
    prisma.lead.groupBy({ by: ["status"], _count: true }),
    prisma.payment.aggregate({ _sum: { amount: true }, where: { status: "PAID" } }),
    prisma.user.count({ where: { referredById: { not: null } } }),
  ]);

  const statusMap: Record<string, number> = {};
  for (const s of leadsByStatus) {
    statusMap[s.status] = s._count;
  }

  res.json({
    success: true,
    data: {
      totalUsers,
      totalLeads,
      leadsByStatus: statusMap,
      leadsByStatusLabels: LEAD_STATUS_LABELS,
      totalPayments: Number(payments._sum.amount ?? 0),
      totalReferrals: referrals,
    },
  });
});

router.get("/leads", async (req, res) => {
  const page = parseInt((req.query.page as string) ?? "1", 10);
  const limit = Math.min(parseInt((req.query.limit as string) ?? "20", 10), 100);
  const status = req.query.status as LeadStatus | undefined;
  const skip = (page - 1) * limit;

  const where = status ? { status } : {};

  const [leads, total] = await Promise.all([
    prisma.lead.findMany({
      where,
      skip,
      take: limit,
      orderBy: { updatedAt: "desc" },
      include: {
        user: true,
        offer: true,
      },
    }),
    prisma.lead.count({ where }),
  ]);

  res.json({
    success: true,
    data: {
      items: leads.map((l) => ({ ...l, user: { ...l.user, telegramId: l.user.telegramId.toString() } })),
      total,
      page,
      pages: Math.ceil(total / limit),
    },
  });
});

router.patch("/leads/:id", requireRole("SUPER_ADMIN", "ADMIN", "MANAGER"), async (req, res) => {
  const schema = z.object({
    status: z.nativeEnum(LeadStatus).optional(),
    notes: z.string().optional(),
    currentStep: z.number().optional(),
  });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ success: false, error: "Invalid input" });
    return;
  }

  const leadId = String(req.params.id);
  const lead = await prisma.lead.update({
    where: { id: leadId },
    data: parsed.data,
    include: { user: true, offer: true },
  });

  const admin = (req as { admin?: { adminId: string } }).admin;
  await prisma.auditLog.create({
    data: {
      adminId: admin?.adminId,
      action: "UPDATE_LEAD",
      entity: "lead",
      entityId: lead.id,
      meta: parsed.data,
    },
  });

  res.json({ success: true, data: lead });
});

router.post("/leads/:id/status", requireRole("SUPER_ADMIN", "ADMIN", "MANAGER"), async (req, res) => {
  const schema = z.object({ status: z.nativeEnum(LeadStatus), notes: z.string().optional() });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ success: false, error: "Invalid input" });
    return;
  }
  const lead = await updateLeadStatus(String(req.params.id), parsed.data.status, parsed.data.notes);
  res.json({ success: true, data: lead });
});

router.get("/offers", async (_req, res) => {
  const offers = await prisma.offer.findMany({ orderBy: { sortOrder: "asc" } });
  res.json({ success: true, data: offers });
});

router.post("/offers", requireRole("SUPER_ADMIN", "ADMIN"), async (req, res) => {
  const schema = z.object({
    slug: z.string(),
    title: z.string(),
    description: z.string(),
    ourProfit: z.string(),
    clientProfit: z.string(),
    steps: z.array(z.unknown()),
    referralLink: z.string(),
    tags: z.array(z.string()).optional(),
    active: z.boolean().optional(),
    sortOrder: z.number().optional(),
  });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ success: false, error: "Invalid input" });
    return;
  }
  const offer = await prisma.offer.create({ data: parsed.data as never });
  res.json({ success: true, data: offer });
});

router.patch("/offers/:id", requireRole("SUPER_ADMIN", "ADMIN"), async (req, res) => {
  const offer = await prisma.offer.update({ where: { id: String(req.params.id) }, data: req.body });
  res.json({ success: true, data: offer });
});

router.get("/users", async (req, res) => {
  const page = parseInt((req.query.page as string) ?? "1", 10);
  const limit = 20;
  const skip = (page - 1) * limit;

  const [users, total] = await Promise.all([
    prisma.user.findMany({
      skip,
      take: limit,
      orderBy: { createdAt: "desc" },
      include: { _count: { select: { referrals: true, leads: true } } },
    }),
    prisma.user.count(),
  ]);

  res.json({
    success: true,
    data: {
      items: users.map((u) => ({ ...u, telegramId: u.telegramId.toString() })),
      total,
      page,
    },
  });
});

router.post("/broadcast", requireRole("SUPER_ADMIN", "ADMIN"), async (req, res) => {
  const schema = z.object({
    message: z.string().min(1).max(4096),
    userIds: z.array(z.string()).optional(),
  });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ success: false, error: "Invalid input" });
    return;
  }

  const users = parsed.data.userIds?.length
    ? await prisma.user.findMany({ where: { id: { in: parsed.data.userIds } } })
    : await prisma.user.findMany({ where: { isBlocked: false } });

  const result = await broadcastMessage(
    users.map((u) => u.telegramId),
    parsed.data.message
  );

  res.json({ success: true, data: result });
});

router.get("/knowledge", async (_req, res) => {
  const articles = await prisma.knowledgeArticle.findMany({ orderBy: { updatedAt: "desc" } });
  res.json({ success: true, data: articles });
});

router.get("/payments", async (_req, res) => {
  const payments = await prisma.payment.findMany({
    orderBy: { createdAt: "desc" },
    take: 50,
    include: { user: true, lead: { include: { offer: true } } },
  });
  res.json({
    success: true,
    data: payments.map((p) => ({
      ...p,
      user: { ...p.user, telegramId: p.user.telegramId.toString() },
    })),
  });
});

export default router;
