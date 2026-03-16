import os

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import User
from .schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
from .security import create_access_token, decode_access_token, hash_password, verify_password

load_dotenv()

app = FastAPI(title="Authentication Service", version="0.1.0")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

RECOMMENDATION_SERVICE_URL = os.getenv(
    "RECOMMENDATION_SERVICE_URL", "http://recommendation-service:8001"
)
SERVICE_TO_SERVICE_TOKEN = os.getenv("SERVICE_TO_SERVICE_TOKEN", "internal-token")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "authentication-service"}


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=user.email)
    recommendations = fetch_recommendations_for_user(user.id)

    return TokenResponse(access_token=token, recommendations=recommendations)


@app.get("/auth/me", response_model=UserResponse)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def fetch_recommendations_for_user(user_id: int) -> list[str]:
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get(
                f"{RECOMMENDATION_SERVICE_URL}/internal/recommendations/{user_id}",
                headers={"x-service-token": SERVICE_TO_SERVICE_TOKEN},
            )
        response.raise_for_status()
        return response.json().get("recommendations", [])
    except Exception:
        return []
