# Authentication API

This document details the authentication endpoints available in `backend/app/routes/auth_routes.py`.

## Endpoints

### 1. Login
**POST** `/api/auth/login`

Authenticates a user and returns a JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "role": "admin",
  "tenant_status": "activo"
}
```

**Errors:**
- `401 Unauthorized`: Invalid credentials.
- `429 Too Many Requests`: Too many failed attempts (brute-force protection).

---

### 2. Register
**POST** `/api/auth/register`

Registers a new tenant and admin user.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "strongpassword",
  "full_name": "John Doe",
  "website": "" // Honeypot field (leave empty)
}
```

**Response (201 Created):**
```json
{
  "ok": true
}
```

**Errors:**
- `400 Bad Request`: Missing fields, invalid email, weak password.
- `409 Conflict`: Email already exists.
- `429 Too Many Requests`: Registration rate limit exceeded.

---

### 3. Verify Token
**GET** `/api/auth/me`

Verifies if the current token is valid.

**Headers:**
`Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "ok": true,
  "sub": 123,
  "tenant_id": 456,
  "role": "admin"
}
```

## Security Mechanisms

- **Rate Limiting:** Login is limited to 10 requests/minute.
- **Brute Force Protection:** IP+Email pairs are locked out for 5 minutes after 5 failed attempts.
- **Honeypot:** The `website` field in registration must be empty.
