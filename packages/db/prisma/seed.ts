import { PrismaClient, AdminRole } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

const OFFERS = [
  {
    slug: "alfa-regbiz",
    title: "Альфа-РегБиз",
    description:
      "Открытие ИП через Альфа-Банк для самозанятых. Полный сопровождение от проверки СМЗ до получения выплаты.",
    ourProfit: "9000-10000 ₽",
    clientProfit: "3000-4000 ₽",
    referralLink: "https://example.com/alfa-regbiz?ref={ref}",
    tags: ["банк", "ип", "смз", "альфа"],
    sortOrder: 1,
    steps: [
      {
        order: 1,
        title: "Проверка СМЗ",
        content:
          "Убедитесь, что у вас есть статус самозанятого (СМЗ). Проверить можно в приложении «Мой налог» или на nalog.gov.ru.",
      },
      {
        order: 2,
        title: "Открытие ИП",
        content:
          "Перейдите по реферальной ссылке и начните процесс регистрации ИП. Подготовьте паспорт и СНИЛС.",
      },
      {
        order: 3,
        title: "Данные анкеты",
        content:
          "Заполните анкету. Понадобятся: ИНН, ФИО, телефон, почта, город. Отправьте данные боту командой или кнопкой «Отправить данные».",
        collectData: ["inn", "fullName", "phone", "email", "city"],
      },
      {
        order: 4,
        title: "После заявки",
        content:
          "После подачи заявки дождитесь звонка менеджера банка (1-3 рабочих дня). Не пропускайте звонки с незнакомых номеров.",
      },
      {
        order: 5,
        title: "Напоминание о встрече",
        content:
          "Назначена встреча с представителем банка. Возьмите паспорт и документы. При необходимости перенесите встречу заранее.",
      },
      {
        order: 6,
        title: "После встречи",
        content:
          "После встречи дождитесь активации счёта. Обычно это 1-2 рабочих дня. Сообщите нам, когда счёт открыт.",
      },
      {
        order: 7,
        title: "Получение выплаты",
        content:
          "После подтверждения открытия счёта выплата поступит на указанные реквизиты в течение 3-7 рабочих дней.",
      },
    ],
  },
  {
    slug: "tinkoff-business",
    title: "Тинькофф Бизнес",
    description: "Регистрация ИП и расчётный счёт в Тинькофф для партнёров.",
    ourProfit: "7000-8500 ₽",
    clientProfit: "2500-3500 ₽",
    referralLink: "https://example.com/tinkoff?ref={ref}",
    tags: ["банк", "ип", "тинькофф"],
    sortOrder: 2,
    steps: [
      { order: 1, title: "Регистрация", content: "Перейдите по ссылке и начните регистрацию ИП онлайн." },
      { order: 2, title: "Верификация", content: "Пройдите видео-идентификацию в приложении банка." },
      { order: 3, title: "Выплата", content: "После открытия счёта сообщите нам для начисления бонуса." },
    ],
  },
  {
    slug: "sber-smz",
    title: "Сбер СМЗ Плюс",
    description: "Подключение самозанятого к экосистеме Сбера с бонусом.",
    ourProfit: "5000-6000 ₽",
    clientProfit: "1500-2000 ₽",
    referralLink: "https://example.com/sber-smz?ref={ref}",
    tags: ["банк", "смз", "сбер"],
    sortOrder: 3,
    steps: [
      { order: 1, title: "Проверка", content: "Проверьте статус СМЗ в приложении «Мой налог»." },
      { order: 2, title: "Подключение", content: "Оформите подключение по реферальной ссылке." },
      { order: 3, title: "Бонус", content: "После активации получите выплату на карту." },
    ],
  },
];

const KNOWLEDGE = [
  {
    category: "faq",
    title: "Как начать зарабатывать?",
    content:
      "1) Нажмите /start\n2) Выберите оффер\n3) Следуйте пошаговой инструкции\n4) Выполните все шаги\n5) Получите выплату после подтверждения",
    tags: ["start", "earning"],
  },
  {
    category: "faq",
    title: "Когда придёт выплата?",
    content:
      "Выплата производится после подтверждения выполнения оффера менеджером. Обычно 3-7 рабочих дней после статуса APPROVED.",
    tags: ["payment", "payout"],
  },
  {
    category: "faq",
    title: "Реферальная программа",
    content:
      "Приглашайте друзей по своей реферальной ссылке. За каждого активного реферала, завершившего оффер, вы получаете бонус 500 ₽.",
    tags: ["referral"],
  },
  {
    category: "instruction",
    title: "Альфа-РегБиз: общая инструкция",
    content:
      "Полный цикл: СМЗ → ИП → анкета → встреча → счёт → выплата. На каждом этапе бот подскажет следующий шаг.",
    tags: ["alfa-regbiz"],
    offerSlug: "alfa-regbiz",
  },
  {
    category: "script",
    title: "Приветствие нового пользователя",
    content:
      "Привет! 👋 Я помогу тебе заработать на банковских офферах. Выбери подходящий оффер, следуй инструкции — и получи выплату на карту.",
    tags: ["welcome"],
  },
];

const TEMPLATES = [
  { key: "welcome", title: "Приветствие", content: "👋 Добро пожаловать в партнёрскую программу!\n\nЗдесь ты можешь зарабатывать на банковских офферах. Выбери оффер, выполни шаги — получи выплату." },
  { key: "mechanics", title: "Механика", content: "💰 *Как это работает:*\n\n1. Выбираешь оффер\n2. Получаешь персональную ссылку\n3. Выполняешь шаги по инструкции\n4. Мы проверяем результат\n5. Получаешь выплату на карту\n\n+ Бонусы за приглашённых друзей!" },
  { key: "meeting_reminder", title: "Напоминание о встрече", content: "📅 Напоминание: у тебя скоро встреча с представителем банка. Не забудь паспорт!" },
  { key: "reactivation", title: "Реактивация", content: "👋 Давно не заходил! У нас есть новые офферы с повышенной выплатой. Загляни в меню «Офферы»." },
];

async function main() {
  console.log("🌱 Seeding database...");

  for (const offer of OFFERS) {
    await prisma.offer.upsert({
      where: { slug: offer.slug },
      update: offer,
      create: offer,
    });
  }

  for (const article of KNOWLEDGE) {
    const existing = await prisma.knowledgeArticle.findFirst({
      where: { title: article.title, category: article.category },
    });
    if (existing) {
      await prisma.knowledgeArticle.update({ where: { id: existing.id }, data: article });
    } else {
      await prisma.knowledgeArticle.create({ data: article });
    }
  }

  for (const tpl of TEMPLATES) {
    await prisma.messageTemplate.upsert({
      where: { key: tpl.key },
      update: tpl,
      create: tpl,
    });
  }

  const adminEmail = process.env.ADMIN_EMAIL ?? "admin@example.com";
  const adminPassword = process.env.ADMIN_PASSWORD ?? "changeme123";
  const passwordHash = await bcrypt.hash(adminPassword, 12);

  await prisma.adminUser.upsert({
    where: { email: adminEmail },
    update: { passwordHash, role: AdminRole.SUPER_ADMIN },
    create: {
      email: adminEmail,
      passwordHash,
      name: "Super Admin",
      role: AdminRole.SUPER_ADMIN,
    },
  });

  console.log("✅ Seed completed");
  console.log(`   Admin: ${adminEmail} / ${adminPassword}`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
