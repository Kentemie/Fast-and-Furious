from pydantic import BaseModel, computed_field


class VersionOne(BaseModel):
    PREFIX: str = "/v1"

    REGISTER_EP: str = "/register"
    VERIFY_EP: str = "/verify"
    RESET_PASSWORD_EP: str = "/reset-password"
    AUTH_EP: str = "/auth"
    USERS_EP: str = "/users"


class Api(BaseModel):
    PREFIX: str = "/api"

    V1: VersionOne = VersionOne()

    @computed_field
    @property
    def BEARER_TOKEN_URL(self) -> str:
        parts = (self.PREFIX, self.V1.PREFIX, self.V1.AUTH_EP, "/login")
        path = "".join(parts)
        return path.removeprefix("/")
