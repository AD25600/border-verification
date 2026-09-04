import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.schemas.user import UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead], dependencies=[Depends(require_role(RoleName.ADMIN, RoleName.SUPERVISOR))])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return UserService(db).list_users()


@router.get("/{user_id}", response_model=UserRead, dependencies=[Depends(require_role(RoleName.ADMIN, RoleName.SUPERVISOR))])
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> User:
    return UserService(db).get_user(user_id)
