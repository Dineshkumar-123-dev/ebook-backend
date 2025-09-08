from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from schemas import OrderBase, OrderOut
from database import SessionLocal
from models import Order, User  # ✅ User model should exist
from routes.auth import get_current_user

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🔹 Place an order (logged-in user)
@router.post("/", response_model=OrderOut)
def place_order(order: OrderBase, 
                db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user)):
    new_order = Order(
        book_id=order.book_id,
        quantity=order.quantity,
        user_id=current_user.id,   # ✅ linked to logged-in user
        status="placed"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

# 🔹 Get all orders of the logged-in user
@router.get("/my-orders")
def get_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.user_id == current_user.id).all()


# 🔹 Cancel an order (only your own)
@router.delete("/{order_id}")
def cancel_order(order_id: int, 
                 db: Session = Depends(get_db), 
                 current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "cancelled"
    db.commit()
    return {"message": "Order cancelled"}

# 🔹 Admin: View all orders
@router.get("/admin/all", response_model=List[OrderOut])
def get_all_orders(db: Session = Depends(get_db), 
                   current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(Order).all()
