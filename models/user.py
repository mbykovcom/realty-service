from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic.networks import EmailStr


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


class TokenData(BaseModel):
    email: EmailStr = None


class Token(BaseModel):
    access_token: str
    token_type: str
