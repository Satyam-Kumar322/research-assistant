from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas
from utils import get_current_user

router = APIRouter()


# ─── GET /api/workspace/ ──────────────────────────────────────────────────────

@router.get("/", response_model=List[schemas.WorkspaceResponse])
def get_workspaces(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all workspaces for the authenticated user."""
    return db.query(models.Workspace).filter(
        models.Workspace.user_id == current_user.id
    ).all()


# ─── POST /api/workspace/ ─────────────────────────────────────────────────────

@router.post("/", response_model=schemas.WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace_data: schemas.WorkspaceCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new workspace for the authenticated user."""
    workspace = models.Workspace(
        user_id=current_user.id,
        project_name=workspace_data.project_name,
        description=workspace_data.description
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


# ─── GET /api/workspace/{id} ──────────────────────────────────────────────────

@router.get("/{workspace_id}", response_model=schemas.WorkspaceResponse)
def get_workspace(
    workspace_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific workspace. Only accessible by its owner."""
    workspace = db.query(models.Workspace).filter(
        models.Workspace.workspace_id == workspace_id,
        models.Workspace.user_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found or access denied"
        )
    return workspace


# ─── DELETE /api/workspace/{id} ───────────────────────────────────────────────

@router.delete("/{workspace_id}", response_model=schemas.MessageResponse)
def delete_workspace(
    workspace_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a workspace. Only the owner can delete it."""
    workspace = db.query(models.Workspace).filter(
        models.Workspace.workspace_id == workspace_id,
        models.Workspace.user_id == current_user.id
    ).first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found or access denied"
        )

    db.delete(workspace)
    db.commit()
    return schemas.MessageResponse(message=f"Workspace '{workspace.project_name}' deleted successfully")
