from fastapi import status, Body, HTTPException, APIRouter, Header

from db import requests
from utils.auth import get_current_user
from models.requests import RequestIn, RequestOut

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=RequestOut)
async def create_request(request: RequestIn = Body(
    ...,
    example={
        "title": "Title request",
        "description": "Description request",
        "date_receipt": "2020-03-29 14:10:00"
    }), jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    response = requests.create_request(request, user)
    return response


@router.get("", status_code=status.HTTP_200_OK)
async def get_requests(jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    requests_ = requests.get_requests(user)
    return {'requests': [request for request in requests_]}


@router.get("/{request_id}", status_code=status.HTTP_200_OK)
async def get_request(request_id: str, jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    return requests.get_request(request_id, user)


@router.patch("/{request_id}", status_code=status.HTTP_200_OK, response_model=RequestOut)
async def edit_request(request_id: str, title: str = None, description: str = None,
                       jwt: str = Header(..., example='key')) -> RequestOut:
    user = get_current_user(jwt)
    if user:
        if title or description:
            return requests.edit_request(request_id, user, title, description)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='The Title and Description fields are empty')


@router.patch("/status/{request_id}", status_code=status.HTTP_200_OK)
async def edit_status_request(request_id: str, jwt: str = Header(..., example='key')):
    user = get_current_user(jwt)
    return requests.edit_status_request(request_id, user)
