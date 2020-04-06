from collections import namedtuple

from bson import ObjectId
from pydantic import Field, BaseModel

Coordinates = namedtuple('Coordinates', ['lat', 'lon'])


class BuildingIn(BaseModel):
    location: Coordinates = Field(..., description='The coordinates of the location')
    name: str = Field(..., description='The name of the building')
    description: str = Field(..., description='Building description')
    square: float = Field(..., description='Square area of the building')


class BuildingOut(BaseModel):
    building_id: str = Field(..., description='The object that the user belongs to')
    location: Coordinates = Field(..., description='The coordinates of the location')
    name: str = Field(..., description='The name of the building')
    description: str = Field(..., description='Building description')
    square: float = Field(..., description='Square area of the building')


class BuildingInDB:
    def __init__(self, **kwargs):
        self._id: ObjectId = kwargs['_id']
        self.location: Coordinates = kwargs['location']
        self.name: str = kwargs['name']
        self.description: str = kwargs['description']
        self.square: float = kwargs['square']
