import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.checkpoint import Checkpoint


class CheckpointRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, checkpoint_id: uuid.UUID) -> Optional[Checkpoint]:
        return self.db.query(Checkpoint).filter(Checkpoint.id == checkpoint_id).first()

    def get_by_code(self, code: str) -> Optional[Checkpoint]:
        return self.db.query(Checkpoint).filter(Checkpoint.code == code).first()

    def list_all(self) -> list[Checkpoint]:
        return self.db.query(Checkpoint).order_by(Checkpoint.name).all()

    def create(self, checkpoint: Checkpoint) -> Checkpoint:
        self.db.add(checkpoint)
        self.db.commit()
        self.db.refresh(checkpoint)
        return checkpoint
