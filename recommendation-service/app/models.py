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

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.sql import func
from app.database import Base


class Product(Base):
    """
    The products table. This is what we search through and recommend.
    We read from this table — we never write to it here.
    """
    __tablename__ = "products"

    product_id   = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False, index=True)   # Used for cosine similarity search
    category_id  = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    price        = Column(Numeric(10, 2), nullable=True)
    description  = Column(Text, nullable=True)
    image_url    = Column(String, nullable=True)
    brand        = Column(String, nullable=True)
    product_type = Column(String, nullable=False)


class SearchHistory(Base):
    """
    Stores every search keyword a user types.
    We READ this to find what a user searched for, then run cosine similarity
    between those past keywords and all product names.
    We also WRITE to this table when a new search happens.
    """
    __tablename__ = "search_history"

    search_id   = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    searched_keyword = Column(String,  nullable=False)         # The search term the user typed
    searched_at = Column(DateTime(timezone=True), server_default=func.now())


class ProductVisit(Base):
    """
    Tracks which product pages a user has visited.
    We READ this to find visited products, then:
      i.  Show those exact products again (direct recommendation)
      ii. Find cosine-similar products to those visited ones
    """
    __tablename__ = "product_visits"

    visit_id   = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    visited_at  = Column(DateTime(timezone=True), server_default=func.now())


class Order(Base):
    """
    Stores one order header row.
    Product-level items are in order_items.
    """
    __tablename__ = "orders"

    order_id   = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    order_date = Column(DateTime(timezone=True), server_default=func.now())


class OrderItem(Base):
    """Items belonging to each order, used to derive ordered product signals."""
    __tablename__ = "order_items"

    order_item_id = Column(Integer, primary_key=True, index=True)
    order_id      = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    product_id    = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity      = Column(Integer, nullable=False)


class User(Base):
    """
    Users table — we don't manage auth here, but we need this class
    so SQLAlchemy understands the foreign key relationships above.
    Think of it as a reference, not something we write to.
    """
    __tablename__ = "users"

    user_id    = Column(Integer, primary_key=True, index=True)
    email = Column(String,  unique=True, nullable=False)
