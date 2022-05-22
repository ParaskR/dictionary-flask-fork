import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class Person(BaseModel):
    id: Optional[int]
    firstName: str
    lastName: str
    dateOfBirth: Optional[datetime.date]

    class Config:
        orm_mode = True


class User(Person):
    username: str
    email: EmailStr
    password: str

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: str
    password: str

    class Config:
        orm_mode = True
