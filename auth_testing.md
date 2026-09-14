# 🔐 OMNIA Auth Testing Playbook

Use this guide to verify JWT auth + Resend email + multi-tenant role checks
after M1.S3 implementation.

---

## 0 — Prerequisites

- Backend running on port 8001 (supervisor)
- MongoDB reachable via MONGO_URL
- .env contains JWT_SECRET (64 hex chars), ADMIN_EMAIL, ADMIN_PASSWORD, RESEND_API_KEY
- Frontend running on port 3000

---

## 1 — MongoDB sanity checks

```bash
mongosh
> use test_database
> db.users.find({}, {email:1, role:1, agency_ids:1, lang:1}).pretty()
> db.users.getIndexes()        # must include unique on `email`
> db.password_reset_tokens.getIndexes()  # must include TTL on expires_at
> db.login_attempts.getIndexes()
```

Expected:
- `db.users` has unique index on `email`
- bcrypt hashes start with `$2b$`
- Admin user exists with role `super_admin` and lang `it`

---

## 2 — Backend API endpoints (curl)

Replace `$URL` with `$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)`.

### 2.1 Register
```bash
curl -c cookies.txt -X POST "$URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -H "Accept-Language: it" \
  -d '{"email":"test@omnia.it","password":"Test1234!","name":"Mario Rossi","role":"agent","lang":"it"}'
```
Expected: 200, user object returned, cookies `access_token` + `refresh_token` set.

### 2.2 Login
```bash
curl -c cookies.txt -X POST "$URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@omniarealestateecosystem.it","password":"<ADMIN_PASSWORD>"}'
cat cookies.txt
```
Expected: cookies file contains 2 entries (access_token, refresh_token).

### 2.3 Get current user
```bash
curl -b cookies.txt "$URL/api/auth/me"
```
Expected: user object with no `password_hash`, includes `lang`, `role`, `agency_ids`.

### 2.4 Refresh
```bash
curl -b cookies.txt -X POST "$URL/api/auth/refresh"
```
Expected: new `access_token` cookie issued.

### 2.5 Logout
```bash
curl -b cookies.txt -X POST "$URL/api/auth/logout"
```
Expected: cookies deleted.

### 2.6 Forgot password
```bash
curl -X POST "$URL/api/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -H "Accept-Language: en" \
  -d '{"email":"test@omnia.it"}'
```
Expected: 200 (always, to avoid email enumeration); Resend sends email
in EN; reset link appears in backend logs in dev mode.

### 2.7 Reset password
```bash
curl -X POST "$URL/api/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{"token":"<TOKEN_FROM_LOG>","new_password":"NewPass4567!"}'
```
Expected: 200, token marked used; login with new password works.

---

## 3 — Brute force protection

Run login with WRONG password 6 times from the same IP:
```bash
for i in {1..6}; do
  curl -X POST "$URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@omniarealestateecosystem.it","password":"WRONG"}'
done
```
After 5 attempts the 6th must return 429 with "Too many attempts" message
localized in IT/EN/ES per Accept-Language header.

---

## 4 — Multi-tenant isolation

1. Create two agencies (A, B).
2. Create user1 in agency A, user2 in agency B.
3. Verify `/api/auth/me` returns ONLY the agency the user belongs to.
4. Verify any tenant-aware endpoint refuses cross-tenant reads.

---

## 5 — i18n in emails

Trigger forgot-password with three different Accept-Language headers
(`it`, `en`, `es`) and verify:
- Email subject in correct language
- Email body in correct language
- Reset link uses URL with same `/{lang}/` prefix

---

## 6 — Frontend smoke test

Open in browser:
- `/it/app` (ImmoWeb) — login form visible in italiano
- Login with admin credentials
- After login redirect to dashboard placeholder
- Refresh page → still logged in (cookies persistent)
- Logout → redirected back to login form
- Switch lang to EN → form labels translate without losing session

---

## 7 — Testing agent invocation

To run automated tests with the testing_agent:

```
features_or_bugs_to_test:
  - POST /api/auth/register creates user + sets cookies
  - POST /api/auth/login returns user + cookies
  - GET /api/auth/me returns user from cookie
  - POST /api/auth/refresh issues new access token
  - POST /api/auth/logout clears cookies
  - POST /api/auth/forgot-password sends email via Resend
  - Brute force lockout after 5 wrong attempts
  - Login form in /it/app shows ITA labels
  - Login form in /es/app shows ESP labels
```

---

*Saved at /app/auth_testing.md — referenced by testing_agent_v3 in M1.S3 final QA.*
