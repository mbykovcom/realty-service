from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic.networks import EmailStr


class UserIn(BaseModel):
    email: EmailStr = Field(..., description='The email a user')
    password: str = Field(..., description='The password a user', min_length=4)
    building_id: str = Field(None, description='The object that the user belongs to')


class UserOut(BaseModel):
    user_id: str = Field(..., description='The id a user')
    building_id: str = Field(None, description='The object that the user belongs to')
    email: EmailStr = Field(..., description='The email a user')
    role: str = Field(..., description='The role a user in app')
    date_registration: str = Field(None, description='Date of user registration in the system')


class UserInDB:
    def __init__(self, **kwargs):
        self._id: ObjectId = kwargs['_id']
        self.email: EmailStr = kwargs['email']
        self.hash_password: str = kwargs['hash_password']
        self.role: str = kwargs['role']
        self.building_id: str = kwargs['building_id']
        self.date_registration: datetime = kwargs['date_registration']


class TokenData(BaseModel):
    email: EmailStr = None


class Token(BaseModel):
    access_token: str
    token_type: str