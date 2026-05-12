# Jobify API

Jobify API - FastAPI yordamida yozilgan ish topish platformasi backend qismi.
Loyiha HeadHunter/ish qidirish platformasiga o'xshash qilib tuzilgan.

Bu backend orqali:

- foydalanuvchi ro'yxatdan o'tadi;
- email tasdiqlash kodi oladi;
- login qiladi;
- candidate vakansiyaga murojaat yuboradi;
- candidate resume yuklaydi;
- HR vakansiya joylaydi;
- HR candidate murojaatini accept/reject qiladi;
- HR va candidate chat qiladi;
- HR yoki candidate support orqali adminga yozadi;
- admin HR akkauntlarni approve qiladi;
- admin support xabarlariga javob beradi.

To'liq Postman qo'llanma:

```text
POSTMAN_TESTING.md
```

---

## 1. Loyihadagi asosiy rollar

Loyihada 3 ta role bor:

```text
candidate
hr
admin
```

### Candidate nima qila oladi?

- Register qiladi.
- Email verification code orqali akkauntini tasdiqlaydi.
- Login qiladi.
- Ochiq vakansiyalarni ko'radi.
- Vakansiyaga apply qiladi.
- O'z applicationlarini ko'radi.
- Resume yuklaydi, yangilaydi, o'chiradi.
- HR applicationni accept qilgandan keyin chatga yozadi.
- Support thread ochib admin bilan yozishadi.

### HR nima qila oladi?

- Register qiladi.
- Email verification code orqali akkauntini tasdiqlaydi.
- Admin approve qilmaguncha vakansiya joylay olmaydi.
- Admin approve qilgandan keyin vakansiya yaratadi.
- O'z vakansiyalarini ko'radi.
- Candidate applicationlarini ko'radi.
- Candidate resumesini download qiladi.
- Applicationni accept yoki reject qiladi.
- Accept qilingan application bo'yicha candidate bilan chat qiladi.
- Support thread ochib admin bilan yozishadi.

### Admin nima qila oladi?

- Oddiy register endpoint orqali yaratilmaydi.
- Pending HR akkauntlarni ko'radi.
- HR akkauntni approve qiladi.
- Barcha support threadlarni ko'radi.
- Support threadga javob yozadi.
- Support threadni close qiladi.

---

## 2. Nimalar qilingan?

### Auth

- Register
- Email verification
- Verification code resend
- Login
- Access token
- Refresh token
- Refresh token rotation
- Logout
- Logout all devices
- Me endpoint
- Change password
- Forgot password
- Reset password
- Rate limit

### Vacancy

- Public vacancy list
- Public vacancy detail
- Candidate apply
- HR vacancy create
- HR vacancy list
- HR vacancy detail
- HR vacancy soft delete

### Application va chat

- Candidate application list/detail
- HR application list/detail
- HR accept/reject
- Candidate va HR chat messages
- Chat faqat application `chat_open` bo'lgandan keyin ishlaydi

### Resume

- Candidate resume upload
- Candidate resume update
- Candidate resume detail
- Candidate resume download
- Candidate resume delete
- HR candidate resume download

### Support

- Candidate yoki HR support thread ochadi
- Candidate yoki HR o'z threadlarini ko'radi
- Candidate yoki HR threadga message yozadi
- Admin barcha threadlarni ko'radi
- Admin javob yozadi
- Admin threadni close qiladi

### Admin

- Pending HR list
- HR approve
- Support thread management

---

## 3. Yangi qo'shilgan narsalar

Avval loyiha asosan auth module edi. Hozir quyidagi yangi qismlar qo'shilgan:

```text
app/api/admin.py
app/api/hr.py
app/api/vacancies.py
app/api/candidate_recruitment.py
app/api/support.py
```

Yangi schema fayllar:

```text
app/schemas/admin.py
app/schemas/hr_vacancy.py
app/schemas/resume.py
app/schemas/support.py
```

Yangi service fayllar:

```text
app/services/admin_service.py
app/services/resume_service.py
app/services/support_service.py
app/services/vacancy_application_service.py
```

Yangi model qismlar:

```text
app/models/vacancy.py
app/models/candidate_resume.py
app/models/support.py
```

Yangi funksiyalar:

- HR approval flow
- Vakansiya yaratish va o'chirish
- Candidate apply flow
- Application status: `pending`, `chat_open`, `rejected`
- Candidate/HR chat
- Resume upload/download
- Support thread
- Admin support management
- Gmail direct email mode
- Verification/reset code terminalga print bo'lishi
- Postman uchun to'liq qo'llanma

---

## 4. Texnologiyalar

### FastAPI

API endpointlar yozish uchun ishlatilgan.

Qayerda:

```text
main.py
app/api/*.py
```

### SQLAlchemy Async

PostgreSQL bilan async ishlash uchun ishlatilgan.

Qayerda:

```text
app/core/database.py
app/models/*.py
app/services/*.py
```

### PostgreSQL

Asosiy database.

Unda saqlanadi:

- users
- verification codes
- password reset codes
- refresh tokens
- vacancies
- vacancy applications
- application messages
- candidate resumes
- support threads
- support messages

### Alembic

Database migration uchun.

Qayerda:

```text
alembic/
alembic.ini
```

### JWT

Login, access token, refresh token uchun.

Qayerda:

```text
app/core/security.py
```

### Passlib + bcrypt

Passwordni hash qilish uchun.

Qayerda:

```text
app/core/security.py
```

### Redis

Redis ikki joyda kerak bo'ladi:

1. Rate limit uchun.
2. Celery broker/backend uchun.

To'liq tushuntirish pastda alohida berilgan.

### Celery

Email yuborishni background task qilish uchun ishlatiladi.

To'liq tushuntirish pastda alohida berilgan.

### SMTP/Gmail

Email verification code, reset code va HR notification yuborish uchun.

Qayerda:

```text
app/tasks/email_tasks.py
app/services/email_service.py
```

### python-multipart

Resume upload qilish uchun.

Qayerda:

```text
POST /api/candidate/resume/
PUT  /api/candidate/resume/
```

---

## 5. Redis qachon va qayerda ishlatilgan?

Redis loyihada 2 ta asosiy vazifa uchun ishlatilgan.

---

### 5.1. Rate limit uchun

Redis login, resend verification va forgot password endpointlarida ko'p request yuborishni cheklash uchun ishlatiladi.

Qayerda yozilgan:

```text
app/core/redis_client.py
```

Asosiy funksiya:

```python
enforce_rate_limit(key, limit, window_seconds)
```

U nima qiladi:

```text
1. Redis ichida key bo'yicha counter oshiradi.
2. Birinchi request bo'lsa expire vaqt qo'yadi.
3. Counter limitdan oshsa False qaytaradi.
4. False bo'lsa API 429 Too Many Requests qaytaradi.
```

Qayerlarda chaqirilgan:

```text
app/api/auth.py
```

Endpointlar:

```text
POST /api/auth/resend-verification-code/
POST /api/auth/login/
POST /api/auth/forgot-password/
```

Masalan:

```text
Login endpointda bir IP va email uchun ko'p marta login qilish cheklanadi.
```

`.env` sozlamalari:

```env
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_LOGIN_LIMIT=5
RATE_LIMIT_LOGIN_WINDOW_SECONDS=60
RATE_LIMIT_RESEND_LIMIT=1
RATE_LIMIT_RESEND_WINDOW_SECONDS=60
RATE_LIMIT_FORGOT_LIMIT=3
RATE_LIMIT_FORGOT_WINDOW_SECONDS=300
```

Muhim:

```text
Agar Redis ishlamay qolsa, auth endpointlar blok bo'lib qolmasligi uchun fail-open qilingan.
Ya'ni Redis xato bersa enforce_rate_limit True qaytaradi.
```

Koddagi joyi:

```text
app/core/redis_client.py
```

---

### 5.2. Celery broker/backend uchun

Celery tasklarni navbatga qo'yish uchun broker kerak.
Bu loyihada broker sifatida Redis ishlatilgan.

Qayerda:

```text
app/core/celery_app.py
```

Kod ma'nosi:

```python
celery_app = Celery(
    "jobify_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
```

Bu nimani anglatadi:

```text
API email taskni Redis navbatiga tashlaydi.
Celery worker Redisdan taskni olib email yuboradi.
```

`.env`:

```env
REDIS_URL=redis://localhost:6379/0
```

Docker ichida:

```env
REDIS_URL=redis://redis:6379/0
```

---

## 6. Celery qachon va qayerda ishlatilgan?

Celery email yuborishni background task qilish uchun ishlatilgan.

Nima uchun kerak:

```text
Agar email yuborish request ichida to'g'ridan-to'g'ri qilinsa, API sekinlashishi mumkin.
Celery bilan API taskni navbatga tashlaydi va tez javob qaytaradi.
Emailni esa worker alohida yuboradi.
```

Qayerda konfiguratsiya qilingan:

```text
app/core/celery_app.py
```

Qayerda task bor:

```text
app/tasks/email_tasks.py
```

Task nomi:

```python
send_email_task
```

Qayerda chaqiriladi:

```text
app/services/email_service.py
```

Email yuborish flow:

```text
register
  -> verification code yaratiladi
  -> send_verification_code()
  -> send_email()
  -> EMAIL_DELIVERY_MODE ga qaraydi

forgot-password
  -> reset code yaratiladi
  -> send_password_reset_code()
  -> send_email()
  -> EMAIL_DELIVERY_MODE ga qaraydi

HR register
  -> adminlarga notification yuboriladi
  -> send_hr_registration_admin_notification()
  -> send_email()
```

Celery qachon ishlaydi:

```text
EMAIL_DELIVERY_MODE=celery bo'lsa
```

Worker command:

```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info -Q celery
```

Docker Compose ichida worker bor:

```text
celery-worker
```

Docker command:

```bash
docker compose up --build
```

Shunda quyidagilar birga ishlaydi:

```text
app
db
redis
celery-worker
```

---

## 7. EMAIL_DELIVERY_MODE nima?

Email yuborishda 2 xil rejim bor:

```text
direct
celery
```

### direct

`.env`:

```env
EMAIL_DELIVERY_MODE=direct
```

Bu holatda:

```text
Email uvicorn process ichida yuboriladi.
Celery worker kerak emas.
Local development uchun qulay.
```

Siz faqat shuni ishlatayotgan bo'lsangiz:

```bash
python -m uvicorn main:app --reload --port 8001
```

`direct` mode yaxshi.

---

### celery

`.env`:

```env
EMAIL_DELIVERY_MODE=celery
```

Bu holatda:

```text
API email taskni Redisga tashlaydi.
Celery worker Redisdan taskni olib email yuboradi.
Redis va celery-worker ishlashi shart.
```

Kerak bo'ladi:

```bash
redis-server
celery -A app.core.celery_app.celery_app worker --loglevel=info -Q celery
```

Docker bilan ishlatsangiz bu avtomatik docker-compose orqali ko'tariladi.

---

## 8. Verification/reset code terminalda chiqishi

Register yoki forgot password qilinganda kod terminalga ham chiqadi.

Register qilganda:

```text
[VERIFICATION-CODE] email=candidate@example.com code=123456
```

Forgot password qilganda:

```text
[RESET-CODE] email=candidate@example.com code=654321
```

Bu qayerda yozilgan:

```text
app/services/email_service.py
```

Nima uchun kerak:

```text
Local developmentda Gmail ishlamasa ham kodni terminaldan olib Postmanda ishlatish uchun.
```

Kod terminalga chiqmasa:

```text
1. Postman portini tekshiring.
   Uvicorn --port 8001 bo'lsa:
   http://127.0.0.1:8001/api/auth/register/

2. Kod faqat shu endpointlarda chiqadi:
   POST /api/auth/register/
   POST /api/auth/resend-verification-code/
   POST /api/auth/forgot-password/

3. Oldin register bo'lgan email bilan register qilsangiz 409 qaytadi.
   Bunday holatda yangi kod yaratilmaydi.

4. Yangi email ishlating yoki resend-verification-code endpointini chaqiring.
```

---

## 9. Gmail sozlash

Gmail bilan real email yuborish uchun oddiy Gmail password ishlamaydi.
Gmail App Password kerak.

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

Muhim:

```text
SMTP_PASSWORD=oddiy_gmail_parol emas
SMTP_PASSWORD=Gmail App Password
```

Agar Gmail sozlanmagan bo'lsa:

```text
Kod baribir terminalda print bo'ladi.
```

---

## 10. Loyiha strukturasi

```text
.
├── main.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── POSTMAN_TESTING.md
├── postman/
│   ├── Jobify_Auth_API.postman_collection.json
│   └── Jobify_Auth_API.postman_environment.json
├── alembic/
│   └── versions/
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
    │   ├── user.py
    │   ├── refresh_token.py
    │   ├── email_verification_code.py
    │   ├── password_reset_code.py
    │   ├── vacancy.py
    │   ├── candidate_resume.py
    │   └── support.py
    ├── schemas/
    │   ├── auth.py
    │   ├── admin.py
    │   ├── hr_vacancy.py
    │   ├── resume.py
    │   └── support.py
    ├── services/
    │   ├── auth_service.py
    │   ├── admin_service.py
    │   ├── email_service.py
    │   ├── resume_service.py
    │   ├── support_service.py
    │   └── vacancy_application_service.py
    └── tasks/
        └── email_tasks.py
```

---

## 11. Ishga tushirish

### Docker bilan

1. `.env.example` dan `.env` yarating.
2. Docker ishga tushgan bo'lsin.
3. Command:

```bash
docker compose up --build
```

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Docker ichida `.env` uchun:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/jobify
REDIS_URL=redis://redis:6379/0
```

`docker-compose.yml` Docker ichida `DATABASE_URL` va `REDIS_URL` ni o'zi `db`/`redis` qilib override qiladi. Shuning uchun `.env` ichida local uchun `localhost` yozilgan bo'lsa ham Docker app container noto'g'ri hostga ulanib qolmaydi.

Browserda `ERR_CONNECTION_REFUSED` chiqsa:

```text
1. jobify-app container ishlamayotgan bo'lishi mumkin.
2. Docker Desktop -> Containers -> jobify-app -> Logs ni oching.
3. Yoki terminalda:
```

```powershell
docker compose ps
docker compose logs app
```

Normal holatda quyidagilar running bo'lishi kerak:

```text
jobify-app
jobify-db
jobify-redis
jobify-celery-worker
```

Docker build vaqtida shunday xato chiqsa:

```text
target celery-worker: failed to receive status: rpc error: code = Unavailable desc = error reading from server: EOF
```

Yoki container yaratishda shunday xato chiqsa:

```text
request returned 502 Bad Gateway for API route ... containers/create?name=jobify-app
```

Bu odatda Docker Desktop/BuildKit build jarayonida uzilib qolganini bildiradi. Loyiha `docker-compose.yml`da bitta `jobs-app:latest` image build qiladi, `celery-worker` ham shu image'dan ishlaydi.

Build yengilroq bo'lishi uchun `.dockerignore` qo'shilgan va Dockerfile faqat kerakli fayllarni image ichiga copy qiladi.

Windows PowerShell'da qayta urinish uchun:

```powershell
docker compose down
docker builder prune -f
docker compose build --no-cache app
docker compose up
```

Agar yana chiqsa:

```text
1. Docker Desktopni restart qiling.
2. PowerShellni yopib qayta oching.
3. docker context use desktop-linux commandini ishlating.
4. Eski alohida redis containerlarni stop/delete qiling.
5. Docker Desktop resources/memory yetarli ekanini tekshiring.
6. Qayta docker compose up --build qiling.
```

Docker Desktop engine nosog'lom bo'lib qolsa:

```powershell
wsl --shutdown
```

Keyin Docker Desktopni qayta oching va:

```powershell
docker ps
docker compose up --build
```

---

### Local bilan

Virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install:

```bash
pip install -r requirements.txt
```

Migration:

```bash
alembic upgrade head
```

Run:

```bash
python -m uvicorn main:app --reload --port 8001
```

API:

```text
http://127.0.0.1:8001
```

Swagger:

```text
http://127.0.0.1:8001/docs
```

Local `.env` uchun:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/jobify
REDIS_URL=redis://localhost:6379/0
EMAIL_DELIVERY_MODE=direct
```

---

## 12. Environment variables

Asosiy sozlamalar:

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

---

## 13. Database modellar

Asosiy tablelar:

```text
users
email_verification_codes
password_reset_codes
refresh_tokens
vacancies
vacancy_applications
application_messages
candidate_resumes
support_threads
support_messages
```

### users

Saqlaydi:

- email
- password_hash
- role
- is_active
- is_verified
- hr_approved

### vacancies

Saqlaydi:

- HR yaratgan vakansiya
- title
- description
- company
- location
- salary
- employment_type
- work_mode
- expires_at

### vacancy_applications

Saqlaydi:

- qaysi candidate qaysi vacancyga apply qilgani
- initial_message
- status: `pending`, `chat_open`, `rejected`

### application_messages

Saqlaydi:

- HR va candidate orasidagi chat xabarlari

### candidate_resumes

Saqlaydi:

- candidate resume fayl pathi
- original filename
- content type
- size

### support_threads

Saqlaydi:

- HR/candidate ochgan support mavzusi
- status: `open`, `closed`

### support_messages

Saqlaydi:

- support ichidagi xabarlar

---

## 14. API endpointlar

### Auth

Base:

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

Base:

```text
/api/vacancies
```

Endpointlar:

```text
GET  /
GET  /{vacancy_id}/
POST /{vacancy_id}/apply/
```

Izoh:

```text
GET endpointlar token talab qilmaydi.
apply uchun candidate token kerak.
```

---

### Candidate

Base:

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

Resume upload uchun:

```text
Body -> form-data
key  -> file
type -> File
```

---

### HR

Base:

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

Izoh:

```text
HR vakansiya yaratishi uchun admin approve qilgan bo'lishi kerak.
```

---

### Support

Base:

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

Izoh:

```text
Bu endpointlar candidate yoki HR token bilan ishlaydi.
```

---

### Admin

Base:

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

Izoh:

```text
Bu endpointlar admin token talab qiladi.
```

---

## 15. Asosiy ish flow

```text
1. Candidate register qiladi.
2. Terminaldan [VERIFICATION-CODE] olinadi.
3. Candidate email verify qiladi.
4. Candidate login qiladi.
5. HR register qiladi.
6. HR email verify qiladi.
7. Admin login qiladi.
8. Admin pending HR ro'yxatini ko'radi.
9. Admin HR ni approve qiladi.
10. HR login qiladi.
11. HR vakansiya yaratadi.
12. Candidate public vacancies orqali vakansiyani ko'radi.
13. Candidate vakansiyaga apply qiladi.
14. HR applicationni ko'radi.
15. HR applicationni accept qiladi.
16. Candidate va HR chat qiladi.
17. Candidate yoki HR support thread ochadi.
18. Admin support threadga javob beradi yoki close qiladi.
```

---

## 16. Postman

To'liq qo'llanma:

```text
POSTMAN_TESTING.md
```

Import fayllar:

```text
postman/Jobify_Auth_API.postman_collection.json
postman/Jobify_Auth_API.postman_environment.json
```

Portga e'tibor bering:

```text
Docker: http://127.0.0.1:8000
Local uvicorn --port 8001: http://127.0.0.1:8001
```

---

## 17. Status kodlar

Ko'p uchraydigan statuslar:

```text
200 OK
201 Created
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
429 Too Many Requests
```

Misollar:

```text
409 - email oldin ro'yxatdan o'tgan
403 - role mos emas yoki HR approve qilinmagan
401 - token noto'g'ri
422 - request body noto'g'ri
429 - rate limit
```

---

## 18. Xavfsizlik

Qilingan ishlar:

- Password hash qilinadi.
- Access token va refresh token alohida.
- Refresh token DBda hash holatda saqlanadi.
- Refresh token rotation bor.
- Logout refresh tokenni revoke qiladi.
- Logout all barcha tokenlarni revoke qiladi.
- Change password barcha refresh tokenlarni revoke qiladi.
- Verification/reset code expire bo'ladi.
- Verification/reset code bir martalik.
- Rate limit Redis orqali ishlaydi.
- Role-based access bor.

---

## 19. Muhim eslatmalar

- Admin oddiy register orqali yaratilmaydi.
- HR register qilgandan keyin admin approve qilishi kerak.
- Candidate bitta vakansiyaga faqat bir marta apply qila oladi.
- Chat faqat HR applicationni accept qilgandan keyin ishlaydi.
- Resume upload uchun `python-multipart` kerak.
- Gmail ishlamasa ham kod terminalda print bo'ladi.
- Redis rate limit uchun ishlatiladi.
- Celery faqat `EMAIL_DELIVERY_MODE=celery` bo'lsa email yuborishda ishlatiladi.
- Local developmentda odatda `EMAIL_DELIVERY_MODE=direct` qulay.

