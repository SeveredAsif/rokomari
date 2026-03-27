"""
search.py
---------
Handles the product SEARCH endpoint.

Flow:
  1. User sends a search keyword (e.g. "history of bangladesh")
  2. We fetch ALL product names from the database
  3. We compute cosine similarity between the keyword and every product name
  4. We return products whose similarity score is above the threshold
  5. We save this keyword to search_history for future analysis

Node.js analogy for routers:
-----------------------------
In Express you'd have a separate router file:
    const router = express.Router()
    router.get('/search', async (req, res) => { ... })
    module.exports = router

    // In app.js:
    app.use('/api', router)

In FastAPI it works identically:
    router = APIRouter()
    @router.get('/search')
    def search(): ...

    # In main.py:
    app.include_router(router, prefix="/api")
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from .database import get_db
from .auth import verify_jwt
from .similarity import compute_cosine_similarities, filter_by_threshold
from .cache import cache_get, cache_set
from . import models

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
def search_products(
    # Query parameter: GET /search?q=history+of+bangladesh&threshold=0.1
    q: str = Query(..., min_length=1, description="Search keyword"),
    threshold: float = Query(0.1, ge=0.0, le=1.0, description="Similarity threshold"),
    limit: int = Query(50, ge=1, le=200, description="Max number of results"),

    # These are injected by FastAPI automatically before the function runs
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
):
    """
    Search for products using cosine similarity on product names.

    - Checks the cache first (fast path)
    - On cache miss: fetches all products, computes similarity, filters by threshold
    - Saves the keyword to search_history
    - Caches the result for 5 minutes

    Query Parameters:
        q (required): search keyword
        threshold: similarity threshold (0.0 to 1.0), default 0.1
        limit: max results to return, default 50

    Example:
        GET /search?q=history+of+bangladesh&threshold=0.2&limit=20
    """
    user_id = current_user.get("sub")

    # --- Cache check ---
    # Key format: "search:<user_id>:<keyword>"
    # This means each user's search results are cached separately.
    cache_key = f"search:{user_id}:{q.lower().strip()}"
    cached = cache_get(cache_key)
    if cached is not None:
        return {"source": "cache", "results": cached[:limit]}

    # --- Fetch all products from DB ---
    # TODO: For large product tables, consider only fetching a filtered subset
    #       (e.g. products matching the first word of q) before running similarity.
    products = db.query(models.Product).all()

    if not products:
        return {"source": "db", "results": []}

    # Extract just the names to feed into cosine similarity
    product_names = [p.name for p in products]

    # --- Compute cosine similarity ---
    scores = compute_cosine_similarities(query=q, candidates=product_names)

    # Build list of dicts so filter_by_threshold can attach similarity_score
    product_dicts = [
        {
            "id":          p.id,
            "name":        p.name,
            "description": p.description,
            "author":      p.author,
            "category":    p.category,
            "price":       p.price,
            "image_url":   p.image_url,
        }
        for p in products
    ]

    # --- Filter and sort ---
    results = filter_by_threshold(scores, product_dicts, threshold)[:limit]

    # --- Store in cache ---
    cache_set(cache_key, results, ttl_seconds=300)

    # --- Record search in search_history ---
    # This tracks what users search for, which can be analyzed for:
    #   - Trending keywords
    #   - User behavior analysis
    #   - Future recommendation signals
    try:
        search_entry = models.SearchHistory(
            user_id=user_id,
            query=q.lower().strip(),
            timestamp=datetime.utcnow()
        )
        db.add(search_entry)
        db.commit()
    except Exception as e:
        # Log but don't fail the search if history recording fails
        print(f"Warning: Could not record search history: {e}")
        db.rollback()

    return {
        "source": "db",
        "query": q,
        "count": len(results),
        "threshold": threshold,
        "results": results
    }


@router.get("/history")
def get_search_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt),
):
    """
    Get the user's search history.

    Returns the most recent searches (default 20, max 100).

    Example:
        GET /search/history?limit=10
    """
    user_id = current_user.get("sub")

    history = db.query(models.SearchHistory).filter(
        models.SearchHistory.user_id == user_id
    ).order_by(
        models.SearchHistory.timestamp.desc()
    ).limit(limit).all()

    return {
        "user_id": user_id,
        "count": len(history),
        "searches": [
            {
                "query": h.query,
                "timestamp": h.timestamp.isoformat() if h.timestamp else None
            }
            for h in history
        ]
    }


@router.get("/trending")
def get_trending_searches(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Get the most commonly searched keywords (trending searches).

    Returns aggregated data across ALL users — useful for analytics.

    Example:
        GET /search/trending?limit=15
    """
    # Query the database to count how many times each query appears
    trending = db.query(
        models.SearchHistory.query,
        db.func.count(models.SearchHistory.id).label("count")
    ).group_by(
        models.SearchHistory.query
    ).order_by(
        db.func.count(models.SearchHistory.id).desc()
    ).limit(limit).all()

    return {
        "count": len(trending),
        "trending_searches": [
            {"query": q, "search_count": count}
            for q, count in trending
        ]
    }
