from fastapi import status, Body, HTTPException, APIRouter, Header

import db.requests as db_request
from utils.auth import get_current_user
from models.requests import RequestIn, RequestOut

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=RequestOut)
async def create_request(request_data: RequestIn = Body(
    ...,
    example={
        "title": "Title request",
        "description": "Description request",
        "date_receipt": "2020-03-29 14:10:00"
    }), jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    response = db_request.create_request(request_data, user._id)

    return response


@router.get("", status_code=status.HTTP_200_OK)
async def get_requests(jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    requests = db_request.get_requests(user)
    return {'requests': [request for request in requests]}


@router.get("/{request_id}", status_code=status.HTTP_200_OK)
async def get_request(request_id: str, jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    return db_request.get_request(request_id, user)


@router.patch("/{request_id}", status_code=status.HTTP_200_OK, response_model=RequestOut)
async def edit_request(request_id: str, title: str = None, description: str = None,
                       jwt: str = Header(..., example='key')) -> RequestOut:
    if get_current_user(jwt):
        if title or description:
            return db_request.edit_request(request_id, title, description)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='The Title and Description fields are empty')


@router.patch("/status/{request_id}", status_code=status.HTTP_200_OK)
async def edit_status_request(request_id: str, jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    return db_request.edit_status_request(request_id, user)
