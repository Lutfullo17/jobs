# Jobify Auth API ni Postman orqali test qilish

Bu qo'llanma `Jobify Auth API` endpointlarini Postman'da qanday chaqirish, qaysi JSON body yozish va tokenlarni qanday saqlashni ko'rsatadi.

## 1. API ni ishga tushirish

1. `.env.example` faylidan `.env` yarating.
2. Docker orqali ishga tushiring:

```bash
docker compose up --build
```

API ishga tushgandan keyin:

- Swagger: `http://localhost:8000/docs`
- Base URL: `http://localhost:8000`
- Auth prefix: `/api/auth`

Email uchun SMTP sozlanmagan bo'lsa, verification/reset kodlar `celery-worker` logida chiqadi:

```text
[EMAIL-DEV][CELERY] To=test@example.com | Subject=... | Body=Sizning tasdiqlash kodingiz: 123456
```

Shu 6 xonali kodni Postman environment ichidagi `verification_code` yoki `reset_code` qiymatiga qo'ying.

## 2. Tayyor Postman fayllar

Repo ichida tayyor import fayllar bor:

- `postman/Jobify_Auth_API.postman_collection.json`
- `postman/Jobify_Auth_API.postman_environment.json`

Postman'da:

1. `Import` tugmasini bosing.
2. Ikkala JSON faylni import qiling.
3. Environment sifatida `Jobify Auth API - Local` ni tanlang.
4. Requestlarni pastdagi tartibda yuboring.

## 3. Environment variable'lar

Postman environment ichida quyidagi variable'lar ishlatiladi:

| Variable | Ma'nosi |
| --- | --- |
| `base_url` | API hosti, default: `http://localhost:8000` |
| `email` | Test user emaili |
| `password` | Test user paroli |
| `new_password` | Change password uchun yangi parol |
| `reset_new_password` | Reset password uchun yangi parol |
| `role` | `candidate` yoki `hr`; `admin` oddiy register orqali yaratilmaydi |
| `verification_code` | Email tasdiqlash kodi |
| `reset_code` | Password reset kodi |
| `access_token` | Login/refresh javobidan avtomatik saqlanadi |
| `refresh_token` | Login/refresh javobidan avtomatik saqlanadi |

## 4. Test qilish tartibi

### 4.1. Health check

**Method:** `GET`

```text
{{base_url}}/
```

Kutilgan javob:

```json
{
  "message": "Jobify Auth API is running"
}
```

### 4.2. Register

**Method:** `POST`

```text
{{base_url}}/api/auth/register/
```

**Headers:**

```text
Content-Type: application/json
```

**Body:**

```json
{
  "email": "{{email}}",
  "password": "{{password}}",
  "confirm_password": "{{password}}",
  "role": "{{role}}"
}
```

Izoh:

- `password` kamida 8 ta belgidan iborat bo'lishi kerak.
- `role` qiymati `candidate` yoki `hr` bo'lishi mumkin.
- `admin` role bilan register qilish taqiqlangan.
- Javobdan keyin verification code emailga yoki Celery logiga chiqadi.

**Tests tab script:**

```javascript
pm.test("Register status is 201", function () {
  pm.response.to.have.status(201);
});

pm.test("Register response has user and message", function () {
  const json = pm.response.json();
  pm.expect(json).to.have.property("user");
  pm.expect(json.user.email).to.eql(pm.environment.get("email"));
  pm.expect(json.user.is_verified).to.eql(false);
});
```

### 4.3. Verify email

Avval Celery logidan 6 xonali kodni olib, Postman environment'dagi `verification_code` variable'ga yozing.

**Method:** `POST`

```text
{{base_url}}/api/auth/verify-email/
```

**Body:**

```json
{
  "email": "{{email}}",
  "code": "{{verification_code}}"
}
```

**Tests tab script:**

```javascript
pm.test("Email verified", function () {
  pm.response.to.have.status(200);
  pm.expect(pm.response.json().message).to.eql("Email verified successfully.");
});
```

### 4.4. Resend verification code

Bu endpoint faqat hali verify bo'lmagan user uchun kerak.

**Method:** `POST`

```text
{{base_url}}/api/auth/resend-verification-code/
```

**Body:**

```json
{
  "email": "{{email}}"
}
```

Izoh:

- 1 daqiqada ko'p yuborilsa `429 Too Many Requests` qaytadi.
- User allaqachon verify bo'lgan bo'lsa `400 User already verified` qaytadi.

### 4.5. Login

**Method:** `POST`

```text
{{base_url}}/api/auth/login/
```

**Body:**

```json
{
  "email": "{{email}}",
  "password": "{{password}}"
}
```

Javobda `access_token` va `refresh_token` keladi. Ularni keyingi requestlar uchun environment'ga avtomatik saqlash kerak.

**Tests tab script:**

```javascript
pm.test("Login status is 200", function () {
  pm.response.to.have.status(200);
});

pm.test("Save access and refresh tokens", function () {
  const json = pm.response.json();
  pm.expect(json).to.have.property("access_token");
  pm.expect(json).to.have.property("refresh_token");
  pm.environment.set("access_token", json.access_token);
  pm.environment.set("refresh_token", json.refresh_token);
});
```

### 4.6. Auth talab qiladigan requestlar

`/me`, `/logout-all`, `/change-password`, role-based endpointlar uchun header kerak:

```text
Authorization: Bearer {{access_token}}
```

Postman'da buni requestning `Authorization` tabida ham berish mumkin:

- Type: `Bearer Token`
- Token: `{{access_token}}`

### 4.7. Get current user

**Method:** `GET`

```text
{{base_url}}/api/auth/me/
```

**Authorization:** `Bearer {{access_token}}`

**Tests tab script:**

```javascript
pm.test("Current user returned", function () {
  pm.response.to.have.status(200);
  const json = pm.response.json();
  pm.expect(json.email).to.eql(pm.environment.get("email"));
});
```

### 4.8. Role-based endpointlar

Candidate user uchun:

**Method:** `GET`

```text
{{base_url}}/api/auth/candidate-only/
```

**Authorization:** `Bearer {{access_token}}`

Kutilgan javob:

```json
{
  "message": "Welcome Candidate. You can access this endpoint."
}
```

HR user uchun:

```text
GET {{base_url}}/api/auth/hr-only/
```

Admin uchun:

```text
GET {{base_url}}/api/auth/admin-only/
```

Izoh:

- Oddiy `/register/` orqali `admin` yaratib bo'lmaydi.
- Role mos kelmasa `403 Permission denied` qaytadi.

### 4.9. Refresh token

**Method:** `POST`

```text
{{base_url}}/api/auth/refresh/
```

**Body:**

```json
{
  "refresh_token": "{{refresh_token}}"
}
```

Bu endpoint refresh token rotation qiladi: eski refresh token bekor bo'ladi va yangisi beriladi.

**Tests tab script:**

```javascript
pm.test("Refresh status is 200", function () {
  pm.response.to.have.status(200);
});

pm.test("Save rotated tokens", function () {
  const json = pm.response.json();
  pm.environment.set("access_token", json.access_token);
  pm.environment.set("refresh_token", json.refresh_token);
});
```

### 4.10. Change password

**Method:** `POST`

```text
{{base_url}}/api/auth/change-password/
```

**Authorization:** `Bearer {{access_token}}`

**Body:**

```json
{
  "old_password": "{{password}}",
  "new_password": "{{new_password}}",
  "confirm_new_password": "{{new_password}}"
}
```

Izoh:

- Yangi parol kamida 8 ta belgidan iborat bo'lishi kerak.
- Yangi parol eski parol bilan bir xil bo'lmasligi kerak.
- Password o'zgargandan keyin eski refresh tokenlar revoke qilinadi.

**Tests tab script:**

```javascript
pm.test("Password changed", function () {
  pm.response.to.have.status(200);
  pm.expect(pm.response.json().message).to.eql("Password changed successfully.");
});

if (pm.response.code === 200) {
  pm.environment.set("password", pm.environment.get("new_password"));
}
```

### 4.11. Forgot password

**Method:** `POST`

```text
{{base_url}}/api/auth/forgot-password/
```

**Body:**

```json
{
  "email": "{{email}}"
}
```

Javob:

```json
{
  "message": "If this email exists, reset code has been sent."
}
```

Reset code Celery logida chiqadi. Uni environment'dagi `reset_code` variable'ga yozing.

### 4.12. Reset password

**Method:** `POST`

```text
{{base_url}}/api/auth/reset-password/
```

**Body:**

```json
{
  "email": "{{email}}",
  "code": "{{reset_code}}",
  "new_password": "{{reset_new_password}}",
  "confirm_new_password": "{{reset_new_password}}"
}
```

**Tests tab script:**

```javascript
pm.test("Password reset", function () {
  pm.response.to.have.status(200);
  pm.expect(pm.response.json().message).to.eql("Password reset successfully.");
});

if (pm.response.code === 200) {
  pm.environment.set("password", pm.environment.get("reset_new_password"));
}
```

### 4.13. Logout

**Method:** `POST`

```text
{{base_url}}/api/auth/logout/
```

**Body:**

```json
{
  "refresh_token": "{{refresh_token}}"
}
```

Javob:

```json
{
  "message": "Logged out successfully."
}
```

### 4.14. Logout all devices

**Method:** `POST`

```text
{{base_url}}/api/auth/logout-all/
```

**Authorization:** `Bearer {{access_token}}`

Javob namunasi:

```json
{
  "message": "All devices logged out. Revoked tokens: 1"
}
```

## 5. Tez uchraydigan xatolar

| Status | Sabab |
| --- | --- |
| `400 Invalid verification code` | `verification_code` noto'g'ri yoki eski |
| `400 User already verified` | Verify bo'lgan userga resend qilinyapti |
| `401 Invalid credentials` | Email/parol noto'g'ri |
| `401 Invalid access token` | `access_token` noto'g'ri yoki muddati o'tgan |
| `401 Refresh token expired or revoked` | Eski refresh token ishlatildi |
| `403 Email is not verified` | Login qilishdan oldin email verify qilinmagan |
| `403 Permission denied` | Role endpoint user role'iga mos emas |
| `409 Email already exists` | Shu email bilan user bor |
| `422` | JSON body maydonlari noto'g'ri yoki parol uzunligi yetarli emas |
| `429 Too Many Requests` | Rate limitga tushib qoldingiz |

## 6. Tavsiya etilgan collection run ketma-ketligi

1. `Health Check`
2. `Register`
3. Celery logidan verification code oling va `verification_code` ga yozing.
4. `Verify Email`
5. `Login`
6. `Get Current User`
7. `Candidate Only` yoki `HR Only`
8. `Refresh Token`
9. `Change Password`
10. `Forgot Password`
11. Celery logidan reset code oling va `reset_code` ga yozing.
12. `Reset Password`
13. `Login` - yangi parol bilan tekshirish uchun
14. `Logout`

