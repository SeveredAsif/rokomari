# Rokomari Microservices API Documentation

## Accessing Services from the Frontend

Each backend service runs in its own Docker container and is accessible from the frontend (or any client) via the following host and port mappings:

| Service Name             | Docker Container         | Host URL (for frontend)         |
|-------------------------|-------------------------|---------------------------------|
| Authentication Service  | authentication-service  | http://localhost:8000           |
| Recommendation Service  | recommendation-service  | http://localhost:8001           |
| Interaction Service     | interaction-service     | http://localhost:8002           |

**How to call from frontend:**

- For local development, use the above URLs directly in your frontend code (e.g., with fetch, axios, etc.).
- Example: To register a user, POST to `http://localhost:8000/auth/register`.
- If deploying to production, update the URLs to match your server's domain/IP and exposed ports.

**Note:**
- If the frontend is running in a different Docker container, use the service name (e.g., `http://authentication-service:8000`) in Docker Compose network.
- For browser-based frontend (React, etc.), use `localhost` and the mapped port as shown above.

This document covers all currently available backend services and endpoints.

## Base URLs (Docker)

- Authentication Service: http://localhost:8000
- Recommendation Service: http://localhost:8001
- Interaction Service: http://localhost:8002

## 1) Authentication Service

Base URL: `http://localhost:8000`

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
- Authorization: Bearer <JWT_TOKEN>

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

## 2) Recommendation Service

Base URL: `http://localhost:8001`

### GET /health
Health check.

Example response:
```json
{
  "status": "ok",
  "service": "recommendation-service"
}
```

### GET /hello
Simple hello endpoint.

Example response:
```json
{
  "message": "hello from recommendation service",
  "service": "recommendation-service"
}
```

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

## Suggested Frontend Workflow

1. Register or login from auth service.
2. Save JWT token from `/auth/login`.
3. Use `/auth/me` to verify session.
4. For user actions, call interaction-service endpoints:
   - product click -> `/interactions/product-visit`
   - search -> `/interactions/search`
   - address save -> `/interactions/address`
   - cart save -> `/interactions/cart/save`
   - place order -> `/interactions/order`
