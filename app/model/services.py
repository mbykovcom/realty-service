import smtplib
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import HTTPException
from starlette import status

from app.model.models import UserIn, UserOut, UserInDB, RequestIn, RequestOut
from app import user_collection, request_collection, celery
from Config import Config
from bson.objectid import ObjectId
from app.model.oauth2_jwt import get_password_hash, verify_password, create_access_token


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
    except BaseException as e:      # If an exception is raised when adding to the database
        print(f'Error: {e}')
        if user_collection:
            user_collection.remove({'_id': user_id})
    if user_id:
        return UserOut(user_id=user_id, email=user_db['email'], role=role)
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to add a user')


@celery.task
def send_email(email, title, description) -> bool:
    """Send an email

    :param email: recipient's email address as name@email.com
    :param title: message subject
    :param description: the text of the letter
    :return: True if the email is sent, otherwise False
    """
    try:
        smtpObj = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
        smtpObj.starttls()
        smtpObj.login(Config.EMAIL, Config.EMAIL_PASSWORD)
        message = MIMEMultipart("alternative")
        message["Subject"] = title
        message["From"] = Config.EMAIL
        message["To"] = email
        msg = f"""\
                {description}"""
        message.attach(MIMEText(msg, 'plain'))
        smtpObj.sendmail(Config.EMAIL, email, message.as_string())
    except Exception as error:      # If an exception is raised when send email
        print(error)
        return False
    return True


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
    except BaseException as e:      # If an exception is raised when adding to the database
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'This request ({request_id}) does not exist')


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
        result = 0      # The modified flag
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
    result = 0      # The modified flag
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