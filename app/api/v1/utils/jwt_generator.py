import jwt

from datetime import datetime, timedelta, timezone
from typing import Any


def generate_jwt(
    data: dict[str, Any],
    private_key: str,
    audience: str,
    lifetime_seconds: int,
    algorithm: str,
) -> str:
    payload = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(seconds=lifetime_seconds)

    payload["exp"] = expire
    payload["aud"] = audience

    return jwt.encode(payload=payload, key=private_key, algorithm=algorithm)


def decode_jwt(
    encoded_jwt: str, public_key: str, audience: str, algorithms: list[str]
) -> dict[str, Any]:
    return jwt.decode(
        jwt=encoded_jwt, key=public_key, algorithms=algorithms, audience=audience
    )
