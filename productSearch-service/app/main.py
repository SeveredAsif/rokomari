"""
main.py
-------
The entry point of the product search service.
FastAPI reads this file when you run:
    uvicorn app.main:app --host 0.0.0.0 --port 8002
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from . import models
from . import search

load_dotenv()

# Create all tables that don't exist yet.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Rokomari Product Search Service",
    version="1.0.0",
    description="Product search engine for Rokomari using cosine similarity and semantic matching.",
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(search.router)


@app.get("/health", tags=["Health"])
def health_check():
    """Service health check endpoint."""
    return {"status": "ok", "service": "productSearch-service"}


@app.get("/hello", tags=["Health"])
def hello():
    """Hello endpoint for compatibility."""
    return {
        "message": "hello from product search service",
        "service": "productSearch-service",
    }


@app.get("/", tags=["Health"])
def root():
    """Root endpoint."""
    return {"message": "product search service is running"}
