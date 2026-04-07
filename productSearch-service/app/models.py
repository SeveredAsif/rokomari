from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.sql import func

try:
    from .database import Base
except ImportError:
    from database import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False, index=True)
    category_id = Column(Integer, nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock_qty = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    product_type = Column(String, nullable=False, index=True)


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, nullable=False, unique=True, index=True)


class BookDetail(Base):
    __tablename__ = "book_details"

    product_id = Column(Integer, ForeignKey("products.product_id"), primary_key=True, index=True)
    isbn = Column(String)
    author = Column(String, index=True)
    publisher = Column(String, index=True)
    language = Column(String)
    num_pages = Column(Integer)
    edition = Column(String)


class SearchHistory(Base):
    __tablename__ = "search_history"

    search_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    searched_keyword = Column(String, nullable=False, index=True)
    searched_at = Column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, server_default=func.now())