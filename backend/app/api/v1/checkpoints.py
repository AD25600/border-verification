import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.checkpoint import Checkpoint
from app.models.role import RoleName
from app.schemas.checkpoint import CheckpointCreate, CheckpointRead
from app.services.checkpoint_service import CheckpointService

router = APIRouter(prefix="/checkpoints", tags=["checkpoints"])


@router.get("", response_model=list[CheckpointRead], dependencies=[Depends(get_current_user)])
def list_checkpoints(db: Session = Depends(get_db)) -> list[Checkpoint]:
    return CheckpointService(db).list_checkpoints()


@router.post(
    "",
    response_model=CheckpointRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(RoleName.ADMIN))],
)
def create_checkpoint(payload: CheckpointCreate, db: Session = Depends(get_db)) -> Checkpoint:
    return CheckpointService(db).create_checkpoint(payload)


@router.get("/{checkpoint_id}", response_model=CheckpointRead, dependencies=[Depends(get_current_user)])
def get_checkpoint(checkpoint_id: uuid.UUID, db: Session = Depends(get_db)) -> Checkpoint:
    return CheckpointService(db).get_checkpoint(checkpoint_id)
