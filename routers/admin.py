from fastapi import APIRouter, Body, Header, HTTPException
from starlette import status
from starlette.responses import JSONResponse

from db import building
from db import user as db_user
from models.building import BuildingIn, BuildingOut
from models.user import UserOut, UserIn
from utils.auth import get_current_user
from celery_app import send_email

router = APIRouter()


@router.post('', responses={
    201: {'model': UserOut},
    403: {}})
async def create_administrator(user_data: UserIn = Body(
    ...,
    example={
        "email": "name@email.ru",
        "password": "password",
        "building_id": 'id'
    }), jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    if user.role != 'admin':
        return JSONResponse(status_code=403, content={'detail': 'The user does not have access rights'})
    result = db_user.registration(user_data, 'administrator')
    if type(result) is not HTTPException:
        send_email.delay(user_data.email, title='Registering with realty-service',
                         description=f'The administrator {user_data.email} was created successfully.')
        return JSONResponse(status_code=201, content={'user_id': result.user_id, 'building_id': result.building_id,
                                                      'email': result.email, 'role': result.role,
                                                      'date_registration': result.date_registration})
    else:
        return JSONResponse(status_code=result.status_code, content={"detail": result.detail})


@router.get('/users', status_code=status.HTTP_200_OK)
async def get_users(jwt: str = Header(..., example='key'), role: str = None, building_id: str = None):
    user = get_current_user(jwt)
    if user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='The user does not have access rights')
    users = db_user.get_users(role, building_id)
    return {'users': users}


@router.post("/building", status_code=status.HTTP_201_CREATED, response_model=BuildingOut)
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


@router.get("/building", status_code=status.HTTP_200_OK)
async def get_buildings(jwt: str = Header(..., example='key')):
    if get_current_user(jwt).role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    building_list = building.get_buildings()
    return {'buildings': [building_ for building_ in building_list]}


@router.get("/building/{building_id}", status_code=status.HTTP_200_OK)
async def get_building(building_id: str, jwt: str = Header(..., example='key')):
    if get_current_user(jwt).role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    return building.get_building(building_id)


@router.patch("/building/{building_id}", status_code=status.HTTP_200_OK, response_model=BuildingOut)
async def edit_request(building_id: str, name: str = None, description: str = None, square: float = None,
                       jwt: str = Header(..., example='key')) -> BuildingOut:
    if get_current_user(jwt).role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    if name or description or square:
        return building.edit_building(building_id, name, description, square)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='The Name, Description and Square fields are empty')
