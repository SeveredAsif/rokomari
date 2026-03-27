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
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# Reads DATABASE_URL from the .env file.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable is not set!")
    print("Please set DATABASE_URL in .env file")
    sys.exit(1)

# create_engine is like creating the pool in pg (Node.js).
try:
    engine = create_engine(DATABASE_URL)
    print(f"✓ Database engine created: {DATABASE_URL[:50]}...")
except Exception as e:
    print(f"ERROR: Failed to create database engine: {e}")
    sys.exit(1)

# SessionLocal is the factory for database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class that all our database models (tables) will inherit from.
# Equivalent to defining a Sequelize model that extends Model.
class Base(DeclarativeBase):
    pass


def get_db():
    """
    A FastAPI 'dependency' — a function that FastAPI calls automatically
    before your route handler runs, and cleans up after it finishes.

    This is similar to middleware in Express:
        app.use((req, res, next) => {
            req.db = getNewDatabaseSession()
            res.on('finish', () => req.db.close())
            next()
        })

    But in FastAPI it's cleaner — you just list it as a parameter:
        @app.get("/")
        def my_route(db: Session = Depends(get_db)):
            # FastAPI calls get_db() before running your function
            # The session is automatically closed after the function returns

    Usage:
        def my_route(db: Session = Depends(get_db)):
            user = db.query(User).first()
            return user
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
