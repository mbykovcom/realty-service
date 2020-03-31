import time
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
from db import requests
from models.requests import RequestIn, RequestOut, RequestOutAdmin, RequestOutEmployee
from models.user import UserIn, UserOut, UserInDB
from db.user import get_user, registration, login, get_employees
from utils.auth import create_access_token, get_current_user, get_password_hash
from utils.db import user_collection, request_collection

client = TestClient(app)


class TestRoutes:

    def setup_class(cls):
        cls.admin = {'email': 'admin@example.com', 'password': 'admin'}
        cls.user = {'email': 'user@realty.ru', 'password': 'user'}
        cls.user_id = None
        cls.employee = {'email': 'employee@realty.ru', 'password': 'employee'}
        cls.employee_id = None
        cls.request = {'title': 'Test Title', 'description': 'Test Description',
                       'date_receipt': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        cls.request_id = None
        cls.jwt = {'user': None, 'admin': None, 'employee': None}

    def teardown_class(cls):
        user_collection.delete_one({'_id': cls.user_id})
        user_collection.delete_many({'role': 'employee'})
        request_collection.delete_many({'user_id': cls.user_id})

    def test_registration_user(self):
        response = client.post('/registration', json=self.user)
        TestRoutes.user_id = get_user(self.user['email'])._id
        assert response.status_code == 201
        assert response.json() == {"user_id": str(self.user_id),
                                   "email": self.user['email'],
                                   "role": "user",
                                   "date_registration": response.json()['date_registration']}

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
        headers = {'jwt': self.jwt['user']}
        response = client.post('/requests', json=self.request, headers=headers)
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
                        "header",
                        "jwt"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                },
                {
                    "loc": [
                        "body",
                        "request"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]}

    def test_create_request_without_jwt(self):
        response = client.post('/requests', json=self.request)
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "header",
                        "jwt"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]}

    def test_create_request_without_request(self):
        headers = {'jwt': self.jwt['user']}
        response = client.post('/requests', headers=headers)
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {'loc': ['body', 'request'],
                 'msg': 'field required',
                 'type': 'value_error.missing'}
            ]
        }

    def test_create_request_without_title(self):
        headers = {'jwt': self.jwt['user']}
        response = client.post('/requests', json={'description': self.request['description'],
                                                  'date_receipt': self.request['date_receipt']}, headers=headers)
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
        headers = {'jwt': self.jwt['user']}
        response = client.post('/requests', json={'title': self.request['title'],
                                                  'date_receipt': self.request['date_receipt']}, headers=headers)
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
        headers = {'jwt': self.jwt['user']}
        response = client.post('/requests', json={'title': self.request['title'],
                                                  'description': self.request['description']}, headers=headers)
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
        headers = {'jwt': self.jwt['user']}
        response = client.get(f"/requests", headers=headers)
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
        headers = {'jwt': self.jwt['user']}
        request_collection.delete_many({'user_id': self.user_id})
        response = client.get(f"/requests", headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "This user does not have any requests"}

    def test_get_requests_admin_empty(self):
        response = client.post('/login', json=self.admin)
        TestRoutes.jwt['admin'] = response.json()['access_token']
        print(self.user_id)
        request_collection.delete_many({'user_id': self.user_id})
        headers = {'jwt': self.jwt['admin']}
        response = client.get(f"/requests", headers=headers)
        print(response.json())
        assert response.status_code == 400
        assert response.json() == {"detail": "This admin does not have any requests"}

    def test_get_requests_admin(self):
        headers = {'jwt': self.jwt['user']}
        response = client.post('/requests', json=self.request, headers=headers)
        TestRoutes.request_id = response.json()['request_id']
        headers = {'jwt': self.jwt['user']}
        client.patch(f"/requests/status/{self.request_id}", headers=headers)
        headers['jwt'] = self.jwt['admin']
        response = client.get(f"/requests", headers=headers)
        response = response.json()
        assert type(response['requests']) is list
        response['requests'][0]['date_receipt'] = str(
            datetime.strptime(response['requests'][0]['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {'requests':
            [
                {"request_id": response['requests'][0]['request_id'],
                 "user_id": response['requests'][0]['user_id'],
                 "title": self.request['title'],
                 "description": self.request['description'],
                 "employee_id": "",
                 "status": "active",
                 "date_receipt": self.request['date_receipt']}
            ]
        }

    def test_get_request_user(self):
        headers = {'jwt': self.jwt['user']}
        response = client.get(f"/requests/{self.request_id}", headers=headers)
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
        headers = {'jwt': self.jwt['admin']}
        response = client.get(f"/requests/{self.request_id}", headers=headers)
        assert response.status_code == 200
        response = response.json()
        response['date_receipt'] = str(
            datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": self.request_id,
                            "user_id": response['user_id'],
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "employee_id": "",
                            "status": "active",
                            "date_receipt": self.request['date_receipt']}

    def test_get_request_user_not_exist(self):
        request_id = '5e7bfee773467953a87e467a'
        headers = {'jwt': self.jwt['user']}
        response = client.get(f"/requests/{request_id}", headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "This user does not have request with id=5e7bfee773467953a87e467a"}

    def test_get_request_admin_not_exist(self):
        request_id = '5e7bfee773467953a87e467a'
        headers = {'jwt': self.jwt['admin']}
        response = client.get(f"/requests/{request_id}", headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": f"This request ({request_id}) does not exist"}

    def test_edit_request_nothing(self):
        headers = {'jwt': self.jwt['user']}
        response = client.patch(f"/requests/{self.request_id}", headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "The Title and Description fields are empty"}

    def test_edit_request_active(self):
        self.request['title'] = 'New Title'
        headers = {'jwt': self.jwt['user']}
        response = client.patch(f"/requests/{self.request_id}?title={self.request['title']}", headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "The status of the request active"}

    def test_edit_request_title(self):
        headers = {'jwt': self.jwt['user']}
        response = client.post('/requests', json=self.request, headers=headers)
        TestRoutes.request_id = response.json()['request_id']

        self.request['title'] = 'New Title'
        response = client.patch(f"/requests/{self.request_id}?title={self.request['title']}", headers=headers)
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
        headers = {'jwt': self.jwt['user']}
        response = client.patch(f"/requests/{self.request_id}?description={self.request['description']}",
                                headers=headers)
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
        headers = {'jwt': self.jwt['user']}
        response = client.patch(f"/requests/{self.request_id}?title={self.request['title']}&"
                                f"description={self.request['description']}", headers=headers)
        assert response.status_code == 200
        response = response.json()
        response['date_receipt'] = str(datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": self.request_id,
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "draft",
                            "date_receipt": self.request['date_receipt']}

    def test_edit_status_request_active(self):
        headers = {'jwt': self.jwt['user']}
        response = client.patch(f"/requests/status/{self.request_id}", headers=headers)
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
        headers = {'jwt': self.jwt['user']}
        response = client.patch(f"/requests/status/{self.request_id}", headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": f'This request ({self.request_id}) has the active status'}

    def test_edit_status_request_in_progress(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.patch(f"/requests/status/{self.request_id}", headers=headers)
        assert response.status_code == 200
        response = response.json()
        response['date_receipt'] = str(
            datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": self.request_id,
                            'user_id': response['user_id'],
                            "employee_id": "",
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "in_progress",
                            "date_receipt": self.request['date_receipt']}

    def test_edit_status_request_finished(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.patch(f"/requests/status/{self.request_id}", headers=headers)
        assert response.status_code == 200
        response = response.json()
        response['date_receipt'] = str(
            datetime.strptime(response['date_receipt'], '%Y-%m-%dT%H:%M:%S'))
        assert response == {"request_id": self.request_id,
                            'user_id': response['user_id'],
                            "employee_id": "",
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "finished",
                            "date_receipt": self.request['date_receipt']}

    def test_edit_status_request_finished_again(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.patch(f"/requests/status/{self.request_id}", headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": f'This request ({self.request_id}) has the finished status'}

    def test_registration_employee(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.post('/employee', json=self.employee, headers=headers)
        TestRoutes.employee_id = get_user(self.employee['email'])._id
        assert response.status_code == 201
        assert response.json() == {"user_id": response.json()['user_id'],
                                   "email": self.employee['email'],
                                   "role": "employee",
                                   "date_registration": response.json()['date_registration']}

    def test_get_employees(self):
        headers = {'jwt': self.jwt['admin']}
        new_employee = self.employee.copy()
        time.sleep(1)
        new_employee['email'] = 'new_employee@realty.ru'
        client.post('/employee', json=new_employee, headers=headers)
        response = client.get('/employee', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert len(response['employees']) == 2
        assert response['employees'][0] == {'date_registration': response['employees'][0]['date_registration'],
                                            'email': new_employee['email'],
                                            'role': 'employee',
                                            'user_id': response['employees'][0]['user_id']}

    def test_employee_get_requests_empty(self):
        response = client.post('/login', json=self.employee)
        TestRoutes.jwt['employee'] = response.json()['access_token']
        headers = {'jwt': self.jwt['employee']}
        response = client.get('/requests', headers=headers)
        assert response.status_code == 400
        assert response.json() == {'detail': 'This employee does not have any requests'}

    def test_assign_employee(self):
        headers = {'jwt': self.jwt['user']}
        request_id = client.post('/requests', json=self.request, headers=headers).json()['request_id']
        client.patch(f'/requests/status/{request_id}', headers=headers).json()
        headers['jwt'] = self.jwt['admin']
        response = client.patch(f"/employee/assign?employee_id={self.employee_id}&request_id={request_id}",
                                headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response == {"request_id": response['request_id'],
                            'user_id': response['user_id'],
                            "employee_id": str(self.employee_id),
                            "title": self.request['title'],
                            "description": self.request['description'],
                            "status": "active",
                            "date_receipt": response['date_receipt']}

    def test_employee_get_requests(self):
        headers = {'jwt': self.jwt['employee']}
        response = client.get('/requests', headers=headers)
        assert response.status_code == 200
        response = response.json()
        TestRoutes.request_id = response['requests'][0]['request_id']
        assert response == {'requests': [{
            'date_receipt': response['requests'][0]['date_receipt'],
            'description': self.request['description'],
            'request_id': response['requests'][0]['request_id'],
            'status': response['requests'][0]['status'],
            'title': self.request['title'],
            'user_id': response['requests'][0]['user_id']}]}

    def test_employee_get_request(self):
        headers = {'jwt': self.jwt['employee']}
        response = client.get(f'/requests/{self.request_id}', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response == {
            'date_receipt': response['date_receipt'],
            'description': self.request['description'],
            'request_id': response['request_id'],
            'status': response['status'],
            'title': self.request['title'],
            'user_id': response['user_id']}


class TestService:

    def setup_class(cls):
        cls.admin = {'_id': None, 'email': 'newadmin@example.com', 'password': 'admin', 'hash_password': None,
                     'role': 'admin', "date_registration": None}
        cls.user = {'_id': None, 'email': 'newuser@example.com', 'password': 'string',
                    'hash_password': None, 'role': 'user', "date_registration": None}
        cls.employee = {'_id': None, 'email': 'employee@example.com', 'password': 'password',
                        'hash_password': None, 'role': 'employee', "date_registration": None}
        cls.request = {'_id': None, 'title': 'Test Title', 'description': 'Test Description',
                       'date_receipt': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'status': None}
        cls.jwt = {'user': None, 'admin': None, 'employee': None}

        cls.admin_in = UserIn(email=cls.admin['email'], password=cls.admin['password'])
        cls.user_in = UserIn(email=cls.user['email'], password=cls.user['password'])
        cls.employee_in = UserIn(email=cls.employee['email'], password=cls.employee['password'])
        cls.request_in = RequestIn(title=cls.request['title'], description=cls.request['description'],
                                   date_receipt=cls.request['date_receipt'])

        cls.new_user = UserIn(email='newuser@example.com', password=cls.user['password'])
        cls.new_admin = UserIn(email='newadmin@example.com', password=cls.admin['password'])

        cls.admin_in_db = UserInDB(_id=cls.admin['_id'], email=cls.admin['email'],
                                   hash_password=cls.admin['hash_password'], role=cls.admin['role'],
                                   date_registration=cls.admin['date_registration'])
        cls.user_in_db = UserInDB(_id=cls.user['_id'], email=cls.user['email'],
                                  hash_password=cls.user['hash_password'], role=cls.user['role'],
                                  date_registration=cls.user['date_registration'])
        cls.employee_in_db = UserInDB(_id=cls.employee['_id'], email=cls.employee['email'],
                                      hash_password=cls.employee['hash_password'], role=cls.employee['role'],
                                      date_registration=cls.employee['date_registration'])

        cls.incorrect_user_id = '5e7c92cf6e66c5e9a8b9e005'
        cls.incorrect_request_id = '5e7c92cf6e66c5e9a8b9e005'

    def teardown_class(cls):
        print(user_collection.delete_many({'role': cls.user['role']}).deleted_count)
        print(user_collection.delete_one({'_id': ObjectId(cls.admin['_id'])}).deleted_count)
        print(user_collection.delete_many({'role': cls.employee['role']}).deleted_count)
        print(request_collection.delete_many({'user_id': ObjectId(cls.user['_id'])}).deleted_count)
        print(request_collection.delete_many({'user_id': ObjectId(cls.admin['_id'])}).deleted_count)

    def test_registration_user(self):
        role = 'user'
        result = registration(self.new_user)
        TestService.user['_id'] = result.user_id
        TestService.user['hash_password'] = get_password_hash(self.user['password'])
        TestService.user['date_registration'] = TestService.user_in_db.date_registration = result.date_registration
        assert type(result) is UserOut
        assert result.role == role

    def test_registration_user_exists(self):
        with raises(HTTPException):
            assert registration(self.new_user)

    def test_registration_admin(self):
        role = 'admin'
        result = registration(self.new_admin, role='admin')
        TestService.admin['_id'] = result.user_id
        TestService.admin['hash_password'] = get_password_hash(self.admin['password'])
        TestService.admin['date_registration'] = result.date_registration
        assert type(result) is UserOut
        assert result.role == role

    def test_get_user(self):
        result = get_user(self.user['email'])
        assert type(result) is UserInDB

    def test_get_user_not_exists(self):
        email = 'not_exists@gmail.com'
        result = get_user(email)
        assert result is None

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
        print(self.user['_id'])
        result = requests.create_request(self.request_in, ObjectId(self.user['_id']))
        TestService.request['_id'] = result.request_id
        TestService.request['status'] = result.status
        assert type(result) is RequestOut

    def test_get_requests(self):
        TestService.user_in_db._id = ObjectId(self.user['_id'])
        result = requests.get_requests(self.user_in_db)
        assert type(result) is list

    def test_get_request(self):
        result = requests.get_request(self.request['_id'], self.user_in_db)
        assert type(result) is RequestOut

    def test_get_request_doesnt_exists(self):
        with raises(HTTPException):
            assert requests.get_request(self.incorrect_request_id, self.user_in_db)

    def test_get_requests_incorrect_user_id(self):
        with raises(HTTPException):
            user = UserInDB(_id=self.incorrect_user_id, email=self.user['email'],
                            hash_password=self.user['hash_password'], role=self.user['role'],
                            date_registration=self.user['date_registration'])
            assert requests.get_requests(user)

    def test_edit_request(self):
        result = requests.edit_request(self.request['_id'])
        assert type(result) is RequestOut
        result = requests.edit_request(self.request['_id'], title='Title')
        assert result.title == 'Title'
        result = requests.edit_request(self.request['_id'], description='Description')
        assert result.description == 'Description'

    def test_edit_status_request_user(self):
        result = requests.edit_status_request(self.request['_id'], self.user_in_db)
        assert result.status == 'active'

    def test_edit_status_request_user_status_active(self):
        with raises(HTTPException):
            assert requests.edit_status_request(self.request['_id'], self.user_in_db)

    def test_edit_request_status_not_draft(self):
        with raises(HTTPException):
            assert requests.edit_request(self.request['_id'], title='Title', description='Description')

    def test_edit_status_request_admin(self):
        result = requests.edit_status_request(self.request['_id'], self.admin_in_db)
        assert result.status == 'in_progress'

    def test_edit_status_request_admin_status_in_progress(self):
        result = requests.edit_status_request(self.request['_id'], self.admin_in_db)
        assert result.status == 'finished'

    def test_edit_status_request_admin_status_finished(self):
        with raises(HTTPException):
            assert requests.edit_status_request(self.request['_id'], self.admin_in_db)

    def test_admin_get_employees_empty(self):
        result = get_employees()
        assert len(result) == 0

    def test_create_employee(self):
        self.employee_in.email = 'employee1@realty.com'
        registration(self.employee_in, self.employee['role'])
        time.sleep(1)
        self.employee_in.email = self.employee['email']
        result = registration(self.employee_in, self.employee['role'])
        TestService.employee['_id'] = result.user_id
        TestService.employee_in_db._id = ObjectId(result.user_id)
        TestService.employee['hash_password'] = get_password_hash(self.user['password'])
        TestService.employee[
            'date_registration'] = TestService.employee_in_db.date_registration = result.date_registration
        assert type(result) is UserOut
        assert result.role == self.employee['role']

    def test_admin_get_employees(self):
        result = get_employees()
        assert type(result[0]) is UserOut
        assert result[0].user_id == self.employee['_id']

    def test_assign_employee_to_request_not_active(self):
        with raises(HTTPException):
            assert requests.assign_employee_to_request(self.employee['_id'], self.request['_id'], self.admin_in_db)

    def test_assign_employee_to_request(self):
        TestService.request['_id'] = requests.create_request(self.request_in, self.user_in_db._id).request_id
        requests.edit_status_request(self.request['_id'], self.user_in_db)
        result = requests.assign_employee_to_request(self.employee['_id'], self.request['_id'], self.admin_in_db)
        assert result == RequestOutAdmin(request_id=self.request['_id'], user_id=result.user_id,
                                         employee_id=self.employee['_id'], title=self.request['title'],
                                         description=self.request['description'], status='active',
                                         date_receipt=self.request['date_receipt'])

    def test_employee_get_requests(self):
        result = requests.get_requests(self.employee_in_db)
        assert len(result) == 1
        assert result[0] == RequestOutEmployee(request_id=self.request['_id'], user_id=self.user['_id'],
                                               title=self.request['title'], description=self.request['description'],
                                               status='active', date_receipt=self.request['date_receipt'])

    def test_employee_get_request(self):
        result = requests.get_request(self.request['_id'], self.employee_in_db)
        assert result == RequestOutEmployee(request_id=self.request['_id'], user_id=self.user['_id'],
                                            title=self.request['title'], description=self.request['description'],
                                            status='active', date_receipt=self.request['date_receipt'])

    def test_employee_edit_status_request(self):
        result = requests.edit_status_request(self.request['_id'], self.employee_in_db)
        assert result.status == 'in_progress'
        result = requests.edit_status_request(self.request['_id'], self.employee_in_db)
        assert result.status == 'finished'
        with raises(HTTPException):
            assert requests.edit_status_request(self.request['_id'], self.employee_in_db)


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


class TestCelery:

    def setup_class(cls):
        cls.admin = {'_id': ObjectId("5e81d28fe21b6af5982f93fa"), 'email': 'admin@example.com', 'password': 'admin',
                     'role': 'admin', 'date_registration': None}
        cls.admin_in_db = UserInDB(_id=cls.admin['_id'], email=cls.admin['email'],
                                   hash_password=get_password_hash(cls.admin['password']), role=cls.admin['role'],
                                   date_registration=cls.admin['date_registration'])

        cls.employee = {'_id': None, 'email': 'employee@celery.ru', 'password': 'employee'}
        cls.employee_in = UserIn(email=cls.employee['email'], password=cls.employee['password'])
        cls.employee['_id'] = registration(cls.employee_in, role='employee').user_id

        cls.user = {'_id': None, 'email': 'user@celery.ru', 'password': 'user', 'role': 'user',
                    'date_registration': None}
        cls.user_in = UserIn(email=cls.user['email'], password=cls.user['password'])
        data_user = registration(cls.user_in)
        cls.user['_id'] = data_user.user_id
        cls.user['date_registration'] = data_user.date_registration
        cls.user_in_db = UserInDB(_id=ObjectId(cls.user['_id']), email=cls.user['email'],
                                  hash_password=get_password_hash(cls.user['password']), role=cls.user['role'],
                                  date_registration=cls.user['date_registration'])

        cls.request = {'_id': None, 'title': 'Test Title', 'description': 'Test Description',
                       'date_receipt': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'status': None}
        cls.request_in = RequestIn(title=cls.request['title'], description=cls.request['description'],
                                   date_receipt=cls.request['date_receipt'])
        cls.request['_id'] = requests.create_request(cls.request_in, ObjectId(cls.user['_id'])).request_id
        requests.edit_status_request(cls.request['_id'], cls.user_in_db)

    def teardown_class(cls):
        user_collection.delete_many({'role': 'employee'})
        user_collection.delete_many({'role': 'user'})
        request_collection.delete_many({'user_id': ObjectId(cls.user['_id'])})

    def test_send_email(self):
        result = celery_app.send_email('bykov@appvelox.ru', 'Test', 'Test')
        assert result is True

    def test_no_overdue_requests_processing(self):
        result = celery_app.warning_admin_long_time_consider_request()
        assert result is False

    def test_overdue_requests_processing(self):
        new_date = datetime.now() - timedelta(hours=5)
        request = request_collection.update_one({'_id': ObjectId(self.request['_id'])},
                                                {'$set': {"date_receipt": new_date}}).modified_count
        result = celery_app.warning_admin_long_time_consider_request()
        assert result is True

    def test_no_overdue_requests_execution(self):
        result = celery_app.warning_employee_long_time_complete_request()
        assert result is False

    def test_overdue_requests_execution(self):
        requests.assign_employee_to_request(self.employee['_id'], self.request['_id'], self.admin_in_db)
        new_date = datetime.now() - timedelta(hours=72)
        request = request_collection.update_one({'_id': ObjectId(self.request['_id'])},
                                                {'$set': {"date_receipt": new_date}}).modified_count
        result = celery_app.warning_employee_long_time_complete_request()
        assert result is True


if __name__ == '__main__':
    unittest.main()
