"""
auth.py
-------
Two types of authentication this service needs to handle:

1. USER requests (from the frontend via the auth service)
   The frontend sends a JWT token in the Authorization header.
   We verify it here so we know WHICH user is asking for recommendations.

2. SERVICE-TO-SERVICE requests (from the auth service directly)
   The auth service calls us with a static SERVICE_TO_SERVICE_TOKEN.
   We check that token to confirm the request is internal, not from a random client.

Node.js analogy:
----------------
In Express you'd write a middleware function:
    function requireAuth(req, res, next) {
        const token = req.headers.authorization?.split(' ')[1]
        try {
            req.user = jwt.verify(token, process.env.JWT_SECRET)
            next()
        } catch {
            res.status(401).json({ error: 'Unauthorized' })
        }
    }

In FastAPI, the same idea is called a "dependency" (Depends).
Instead of calling next(), you just return the value you want injected.
FastAPI automatically calls this function before your route handler runs.
"""

import os
import jwt   # PyJWT — same as jsonwebtoken in Node.js
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# HTTPBearer tells FastAPI to look for "Authorization: Bearer <token>" in headers
bearer_scheme = HTTPBearer(auto_error=False)


def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    """
    FastAPI dependency that verifies a user's JWT token.
    Returns the decoded token payload (which contains the user_id).

    Usage in a route:
        @router.get("/recommendations")
        def get_recs(user: dict = Depends(verify_jwt), db: Session = Depends(get_db)):
            user_id = user["sub"]   # "sub" is the standard JWT field for user ID
            ...

    Raises HTTP 401 if the token is missing, expired, or tampered with.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    token = credentials.credentials
    secret = os.getenv("JWT_SECRET_KEY", "")

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_service_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> bool:
    """
    FastAPI dependency for internal service-to-service endpoints.
    The auth service sends SERVICE_TO_SERVICE_TOKEN instead of a user JWT.

    Usage:
        @router.get("/internal/something")
        def internal_route(_: bool = Depends(verify_service_token)):
            ...
    """
    expected = os.getenv("SERVICE_TO_SERVICE_TOKEN", "")

    if credentials is None or credentials.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing service token",
        )
    return True
