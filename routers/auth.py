from fastapi import status, Body, APIRouter

from celery_app import send_email
from models.user import UserIn, UserOut, Token
from db import user as u
router = APIRouter()


@router.post("/registration", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def registration(user: UserIn = Body(
    ...,
    example={
        "email": "name@email.ru",
        "password": "password"
    })):
    result = u.registration(user)
    send_email.delay(user.email, title='Registering with realty-service',
                     description=f'The user {user.email} was created successfully.')
    return result


@router.post("/login", status_code=status.HTTP_200_OK, response_model=Token)
async def login(user: UserIn = Body(
    ...,
    example={
        "email": "name@email.ru",
        "password": "password"
    })):
    return u.login(user)
