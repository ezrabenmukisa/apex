import uuid
from sqlalchemy.orm import Session
from decimal import Decimal
from app.models.milestone import Milestone
from app.schemas.milestone import MilestoneCreate, MilestoneUpdate

def create_milestone(db: Session, project_id: uuid.UUID, payload: MilestoneCreate) -> Milestone:
    milestone = Milestone(
        project_id=project_id,
        title=payload.title,
        sequence=payload.sequence,
        description=payload.description,
        start_date=payload.start_date,
        due_date=payload.due_date,
        planned_budget=payload.planned_budget,
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone

def get_project_milestones(db: Session, project_id: uuid.UUID) -> list[Milestone]:
    return (
        db.query(Milestone)
        .filter(Milestone.project_id == project_id)
        .order_by(Milestone.sequence.asc())
        .all()
    )

def get_milestone_by_id(db: Session, milestone_id: uuid.UUID) -> Milestone | None:
    return db.query(Milestone).filter(Milestone.milestone_id == milestone_id).first()

def update_milestone(db: Session, milestone: Milestone, payload: MilestoneUpdate) -> Milestone:
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(milestone, key, value)
    
    db.commit()
    db.refresh(milestone)
    return milestone