import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CheckpointBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=20)
    location: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = True


class CheckpointCreate(CheckpointBase):
    pass


class CheckpointRead(CheckpointBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
