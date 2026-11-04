import uuid
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.enums import ProjectStatus, UserRole
from app.core.dependencies import get_current_user
from app.core.email import send_invitation_email
from app.services.project import (
    create_project, get_user_projects, get_project_details, update_project,
    get_project_members, remove_project_member,
    create_project_invitation, accept_project_invitation,
)
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse,
    ProjectMemberResponse, ProjectInvitationCreate, ProjectInvitationResponse,
    ProjectInvitationAccept, ProjectInvitationAcceptResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["Projects"])


def _get_project_or_403(db: Session, project_id: uuid.UUID, user: User):
    project = get_project_details(db=db, project_id=project_id, user_id=user.user_id)
    if not project:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Project not found or access denied.")
    return project


def _get_owned_project_or_403(db: Session, project_id: uuid.UUID, user: User, action: str):
    project = _get_project_or_403(db, project_id, user)
    if project.current_user_role != UserRole.OWNER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Only the project owner can {action}.")
    return project


def _send_invite_safely(to_email: str, project_name: str, token: str, message: str) -> None:
    try:
        send_invitation_email(to_email, project_name, token, message)
    except Exception:
        logger.exception("Failed to send invitation email to %s", to_email)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create project")
def create_new_project(payload: ProjectCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = create_project(db=db, user_id=current_user.user_id, payload=payload)
    project.current_user_role = UserRole.OWNER
    return project


@router.get("", response_model=ProjectListResponse, summary="List projects")
def list_my_projects(
    status_filter: ProjectStatus | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = get_user_projects(db=db, user_id=current_user.user_id, status=status_filter)
    return ProjectListResponse(items=[ProjectResponse.model_validate(p) for p in projects])


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project details")
def fetch_project_details(project_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_project_or_403(db, project_id, current_user)


@router.patch("/{project_id}", response_model=ProjectResponse, summary="Update project metadata")
def update_existing_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_owned_project_or_403(db, project_id, current_user, "update project metadata")
    updated = update_project(db=db, project=project, payload=payload)
    updated.current_user_role = UserRole.OWNER
    return updated


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse], summary="List project members")
def list_project_members(project_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_project_or_403(db, project_id, current_user)
    return get_project_members(db=db, project_id=project_id)


@router.delete("/{project_id}/members/{user_id}", summary="Remove member access")
def revoke_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_project_or_403(db, project_id, current_user, "remove members")

    if user_id == current_user.user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The owner cannot remove themselves.")

    if not remove_project_member(db=db, project_id=project_id, user_id=user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project member not found.")
    return {"message": "Successfully removed member from project."}


@router.post("/{project_id}/members", response_model=ProjectInvitationResponse, status_code=status.HTTP_201_CREATED, summary="Invite member to project")
def invite_project_member(
    project_id: uuid.UUID,
    payload: ProjectInvitationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_owned_project_or_403(db, project_id, current_user, "invite members")

    if payload.user_role == UserRole.OWNER:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot invite another owner.")

    invitation = create_project_invitation(
        db=db, project_id=project_id, email=payload.contact_email, user_role=payload.user_role
    )
    background_tasks.add_task(
        _send_invite_safely, invitation.email, project.project_name, invitation.token, payload.message
    )
    return invitation


@router.post("/invitations/accept", response_model=ProjectInvitationAcceptResponse, summary="Accept project invitation")
def accept_invitation(
    payload: ProjectInvitationAccept,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        member = accept_project_invitation(
            db=db,
            token=payload.token,
            user_id=current_user.user_id,
            user_email=current_user.contact_email,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"message": "Successfully joined project.", "project_id": member.project_id}
