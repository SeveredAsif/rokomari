# Rokomari Microservices API Documentation

## Accessing Services from the Frontend

Each backend service runs in its own Docker container and is accessible from the frontend (or any client) via the following host and port mappings:

| Service Name             | Docker Container         | Host URL (for frontend)         |
|-------------------------|-------------------------|---------------------------------|
| Authentication Service  | authentication-service  | http://localhost:8000           |
| Recommendation Service  | recommendation-service  | http://localhost:8001           |
| Product Search Service  | productsearch-service   | http://localhost:8002           |
| Interaction Service     | interaction-service     | http://localhost:8004           |

**How to call from frontend:**

- For local development, use the above URLs directly in your frontend code (e.g., with fetch, axios, etc.).
- Example: To register a user, POST to `http://localhost:8000/auth/register`.
- If deploying to production, update the URLs to match your server's domain/IP and exposed ports.

**Note:**
- If the frontend is running in a different Docker container, use the service name (e.g., `http://authentication-service:8000`) in Docker Compose network.
- For browser-based frontend (React, etc.), use `localhost` and the mapped port as shown above.

This document covers all currently available backend services and endpoints.

## Base URL (via Nginx reverse proxy)

Use `http://localhost:8080` and the service prefixes below.

| Service | Base Path | Example Health URL |
|---|---|---|
| Authentication | `/auth` | `http://localhost:8080/auth/health` |
| Recommendation | `/recommendation` | `http://localhost:8080/recommendation/health` |
| Product Search | `/productsearch` | `http://localhost:8080/productsearch/health` |
| Interaction | `/interaction` | `http://localhost:8080/interaction/health` |

(Direct ports like `:8000`, `:8001` still work for local debugging.)

---

## 1) Authentication Service

Base URL (nginx): `http://localhost:8080/auth`

Base URL (direct): `http://localhost:8000`

### GET /
Checks whether auth service is running.

Example response:
```json
{
  "message": "Authentication service is running"
}
```

### GET /health
Checks service + database connectivity.

Example response:
```json
{
  "status": "ok",
  "service": "authentication-service"
}
```

### POST /auth/register
Registers a new user.

Request body:
```json
{
  "email": "newuser@mail.com",
  "full_name": "New User",
  "phone": "01712345678",
  "password": "StrongPass123"
}
```

Success response (201):
```json
{
  "user_id": 1001,
  "email": "newuser@mail.com",
  "full_name": "New User",
  "phone": "01712345678",
  "created_at": "2026-03-23T13:40:20.000000"
}
```

### POST /auth/login
Authenticates using email + password and returns JWT token.

Request body:
```json
{
  "email": "newuser@mail.com",
  "password": "StrongPass123"
}
```

Success response:
```json
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer"
}
```

### GET /auth/me
Gets logged-in user profile from JWT.

Header:
- Authorization: Bearer \<JWT_TOKEN\>

Success response:
```json
{
  "user_id": 1001,
  "email": "newuser@mail.com",
  "full_name": "New User",
  "phone": "01712345678",
  "created_at": "2026-03-23T13:40:20.000000"
}
```

### GET /auth/recommendation-demo
Demo endpoint showing service-to-service call from auth -> recommendation.

Success response:
```json
{
  "called_service": "recommendation-service",
  "response": {
    "message": "hello from recommendation service",
    "service": "recommendation-service"
  }
}
```

---

## 2) Recommendation Service

Base URL (nginx): `http://localhost:8080/recommendation`

Base URL (direct): `http://localhost:8001`

**Authentication:** All endpoints except `/health`, `/hello`, and `/recommendations/popular`
require a JWT token in the Authorization header:
```
Authorization: Bearer <JWT_TOKEN>
```
Obtain the token from `POST /auth/login` on the Authentication Service.

**Important note on data flow:**
This service only **reads** from `search_history` and `product_visits`.
Writing to those tables is handled by the Interaction Service.
The recommended frontend workflow is:
1. User searches → call `POST /interactions/search` (Interaction Service) to save it
2. Then call `GET /search` (Product Search Service) to get similarity results
3. User visits a product → call `POST /interactions/product-visit` (Interaction Service)
4. Then call `GET /recommendations` to get personalised results

---

### GET /health
Health check.

Example response:
```json
{
  "status": "ok",
  "service": "recommendation-service"
}
```

---

### GET /hello
Simple hello endpoint. Used by the auth service demo.

Example response:
```json
{
  "message": "hello from recommendation service",
  "service": "recommendation-service"
}
```

---

### GET /recommendations
Returns personalised product recommendations for the logged-in user,
combining three signals from their activity history.

**Auth required:** Yes (JWT)

Query parameters:

| Parameter   | Type  | Required | Default | Description                                      |
|-------------|-------|----------|---------|--------------------------------------------------|
| `limit`     | int   | No       | `10`    | Max number of results to return (1 – 50)         |
| `threshold` | float | No       | `0.1`   | Minimum similarity score to include (0.0 – 1.0) |

Example request:
```
GET /recommendations?limit=10&threshold=0.15
Authorization: Bearer <JWT_TOKEN>
```

Success response:
```json
{
  "source": "db",
  "user_id": 1001,
  "count": 5,
  "results": [
    {
      "id": 15,
      "name": "Atomic Habits",
      "description": "...",
      "author": "James Clear",
      "category": "Self-help",
      "price": 500.0,
      "image_url": "...",
      "similarity_score": 0.8821
    }
  ]
}
```

Error responses:
- `401` — Missing or invalid JWT token

**How it works (three signals):**

| Signal | Source table | Logic |
|--------|-------------|-------|
| Search history | `search_history` | Finds products similar to past search keywords |
| Product visits (direct) | `product_visits` | Re-surfaces the exact products the user visited |
| Product visits (similar) | `product_visits` | Finds products similar to visited product names |
| Order history | `orders` | Finds products similar to previously ordered product names |

Results from all signals are merged, deduplicated (highest score wins on duplicates),
sorted by score descending, and trimmed to `limit`.

Cache key: `recommendations:<user_id>`, TTL 5 minutes.

---

### GET /recommendations/popular
Returns the most visited products across all users.

**Auth required:** No

This is the fallback recommendation shown to new users or logged-out visitors
who don't yet have any search history, visits, or orders.

Query parameters:

| Parameter | Type | Required | Default | Description                      |
|-----------|------|----------|---------|----------------------------------|
| `limit`   | int  | No       | `10`    | Max number of results (1 – 50)   |

Example request:
```
GET /recommendations/popular?limit=5
```

Success response:
```json
{
  "source": "db",
  "count": 5,
  "results": [
    {
      "id": 20,
      "name": "Atomic Habits",
      "description": "...",
      "author": "James Clear",
      "category": "Self-help",
      "price": 500.0,
      "image_url": "...",
      "visit_count": 342
    },
    {
      "id": 8,
      "name": "Rich Dad Poor Dad",
      "description": "...",
      "author": "Robert Kiyosaki",
      "category": "Finance",
      "price": 380.0,
      "image_url": "...",
      "visit_count": 289
    }
  ]
}
```

Cache key: `recommendations:popular`, TTL 15 minutes (longer since it changes slowly).

---

## 3) Interaction Service

Base URL: `http://localhost:8002`

This service handles frontend interaction events and writes into:
- product_visits
- search_history
- addresses
- cart
- cart_items
- orders
- order_items
- order_status_history
- payments

### GET /
Checks whether interaction service is running.

Example response:
```json
{
  "message": "Interaction service is running"
}
```

### GET /health
Checks interaction service + DB connectivity.

Example response:
```json
{
  "status": "ok",
  "service": "interaction-service"
}
```

### POST /interactions/product-visit
Stores one product visit.

Request body:
```json
{
  "user_id": 5,
  "product_id": 20
}
```

Success response (201):
```json
{
  "visit_id": 3001,
  "user_id": 5,
  "product_id": 20,
  "visited_at": "2026-03-23T13:50:10.000000"
}
```

### POST /interactions/search
Stores one search history record.

Request body:
```json
{
  "user_id": 5,
  "searched_keyword": "atomic habits"
}
```

Success response (201):
```json
{
  "search_id": 2001,
  "user_id": 5,
  "searched_keyword": "atomic habits",
  "searched_at": "2026-03-23T13:50:30.000000"
}
```

### POST /interactions/address
Stores one address.

Request body:
```json
{
  "user_id": 5,
  "recipient_name": "Asif Rahman",
  "phone": "01711223344",
  "address_line": "House 12, Road 3",
  "city": "Dhaka",
  "area": "Mirpur",
  "postal_code": "1216"
}
```

Success response (201):
```json
{
  "address_id": 1002,
  "user_id": 5,
  "recipient_name": "Asif Rahman",
  "phone": "01711223344",
  "address_line": "House 12, Road 3",
  "city": "Dhaka",
  "area": "Mirpur",
  "postal_code": "1216",
  "created_at": "2026-03-23T13:51:00.000000"
}
```

### POST /interactions/cart/save
Creates or replaces user cart items.

Request body:
```json
{
  "user_id": 5,
  "items": [
    { "product_id": 20, "quantity": 2 },
    { "product_id": 42, "quantity": 1 }
  ]
}
```

Success response:
```json
{
  "message": "Cart saved successfully",
  "user_id": 5,
  "cart_id": 5,
  "items_saved": 2
}
```

### POST /interactions/order
Creates order + order_items + order_status_history + payment in one request.

Request body:
```json
{
  "user_id": 5,
  "address_id": 1002,
  "items": [
    { "product_id": 20, "quantity": 2 },
    { "product_id": 42, "quantity": 1 }
  ],
  "payment_method": "COD",
  "shipping_charge": 50.0,
  "discount_amount": 20.0,
  "order_status": "PENDING"
}
```

Success response (201):
```json
{
  "message": "Order created successfully",
  "order_id": 1001,
  "order_date": "2026-03-23T13:52:10.000000",
  "user_id": 5,
  "total_amount": "1290.00",
  "payment_status": "UNPAID",
  "items_count": 2
}
```

---

## 3) Product Search Service

Base URL (nginx): `http://localhost:8080/productsearch`

Base URL (direct): `http://localhost:8002`

The Product Search Service provides semantic product search capabilities using TF-IDF vectorization and cosine similarity.

### GET /health
Checks service + database connectivity.

Example response:
```json
{
  "status": "ok",
  "service": "productSearch-service"
}
```

### GET /search
Searches for products using semantic similarity on product names.

**Auth required:** Yes (JWT)

Query parameters:

| Parameter   | Type  | Required | Default | Description                                      |
|-------------|-------|----------|---------|--------------------------------------------------|
| `q`         | str   | Yes      | —       | Search keyword (min 1 character)                |
| `threshold` | float | No       | `0.1`   | Minimum similarity score to include (0.0 – 1.0) |
| `limit`     | int   | No       | `50`    | Max number of results to return (1 – 200)       |

Example request:
```
GET /search?q=history+of+bangladesh&threshold=0.2&limit=20
Authorization: Bearer <JWT_TOKEN>
```

Success response (from database):
```json
{
  "source": "db",
  "query": "history of bangladesh",
  "count": 3,
  "threshold": 0.2,
  "results": [
    {
      "id": 12,
      "name": "Bangladesh Liberation War",
      "description": "A comprehensive history...",
      "author": "Dr. Ahmed Hassan",
      "category": "History",
      "price": 350.0,
      "image_url": "...",
      "similarity_score": 0.8214
    },
    {
      "id": 7,
      "name": "History of South Asia",
      "description": "...",
      "author": "Prof. Robert Smith",
      "category": "History",
      "price": 420.0,
      "image_url": "...",
      "similarity_score": 0.6104
    }
  ]
}
```

When result is served from cache:
```json
{
  "source": "cache",
  "results": [ ... ]
}
```

Error responses:
- `401` — Missing or invalid JWT token
- `422` — Missing required `q` parameter or invalid query format

**How it works:**
1. Checks Redis cache first (key: `search:<user_id>:<keyword>`, TTL 5 minutes)
2. On cache miss:
   - Fetches all products from database
   - Computes TF-IDF vectorization of search query and product names
   - Applies cosine similarity to find matching products
   - Filters results below the `threshold`
   - Sorts by similarity score descending
3. Records search in `search_history` table for analytics
4. Caches and returns results

**Similarity scoring:**
- Uses TF-IDF (Term Frequency-Inverse Document Frequency) vectorization
- Considers single words and 2-word phrases (bigrams)
- Ignores common English stopwords (the, a, is, etc.)
- Returns scores from 0.0 (completely different) to 1.0 (identical)

### GET /search/history
Get the current user's search history.

**Auth required:** Yes (JWT)

Query parameters:

| Parameter | Type | Required | Default | Description                      |
|-----------|------|----------|---------|----------------------------------|
| `limit`   | int  | No       | `20`    | Max number of searches to return (1 – 100) |

Example request:
```
GET /search/history?limit=10
Authorization: Bearer <JWT_TOKEN>
```

Success response:
```json
{
  "user_id": 1001,
  "count": 3,
  "searches": [
    {
      "query": "history of bangladesh",
      "timestamp": "2026-03-25T14:30:22.000000"
    },
    {
      "query": "bengali literature",
      "timestamp": "2026-03-25T13:15:45.000000"
    }
  ]
}
```

Error responses:
- `401` — Missing or invalid JWT token

### GET /search/trending
Get the most commonly searched keywords across ALL users (for analytics).

**Auth required:** No

Query parameters:

| Parameter | Type | Required | Default | Description                      |
|-----------|------|----------|---------|----------------------------------|
| `limit`   | int  | No       | `10`    | Max trending searches to return (1 – 50) |

Example request:
```
GET /search/trending?limit=15
```

Success response:
```json
{
  "count": 3,
  "trending_searches": [
    {
      "query": "bengali fiction",
      "search_count": 245
    },
    {
      "query": "history",
      "search_count": 198
    },
    {
      "query": "programming",
      "search_count": 187
    }
  ]
}
```

---

## Error Response Format

Most validation and business errors return:
```json
{
  "detail": "..."
}
```

Common examples:
- 400: invalid input, empty cart/order, invalid payment/order status
- 401: invalid credentials or JWT token
- 404: user/product/address not found
- 503: downstream service unavailable

---

## Suggested Frontend Workflow

1. Register or login from auth service.
2. Save JWT token from `/auth/login`.
3. Use `/auth/me` to verify session.
4. Show popular books on homepage → `GET /recommendations/popular` (no auth needed).
5. User types in search box:
   - Get semantic search results → `GET /search?q=<keyword>` (Product Search Service)
   - Get user's search history → `GET /search/history` (Product Search Service)
6. Show trending searches on homepage → `GET /search/trending` (Product Search Service, no auth needed)
7. User clicks a product:
   - Record the visit → `POST /interactions/product-visit` (Interaction Service)
8. Show personalised recommendations → `GET /recommendations` (Recommendation Service)
9. For user actions (address, cart, order) → call Interaction Service endpoints as before.
