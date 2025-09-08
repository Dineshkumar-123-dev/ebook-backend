from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ~~~~~~~~~~~ USER SCHEMAS ~~~~~~~~~~~
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str  
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: int
    username: str
    email: str
    is_admin: Optional[bool] = None
    admin_id: Optional[int] = None   # Show who created the user

    class Config:
        from_attributes = True


# ~~~~~~~~~~~~~~ ADMIN SCHEMAS ~~~~~~~~~~~~~~
class AdminBase(BaseModel):
    username: str
    email: EmailStr


# For creating an admin (requires password)
class AdminCreate(AdminBase):
    password: str


# For updating an admin (all fields optional)
class AdminUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


# For returning admin details
class AdminOut(AdminBase):
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True


# ~~~~~~~~~~~~~ BOOK SCHEMAS ~~~~~~~~~~~~~
class BookBase(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    price: Optional[float] = None


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None


class BookOut(BookBase):
    id: int
    title: str
    author: str
    description: str
    price: float
    
    class Config:
        from_attributes = True


# ~~~~~~~~~~~~~~ ORDER SCHEMAS ~~~~~~~~~~~~~~~~~~
class OrderBase(BaseModel):
    user_id: int
    book_id: int
    quantity: int


class OrderCreate(OrderBase):
    pass


class OrderOut(OrderBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ~~~~~~~~~~~~~~~ REVIEW SCHEMAS ~~~~~~~~~~~~~~~~~~
class ReviewBase(BaseModel):
    book_id: int
    rating: int
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None


class ReviewOut(ReviewBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ~~~~~~~~~~~~~~~~ AUTHENTICATION SCHEMAS ~~~~~~~~~~~~~~~~~~~
class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):  # renamed for convention
    access_token: str
    token_type: str = "bearer"


# ~~~~~~~~~~~~~~~~ CART SCHEMAS ~~~~~~~~~~~~~~~~~~~
class CartBase(BaseModel):
    book_id: int
    quantity: int = 1

class CartCreate(CartBase):
    pass

class CartOut(BaseModel):
    id: int
    user_id: int
    book_id: int
    quantity: int
    book: BookOut 

    class Config:
        from_attributes = True

# ~~~~~~~~~~~~~~~~ FAVORITE SCHEMAS ~~~~~~~~~~~~~~~~~~~
class FavoriteBase(BaseModel):
    book_id: int

class FavoriteCreate(FavoriteBase):
    pass

class FavoriteOut(FavoriteBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True



# ================= NESTED RELATIONS ===================
class OrderWithBook(OrderOut):
    book: BookOut


class UserWithOrders(UserOut):
    orders: List[OrderWithBook] = Field(default_factory=list)


class ReviewWithUser(ReviewOut):
    user: UserOut


class BookWithReviews(BookOut):
    reviews: List[ReviewWithUser] = Field(default_factory=list)
