import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.core.dependencies import get_current_user
from app.services.milestones import get_milestone_by_id
from app.services.project import get_project_details
from app.services.evidence import (
    generate_upload_tokens,
    create_evidence,
    get_evidence_by_milestone,
    get_evidence_by_id,
    create_evidence_review
)
from app.schemas import (
    EvidenceUploadRequest,
    EvidenceUploadResponse,
    EvidenceCreate,
    EvidenceResponse,
    EvidenceReviewCreate,
    EvidenceReviewResponse
)

router = APIRouter(tags=["Evidence"])


@router.post("/milestones/{milestone_id}/evidence/upload-urls", response_model=list[EvidenceUploadResponse], status_code=status.HTTP_200_OK, summary="Get direct S3 upload URLs")
def get_evidence_upload_urls(
    milestone_id: uuid.UUID,
    payload: EvidenceUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    milestone = get_milestone_by_id(db=db, milestone_id=milestone_id)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found.")

    project = get_project_details(db=db, project_id=milestone.project_id, user_id=current_user.user_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return generate_upload_tokens(filenames=payload.filenames, folder=payload.folder)


@router.post("/milestones/{milestone_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED, summary="Submit progress evidence")
def submit_progress_evidence(
    milestone_id: uuid.UUID,
    payload: EvidenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    milestone = get_milestone_by_id(db=db, milestone_id=milestone_id)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found.")

    project = get_project_details(db=db, project_id=milestone.project_id, user_id=current_user.user_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # Check if evidence already exists for this milestone (Immutable state rule)
    existing = get_evidence_by_milestone(db=db, milestone_id=milestone_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Evidence for this milestone has already been submitted. Editing is locked; corrections require a new submission cycle."
        )

    return create_evidence(db=db, milestone_id=milestone_id, payload=payload)


@router.get("/milestones/{milestone_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_200_OK, summary="Get evidence details")
def fetch_evidence_details(
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

    evidence = get_evidence_by_milestone(db=db, milestone_id=milestone_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No evidence submitted for this milestone.")

    return evidence


@router.post("/evidence/{evidence_id}/reviews", response_model=EvidenceReviewResponse, status_code=status.HTTP_201_CREATED, summary="Review evidence submitted")
def review_progress_evidence(
    evidence_id: uuid.UUID,
    payload: EvidenceReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evidence = get_evidence_by_id(db=db, evidence_id=evidence_id)
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found.")

    # Verify project owner access
    milestone = get_milestone_by_id(db=db, milestone_id=evidence.milestone_id)
    project = get_project_details(db=db, project_id=milestone.project_id, user_id=current_user.user_id)
    if not project or getattr(project, "current_user_role") != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can review and record decisions on evidence."
        )

    review = create_evidence_review(db=db, evidence=evidence, payload=payload)
    
    return EvidenceReviewResponse(
        evidence_id=evidence.evidence_id,
        decision=review.decision,
        comment=review.comment,
        message=f"Evidence review recorded successfully as {review.decision}."
    )