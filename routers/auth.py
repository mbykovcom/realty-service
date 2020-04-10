from fastapi import status, Body, APIRouter, HTTPException
from celery_app import send_email
from models.building import Coordinates
from models.http_exception import Error
from models.user import UserIn, UserOut, Token
from db import user
from utils.location import check_location

router = APIRouter()


@router.post("/registration", status_code=status.HTTP_201_CREATED, response_model=UserOut,
             responses={400: {'model': Error}})
async def registration(user_data: UserIn = Body(
    ...,
    example={
        "email": "name@email.ru",
        "password": "password",
        "building_id": 'id'
    }), location: dict = Body(
    ...,
    example={
        'lat': 59.93904113769531,
        'lon': 30.3157901763916
    })):
    user_location = Coordinates(lat=location['lat'], lon=location['lon'])
    if not check_location(user_data.building_id, user_location):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The user is located outside the building')
    result = user.registration(user_data)
    if type(result) is not HTTPException:
        send_email.delay(user_data.email, title='Registering with realty-service',
                         description=f'The user {user_data.email} was created successfully.')
        return UserOut(user_id=result.user_id, building_id=result.building_id, email=result.email, role=result.role,
                       date_registration=result.date_registration)
    else:
        raise HTTPException(status_code=result.status_code, detail=result.detail)


@router.post("/login", status_code=status.HTTP_200_OK, response_model=Token)
async def login(user_data: UserIn = Body(
    ...,
    example={
        "email": "name@email.ru",
        "password": "password"
    })):
    return user.login(user_data)
