import os
import jwt
from decimal import Decimal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:8149@postgres:5432/rokomari",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Interaction Service", version="0.1.0", root_path="/interaction")

# JWT Authentication
bearer_scheme = HTTPBearer(auto_error=False)


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
    Verifies a user's JWT token and returns the decoded payload.
    The decoded payload contains 'sub' field with the user's email.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        decoded = jwt.decode(
            token,
            key=os.getenv("JWT_SECRET"),
            algorithms=["HS256"]
        )
        return decoded
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _resolve_user_id(db: Session, principal: str | int | None) -> int:
    """
    Resolves a JWT subject (email) or user_id integer to a user_id.
    Follows the pattern from productSearch-service/app/search.py.
    """
    if principal is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    as_text = str(principal).strip()
    if as_text.isdigit():
        return int(as_text)

    user = db.execute(text("SELECT user_id FROM users WHERE email = :email"), {"email": as_text}).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="User not found for token subject")

    return user.user_id


class ProductVisitRequest(BaseModel):
    user_id: int
    product_id: int


class SearchRequest(BaseModel):
    user_id: int
    searched_keyword: str


# JWT-authenticated request models (only need product_id or searched_keyword)
class ProductVisitRequestJWT(BaseModel):
    product_id: int


class SearchRequestJWT(BaseModel):
    searched_keyword: str


class AddressCreateRequest(BaseModel):
    user_id: int
    recipient_name: str
    phone: str
    address_line: str
    city: str
    area: str | None = None
    postal_code: str | None = None


class CartItemInput(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class SaveCartRequest(BaseModel):
    user_id: int
    items: list[CartItemInput]


class CreateOrderRequest(BaseModel):
    user_id: int
    address_id: int
    items: list[CartItemInput]
    payment_method: str = "COD"
    shipping_charge: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    order_status: str = "PENDING"


ALLOWED_PAYMENT_METHODS = {"COD", "BKASH", "NAGAD", "CARD", "BANK_TRANSFER"}
ALLOWED_ORDER_STATUSES = {"PENDING", "CONFIRMED", "PACKED", "SHIPPED", "DELIVERED", "CANCELLED"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_user_exists(db: Session, user_id: int) -> None:
    user = db.execute(text("SELECT user_id FROM users WHERE user_id = :user_id"), {"user_id": user_id}).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {user_id}")


def ensure_product_exists(db: Session, product_id: int) -> None:
    product = db.execute(
        text("SELECT product_id FROM products WHERE product_id = :product_id"),
        {"product_id": product_id},
    ).fetchone()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product not found: {product_id}")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Interaction service is running"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "service": "interaction-service"}


# Canonical route (matches other services that rely on root_path only)
@app.post("/product-visit", status_code=status.HTTP_201_CREATED)
# Backward-compatible alias for existing clients
@app.post("/interactions/product-visit", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def add_product_visit(payload: ProductVisitRequest, db: Session = Depends(get_db)):
    ensure_user_exists(db, payload.user_id)
    ensure_product_exists(db, payload.product_id)

    row = db.execute(
        text(
            """
            INSERT INTO product_visits (user_id, product_id)
            VALUES (:user_id, :product_id)
            RETURNING visit_id, user_id, product_id, visited_at
            """
        ),
        {"user_id": payload.user_id, "product_id": payload.product_id},
    ).fetchone()
    db.commit()

    return {
        "visit_id": row.visit_id,
        "user_id": row.user_id,
        "product_id": row.product_id,
        "visited_at": row.visited_at,
    }


@app.post("/search", status_code=status.HTTP_201_CREATED)
@app.post("/interactions/search", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def add_search_history(payload: SearchRequest, db: Session = Depends(get_db)):
    ensure_user_exists(db, payload.user_id)

    row = db.execute(
        text(
            """
            INSERT INTO search_history (user_id, searched_keyword)
            VALUES (:user_id, :searched_keyword)
            RETURNING search_id, user_id, searched_keyword, searched_at
            """
        ),
        {"user_id": payload.user_id, "searched_keyword": payload.searched_keyword},
    ).fetchone()
    db.commit()

    return {
        "search_id": row.search_id,
        "user_id": row.user_id,
        "searched_keyword": row.searched_keyword,
        "searched_at": row.searched_at,
    }


# JWT-authenticated variants: extract user_id from token
@app.post("/me/product-visit", status_code=status.HTTP_201_CREATED)
def add_product_visit_jwt(
    payload: ProductVisitRequestJWT,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt)
):
    """
    JWT-authenticated variant of POST /product-visit.
    Reads user_id from the JWT token's 'sub' field (email).
    Only requires product_id in the request body.
    """
    user_id = _resolve_user_id(db, current_user.get("sub"))
    ensure_user_exists(db, user_id)
    ensure_product_exists(db, payload.product_id)

    row = db.execute(
        text(
            """
            INSERT INTO product_visits (user_id, product_id)
            VALUES (:user_id, :product_id)
            RETURNING visit_id, user_id, product_id, visited_at
            """
        ),
        {"user_id": user_id, "product_id": payload.product_id},
    ).fetchone()
    db.commit()

    return {
        "visit_id": row.visit_id,
        "user_id": row.user_id,
        "product_id": row.product_id,
        "visited_at": row.visited_at,
    }


@app.post("/me/search", status_code=status.HTTP_201_CREATED)
def add_search_history_jwt(
    payload: SearchRequestJWT,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt)
):
    """
    JWT-authenticated variant of POST /search.
    Reads user_id from the JWT token's 'sub' field (email).
    Only requires searched_keyword in the request body.
    """
    user_id = _resolve_user_id(db, current_user.get("sub"))
    ensure_user_exists(db, user_id)

    row = db.execute(
        text(
            """
            INSERT INTO search_history (user_id, searched_keyword)
            VALUES (:user_id, :searched_keyword)
            RETURNING search_id, user_id, searched_keyword, searched_at
            """
        ),
        {"user_id": user_id, "searched_keyword": payload.searched_keyword},
    ).fetchone()
    db.commit()

    return {
        "search_id": row.search_id,
        "user_id": row.user_id,
        "searched_keyword": row.searched_keyword,
        "searched_at": row.searched_at,
    }


@app.post("/address", status_code=status.HTTP_201_CREATED)
@app.post("/interactions/address", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def add_address(payload: AddressCreateRequest, db: Session = Depends(get_db)):
    ensure_user_exists(db, payload.user_id)

    row = db.execute(
        text(
            """
            INSERT INTO addresses (user_id, recipient_name, phone, address_line, city, area, postal_code)
            VALUES (:user_id, :recipient_name, :phone, :address_line, :city, :area, :postal_code)
            RETURNING address_id, user_id, recipient_name, phone, address_line, city, area, postal_code, created_at
            """
        ),
        {
            "user_id": payload.user_id,
            "recipient_name": payload.recipient_name,
            "phone": payload.phone,
            "address_line": payload.address_line,
            "city": payload.city,
            "area": payload.area,
            "postal_code": payload.postal_code,
        },
    ).fetchone()
    db.commit()

    return {
        "address_id": row.address_id,
        "user_id": row.user_id,
        "recipient_name": row.recipient_name,
        "phone": row.phone,
        "address_line": row.address_line,
        "city": row.city,
        "area": row.area,
        "postal_code": row.postal_code,
        "created_at": row.created_at,
    }


@app.post("/cart/save")
@app.post("/interactions/cart/save", include_in_schema=False)
def save_cart(payload: SaveCartRequest, db: Session = Depends(get_db)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cart items cannot be empty")

    ensure_user_exists(db, payload.user_id)

    for item in payload.items:
        ensure_product_exists(db, item.product_id)

    try:
        cart = db.execute(
            text("SELECT cart_id FROM cart WHERE user_id = :user_id"),
            {"user_id": payload.user_id},
        ).fetchone()

        if cart:
            cart_id = cart.cart_id
        else:
            created_cart = db.execute(
                text("INSERT INTO cart (user_id) VALUES (:user_id) RETURNING cart_id"),
                {"user_id": payload.user_id},
            ).fetchone()
            cart_id = created_cart.cart_id

        db.execute(text("DELETE FROM cart_items WHERE cart_id = :cart_id"), {"cart_id": cart_id})

        for item in payload.items:
            db.execute(
                text(
                    """
                    INSERT INTO cart_items (cart_id, product_id, quantity)
                    VALUES (:cart_id, :product_id, :quantity)
                    """
                ),
                {
                    "cart_id": cart_id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                },
            )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Cart saved successfully",
        "user_id": payload.user_id,
        "cart_id": cart_id,
        "items_saved": len(payload.items),
    }


@app.post("/order", status_code=status.HTTP_201_CREATED)
@app.post("/interactions/order", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_order(payload: CreateOrderRequest, db: Session = Depends(get_db)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order items cannot be empty")

    if payload.payment_method not in ALLOWED_PAYMENT_METHODS:
        raise HTTPException(status_code=400, detail="Invalid payment_method")

    if payload.order_status not in ALLOWED_ORDER_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid order_status")

    ensure_user_exists(db, payload.user_id)

    address = db.execute(
        text("SELECT address_id FROM addresses WHERE address_id = :address_id AND user_id = :user_id"),
        {"address_id": payload.address_id, "user_id": payload.user_id},
    ).fetchone()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found for this user")

    product_ids = [item.product_id for item in payload.items]
    prices = db.execute(
        text("SELECT product_id, price FROM products WHERE product_id = ANY(:product_ids)"),
        {"product_ids": product_ids},
    ).fetchall()
    price_map = {row.product_id: Decimal(str(row.price)) for row in prices}

    missing_products = [pid for pid in product_ids if pid not in price_map]
    if missing_products:
        raise HTTPException(status_code=404, detail=f"Products not found: {missing_products}")

    subtotal = sum(price_map[item.product_id] * item.quantity for item in payload.items)
    total_amount = subtotal + payload.shipping_charge - payload.discount_amount
    if total_amount < 0:
        raise HTTPException(status_code=400, detail="Total amount cannot be negative")

    payment_status = "UNPAID" if payload.payment_method == "COD" else "PAID"

    try:
        order = db.execute(
            text(
                """
                INSERT INTO orders (user_id, address_id, total_amount, shipping_charge, discount_amount, order_status)
                VALUES (:user_id, :address_id, :total_amount, :shipping_charge, :discount_amount, :order_status)
                RETURNING order_id, order_date
                """
            ),
            {
                "user_id": payload.user_id,
                "address_id": payload.address_id,
                "total_amount": total_amount,
                "shipping_charge": payload.shipping_charge,
                "discount_amount": payload.discount_amount,
                "order_status": payload.order_status,
            },
        ).fetchone()

        for item in payload.items:
            db.execute(
                text(
                    """
                    INSERT INTO order_items (order_id, product_id, quantity)
                    VALUES (:order_id, :product_id, :quantity)
                    """
                ),
                {
                    "order_id": order.order_id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                },
            )

        db.execute(
            text(
                """
                INSERT INTO order_status_history (order_id, status, note)
                VALUES (:order_id, :status, :note)
                """
            ),
            {
                "order_id": order.order_id,
                "status": payload.order_status,
                "note": "Order created from interaction-service",
            },
        )

        db.execute(
            text(
                """
                INSERT INTO payments (order_id, payment_method, payment_status, transaction_id, paid_at)
                VALUES (:order_id, :payment_method, :payment_status, :transaction_id,
                        CASE WHEN :payment_status = 'PAID' THEN CURRENT_TIMESTAMP ELSE NULL END)
                """
            ),
            {
                "order_id": order.order_id,
                "payment_method": payload.payment_method,
                "payment_status": payment_status,
                "transaction_id": f"TXN-{order.order_id}",
            },
        )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Order created successfully",
        "order_id": order.order_id,
        "order_date": order.order_date,
        "user_id": payload.user_id,
        "total_amount": str(total_amount),
        "payment_status": payment_status,
        "items_count": len(payload.items),
    }
