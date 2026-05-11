# Jobify API

Jobify API - FastAPI yordamida yozilgan ish topish platformasi backend qismi.

Loyihada quyidagi asosiy qismlar bor:

- Auth: register, email verify, login, refresh token, logout
- Candidate: vakansiyaga apply qilish, applicationlarni ko'rish, resume yuklash
- HR: vakansiya yaratish, applicationlarni boshqarish, candidate bilan chat
- Admin: HR akkauntlarni approve qilish, support threadlarni boshqarish
- Support: candidate/HR admin bilan yozishishi
- Public vacancies: ochiq vakansiyalar ro'yxati va detail

Postman uchun alohida qo'llanma:

```text
POSTMAN_TESTING.md
```

---

## 1. Texnologiyalar

- Python
- FastAPI
- SQLAlchemy Async
- PostgreSQL
- Alembic
- JWT
- Passlib + bcrypt
- Redis
- Celery
- SMTP/Gmail
- Docker Compose
- Pydantic

---

## 2. Loyiha strukturasi

```text
.
├── main.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── alembic/
├── postman/
├── POSTMAN_TESTING.md
└── app/
    ├── api/
    │   ├── auth.py
    │   ├── admin.py
    │   ├── hr.py
    │   ├── vacancies.py
    │   ├── candidate_recruitment.py
    │   ├── support.py
    │   └── deps.py
    ├── core/
    │   ├── config.py
    │   ├── database.py
    │   ├── security.py
    │   ├── redis_client.py
    │   └── celery_app.py
    ├── models/
    ├── schemas/
    ├── services/
    └── tasks/
```

---

## 3. Ishga tushirish

### 3.1. Docker bilan

1. `.env.example` faylidan `.env` yarating.
2. Docker Desktop yoki Docker Engine ishga tushgan bo'lishi kerak.
3. Quyidagi commandni bajaring:

```bash
docker compose up --build
```

Docker Compose quyidagilarni ishga tushiradi:

- FastAPI app
- PostgreSQL
- Redis
- Celery worker
- Alembic migration

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

### 3.2. Local ishga tushirish

Virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

Dependency install:

```bash
pip install -r requirements.txt
```

Migration:

```bash
alembic upgrade head
```

API:

```bash
python -m uvicorn main:app --reload --port 8001
```

Local API:

```text
http://127.0.0.1:8001
```

Swagger:

```text
http://127.0.0.1:8001/docs
```

Eslatma:

```text
Docker porti odatda 8000.
Local uvicorn porti siz bergan portga bog'liq, masalan 8001.
Postman URL ham shu port bilan bir xil bo'lishi kerak.
```

---

## 4. Environment sozlamalari

`.env.example` dan `.env` yarating.

Namuna:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/jobify
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
EMAIL_FROM=your_email@gmail.com
SMTP_USE_TLS=false
SMTP_USE_STARTTLS=true
EMAIL_DELIVERY_MODE=direct

REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_LOGIN_LIMIT=5
RATE_LIMIT_LOGIN_WINDOW_SECONDS=60
RATE_LIMIT_RESEND_LIMIT=1
RATE_LIMIT_RESEND_WINDOW_SECONDS=60
RATE_LIMIT_FORGOT_LIMIT=3
RATE_LIMIT_FORGOT_WINDOW_SECONDS=300
```

Docker ichida `DATABASE_URL` va `REDIS_URL` service nomlari bilan bo'ladi:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/jobify
REDIS_URL=redis://redis:6379/0
```

Localda esa:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/jobify
REDIS_URL=redis://localhost:6379/0
```

---

## 5. Gmail va verification code

Gmailga kod yuborish uchun oddiy Gmail parol ishlatilmaydi.

Kerak bo'ladi:

```text
Gmail App Password
```

App Password olish:

```text
Google Account
Security
2-Step Verification
App passwords
```

`.env`:

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

`EMAIL_DELIVERY_MODE`:

```text
direct - email uvicorn process ichida yuboriladi
celery - email Celery worker orqali yuboriladi
```

Faqat `uvicorn` ishlatayotgan bo'lsangiz:

```env
EMAIL_DELIVERY_MODE=direct
```

Celery ishlatmoqchi bo'lsangiz Redis va worker ham ishlashi kerak:

```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info -Q celery
```

---

## 6. Kod terminalga chiqishi

Register yoki forgot password qilinganda kod terminalga ham print bo'ladi.

Register:

```text
[VERIFICATION-CODE] email=candidate@example.com code=123456
```

Forgot password:

```text
[RESET-CODE] email=candidate@example.com code=654321
```

Kod terminalga chiqmasa:

```text
1. Postman URL porti uvicorn porti bilan bir xil bo'lishi kerak.
   Masalan uvicorn --port 8001 bo'lsa:
   http://127.0.0.1:8001/api/auth/register/

2. Kod faqat shu endpointlarda chiqadi:
   POST /api/auth/register/
   POST /api/auth/resend-verification-code/
   POST /api/auth/forgot-password/

3. Oldin ro'yxatdan o'tgan email bilan register qilsangiz 409 qaytadi.
   Bunday holatda yangi kod yaratilmaydi.
   Yangi email ishlating yoki resend endpointdan foydalaning.
```

---

## 7. Role lar

Loyihada 3 ta role bor:

```text
candidate
hr
admin
```

Candidate:

- register qila oladi
- email verify qiladi
- login qiladi
- vakansiyaga apply qiladi
- resume yuklaydi
- HR bilan chat qiladi
- support thread ochadi

HR:

- register qila oladi
- email verify qiladi
- admin approve qilmaguncha vakansiya joylay olmaydi
- approve bo'lgandan keyin vakansiya yaratadi
- applicationlarni ko'radi
- candidate murojaatini accept/reject qiladi
- candidate bilan chat qiladi
- support thread ochadi

Admin:

- oddiy register orqali yaratilmaydi
- pending HR larni ko'radi
- HR ni approve qiladi
- barcha support threadlarni ko'radi
- supportga javob beradi
- support threadni close qiladi

---

## 8. Asosiy flow

```text
1. Candidate register qiladi
2. Terminal yoki Gmaildan verification code olinadi
3. Candidate email verify qiladi
4. Candidate login qiladi
5. HR register qiladi
6. HR email verify qiladi
7. Admin HR ni approve qiladi
8. HR vakansiya yaratadi
9. Candidate public vacancies ro'yxatidan vakansiyani ko'radi
10. Candidate vakansiyaga apply qiladi
11. HR applicationni ko'radi
12. HR accept qilsa chat ochiladi
13. HR va candidate chat orqali yozishadi
14. Candidate yoki HR support thread ochadi
15. Admin supportga javob beradi yoki yopadi
```

---

## 9. Endpointlar

### Auth

Base URL:

```text
/api/auth
```

Endpointlar:

```text
POST /register/
POST /verify-email/
POST /resend-verification-code/
POST /login/
POST /refresh/
POST /logout/
POST /logout-all/
GET  /me/
POST /change-password/
POST /forgot-password/
POST /reset-password/
```

---

### Public vacancies

Base URL:

```text
/api/vacancies
```

Endpointlar:

```text
GET  /
GET  /{vacancy_id}/
POST /{vacancy_id}/apply/
```

`GET` endpointlar token talab qilmaydi.
`apply` uchun candidate token kerak.

---

### Candidate

Base URL:

```text
/api/candidate
```

Endpointlar:

```text
GET    /applications/
GET    /applications/{application_id}/
POST   /applications/{application_id}/messages/
GET    /resume/
GET    /resume/download/
POST   /resume/
PUT    /resume/
DELETE /resume/
```

Resume upload/update uchun Postman Body:

```text
form-data
key: file
type: File
```

---

### HR

Base URL:

```text
/api/hr
```

Endpointlar:

```text
GET    /status/
POST   /vacancies/
GET    /vacancies/
GET    /vacancies/{vacancy_id}/
DELETE /vacancies/{vacancy_id}/
GET    /applications/
GET    /applications/{application_id}/
GET    /applications/{application_id}/resume/
POST   /applications/{application_id}/accept/
POST   /applications/{application_id}/reject/
POST   /applications/{application_id}/messages/
```

---

### Support

Base URL:

```text
/api/support
```

Endpointlar:

```text
POST /threads/
GET  /threads/
GET  /threads/{thread_id}/
POST /threads/{thread_id}/messages/
```

Bu endpointlar HR yoki candidate token bilan ishlaydi.

---

### Admin

Base URL:

```text
/api/admin
```

Endpointlar:

```text
GET  /pending-hr/
POST /hr/{user_id}/approve/
GET  /support/threads/
GET  /support/threads/{thread_id}/
POST /support/threads/{thread_id}/messages/
POST /support/threads/{thread_id}/close/
```

Bu endpointlar admin token talab qiladi.

---

## 10. Postman

To'liq Postman qo'llanma:

```text
POSTMAN_TESTING.md
```

Import qilinadigan Postman fayllar:

```text
postman/Jobify_Auth_API.postman_collection.json
postman/Jobify_Auth_API.postman_environment.json
```

Postman ishlatishda portga e'tibor bering:

```text
Docker: http://127.0.0.1:8000
Local uvicorn --port 8001: http://127.0.0.1:8001
```

---

## 11. Status kodlar

Ko'p uchraydigan javoblar:

```text
200 - OK
201 - Created
204 - No Content
400 - Bad Request
401 - Unauthorized
403 - Forbidden
404 - Not Found
409 - Conflict
422 - Validation Error
429 - Too Many Requests
```

Misollar:

```text
409 - email oldin ro'yxatdan o'tgan
403 - role mos emas yoki HR approve qilinmagan
401 - token noto'g'ri yoki login qilinmagan
422 - body noto'g'ri yuborilgan
429 - rate limit
```

---

## 12. Muhim eslatmalar

- Password hash holatda saqlanadi.
- Access token va refresh token alohida.
- Refresh token rotation ishlaydi.
- Logout refresh tokenni revoke qiladi.
- Change password barcha refresh tokenlarni revoke qiladi.
- Email verification code va reset code bir martalik.
- HR vakansiya joylashdan oldin admin approve qilishi kerak.
- Candidate bitta vakansiyaga faqat bir marta apply qila oladi.
- Chat faqat HR applicationni accept qilgandan keyin ochiladi.

