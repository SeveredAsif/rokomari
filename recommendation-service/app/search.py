"""
routers/search.py
-----------------
Handles the product SEARCH endpoint.

Flow:
  1. User sends a search keyword (e.g. "history of bangladesh")
  2. We fetch ALL product names from the database
  3. We compute cosine similarity between the keyword and every product name
  4. We return products whose similarity score is above the threshold
  5. We save this keyword to search_history for future recommendation use

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

from app.database import get_db
from app.auth import verify_jwt
from app.similarity import compute_cosine_similarities, filter_by_threshold
from app.cache import cache_get, cache_set
from app import models

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
def search_products(
    # Query parameter: GET /search?q=history+of+bangladesh&threshold=0.1
    q: str = Query(..., min_length=1, description="Search keyword"),
    threshold: float = Query(0.1, ge=0.0, le=1.0, description="Similarity threshold"),

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
    """
    user_id = current_user.get("sub")

    # --- Cache check ---
    # Key format: "search:<user_id>:<keyword>"
    # This means each user's search results are cached separately.
    cache_key = f"search:{user_id}:{q.lower().strip()}"
    cached = cache_get(cache_key)
    if cached is not None:
        return {"source": "cache", "results": cached}

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
    results = filter_by_threshold(scores, product_dicts, threshold)

    # --- Save to search_history ---
    # We do this AFTER computing results so a DB write failure doesn't block the response
    try:
        history_entry = models.SearchHistory(user_id=user_id, keyword=q)
        db.add(history_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        # Log but don't fail the whole request just because history save failed
        print(f"⚠️  Could not save search history: {e}")

    # --- Store in cache ---
    cache_set(cache_key, results, ttl_seconds=300)

    return {"source": "db", "query": q, "count": len(results), "results": results}
