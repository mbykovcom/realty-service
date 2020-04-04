from fastapi import status, Body, APIRouter

from celery_app import send_email
from models.user import UserIn, UserOut, Token
import db.user as db_user
router = APIRouter()


@router.post("/registration", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def registration(user_data: UserIn = Body(
    ...,
    example={
        "email": "name@email.ru",
        "password": "password"
    })):
    result = db_user.registration(user_data)
    send_email.delay(user_data.email, title='Registering with realty-service',
                     description=f'The user {user_data.email} was created successfully.')
    return result


@router.post("/login", status_code=status.HTTP_200_OK, response_model=Token)
async def login(user_data: UserIn = Body(
    ...,
    example={
        "email": "name@email.ru",
        "password": "password"
    })):
    return db_user.login(user_data)