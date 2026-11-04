import uuid
import secrets
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.models.enums import UserRole, ProjectStatus, InvitationStatus
from app.models.project import Project, ProjectMember, ProjectInvitation
from app.models.user import User


def create_project(db: Session, user_id: uuid.UUID, payload: ProjectCreate) -> Project:
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
    db.flush()

    db.add(ProjectMember(project_id=project.project_id, user_id=user_id, user_role=UserRole.OWNER))
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

    projects = []
    for proj, role in query.all():
        proj.current_user_role = role
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
    proj.current_user_role = role
    return proj


def get_project_owner_ids(db: Session, project_id: uuid.UUID) -> list[uuid.UUID]:
    rows = (
        db.query(ProjectMember.user_id)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_role == UserRole.OWNER)
        .all()
    )
    return [r[0] for r in rows]


def update_project(db: Session, project: Project, payload: ProjectUpdate) -> Project:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def get_project_members(db: Session, project_id: uuid.UUID) -> list[dict]:
    rows = (
        db.query(ProjectMember, User)
        .join(User, User.user_id == ProjectMember.user_id)
        .filter(ProjectMember.project_id == project_id)
        .all()
    )
    return [
        {
            "project_id": m.project_id,
            "user_id": m.user_id,
            "user_role": m.user_role,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "contact_email": u.contact_email,
        }
        for m, u in rows
    ]


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


def create_project_invitation(db: Session, project_id: uuid.UUID, email: str, user_role: UserRole) -> ProjectInvitation:
    invitation = ProjectInvitation(
        project_id=project_id,
        email=email.lower(),
        user_role=user_role,
        token=secrets.token_urlsafe(32),
        status=InvitationStatus.PENDING,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def accept_project_invitation(db: Session, token: str, user_id: uuid.UUID, user_email: str | None) -> ProjectMember:
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

    if not user_email or invitation.email.lower() != user_email.lower():
        raise ValueError("This invitation was sent to a different email address. Update your profile email to match.")

    existing_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == invitation.project_id,
        ProjectMember.user_id == user_id
    ).first()

    if existing_member:
        invitation.status = InvitationStatus.ACCEPTED
        db.commit()
        return existing_member

    member = ProjectMember(project_id=invitation.project_id, user_id=user_id, user_role=invitation.user_role)
    db.add(member)
    invitation.status = InvitationStatus.ACCEPTED
    db.commit()
    db.refresh(member)
    return member
