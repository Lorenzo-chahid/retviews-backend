from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_username(db: Session, username: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    return user


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        username=user.username, email=user.email, hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_clothing_items(db: Session, skip: int = 0, limit: int = 1000):
    return (
        db.query(models.ClothingItem)
        .order_by(models.ClothingItem.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_clothing_item_by_id(db: Session, item_id: int):
    return (
        db.query(models.ClothingItem).filter(models.ClothingItem.id == item_id).first()
    )


def create_clothing_item(db: Session, clothing_item: schemas.ClothingItemCreate):
    db_item = models.ClothingItem(
        name=clothing_item.name,
        description=clothing_item.description,
        image_url=clothing_item.image_url,
        category_id=clothing_item.category_id,
        user_id=clothing_item.user_id,
    )
    db.add(db_item)
    db.commit()
    print("Item saved")
    return db_item


def get_clothing_items_by_user_id(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
):
    return (
        db.query(models.ClothingItem)
        .filter(models.ClothingItem.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ClothingCategory).offset(skip).limit(limit).all()


def update_clothing_item(
    db: Session, item_id: int, item_update: schemas.ClothingItemCreate, user_id: int
):
    db_item = (
        db.query(models.ClothingItem)
        .filter(
            models.ClothingItem.id == item_id, models.ClothingItem.user_id == user_id
        )
        .first()
    )
    if db_item is None:
        return None
    # Mettez à jour les champs de db_item avec les valeurs de item_update
    for var, value in vars(item_update).items():
        setattr(db_item, var, value) if value else None
    db.commit()
    db.refresh(db_item)
    return db_item
