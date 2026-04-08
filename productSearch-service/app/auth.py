"""
auth.py
-------
Two types of authentication this service needs to handle:

1. USER requests (from the frontend via the auth service)
   The frontend sends a JWT token in the Authorization header.
   We verify it here so we know WHICH user is asking for searches.

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
        @router.get("/search")
        def search(user: dict = Depends(verify_jwt), db: Session = Depends(get_db)):
            user_id = user["sub"]   # "sub" is the standard JWT field for user ID
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        # Decode the JWT with your secret key.
        # PyJWT will raise InvalidTokenError if:
        #   - the signature is wrong
        #   - the token is expired
        #   - the token is malformed
        decoded = jwt.decode(
            token,
            key=os.getenv("JWT_SECRET"),
            algorithms=["HS256"]
        )
        return decoded
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_jwt_optional(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict | None:
    """
    Optional JWT dependency.
    - No token provided: returns None (anonymous request)
    - Valid token provided: returns decoded payload
    - Invalid token provided: raises 401
    """
    if not credentials:
        return None

    token = credentials.credentials
    try:
        decoded = jwt.decode(
            token,
            key=os.getenv("JWT_SECRET"),
            algorithms=["HS256"],
        )
        return decoded
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_service_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> bool:
    """
    Verifies that a request came from another authorized service (e.g., auth-service).
    Used for inter-service communication.

    Returns True if valid, raises HTTPException otherwise.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing service token",
        )

    token = credentials.credentials
    expected_token = os.getenv("SERVICE_TO_SERVICE_TOKEN")

    if not expected_token or token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid service token",
        )

    return True
