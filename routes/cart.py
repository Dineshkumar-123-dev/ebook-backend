from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
import models, schemas, database
from routes.auth import get_current_user
from typing import List

router = APIRouter(prefix="/api/cart", tags=["Cart"])


@router.post("/", response_model=schemas.CartOut)
def add_to_cart(
    cart: schemas.CartCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = (
        db.query(models.Cart)
        .filter_by(user_id=current_user.id, book_id=cart.book_id)
        .first()
    )
    if existing:
        existing.quantity += cart.quantity
        db.commit()
        db.refresh(existing)
        return existing

    # Ensure book exists
    book = db.query(models.Book).filter(models.Book.id == cart.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    new_cart = models.Cart(user_id=current_user.id, **cart.dict())
    db.add(new_cart)
    db.commit()
    db.refresh(new_cart)
    return new_cart


@router.get("/", response_model=list[schemas.CartOut])
def get_cart(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    items = (
        db.query(models.Cart)
        .options(joinedload(models.Cart.book), joinedload(models.Cart.user))
        .filter(models.Cart.user_id == current_user.id)
        .all()
    )
    return items


@router.delete("/{book_id}")
def remove_from_cart(
    book_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = (
        db.query(models.Cart)
        .filter_by(user_id=current_user.id, book_id=book_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Book not found in cart")
    db.delete(item)
    db.commit()
    return {"msg": "Removed from cart"}
