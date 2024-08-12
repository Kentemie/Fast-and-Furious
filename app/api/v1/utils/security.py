import secrets


def generate_verification_code() -> int:
    return secrets.randbelow(900_000) + 100_000


def generate_reset_password_token() -> str:
    return secrets.token_urlsafe()
