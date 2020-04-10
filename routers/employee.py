from typing import List

from fastapi import status, Body, APIRouter, HTTPException, Header

from celery_app import send_email
import db.user as db_user
import db.requests as db_requests
from models.http_exception import Error
from models.user import UserIn, UserOut
from models.requests import RequestOutAdmin
from utils.auth import get_current_user

router = APIRouter()


@router.post('', status_code=status.HTTP_201_CREATED, response_model=UserOut,
             responses={401: {'model': Error}, 403: {'model': Error}})
async def create_employee(user_data: UserIn = Body(
    ...,
    example={
        "email": "name@email.ru",
        "password": "password",
        "building_id": 'id'
    }), jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    if user.role not in ['admin', 'administrator']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    user_data.building_id = user.building_id
    result = db_user.registration(user_data, 'employee')
    send_email.delay(user_data.email, title='Registering with realty-service',
                     description=f'The employee {user_data.email} was created successfully.')
    return result


@router.get('', status_code=status.HTTP_200_OK, response_model=List[UserOut],
            responses={401: {'model': Error}, 403: {'model': Error}})
async def get_employees(jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    if user.role not in ['admin', 'administrator']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    employees = db_user.get_employees(user.building_id)
    return employees


@router.patch('/assign', status_code=status.HTTP_200_OK, response_model=RequestOutAdmin,
              responses={401: {'model': Error}, 403: {'model': Error}})
async def assign_employee(employee_id: str, request_id: str, jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    if user.role not in ['admin', 'administrator']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    response = db_requests.assign_employee_to_request(employee_id, request_id, user)
    return response
