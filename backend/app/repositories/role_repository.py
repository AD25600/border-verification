from typing import Optional

from sqlalchemy.orm import Session

from app.models.role import Role


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.name == name).first()

    def list_all(self) -> list[Role]:
        return self.db.query(Role).order_by(Role.name).all()
