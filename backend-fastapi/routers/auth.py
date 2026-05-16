from datetime import datetime, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from ulid import ULID

from core.auth import create_token
from db.models import User
from db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _fmt(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("/register", status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if len(body.password) < 8:
        raise HTTPException(400, "password must be at least 8 characters")

    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(409, "An account with this email already exists")

    user = User(
        id=str(ULID()),
        email=body.email.lower(),
        name=body.name.strip(),
        role="admin",
        password_hash=bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode(),
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id, user.email, user.name, user.role)
    return {"token": token, "user": _fmt(user)}


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not bcrypt.checkpw(body.password.encode(), user.password_hash.encode()):
        raise HTTPException(401, "Invalid email or password")

    token = create_token(user.id, user.email, user.name, user.role)
    return {"token": token, "user": _fmt(user)}
