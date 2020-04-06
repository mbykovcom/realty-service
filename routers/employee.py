from fastapi import status, Body, APIRouter, HTTPException, Header

from celery_app import send_email
import db.user as db_user
import db.requests as db_requests
from models.building import Coordinates
from models.user import UserIn, UserOut
from models.requests import RequestOutAdmin
from utils.auth import get_current_user
from utils.location import check_location

router = APIRouter()


@router.post('', status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_employee(user_data: UserIn = Body(
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
    }), jwt: str = Header(..., example='key')):
    user_location = Coordinates(lat=location['lat'], lon=location['lon'])
    if not check_location(user_data.building_id, user_location):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail='The user is located outside the building')
    user = get_current_user(jwt)
    if user.role != 'administrator':
        HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    result = db_user.registration(user_data, 'employee')
    send_email.delay(user_data.email, title='Registering with realty-service',
                     description=f'The employee {user_data.email} was created successfully.')
    return result


@router.get('', status_code=status.HTTP_200_OK)
def get_employees(jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    if user.role != 'admin':
        HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    employees = db_user.get_employees()
    return {'employees': employees}


@router.patch('/assign', status_code=status.HTTP_200_OK, response_model=RequestOutAdmin)  # TODO Написать тесты
def assign_employee(employee_id: str, request_id: str, jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    if user.role != 'admin':
        HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No access rights')
    response = db_requests.assign_employee_to_request(employee_id, request_id, user)
    return response
