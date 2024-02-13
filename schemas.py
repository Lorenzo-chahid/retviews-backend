from pydantic import BaseModel
from typing import Optional, List


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int


class ClothingCategoryBase(BaseModel):
    name: str


class ClothingCategory(ClothingCategoryBase):
    id: int

    class Config:
        from_attributes = True  # Correction ici


class ClothingItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    category_id: int


class ClothingItemCreate(ClothingItemBase):
    user_id: int


class ClothingItem(ClothingItemBase):
    id: int
    category: Optional[ClothingCategory]

    class Config:
        from_attributes = True


class ClothingItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None
