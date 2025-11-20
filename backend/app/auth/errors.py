"""Excepciones personalizadas para manejo de tokens JWT."""


class AuthTokenError(Exception):
    """Base para errores de autenticación mediante token."""


class AuthTokenExpired(AuthTokenError):
    """Token expirado."""


class AuthTokenInvalid(AuthTokenError):
    """Token inválido o mal formado."""
