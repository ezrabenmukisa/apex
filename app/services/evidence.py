import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.evidence import ProgressEvidence, EvidenceReview
from app.models.enums import EvidenceStatus
from app.models.milestone import Milestone
from app.schemas.evidence import EvidenceCreate, EvidenceReviewCreate, EvidenceResponse
from app.core.storage import s3_service


def _key_prefix(milestone_id: uuid.UUID, folder: str) -> str:
    return f"evidence/{milestone_id}/{folder}"


def generate_upload_tokens(milestone_id: uuid.UUID, filenames: list[str], folder: str) -> list[dict]:
    prefix = _key_prefix(milestone_id, folder)
    results = []
    for filename in filenames:
        file_key, upload_url = s3_service.generate_presigned_upload_url(prefix=prefix, filename=filename)
        results.append({"file_key": file_key, "upload_url": upload_url})
    return results


def _validate_keys(milestone_id: uuid.UUID, keys: list[str], folder: str) -> None:
    """Keys must be ones this server issued for THIS milestone and must already be uploaded.
    Without this, a member could submit any key in the bucket and receive a view URL for it."""
    prefix = _key_prefix(milestone_id, folder) + "/"
    for key in keys:
        if not key.startswith(prefix) or ".." in key:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid {folder} file key.")
        if not s3_service.object_exists(key):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "A file was not found in storage. Finish the upload and try again.")


def get_latest_evidence(db: Session, milestone_id: uuid.UUID) -> ProgressEvidence | None:
    return (
        db.query(ProgressEvidence)
        .filter(ProgressEvidence.milestone_id == milestone_id)
        .order_by(ProgressEvidence.submitted_at.desc())
        .first()
    )


def get_evidence_by_id(db: Session, evidence_id: uuid.UUID, for_update: bool = False) -> ProgressEvidence | None:
    query = db.query(ProgressEvidence).filter(ProgressEvidence.evidence_id == evidence_id)
    if for_update:
        query = query.with_for_update()   # stops two simultaneous reviews of the same evidence
    return query.first()


def create_evidence(
    db: Session,
    milestone: Milestone,
    user_id: uuid.UUID,
    payload: EvidenceCreate,
) -> tuple[ProgressEvidence, bool]:
    """Returns (evidence, created). created=False means this exact submission already went through
    (an offline-queue retry after a dropped response), so nothing new was stored."""
    latest = get_latest_evidence(db, milestone.milestone_id)
    if latest is not None:
        if (
            latest.status == EvidenceStatus.SUBMITTED
            and latest.submitted_by == user_id
            and list(latest.site_media_urls) == payload.site_media_keys
        ):
            return latest, False
        if latest.status != EvidenceStatus.REQUEST_CHANGES:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Evidence for this milestone is already submitted. A new submission is only allowed after changes are requested.",
            )

    _validate_keys(milestone.milestone_id, payload.site_media_keys, "site_media")
    receipt_keys = payload.receipt_media_keys or []
    _validate_keys(milestone.milestone_id, receipt_keys, "receipt_media")

    evidence = ProgressEvidence(
        milestone_id=milestone.milestone_id,
        submitted_by=user_id,
        description=payload.description,
        captured_latitude=payload.captured_latitude,
        captured_longitude=payload.captured_longitude,
        captured_at=payload.captured_at,
        site_media_urls=payload.site_media_keys,
        expenditure_notes=payload.expenditure_notes,
        total_cost_spent=payload.total_cost_spent,
        receipt_media_urls=receipt_keys or None,
        status=EvidenceStatus.SUBMITTED,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(evidence)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Evidence for this milestone was just submitted.")
    db.refresh(evidence)
    return evidence, True


def build_evidence_response(evidence: ProgressEvidence) -> EvidenceResponse:
    """Builds the API response with fresh presigned URLs WITHOUT touching the ORM object.
    (The old enrich_evidence_urls overwrote the stored S3 keys with temporary URLs, and the next
    commit, e.g. on review, saved those URLs to the database.)"""
    return EvidenceResponse(
        evidence_id=evidence.evidence_id,
        milestone_id=evidence.milestone_id,
        description=evidence.description,
        captured_latitude=evidence.captured_latitude,
        captured_longitude=evidence.captured_longitude,
        captured_at=evidence.captured_at,
        site_media_urls=[s3_service.generate_presigned_url(k) for k in (evidence.site_media_urls or [])],
        expenditure_notes=evidence.expenditure_notes,
        total_cost_spent=evidence.total_cost_spent,
        receipt_media_urls=[s3_service.generate_presigned_url(k) for k in (evidence.receipt_media_urls or [])],
        status=evidence.status,
        submitted_at=evidence.submitted_at,
    )


def create_evidence_review(db: Session, evidence: ProgressEvidence, payload: EvidenceReviewCreate) -> EvidenceReview:
    review = EvidenceReview(
        evidence_id=evidence.evidence_id,
        decision=payload.decision,
        comment=payload.comment,
    )
    db.add(review)
    evidence.status = EvidenceStatus(payload.decision.value)
    db.commit()
    db.refresh(review)
    return review
