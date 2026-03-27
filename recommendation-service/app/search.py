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

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

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
    product_names = [p.product_name for p in products]

    # --- Compute cosine similarity ---
    scores = compute_cosine_similarities(query=q, candidates=product_names) #what is in product db and what i searched

    # Build list of dicts so filter_by_threshold can attach similarity_score
    product_dicts = [
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

    # --- Filter and sort ---
    results = filter_by_threshold(scores, product_dicts, threshold)

    # --- Store in cache ---
    #cache_key is the query and user
    cache_set(cache_key, results, ttl_seconds=300) #in redis, save it. where do we use this cache? 

    return {"source": "db", "query": q, "count": len(results), "results": results}
