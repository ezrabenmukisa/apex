import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.enums import ProjectStatus, UserRole
from app.core.dependencies import get_current_user
from app.services.project import (
    create_project, get_user_projects, 
    get_project_details, update_project, 
    get_project_members, remove_project_member, 
    create_project_invitation, accept_project_invitation
)
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, 
    ProjectMemberResponse, ProjectInvitationCreate, 
    ProjectInvitationResponse, ProjectInvitationAccept
)

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create project")
def create_new_project(
    payload: ProjectCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    project = create_project(db=db, user_id=current_user.user_id, payload=payload)
    setattr(project, "current_user_role", UserRole.OWNER)
    return project



@router.get("", response_model=list[ProjectResponse], summary="List projects")
def list_my_projects(
    status_filter: ProjectStatus | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    projects = get_user_projects(db=db, user_id=current_user.user_id, status=status_filter)
    return projects



@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project details")
def fetch_project_details(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_project_details(db=db, project_id=project_id, user_id=current_user.user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project."
        )
    return project



@router.patch("/{project_id}", response_model=ProjectResponse, summary="Update project metadata")
def update_existing_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_project_details(db=db, project_id=project_id, user_id=current_user.user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project not found or access denied."
        )
    
    # Enforce strict creator/owner guard for updates
    if getattr(project, "current_user_role") != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can update project metadata."
        )

    updated_project = update_project(db=db, project=project, payload=payload)
    setattr(updated_project, "current_user_role", UserRole.OWNER)
    return updated_project



@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse], status_code=status.HTTP_200_OK, summary="List project members")
def list_project_members(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_project_details(db=db, project_id=project_id, user_id=current_user.user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project not found or access denied."
        )

    return get_project_members(db=db, project_id=project_id)



@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_200_OK, summary="Remove member access")
def revoke_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_project_details(db=db, project_id=project_id, user_id=current_user.user_id)
    if not project or getattr(project, "current_user_role") not in [UserRole.OWNER, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to revoke members from this project."
        )

    success = remove_project_member(db=db, project_id=project_id, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project member not found."
        )

    return {"message": "Successfully removed member from project."}



@router.post("/{project_id}/members", response_model=ProjectInvitationResponse, status_code=status.HTTP_201_CREATED, summary="Invite member to project")
def invite_project_member(
    project_id: uuid.UUID,
    payload: ProjectInvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify current user has access and is owner/manager
    project = get_project_details(db=db, project_id=project_id, user_id=current_user.user_id)
    if not project or getattr(project, "current_user_role") not in [UserRole.OWNER, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to manage members for this project."
        )

    invitation = create_project_invitation(
        db=db,
        project_id=project_id,
        project_name=project.project_name,
        email=payload.email,
        user_role=payload.user_role
    )
    return invitation



@router.post("/invitations/accept", status_code=status.HTTP_200_OK, summary="Accept project invitation")
def accept_invitation(
    payload: ProjectInvitationAccept,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        member = accept_project_invitation(
            db=db,
            token=payload.token,
            user_id=current_user.user_id,
            user_email=current_user.email
        )
        return {"message": "Successfully joined project.", "project_id": member.project_id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))