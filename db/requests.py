from bson.objectid import ObjectId
from fastapi import HTTPException
from starlette import status

from models.requests import RequestIn, RequestOut
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
        request_db = {'user_id': user_id, 'title': request.title, 'description': request.description,
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


def get_requests(user_id: ObjectId) -> list:
    """Get requests the user

    :param user_id: id user
    :return: request (RequestOut) list
    """
    user = user_collection.find_one({'_id': user_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User doesn\'t exists')
    if user['role'] == 'user':
        cursor = request_collection.find({'user_id': user_id})
    elif user['role'] == 'admin':
        cursor = request_collection.find({'status': {'$not': {'$eq': 'draft'}}})
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid user')
    requests = [RequestOut(request_id=str(request['_id']), title=request['title'], description=request['description'],
                           status=request['status'], date_receipt=request['date_receipt']) for request in cursor]
    if requests:
        return requests
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='This user does not have any requests')


def get_request(request_id: str, role: str = 'user') -> RequestOut:
    """ Get request by a id request

    :param request_id: id request
    :param role: role the user in app
    :return: data the request
    """
    request = None
    if role == 'user':
        request = request_collection.find_one({'_id': ObjectId(request_id)})
    elif role == 'admin':
        request = request_collection.find_one({'$and': [
            {'_id': ObjectId(request_id)},
            {'status': {'$not': {'$eq': 'draft'}}}
        ]
        })

    if request:
        return RequestOut(request_id=str(request['_id']), title=request['title'], description=request['description'],
                          status=request['status'], date_receipt=request['date_receipt'])
    elif role == 'user':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='This user does not have request with id='
                                                                            f'{request_id}')
    elif role == 'admin':
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


def edit_status_request(request_id: str, role: str) -> RequestOut:
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
    if role == 'user':
        if request['status'] == 'draft':
            result = request_collection.update_one({'_id': ObjectId(request_id)},
                                                   {'$set': {"status": 'active'}}).modified_count
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'This request ({request_id}) '
                                                                                f'has the active status')
    elif role == 'admin':
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
    if result:
        request = request_collection.find_one({'_id': ObjectId(request_id)})
        return RequestOut(request_id=str(request['_id']), title=request['title'],
                          description=request['description'], status=request['status'],
                          date_receipt=request['date_receipt'])
