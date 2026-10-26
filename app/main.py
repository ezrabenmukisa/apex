import app.core.firebase
from fastapi import FastAPI
from app.routers import auth_router, user_router, links_router, project_router, milestones_router, evidence_router, notifications_router

app = FastAPI(
    title="Apex API",
    version="1.0.0"
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(links_router)
app.include_router(project_router, prefix="/api/v1")
app.include_router(milestones_router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "Apex API"}
