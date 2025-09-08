from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import SessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/api/admin", tags=["Admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== CREATE ADMIN ==========
@router.post("/create-admin", response_model=schemas.AdminOut)
def create_admin(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
    """Super Admin can create an admin directly"""

    # Check existing admin by email
    existing_admin = db.query(models.Admin).filter(models.Admin.email == admin.email).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists")

    # Hash password
    hashed_password = pwd_context.hash(admin.password)

    # Create new admin
    new_admin = models.Admin(
        username=admin.username,
        email=admin.email,
        hashed_password=hashed_password
    )

    try:
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return new_admin


# ========== USER MANAGEMENT ==========
@router.get("/users", response_model=list[schemas.UserOut])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": f"User {user.username} deleted successfully"}


@router.put("/users/{user_id}/promote")
def promote_to_admin(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = "admin"
    db.commit()
    db.refresh(user)
    return {"message": "User promoted to admin", "user": user}

@router.put("/users/{user_id}/demote")
def demote_to_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = "user"
    db.commit()
    db.refresh(user)
    return {"message": "User demoted to user", "user": user}

# ========== BOOK MANAGEMENT ==========
@router.get("/books", response_model=list[schemas.BookOut])
def get_all_books(db: Session = Depends(get_db)):
    return db.query(models.Book).all()


@router.post("/books", response_model=schemas.BookOut)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    """Admin can add a new book"""
    new_book = models.Book(
        title=book.title,
        author=book.author,
        description=book.description,
        price=book.price,
       # is_approved=True  # Directly approved when added by Admin
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


@router.put("/books/{book_id}", response_model=schemas.BookOut)
def update_book(book_id: int, updated_book: schemas.BookCreate, db: Session = Depends(get_db)):
    """Admin can update book details"""
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book.title = updated_book.title
    book.author = updated_book.author
    book.description = updated_book.description
    book.price = updated_book.price
    db.commit()
    db.refresh(book)
    return book


@router.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Admin can delete a book"""
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return {"message": f"Book '{book.title}' deleted successfully"}


# ========== DASHBOARD STATS ==========
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    user_count = db.query(models.User).count()
    book_count = db.query(models.Book).count()
    approved_books = db.query(models.Book).filter(models.Book.is_approved == True).count()
    pending_books = db.query(models.Book).filter(models.Book.is_approved == False).count()

    return {
        "total_users": user_count,
        "total_books": book_count,
        "approved_books": approved_books,
        "pending_books": pending_books
    }


