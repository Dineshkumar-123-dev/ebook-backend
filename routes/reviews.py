from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import SessionLocal
from routes.auth import get_current_user

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🔹 Add a review to a book
@router.post("/", response_model=schemas.ReviewOut)
def create_review(
    review: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    new_review = models.Review(
        user_id=current_user.id,
        book_id=review.book_id,
        rating=review.rating,
        comment=review.comment,
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review



# 🔹 Get all reviews for a book
@router.get("/{book_id}", response_model=List[schemas.ReviewOut])
def get_reviews(book_id: int, db: Session = Depends(get_db)):
    reviews = db.query(models.Review).filter(models.Review.book_id == book_id).all()
    return reviews


# 🔹 Update review (by owner)
@router.put("/{review_id}", response_model=schemas.ReviewOut)
def update_review(review_id: int, updated: schemas.ReviewBase, db: Session = Depends(get_db)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.rating = updated.rating
    review.comment = updated.comment
    db.commit()
    db.refresh(review)
    return review


# 🔹 Delete review (by owner)
@router.delete("/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    db.delete(review)
    db.commit()
    return {"message": "Review deleted"}
