import os
import smtplib
from datetime import timedelta
from email.mime.text import MIMEText

from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import jwt
from jose import JWTError

from database import get_db
from models import User
from schemas import UserCreate
from .auth import pwd_context, create_token
from .auth import SECRET_KEY, ALGORITHM   # make sure you have these defined in config.py

# =============================
# Load environment variables
# =============================
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
FRONTEND_URL = os.getenv("FRONTEND_URL")
VERIFICATION_TOKEN_EXPIRE_HOURS = int(os.getenv("VERIFICATION_TOKEN_EXPIRE_HOURS", 1))

router = APIRouter(tags=["Email"])


# =============================
# Email sending utility
# =============================
def send_verification_email(email: str, token: str):
    """Send verification email to the user"""
    link = f"{FRONTEND_URL}/verify/{token}"
    body = f"""
    Hi,

    Thank you for registering! Please verify your email by clicking the link below:
    {link}

    This link will expire in {VERIFICATION_TOKEN_EXPIRE_HOURS} hour(s).

    If you didn’t create this account, you can safely ignore this email.

    Regards,
    Your App Team
    """

    msg = MIMEText(body, "plain")
    msg["Subject"] = "Verify your account"
    msg["From"] = EMAIL_USER
    msg["To"] = email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)  # Gmail App Password required
            server.sendmail(EMAIL_USER, [email], msg.as_string())
        print(f"✅ Verification email sent to {email}")
    except Exception as e:
        import traceback
        print("❌ Error sending email:", e)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send verification email: {str(e)}"
        )


# =============================
# Register (User signup)
# =============================
@router.post("/register")
def register(new_user: UserCreate, db: Session = Depends(get_db)):
    """User Registration with email verification"""
    existing_user = db.query(User).filter(User.email == new_user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # ✅ Hash password before saving
    hashed_password = pwd_context.hash(new_user.password)

    user = User(
        username=new_user.username,
        email=new_user.email,
        hashed_password=hashed_password,
        role="user",
        is_verified=False  # not verified until email confirmation
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        print(f"❌ Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

    # ✅ Create verification token
    token = create_token(
        {"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
    )

    # ✅ Send verification email
    send_verification_email(user.email, token)

    return {
        "message": "✅ Registration successful. Please check your email to verify your account.",
        "token": token
    }


# =============================
# Verify Email
# =============================
@router.get("/verify/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        # ✅ Already verified → just redirect to login
        return RedirectResponse(url=f"{FRONTEND_URL}/login")

    # ✅ Mark as verified
    user.is_verified = True
    db.commit()
    db.refresh(user)

    # ✅ Redirect to login page after verification
    return {"message": "Email verified successfully"}
