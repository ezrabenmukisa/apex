import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.core.dependencies import get_current_user
from app.services.project import get_project_details
from app.services.milestones import (
    create_milestone,
    get_project_milestones,
    get_milestone_by_id,
    update_milestone
)
from app.schemas import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse
)

router = APIRouter(tags=["Milestones"])

@router.post("/projects/{project_id}/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED, summary="Create milestone")
def create_new_milestone(
    project_id: uuid.UUID,
    payload: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Strict Creator Guard: Only OWNER can create milestones
    project = get_project_details(db=db, project_id=project_id, user_id=current_user.user_id)
    if not project or getattr(project, "current_user_role") != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can create milestones."
        )

    return create_milestone(db=db, project_id=project_id, payload=payload)

@router.get("/projects/{project_id}/milestones", response_model=list[MilestoneResponse], status_code=status.HTTP_200_OK, summary="List milestones")
def list_milestones(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Manager Read-Only Access / Member read check
    project = get_project_details(db=db, project_id=project_id, user_id=current_user.user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project not found or access denied."
        )

    return get_project_milestones(db=db, project_id=project_id)

@router.get("/milestones/{milestone_id}", response_model=MilestoneResponse, status_code=status.HTTP_200_OK, summary="Get milestone details")
def fetch_milestone_details(
    milestone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    milestone = get_milestone_by_id(db=db, milestone_id=milestone_id)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found.")

    project = get_project_details(db=db, project_id=milestone.project_id, user_id=current_user.user_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return milestone

@router.patch("/milestones/{milestone_id}", response_model=MilestoneResponse, status_code=status.HTTP_200_OK, summary="Update milestone")
def update_existing_milestone(
    milestone_id: uuid.UUID,
    payload: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    milestone = get_milestone_by_id(db=db, milestone_id=milestone_id)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found.")

    # Strict Creator Guard: Only OWNER can update milestones
    project = get_project_details(db=db, project_id=milestone.project_id, user_id=current_user.user_id)
    if not project or getattr(project, "current_user_role") != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can update milestones."
        )

    return update_milestone(db=db, milestone=milestone, payload=payload)