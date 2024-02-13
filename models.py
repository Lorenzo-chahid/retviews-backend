from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import database
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ClothingCategory(Base):
    __tablename__ = "clothing_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    clothing_items = relationship("ClothingItem", back_populates="category")


class ClothingItem(Base):
    __tablename__ = "clothing_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(String, index=True, nullable=True)
    image_url = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey("clothing_categories.id"))

    category = relationship("ClothingCategory", back_populates="clothing_items")
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="clothing_items")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    clothing_items = relationship("ClothingItem", back_populates="user")


def recreate_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
