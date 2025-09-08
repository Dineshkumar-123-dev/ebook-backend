from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


# ================= USERS ===================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, nullable=False, default="user") 
    is_verified = Column(Boolean, default=False)  # email verification status
    is_admin = Column(Boolean,nullable=False, default=False)

    # Reference to creator (admin_id)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)

    # Relationship back to Admin
    created_by = relationship("Admin", back_populates="users")

    # Relationships
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")  # need to see the cascade
    cart_items = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")



# ================= ADMINS ===================
class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, nullable=False, default="admin")  # e.g., superadmin, moderator

    users = relationship("User", back_populates="created_by", cascade="all, delete-orphan")

# ================= BOOKS ===================
class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String)
    description = Column(String)
    price = Column(Float, nullable=False)

    # Relationships
    orders = relationship("Order", back_populates="book", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")
    cart_items = relationship("Cart", back_populates="book", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="book", cascade="all, delete-orphan")

# ================= ORDERS ===================
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    quantity = Column(Integer, default=1)
    status = Column(String, default="pending")  # pending, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    


    # Relationships
    user = relationship("User", back_populates="orders")
    book = relationship("Book", back_populates="orders")


# ================= REVIEWS ===================
class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    rating = Column(Integer)  # e.g., 1-5 stars
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reviews")
    book = relationship("Book", back_populates="reviews")


# ================= Add to cart ===================
class Cart(Base):
    __tablename__ = "cart"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    quantity = Column(Integer, default=1)

    user = relationship("User", back_populates="cart_items")
    book = relationship("Book", back_populates="cart_items")


# ================= Favourites ===================
class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    
    user = relationship("User", back_populates="favorites")
    book = relationship("Book", back_populates="favorites")



