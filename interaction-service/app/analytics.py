"""
Analytics endpoints for the interaction service.
Provides statistics on user interactions, products, and searches.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter(tags=["Analytics"])


def get_db_analytics():
    """Get database session for analytics queries."""
    from .main import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_user_exists_analytics(db: Session, user_id: int) -> None:
    """Verify that a user exists."""
    user = db.execute(text("SELECT user_id FROM users WHERE user_id = :user_id"), {"user_id": user_id}).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {user_id}")


@router.get("")
def get_interaction_stats(db: Session = Depends(get_db_analytics)) -> dict:
    """Get overall interaction statistics across all users."""
    total_visits = db.execute(text("SELECT COUNT(*) FROM product_visits")).scalar() or 0
    unique_visitors = db.execute(text("SELECT COUNT(DISTINCT user_id) FROM product_visits")).scalar() or 0
    total_searches = db.execute(text("SELECT COUNT(*) FROM search_history")).scalar() or 0
    unique_searchers = db.execute(text("SELECT COUNT(DISTINCT user_id) FROM search_history")).scalar() or 0

    avg_visits = round(total_visits / unique_visitors, 2) if unique_visitors > 0 else 0
    avg_searches = round(total_searches / unique_searchers, 2) if unique_searchers > 0 else 0

    return {
        "total_product_visits": total_visits,
        "total_unique_visitors": unique_visitors,
        "total_searches": total_searches,
        "total_unique_searchers": unique_searchers,
        "avg_visits_per_user": avg_visits,
        "avg_searches_per_user": avg_searches,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/user/{user_id}")
def get_user_interaction_stats(user_id: int, db: Session = Depends(get_db_analytics)) -> dict:
    """Get interaction statistics for a specific user."""
    ensure_user_exists_analytics(db, user_id)

    total_visits = db.execute(
        text("SELECT COUNT(*) FROM product_visits WHERE user_id = :user_id"),
        {"user_id": user_id}
    ).scalar() or 0

    unique_products = db.execute(
        text("SELECT COUNT(DISTINCT product_id) FROM product_visits WHERE user_id = :user_id"),
        {"user_id": user_id}
    ).scalar() or 0

    total_searches = db.execute(
        text("SELECT COUNT(*) FROM search_history WHERE user_id = :user_id"),
        {"user_id": user_id}
    ).scalar() or 0

    unique_searches = db.execute(
        text("SELECT COUNT(DISTINCT searched_keyword) FROM search_history WHERE user_id = :user_id"),
        {"user_id": user_id}
    ).scalar() or 0

    last_visit = db.execute(
        text("SELECT MAX(visited_at) FROM product_visits WHERE user_id = :user_id"),
        {"user_id": user_id}
    ).scalar()

    last_search = db.execute(
        text("SELECT MAX(searched_at) FROM search_history WHERE user_id = :user_id"),
        {"user_id": user_id}
    ).scalar()

    return {
        "user_id": user_id,
        "total_product_visits": total_visits,
        "unique_products_visited": unique_products,
        "total_searches": total_searches,
        "unique_searches": unique_searches,
        "last_visit": last_visit.isoformat() if last_visit else None,
        "last_search": last_search.isoformat() if last_search else None,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/products/most-visited")
def get_most_visited_products(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db_analytics)) -> dict:
    """Get most visited products with visit counts."""
    products = db.execute(
        text("""
            SELECT product_id, COUNT(*) as visit_count, COUNT(DISTINCT user_id) as unique_visitors
            FROM product_visits GROUP BY product_id ORDER BY visit_count DESC LIMIT :limit
        """),
        {"limit": limit}
    ).fetchall()

    return {
        "count": len(products),
        "limit": limit,
        "most_visited_products": [
            {"product_id": p.product_id, "total_visits": p.visit_count, "unique_visitors": p.unique_visitors}
            for p in products
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/searches/most-searched")
def get_most_searched_keywords(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db_analytics)) -> dict:
    """Get most searched keywords with search counts."""
    keywords = db.execute(
        text("""
            SELECT searched_keyword, COUNT(*) as search_count, COUNT(DISTINCT user_id) as unique_searchers
            FROM search_history GROUP BY searched_keyword ORDER BY search_count DESC LIMIT :limit
        """),
        {"limit": limit}
    ).fetchall()

    return {
        "count": len(keywords),
        "limit": limit,
        "most_searched_keywords": [
            {"keyword": k.searched_keyword, "total_searches": k.search_count, "unique_searchers": k.unique_searchers}
            for k in keywords
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/active-users")
def get_active_users(time_window_hours: int = Query(24, ge=1, le=720), db: Session = Depends(get_db_analytics)) -> dict:
    """Get count of active users in the past N hours."""
    cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

    active_visitors = db.execute(
        text("SELECT COUNT(DISTINCT user_id) FROM product_visits WHERE visited_at > :cutoff_time"),
        {"cutoff_time": cutoff_time}
    ).scalar() or 0

    active_searchers = db.execute(
        text("SELECT COUNT(DISTINCT user_id) FROM search_history WHERE searched_at > :cutoff_time"),
        {"cutoff_time": cutoff_time}
    ).scalar() or 0

    total_active = db.execute(
        text("""
            SELECT COUNT(DISTINCT user_id) FROM (
                SELECT user_id FROM product_visits WHERE visited_at > :cutoff_time
                UNION SELECT user_id FROM search_history WHERE searched_at > :cutoff_time
            ) combined
        """),
        {"cutoff_time": cutoff_time}
    ).scalar() or 0

    return {
        "time_window_hours": time_window_hours,
        "total_active_users": total_active,
        "active_visitors": active_visitors,
        "active_searchers": active_searchers,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/top-visitors")
def get_top_visitors(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db_analytics)) -> dict:
    """Get top N users by product visits."""
    users = db.execute(
        text("""
            SELECT user_id, COUNT(*) as visit_count, COUNT(DISTINCT product_id) as unique_products,
                   MAX(visited_at) as last_visit
            FROM product_visits GROUP BY user_id ORDER BY visit_count DESC LIMIT :limit
        """),
        {"limit": limit}
    ).fetchall()

    return {
        "count": len(users),
        "limit": limit,
        "top_visitors": [
            {"user_id": u.user_id, "total_visits": u.visit_count, "unique_products_visited": u.unique_products,
             "last_visit": u.last_visit.isoformat() if u.last_visit else None}
            for u in users
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/top-searchers")
def get_top_searchers(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db_analytics)) -> dict:
    """Get top N users by search count."""
    users = db.execute(
        text("""
            SELECT user_id, COUNT(*) as search_count, COUNT(DISTINCT searched_keyword) as unique_keywords,
                   MAX(searched_at) as last_search
            FROM search_history GROUP BY user_id ORDER BY search_count DESC LIMIT :limit
        """),
        {"limit": limit}
    ).fetchall()

    return {
        "count": len(users),
        "limit": limit,
        "top_searchers": [
            {"user_id": u.user_id, "total_searches": u.search_count, "unique_keywords": u.unique_keywords,
             "last_search": u.last_search.isoformat() if u.last_search else None}
            for u in users
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/interaction-trends")
def get_interaction_trends(days: int = Query(7, ge=1, le=90), db: Session = Depends(get_db_analytics)) -> dict:
    """Get interaction trends over the past N days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    daily_visits = db.execute(
        text("""
            SELECT DATE(visited_at) as date, COUNT(*) as visit_count, COUNT(DISTINCT user_id) as unique_users
            FROM product_visits WHERE visited_at > :cutoff_date GROUP BY DATE(visited_at) ORDER BY date ASC
        """),
        {"cutoff_date": cutoff_date}
    ).fetchall()

    daily_searches = db.execute(
        text("""
            SELECT DATE(searched_at) as date, COUNT(*) as search_count, COUNT(DISTINCT user_id) as unique_users
            FROM search_history WHERE searched_at > :cutoff_date GROUP BY DATE(searched_at) ORDER BY date ASC
        """),
        {"cutoff_date": cutoff_date}
    ).fetchall()

    return {
        "days_analyzed": days,
        "daily_visits": [
            {"date": str(v.date), "total_visits": v.visit_count, "unique_users": v.unique_users}
            for v in daily_visits
        ],
        "daily_searches": [
            {"date": str(s.date), "total_searches": s.search_count, "unique_users": s.unique_users}
            for s in daily_searches
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
