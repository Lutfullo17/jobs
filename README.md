# JOBIFY AUTH MODULE (FastAPI, Async)

Bu loyiha `Jobify / HeadHunter-like` platformasining **Auth** qismi uchun yozilgan.
Kodlar junior darajaga mos, sodda va tushunarli uslubda yozilgan.

## 1) Hozirgacha nima qilindi?

Quyidagi auth funksiyalar implement qilindi:

- Register
- Verify email (kod bilan)
- Resend verification code
- Login (access + refresh token)
- Refresh token (rotation bilan)
- Logout
- Logout all devices
- Get current user (`/me`)
- Change password
- Forgot password
- Reset password
- Role-based check (`admin`, `hr`, `candidate`)
- Rate limit (`login`, `resend`, `forgot`)
- Docker + Docker Compose
- Alembic migration
- Swagger docs (FastAPI orqali avtomatik)

---

## 2) Qaysi texnologiyalar ishlatildi va nega?

Quyida **nima**, **nima uchun**, **qayerda** ishlatilgani yozilgan.

### Python
- **Nima uchun:** backend yozish uchun asosiy til.
- **Qayerda:** butun loyiha Python’da yozilgan (`main.py`, `app/*`, `alembic/*`).

### FastAPI
- **Nima uchun:** tez, sodda, async support bor, Swagger avtomatik beradi.
- **Qayerda:** API endpointlar `app/api/auth.py`, app yaratish `main.py`.

### Async SQLAlchemy
- **Nima uchun:** PostgreSQL bilan async ishlash, ko‘p request bo‘lsa samarali.
- **Qayerda:** `app/core/database.py`, `app/services/auth_service.py`.

### PostgreSQL
- **Nima uchun:** ishonchli relational database, auth uchun mos.
- **Qayerda:** `docker-compose.yml` ichida `db` service, model tablelar `app/models/*`.

### Alembic
- **Nima uchun:** table o‘zgarishlarini migration bilan boshqarish.
- **Qayerda:** `alembic.ini`, `alembic/env.py`, `alembic/versions/20260508_01_init_auth_tables.py`.

### JWT (PyJWT)
- **Nima uchun:** stateless auth, access/refresh token flow.
- **Qayerda:** `app/core/security.py` (`create_access_token`, `create_refresh_token`, `decode_token`).

### Passlib + bcrypt
- **Nima uchun:** password’ni plain text saqlamaslik, hash qilib xavfsiz saqlash.
- **Qayerda:** `app/core/security.py` (`hash_password`, `verify_password`).

### Redis
- **Nima uchun:** rate limit uchun tezkor cache/increment store.
- **Qayerda:** `app/core/redis_client.py`, endpointlarda `app/api/auth.py`.

### Celery
- **Nima uchun:** email yuborishni background taskga chiqarish (API tezroq javob beradi).
- **Qayerda:** `app/core/celery_app.py`, `app/tasks/email_tasks.py`, `app/services/email_service.py`.

### SMTP (email)
- **Nima uchun:** verification va reset code emailga yuborish.
- **Qayerda:** `app/tasks/email_tasks.py` (real yuborish), `.env` sozlamalari.

### Docker / Docker Compose
- **Nima uchun:** bir xil environmentda tez ishga tushirish.
- **Qayerda:** `Dockerfile`, `docker-compose.yml`.

### Pydantic
- **Nima uchun:** request/response validation, aniq schema.
- **Qayerda:** `app/schemas/auth.py`, `app/core/config.py`.

---

## 3) Loyiha strukturasi

```text
.
├── main.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 20260508_01_init_auth_tables.py
└── app/
    ├── api/
    │   ├── auth.py
    │   └── deps.py
    ├── core/
    │   ├── config.py
    │   ├── database.py
    │   ├── security.py
    │   ├── redis_client.py
    │   └── celery_app.py
    ├── models/
    │   ├── user.py
    │   ├── email_verification_code.py
    │   ├── password_reset_code.py
    │   └── refresh_token.py
    ├── schemas/
    │   └── auth.py
    ├── services/
    │   ├── auth_service.py
    │   └── email_service.py
    └── tasks/
        └── email_tasks.py
```

---

## 4) Auth endpointlar ro‘yxati

Base prefix: `/api/auth`

- `POST /register/`
- `POST /verify-email/`
- `POST /resend-verification-code/`
- `POST /login/`
- `POST /refresh/`
- `POST /logout/`
- `POST /logout-all/`
- `GET /me/`
- `POST /change-password/`
- `POST /forgot-password/`
- `POST /reset-password/`
- `GET /admin-only/`
- `GET /hr-only/`
- `GET /candidate-only/`

Swagger: `http://localhost:8000/docs`

---

## 5) Database modellar

### users
- `id`
- `email` (unique)
- `password_hash`
- `role` (`admin`, `hr`, `candidate`)
- `is_active`
- `is_verified`
- `created_at`
- `updated_at`

### email_verification_codes
- `id`
- `user_id`
- `code` (6 xonali)
- `expires_at`
- `is_used`
- `created_at`

### password_reset_codes
- `id`
- `user_id`
- `code` (6 xonali)
- `expires_at`
- `is_used`
- `created_at`

### refresh_tokens
- `id`
- `user_id`
- `token_hash`
- `expires_at`
- `revoked_at`
- `created_at`
- `user_agent`
- `ip_address`

---

## 6) Xavfsizlik bo‘yicha ishlanganlar

- Password hash holatda saqlanadi (bcrypt).
- Access va refresh tokenlar alohida.
- Refresh token DB’da hash holatda saqlanadi.
- Refresh token rotation bor (eski refresh revoke bo‘ladi).
- Logout token revoke qiladi.
- Logout all devices barcha refresh tokenlarni revoke qiladi.
- Email verification / reset code expire bo‘ladi va one-time ishlatiladi.
- `admin` oddiy register orqali yaratilmaydi.
- Rate limit bor (`login`, `resend`, `forgot`).

---

## 7) Environment o‘zgaruvchilar

`.env.example` dan nusxa olib `.env` yarating.

Majburiy/asosiy qiymatlar:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `SMTP_USE_TLS`
- `SMTP_USE_STARTTLS`
- `EMAIL_DELIVERY_MODE` (`direct` yoki `celery`)
- `REDIS_URL`
- `RATE_LIMIT_LOGIN_LIMIT`
- `RATE_LIMIT_LOGIN_WINDOW_SECONDS`
- `RATE_LIMIT_RESEND_LIMIT`
- `RATE_LIMIT_RESEND_WINDOW_SECONDS`
- `RATE_LIMIT_FORGOT_LIMIT`
- `RATE_LIMIT_FORGOT_WINDOW_SECONDS`

---

## 8) Ishga tushirish (Docker bilan)

1. `.env` fayl yarating:
   - Windows: `.env.example` ni `.env` qilib nusxalang
2. Docker’ni yoqing
3. Quyidagini ishga tushiring:

```bash
docker compose up --build
```

Nima bo‘ladi:
- `db` (PostgreSQL) ishga tushadi
- `redis` ishga tushadi
- `app` ishga tushishdan oldin `alembic upgrade head` bajaradi
- `celery-worker` ishga tushadi

Swagger:
- `http://localhost:8000/docs`

---

## 9) Local (docker’siz) ishga tushirish

1. Virtual env aktiv qiling
2. Install:

```bash
pip install -r requirements.txt
```

3. Migratsiya:

```bash
alembic upgrade head
```

4. API:

```bash
uvicorn main:app --reload
```

5. Celery worker (alohida terminalda):

```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info -Q celery
```

Gmailga real kod yuborish uchun `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
EMAIL_FROM=your_email@gmail.com
SMTP_USE_TLS=false
SMTP_USE_STARTTLS=true
EMAIL_DELIVERY_MODE=direct
```

`SMTP_PASSWORD` joyiga oddiy Gmail parol emas, Gmail App Password yoziladi.
App Password olish uchun Gmail akkauntda 2-Step Verification yoqilgan bo'lishi kerak.
Faqat `uvicorn` bilan ishlatsangiz `EMAIL_DELIVERY_MODE=direct` qiling; `EMAIL_DELIVERY_MODE=celery` bo'lsa Redis va Celery worker ham ishlashi kerak.

---

## 10) Hozircha soddalashtirilgan joylar

- Email yuborish uchun SMTP sozlanmasa, dev fallback (`print`) ishlaydi.
- Hozir testlar (`pytest`) yozilmagan.
- Admin yaratish seed/management command hali qo‘shilmagan.

---

## 11) Keyingi tavsiya etiladigan ishlar

- Admin create command (superuser) qo‘shish
- Pytest testlar (auth flow bo‘yicha)
- CI pipeline (lint + tests)
- API response formatni yagona standardga o‘tkazish
- Login history / audit log qo‘shish

---

## 12) Tezkor tekshiruv checklist

- [ ] Register ishlaydi
- [ ] Verification code emailga boradi
- [ ] Verify email ishlaydi
- [ ] Login access+refresh beradi
- [ ] Refresh rotation ishlaydi
- [ ] Logout tokenni revoke qiladi
- [ ] Logout all devices ishlaydi
- [ ] Forgot/reset password ishlaydi
- [ ] `/me` access token bilan ishlaydi
- [ ] Role-based endpointlar to‘g‘ri cheklaydi
- [ ] Rate limit ishlaydi
- [ ] Docker compose bilan tizim ko‘tariladi

