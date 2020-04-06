from typing import Union

from bson.objectid import ObjectId
from fastapi import HTTPException
from starlette import status

from models.requests import RequestIn, RequestOut, RequestOutEmployee, RequestOutAdmin
from models.user import UserInDB
from utils.db import user_collection, request_collection


def create_request(request: RequestIn, user_id: ObjectId) -> RequestOut:
    """Create a request

    :param request: object RequestIn with data a user for create a request
    :param user_id: id of the user creating the request
    :return: data the request
    """
    request_db = {}
    request_id = None
    try:
        request_db = {'user_id': user_id, 'employee_id': '', 'title': request.title, 'description': request.description,
                      'date_receipt': request.date_receipt, 'status': 'draft'}
        request_id = str(request_collection.insert_one(request_db).inserted_id)
    except BaseException as e:  # If an exception is raised when adding to the database
        print(f'Error: {e}')
        if request_collection:
            request_collection.remove({'_id': user_id})
    if request_id:
        return RequestOut(request_id=request_id, title=request_db['title'], description=request_db['description'],
                          status=request_db['status'], date_receipt=request_db['date_receipt'])
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to add a request')


def get_requests(user_data: UserInDB) -> list:
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
    elif user_data.role in ['admin', 'administrator']:
        cursor = request_collection.find({'status': {'$not': {'$eq': 'draft'}}})
        requests = [
            RequestOutAdmin(request_id=str(request['_id']), user_id=str(request['user_id']),
                            employee_id=str(request['employee_id']), title=request['title'],
                            description=request['description'], status=request['status'],
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
    elif user_data.role in ['admin', 'administrator']:
        request = request_collection.find_one({'$and': [
            {'_id': ObjectId(request_id)},
            {'status': {'$not': {'$eq': 'draft'}}}
        ]})
        if request:
            return RequestOutAdmin(request_id=str(request['_id']), user_id=str(request['user_id']),
                                   employee_id=request['employee_id'], title=request['title'],
                                   description=request['description'], status=request['status'],
                                   date_receipt=request['date_receipt'])
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'This request ({request_id}) does not exist')


def edit_request(request_id: str, title: str = None, description: str = None) -> RequestOut:
    """Edit request

    :param request_id: id request
    :param title: new title request
    :param description: new description request
    :return: data the request
    """
    request = request_collection.find_one({'_id': ObjectId(request_id)})
    if not request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='This user does not have request with id='
                                                                            f'{request_id}')
    status_ = request['status']
    title_ = request['title']
    description_ = request['description']
    if status_ == 'draft':
        result = 0  # The modified flag
        if title is not None and title != title_:
            result = request_collection.update_one({'_id': ObjectId(request_id)},
                                                   {'$set': {"title": title}}).modified_count
        if description is not None and description != description_:
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'The status of the request {status_}')


def edit_status_request(request_id: str,
                        user: UserInDB) -> RequestOut:  # TODO Добавить в тесты изменение статуса запроса сотрудником
    """Edit status request

    :param request_id: id request
    :param role: role the user in app
    :return: data the request
    """
    request = request_collection.find_one({'_id': ObjectId(request_id)})
    if not request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='This user does not have request with id='
                                                                            f'{request_id}')
    result = 0  # The modified flag
    if user.role == 'user' and user._id == request['user_id']:
        if request['status'] == 'draft':
            result = request_collection.update_one({'_id': ObjectId(request_id)},
                                                   {'$set': {"status": 'active'}}).modified_count
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'This request ({request_id}) '
                                                                                f'has the active status')
    elif user.role in ['admin', 'administrator'] or (user.role == 'employee' and request['employee_id'] == user._id):
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
                            detail=f'This {user.role} does not have request with id={request_id}')

    if result:
        request = request_collection.find_one({'_id': ObjectId(request_id)})
        if user.role == 'user':
            return RequestOut(request_id=str(request['_id']), title=request['title'],
                              description=request['description'], status=request['status'],
                              date_receipt=request['date_receipt'])
        elif user.role == 'employee':
            return RequestOutEmployee(request_id=str(request['_id']), user_id=str(request['user_id']),
                                      title=request['title'], description=request['description'],
                                      status=request['status'], date_receipt=request['date_receipt'])
        elif user.role in ['admin', 'administrator']:
            return RequestOutAdmin(request_id=str(request['_id']), user_id=str(request['user_id']),
                                   employee_id=request['employee_id'], title=request['title'],
                                   description=request['description'], status=request['status'],
                                   date_receipt=request['date_receipt'])
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid user')


def assign_employee_to_request(employee_id: str, request_id: str,
                               admin: UserInDB) -> Union[RequestOutAdmin, RequestOut]:
    request = get_request(request_id, admin)
    if request.status != 'active':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'This request ({request_id}) '
                                                                            f'does not have the active status')
    result = request_collection.update_one({'_id': ObjectId(request_id)},
                                           {'$set': {"employee_id": ObjectId(employee_id)}}).modified_count
    if result:
        return RequestOutAdmin(request_id=request_id, user_id=request.user_id, employee_id=employee_id,
                               title=request.title, description=request.description, status=request.status,
                               date_receipt=request.date_receipt)
    else:
        return request
