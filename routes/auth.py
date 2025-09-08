from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import EmailStr
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from dotenv import load_dotenv
import os

import models
from database import SessionLocal, get_db
from schemas import LoginSchema as LoginRequest, UserCreate
from models import User, Admin

# =============================
# Load environment variables
# =============================
load_dotenv()

SUPER_ADMIN_EMAIL = os.getenv("SUPER_ADMIN_EMAIL")
SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# =============================
# Security utils
# =============================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter(tags=["Authentication"])


# =============================
# Utility: Create JWT Token
# =============================
def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# =============================
# Dependency: Get Current User
# =============================
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Validate JWT and return user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # ✅ If superadmin, return pseudo user
    if role == "superadmin":
        return {"id": 0, "email": SUPER_ADMIN_EMAIL, "role": "superadmin"}

    # ✅ Otherwise fetch from DB
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


# =============================
# Login
# =============================
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    # ✅ Super Admin Login
    if data.email == SUPER_ADMIN_EMAIL and data.password == SUPER_ADMIN_PASSWORD:
        token = create_token(
            {"sub": "0", "email": SUPER_ADMIN_EMAIL, "role": "superadmin"},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return {
            "access_token": token,
            "role": "superadmin",
            "redirect_to": "/super-admin-dashboard"
        }

    # ✅ Admin Login
    admin = db.query(Admin).filter(Admin.email == data.email).first()
    if admin and pwd_context.verify(data.password, admin.hashed_password):
        token = create_token(
            {"sub": str(admin.id), "email": admin.email, "role": "admin"},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return {
            "access_token": token,
            "role": "admin",
            "redirect_to": "/admins"
        }

    # ✅ User Login
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not pwd_context.verify(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in."
        )

    token = create_token(
        {"sub": str(user.id), "email": user.email, "role": "user"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": token,
        "role": "user",
        "redirect_to": "/user-dashboard"
    }


# =============================
# Role Dependencies
# =============================
def check_is_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admins only."
        )
    return current_user


def check_is_superadmin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Super Admins only."
        )
    return current_user


# =============================
# Logout
# =============================
@router.post("/logout")
def logout():
    return {"message": "User logged out successfully"}


# =============================
# Super Admin: Manage Admins
# =============================
@router.get("/admins")
def get_admins(current_user: dict = Depends(check_is_superadmin), db: Session = Depends(get_db)):
    """Get all admins (Super Admin only)"""
    return db.query(Admin).all()


@router.post("/add-admin")
def add_admin(
    new_admin: UserCreate,
    current_user: dict = Depends(check_is_superadmin),
    db: Session = Depends(get_db),
):
    """Super Admin creates a new Admin"""
    existing_admin = db.query(Admin).filter(Admin.email == new_admin.email).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin with this email already exists")

    hashed_password = pwd_context.hash(new_admin.password)
    admin = Admin(
        username=new_admin.username,
        email=new_admin.email,
        hashed_password=hashed_password,
        role="admin"
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return {"message": f"Admin {admin.username} created successfully", "id": admin.id}
