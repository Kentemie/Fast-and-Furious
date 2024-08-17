from pydantic import BaseModel


class Redis(BaseModel):
    HOST: str
    PORT: int
    TOKEN_BLACKLIST_DB: list[int] = [0]
    SECURITY_DB: list[int] = [1]
    CACHE_DB: list[int] = [2]
