"""
models.py
---------
Defines the database tables as Python classes (ORM models).

In Node.js with Sequelize you'd write:
    const Product = sequelize.define('Product', {
        id: { type: DataTypes.INTEGER, primaryKey: true },
        name: DataTypes.STRING,
        ...
    })

Here we write Python classes instead. SQLAlchemy reads these classes and knows
exactly which table and columns to query.

IMPORTANT: These models assume the tables already exist in the database
(created by the auth service or a migration). This service only READS from
most of these tables. It does write to search_history.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

try:
    from .database import Base
except ImportError:
    from database import Base


class Product(Base):
    """
    The products table. This is what we search through.
    We read from this table — we never write to it here.
    """
    __tablename__ = "products"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False, index=True)   # Used for cosine similarity search
    description = Column(Text,   nullable=True)
    author      = Column(String, nullable=True)
    category    = Column(String, nullable=True, index=True)
    price       = Column(Float,  nullable=True)
    image_url   = Column(String, nullable=True)


class SearchHistory(Base):
    """
    Stores every search query a user makes.
    We READ this to track search patterns.
    We WRITE to this table when a new search happens.
    """
    __tablename__ = "search_history"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    query      = Column(String, nullable=False, index=True)
    timestamp  = Column(DateTime, server_default=func.now())


class User(Base):
    """
    The users table. Used to track search history per user.
    We read from this table to validate users exist.
    """
    __tablename__ = "users"

    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email    = Column(String, unique=True, nullable=False, index=True)
