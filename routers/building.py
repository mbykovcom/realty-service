from fastapi import status, Body, HTTPException, APIRouter, Header

from db import building
from utils.auth import get_current_user
from models.building import BuildingIn, BuildingOut

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=BuildingOut)
async def create_building(building_data: BuildingIn = Body(
    ...,
    example={
        "name": "Name building",
        "description": "Description building",
        "location": {'lat': 59.93904113769531, 'lon': 30.3157901763916},
        "square": 100.2
    }), jwt: str = Header(..., example='key')):
    if get_current_user(jwt).role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    return building.create_building(building_data)


@router.get("", status_code=status.HTTP_200_OK)
async def get_buildings(jwt: str = Header(..., example='key')):
    if get_current_user(jwt).role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    building_list = building.get_buildings()
    return {'buildings': [building_ for building_ in building_list]}


@router.get("/{building_id}", status_code=status.HTTP_200_OK)
async def get_building(building_id: str, jwt: str = Header(..., example='key')):
    if get_current_user(jwt).role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    return building.get_building(building_id)


@router.patch("/{building_id}", status_code=status.HTTP_200_OK, response_model=BuildingOut)
async def edit_request(building_id: str, name: str = None, description: str = None, square: float = None,
                       jwt: str = Header(..., example='key')) -> BuildingOut:
    if get_current_user(jwt).role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    if name or description or square:
        return building.edit_building(building_id, name, description, square)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='The Name, Description and Square fields are empty')
