import os

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException

load_dotenv()

app = FastAPI(title="Recommendation Service", version="0.1.0")
SERVICE_TO_SERVICE_TOKEN = os.getenv("SERVICE_TO_SERVICE_TOKEN", "internal-token")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "recommendation-service"}


@app.get("/internal/recommendations/{user_id}")
def internal_recommendations(user_id: int, x_service_token: str | None = Header(default=None)):
    if x_service_token != SERVICE_TO_SERVICE_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    # In real life this would come from the recommendation model pipeline.
    sample_items = [
        "Atomic Habits",
        "Sapiens",
        "A Brief History of Time",
        "Deep Work",
        "Thinking, Fast and Slow",
    ]

    start = user_id % len(sample_items)
    recommendations = [sample_items[(start + i) % len(sample_items)] for i in range(3)]

    return {
        "user_id": user_id,
        "recommendations": recommendations,
        "source": "recommendation-service",
    }
