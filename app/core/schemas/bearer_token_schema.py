from pydantic import BaseModel


class BearerTokenSchema(BaseModel):
    access_token: str
    token_type: str
