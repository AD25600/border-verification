import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if token is None:
        raise UnauthorizedError("Authentication token missing.")

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise UnauthorizedError("Invalid or expired token.")

    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise UnauthorizedError("Invalid token subject.")

    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive.")

    return user


def require_role(*allowed_roles: str):
    """
    Reusable FastAPI dependency factory for role-based access control.
    Usage: dependencies=[Depends(require_role("ADMIN"))]
    """

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise ForbiddenError(
                f"This action requires one of the following roles: {', '.join(allowed_roles)}."
            )
        return current_user

    return _dependency
