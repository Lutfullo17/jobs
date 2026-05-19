# Jobify API

**Jobify** — ish qidiruv va kadrlar boshqaruvi uchun backend API. Platforma HeadHunter / ish e’lonlari saytlariga o‘xshash mantiqda ishlaydi: kompaniyalar vakansiya joylaydi, nomzodlar qidiradi va murojaat qiladi, HR nomzodlar bilan suhbatlashadi, admin tizimni nazorat qiladi.

API **FastAPI** asosida, **async** uslubda yozilgan. Barcha endpointlar Swagger orqali hujjatlashtirilgan: `http://localhost:8001/docs` (port muhitga qarab o‘zgarishi mumkin).

---

## 1. Loyihaning umumiy maqsadi

Jobify uch tomonlarni birlashtiradi:

| Tomon | Maqsad |
|--------|--------|
| **Nomzod (candidate)** | Vakansiyalarni qidirish, profil va rezyumeni to‘ldirish, murojaat yuborish, HR bilan yozishmalar, dashboard |
| **HR** | Kompaniya yaratish, vakansiya e’lon qilish, kelgan murojaatlarni ko‘rib chiqish, qabul/rad etish, chat |
| **Admin** | HR akkauntlarni tasdiqlash, foydalanuvchilar bilan support (yordam) yozishmalari |

Asosiy biznes oqimi qisqacha:

1. Foydalanuvchi ro‘yxatdan o‘tadi va emailni tasdiqlaydi.
2. HR admin tomonidan tasdiqlangach vakansiya joylashi mumkin.
3. Vakansiya `published` holatida bo‘lsa, ochiq ro‘yxatda va nomzod qidiruvida ko‘rinadi.
4. Nomzod murojaat yuboradi — HR pipeline bo‘yicha statuslarni boshqaradi.
5. Faol murojaatlar uchun HR va nomzod o‘rtasida chat mavjud.
6. HR yoki nomzod admin bilan alohida **support** murojaati ochishi mumkin.

---

## 2. Rollar va imkoniyatlar

Tizimda uchta asosiy rol bor: `admin`, `hr`, `candidate`.

### Admin (`admin`)

- Oddiy `/register` orqali **yaratilmaydi** — alohida skript yoki ma’muriy yo‘l bilan qo‘shiladi.
- **HR tasdiqlash:** kutilayotgan HR ro‘yxati, tasdiqlash (`hr_approved = true`).
- **Support (admin tomondan):** barcha support murojaatlarini ko‘rish, javob berish, yopish.
- `/api/admin/*` prefiksi ostidagi endpointlar.

### HR (`hr`)

- Ro‘yxatdan o‘tgach email tasdiqlanadi, lekin vakansiya joylash uchun **admin tasdiqi** kerak (`hr_approved`).
- **Kompaniya:** yangi kompaniya yaratish, profilni tahrirlash (`/api/companies`).
- **Vakansiyalar:** yaratish, tahrirlash, yopish, yumshoq o‘chirish (`/api/hr/vacancies`).
- **Murojaatlar:** kelgan arizalarni filterlash, batafsil ko‘rish, nomzod rezyumesini yuklab olish.
- **Recruitment:** qabul qilish / rad etish, chat xabarlari (`/api/hr/applications`).
- **Support:** admin bilan yozishma ochish va davom ettirish (`/api/support` — faqat HR va candidate).
- **Status:** `/api/hr/status/` — tasdiqlanganligi va vakansiya joylash mumkinligini ko‘rish.

### Nomzod (`candidate`)

- Ro‘yxatdan o‘tish, email tasdiqlash, login.
- **Vakansiya qidiruvi:** filtrlar, pagination, allaqachon murojaat qilganlarni yashirish (`/api/candidate/vacancies`).
- **Ochiq vakansiyalar:** login shart emas (`/api/vacancies`) — ro‘yxat va bitta vakansiya; murojaat uchun token kerak.
- **Murojaatlar:** o‘z arizalari, status, chat (`/api/candidate/applications`).
- **Profil:** structured profil (tajriba, ta’lim, ko‘nikmalar va hokazo) — hozir asosan ko‘rish (`/api/candidate/profile`).
- **Rezyume:** fayl yuklash, yangilash, yuklab olish (`/api/candidate/resume`).
- **Dashboard:** arizalar statistikasi, o‘qilmagan bildirishnomalar, profil to‘liqligi (`/api/candidate/dashboard`).
- **Bildirishnomalar:** ro‘yxat, o‘qilgan deb belgilash.
- **Support:** admin bilan murojaat (`/api/support`).

### Autentifikatsiya (barcha rollar)

`/api/auth` — register, verify email, login, refresh, logout, parolni tiklash, `/me` va hokazo.  
Ko‘pchilik himoyalangan endpointlar `Authorization: Bearer <access_token>` talab qiladi.

---

## 3. API modullari (prefiks bo‘yicha)

| Prefiks | Kim uchun | Asosiy vazifa |
|---------|-----------|----------------|
| `/api/auth` | Hammaga | Hisob, JWT, email tasdiqlash, parol |
| `/api/admin` | Admin | HR tasdiqlash, support boshqaruvi |
| `/api/hr` | HR (tasdiqlangan) | Vakansiya CRUD, murojaatlar, chat |
| `/api/companies` | HR + ochiq o‘qish | Kompaniya profili, slug bo‘yicha sahifa |
| `/api/vacancies` | Ochiq + nomzod (apply) | E’lonlar ro‘yxati, tafsilot, murojaat |
| `/api/candidate/vacancies` | Nomzod | Kengaytirilgan qidiruv |
| `/api/candidate/applications` | Nomzod | Arizalar, chat, rezyume |
| `/api/candidate/profile` | Nomzod | Profil ko‘rish |
| `/api/candidate` | Nomzod | Dashboard, bildirishnomalar |
| `/api/support` | HR, nomzod | Admin bilan yordam chat |
| `/` | — | API ishlayotganini tekshirish |

**Eslatmalar:**

- Support uchun admin `/api/admin/support/...`, HR/nomzod `/api/support/...` ishlatadi — URL va ruxsatlar farq qiladi.
- Vakansiya qidiruvida faqat `status = published`, muddati o‘tmagan va `is_deleted = false` bo‘lgan e’lonlar chiqadi.
- HR vakansiya yaratganda dastlab odatda `draft` holati; e’lonni ko‘rinishi uchun `published` qilish kerak (ma’lumotlar bazasi yoki keyingi jarayon orqali).

---

## 4. Asosiy biznes tushunchalari

### Vakansiya holatlari

`draft`, `on_moderation`, `published`, `closed`, `archived`, `rejected_by_admin` — HR e’lonni boshqaradi; nomzod va ochiq API faqat **published** e’lonlarni ko‘radi.

### Murojaat (application) pipeline

Nomzod vakansiyaga murojaat qilganda `VacancyApplication` yaratiladi. Statuslar masalan: `applied`, `viewed`, `shortlisted`, `screening`, `interview_scheduled`, `interviewed`, `test_task`, `offer_sent`, `hired`, `rejected`, `withdrawn` va boshqalar.  
Ba’zi statuslarda HR va nomzod o‘rtasida **chat** ochiq bo‘ladi.

### Kompaniya

HR kompaniya yaratadi (`slug`, nom, soha, manzil va hokazo). Vakansiya ixtiyoriy ravishda `company_id` bilan bog‘lanadi. `verified_company_only` filtri tasdiqlangan kompaniyalarni ajratadi.

### Support

HR yoki nomzod **mavzu + birinchi xabar** bilan murojaat ochadi. Admin barcha threadlarni ko‘radi va javob beradi. Thread `open` / `closed` holatlarida bo‘ladi.

### Bildirishnomalar

Nomzod (va kelajakda boshqa rollar) uchun `notifications` jadvali — dashboardda o‘qilmaganlar soni chiqadi.

---

## 5. Texnologiyalar: nima, nima uchun, qayerda

### Python 3

- **Nima uchun:** butun backend tili.
- **Qayerda:** `main.py`, `app/`, `alembic/`, `scripts/`.

### FastAPI

- **Nima uchun:** tez REST API, avtomatik OpenAPI/Swagger, async endpointlar, Pydantic integratsiyasi.
- **Qayerda:** `main.py` (app yaratish, router ulash), `app/api/*.py` (barcha HTTP endpointlar).

### Uvicorn

- **Nima uchun:** ASGI server — FastAPI ilovasini ishga tushirish.
- **Qayerda:** ishlab chiqish va Docker `command` ichida (`uvicorn main:app`).

### SQLAlchemy 2 (async)

- **Nima uchun:** PostgreSQL bilan async ORM, murakkab so‘rovlar, bog‘lanishlar.
- **Qayerda:** `app/core/database.py` (engine, sessiya), `app/models/*` (jadval modellari), `app/services/*` (biznes logika va so‘rovlar).

### asyncpg

- **Nima uchun:** PostgreSQL uchun async drayver (`postgresql+asyncpg://...`).
- **Qayerda:** `DATABASE_URL` orqali SQLAlchemy engine.

### PostgreSQL

- **Nima uchun:** asosiy ma’lumotlar bazasi — foydalanuvchilar, vakansiyalar, murojaatlar, kompaniyalar, support, bildirishnomalar.
- **Qayerda:** Docker `db` servisi yoki mahalliy PostgreSQL; barcha `app/models` jadvallari shu yerda.

### Alembic

- **Nima uchun:** sxema o‘zgarishlarini versiyalash (migration).
- **Qayerda:** `alembic.ini`, `alembic/env.py`, `alembic/versions/*.py`.

### Pydantic / pydantic-settings

- **Nima uchun:** request/response validatsiyasi, `.env` dan sozlamalarni o‘qish.
- **Qayerda:** `app/schemas/*` (API kontrakt), `app/core/config.py` (`Settings`).

### PyJWT

- **Nima uchun:** access va refresh token yaratish va tekshirish.
- **Qayerda:** `app/core/security.py`, `app/api/deps.py` (`get_current_user`).

### Passlib + bcrypt

- **Nima uchun:** parollarni xeshlash — ma’lumotlar bazasida plain text saqlanmaydi.
- **Qayerda:** `app/core/security.py`, `app/services/auth_service.py`.

### Redis

- **Nima uchun:** tezkor in-memory store — login/resend/forgot **rate limit** hisoblagichi.
- **Qayerda:** `app/core/redis_client.py` (`enforce_rate_limit`), `app/api/auth.py`.  
  Redis ishlamasa, xavfsizlik yuzasidan so‘rovlar cheklanishi mumkin (login bloklanishi).

### Celery

- **Nima uchun:** uzoq ishlaydigan vazifalarni fon rejimida bajarish (asosan email).
- **Qayerda:** `app/core/celery_app.py`, `app/tasks/email_tasks.py`, `app/services/email_service.py`.

### SMTP (email)

- **Nima uchun:** tasdiqlash va parol tiklash kodlarini yuborish.
- **Qayerda:** Celery task ichida; `.env` da `SMTP_*` sozlamalari.  
  SMTP yo‘q bo‘lsa, dev rejimida kod konsolga `[VERIFICATION-CODE]` ko‘rinishida chiqadi.

### Docker / Docker Compose

- **Nima uchun:** bir xil muhitda API, PostgreSQL, Redis, Celery worker ni birga ko‘tarish.
- **Qayerda:** `Dockerfile`, `docker-compose.yml` (`app`, `db`, `redis`, `celery-worker`).

### python-multipart

- **Nima uchun:** fayl yuklash (nomzod rezyumesi).
- **Qayerda:** `app/api/candidate_recruitment.py` (resume upload).

---

## 6. Loyiha tuzilishi

```text
.
├── main.py                 # FastAPI app, routerlar
├── requirements.txt
├── .env.example            # Muhit o‘zgaruvchilari namunasi
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/           # Migratsiya fayllari
├── scripts/                # Admin yaratish, seed skriptlar
└── app/
    ├── api/                # HTTP endpointlar (modul bo‘yicha)
    │   ├── auth.py
    │   ├── admin.py
    │   ├── hr.py
    │   ├── companies.py
    │   ├── vacancies.py
    │   ├── support.py
    │   ├── candidate_vacancies.py
    │   ├── candidate_recruitment.py
    │   ├── candidate_profile.py
    │   ├── candidate_platform.py
    │   └── deps.py         # Token, rol tekshiruvlari
    ├── core/
    │   ├── config.py       # Sozlamalar
    │   ├── database.py     # Async DB sessiya
    │   ├── security.py     # JWT, parol xesh
    │   ├── redis_client.py
    │   └── celery_app.py
    ├── models/             # SQLAlchemy jadval modellari
    ├── schemas/            # Pydantic request/response
    ├── services/           # Biznes logika
    └── tasks/              # Celery vazifalar
```

**Qatlamlar mantig‘i:**

- **api** — HTTP qabul qiladi, `Depends` orqali foydalanuvchini aniqlaydi, servisni chaqiradi.
- **services** — qoidalar, filtrlash, tranzaksiyalar.
- **models** — jadval tuzilmasi.
- **schemas** — API kirish/chiqish formati.

---

## 7. Ma’lumotlar bazasi (asosiy jadvallar)

| Jadval / guruhi | Vazifasi |
|-----------------|----------|
| `users` | Email, parol xesh, rol, `is_verified`, HR uchun `hr_approved` |
| `email_verification_codes`, `password_reset_codes` | Bir martalik kodlar |
| `refresh_tokens` | Refresh token xesh, revoke, qurilma/IP |
| `companies`, `company_members` | Ish beruvchi profili va HR a’zoligi |
| `vacancies` | E’lonlar (lavozim, maosh, joy, status, `company_id`) |
| `vacancy_applications` | Nomzod murojaatlari va pipeline statusi |
| `application_messages` | HR ↔ nomzod chat |
| `candidate_profiles` + bog‘liq jadvallar | Tajriba, ta’lim, ko‘nikmalar |
| `candidate_resumes` | Yuklangan rezyume fayli |
| `support_threads`, `support_messages` | Admin yordam chat |
| `notifications` | Foydalanuvchi bildirishnomalari |

Batafsil ustunlar uchun `app/models/` va Alembic migratsiyalariga qarang.

---

## 8. Xavfsizlik va cheklovlar

- Parollar **bcrypt** xesh bilan saqlanadi.
- **Access** va **refresh** tokenlar alohida; refresh DB da xesh holatda, rotation va logout qo‘llab-quvvatlanadi.
- Email tasdiqlanmaguncha va `is_active = false` bo‘lsa, kirish cheklanadi.
- `admin` roli public registerda tanlanmaydi.
- HR vakansiya joylashdan oldin **admin tasdiqi** talab qilinadi.
- **Rate limit** (Redis): login, verification resend, forgot password — suiiste’molni kamaytirish.
- Support va murojaatlarda **egasi/admin** tekshiruvi — boshqasining ma’lumotini ko‘rish mumkin emas.

---

## 9. Muhit o‘zgaruvchilari

Asosiy sozlamalar `.env` faylida (namuna: `.env.example`):

| Guruh | O‘zgaruvchilar |
|--------|----------------|
| Ma’lumotlar bazasi | `DATABASE_URL` |
| JWT | `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` |
| Email | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `SMTP_USE_TLS`, `SMTP_USE_STARTTLS` |
| Redis | `REDIS_URL` |
| Rate limit | `RATE_LIMIT_LOGIN_*`, `RATE_LIMIT_RESEND_*`, `RATE_LIMIT_FORGOT_*` |

Production uchun `JWT_SECRET_KEY` va SMTP parollarini xavfsiz saqlang; `.env` ni gitga commit qilmang.

---

## 10. Hujjatlashtirish va keyingi qadamlar

- **Swagger UI:** `/docs` — barcha endpointlar, parametrlar va modellar.
- **ReDoc:** `/redoc` — alternativ hujjat ko‘rinishi.

Loyiha rivojlantirishda odatda qo‘shiladi: avtomatlashtirilgan testlar (pytest), CI, vakansiyani API orqali `published` qilish, profilni to‘liq tahrirlash endpointlari, admin panel integratsiyasi.

---

*Jobify API — ish e’lonlari platformasi uchun yagona backend manbasi. Savollar bo‘lsa, Swagger (`/docs`) va `app/services` dagi biznes qoidalardan boshlang.*
