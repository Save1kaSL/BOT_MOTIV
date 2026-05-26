import { Router, type Request, type Response, type NextFunction } from "express";
import { z } from "zod";
import { prisma } from "@bot-motiv/db";
import { findOrCreateUser, getUserProfile } from "../services/user.service.js";
import { selectOffer, advanceStep, goBackStep, saveStepData, getActiveLead } from "../services/lead.service.js";
import { chatWithAi } from "../services/ai.service.js";
import { scheduleMeetingReminder } from "../services/notification.service.js";

const router = Router();

const internalKey = process.env.INTERNAL_API_KEY ?? "internal-dev-key";

function botAuth(req: Request, res: Response, next: NextFunction): void {
  if (req.headers["x-internal-key"] !== internalKey) {
    res.status(403).json({ success: false, error: "Forbidden" });
    return;
  }
  next();
}

router.use(botAuth);

router.post("/users/sync", async (req, res) => {
  const schema = z.object({
    telegramId: z.string(),
    username: z.string().optional(),
    firstName: z.string().optional(),
    lastName: z.string().optional(),
    startPayload: z.string().optional(),
  });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ success: false, error: "Invalid input" });
    return;
  }

  const user = await findOrCreateUser({
    telegramId: BigInt(parsed.data.telegramId),
    username: parsed.data.username,
    firstName: parsed.data.firstName,
    lastName: parsed.data.lastName,
    startPayload: parsed.data.startPayload,
  });

  res.json({ success: true, data: serializeUser(user) });
});

router.get("/users/:telegramId", async (req, res) => {
  const user = await prisma.user.findUnique({
    where: { telegramId: BigInt(req.params.telegramId) },
    include: {
      leads: { orderBy: { updatedAt: "desc" }, take: 1, include: { offer: true } },
      _count: { select: { referrals: true } },
    },
  });
  if (!user) {
    res.status(404).json({ success: false, error: "Not found" });
    return;
  }
  res.json({ success: true, data: serializeUser(user) });
});

router.get("/offers", async (_req, res) => {
  const offers = await prisma.offer.findMany({
    where: { active: true },
    orderBy: { sortOrder: "asc" },
  });
  res.json({ success: true, data: offers });
});

router.post("/offers/select", async (req, res) => {
  const schema = z.object({ userId: z.string(), offerId: z.string() });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ success: false, error: "Invalid input" });
    return;
  }
  const lead = await selectOffer(parsed.data.userId, parsed.data.offerId);
  res.json({ success: true, data: lead });
});

router.post("/leads/go-back", async (req, res) => {
  const schema = z.object({ userId: z.string() });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ success: false, error: "Invalid input" });
    return;
  }
  const lead = await goBackStep(parsed.data.userId);
  res.json({ success: true, data: lead });
});

router.post("/leads/advance", async (req, res) => {
  const schema = z.object({ userId: z.string() });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ success: false, error: "Invalid input" });
    return;
  }
  const lead = await advanceStep(parsed.data.userId);
  if (lead.currentStep === 5) {
    await scheduleMeetingReminder(parsed.data.userId, 24);
  }
  res.json({ success: true, data: lead });
});

router.post("/leads/step-data", async (req, res) => {
  const schema = z.object({ userId: z.string(), data: z.record(z.string()) });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ success: false, error: "Invalid input" });
    return;
  }
  const lead = await saveStepData(parsed.data.userId, parsed.data.data);
  res.json({ success: true, data: lead });
});

router.get("/leads/active/:userId", async (req, res) => {
  const lead = await getActiveLead(req.params.userId);
  res.json({ success: true, data: lead });
});

router.get("/faq", async (_req, res) => {
  const articles = await prisma.knowledgeArticle.findMany({
    where: { category: "faq", active: true },
  });
  res.json({ success: true, data: articles });
});

router.post("/ai/chat", async (req, res) => {
  const schema = z.object({ userId: z.string(), message: z.string().min(1).max(2000) });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ success: false, error: "Invalid input" });
    return;
  }
  try {
    const reply = await chatWithAi(parsed.data.userId, parsed.data.message);
    res.json({ success: true, data: { reply } });
  } catch {
    res.status(500).json({ success: false, error: "AI error" });
  }
});

router.get("/templates/:key", async (req, res) => {
  const tpl = await prisma.messageTemplate.findUnique({ where: { key: req.params.key } });
  res.json({ success: true, data: tpl });
});

router.get("/profile/:userId", async (req, res) => {
  const profile = await getUserProfile(req.params.userId);
  res.json({ success: true, data: profile });
});

function serializeUser(user: {
  id: string;
  telegramId: bigint;
  username: string | null;
  firstName: string | null;
  referralCode: string;
  trafficSource: string | null;
  leads: unknown[];
  _count: { referrals: number };
}) {
  return {
    ...user,
    telegramId: user.telegramId.toString(),
  };
}

export default router;
