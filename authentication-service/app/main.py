from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

try:
    from .database import get_db
    from .schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
    from .security import create_access_token, decode_access_token, hash_password, verify_password
except ImportError:
    from database import get_db
    from schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
    from security import create_access_token, decode_access_token, hash_password, verify_password

load_dotenv()

app = FastAPI(title="Authentication Service", version="0.2.0", root_path="/auth")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
RECOMMENDATION_SERVICE_URL = os.getenv("RECOMMENDATION_SERVICE_URL", "http://localhost:8001")

REQUIRED_TABLES = [
    "users",
    "admins",
    "categories",
    "products",
    "book_details",
    "electronics_details",
    "search_history",
    "product_visits",
    "addresses",
    "cart",
    "cart_items",
    "orders",
    "order_items",
    "payments",
    "order_status_history",
]


def _table_creation_sql_path() -> Path:
    return Path(__file__).resolve().parent.parent / "table_creation.sql"


def _insert_code_sql_path() -> Path:
    return Path(__file__).resolve().parent.parent / "insert_code.sql"


def _execute_sql_file(db: Session, sql_path: Path) -> None:
    script = sql_path.read_text(encoding="utf-8")
    statements = [stmt.strip() for stmt in script.split(";") if stmt.strip()]

    print(f"Executing SQL bootstrap file: {sql_path}", flush=True)
    for statement in statements:
        db.execute(text(statement))
    db.commit()


def ensure_schema_and_seed(db: Session) -> None:
    existing = {
        row[0]
        for row in db.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
        ).fetchall()
    }

    missing_tables = [table for table in REQUIRED_TABLES if table not in existing]
    if missing_tables:
        # Run the provided SQL bootstrap only when core schema is absent.
        print(f"Missing tables detected: {', '.join(missing_tables)}", flush=True)
        if "users" not in existing:
            table_sql = _table_creation_sql_path()
            insert_sql = _insert_code_sql_path()

            if not table_sql.exists():
                raise RuntimeError(f"Missing SQL file: {table_sql}")
            if not insert_sql.exists():
                raise RuntimeError(f"Missing SQL file: {insert_sql}")

            _execute_sql_file(db, table_sql)
            _execute_sql_file(db, insert_sql)
            print("Schema bootstrap completed successfully.", flush=True)
        else:
            raise RuntimeError(
                "Some required tables are missing but users table already exists. "
                "Skipping table_creation.sql to avoid destructive DROP SCHEMA. "
                f"Missing: {', '.join(missing_tables)}"
            )


@app.on_event("startup")
def on_startup() -> None:
    db = next(get_db())
    try:
        ensure_schema_and_seed(db)
    finally:
        db.close()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Authentication service is running"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "service": "authentication-service"}


@app.get("/auth/recommendation-demo")
def recommendation_demo() -> dict:
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{RECOMMENDATION_SERVICE_URL}/hello")
        response.raise_for_status()
        payload = response.json()
        print(f"Recommendation service replied: {payload}")
        return {
            "called_service": "recommendation-service",
            "response": payload,
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"recommendation-service unavailable: {exc}")


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    existing_user = db.execute(
        text("SELECT user_id FROM users WHERE email = :email"),
        {"email": payload.email},
    ).fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    inserted = db.execute(
        text(
            """
            INSERT INTO users (full_name, email, phone, password_hash)
            VALUES (:full_name, :email, :phone, :password_hash)
            RETURNING user_id, full_name, email, phone, created_at
            """
        ),
        {
            "full_name": payload.full_name,
            "email": payload.email,
            "phone": payload.phone,
            "password_hash": hash_password(payload.password),
        },
    ).fetchone()
    db.commit()

    return UserResponse(
        user_id=inserted.user_id,
        full_name=inserted.full_name,
        email=inserted.email,
        phone=inserted.phone,
        created_at=inserted.created_at,
    )


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.execute(
        text(
            """
            SELECT user_id, email, password_hash
            FROM users
            WHERE email = :email
            """
        ),
        {"email": payload.email},
    ).fetchone()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


@app.get("/auth/me", response_model=UserResponse)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserResponse:
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.execute(
        text(
            """
            SELECT user_id, full_name, email, phone, created_at
            FROM users
            WHERE email = :email
            """
        ),
        {"email": email},
    ).fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        created_at=user.created_at,
    )
