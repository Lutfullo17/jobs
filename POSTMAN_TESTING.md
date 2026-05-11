# Postman orqali test qilish

API ni ishga tushirish:

```bash
docker compose up --build
```

Asosiy URL:

```text
http://127.0.0.1:8000
```

Postman'da JSON yuboriladigan requestlarda:

```text
Headers:
Content-Type: application/json
```

Token kerak bo'ladigan requestlarda:

```text
Headers:
Authorization: Bearer access_token_value
```

`access_token_value` o'rniga login natijasida kelgan `access_token` yoziladi.

Role bo'yicha tokenlar:

```text
candidate token → candidate API lar uchun
hr token        → HR API lar uchun
admin token     → Admin API lar uchun
```

`verification code` va `reset code` emailga yuboriladi. Agar SMTP sozlanmagan bo'lsa, kod `celery-worker` logida chiqadi.

Masalan:

```text
[EMAIL-DEV][CELERY] To=candidate@example.com | Subject=... | Body=Sizning tasdiqlash kodingiz: 123456
```

Server terminalida kod alohida ham print bo'ladi:

```text
[VERIFICATION-CODE] email=candidate@example.com code=123456
[RESET-CODE] email=candidate@example.com code=654321
```

Kod terminalga chiqmasa tekshiring:

```text
1. Postman URL siz ishlatayotgan port bo'lishi kerak.
   Masalan uvicorn --port 8001 bo'lsa:
   http://127.0.0.1:8001/api/auth/register/

2. Kod faqat shu requestlarda chiqadi:
   POST /api/auth/register/
   POST /api/auth/resend-verification-code/
   POST /api/auth/forgot-password/

3. Oldin register qilingan email bilan qayta register qilsangiz 409 qaytadi,
   bunday holatda yangi kod yaratilmaydi.
   Yangi email yozing yoki resend-verification-code ishlating.
```

Gmailga kod kelishi uchun `.env` ichida shunday yozing:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
EMAIL_FROM=your_email@gmail.com
SMTP_USE_TLS=false
SMTP_USE_STARTTLS=true
EMAIL_DELIVERY_MODE=direct
```

Eslatma:

```text
SMTP_PASSWORD joyiga oddiy Gmail parol emas, Gmail App Password yoziladi.
Gmail App Password olish uchun Google Account → Security → 2-Step Verification → App passwords.
Agar EMAIL_DELIVERY_MODE=celery bo'lsa, Redis bilan birga celery-worker ham ishlab turishi kerak.
Faqat uvicorn bilan ishlatsangiz EMAIL_DELIVERY_MODE=direct qiling.
```

---

# 1. Auth API

## 1.1. API ishlayotganini tekshirish

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "message": "Jobify Auth API is running"
}
```

---

## 1.2. Candidate register

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/auth/register/
```

Body:

```json
{
  "email": "candidate@example.com",
  "password": "Password123!",
  "confirm_password": "Password123!",
  "role": "candidate"
}
```

Natija:

```json
{
  "message": "Elektron pochta tasdiqlash kodi yuborildi."
}
```

---

## 1.3. HR register

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/auth/register/
```

Body:

```json
{
  "email": "hr@example.com",
  "password": "Password123!",
  "confirm_password": "Password123!",
  "role": "hr"
}
```

Natija:

```json
{
  "message": "Elektron pochta tasdiqlash kodi yuborildi."
}
```

Eslatma:

```text
HR register bo'lgandan keyin admin uni approve qilmaguncha vakansiya joylay olmaydi.
```

---

## 1.4. Email tasdiqlash

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/auth/verify-email/
```

Body:

```json
{
  "email": "candidate@example.com",
  "code": "123456"
}
```

Natija:

```json
{
  "user": {
    "id": 1,
    "email": "candidate@example.com",
    "role": "candidate",
    "is_active": true,
    "is_verified": true,
    "hr_approved": true,
    "created_at": "2026-05-11T10:00:00"
  },
  "message": "Elektron pochta muvaffaqiyatli tasdiqlandi."
}
```

Eslatma:

```text
123456 o'rniga celery-worker logida chiqqan kod yoziladi.
```

---

## 1.5. Verification code qayta yuborish

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/auth/resend-verification-code/
```

Body:

```json
{
  "email": "candidate@example.com"
}
```

Natija:

```json
{
  "message": "Tasdiqlash kodi yuborildi."
}
```

---

## 1.6. Login

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/auth/login/
```

Body:

```json
{
  "email": "candidate@example.com",
  "password": "Password123!"
}
```

Natija:

```json
{
  "access_token": "access_token_value",
  "refresh_token": "refresh_token_value",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "candidate@example.com",
    "role": "candidate",
    "is_active": true,
    "is_verified": true,
    "hr_approved": true,
    "created_at": "2026-05-11T10:00:00"
  }
}
```

Eslatma:

```text
access_token_value ni Authorization headerga qo'yasiz.
refresh_token_value ni refresh va logout requestlarida ishlatasiz.
```

---

## 1.7. Me

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/auth/me/
```

Headers:

```text
Authorization: Bearer access_token_value
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "id": 1,
  "email": "candidate@example.com",
  "role": "candidate",
  "is_active": true,
  "is_verified": true,
  "hr_approved": true,
  "created_at": "2026-05-11T10:00:00"
}
```

---

## 1.8. Refresh token

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/auth/refresh/
```

Body:

```json
{
  "refresh_token": "refresh_token_value"
}
```

Natija:

```json
{
  "access_token": "new_access_token_value",
  "refresh_token": "new_refresh_token_value",
  "token_type": "bearer"
}
```

Eslatma:

```text
Refresh qilgandan keyin eski refresh_token ishlamaydi.
```

---

## 1.9. Parolni o'zgartirish

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/auth/change-password/
```

Headers:

```text
Authorization: Bearer access_token_value
```

Body:

```json
{
  "old_password": "Password123!",
  "new_password": "NewPassword123!",
  "confirm_new_password": "NewPassword123!"
}
```

Natija:

```json
{
  "message": "Parol muvaffaqiyatli o'zgartirildi."
}
```

---

## 1.10. Forgot password

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/auth/forgot-password/
```

Body:

```json
{
  "email": "candidate@example.com"
}
```

Natija:

```json
{
  "message": "Parol tiklash kodi yuborildi."
}
```

---

## 1.11. Reset password

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/auth/reset-password/
```

Body:

```json
{
  "email": "candidate@example.com",
  "code": "123456",
  "new_password": "ResetPassword123!",
  "confirm_new_password": "ResetPassword123!"
}
```

Natija:

```json
{
  "message": "Parol muvaffaqiyatli tiklandi."
}
```

---

## 1.12. Logout

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/auth/logout/
```

Body:

```json
{
  "refresh_token": "refresh_token_value"
}
```

Natija:

```json
{
  "message": "Chiqib ketildi."
}
```

---

## 1.13. Logout all devices

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/auth/logout-all/
```

Headers:

```text
Authorization: Bearer access_token_value
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "message": "Barcha qurilmalar chiqib ketildi. Revoked tokens: 1"
}
```

---

# 2. Public vacancies API

Bu API lar ochiq vakansiyalar uchun. Ro'yxat va detail uchun token kerak emas.

Enum qiymatlar:

```text
employment_type: full_time, part_time, contract, internship
work_mode: office, remote, hybrid
```

## 2.1. Ochiq vakansiyalar ro'yxati

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/vacancies/
```

Body:

```text
Body kerak emas
```

Natija:

```json
[
  {
    "id": 1,
    "title": "Python Backend Developer",
    "company_name": "Jobify",
    "location": "Toshkent",
    "employment_type": "full_time",
    "work_mode": "office",
    "salary_from": 5000000,
    "salary_to": 10000000,
    "salary_currency": "UZS",
    "salary_negotiable": true,
    "expires_at": "2026-12-31",
    "created_at": "2026-05-11T10:00:00"
  }
]
```

Filter bilan:

```text
http://127.0.0.1:8000/api/vacancies/?q=python&location=Toshkent&employment_type=full_time&work_mode=office&salary_from=3000000&salary_to=12000000&salary_currency=UZS&salary_negotiable=true
```

---

## 2.2. Bitta vakansiyani ko'rish

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/vacancies/1/
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "id": 1,
  "title": "Python Backend Developer",
  "description": "FastAPI backend yozish",
  "company_name": "Jobify",
  "location": "Toshkent",
  "employment_type": "full_time",
  "work_mode": "office",
  "salary_from": 5000000,
  "salary_to": 10000000,
  "salary_currency": "UZS",
  "salary_negotiable": true,
  "responsibilities": "API yozish",
  "requirements": "Python, FastAPI, PostgreSQL",
  "benefits": "Bonuslar",
  "experience_note": "1-3 yil",
  "education_note": "Muhim emas",
  "contact_phone": "+998901234567",
  "expires_at": "2026-12-31",
  "created_at": "2026-05-11T10:00:00"
}
```

---

## 2.3. Vakansiyaga murojaat yuborish

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/vacancies/1/apply/
```

Headers:

```text
Authorization: Bearer candidate_access_token
Content-Type: application/json
```

Body:

```json
{
  "message": "Assalomu alaykum, men shu vakansiyaga qiziqyapman."
}
```

Natija:

```json
{
  "application_id": 1,
  "vacancy_id": 1,
  "status": "pending",
  "message": "Murojaat qabul qilindi. HR javobini kuting."
}
```

Eslatma:

```text
Bitta candidate bitta vakansiyaga faqat bir marta murojaat yubora oladi.
```

---

# 3. Candidate API

Bu API lar uchun candidate token kerak.

## 3.1. Candidate murojaatlari ro'yxati

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/candidate/applications/
```

Headers:

```text
Authorization: Bearer candidate_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
[
  {
    "id": 1,
    "vacancy_id": 1,
    "vacancy_title": "Python Backend Developer",
    "candidate_id": 1,
    "candidate_email": "candidate@example.com",
    "status": "pending",
    "initial_message": "Assalomu alaykum, men shu vakansiyaga qiziqyapman.",
    "created_at": "2026-05-11T10:00:00",
    "resume_download_url": null,
    "chat_messages": []
  }
]
```

Filter bilan:

```text
http://127.0.0.1:8000/api/candidate/applications/?status=pending&vacancy_id=1&q=python
```

---

## 3.2. Candidate bitta murojaat detail

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/candidate/applications/1/
```

Headers:

```text
Authorization: Bearer candidate_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "id": 1,
  "vacancy_id": 1,
  "vacancy_title": "Python Backend Developer",
  "candidate_id": 1,
  "candidate_email": "candidate@example.com",
  "status": "chat_open",
  "initial_message": "Assalomu alaykum, men shu vakansiyaga qiziqyapman.",
  "created_at": "2026-05-11T10:00:00",
  "resume_download_url": null,
  "chat_messages": []
}
```

---

## 3.3. Candidate HR bilan chatga xabar yozishi

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/candidate/applications/1/messages/
```

Headers:

```text
Authorization: Bearer candidate_access_token
Content-Type: application/json
```

Body:

```json
{
  "message": "Suhbat uchun rahmat, qo'shimcha ma'lumot yuboraman."
}
```

Natija:

```json
{
  "message": "Xabar yuborildi."
}
```

Eslatma:

```text
Bu faqat HR murojaatni accept qilgandan keyin, ya'ni status chat_open bo'lsa ishlaydi.
```

---

## 3.4. Candidate rezume ma'lumotini ko'rish

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/candidate/resume/
```

Headers:

```text
Authorization: Bearer candidate_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "id": 1,
  "candidate_id": 1,
  "original_filename": "resume.pdf",
  "content_type": "application/pdf",
  "size_bytes": 12345,
  "created_at": "2026-05-11T10:00:00",
  "updated_at": "2026-05-11T10:00:00",
  "download_url": "http://127.0.0.1:8001/api/candidate/resume/download/"
}
```

Eslatma:

```text
Agar rezume yo'q bo'lsa Natija null bo'ladi.
```

---

## 3.5. Candidate rezume yuklash

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/candidate/resume/
```

Headers:

```text
Authorization: Bearer candidate_access_token
```

Body:

```text
form-data:
key  → file
type → File
value → resume.pdf
```

Natija:

```json
{
  "id": 1,
  "candidate_id": 1,
  "original_filename": "resume.pdf",
  "content_type": "application/pdf",
  "size_bytes": 12345,
  "created_at": "2026-05-11T10:00:00",
  "updated_at": "2026-05-11T10:00:00",
  "download_url": "http://127.0.0.1:8001/api/candidate/resume/download/"
}
```

---

## 3.6. Candidate rezume yangilash

Postman:

Method → PUT

URL:

```text
http://127.0.0.1:8000/api/candidate/resume/
```

Headers:

```text
Authorization: Bearer candidate_access_token
```

Body:

```text
form-data:
key  → file
type → File
value → new_resume.pdf
```

Natija:

```json
{
  "id": 1,
  "candidate_id": 1,
  "original_filename": "new_resume.pdf",
  "content_type": "application/pdf",
  "size_bytes": 15000,
  "created_at": "2026-05-11T10:00:00",
  "updated_at": "2026-05-11T11:00:00",
  "download_url": "http://127.0.0.1:8001/api/candidate/resume/download/"
}
```

---

## 3.7. Candidate rezume download

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/candidate/resume/download/
```

Headers:

```text
Authorization: Bearer candidate_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```text
Fayl download bo'ladi.
```

---

## 3.8. Candidate rezume o'chirish

Postman:

Method → DELETE

URL:

```text
http://127.0.0.1:8000/api/candidate/resume/
```

Headers:

```text
Authorization: Bearer candidate_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```text
204 No Content
```

---

# 4. HR API

Bu API lar uchun HR token kerak. Vakansiya joylash va applications bilan ishlash uchun HR admin tomonidan approve qilingan bo'lishi kerak.

## 4.1. HR status

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/hr/status/
```

Headers:

```text
Authorization: Bearer hr_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "hr_approved": true,
  "can_post_vacancies": true
}
```

---

## 4.2. HR vakansiya yaratish

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/hr/vacancies/
```

Headers:

```text
Authorization: Bearer hr_access_token
Content-Type: application/json
```

Body:

```json
{
  "title": "Python Backend Developer",
  "description": "FastAPI backend yozish",
  "company_name": "Jobify",
  "location": "Toshkent",
  "employment_type": "full_time",
  "work_mode": "office",
  "responsibilities": "API yozish va PostgreSQL bilan ishlash",
  "requirements": "Python, FastAPI, PostgreSQL",
  "benefits": "Bonuslar va qulay ofis",
  "salary_from": 5000000,
  "salary_to": 10000000,
  "salary_currency": "UZS",
  "salary_negotiable": true,
  "experience_note": "1-3 yil",
  "education_note": "Muhim emas",
  "contact_phone": "+998901234567",
  "expires_at": "2026-12-31"
}
```

Natija:

```json
{
  "id": 1,
  "hr_id": 2,
  "title": "Python Backend Developer",
  "description": "FastAPI backend yozish",
  "company_name": "Jobify",
  "location": "Toshkent",
  "employment_type": "full_time",
  "work_mode": "office",
  "salary_from": 5000000,
  "salary_to": 10000000,
  "salary_currency": "UZS",
  "salary_negotiable": true,
  "responsibilities": "API yozish va PostgreSQL bilan ishlash",
  "requirements": "Python, FastAPI, PostgreSQL",
  "benefits": "Bonuslar va qulay ofis",
  "experience_note": "1-3 yil",
  "education_note": "Muhim emas",
  "contact_phone": "+998901234567",
  "expires_at": "2026-12-31",
  "created_at": "2026-05-11T10:00:00",
  "updated_at": "2026-05-11T10:00:00"
}
```

---

## 4.3. HR o'z vakansiyalarini ko'rish

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/hr/vacancies/
```

Headers:

```text
Authorization: Bearer hr_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
[
  {
    "id": 1,
    "hr_id": 2,
    "title": "Python Backend Developer",
    "description": "FastAPI backend yozish",
    "company_name": "Jobify",
    "location": "Toshkent",
    "employment_type": "full_time",
    "work_mode": "office",
    "salary_from": 5000000,
    "salary_to": 10000000,
    "salary_currency": "UZS",
    "salary_negotiable": true,
    "responsibilities": "API yozish va PostgreSQL bilan ishlash",
    "requirements": "Python, FastAPI, PostgreSQL",
    "benefits": "Bonuslar va qulay ofis",
    "experience_note": "1-3 yil",
    "education_note": "Muhim emas",
    "contact_phone": "+998901234567",
    "expires_at": "2026-12-31",
    "created_at": "2026-05-11T10:00:00",
    "updated_at": "2026-05-11T10:00:00"
  }
]
```

---

## 4.4. HR bitta vakansiyasini ko'rish

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/hr/vacancies/1/
```

Headers:

```text
Authorization: Bearer hr_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "id": 1,
  "hr_id": 2,
  "title": "Python Backend Developer",
  "description": "FastAPI backend yozish",
  "company_name": "Jobify",
  "location": "Toshkent",
  "employment_type": "full_time",
  "work_mode": "office",
  "salary_from": 5000000,
  "salary_to": 10000000,
  "salary_currency": "UZS",
  "salary_negotiable": true,
  "responsibilities": "API yozish va PostgreSQL bilan ishlash",
  "requirements": "Python, FastAPI, PostgreSQL",
  "benefits": "Bonuslar va qulay ofis",
  "experience_note": "1-3 yil",
  "education_note": "Muhim emas",
  "contact_phone": "+998901234567",
  "expires_at": "2026-12-31",
  "created_at": "2026-05-11T10:00:00",
  "updated_at": "2026-05-11T10:00:00"
}
```

---

## 4.5. HR vakansiyani o'chirish

Postman:

Method → DELETE

URL:

```text
http://127.0.0.1:8000/api/hr/vacancies/1/
```

Headers:

```text
Authorization: Bearer hr_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "message": "Vakansiya o'chirildi (yashirin)."
}
```

---

## 4.6. HR applications ro'yxati

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/hr/applications/
```

Headers:

```text
Authorization: Bearer hr_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
[
  {
    "id": 1,
    "vacancy_id": 1,
    "vacancy_title": "Python Backend Developer",
    "candidate_id": 1,
    "candidate_email": "candidate@example.com",
    "status": "pending",
    "initial_message": "Assalomu alaykum, men shu vakansiyaga qiziqyapman.",
    "created_at": "2026-05-11T10:00:00",
    "resume_download_url": "http://127.0.0.1:8000/api/hr/applications/1/resume/"
  }
]
```

Filter bilan:

```text
http://127.0.0.1:8000/api/hr/applications/?status=pending&vacancy_id=1&q=python
```

---

## 4.7. HR application detail

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/hr/applications/1/
```

Headers:

```text
Authorization: Bearer hr_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "id": 1,
  "vacancy_id": 1,
  "vacancy_title": "Python Backend Developer",
  "candidate_id": 1,
  "candidate_email": "candidate@example.com",
  "status": "pending",
  "initial_message": "Assalomu alaykum, men shu vakansiyaga qiziqyapman.",
  "created_at": "2026-05-11T10:00:00",
  "resume_download_url": "http://127.0.0.1:8000/api/hr/applications/1/resume/",
  "chat_messages": []
}
```

---

## 4.8. HR candidate rezumesini download qilish

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/hr/applications/1/resume/
```

Headers:

```text
Authorization: Bearer hr_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```text
Fayl download bo'ladi.
```

---

## 4.9. HR application accept qilish

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/hr/applications/1/accept/
```

Headers:

```text
Authorization: Bearer hr_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "application_id": 1,
  "status": "chat_open",
  "message": "Nomzod bilan qo'shimcha yozishish ochildi."
}
```

---

## 4.10. HR application reject qilish

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/hr/applications/1/reject/
```

Headers:

```text
Authorization: Bearer hr_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "application_id": 1,
  "status": "rejected",
  "message": "Murojaat rad etildi."
}
```

---

## 4.11. HR chatga xabar yozishi

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/hr/applications/1/messages/
```

Headers:

```text
Authorization: Bearer hr_access_token
Content-Type: application/json
```

Body:

```json
{
  "message": "Assalomu alaykum, suhbatni boshladik."
}
```

Natija:

```json
{
  "message": "Xabar yuborildi."
}
```

---

# 5. Support API

Bu API lar HR yoki candidate token bilan ishlaydi. Admin uchun alohida support endpointlar 6-bo'limda.

## 5.1. Support thread ochish

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/support/threads/
```

Headers:

```text
Authorization: Bearer candidate_or_hr_access_token
Content-Type: application/json
```

Body:

```json
{
  "subject": "Yordam kerak",
  "message": "Admin bilan bog'lanmoqchiman."
}
```

Natija:

```json
{
  "id": 1,
  "subject": "Yordam kerak",
  "status": "open",
  "created_at": "2026-05-11T10:00:00",
  "updated_at": "2026-05-11T10:00:00"
}
```

---

## 5.2. O'zim ochgan support threadlar

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/support/threads/
```

Headers:

```text
Authorization: Bearer candidate_or_hr_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
[
  {
    "id": 1,
    "subject": "Yordam kerak",
    "status": "open",
    "created_at": "2026-05-11T10:00:00",
    "updated_at": "2026-05-11T10:00:00"
  }
]
```

---

## 5.3. Support thread detail

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/support/threads/1/
```

Headers:

```text
Authorization: Bearer candidate_or_hr_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "id": 1,
  "subject": "Yordam kerak",
  "status": "open",
  "created_by_id": 1,
  "creator_role": "candidate",
  "creator_email": "candidate@example.com",
  "created_at": "2026-05-11T10:00:00",
  "updated_at": "2026-05-11T10:00:00",
  "messages": [
    {
      "id": 1,
      "sender_id": 1,
      "body": "Admin bilan bog'lanmoqchiman.",
      "created_at": "2026-05-11T10:00:00"
    }
  ]
}
```

---

## 5.4. Support threadga xabar yozish

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/support/threads/1/messages/
```

Headers:

```text
Authorization: Bearer candidate_or_hr_access_token
Content-Type: application/json
```

Body:

```json
{
  "message": "Qo'shimcha savolim bor."
}
```

Natija:

```json
{
  "message": "Xabar yuborildi."
}
```

---

# 6. Admin API

Bu API lar uchun admin token kerak.

Eslatma:

```text
Oddiy /api/auth/register/ orqali admin yaratib bo'lmaydi.
Admin user bazada oldindan bor bo'lishi kerak.
```

## 6.1. Tasdiqlanishi kerak bo'lgan HR lar

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/admin/pending-hr/
```

Headers:

```text
Authorization: Bearer admin_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
[
  {
    "id": 2,
    "email": "hr@example.com",
    "is_verified": true,
    "created_at": "2026-05-11T10:00:00"
  }
]
```

---

## 6.2. HR ni approve qilish

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/admin/hr/2/approve/
```

Headers:

```text
Authorization: Bearer admin_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "id": 2,
  "email": "hr@example.com",
  "role": "hr",
  "is_active": true,
  "is_verified": true,
  "hr_approved": true,
  "created_at": "2026-05-11T10:00:00"
}
```

---

## 6.3. Admin barcha support threadlarni ko'rishi

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/admin/support/threads/
```

Headers:

```text
Authorization: Bearer admin_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
[
  {
    "id": 1,
    "subject": "Yordam kerak",
    "status": "open",
    "created_by_id": 1,
    "creator_role": "candidate",
    "creator_email": "candidate@example.com",
    "created_at": "2026-05-11T10:00:00",
    "updated_at": "2026-05-11T10:00:00"
  }
]
```

Filter bilan:

```text
http://127.0.0.1:8000/api/admin/support/threads/?status=open
```

---

## 6.4. Admin support thread detail

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/admin/support/threads/1/
```

Headers:

```text
Authorization: Bearer admin_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "id": 1,
  "subject": "Yordam kerak",
  "status": "open",
  "created_by_id": 1,
  "creator_role": "candidate",
  "creator_email": "candidate@example.com",
  "created_at": "2026-05-11T10:00:00",
  "updated_at": "2026-05-11T10:00:00",
  "messages": [
    {
      "id": 1,
      "sender_id": 1,
      "body": "Admin bilan bog'lanmoqchiman.",
      "created_at": "2026-05-11T10:00:00"
    }
  ]
}
```

---

## 6.5. Admin support threadga javob yozishi

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/admin/support/threads/1/messages/
```

Headers:

```text
Authorization: Bearer admin_access_token
Content-Type: application/json
```

Body:

```json
{
  "message": "Murojaatingiz qabul qilindi."
}
```

Natija:

```json
{
  "message": "Javob yuborildi."
}
```

---

## 6.6. Admin support threadni yopishi

Postman:

Method → POST

URL:

```text
http://127.0.0.1:8000/api/admin/support/threads/1/close/
```

Headers:

```text
Authorization: Bearer admin_access_token
```

Body:

```text
Body kerak emas
```

Natija:

```json
{
  "id": 1,
  "subject": "Yordam kerak",
  "status": "closed",
  "created_by_id": 1,
  "creator_role": "candidate",
  "creator_email": "candidate@example.com",
  "created_at": "2026-05-11T10:00:00",
  "updated_at": "2026-05-11T11:00:00"
}
```

---

# 7. Test qilish tartibi

Eng qulay tartib:

```text
1. Candidate register
2. Candidate verify email
3. Candidate login → candidate_access_token olasiz
4. HR register
5. HR verify email
6. HR login → hr_access_token olasiz
7. Admin login → admin_access_token olasiz
8. Admin pending HR list ko'radi
9. Admin HR ni approve qiladi
10. HR vakansiya yaratadi
11. Candidate public vacancies ro'yxatidan vakansiyani ko'radi
12. Candidate vakansiyaga apply qiladi
13. HR applications ro'yxatidan murojaatni ko'radi
14. HR accept qiladi
15. HR va candidate chat messages yuboradi
16. Candidate yoki HR support thread ochadi
17. Admin support threadga javob beradi yoki close qiladi
```
