from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base
from routes import users, admin, books, orders, reviews, auth, cart, favorites
from fastapi.middleware.cors import CORSMiddleware
from routes import email_utils as email

origins = [
    "http://localhost:5173",   # your frontend Vite dev server
    "http://127.0.0.1:5173"
]

app = FastAPI(title="E-Book Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Create DB tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to the E-Book Platform"}

# Include routers
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(books.router)
app.include_router(auth.router, prefix="/api/auth")
app.include_router(email.router, prefix="/api")
app.include_router(orders.router)
app.include_router(reviews.router)
app.include_router(cart.router)
app.include_router(favorites.router)


