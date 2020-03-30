from datetime import timedelta

from fastapi import HTTPException
from starlette import status

from config import Config
from models.user import UserIn, UserOut, UserInDB
from utils.auth import get_password_hash, verify_password, create_access_token
from utils.db import user_collection


def get_user(email: str) -> UserInDB:
    """ Get a user by email

    :param email: email user as name@email.com
    :return: data the user or nothing if the user doesn`t exists
    """
    user_data = user_collection.find_one({'email': email})
    if user_data:
        return UserInDB(**user_data)


def registration(user_: UserIn, role: str = 'user') -> UserOut:
    """Registration new a user

    :param user_: object UserIn with data a user for registration
    :param role: role the user in the app
    :return: data the user
    """
    if get_user(user_.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='A user with this email already exists')
    user_db = {}
    user_id = None
    try:
        user_db = {'email': user_.email, 'hash_password': get_password_hash(user_.password), 'role': role}
        user_id = str(user_collection.insert_one(user_db).inserted_id)
    except BaseException as e:  # If an exception is raised when adding to the database
        print(f'Error: {e}')
        if user_collection:
            user_collection.remove({'_id': user_id})
    if user_id:
        return UserOut(user_id=user_id, email=user_db['email'], role=role)
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to add a user')


def login(user_: UserIn) -> dict:
    """User authorization

    :param user_: object UserIn with data a user for registration
    :return: Dictionary with access token and token type
    """
    user_data = user_collection.find_one({'email': user_.email})
    if user_data:
        if verify_password(user_.password, user_data['hash_password']):
            access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user_.email}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Wrong password',
                                headers={"WWW-Authenticate": "Bearer"}, )
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='The user with this email address does not exist',
                            headers={"WWW-Authenticate": "Bearer"}, )
