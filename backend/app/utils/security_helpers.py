"""
Security Helper Functions for Authentication.

Includes:
- IP address extraction
- Lockout mechanisms (Login & Registration)
"""

import time
import logging
from flask import request

# Protección básica anti abuso independiente del login
FAILED_REGISTRATIONS: dict[tuple[str, str], dict] = {}
# Protección básica anti fuerza bruta (en memoria).
FAILED_LOGINS: dict[tuple[str, str], dict] = {}

# Default values if config not loaded properly (safe fallbacks)
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes

def configure_security(max_attempts: int, lockout_sec: int):
    """Update security parameters from config"""
    global MAX_FAILED_ATTEMPTS, LOCKOUT_SECONDS
    MAX_FAILED_ATTEMPTS = max_attempts
    LOCKOUT_SECONDS = lockout_sec

def get_client_ip() -> str:
    """Extract client IP from headers or remote_addr"""
    hdr = request.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
    return hdr or request.remote_addr or "unknown"

# --- Login Lockout Helpers ---

def is_login_locked(key: tuple[str, str]) -> bool:
    """Check if login is locked for a given (IP, Email) key"""
    entry = FAILED_LOGINS.get(key)
    if not entry:
        return False
    until = entry.get("blocked_until", 0)
    return until and until > int(time.time())

def register_login_failure(key: tuple[str, str]) -> int:
    """Register a failed login attempt. Returns current failure count."""
    now = int(time.time())
    entry = FAILED_LOGINS.get(key) or {"count": 0, "blocked_until": 0}
    last = entry.get("last_failed", 0)

    # Reset count if lockout period passed since last failure
    if last and now - last > LOCKOUT_SECONDS:
        entry["count"] = 0

    entry["count"] += 1
    entry["last_failed"] = now

    if entry["count"] >= MAX_FAILED_ATTEMPTS:
        entry["blocked_until"] = now + LOCKOUT_SECONDS

    FAILED_LOGINS[key] = entry
    return entry["count"]

def reset_login_lock(key: tuple[str, str]) -> None:
    """Reset lock for a key (successful login)"""
    FAILED_LOGINS.pop(key, None)

# --- Registration Lockout Helpers ---

def is_registration_locked(key: tuple[str, str]) -> bool:
    """Check if registration is locked for a given (IP, Email) key"""
    entry = FAILED_REGISTRATIONS.get(key)
    if not entry:
        return False
    until = entry.get("blocked_until", 0)
    return until and until > int(time.time())

def register_registration_failure(key: tuple[str, str]) -> int:
    """Register a failed registration attempt. Returns current failure count."""
    now = int(time.time())
    entry = FAILED_REGISTRATIONS.get(key) or {"count": 0, "blocked_until": 0}
    last = entry.get("last_failed", 0)

    if last and now - last > LOCKOUT_SECONDS:
        entry["count"] = 0

    entry["count"] += 1
    entry["last_failed"] = now

    if entry["count"] >= MAX_FAILED_ATTEMPTS:
        entry["blocked_until"] = now + LOCKOUT_SECONDS

    FAILED_REGISTRATIONS[key] = entry
    return entry["count"]

def reset_registration_lock(key: tuple[str, str]) -> None:
    """Reset registration lock for a key"""
    FAILED_REGISTRATIONS.pop(key, None)
