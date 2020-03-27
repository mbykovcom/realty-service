from fastapi import status, Body, HTTPException

from app import app
from app.model.models import UserIn, UserOut, RequestIn, RequestOut, Token
from app.model import services
from app.model.oauth2_jwt import get_current_user


@app.post("/registration", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def registration(user: UserIn = Body(
        ...,
        example={
            "email": "name@email.ru",
            "password": "password"
        })):
    result = services.registration(user)
    services.send_email.delay(user.email, title='Registering with realty-service',
                              description=f'The user {user.email} was created successfully.')
    return result


@app.post("/login", status_code=status.HTTP_200_OK, response_model=Token)
async def login(user: UserIn = Body(
        ...,
        example={
            "email": "name@email.ru",
            "password": "password"
        })):
    return services.login(user)


@app.post("/create_request", status_code=status.HTTP_201_CREATED, response_model=RequestOut)
async def create_request(request: RequestIn = Body(
        ...,
        example={
            "email": "name@email.ru",
            "password": "password"
        }), jwt: str = Body(..., example='key')):
    user = get_current_user(jwt)
    return services.create_request(request, user._id)


@app.get("/requests", status_code=status.HTTP_200_OK)
async def get_requests(jwt: str):
    user = get_current_user(jwt)
    requests = services.get_requests(user._id)
    return {'requests': [request for request in requests]}


@app.get("/requests/{request_id}", status_code=status.HTTP_200_OK)
async def get_request(request_id: str, jwt: str):
    user = get_current_user(jwt)
    return services.get_request(request_id, user.role)


@app.put("/edit_request/{request_id}", status_code=status.HTTP_200_OK, response_model=RequestOut)
async def edit_request(request_id: str, jwt: str, title: str = None, description: str = None) -> RequestOut:
    if get_current_user(jwt):
        if title or description:
            return services.edit_request(request_id, title, description)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='The Title and Description fields are empty')


@app.put("/edit_status_request/{request_id}", status_code=status.HTTP_200_OK)
async def edit_status_request(request_id: str, jwt: str):
    user = get_current_user(jwt)
    return services.edit_status_request(request_id, user.role)