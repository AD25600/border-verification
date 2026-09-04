import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.checkpoint import CheckpointRead


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role_name: str = Field(description="One of ADMIN, SUPERVISOR, OFFICER")
    checkpoint_id: Optional[uuid.UUID] = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    role_name: str
    checkpoint: Optional[CheckpointRead] = None
