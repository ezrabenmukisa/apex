import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.evidence import ProgressEvidence, EvidenceReview
from app.models.enums import EvidenceStatus
from app.schemas.evidence import EvidenceCreate, EvidenceReviewCreate
from app.core.storage import s3_service


def generate_upload_tokens(filenames: list[str], folder: str) -> list[dict]:
    results = []
    for filename in filenames:
        file_key, upload_url = s3_service.generate_presigned_upload_url(folder=folder, filename=filename)
        results.append({"file_key": file_key, "upload_url": upload_url})
    return results


def create_evidence(
    db: Session,
    milestone_id: uuid.UUID,
    payload: EvidenceCreate
) -> ProgressEvidence:
    # Create database record using the pre-uploaded S3 keys directly
    evidence = ProgressEvidence(
        milestone_id=milestone_id,
        description=payload.description,
        captured_latitude=payload.captured_latitude,
        captured_longitude=payload.captured_longitude,
        captured_at=payload.captured_at,
        site_media_urls=payload.site_media_keys,
        expenditure_notes=payload.expenditure_notes,
        total_cost_spent=payload.total_cost_spent,
        receipt_media_urls=payload.receipt_media_keys if payload.receipt_media_keys else None,
        status=EvidenceStatus.SUBMITTED,
        submitted_at=datetime.utcnow()
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def enrich_evidence_urls(evidence: ProgressEvidence) -> ProgressEvidence:
    """Helper to convert stored S3 keys into fresh presigned viewing URLs on read"""
    if evidence.site_media_urls:
        evidence.site_media_urls = [s3_service.generate_presigned_url(key) for key in evidence.site_media_urls]
    if evidence.receipt_media_urls:
        evidence.receipt_media_urls = [s3_service.generate_presigned_url(key) for key in evidence.receipt_media_urls]
    return evidence


def get_evidence_by_milestone(db: Session, milestone_id: uuid.UUID) -> ProgressEvidence | None:
    evidence = db.query(ProgressEvidence).filter(ProgressEvidence.milestone_id == milestone_id).first()
    if evidence:
        enrich_evidence_urls(evidence)
    return evidence


def get_evidence_by_id(db: Session, evidence_id: uuid.UUID) -> ProgressEvidence | None:
    evidence = db.query(ProgressEvidence).filter(ProgressEvidence.evidence_id == evidence_id).first()
    if evidence:
        enrich_evidence_urls(evidence)
    return evidence


def create_evidence_review(
    db: Session,
    evidence: ProgressEvidence,
    payload: EvidenceReviewCreate
) -> EvidenceReview:
    review = EvidenceReview(
        evidence_id=evidence.evidence_id,
        decision=payload.decision,
        comment=payload.comment
    )
    db.add(review)

    evidence.status = payload.decision
    db.commit()
    db.refresh(review)
    return review