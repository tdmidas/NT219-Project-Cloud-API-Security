from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

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

    def __str__(self):
        return str(super())

class RefreshToken(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    token: str = Field(..., min_length=1)
    user_id: PyObjectId = Field(..., alias="userId")
    expires_at: datetime = Field(..., alias="expiresAt")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    is_revoked: bool = Field(default=False, alias="isRevoked")
    device_info: Optional[str] = Field(None, alias="deviceInfo")
    ip_address: Optional[str] = Field(None, alias="ipAddress")

class RefreshTokenCreate(BaseModel):
    token: str
    user_id: str
    expires_at: datetime
    device_info: Optional[str] = None
    ip_address: Optional[str] = None 