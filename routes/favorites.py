from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, database
from routes.auth import get_current_user

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])


@router.post("/", response_model=schemas.FavoriteOut)
def add_favorite(
    fav: schemas.FavoriteCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = (
        db.query(models.Favorite)
        .filter_by(user_id=current_user.id, book_id=fav.book_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already in favorites")

    # Ensure book exists
    book = db.query(models.Book).filter(models.Book.id == fav.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    new_fav = models.Favorite(user_id=current_user.id, **fav.dict())
    db.add(new_fav)
    db.commit()
    db.refresh(new_fav)
    return new_fav


@router.get("/", response_model=list[schemas.FavoriteOut])
def get_favorites(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Favorite).filter(models.Favorite.user_id == current_user.id).all()


@router.delete("/{book_id}")
def remove_favorite(
    book_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    fav = (
        db.query(models.Favorite)
        .filter_by(user_id=current_user.id, book_id=book_id)
        .first()
    )
    if not fav:
        raise HTTPException(status_code=404, detail="Book not found in favorites")

    db.delete(fav)
    db.commit()
    return {"msg": "Removed from favorites"}
