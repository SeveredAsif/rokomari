"""
routers/recommendations.py
---------------------------
The core recommendation engine. Combines THREE signals to build a recommendation list:

  Signal 1 — Search history similarity
    "You searched for 'history books' before → here are products similar to that"

  Signal 2 — Product visits (direct + similarity)
    "You visited this book → here's that book again + similar ones"

  Signal 3 — Order history similarity
    "You ordered this book → here are similar books you might also like"

Each signal produces a list of products with similarity scores. We merge and
deduplicate them at the end, then return the top N results.

This is a common pattern called "candidate generation + ranking" in recommendation systems.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import verify_jwt
from app.similarity import compute_cosine_similarities, filter_by_threshold
from app.cache import cache_get, cache_set
from app import models

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# How many results to return per signal, and in total
SIGNAL_LIMIT = 20    # fetch up to 20 candidates per signal before similarity
FINAL_LIMIT  = 10    # return top 10 merged recommendations


def _resolve_user_id(db: Session, principal: str | int | None) -> int:
    """
    JWT 'sub' may contain either numeric user_id or user email.
    Convert it to integer user_id for table filters.
    """
    if principal is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if isinstance(principal, int):
        return principal

    as_text = str(principal).strip()
    if as_text.isdigit():
        return int(as_text)

    user = (
        db.query(models.User)
        .filter(models.User.email == as_text)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.user_id


def _all_products_as_dicts(db: Session) -> list[dict]:
    """Helper: fetch all products and return as list of dicts."""
    products = db.query(models.Product).all()
    return [
        {
            "id":          p.product_id,
            "name":        p.product_name,
            "description": p.description,
            "author":      None,
            "category":    None,
            "price":       float(p.price) if p.price is not None else None,
            "image_url":   p.image_url,
        }
        for p in products
    ]


def _merge_results(*result_lists) -> list[dict]:
    """
    Merge multiple result lists, keeping the HIGHEST similarity score
    when the same product appears in more than one list.
    Returns deduplicated results sorted by score descending.
    """
    seen: dict[int, dict] = {}   # product_id → best result dict

    for result_list in result_lists:
        for item in result_list:
            pid = item["id"]
            if pid not in seen or item["similarity_score"] > seen[pid]["similarity_score"]:
                seen[pid] = item

    merged = list(seen.values())
    merged.sort(key=lambda x: x["similarity_score"], reverse=True)
    return merged


@router.get("")
def get_recommendations(
    limit: int = Query(FINAL_LIMIT, ge=1, le=50),
    threshold: float = Query(0.1, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
):
    """
    Returns personalised book recommendations for the logged-in user.
    Combines search history, product visits, and order history signals.

    GET /recommendations?limit=10&threshold=0.1
    """
    user_id = _resolve_user_id(db, current_user.get("sub"))

    # --- Cache check ---
    cache_key = f"recommendations:{user_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return {"source": "cache", "results": cached[:limit]}

    # Fetch all products once — used by all three signals
    all_products = _all_products_as_dicts(db)
    if not all_products:
        return {"source": "db", "results": []}
    all_names = [p["name"] for p in all_products]

    # =========================================================
    # Signal 1: Search history
    # =========================================================
    # Fetch the user's most recent N search keywords
    recent_searches = (
        db.query(models.SearchHistory)
        .filter(models.SearchHistory.user_id == user_id)
        .order_by(models.SearchHistory.searched_at.desc())
        .limit(SIGNAL_LIMIT)
        .all()
    )

    search_results: list[dict] = []
    for search in recent_searches:
        scores = compute_cosine_similarities(search.searched_keyword, all_names)
        hits   = filter_by_threshold(scores, all_products, threshold)
        search_results.extend(hits)

    # =========================================================
    # Signal 2: Product visits
    # =========================================================
    # i. The exact visited products themselves
    # ii. Products similar to visited product names
    visited = (
        db.query(models.ProductVisit)
        .filter(models.ProductVisit.user_id == user_id)
        .order_by(models.ProductVisit.visited_at.desc())
        .limit(SIGNAL_LIMIT)
        .all()
    )

    visited_ids = {v.product_id for v in visited}

    # i. Direct: include visited products themselves (with score 1.0 — exact match)
    direct_visits = [
        {**p, "similarity_score": 1.0}
        for p in all_products
        if p["id"] in visited_ids
    ]

    # ii. Similarity: use visited product names as queries
    visit_similarity_results: list[dict] = []
    for product in all_products:
        if product["id"] in visited_ids:
            scores = compute_cosine_similarities(product["name"], all_names)
            hits   = filter_by_threshold(scores, all_products, threshold)
            # Exclude the product itself from its own recommendations
            hits   = [h for h in hits if h["id"] != product["id"]]
            visit_similarity_results.extend(hits)

    # =========================================================
    # Signal 3: Order history
    # =========================================================
    ordered_items = (
        db.query(models.OrderItem.product_id)
        .join(models.Order, models.Order.order_id == models.OrderItem.order_id)
        .filter(models.Order.user_id == user_id)
        .order_by(models.Order.order_date.desc())
        .limit(SIGNAL_LIMIT)
        .all()
    )

    ordered_ids = {row.product_id for row in ordered_items}

    order_results: list[dict] = []
    for product in all_products:
        if product["id"] in ordered_ids:
            scores = compute_cosine_similarities(product["name"], all_names)
            hits   = filter_by_threshold(scores, all_products, threshold)
            hits   = [h for h in hits if h["id"] != product["id"]]
            order_results.extend(hits)

    # =========================================================
    # Merge all signals and return top N
    # =========================================================
    merged = _merge_results(
        search_results,
        direct_visits,
        visit_similarity_results,
        order_results,
    )

    final = merged[:limit]

    # Cache for 5 minutes
    cache_set(cache_key, merged, ttl_seconds=300)

    return {
        "source": "db",
        "user_id": user_id,
        "count": len(final),
        "results": final,
    }


@router.get("/popular")
def get_popular_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Returns the most visited products across ALL users.
    This is the fallback recommendation for new/anonymous users
    who don't have search history, visits, or orders yet.

    No auth required — anyone can see popular items.
    This is your "cached items to show the customer" from the requirements.

    GET /recommendations/popular
    """
    cache_key = "recommendations:popular"
    cached = cache_get(cache_key)
    if cached is not None:
        return {"source": "cache", "results": cached[:limit]}

    # Count product_visits per product_id, order by count descending
    # This is like:  SELECT product_id, COUNT(*) as visits FROM product_visits GROUP BY product_id ORDER BY visits DESC
    popular_rows = (
        db.query(
            models.ProductVisit.product_id,
            func.count(models.ProductVisit.visit_id).label("visit_count")
        )
        .group_by(models.ProductVisit.product_id)
        .order_by(func.count(models.ProductVisit.visit_id).desc())
        .limit(limit)
        .all()
    )

    popular_ids = [row.product_id for row in popular_rows]
    visit_counts = {row.product_id: row.visit_count for row in popular_rows}

    # Fetch full product details for those IDs
    products = (
        db.query(models.Product)
        .filter(models.Product.product_id.in_(popular_ids))
        .all()
    )

    results = [
        {
            "id":          p.product_id,
            "name":        p.product_name,
            "description": p.description,
            "author":      None,
            "category":    None,
            "price":       float(p.price) if p.price is not None else None,
            "image_url":   p.image_url,
            "visit_count": visit_counts.get(p.product_id, 0),
        }
        for p in products
    ]

    # Sort to preserve original order (DB IN clause doesn't guarantee order)
    results.sort(key=lambda x: x["visit_count"], reverse=True)

    # Cache popular for longer — it changes slowly (15 minutes)
    cache_set(cache_key, results, ttl_seconds=900)

    return {"source": "db", "count": len(results), "results": results}
