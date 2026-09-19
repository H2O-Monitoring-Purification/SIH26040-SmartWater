from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import UserLogin, UserRegister


def register_user(
    db: Session,
    data: UserRegister,
) -> User:
    existing_user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_user:
        raise ValueError("Email is already registered")

    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="operator",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    data: UserLogin,
) -> User | None:
    user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        return None

    return user


def create_user_token(user: User) -> str:
    return create_access_token(str(user.id))