import json
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import crud, models, schemas, database
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()

SECRET_KEY = "8B478AD74FB2D4DBD7EA2DDA83B14"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

origins = ["http://localhost:4200", "https://retchad.onrender.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def populate_categories_if_empty(db: Session):
    if db.query(models.ClothingCategory).count() == 0:
        categories = ["nice to have", "wishlist", "bought"]
        for category_name in categories:
            category = models.ClothingCategory(name=category_name)
            db.add(category)
        db.commit()
        print("Add 🚀")


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user


def populate_db_with_clothing_data(db: Session):
    with open("./clothing_data.json") as file:
        data = json.load(file)
        for item_data in data:
            category = (
                db.query(models.ClothingCategory)
                .filter(models.ClothingCategory.name == item_data["category"])
                .first()
            )
            if not category:
                category = models.ClothingCategory(name=item_data["category"])
                db.add(category)
                db.commit()

            item = models.ClothingItem(
                name=item_data["name"],
                description=item_data["description"],
                image_url=item_data["image_url"],
                category=category,
            )
            db.add(item)
        db.commit()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    print("AUTHENTICATE")
    populate_categories_if_empty(db)
    user = crud.get_user_by_username(db, username=username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Informations d'identification incorrectes",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
    }


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.get("/clothing-items/", response_model=List[schemas.ClothingItem])
def read_clothing_items(
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    clothing_items = crud.get_clothing_items_by_user_id(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return clothing_items


@app.get("/clothing-items/{item_id}/", response_model=schemas.ClothingItem)
def read_clothing_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_item = crud.get_clothing_item_by_id(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.put("/edit-clothing/{item_id}/", response_model=schemas.ClothingItem)
def update_clothing_item(
    item_id: int,
    item_update: schemas.ClothingItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    updated_item = crud.update_clothing_item(
        db, item_id=item_id, item_update=item_update, user_id=current_user.id
    )
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item


@app.get("/clothing-categories/", response_model=List[schemas.ClothingCategory])
def read_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    print("CATEGORY CHOOSE")
    categories = crud.get_categories(db, skip=skip, limit=limit)
    return categories


@app.post("/new-clothing/", response_model=schemas.ClothingItem)
def create_clothing_item(
    clothing_item: schemas.ClothingItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.create_clothing_item(db=db, clothing_item=clothing_item)


if __name__ == "__main__":
    db = database.SessionLocal()
    populate_categories_if_empty(db)
    db.close()
