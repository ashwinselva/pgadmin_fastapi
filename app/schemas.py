from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, Literal
from datetime import datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


ALLOWED_TYPES = ('Add', 'Sub', 'Multiply', 'Divide')


class CalculationCreate(BaseModel):
    a: float
    b: float
    type: Literal['Add', 'Sub', 'Multiply', 'Divide']

    @model_validator(mode='after')
    def check_division(cls, values):
        # values is the model instance in pydantic v2; perform divide-by-zero check
        if values.type == 'Divide' and values.b == 0:
            raise ValueError('Division by zero is not allowed')
        return values


class CalculationRead(BaseModel):
    id: int
    a: float
    b: float
    type: str
    result: Optional[float]
    user_id: Optional[int]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

