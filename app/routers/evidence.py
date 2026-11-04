import uuid
from datetime import timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.enums import UserRole, EvidenceStatus
from app.core.dependencies import get_current_user
from app.services.milestones import get_milestone_by_id
from app.services.project import get_project_details, get_project_owner_ids
from app.services.notification import notify_users
from app.services.evidence import (
    generate_upload_tokens,
    create_evidence,
    get_latest_evidence,
    get_evidence_by_id,
    create_evidence_review,
    build_evidence_response,
)
from app.schemas.evidence import (
    EvidenceUploadRequest,
    EvidenceUploadResponse,
    EvidenceCreate,
    EvidenceResponse,
    EvidenceReviewCreate,
    EvidenceReviewResponse,
)

router = APIRouter(tags=["Evidence"])

_DECISION_WORDS = {
    "APPROVED": "approved",
    "REQUEST_CHANGES": "returned for changes",
    "FLAGGED": "flagged",
}


def _load_milestone_and_project(db: Session, milestone_id: uuid.UUID, user: User):
    milestone = get_milestone_by_id(db=db, milestone_id=milestone_id)
    if not milestone:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Milestone not found.")
    project = get_project_details(db=db, project_id=milestone.project_id, user_id=user.user_id)
    if not project:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")
    return milestone, project


def _require_manager(project) -> None:
    if project.current_user_role != UserRole.MANAGER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only project managers can submit evidence.")


@router.post("/milestones/{milestone_id}/evidence/upload-urls", response_model=list[EvidenceUploadResponse], summary="Get direct S3 upload URLs")
def get_evidence_upload_urls(
    milestone_id: uuid.UUID,
    payload: EvidenceUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    milestone, project = _load_milestone_and_project(db, milestone_id, current_user)
    _require_manager(project)
    return generate_upload_tokens(milestone_id=milestone.milestone_id, filenames=payload.filenames, folder=payload.folder)


@router.post("/milestones/{milestone_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED, summary="Submit progress evidence")
def submit_progress_evidence(
    milestone_id: uuid.UUID,
    payload: EvidenceCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    milestone, project = _load_milestone_and_project(db, milestone_id, current_user)
    _require_manager(project)

    evidence, created = create_evidence(db=db, milestone=milestone, user_id=current_user.user_id, payload=payload)
    response = build_evidence_response(evidence)

    if created:
        submitted = evidence.submitted_at.astimezone(timezone.utc)
        name = f"{current_user.first_name} {current_user.last_name}".strip()
        body = (
            f"Manager {name} submitted evidence for Milestone {milestone.sequence} "
            f"({milestone.title}) at {submitted:%d %b %Y, %H:%M} UTC."
        )
        notify_users(db, background_tasks, get_project_owner_ids(db, project.project_id), "New progress evidence", body)

    return response


@router.get("/milestones/{milestone_id}/evidence", response_model=EvidenceResponse, summary="Get evidence details")
def fetch_evidence_details(
    milestone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _load_milestone_and_project(db, milestone_id, current_user)

    evidence = get_latest_evidence(db=db, milestone_id=milestone_id)
    if not evidence:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No evidence submitted for this milestone.")
    return build_evidence_response(evidence)


@router.post("/evidence/{evidence_id}/reviews", response_model=EvidenceReviewResponse, status_code=status.HTTP_201_CREATED, summary="Review evidence submitted")
def review_progress_evidence(
    evidence_id: uuid.UUID,
    payload: EvidenceReviewCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evidence = get_evidence_by_id(db=db, evidence_id=evidence_id, for_update=True)
    if not evidence:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evidence not found.")

    milestone = get_milestone_by_id(db=db, milestone_id=evidence.milestone_id)
    project = get_project_details(db=db, project_id=milestone.project_id, user_id=current_user.user_id)
    if not project or project.current_user_role != UserRole.OWNER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only project owners can review and record decisions on evidence.")

    if evidence.status != EvidenceStatus.SUBMITTED:
        raise HTTPException(status.HTTP_409_CONFLICT, "This evidence has already been reviewed.")

    submitter_id = evidence.submitted_by
    milestone_label = f"Milestone {milestone.sequence} ({milestone.title})"
    review = create_evidence_review(db=db, evidence=evidence, payload=payload)

    decision = review.decision.value
    if submitter_id:
        notify_users(
            db, background_tasks, [submitter_id],
            "Evidence reviewed",
            f"Your evidence for {milestone_label} was {_DECISION_WORDS[decision]}. Comment: {review.comment}",
        )

    return EvidenceReviewResponse(
        evidence_id=review.evidence_id,
        decision=review.decision,
        comment=review.comment,
        message=f"Evidence review recorded successfully as {decision}.",
    )
