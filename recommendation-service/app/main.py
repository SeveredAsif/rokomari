"""
main.py
-------
The entry point of the recommendation service.
FastAPI reads this file when you run:
    uvicorn app.main:app --host 0.0.0.0 --port 8001

Node.js analogy:
----------------
This is your index.js / server.js. The equivalent would be:
    const express = require('express')
    const app = express()
    app.use('/search',          searchRouter)
    app.use('/recommendations', recommendationsRouter)
    app.listen(8001)
"""

from fastapi import FastAPI
from app.database import engine
from app import models
from app import search, recommendations

# Create all tables that don't exist yet.
# In production you'd use a proper migration tool (like Alembic),
# but for a lab project this is fine.
# Node.js equivalent: sequelize.sync() or running migration scripts manually.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Rokomari Recommendation Service",
    version="0.2.0",
    description="Product search and personalised recommendation engine for Rokomari.",
)

# Register routers
# Each router handles a group of related endpoints.
# Node.js equivalent: app.use('/search', searchRouter)
app.include_router(search.router)
app.include_router(recommendations.router)


@app.get("/health", tags=["Health"])
def health_check():
    """
    Simple health check endpoint.
    Docker Compose (and load balancers) ping this to know if the service is alive.
    If this returns 200, the container is considered healthy.
    """
    return {"status": "ok", "service": "recommendation-service"}


@app.get("/hello", tags=["Health"])
def hello():
    """Kept from the original skeleton for compatibility."""
    return {
        "message": "hello from recommendation service",
        "service": "recommendation-service",
    }
