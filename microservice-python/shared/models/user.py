from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime
from bson import ObjectId
from enum import Enum
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return {"type": "string", "format": "objectid"}

    def __str__(self):
        return str(super())

class ThemeEnum(str, Enum):
    light = "light"
    dark = "dark"

class TransactionTypeEnum(str, Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    purchase = "purchase"
    sale = "sale"

class Rating(BaseModel):
    from_user: Optional[PyObjectId] = Field(alias="fromUser")
    stars: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")

class WalletHistory(BaseModel):
    amount: float
    type: TransactionTypeEnum
    date: datetime = Field(default_factory=datetime.utcnow)

class Wallet(BaseModel):
    balance: float = 0.0
    history: List[WalletHistory] = []

class User(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()},
        json_schema_extra={
            "example": {
                "username": "testuser123",
                "email": "test@example.com",
                "password": "securepassword123",
                "admin": False,
                "bio": "Test user bio",
                "theme": "light"
            }
        }
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    username: str = Field(..., min_length=6, max_length=20)
    email: EmailStr = Field(..., min_length=8, max_length=40)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    admin: bool = False
    google_id: Optional[str] = Field(None, alias="googleId")
    facebook_id: Optional[str] = Field(None, alias="facebookId")
    avatar_url: str = Field(default="/default-avatar.png", alias="avatarUrl")
    bio: Optional[str] = Field(None, max_length=200)
    vouchers_posted: int = Field(default=0, alias="vouchersPosted")
    vouchers_sold: int = Field(default=0, alias="vouchersSold")
    vouchers_bought: int = Field(default=0, alias="vouchersBought")
    vouchers: List[PyObjectId] = []
    ratings: List[Rating] = []
    wallet: Wallet = Field(default_factory=Wallet)
    theme: ThemeEnum = ThemeEnum.light
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

class UserCreate(BaseModel):
    username: str = Field(..., min_length=6, max_length=20)
    email: EmailStr = Field(..., min_length=8, max_length=40)
    password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=6, max_length=20)
    email: Optional[EmailStr] = Field(None, min_length=8, max_length=40)
    bio: Optional[str] = Field(None, max_length=200)
    avatar_url: Optional[str] = Field(None, alias="avatarUrl")
    theme: Optional[ThemeEnum] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(alias="_id")
    username: str
    email: EmailStr
    admin: bool
    avatar_url: str = Field(alias="avatarUrl")
    bio: Optional[str]
    vouchers_posted: int = Field(alias="vouchersPosted")
    vouchers_sold: int = Field(alias="vouchersSold")
    vouchers_bought: int = Field(alias="vouchersBought")
    wallet: Wallet
    theme: ThemeEnum
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt") 