import time
import unittest
from datetime import datetime

from fastapi.testclient import TestClient
from mock import patch

import celery_app
from app import app

from db.user import get_user, registration
from models.user import UserIn
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
        registration(UserIn(email='admin@example.com', password='admin'), 'admin')


    def teardown_class(cls):
        user_collection.delete_many({})
        request_collection.delete_many({})

    @patch("celery_app.send_email")
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
        request_collection.delete_many({'user_id': self.user_id})
        headers = {'jwt': self.jwt['admin']}
        response = client.get(f"/requests", headers=headers)
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

    @patch("celery_app.send_email")
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

if __name__ == '__main__':
    unittest.main()