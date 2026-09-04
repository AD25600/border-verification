import uuid
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.role), joinedload(User.checkpoint))
            .filter(User.id == user_id)
            .first()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.role), joinedload(User.checkpoint))
            .filter(User.email == email)
            .first()
        )

    def list_all(self) -> list[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.role), joinedload(User.checkpoint))
            .order_by(User.created_at.desc())
            .all()
        )

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
