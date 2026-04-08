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
from sqlalchemy import func, text

from app.database import get_db
from app.auth import verify_jwt
from app.similarity import compute_cosine_similarities, filter_by_threshold
from app.cache import cache_get, cache_set
from app import models

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# How many results to return per signal, and in total
SIGNAL_LIMIT = 20    # fetch up to 20 candidates per signal before similarity
FINAL_LIMIT  = 10    # return top 10 merged recommendations

# Personalized ranking weights from user-only behavior signals.
PERSONALIZED_VISIT_SIGNAL_WEIGHT = 2.20
PERSONALIZED_SEARCH_SIGNAL_WEIGHT = 3.60


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
            "author":      p.brand,
            "category":    p.product_type,
            "product_type": p.product_type,
            "price":       float(p.price) if p.price is not None else None,
            "image_url":   p.image_url,
        }
        for p in products
    ]


def _global_visit_counts(db: Session) -> dict[int, int]:
    rows = (
        db.query(
            models.ProductVisit.product_id,
            func.count(models.ProductVisit.visit_id).label("visit_count"),
        )
        .group_by(models.ProductVisit.product_id)
        .all()
    )
    return {row.product_id: int(row.visit_count) for row in rows}


def _user_visit_counts(db: Session, user_id: int) -> dict[int, int]:
    rows = (
        db.query(
            models.ProductVisit.product_id,
            func.count(models.ProductVisit.visit_id).label("visit_count"),
        )
        .filter(models.ProductVisit.user_id == user_id)
        .group_by(models.ProductVisit.product_id)
        .all()
    )
    return {row.product_id: int(row.visit_count) for row in rows}


def _search_match_counts(db: Session, user_id: int | None = None) -> dict[int, int]:
    user_filter = "WHERE sh.user_id = :user_id" if user_id is not None else ""
    params = {"user_id": user_id} if user_id is not None else {}

    rows = db.execute(
        text(
            f"""
            SELECT p.product_id, COUNT(sh.search_id) AS search_count
            FROM products p
            JOIN search_history sh
              ON (
                LOWER(p.product_name) LIKE ('%' || LOWER(TRIM(sh.searched_keyword)) || '%')
                OR LOWER(COALESCE(p.brand, '')) LIKE ('%' || LOWER(TRIM(sh.searched_keyword)) || '%')
                OR LOWER(p.product_type) = LOWER(TRIM(sh.searched_keyword))
              )
            {user_filter}
            GROUP BY p.product_id
            """
        ),
        params,
    ).fetchall()

    return {row.product_id: int(row.search_count) for row in rows}


def _user_signal_fingerprint(db: Session, user_id: int) -> str:
    visit_stats = db.execute(
        text(
            """
            SELECT
                COALESCE(EXTRACT(EPOCH FROM MAX(visited_at))::BIGINT, 0) AS max_ts,
                COUNT(*) AS total_count
            FROM product_visits
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).fetchone()

    search_stats = db.execute(
        text(
            """
            SELECT
                COALESCE(EXTRACT(EPOCH FROM MAX(searched_at))::BIGINT, 0) AS max_ts,
                COUNT(*) AS total_count
            FROM search_history
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).fetchone()

    visit_part = f"v{int(visit_stats.max_ts)}-{int(visit_stats.total_count)}"
    search_part = f"s{int(search_stats.max_ts)}-{int(search_stats.total_count)}"
    return f"{visit_part}:{search_part}"


def _user_preference_type_scores(db: Session, user_id: int) -> dict[str, float]:
    visit_type_rows = (
        db.query(
            models.Product.product_type,
            func.count(models.ProductVisit.visit_id).label("visit_count"),
        )
        .join(models.ProductVisit, models.ProductVisit.product_id == models.Product.product_id)
        .filter(models.ProductVisit.user_id == user_id)
        .group_by(models.Product.product_type)
        .all()
    )

    search_type_rows = db.execute(
        text(
            """
            SELECT p.product_type, COUNT(sh.search_id) AS search_count
            FROM products p
            JOIN search_history sh
              ON (
                LOWER(p.product_name) LIKE ('%' || LOWER(TRIM(sh.searched_keyword)) || '%')
                OR LOWER(COALESCE(p.brand, '')) LIKE ('%' || LOWER(TRIM(sh.searched_keyword)) || '%')
                OR LOWER(p.product_type) = LOWER(TRIM(sh.searched_keyword))
              )
            WHERE sh.user_id = :user_id
            GROUP BY p.product_type
            """
        ),
        {"user_id": user_id},
    ).fetchall()

    type_scores: dict[str, float] = {}

    for row in visit_type_rows:
        type_scores[row.product_type] = type_scores.get(row.product_type, 0.0) + (2.0 * float(row.visit_count))

    for row in search_type_rows:
        type_scores[row.product_type] = type_scores.get(row.product_type, 0.0) + (3.0 * float(row.search_count))

    return type_scores


def _product_dict(p: models.Product) -> dict:
    return {
        "id": p.product_id,
        "name": p.product_name,
        "description": p.description,
        "author": p.brand,
        "category": p.product_type,
        "product_type": p.product_type,
        "price": float(p.price) if p.price is not None else None,
        "image_url": p.image_url,
    }


def _build_popularity_results(
    db: Session,
    product_ids: set[int],
    visit_counts: dict[int, int],
    search_counts: dict[int, int],
    type_boosts: dict[str, float] | None = None,
    global_visit_weight: float = 1.0,
    global_search_weight: float = 0.7,
    user_visit_counts: dict[int, int] | None = None,
    user_search_counts: dict[int, int] | None = None,
    user_visit_weight: float = 0.0,
    user_search_weight: float = 0.0,
) -> list[dict]:
    if not product_ids:
        return []

    products = (
        db.query(models.Product)
        .filter(models.Product.product_id.in_(list(product_ids)))
        .all()
    )

    results: list[dict] = []
    for product in products:
        visit_count = visit_counts.get(product.product_id, 0)
        search_count = search_counts.get(product.product_id, 0)
        user_visit_count = (user_visit_counts or {}).get(product.product_id, 0)
        user_search_count = (user_search_counts or {}).get(product.product_id, 0)
        type_boost = (type_boosts or {}).get(product.product_type, 0.0)

        popularity_score = (
            (global_visit_weight * visit_count)
            + (global_search_weight * search_count)
            + (user_visit_weight * user_visit_count)
            + (user_search_weight * user_search_count)
            + type_boost
        )
        if popularity_score <= 0:
            continue

        item = _product_dict(product)
        item.update(
            {
                "visit_count": visit_count,
                "search_count": search_count,
                "user_visit_count": user_visit_count,
                "user_search_count": user_search_count,
                "popularity_score": round(popularity_score, 3),
            }
        )
        results.append(item)

    results.sort(
        key=lambda x: (
            x["popularity_score"],
            x["visit_count"],
            x["search_count"],
        ),
        reverse=True,
    )
    return results


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


def _signal_counts_fingerprint(user_visit_counts: dict[int, int], user_search_counts: dict[int, int]) -> str:
    visit_total = sum(user_visit_counts.values())
    search_total = sum(user_search_counts.values())
    return f"v{visit_total}-{len(user_visit_counts)}:s{search_total}-{len(user_search_counts)}"


def _top_preferred_types_from_results(results: list[dict], top_n: int = 2) -> list[str]:
    type_scores: dict[str, float] = {}
    for item in results:
        product_type = item.get("product_type")
        if not product_type:
            continue
        type_scores[product_type] = type_scores.get(product_type, 0.0) + float(item.get("popularity_score", 0.0))

    sorted_types = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
    return [ptype for ptype, _ in sorted_types[:top_n]]


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
    cache_key = "recommendations:popular:v2"
    cached = cache_get(cache_key)
    if cached is not None:
        final = cached[:limit]
        return {"source": "cache", "count": len(final), "results": final}

    visit_counts = _global_visit_counts(db)
    search_counts = _search_match_counts(db)
    candidate_ids = set(visit_counts.keys()) | set(search_counts.keys())
    results = _build_popularity_results(
        db=db,
        product_ids=candidate_ids,
        visit_counts=visit_counts,
        search_counts=search_counts,
    )

    # Cache popular for longer — it changes slowly (15 minutes)
    cache_set(cache_key, results, ttl_seconds=900)

    final = results[:limit]
    return {"source": "db", "count": len(final), "results": final}


@router.get("/personalized")
def get_personalized_popular_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
):
    """
    Personalized recommendations based on the product TYPES
    that this user mostly searched and visited.
    """
    user_id = _resolve_user_id(db, current_user.get("sub"))

    # User-only personalization signals (no global popularity blending).
    user_visit_counts = _user_visit_counts(db, user_id)
    user_search_counts = _search_match_counts(db, user_id=user_id)

    signal_fingerprint = _signal_counts_fingerprint(user_visit_counts, user_search_counts)
    cache_key = f"recommendations:personalized-type:{user_id}:{signal_fingerprint}"
    cached = cache_get(cache_key)
    if cached is not None:
        return {
            "source": "cache",
            "user_id": user_id,
            "preferred_types": cached.get("preferred_types", []),
            "results": cached.get("results", [])[:limit],
            "count": len(cached.get("results", [])[:limit]),
        }

    candidate_ids = set(user_visit_counts.keys()) | set(user_search_counts.keys())
    if candidate_ids:
        results = _build_popularity_results(
            db=db,
            product_ids=candidate_ids,
            visit_counts=user_visit_counts,
            search_counts=user_search_counts,
            global_visit_weight=PERSONALIZED_VISIT_SIGNAL_WEIGHT,
            global_search_weight=PERSONALIZED_SEARCH_SIGNAL_WEIGHT,
        )
    else:
        results = []

    preferred_types = _top_preferred_types_from_results(results)

    payload = {
        "preferred_types": preferred_types,
        "results": results,
    }
    cache_set(cache_key, payload, ttl_seconds=300)

    final = results[:limit]
    return {
        "source": "db",
        "user_id": user_id,
        "preferred_types": preferred_types,
        "count": len(final),
        "results": final,
    }
