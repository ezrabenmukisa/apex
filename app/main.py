from fastapi import FastAPI

app = FastAPI(
    title="Apex API",
    version="1.0.0"
)

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "Apex API"}