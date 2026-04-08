from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import get_db
from .auth import verify_jwt, verify_jwt_optional
from .similarity import compute_cosine_similarities, filter_by_threshold, rank_by_similarity
from .cache import cache_get, cache_set
from . import models

router = APIRouter(prefix="/search", tags=["Search"])

SEARCH_CACHE_VERSION = "v3"
ALLOWED_PRODUCT_TYPES = {"BOOK", "STATIONERY", "ELECTRONICS", "GIFT", "OTHER"}


def _resolve_user_id(db: Session, principal: str | int | None) -> int:
    if principal is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if isinstance(principal, int):
        return principal

    principal_text = str(principal).strip()
    if principal_text.isdigit():
        return int(principal_text)

    user = db.query(models.User).filter(models.User.email == principal_text).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found for token subject")

    return user.user_id


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _normalize_product_types(raw_product_types: str | None) -> list[str]:
    if not raw_product_types:
        return []

    normalized: list[str] = []
    for token in raw_product_types.split(","):
        item = token.strip().upper()
        if item and item in ALLOWED_PRODUCT_TYPES and item not in normalized:
            normalized.append(item)

    return normalized


def _build_cache_key(
    *,
    user_id: int | str,
    query: str,
    threshold: float,
    min_price: float | None,
    max_price: float | None,
    product_types: list[str],
    brand: str | None,
    author: str | None,
    publisher: str | None,
    sort_by: str,
    sort_order: str,
) -> str:
    parts = [
        query,
        f"t{threshold:.3f}",
        f"min{'' if min_price is None else f'{min_price:.2f}'}",
        f"max{'' if max_price is None else f'{max_price:.2f}'}",
        f"types:{','.join(product_types)}",
        f"brand:{(brand or '').lower()}",
        f"author:{(author or '').lower()}",
        f"publisher:{(publisher or '').lower()}",
        f"sort:{sort_by}:{sort_order}",
    ]
    return f"search:{SEARCH_CACHE_VERSION}:{user_id}:{'|'.join(parts)}"


def _sort_results(results: list[dict], sort_by: str, sort_order: str) -> list[dict]:
    reverse = sort_order == "desc"

    if sort_by == "price":
        if reverse:
            return sorted(
                results,
                key=lambda item: item["price"] if item["price"] is not None else -1.0,
                reverse=True,
            )
        return sorted(
            results,
            key=lambda item: item["price"] if item["price"] is not None else float("inf"),
        )

    if sort_by == "name":
        return sorted(results, key=lambda item: (item.get("name") or "").lower(), reverse=reverse)

    return sorted(results, key=lambda item: item.get("similarity_score", 0.0), reverse=reverse)


@router.get("")
def search_products(
    q: str = Query(..., min_length=1, description="Search keyword"),
    threshold: float = Query(0.1, ge=0.0, le=1.0, description="Similarity threshold"),
    limit: int = Query(50, ge=1, le=200, description="Max number of results"),
    min_price: float | None = Query(None, ge=0.0, description="Minimum price filter"),
    max_price: float | None = Query(None, ge=0.0, description="Maximum price filter"),
    product_types: str | None = Query(None, description="Comma-separated product types"),
    brand: str | None = Query(None, description="Brand contains filter"),
    author: str | None = Query(None, description="Book author contains filter"),
    publisher: str | None = Query(None, description="Book publisher contains filter"),
    sort_by: str = Query("relevance", pattern="^(relevance|price|name)$", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db),
    current_user: dict | None = Depends(verify_jwt_optional),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price cannot be greater than max_price")

    user_id: int | None = None
    if current_user is not None:
        user_id = _resolve_user_id(db, current_user.get("sub"))

    normalized_q = q.lower().strip()
    normalized_brand = _normalize_optional(brand)
    normalized_author = _normalize_optional(author)
    normalized_publisher = _normalize_optional(publisher)
    normalized_types = _normalize_product_types(product_types)

    if product_types and not normalized_types:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid product_types. Allowed values: "
                + ", ".join(sorted(ALLOWED_PRODUCT_TYPES))
            ),
        )

    cache_key = _build_cache_key(
        user_id=user_id if user_id is not None else "anon",
        query=normalized_q,
        threshold=threshold,
        min_price=min_price,
        max_price=max_price,
        product_types=normalized_types,
        brand=normalized_brand,
        author=normalized_author,
        publisher=normalized_publisher,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    cached = cache_get(cache_key)
    if cached is not None:
        return {
            "source": "cache",
            "query": q,
            "count": len(cached[:limit]),
            "threshold": threshold,
            "sort": {"by": sort_by, "order": sort_order},
            "results": cached[:limit],
        }

    products_query = (
        db.query(
            models.Product.product_id.label("product_id"),
            models.Product.product_name.label("product_name"),
            models.Product.description.label("description"),
            models.Product.brand.label("brand"),
            models.Product.product_type.label("product_type"),
            models.Product.price.label("price"),
            models.Product.image_url.label("image_url"),
            models.Category.category_name.label("category_name"),
            models.BookDetail.author.label("book_author"),
            models.BookDetail.publisher.label("book_publisher"),
            models.BookDetail.isbn.label("isbn"),
            models.BookDetail.language.label("language"),
            models.BookDetail.num_pages.label("num_pages"),
            models.BookDetail.edition.label("edition"),
        )
        .outerjoin(models.BookDetail, models.BookDetail.product_id == models.Product.product_id)
        .outerjoin(models.Category, models.Category.category_id == models.Product.category_id)
    )

    if min_price is not None:
        products_query = products_query.filter(models.Product.price >= min_price)
    if max_price is not None:
        products_query = products_query.filter(models.Product.price <= max_price)
    if normalized_types:
        products_query = products_query.filter(models.Product.product_type.in_(normalized_types))
    if normalized_brand:
        products_query = products_query.filter(models.Product.brand.ilike(f"%{normalized_brand}%"))
    if normalized_author:
        products_query = products_query.filter(models.BookDetail.author.ilike(f"%{normalized_author}%"))
    if normalized_publisher:
        products_query = products_query.filter(models.BookDetail.publisher.ilike(f"%{normalized_publisher}%"))

    products = products_query.all()

    if not products:
        return {
            "source": "db",
            "query": q,
            "count": 0,
            "threshold": threshold,
            "sort": {"by": sort_by, "order": sort_order},
            "results": [],
        }

    # Include metadata in candidate text so author/publisher/category terms can match.
    candidates = [
        " ".join(
            part
            for part in [
                p.product_name,
                p.brand,
                p.book_author,
                p.book_publisher,
                p.category_name,
                p.product_type,
            ]
            if part
        )
        for p in products
    ]

    scores = compute_cosine_similarities(query=q, candidates=candidates)

    product_dicts = [
        {
            "id": p.product_id,
            "name": p.product_name,
            "description": p.description,
            "author": p.book_author or p.brand,
            "brand": p.brand,
            "publisher": p.book_publisher,
            "isbn": p.isbn,
            "language": p.language,
            "pages": p.num_pages,
            "edition": p.edition,
            "product_type": p.product_type,
            "category": p.category_name or p.product_type,
            "price": float(p.price) if p.price is not None else None,
            "image_url": p.image_url,
        }
        for p in products
    ]

    ranked_results = rank_by_similarity(scores, product_dicts)
    results = filter_by_threshold(scores, product_dicts, threshold)

    # Always return non-empty results when products exist:
    # if threshold filters everything out, fall back to top ranked matches.
    source = "db"
    if not results:
        results = ranked_results
        source = "db_fallback"

    results = _sort_results(results, sort_by=sort_by, sort_order=sort_order)[:limit]

    cache_set(cache_key, results, ttl_seconds=300)

    if user_id is not None:
        try:
            search_entry = models.SearchHistory(
                user_id=user_id,
                searched_keyword=normalized_q,
                searched_at=datetime.utcnow(),
            )
            db.add(search_entry)
            db.commit()
        except Exception as e:
            print(f"Warning: Could not record search history: {e}")
            db.rollback()

    return {
        "source": source,
        "query": q,
        "count": len(results),
        "threshold": threshold,
        "sort": {"by": sort_by, "order": sort_order},
        "results": results,
    }


@router.get("/filters")
def get_filter_options(db: Session = Depends(get_db)):
    price_bounds = db.query(
        func.min(models.Product.price).label("min_price"),
        func.max(models.Product.price).label("max_price"),
    ).one()

    product_types = [
        row[0]
        for row in db.query(models.Product.product_type)
        .distinct()
        .order_by(models.Product.product_type)
        .all()
        if row[0]
    ]

    authors = [
        row[0]
        for row in db.query(models.BookDetail.author)
        .filter(models.BookDetail.author.isnot(None))
        .distinct()
        .order_by(models.BookDetail.author)
        .limit(100)
        .all()
        if row[0]
    ]

    publishers = [
        row[0]
        for row in db.query(models.BookDetail.publisher)
        .filter(models.BookDetail.publisher.isnot(None))
        .distinct()
        .order_by(models.BookDetail.publisher)
        .limit(100)
        .all()
        if row[0]
    ]

    brands = [
        row[0]
        for row in db.query(models.Product.brand)
        .filter(models.Product.brand.isnot(None))
        .distinct()
        .order_by(models.Product.brand)
        .limit(100)
        .all()
        if row[0]
    ]

    return {
        "product_types": product_types,
        "brands": brands,
        "authors": authors,
        "publishers": publishers,
        "price_range": {
            "min": float(price_bounds.min_price) if price_bounds.min_price is not None else None,
            "max": float(price_bounds.max_price) if price_bounds.max_price is not None else None,
        },
    }


@router.get("/history")
def get_search_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
):
    user_id = _resolve_user_id(db, current_user.get("sub"))

    history = (
        db.query(models.SearchHistory)
        .filter(models.SearchHistory.user_id == user_id)
        .order_by(models.SearchHistory.searched_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "user_id": user_id,
        "count": len(history),
        "searches": [
            {
                "query": h.searched_keyword,
                "timestamp": h.searched_at.isoformat() if h.searched_at else None,
            }
            for h in history
        ],
    }


@router.get("/trending")
def get_trending_searches(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    trending = (
        db.query(
            models.SearchHistory.searched_keyword,
            func.count(models.SearchHistory.search_id).label("count"),
        )
        .group_by(models.SearchHistory.searched_keyword)
        .order_by(func.count(models.SearchHistory.search_id).desc())
        .limit(limit)
        .all()
    )

    return {
        "count": len(trending),
        "trending_searches": [
            {"query": q, "search_count": count}
            for q, count in trending
        ],
    }