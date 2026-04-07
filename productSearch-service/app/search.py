from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import get_db
from .auth import verify_jwt
from .similarity import compute_cosine_similarities, filter_by_threshold, rank_by_similarity
from .cache import cache_get, cache_set
from . import models

router = APIRouter(prefix="/search", tags=["Search"])

SEARCH_CACHE_VERSION = "v2"


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


@router.get("")
def search_products(
    q: str = Query(..., min_length=1, description="Search keyword"),
    threshold: float = Query(0.1, ge=0.0, le=1.0, description="Similarity threshold"),
    limit: int = Query(50, ge=1, le=200, description="Max number of results"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
):
    user_id = _resolve_user_id(db, current_user.get("sub"))

    normalized_q = q.lower().strip()
    cache_key = f"search:{SEARCH_CACHE_VERSION}:{user_id}:{normalized_q}:t{threshold:.3f}"
    cached = cache_get(cache_key)
    if cached is not None:
        return {
            "source": "cache",
            "query": q,
            "count": len(cached[:limit]),
            "threshold": threshold,
            "results": cached[:limit],
        }

    products = db.query(models.Product).all()

    if not products:
        return {
            "source": "db",
            "query": q,
            "count": 0,
            "threshold": threshold,
            "results": [],
        }

    # Use the REAL DB column
    product_names = [p.product_name for p in products]

    scores = compute_cosine_similarities(query=q, candidates=product_names)

    # Keep API response shape unchanged
    product_dicts = [
        {
            "id": p.product_id,
            "name": p.product_name,
            "description": p.description,
            "author": p.brand,           # best available text field in current schema
            "category": p.product_type,  # product_type is the nearest meaningful category-like value
            "price": float(p.price) if p.price is not None else None,
            "image_url": p.image_url,
        }
        for p in products
    ]

    ranked_results = rank_by_similarity(scores, product_dicts)
    results = filter_by_threshold(scores, product_dicts, threshold)[:limit]

    # Always return non-empty results when products exist:
    # if threshold filters everything out, fall back to top ranked matches.
    source = "db"
    if not results:
        results = ranked_results[:limit]
        source = "db_fallback"

    cache_set(cache_key, results, ttl_seconds=300)

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
        "results": results,
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