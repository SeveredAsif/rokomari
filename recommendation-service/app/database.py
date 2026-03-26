"""
database.py
-----------
Sets up the connection to PostgreSQL using SQLAlchemy.

In Node.js you would do something like:
    const { Pool } = require('pg')
    const pool = new Pool({ connectionString: process.env.DATABASE_URL })

Here we do the same thing but with SQLAlchemy, which is Python's most popular
database toolkit. It gives us both raw SQL execution AND an ORM (like Sequelize or Prisma).

The SessionLocal object is a "session factory" — every time we need to talk to
the database, we ask it to create a new session (think of it like opening and
closing a database connection for each request).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# Reads DATABASE_URL from the .env file.
# Example value: postgresql+psycopg2://admin:password@postgres:5432/rokomari
#                                                       ↑↑↑↑↑↑↑↑
#                              This "postgres" is the Docker service name, not localhost!
DATABASE_URL = os.getenv("DATABASE_URL")

# create_engine is like creating the pool in pg (Node.js).
# It does NOT open a connection immediately — it just prepares one.
engine = create_engine(DATABASE_URL)

# SessionLocal is the factory for database sessions.
# autocommit=False → we control when to commit (save) changes manually.
# autoflush=False  → don't automatically sync changes to DB mid-session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class that all our database models (tables) will inherit from.
# Equivalent to defining a Sequelize model that extends Model.
class Base(DeclarativeBase):
    pass


def get_db():
    """
    A FastAPI 'dependency' — a function that FastAPI calls automatically
    before your route handler runs, and cleans up after it finishes.

    This is like Express middleware, but scoped to a single route.

    Usage in a route:
        from app.database import get_db
        from sqlalchemy.orm import Session
        from fastapi import Depends

        @app.get("/something")
        def my_route(db: Session = Depends(get_db)):
            # db is ready to use here
            ...

    The try/finally ensures the session is always closed even if an error occurs,
    which prevents connection leaks.
    """
    db = SessionLocal()
    try:
        yield db          # "yield" hands the session to the route handler
    finally:
        db.close()        # always runs after the request finishes
