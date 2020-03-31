from datetime import datetime

from bson.objectid import ObjectId
from pydantic import BaseModel, Field


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


class RequestOutEmployee(RequestOut):
    user_id: str


class RequestOutAdmin(RequestOut):
    user_id: str
    employee_id: str


class RequestInDB:
    def __init__(self, **kwargs):
        self._id: ObjectId = kwargs['_id']
        self.user_id: str = kwargs['user_id']
        self.employee_id = kwargs['employee_id']
        self.title: str = kwargs['title']
        self.description: str = kwargs['description']
        self.status: str = kwargs['status']
        self.date_receipt: datetime = kwargs['date_receipt']
