import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def get_user(self, user_id: uuid.UUID) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user

    def list_users(self) -> list[User]:
        return self.users.list_all()
