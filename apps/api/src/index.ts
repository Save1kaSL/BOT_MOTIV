import express from "express";
import cors from "cors";
import helmet from "helmet";
import rateLimit from "express-rate-limit";
import pinoHttp from "pino-http";
import { config } from "./config.js";
import { logger } from "./lib/logger.js";
import authRoutes from "./routes/auth.routes.js";
import botRoutes from "./routes/bot.routes.js";
import adminRoutes from "./routes/admin.routes.js";
import { processPendingNotifications } from "./services/notification.service.js";

const app = express();

app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN ?? "*" }));
app.use(express.json({ limit: "1mb" }));
app.use(pinoHttp({ logger }));

app.use(
  rateLimit({
    windowMs: config.rateLimit.windowMs,
    max: config.rateLimit.max,
    standardHeaders: true,
    legacyHeaders: false,
  })
);

app.get("/health", (_req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

app.use("/auth", authRoutes);
app.use("/bot", botRoutes);
app.use("/admin", adminRoutes);

app.use((err: Error, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  logger.error(err, "Unhandled error");
  res.status(500).json({ success: false, error: "Internal server error" });
});

const NOTIFICATION_INTERVAL_MS = 60_000;

function startNotificationWorker() {
  setInterval(async () => {
    try {
      const sent = await processPendingNotifications();
      if (sent > 0) logger.info({ sent }, "Notifications processed");
    } catch (err) {
      logger.error(err, "Notification worker error");
    }
  }, NOTIFICATION_INTERVAL_MS);
}

app.listen(config.port, () => {
  logger.info(`API running on port ${config.port}`);
  startNotificationWorker();
});
