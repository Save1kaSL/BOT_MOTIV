FROM node:20-alpine AS base
WORKDIR /app

FROM base AS deps
COPY package.json package-lock.json* ./
COPY apps/admin/package.json ./apps/admin/
RUN npm install --workspace=@bot-motiv/admin --include-workspace-root

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY apps/admin ./apps/admin
WORKDIR /app/apps/admin
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM base AS runner
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app/apps/admin
COPY --from=builder /app/apps/admin/.next/standalone ./
COPY --from=builder /app/apps/admin/.next/static ./.next/static
COPY --from=builder /app/apps/admin/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
