import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.checkpoint import Checkpoint
from app.repositories.checkpoint_repository import CheckpointRepository
from app.schemas.checkpoint import CheckpointCreate


class CheckpointService:
    def __init__(self, db: Session):
        self.db = db
        self.checkpoints = CheckpointRepository(db)

    def list_checkpoints(self) -> list[Checkpoint]:
        return self.checkpoints.list_all()

    def get_checkpoint(self, checkpoint_id: uuid.UUID) -> Checkpoint:
        checkpoint = self.checkpoints.get_by_id(checkpoint_id)
        if checkpoint is None:
            raise NotFoundError("Checkpoint not found.")
        return checkpoint

    def create_checkpoint(self, payload: CheckpointCreate) -> Checkpoint:
        if self.checkpoints.get_by_code(payload.code):
            raise ConflictError(f"Checkpoint code '{payload.code}' already exists.")

        checkpoint = Checkpoint(**payload.model_dump())
        return self.checkpoints.create(checkpoint)
