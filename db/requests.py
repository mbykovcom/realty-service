from typing import Union, List

from bson.objectid import ObjectId
from fastapi import HTTPException
from starlette import status

from models.requests import RequestIn, RequestOut, RequestOutEmployee, RequestOutAdmin
from models.user import UserInDB
from utils.db import request_collection, user_collection


def create_request(request: RequestIn, user_data: UserInDB) -> RequestOut:
    """Create a request

    :param request: object RequestIn with data a user for create a request
    :param user_data: user's data
    :return: data the request
    """
    request_db = {}
    try:
        request_db = {'user_id': user_data._id, 'building_id': user_data.building_id, 'employee_id': '',
                      'title': request.title, 'description': request.description,
                      'date_receipt': request.date_receipt, 'status': 'draft'}
        request_db['id'] = str(request_collection.insert_one(request_db).inserted_id)
    except BaseException as e:  # If an exception is raised when adding to the database
        print(f'Error: {e}')
        if request_collection:
            request_collection.remove({'_id': user_data._id})
    if request_db['id']:
        return RequestOut(request_id=request_db['id'], title=request_db['title'], description=request_db['description'],
                          status=request_db['status'], date_receipt=request_db['date_receipt'])
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to add a request')


def get_requests(user_data: UserInDB) -> List[Union[RequestOut, RequestOutEmployee, RequestOutAdmin]]:
    """Get requests the user

    :param user_data: object UserInDB
    :return: request (RequestOut/RequestOutEmployee/RequestOutAdmin) list
    """
    if user_data.role == 'user':
        cursor = request_collection.find({'user_id': user_data._id})
        requests = [
            RequestOut(request_id=str(request['_id']), title=request['title'], description=request['description'],
                       status=request['status'], date_receipt=request['date_receipt']) for request in cursor]
    elif user_data.role == 'employee':
        cursor = request_collection.find({'employee_id': user_data._id})
        requests = [
            RequestOutEmployee(request_id=str(request['_id']), user_id=str(request['user_id']), title=request['title'],
                               description=request['description'], status=request['status'],
                               date_receipt=request['date_receipt']) for request in cursor]
    elif user_data.role == 'administrator':
        cursor = request_collection.find({'$and': [
            {'building_id': user_data.building_id},
            {'status': {'$not': {'$eq': 'draft'}}}]})
        requests = [
            RequestOutAdmin(request_id=str(request['_id']), user_id=str(request['user_id']),
                            building_id=request['building_id'], employee_id=str(request['employee_id']),
                            title=request['title'], description=request['description'], status=request['status'],
                            date_receipt=request['date_receipt']) for request in cursor]
    elif user_data.role == 'admin':
        cursor = request_collection.find()
        requests = [
            RequestOutAdmin(request_id=str(request['_id']), user_id=str(request['user_id']),
                            building_id=request['building_id'], employee_id=str(request['employee_id']),
                            title=request['title'], description=request['description'], status=request['status'],
                            date_receipt=request['date_receipt']) for request in cursor]
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid user')
    if requests:
        return requests
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'This {user_data.role} does not have'
                                                                            ' any requests')


def get_request(request_id: str, user_data: UserInDB) -> RequestOut:
    """ Get request by a id request

    :param request_id: id request
    :param user_data: object UserInDB
    :return: data the request
    """

    if user_data.role == 'user':
        request = request_collection.find_one({'$and': [
            {'_id': ObjectId(request_id)},
            {'user_id': user_data._id}
        ]})
        if request:
            return RequestOut(request_id=str(request['_id']), title=request['title'],
                              description=request['description'], status=request['status'],
                              date_receipt=request['date_receipt'])
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='This user does not have request with '
                                                                                f'id={request_id}')
    elif user_data.role == 'employee':
        request = request_collection.find_one({'$and': [
            {'_id': ObjectId(request_id)},
            {'employee_id': user_data._id}
        ]})
        if request:
            return RequestOutEmployee(request_id=str(request['_id']), user_id=str(request['user_id']),
                                      title=request['title'], description=request['description'],
                                      status=request['status'], date_receipt=request['date_receipt'])
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'This request ({request_id}) does not exist')
    elif user_data.role == 'administrator':
        request = request_collection.find_one({'$and': [
            {'_id': ObjectId(request_id)},
            {'building_id': user_data.building_id},
            {'status': {'$not': {'$eq': 'draft'}}}
        ]})
        if request:
            return RequestOutAdmin(request_id=str(request['_id']), user_id=str(request['user_id']),
                                   building_id=request['building_id'], employee_id=request['employee_id'],
                                   title=request['title'], description=request['description'], status=request['status'],
                                   date_receipt=request['date_receipt'])
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'This request ({request_id}) does not exist')
    elif user_data.role == 'admin':
        request = request_collection.find_one({'_id': ObjectId(request_id)})
        if request:
            return RequestOutAdmin(request_id=str(request['_id']), user_id=str(request['user_id']),
                                   building_id=request['building_id'], employee_id=request['employee_id'],
                                   title=request['title'], description=request['description'], status=request['status'],
                                   date_receipt=request['date_receipt'])
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'This request ({request_id}) does not exist')


def edit_request(request_id: str, user_data: UserInDB, title: str = None, description: str = None) -> RequestOut:
    """Edit request

    :param request_id: id request
    :param user_data: object UserInDB
    :param title: new title request
    :param description: new description request
    :return: data the request
    """
    request = request_collection.find_one({'$and': [
        {'_id': ObjectId(request_id)},
        {'user_id': user_data._id}
    ]})
    if not request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='This user does not have request with id='
                                                                            f'{request_id}')
    if request['status'] == 'draft':
        result = 0  # The modified flag
        if title is not None and title != request['title']:
            result = request_collection.update_one({'_id': ObjectId(request_id)},
                                                   {'$set': {"title": title}}).modified_count
        if description is not None and description != request['description']:
            result = request_collection.update_one({'_id': ObjectId(request_id)},
                                                   {'$set': {"description": description}}).modified_count
        if result:
            request = request_collection.find_one({'_id': ObjectId(request_id)})
            return RequestOut(request_id=str(request['_id']), title=request['title'],
                              description=request['description'], status=request['status'],
                              date_receipt=request['date_receipt'])
        else:
            return RequestOut(request_id=str(request['_id']), title=request['title'],
                              description=request['description'], status=request['status'],
                              date_receipt=request['date_receipt'])
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The status of the request '
                                                                            f'{request["status"]}')


def edit_status_request(request_id: str, user_data: UserInDB) -> RequestOut:
    """Edit status request

    :param request_id: id request
    :param user_data: object UserInDB
    :return: data the request
    """
    if user_data.role == 'user':
        filter = {'$and': [
            {'_id': ObjectId(request_id)},
            {'user_id': user_data._id}
        ]}
    elif user_data.role == 'employee':
        filter = {'$and': [
            {'_id': ObjectId(request_id)},
            {'employee_id': user_data._id}
        ]}
    elif user_data.role == 'administrator':
        filter = {'$and': [
            {'_id': ObjectId(request_id)},
            {'building_id': user_data.building_id}
        ]}
    else:
        filter = {'_id': ObjectId(request_id)}
    request = request_collection.find_one(filter)
    if not request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='This user does not have request with id='
                                                                            f'{request_id}')
    result = 0  # The modified flag
    if user_data.role == 'user' and user_data._id == request['user_id']:
        if request['status'] == 'draft':
            result = request_collection.update_one({'_id': ObjectId(request_id)},
                                                   {'$set': {"status": 'active'}}).modified_count
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'This request ({request_id}) '
                                                                                f'has the active status')
    elif user_data.role in ['admin', 'administrator'] or \
            (user_data.role == 'employee' and request['employee_id'] == user_data._id):
        if request['status'] == 'active':
            result = request_collection.update_one({'_id': ObjectId(request_id)},
                                                   {'$set': {"status": 'in_progress'}}).modified_count
        elif request['status'] == 'in_progress':
            result = request_collection.update_one({'_id': ObjectId(request_id)},
                                                   {'$set': {"status": 'finished'}}).modified_count
        elif request['status'] == 'finished':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'This request ({request_id}) '
                                                                                f'has the finished status')
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'This request ({request_id}) '
                                                                                f'has the draft status')
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f'This {user_data.role} does not have request with id={request_id}')

    if result:
        request = request_collection.find_one({'_id': ObjectId(request_id)})
        if user_data.role == 'user':
            return RequestOut(request_id=str(request['_id']), title=request['title'],
                              description=request['description'], status=request['status'],
                              date_receipt=request['date_receipt'])
        elif user_data.role == 'employee':
            return RequestOutEmployee(request_id=str(request['_id']), user_id=str(request['user_id']),
                                      title=request['title'], description=request['description'],
                                      status=request['status'], date_receipt=request['date_receipt'])
        elif user_data.role in ['admin', 'administrator']:
            return RequestOutAdmin(request_id=str(request['_id']), user_id=str(request['user_id']),
                                   employee_id=request['employee_id'], title=request['title'],
                                   building_id=request['building_id'], description=request['description'],
                                   status=request['status'], date_receipt=request['date_receipt'])
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid user')


def assign_employee_to_request(employee_id: str, request_id: str,
                               admin: UserInDB) -> Union[RequestOutAdmin, RequestOut]:
    request = get_request(request_id, admin)
    employee = user_collection.find_one({'_id': ObjectId(employee_id)})
    if request is None and employee['building_id'] != admin.building_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'The discrepancy building_id')
    if request.status != 'active':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'This request ({request_id}) '
                                                                            f'does not have the active status')
    result = request_collection.update_one({'_id': ObjectId(request_id)},
                                           {'$set': {"employee_id": ObjectId(employee_id)}}).modified_count
    if result:
        return RequestOutAdmin(request_id=request_id, user_id=request.user_id, employee_id=employee_id,
                               building_id=request.building_id, title=request.title, description=request.description,
                               status=request.status, date_receipt=request.date_receipt)
    else:
        return request
