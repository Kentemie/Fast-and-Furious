from pathlib import Path

from pydantic import BaseModel


BASE_DIR = Path(__file__).parent.parent.parent


class JsonWebToken(BaseModel):
    BACKEND_NAME: str = "jwt_bearer"

    PRIVATE_KEY: Path = BASE_DIR / "certs" / "jwt-private.pem"
    PUBLIC_KEY: Path = BASE_DIR / "certs" / "jwt-public.pem"

    ACCESS_TOKEN_LIFETIME_SECONDS: int = 60 * 60
    REFRESH_TOKEN_LIFETIME_SECONDS: int = 60 * 60 * 24 * 14

    TOKEN_AUDIENCE: str = "backend:authentication"
    ALGORITHM: str = "RS256"


class Authentication(BaseModel):
    TOKEN_TYPE: str = "token_type"
    ACCESS_TOKEN: str = "access_token"
    REFRESH_TOKEN: str = "refresh_token"

    JWT: JsonWebToken = JsonWebToken()
