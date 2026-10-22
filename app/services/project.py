import uuid
import secrets
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.core.email import send_invitation_email
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.models.enums import UserRole, ProjectStatus, InvitationStatus
from app.models.project import Project, ProjectMember, ProjectInvitation

def create_project(db: Session, user_id: uuid.UUID, payload: ProjectCreate) -> Project:
    # 1. Create the project instance
    project = Project(
        project_name=payload.project_name,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_name=payload.location_name,
        planned_budget=payload.planned_budget,
        currency=payload.currency or "UGX",
        target_completion_date=payload.target_completion_date,
        status=ProjectStatus.ACTIVE
    )
    db.add(project)
    db.flush()  # Generates project.project_id

    # 2. Assign the creator as the OWNER in project_members
    member = ProjectMember(
        project_id=project.project_id,
        user_id=user_id,
        user_role=UserRole.OWNER
    )
    db.add(member)

    db.commit()
    db.refresh(project)
    return project

def get_user_projects(db: Session, user_id: uuid.UUID, status: ProjectStatus | None = None) -> list[Project]:
    query = (
        db.query(Project, ProjectMember.user_role)
        .join(ProjectMember, Project.project_id == ProjectMember.project_id)
        .filter(ProjectMember.user_id == user_id)
    )
    if status:
        query = query.filter(Project.status == status)

    results = query.all()
    projects = []
    for proj, role in results:
        setattr(proj, "current_user_role", role)
        projects.append(proj)
    return projects

def get_project_details(db: Session, project_id: uuid.UUID, user_id: uuid.UUID) -> Project | None:
    result = (
        db.query(Project, ProjectMember.user_role)
        .join(ProjectMember, Project.project_id == ProjectMember.project_id)
        .filter(Project.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )
    if not result:
        return None
    proj, role = result
    setattr(proj, "current_user_role", role)
    return proj

def update_project(db: Session, project: Project, payload: ProjectUpdate) -> Project:
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return project

def get_project_members(db: Session, project_id: uuid.UUID) -> list[ProjectMember]:
    return db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()

def remove_project_member(db: Session, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    if not member:
        return False
    db.delete(member)
    db.commit()
    return True

def create_project_invitation(db: Session, project_id: uuid.UUID, project_name: str, email: str, user_role: UserRole) -> ProjectInvitation:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invitation = ProjectInvitation(
        project_id=project_id,
        email=email,
        user_role=user_role,
        token=token,
        status=InvitationStatus.PENDING,
        expires_at=expires_at
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    try:
        send_invitation_email(email, project_name, token)
    except Exception as e:
        print(f"Failed to send SMTP email: {e}")

    return invitation

def accept_project_invitation(db: Session, token: str, user_id: uuid.UUID, user_email: str) -> ProjectMember:
    invitation = db.query(ProjectInvitation).filter(
        ProjectInvitation.token == token,
        ProjectInvitation.status == InvitationStatus.PENDING
    ).first()

    if not invitation:
        raise ValueError("Invalid or expired invitation token.")

    if invitation.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        invitation.status = InvitationStatus.EXPIRED
        db.commit()
        raise ValueError("This invitation has expired.")

    if invitation.email.lower() != user_email.lower():
        raise ValueError("This invitation was sent to a different email address.")

    existing_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == invitation.project_id,
        ProjectMember.user_id == user_id
    ).first()

    if existing_member:
        invitation.status = InvitationStatus.ACCEPTED
        db.commit()
        return existing_member

    member = ProjectMember(
        project_id=invitation.project_id,
        user_id=user_id,
        user_role=invitation.user_role
    )
    db.add(member)
    invitation.status = InvitationStatus.ACCEPTED
    db.commit()
    db.refresh(member)
    return member