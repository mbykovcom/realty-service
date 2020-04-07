from datetime import timedelta, datetime

import pymongo
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


def registration(user_data: UserIn, role: str = 'user') -> HTTPException or UserOut:
    """Registration new a user

    :param user_data: object UserIn with data a user for registration
    :param role: role the user in the app
    :return: data the user
    """
    if get_user(user_data.email):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='A user with this email already exists')
    user_db = {}
    user_id = None
    try:
        user_db = {'email': user_data.email, 'hash_password': get_password_hash(user_data.password), 'role': role,
                   'date_registration': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   'building_id': user_data.building_id}
        user_id = str(user_collection.insert_one(user_db).inserted_id)
    except BaseException as e:  # If an exception is raised when adding to the database
        print(f'Error: {e}')
        if user_collection:
            user_collection.remove({'_id': user_id})
    if user_id:
        return UserOut(user_id=user_id, email=user_db['email'], role=role,
                       date_registration=user_db['date_registration'], building_id=user_db['building_id'])
    else:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to add a user')


def login(user_data: UserIn) -> dict:
    """User authorization

    :param user_data: object UserIn with data a user for registration
    :return: Dictionary with access token and token type
    """
    user = user_collection.find_one({'email': user_data.email})
    if user:
        if verify_password(user_data.password, user['hash_password']):
            access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user_data.email}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Wrong password',
                                headers={"WWW-Authenticate": "Bearer"}, )
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='The user with this email address does not exist',
                            headers={"WWW-Authenticate": "Bearer"}, )


def get_users(role: str = None, building_id: str = None) -> list:
    """"Get all users filtered by roles or building

    :param role: role filter
    :param building_id: building filter
    :return: list users (UserOut)
    """
    filter = {}
    if role:
        if role not in ['user', 'administrator', 'employee']:
            raise HTTPException(status_code=400, detail='The wrong role')
        filter['role'] = role
    if building_id:
        filter['building_id'] = building_id
    if len(filter) != 2:
        users = user_collection.find(filter)
    else:
        users = user_collection.find({'$and': [
            {'role': filter['role']},
            {'building_id': filter['building_id']}
        ]})
    if users:
        return [UserOut(user_id=str(user['_id']), email=user['email'], role=user['role'],
                date_registration=user['date_registration'], building_id=user['building_id']) for user in users]
    else:
        return []


def get_employees(building_id: str = None) -> list:
    """Get users with the employee role

    :return: list employees (UserOut)
    """
    filter = {'role': 'employee'}
    if building_id:
        filter['building_id'] = building_id
    employees = user_collection.find(filter).sort('date_registration', pymongo.DESCENDING)
    if employees:
        return [UserOut(user_id=str(employee['_id']), email=employee['email'], role=employee['role'],
                        date_registration=employee['date_registration'],
                        building_id=employee['building_id']) for employee in employees]
    else:
        return []
