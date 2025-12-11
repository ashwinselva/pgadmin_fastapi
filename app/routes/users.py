from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.security import hash_password, verify_password, create_access_token
from pydantic import BaseModel
from app.security import verify_access_token

router = APIRouter(prefix="/users", tags=["users"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # check existing username/email
    existing = db.query(models.User).filter(
        (models.User.username == user_in.username) | (models.User.email == user_in.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    hashed = hash_password(user_in.password)
    user = models.User(username=user_in.username, email=user_in.email, password_hash=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


def _get_token_user_id(authorization: str | None) -> int | None:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2:
        return None
    token = parts[1]
    return verify_access_token(token)


@router.get("/me", response_model=schemas.UserRead)
def get_profile(authorization: str | None = Header(None), db: Session = Depends(get_db)):
    user_id = _get_token_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/me", response_model=schemas.UserRead)
def update_profile(payload: schemas.UserUpdate, authorization: str | None = Header(None), db: Session = Depends(get_db)):
    user_id = _get_token_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # check uniqueness
    if payload.username and payload.username != user.username:
        existing = db.query(models.User).filter(models.User.username == payload.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username or email already registered")
        user.username = payload.username
    if payload.email and payload.email != user.email:
        existing = db.query(models.User).filter(models.User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username or email already registered")
        user.email = payload.email

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password")
def change_password(payload: schemas.PasswordChange, authorization: str | None = Header(None), db: Session = Depends(get_db)):
    user_id = _get_token_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()
    return {"status": "ok"}
