# Postman orqali test qilish

API ni ishga tushirish:

```bash
docker compose up --build
```

Asosiy manzil:

```text
http://127.0.0.1:8000
```

Verification code va reset code emailga yuboriladi. Agar SMTP sozlanmagan bo'lsa, kod `celery-worker` logida chiqadi.

Masalan:

```text
[EMAIL-DEV][CELERY] To=candidate@example.com | Subject=... | Body=Sizning tasdiqlash kodingiz: 123456
```

Shu `123456` kodni Postman body ichida ishlatasiz.

---

## 1. API ishlayotganini tekshirish

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

## 2. Register qilish

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
  "user": {
    "id": "user_id",
    "email": "candidate@example.com",
    "role": "candidate",
    "is_active": true,
    "is_verified": false,
    "created_at": "2026-05-08T10:00:00"
  },
  "message": "Email verification code sent."
}
```

Eslatma:

```text
role faqat candidate yoki hr bo'ladi.
admin bilan register qilib bo'lmaydi.
```

---

## 3. Email tasdiqlash

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
  "message": "Email verified successfully."
}
```

Eslatma:

```text
123456 o'rniga celery-worker logida chiqqan verification code yoziladi.
```

---

## 4. Verification code qayta yuborish

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
  "message": "Verification code sent."
}
```

Eslatma:

```text
Bu faqat user hali verify bo'lmagan bo'lsa ishlaydi.
```

---

## 5. Login qilish

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
    "id": "user_id",
    "email": "candidate@example.com",
    "role": "candidate",
    "is_active": true,
    "is_verified": true,
    "created_at": "2026-05-08T10:00:00"
  }
}
```

Eslatma:

```text
access_token ni keyingi requestlarda Authorization header ichida ishlatasiz.
refresh_token ni refresh va logout uchun ishlatasiz.
```

---

## 6. Profilni ko'rish

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
  "id": "user_id",
  "email": "candidate@example.com",
  "role": "candidate",
  "is_active": true,
  "is_verified": true,
  "created_at": "2026-05-08T10:00:00"
}
```

---

## 7. Candidate endpoint

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/auth/candidate-only/
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
  "message": "Welcome Candidate. You can access this endpoint."
}
```

---

## 8. HR endpoint

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/auth/hr-only/
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
  "message": "Welcome HR. You can access this endpoint."
}
```

Eslatma:

```text
Bu endpoint ishlashi uchun user role hr bo'lishi kerak.
```

---

## 9. Admin endpoint

Postman:

Method → GET

URL:

```text
http://127.0.0.1:8000/api/auth/admin-only/
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
  "message": "Welcome Admin. You can access this endpoint."
}
```

Eslatma:

```text
Oddiy register orqali admin yaratib bo'lmaydi.
Role admin bo'lmasa 403 Permission denied qaytadi.
```

---

## 10. Access token yangilash

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
Yangi refresh_token ni saqlab qo'yish kerak.
```

---

## 11. Parolni o'zgartirish

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
  "message": "Password changed successfully."
}
```

---

## 12. Parolni tiklash kodi yuborish

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
  "message": "If this email exists, reset code has been sent."
}
```

Eslatma:

```text
Reset code celery-worker logida chiqadi.
```

---

## 13. Parolni reset qilish

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
  "message": "Password reset successfully."
}
```

Eslatma:

```text
123456 o'rniga celery-worker logida chiqqan reset code yoziladi.
```

---

## 14. Logout qilish

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
  "message": "Logged out successfully."
}
```

---

## 15. Hamma qurilmalardan logout qilish

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
  "message": "All devices logged out. Revoked tokens: 1"
}
```
