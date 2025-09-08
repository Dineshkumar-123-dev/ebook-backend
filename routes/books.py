from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import SessionLocal
from .auth import check_is_admin, check_is_superadmin

router = APIRouter(prefix="/api/books", tags=["Books"])


# ==================== DB Dependency ====================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== PUBLIC ROUTES ====================

# Get All Books
@router.get("/", response_model=List[schemas.BookOut])
def get_books(db: Session = Depends(get_db)):
    books = db.query(models.Book).all()
    return books


# Get Book by ID
@router.get("/{book_id}", response_model=schemas.BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


# ==================== ADMIN / SUPERADMIN ROUTES ====================

# Create Book
@router.post("/", response_model=schemas.BookOut)
def create_book(
    book: schemas.BookCreate,
    db: Session = Depends(get_db),
    current_user=Depends(check_is_admin)
):
    new_book = models.Book(**book.dict())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


# Update Book
@router.put("/{book_id}", response_model=schemas.BookOut)
def update_book(
    book_id: int,
    updated_book: schemas.BookCreate,
    db: Session = Depends(get_db),
    current_user=Depends(check_is_admin)
):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    for key, value in updated_book.dict().items():
        setattr(book, key, value)

    db.commit()
    db.refresh(book)
    return book


# Delete Book
@router.delete("/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(check_is_admin)
):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(book)
    db.commit()
    return {"message": f"Book with id {book_id} has been deleted"}


# Approve Book (superadmin only)
@router.put("/{book_id}/approve")
def approve_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(check_is_superadmin)
):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book.is_approved = True
    db.commit()
    db.refresh(book)
    return {"message": f"Book '{book.title}' approved by SuperAdmin"}


# Reject Book (superadmin only)
@router.put("/{book_id}/reject")
def reject_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(check_is_superadmin)
):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book.is_approved = False
    db.commit()
    db.refresh(book)
    return {"message": f"Book '{book.title}' rejected by SuperAdmin"}
