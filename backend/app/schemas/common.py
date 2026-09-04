from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ServiceResult(BaseModel, Generic[T]):
    status: str  # "success" | "error"
    confidence: Optional[float] = None
    result: Optional[Any] = None
    errors: List[str] = []
