from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class CreateUpdateDictSchema(BaseModel):
    def create_update_dict(self):
        return self.model_dump(
            exclude_unset=True,
            exclude={
                "is_superuser",
                "is_active",
                "is_verified",
            },
        )

    def create_update_dict_superuser(self):
        return self.model_dump(exclude_unset=True)


class UserSchema(CreateUpdateDictSchema):
    """User Schema."""

    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserCreateSchema(CreateUpdateDictSchema):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False


class UserUpdateSchema(CreateUpdateDictSchema):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None
