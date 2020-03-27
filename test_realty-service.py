import unittest
from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pytest import raises

import celery_app
from app import app
from config import Config

# db_test = client_mongo['test-realty-service']
from models import requests
from models.requests import RequestIn, RequestOut
from models.user import get_user, UserIn, registration, UserOut, UserInDB, login
from utils.auth import create_access_token, get_current_user
from utils.db import user_collection, request_collection

client = TestClient(app)


class TestRoutes:

    def setup_class(cls):
        cls.admin = {'email': 'admin@example.com', 'password': 'admin'}
        cls.user = {'email': 'user@realty.ru', 'password': 'user'}
        cls.user_id = None
        cls.request = {'title': 'Test Title', 'description': 'Test Description',
                       'date_receipt': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        cls.request_id = None
        cls.jwt = {'user': None, 'admin': None}

    def teardown_class(cls):
        user_collection.delete_one({'_id': cls.user_id})
        request_collection.delete_many({'user_id': cls.user_id})

    def test_registration(self):
        response = client.post('/registration', json=self.user)
        TestRoutes.user_id = get_user(self.user['email'])._id
        assert response.status_code == 201
        assert response.json() == {"user_id": str(self.user_id),
                                   "email": self.user['email'],
                                   "role": "user"}

    def test_registration_user_exists(self):
        response = client.post('/registration', json=self.user)
        assert response.status_code == 400
        assert response.json() == {"detail": "A user with this email already exists"}

    def test_registration_no_body(self):
        response = client.post('/registration')
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "user"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

    def test_registration_without_password(self):
        response = client.post('/registration', json={'email': self.user['email']})
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "user",
                        "password"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

    def test_registration_without_email(self):
        response = client.post('/registration', json={'password': self.user['password']})
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "user",
                        "email"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

    def test_login(self):
        response = client.post('/login', json=self.user)
        TestRoutes.jwt['user'] = response.json()['access_token']
        assert response.status_code == 200
        assert list(response.json().keys()) == ['access_token', 'token_type']

    def test_login_no_body(self):
        response = client.post('/login')
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "user"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

    def test_login_without_password(self):
        response = client.post('/login', json={'email': self.user['email']})
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "user",
                        "password"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

    def test_login_without_email(self):
        response = client.post('/login', json={'password': self.user['password']})
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "user",
                        "email"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

    def test_create_request(self):
        response = client.post('/requests', json={'request': self.request, 'jwt': self.jwt['user']})
        assert response.status_code == 201
        response = response.json()
        response['date_receipt'] = str(datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": response['request_id'],
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "draft",
                            "date_receipt": self.request['date_receipt']}

    def test_create_request_no_body(self):
        response = client.post('/requests')
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "request"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                },
                {
                    "loc": [
                        "body",
                        "jwt"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]}

    def test_create_request_without_jwt(self):
        response = client.post('/requests', json={'request': self.request})
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "jwt"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]}

    def test_create_request_without_request(self):
        response = client.post('/requests', json={'jwt': self.jwt['user']})
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "request"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

    def test_create_request_without_title(self):
        response = client.post('/requests', json={'request': {'description': self.request['description'],
                                                                    'date_receipt': self.request['date_receipt']},
                                                        'jwt': self.jwt['user']})
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "request",
                        "title"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

    def test_create_request_without_description(self):
        response = client.post('/requests', json={'request': {'title': self.request['title'],
                                                                    'date_receipt': self.request['date_receipt']},
                                                        'jwt': self.jwt['user']})
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "request",
                        "description"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

    def test_create_request_without_date_receipt(self):
        response = client.post('/requests', json={'request': {'title': self.request['title'],
                                                                    'description': self.request['description']},
                                                        'jwt': self.jwt['user']})
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "request",
                        "date_receipt"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

    def test_get_requests_user(self):
        response = client.get(f"/requests?jwt={self.jwt['user']}")
        assert response.status_code == 200
        response = response.json()
        response['requests'][0]['date_receipt'] = str(
            datetime.strptime(response['requests'][0]['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert type(response['requests']) is list
        assert response == {'requests':
            [
                {"request_id": response['requests'][0]['request_id'],
                 "title": self.request['title'],
                 "description": self.request['description'],
                 "status": "draft",
                 "date_receipt": self.request['date_receipt']}
            ]
        }

    def test_get_requests_user_empty(self):
        request_collection.delete_many({'user_id': self.user_id})
        response = client.get(f"/requests?jwt={self.jwt['user']}")
        assert response.status_code == 400
        assert response.json() == {"detail": "This user does not have any requests"}

    def test_get_requests_admin_empty(self):
        response = client.post('/login', json=self.admin)
        TestRoutes.jwt['admin'] = response.json()['access_token']
        request_collection.delete_many({'user_id': self.user_id})
        response = client.get(f"/requests?jwt={self.jwt['admin']}")
        assert response.status_code == 400
        assert response.json() == {"detail": "This user does not have any requests"}

    def test_get_requests_admin(self):
        print(self.jwt['user'])
        print(self.jwt['admin'])
        response = client.post('/requests', json={'request': self.request, 'jwt': self.jwt['user']})
        TestRoutes.request_id = response.json()['request_id']
        client.patch(f"/requests/status/{self.request_id}?jwt={self.jwt['user']}")
        response = client.get(f"/requests?jwt={self.jwt['admin']}")
        response = response.json()
        print(response)
        assert type(response['requests']) is list
        response['requests'][0]['date_receipt'] = str(
            datetime.strptime(response['requests'][0]['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {'requests':
            [
                {"request_id": response['requests'][0]['request_id'],
                 "title": self.request['title'],
                 "description": self.request['description'],
                 "status": "active",
                 "date_receipt": self.request['date_receipt']}
            ]
        }

    def test_get_request_user(self):
        response = client.get(f"/requests/{self.request_id}?jwt={self.jwt['user']}")
        assert response.status_code == 200
        response = response.json()
        response['date_receipt'] = str(
            datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": self.request_id,
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "active",
                            "date_receipt": self.request['date_receipt']}

    def test_get_request_admin(self):
        response = client.get(f"/requests/{self.request_id}?jwt={self.jwt['admin']}")
        assert response.status_code == 200
        response = response.json()
        response['date_receipt'] = str(
            datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": self.request_id,
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "active",
                            "date_receipt": self.request['date_receipt']}

    def test_get_request_user_not_exist(self):
        request_id = '5e7bfee773467953a87e467a'
        response = client.get(f"/requests/{request_id}?jwt={self.jwt['user']}")
        assert response.status_code == 400
        assert response.json() == {"detail": "This user does not have request with id=5e7bfee773467953a87e467a"}

    def test_get_request_admin_not_exist(self):
        request_id = '5e7bfee773467953a87e467a'
        response = client.get(f"/requests/{request_id}?jwt={self.jwt['admin']}")
        assert response.status_code == 400
        assert response.json() == {"detail": f"This request ({request_id}) does not exist"}

    def test_edit_request_nothing(self):
        response = client.patch(f"/requests/{self.request_id}?jwt={self.jwt['user']}")
        assert response.status_code == 400
        assert response.json() == {"detail": "The Title and Description fields are empty"}

    def test_edit_request_active(self):
        self.request['title'] = 'New Title'
        response = client.patch(f"/requests/{self.request_id}?jwt={self.jwt['user']}&title={self.request['title']}")
        assert response.status_code == 400
        assert response.json() == {"detail": "The status of the request active"}

    def test_edit_request_title(self):
        response = client.post('/requests', json={'request': self.request, 'jwt': self.jwt['user']})
        TestRoutes.request_id = response.json()['request_id']

        self.request['title'] = 'New Title'
        response = client.patch(f"/requests/{self.request_id}?jwt={self.jwt['user']}&title={self.request['title']}")
        assert response.status_code == 200
        response = response.json()
        response['date_receipt'] = str(datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": self.request_id,
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "draft",
                            "date_receipt": self.request['date_receipt']}

    def test_edit_request_decription(self):
        self.request['description'] = 'New Description'
        response = client.patch(f"/requests/{self.request_id}?jwt={self.jwt['user']}&"
                              f"description={self.request['description']}")
        assert response.status_code == 200
        response = response.json()
        response['date_receipt'] = str(datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": self.request_id,
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "draft",
                            "date_receipt": self.request['date_receipt']}

    def test_edit_request_full(self):
        self.request['title'] = 'New Title 2'
        self.request['description'] = 'New Description 2'
        response = client.patch(f"/requests/{self.request_id}?jwt={self.jwt['user']}&title={self.request['title']}&"
                              f"description={self.request['description']}")
        assert response.status_code == 200
        response = response.json()
        response['date_receipt'] = str(datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": self.request_id,
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "draft",
                            "date_receipt": self.request['date_receipt']}

    def test_edit_status_request_active(self):
        response = client.patch(f"/requests/status/{self.request_id}?jwt={self.jwt['user']}")
        assert response.status_code == 200
        response = response.json()
        response['date_receipt'] = str(
            datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": self.request_id,
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "active",
                            "date_receipt": self.request['date_receipt']}

    def test_edit_status_request_active_again(self):
        response = client.patch(f"/requests/status/{self.request_id}?jwt={self.jwt['user']}")
        assert response.status_code == 400
        assert response.json() == {"detail": f'This request ({self.request_id}) has the active status'}

    def test_edit_status_request_in_progress(self):
        response = client.patch(f"/requests/status/{self.request_id}?jwt={self.jwt['admin']}")
        assert response.status_code == 200
        response = response.json()
        response['date_receipt'] = str(
            datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": self.request_id,
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "in_progress",
                            "date_receipt": self.request['date_receipt']}

    def test_edit_status_request_finished(self):
        response = client.patch(f"/requests/status/{self.request_id}?jwt={self.jwt['admin']}")
        assert response.status_code == 200
        response = response.json()
        response['date_receipt'] = str(
            datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": self.request_id,
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "finished",
                            "date_receipt": self.request['date_receipt']}

    def test_edit_status_request_finished_again(self):
        response = client.patch(f"/requests/status/{self.request_id}?jwt={self.jwt['admin']}")
        assert response.status_code == 400
        assert response.json() == {"detail": f'This request ({self.request_id}) has the finished status'}


class TestService:

    def setup_class(cls):
        cls.admin = {'_id': None, 'email': 'newadmin@example.com', 'password': 'admin', 'hash_password': None,
                     'role': 'admin'}
        cls.user = {'_id': None, 'email': 'newuser@example.com', 'password': 'string',
                    'hash_password': '$2b$12$kA8/n5wl1WntvWujhnKhLehH4NC3uDjuI.wS0ieuGNq7u.yleO19u',
                    'role': 'user'}
        cls.request = {'_id': None, 'title': 'Test Title', 'description': 'Test Description',
                       'date_receipt': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'status': None}
        cls.jwt = {'user': None, 'admin': None}
        cls.user_in = UserIn(email=cls.user['email'], password=cls.user['password'])
        cls.new_user = UserIn(email='newuser@example.com', password=cls.user['password'])
        cls.new_admin = UserIn(email='newadmin@example.com', password=cls.admin['password'])
        cls.admin_in = UserIn(email=cls.admin['email'], password=cls.admin['password'])
        cls.request_in = RequestIn(title=cls.request['title'], description=cls.request['description'],
                                   date_receipt=cls.request['date_receipt'])
        cls.user_in_db = UserInDB(_id=cls.user['_id'], email=cls.user['email'],
                                  hash_password=cls.user['hash_password'], role=cls.user['role'])
        cls.incorrect_user_id = '5e7c92cf6e66c5e9a8b9e005'
        cls.incorrect_request_id = '5e7c92cf6e66c5e9a8b9e005'

    def teardown_class(cls):
        user_collection.delete_one({'_id': ObjectId(cls.user['_id'])})
        request_collection.delete_many({'user_id': ObjectId(cls.user['_id'])})
        user_collection.delete_one({'_id': ObjectId(cls.admin['_id'])})
        request_collection.delete_many({'user_id': ObjectId(cls.admin['_id'])})

    def test_registration_user(self):
        role = 'user'
        result = registration(self.new_user)
        TestService.user['_id'] = result.user_id
        assert type(result) is UserOut
        assert result.role == role

    def test_registration_user_exists(self):
        with raises(HTTPException):
            assert registration(self.new_user)

    def test_registration_admin(self):
        role = 'admin'
        result = registration(self.new_admin, role='admin')
        TestService.admin['_id'] = result.user_id
        assert type(result) is UserOut
        assert result.role == role

    def test_get_user(self):
        result = get_user(self.user['email'])
        assert type(result) is UserInDB

    def test_get_user_not_exist(self):
        email = 'not_exit@gmail.com'
        result = get_user(email)
        assert result is None

    def test_send_email(self):
        result = celery_app.send_email('bykov@appvelox.ru', 'Test', 'Test')
        assert result is True

    def test_login(self):
        result = login(self.user_in)
        assert result['access_token'] is not None

    def test_login_user_doesnt_exists(self):
        with raises(HTTPException):
            user = UserIn(email='not_exists@gmail.com', password='password')
            assert login(user)

    def test_login_user_incorrect_data(self):
        with raises(HTTPException):
            user = self.user_in
            user.email = 'not_exit@gmail.com'
            assert login(user)

    def test_create_request(self):
        result = requests.create_request(self.request_in, ObjectId(self.user['_id']))
        TestService.request['_id'] = result.request_id
        TestService.request['status'] = result.status
        assert type(result) is RequestOut

    def test_get_requests(self):
        result = requests.get_requests(ObjectId(self.user['_id']))
        assert type(result) is list

    def test_get_requests_incorrect_user_id(self):
        with raises(HTTPException):
            assert requests.get_requests(ObjectId(self.incorrect_user_id))

    def test_get_request(self):
        result = requests.get_request(self.request['_id'])
        assert type(result) is RequestOut

    def test_get_request_doesnt_exists(self):
        with raises(HTTPException):
            assert requests.get_request(self.incorrect_request_id)

    def test_edit_request(self):
        result = requests.edit_request(self.request['_id'])
        assert type(result) is RequestOut
        result = requests.edit_request(self.request['_id'], title='Title')
        assert result.title == 'Title'
        result = requests.edit_request(self.request['_id'], description='Description')
        assert result.description == 'Description'

    def test_edit_status_request_user(self):
        result = requests.edit_status_request(self.request['_id'], 'user')
        assert result.status == 'active'

    def test_edit_status_request_user_status_active(self):
        with raises(HTTPException):
            assert requests.edit_status_request(self.request['_id'], 'user')

    def test_edit_request_status_not_draft(self):
        with raises(HTTPException):
            assert requests.edit_request(self.request['_id'], title='Title', description='Description')

    def test_edit_status_request_admin(self):
        result = requests.edit_status_request(self.request['_id'], 'admin')
        assert result.status == 'in_progress'

    def test_edit_status_request_admin_status_in_progress(self):
        result = requests.edit_status_request(self.request['_id'], 'admin')
        assert result.status == 'finished'

    def test_edit_status_request_admin_status_finished(self):
        with raises(HTTPException):
            assert requests.edit_status_request(self.request['_id'], 'admin')


class TestOAuth:

    def setup_class(cls):
        cls.email = 'admin@example.com'
        cls.jwt = None
        cls.access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)

    def test_create_access_token(self):
        access_token = create_access_token(data={"sub": self.email},
                                                 expires_delta=self.access_token_expires)
        assert access_token.decode() is not None
        TestOAuth.jwt = access_token.decode()

    def test_get_current_user(self):
        result = get_current_user(self.jwt)
        assert type(result) is UserInDB

    def test_get_current_user_no_email(self):
        access_token = create_access_token(data={}, expires_delta=self.access_token_expires)
        with raises(HTTPException):
            assert get_current_user(access_token.decode())

    def test_get_current_user_doesnt_exists(self):
        access_token = create_access_token(data={'sub': 'not_exists@email.ru'},
                                                 expires_delta=self.access_token_expires)
        with raises(HTTPException):
            assert get_current_user(access_token.decode())


if __name__ == '__main__':
    unittest.main()
