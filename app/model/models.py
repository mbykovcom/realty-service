from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr


class UserIn(BaseModel):
    email: EmailStr = Field(..., description='The email a user')
    password: str = Field(..., description='The password a user', min_length=4)


class UserOut(BaseModel):
    user_id: str = Field(..., description='The id a user')
    email: EmailStr = Field(..., description='The email a user')
    role: str = Field(..., description='The role a user in app')


class UserInDB:
    def __init__(self, **kwargs):
        self._id: ObjectId = kwargs['_id']
        self.email: EmailStr = kwargs['email']
        self.hash_password: str = kwargs['hash_password']
        self.role: str = kwargs['role']


class RequestIn(BaseModel):
    title: str = Field(..., description='The title of a request', min_length=2)
    description: str = Field(..., description='The description of a request', min_length=5)
    date_receipt: datetime = Field(..., description='Date and time the request was created')


class RequestOut(BaseModel):
    request_id: str
    title: str = Field(..., description='The title of a request', min_length=2)
    description: str = Field(..., description='The description of a request', min_length=10)
    status: str = Field('draft', description='The status of a request', min_length=4)
    date_receipt: datetime = Field(..., description='Date and time the request was created')


class RequestInDB:
    def __init__(self, **kwargs):
        self._id: ObjectId = kwargs['_id']
        self.user_id: str = kwargs['user_id']
        self.title: str = kwargs['title']
        self.description: str = kwargs['description']
        self.status: str = kwargs['status']
        self.date_receipt: datetime = kwargs['date_receipt']


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: EmailStr = None
