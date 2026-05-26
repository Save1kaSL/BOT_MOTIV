import { Router } from "express";
import bcrypt from "bcryptjs";
import { z } from "zod";
import { prisma } from "@bot-motiv/db";
import { signToken } from "../lib/auth.js";

const router = Router();

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});

router.post("/login", async (req, res) => {
  const parsed = loginSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ success: false, error: "Invalid input" });
    return;
  }

  const admin = await prisma.adminUser.findUnique({ where: { email: parsed.data.email } });
  if (!admin?.active) {
    res.status(401).json({ success: false, error: "Invalid credentials" });
    return;
  }

  const valid = await bcrypt.compare(parsed.data.password, admin.passwordHash);
  if (!valid) {
    res.status(401).json({ success: false, error: "Invalid credentials" });
    return;
  }

  const token = signToken({ adminId: admin.id, email: admin.email, role: admin.role });

  await prisma.auditLog.create({
    data: { adminId: admin.id, action: "LOGIN", entity: "admin" },
  });

  res.json({
    success: true,
    data: { token, admin: { id: admin.id, email: admin.email, name: admin.name, role: admin.role } },
  });
});

export default router;
