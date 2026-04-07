# Rokomari Microservices API Documentation

This document explains every HTTP endpoint currently implemented in the repo, plus:
1) how to call services **from other backend services** (inside Docker)
2) how to call services **from a browser / frontend**
3) what nginx is doing (at the end)

---

## How to Call APIs

### A) Calling from another backend service (service-to-service)

Use Docker Compose service DNS names and the container ports:

| Service | DNS name (Docker) | Port | Example base URL |
|---|---:|---:|---|
| Authentication | `authentication-service` | 8000 | `http://authentication-service:8000` |
| Recommendation | `recommendation-service` | 8001 | `http://recommendation-service:8001` |
| Product Search | `productsearch-service` | 8002 | `http://productsearch-service:8002` |
| Interaction | `interaction-service` | 8002 | `http://interaction-service:8002` |

Important: when calling services directly like this, **do NOT include** the external prefixes (`/auth`, `/recommendation`, ...).
Example:
- correct: `http://authentication-service:8000/login`
- wrong: `http://authentication-service:8000/auth/login`

### B) Calling from a browser / frontend

Use nginx on port 80 (Compose maps `80:80`):

Base URL: `http://localhost`

| Service | External prefix | Example |
|---|---|---|
| Authentication | `/auth` | `http://localhost/auth/health` |
| Recommendation | `/recommendation` | `http://localhost/recommendation/health` |
| Product Search | `/productsearch` | `http://localhost/productsearch/health` |
| Interaction | `/interaction` | `http://localhost/interaction/health` |

If your frontend is the Vite dev server in Docker, calling relative paths like `fetch('/auth/login')` works because Vite proxies those paths to nginx.

For local debugging you can also call services directly by port from the browser, but then you must omit the external prefixes:
- Auth: `http://localhost:8000/login`, `http://localhost:8000/register`, ...
- Recommendation: `http://localhost:8001/recommendations`, ...
- Product Search: `http://localhost:8002/search`, ...
- Interaction: `http://localhost:8004/product-visit`, ...

---

## Authentication (JWT)

Protected endpoints require:
`Authorization: Bearer <JWT_TOKEN>`

JWT `sub` is the user email, and services resolve it to `user_id` internally when needed.

---

## Authentication Service

External (browser) base: `http://localhost/auth`

Internal (service-to-service) base: `http://authentication-service:8000`

Docs:
- External: `http://localhost/auth/docs`
- Internal: `http://authentication-service:8000/docs`

Endpoints:

### GET /
Returns a simple “service is running” message.

### GET /health
Checks service + DB connectivity.

### POST /register
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

Responses:
- `201` Created → returns user profile
- `409` Conflict → `{"detail":"Email already registered"}` or `{"detail":"Phone already registered"}`

### POST /login
Authenticates and returns a JWT.

Request body:
```json
{
  "email": "newuser@mail.com",
  "password": "StrongPass123"
}
```

Success:
```json
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer"
}
```

### GET /me
Returns the current user profile from the JWT.

Header:
`Authorization: Bearer <JWT_TOKEN>`

### GET /recommendation-demo
Demo call from auth → recommendation.

---

## Recommendation Service

External (browser) base: `http://localhost/recommendation`

Internal (service-to-service) base: `http://recommendation-service:8001`

Docs:
- External: `http://localhost/recommendation/docs`
- Internal: `http://recommendation-service:8001/docs`

Endpoints:

### GET /health
Health check.

### GET /hello
Hello endpoint.

### GET /recommendations
Returns personalised recommendations for the logged-in user.

Auth: required

Query params:
- `limit` (int, 1–50, default 10)
- `threshold` (float, 0.0–1.0, default 0.1)

### GET /recommendations/popular
Returns the most visited products across all users.

Auth: not required

Query params:
- `limit` (int, 1–50, default 10)

---

## Product Search Service

External (browser) base: `http://localhost/productsearch`

Internal (service-to-service) base: `http://productsearch-service:8002`

Docs:
- External: `http://localhost/productsearch/docs`
- Internal: `http://productsearch-service:8002/docs`

Endpoints:

### GET /
Root “service is running” message.

### GET /health
Health check.

### GET /hello
Hello endpoint.

### GET /search
Semantic search for products.

Auth: required

Query params:
- `q` (string, required)
- `threshold` (float, 0.0–1.0, default 0.1)
- `limit` (int, 1–200, default 50)

### GET /search/history
Returns the current user’s search history.

Auth: required

Query params:
- `limit` (int, 1–100, default 20)

### GET /search/trending
Returns the most common search keywords across all users.

Auth: not required

Query params:
- `limit` (int, 1–50, default 10)

---

## Interaction Service

External (browser) base: `http://localhost/interaction`

Internal (service-to-service) base: `http://interaction-service:8002`

Docs:
- External: `http://localhost/interaction/docs`
- Internal: `http://interaction-service:8002/docs`

Endpoints:

### GET /
Root “service is running” message.

### GET /health
Health check.

### POST /product-visit
Records a product visit.

Request body:
```json
{ "user_id": 5, "product_id": 20 }
```

Legacy alias (still supported): `POST /interactions/product-visit`

### POST /search
Records a user search keyword.

Request body:
```json
{ "user_id": 5, "searched_keyword": "atomic habits" }
```

Legacy alias (still supported): `POST /interactions/search`

### POST /address
Creates an address for a user.

Legacy alias (still supported): `POST /interactions/address`

### POST /cart/save
Creates or replaces a user’s cart items.

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

Legacy alias (still supported): `POST /interactions/cart/save`

### POST /order
Creates an order + order items + order status + payment.

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

Legacy alias (still supported): `POST /interactions/order`

### Analytics Endpoints (NEW)

All analytics endpoints are read-only and return JSON statistics.

#### GET /stats
Overall interaction statistics across all users.

Response:
```json
{
  "total_product_visits": 3017,
  "total_unique_visitors": 3,
  "total_searches": 2019,
  "total_unique_searchers": 3,
  "avg_visits_per_user": 1005.67,
  "avg_searches_per_user": 673.0,
  "timestamp": "2026-04-07T10:58:33.920533"
}
```

#### GET /stats/user/{user_id}
Get interaction statistics for a specific user.

Parameters:
- `user_id` (path): User ID to analyze

Response includes: total visits, unique products, total searches, unique keywords, last visit/search timestamps.

#### GET /stats/products/most-visited?limit=10
Get the most visited products.

Query parameters:
- `limit` (optional): Number of results (default: 10, max: 100)

Returns list of products with visit counts and unique visitor counts.

#### GET /stats/searches/most-searched?limit=10
Get the most searched keywords.

Query parameters:
- `limit` (optional): Number of results (default: 10, max: 100)

Returns list of keywords with search counts and unique searcher counts.

#### GET /stats/active-users?time_window_hours=24
Get active users in a time window.

Query parameters:
- `time_window_hours` (optional): Hours to look back (default: 24, max: 720)

Returns counts of total active users, active visitors, and active searchers.

#### GET /stats/top-visitors?limit=10
Get users with the most product visits.

Query parameters:
- `limit` (optional): Number of results (default: 10, max: 100)

Returns list of users with visit counts, unique products, and last visit times.

#### GET /stats/top-searchers?limit=10
Get users with the most searches.

Query parameters:
- `limit` (optional): Number of results (default: 10, max: 100)

Returns list of users with search counts, unique keywords, and last search times.

#### GET /stats/interaction-trends?days=7
Get daily interaction trends.

Query parameters:
- `days` (optional): Number of days to analyze (default: 7, max: 90)

Returns daily breakdown of visits, searches, and unique users by date.

**For detailed analytics documentation, see [INTERACTION_ANALYTICS.md](./INTERACTION_ANALYTICS.md)**

---

## Error Response Format

Most errors are returned as:
```json
{ "detail": "..." }
```

---

## What nginx Is Doing (routing explanation)

nginx is the public entrypoint (port 80). It routes by URL prefix:

- `/auth/*` → `authentication-service:8000/*`
- `/recommendation/*` → `recommendation-service:8001/*`
- `/productsearch/*` → `productsearch-service:8002/*`
- `/interaction/*` → `interaction-service:8002/*`
- `/` → `frontend:3000`

Key detail: each `proxy_pass` uses a trailing slash (example: `proxy_pass http://auth_service/;`).
That trailing slash makes nginx *strip the matching prefix* before forwarding.

Example:
- Browser calls: `GET /auth/login`
- nginx forwards to auth service as: `GET /login`

This is why frontend calls should consistently use the external prefixes (`/auth`, `/productsearch`, ...), while service-to-service calls should hit the services directly **without** those prefixes.
