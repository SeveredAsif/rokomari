from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import httpx
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
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

def _sql_run_01_path() -> Path:
    return Path(__file__).resolve().parent.parent / "sql_code_01.sql"

def _sql_run_02_path() -> Path:
    return Path(__file__).resolve().parent.parent / "sql_code_02.sql"


def _sql_run_03_path() -> Path:
    return Path(__file__).resolve().parent.parent / "sql_code_03.sql"


def _sql_run_04_path() -> Path:
    return Path(__file__).resolve().parent.parent / "sql_code_04.sql"


def _split_sql_statements(script: str) -> list[str]:
    statements = []
    current = []

    in_single_quote = False
    in_double_quote = False
    i = 0
    n = len(script)

    while i < n:
        ch = script[i]
        current.append(ch)

        if ch == "'" and not in_double_quote:
            # Handle SQL escaped single quote: ''
            if in_single_quote and i + 1 < n and script[i + 1] == "'":
                current.append(script[i + 1])
                i += 1
            else:
                in_single_quote = not in_single_quote

        elif ch == '"' and not in_single_quote:
            # Handle escaped double quote inside identifiers: ""
            if in_double_quote and i + 1 < n and script[i + 1] == '"':
                current.append(script[i + 1])
                i += 1
            else:
                in_double_quote = not in_double_quote

        elif ch == ";" and not in_single_quote and not in_double_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement[:-1].strip())  # remove trailing ;
            current = []

        i += 1

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)

    return statements


def _execute_sql_file(db: Session, sql_path: Path) -> None:
    script = sql_path.read_text(encoding="utf-8")
    statements = _split_sql_statements(script)

    print(f"Executing SQL bootstrap file: {sql_path}", flush=True)
    for statement in statements:
        if statement:
            db.execute(text(statement))
    db.commit()


def _existing_public_tables(db: Session) -> set[str]:
    return {
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


def _needs_sql_03(db: Session) -> bool:
    type_category_mismatch = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM products p
            JOIN categories c ON c.category_id = p.category_id
            WHERE
                (p.product_type = 'BOOK' AND lower(c.category_name) <> 'books')
                OR (p.product_type = 'STATIONERY' AND lower(c.category_name) <> 'stationery')
                OR (p.product_type = 'ELECTRONICS' AND lower(c.category_name) <> 'electronics')
                OR (p.product_type = 'GIFT' AND lower(c.category_name) <> 'gift items')
                OR (p.product_type = 'OTHER' AND lower(c.category_name) <> 'other')
            """
        )
    ).scalar() or 0

    dummy_book_metadata = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM book_details
            WHERE
                author ~ '^Author [0-9]+$'
                OR publisher ~ '^Publisher [0-9]+$'
            """
        )
    ).scalar() or 0

    missing_book_details = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM products p
            LEFT JOIN book_details bd ON bd.product_id = p.product_id
            WHERE p.product_type = 'BOOK' AND bd.product_id IS NULL
            """
        )
    ).scalar() or 0

    return (type_category_mismatch > 0) or (dummy_book_metadata > 0) or (missing_book_details > 0)


def _apply_update_scripts_if_needed(db: Session, existing_tables: set[str]) -> None:
    if "users" not in existing_tables or "products" not in existing_tables:
        print("Skipping sql_code updates: users/products table not ready yet.", flush=True)
        return

    # Check if sql_code_01 has been applied (marker: product_id=1 renamed)
    result = db.execute(text("SELECT product_name FROM products WHERE product_id = 1")).fetchone()
    current_name = result[0] if result else None
    if current_name != "A4 Spiral Notebook":
        sql_01 = _sql_run_01_path()
        if sql_01.exists():
            _execute_sql_file(db, sql_01)
            print("sql_code_01.sql executed successfully.", flush=True)
        else:
            print(f"Skipping sql_code_01.sql: file not found at {sql_01}", flush=True)
    else:
        print("sql_code_01.sql already applied.", flush=True)

    # Check if sql_code_02 has been applied (marker: image_url is VARCHAR(500))
    column_info = db.execute(
        text(
            """
            SELECT data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'image_url'
            """
        )
    ).fetchone()

    should_run_sql_02 = (
        not column_info
        or column_info[0] != "character varying"
        or column_info[1] != 500
    )
    if should_run_sql_02:
        sql_02 = _sql_run_02_path()
        if sql_02.exists():
            _execute_sql_file(db, sql_02)
            print("sql_code_02.sql executed successfully.", flush=True)
        else:
            print(f"Skipping sql_code_02.sql: file not found at {sql_02}", flush=True)
    else:
        print("sql_code_02.sql already applied.", flush=True)

    # Normalize taxonomy and enrich book metadata for reliable filtering.
    sql_03 = _sql_run_03_path()
    if not sql_03.exists():
        print(f"Skipping sql_code_03.sql: file not found at {sql_03}", flush=True)
        return

    if _needs_sql_03(db):
        _execute_sql_file(db, sql_03)
        print("sql_code_03.sql executed successfully.", flush=True)
    else:
        print("sql_code_03.sql already applied.", flush=True)

    # One-time visit rebalance migration (internally guarded by marker table).
    sql_04 = _sql_run_04_path()
    if sql_04.exists():
        _execute_sql_file(db, sql_04)
        print("sql_code_04.sql checked/applied successfully.", flush=True)
    else:
        print(f"Skipping sql_code_04.sql: file not found at {sql_04}", flush=True)

def ensure_schema_and_seed(db: Session) -> None:
    existing = _existing_public_tables(db)

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

    # Refresh table snapshot after possible bootstrap and then apply idempotent updates.
    existing = _existing_public_tables(db)
    _apply_update_scripts_if_needed(db, existing)


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


@app.get("/recommendation-demo")
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


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    existing_user = db.execute(
        text("SELECT user_id FROM users WHERE email = :email"),
        {"email": payload.email},
    ).fetchone()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    existing_phone = db.execute(
        text("SELECT user_id FROM users WHERE phone = :phone"),
        {"phone": payload.phone},
    ).fetchone()
    if existing_phone:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered")

    try:
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
    except IntegrityError as exc:
        db.rollback()
        diag = getattr(getattr(exc, "orig", None), "diag", None)
        constraint = getattr(diag, "constraint_name", "") or ""
        message = str(exc).lower()
        if "users_phone_key" in message or "phone" in constraint:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered")
        if "users_email_key" in message or "email" in constraint:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    return UserResponse(
        user_id=inserted.user_id,
        full_name=inserted.full_name,
        email=inserted.email,
        phone=inserted.phone,
        created_at=inserted.created_at,
    )


@app.post("/login", response_model=TokenResponse)
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


@app.get("/me", response_model=UserResponse)
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
