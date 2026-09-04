from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)

    def register(self, payload: UserCreate) -> User:
        if self.users.get_by_email(payload.email):
            raise ConflictError("A user with this email already exists.")

        role = self.roles.get_by_name(payload.role_name)
        if role is None:
            raise ConflictError(f"Role '{payload.role_name}' does not exist.")

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role_id=role.id,
            checkpoint_id=payload.checkpoint_id,
        )
        return self.users.create(user)

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password.")

        if not user.is_active:
            raise UnauthorizedError("This account has been deactivated.")

        token = create_access_token(
            subject=str(user.id),
            extra_claims={
                "role": user.role.name,
                "checkpoint_id": str(user.checkpoint_id) if user.checkpoint_id else None,
            },
        )
        return TokenResponse(access_token=token)
