# Product Search Service

A FastAPI-based microservice for semantic product search using TF-IDF vectorization and cosine similarity.

## Architecture

```
app/
├── main.py              # Entry point, FastAPI app setup
├── database.py          # PostgreSQL connection setup
├── models.py            # SQLAlchemy ORM models
├── auth.py              # JWT verification & service-to-service auth
├── cache.py             # Redis-based caching layer
├── similarity.py        # Cosine similarity computation
└── search.py            # Search API endpoints
```

## Key Features

- **Semantic Search**: Uses TF-IDF vectorization + cosine similarity to match products based on meaning, not just exact keywords
- **Caching**: Redis caching for frequent searches (TTL: 5 minutes)
- **Search History**: Tracks user searches for analytics
- **Trending Analysis**: Provides trending search keywords across all users
- **JWT Authentication**: Protects endpoints with token-based auth

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+psycopg2://username:password@postgres:5432/rokomari

# JWT Secret (same as auth service)
JWT_SECRET=your-secret-key-here

# Inter-service authentication
SERVICE_TO_SERVICE_TOKEN=internal-service-token

# Redis (optional, for caching)
REDIS_URL=redis://redis:6379/0
```

## API Endpoints

### 1. Search Products
```
GET /search?q=history+of+bangladesh&threshold=0.1&limit=50
Authorization: Bearer <JWT_TOKEN>
```

Returns products matching the semantic query with similarity scores.

### 2. Search History
```
GET /search/history?limit=20
Authorization: Bearer <JWT_TOKEN>
```

Returns the current user's search history.

### 3. Trending Searches
```
GET /search/trending?limit=10
```

Returns most popular search keywords (no auth required).

### 4. Health Check
```
GET /health
```

Returns service health status.

## Database Models

### Product
Stores product information (read-only from this service).
- `id`: Primary key
- `name`: Product name (used for similarity matching)
- `description`: Product description
- `author`: Author/publisher
- `category`: Product category
- `price`: Product price
- `image_url`: Product image URL

### SearchHistory
Stores all user searches for analytics.
- `id`: Primary key
- `user_id`: Foreign key to users table
- `query`: The search keyword
- `timestamp`: When the search occurred

### User
Stores user information (read-only from this service).
- `id`: Primary key
- `username`: Username
- `email`: User email

## How Search Works

1. **Cache Check**: Check Redis for cached results (key: `search:<user_id>:<keyword>`)
2. **Database Fetch**: If cache miss, fetch all products from PostgreSQL
3. **Vectorization**: Convert query and product names to TF-IDF vectors
4. **Similarity**: Compute cosine similarity between query and each product
5. **Filter**: Keep only results >= threshold, sort by score descending
6. **Cache**: Store results in Redis for 5 minutes
7. **History**: Record search in search_history table

## Similarity Algorithm

- **Vectorizer**: TF-IDF (Term Frequency-Inverse Document Frequency)
- **Stopwords**: Removes common English words (the, a, is, etc.)
- **N-grams**: Considers both single words and 2-word phrases
- **Metric**: Cosine similarity (0 = different, 1 = identical)

Example:
```
Query: "history of bangladesh"
Product 1: "Bangladesh Liberation War" → similarity: 0.82
Product 2: "Cooking Recipes" → similarity: 0.05
Product 3: "History of South Asia" → similarity: 0.61
```

## Docker Setup

Build:
```bash
docker build -t rokomari-productsearch-service .
```

Run:
```bash
docker run -e DATABASE_URL="..." -e JWT_SECRET="..." -p 8002:8002 rokomari-productsearch-service
```

## Development

Install dependencies:
```bash
pip install -r requirements.txt
```

Run locally:
```bash
uvicorn app.main:app --reload --port 8002
```

Test the service:
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8002/search?q=history&threshold=0.1"
```

## Performance Notes

- **Vectorization**: Computed on every search (no caching of vectors)
- **Database**: All products fetched each time (consider pagination for large catalogs)
- **Cache**: Results cached for 5 minutes to speed up repeated searches
- **Similarity**: O(n*m) where n = products, m = features

For production with 100K+ products:
- Consider PostgreSQL full-text search as a pre-filter
- Cache the TF-IDF vectorizer itself
- Use approximate nearest neighbors (ANN) for faster similarity

## Related Services

- **Authentication Service** (port 8000): JWT token generation
- **Recommendation Service** (port 8001): Personalized recommendations
- **Interaction Service** (port 8004): Track user interactions

## File Structure Correspondence

This service follows the same structure as the recommendation service:
- Both use FastAPI + SQLAlchemy + Redis
- Both have auth.py, cache.py, database.py patterns
- Both compute similarity for ranking results
- Both expose router patterns for modular endpoints
