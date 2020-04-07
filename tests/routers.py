import time
import unittest
from datetime import datetime

from fastapi.testclient import TestClient

from app import app

from db.user import get_user, registration
from models.building import Coordinates
from models.user import UserIn
from utils.db import user_collection, request_collection, building_collection

client = TestClient(app)


class TestRoutes:

    def setup_class(cls):
        cls.admin = {'email': 'admin@realty.ru', 'password': 'admin'}
        registration(UserIn(email=cls.admin['email'], password=cls.admin['password']), 'admin')
        cls.administrator = {'email': 'administrator@example.com', 'password': 'administrator', 'building_id': None}
        cls.user = {'email': 'user@realty.ru', 'password': 'user', 'building_id': None}
        cls.user_id = None
        cls.employee = {'email': 'employee@realty.ru', 'password': 'employee', 'building_id': None}
        cls.employee_id = None
        cls.request = {'title': 'Test Title', 'description': 'Test Description',
                       'date_receipt': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        cls.request_id = None
        location_building = Coordinates(59.93904113769531, 30.3157901763916)
        cls.building = {'_id': None, 'name': 'Name Building', 'description': 'Description Building', 'square': 100.2,
                        'location': location_building}
        cls.jwt = {'admin': None, 'administrator': None, 'user': None, 'employee': None}

    def teardown_class(cls):
        user_collection.delete_many({})
        request_collection.delete_many({})
        building_collection.delete_many({})

    def test_create_building(self):
        json = {
            'name': self.building['name'],
            'description': self.building['description'],
            'location': self.building['location'],
            'square': self.building['square']
        }
        TestRoutes.jwt['admin'] = client.post('/login', json=self.admin).json()['access_token']
        headers = {'jwt': self.jwt['admin']}
        response = client.post('/admin/building', json=json, headers=headers)
        assert response.status_code == 201
        response = response.json()
        TestRoutes.building['_id'] = TestRoutes.administrator['building_id'] = TestRoutes.user['building_id'] = \
            TestRoutes.employee['building_id'] = response['building_id']
        assert response == {"building_id": self.building['_id'],
                            "name": self.building['name'],
                            "description": self.building['description'],
                            "location": [self.building['location'].lat, self.building['location'].lon],
                            "square": self.building['square']}

    def test_create_administrator(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.post('/admin', json=self.administrator, headers=headers)
        assert response.status_code == 201
        response = response.json()
        assert response == {"user_id": response['user_id'],
                            "email": self.administrator['email'],
                            "role": "administrator",
                            "date_registration": response['date_registration'],
                            "building_id": self.building['_id']}

    def test_login_administrator(self):
        response = client.post('/login', json=self.administrator)
        TestRoutes.jwt['administrator'] = response.json()['access_token']
        assert response.status_code == 200
        assert list(response.json().keys()) == ['access_token', 'token_type']

    def test_create_administrator_no_access(self):
        headers = {'jwt': self.jwt['administrator']}
        response = client.post('/admin', json=self.administrator, headers=headers)
        assert response.status_code == 403
        assert response.json() == {'detail': 'The user does not have access rights'}

    def test_get_buildings(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.get("/admin/building", headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert type(response['buildings']) is list
        assert response == {'buildings':
            [
                {"building_id": self.building['_id'],
                 "name": self.building['name'],
                 "description": self.building['description'],
                 "location": [self.building['location'].lat, self.building['location'].lon],
                 "square": self.building['square']}
            ]
        }

    def test_get_building(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.get(f"/admin/building/{self.building['_id']}", headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response == {"building_id": self.building['_id'],
                            "name": self.building['name'],
                            "description": self.building['description'],
                            "location": [self.building['location'].lat, self.building['location'].lon],
                            "square": self.building['square']}

    def test_edit_building_nothing(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.patch(f"/admin/building/{self.building['_id']}", headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "The Name, Description and Square fields are empty"}

    def test_edit_building_name(self):
        self.building['name'] = 'New Name'
        headers = {'jwt': self.jwt['admin']}
        response = client.patch(f"/admin/building/{self.building['_id']}?name={self.building['name']}", headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response == {"building_id": self.building['_id'],
                            "name": self.building['name'],
                            "description": self.building['description'],
                            "location": [self.building['location'].lat, self.building['location'].lon],
                            "square": self.building['square']}

    def test_edit_building_description(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.patch(f"/admin/building/{self.building['_id']}?description={self.building['description']}",
                                headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response == {"building_id": self.building['_id'],
                            "name": self.building['name'],
                            "description": self.building['description'],
                            "location": [self.building['location'].lat, self.building['location'].lon],
                            "square": self.building['square']}

    def test_edit_building_square(self):
        self.request['square'] = 155.5
        headers = {'jwt': self.jwt['admin']}
        response = client.patch(f"/admin/building/{self.building['_id']}?square={self.building['square']}",
                                headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response == {"building_id": self.building['_id'],
                            "name": self.building['name'],
                            "description": self.building['description'],
                            "location": [self.building['location'].lat, self.building['location'].lon],
                            "square": self.building['square']}

    def test_edit_building_full(self):
        self.building['name'] = 'New Name 2'
        self.building['description'] = 'New Description 2'
        self.building['square'] = 201.1
        headers = {'jwt': self.jwt['admin']}
        response = client.patch(f"/admin/building/{self.building['_id']}?name={self.building['name']}&"
                                f"description={self.building['description']}&square={self.building['square']}",
                                headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert response == {"building_id": self.building['_id'],
                            "name": self.building['name'],
                            "description": self.building['description'],
                            "location": [self.building['location'].lat, self.building['location'].lon],
                            "square": self.building['square']}

    def test_registration_user(self):
        json = {'user_data': self.user, 'location': {'lat': 59.9384481, 'lon': 30.316656}}
        response = client.post('/registration', json=json)
        TestRoutes.user_id = get_user(self.user['email'])._id
        assert response.status_code == 201
        assert response.json() == {"user_id": str(self.user_id),
                                   "email": self.user['email'],
                                   "role": "user",
                                   "date_registration": response.json()['date_registration'],
                                   "building_id": self.building['_id']}

    def test_registration_user_outside(self):
        json = {'user_data': self.user, 'location': {'lat': 59.938123, 'lon': 30.317247}}
        response = client.post('/registration', json=json)
        assert response.status_code == 400
        assert response.json() == {"detail": 'The user is located outside the building'}

    def test_registration_user_exists(self):
        json = {'user_data': self.user, 'location': {'lat': 59.9384481, 'lon': 30.316656}}
        response = client.post('/registration', json=json)
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
                        "user_data"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                },
                {
                    "loc": [
                        "body",
                        "location"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

    def test_registration_without_password(self):
        json = {'user_data': {'email': self.user['email']},
                'location': {'lat': 59.9384481, 'lon': 30.316656}}
        response = client.post('/registration', json=json)
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "user_data",
                        "password"
                    ],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

    def test_registration_without_email(self):
        json = {'user_data': {'password': self.user['password']},
                'location': {'lat': 59.9384481, 'lon': 30.316656}}
        response = client.post('/registration', json=json)
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "loc": [
                        "body",
                        "user_data",
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
                        "user_data"
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
                        "user_data",
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
                        "user_data",
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

    def test_get_requests_administrator_empty(self):
        request_collection.delete_many({'user_id': self.user_id})
        headers = {'jwt': self.jwt['administrator']}
        response = client.get(f"/requests", headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "This administrator does not have any requests"}

    def test_get_requests_administrator(self):
        headers = {'jwt': self.jwt['user']}
        response = client.post('/requests', json=self.request, headers=headers)
        TestRoutes.request_id = response.json()['request_id']
        headers = {'jwt': self.jwt['user']}
        client.patch(f"/requests/status/{self.request_id}", headers=headers)
        headers['jwt'] = self.jwt['administrator']
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

    def test_get_request_administrator(self):
        headers = {'jwt': self.jwt['administrator']}
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

    def test_get_request_administrator_not_exist(self):
        request_id = '5e7bfee773467953a87e467a'
        headers = {'jwt': self.jwt['administrator']}
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
        headers = {'jwt': self.jwt['administrator']}
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
        headers = {'jwt': self.jwt['administrator']}
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
        headers = {'jwt': self.jwt['administrator']}
        response = client.patch(f"/requests/status/{self.request_id}", headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": f'This request ({self.request_id}) has the finished status'}

    def test_registration_employee(self):
        headers = {'jwt': self.jwt['administrator']}
        response = client.post('/employee', json=self.employee, headers=headers)
        TestRoutes.employee_id = get_user(self.employee['email'])._id
        assert response.status_code == 201
        assert response.json() == {"user_id": response.json()['user_id'],
                                   "email": self.employee['email'],
                                   "role": "employee",
                                   "date_registration": response.json()['date_registration'],
                                   "building_id": self.building['_id']}

    def test_get_employees_admin(self):
        headers = {'jwt': self.jwt['admin']}
        employee_admin = self.employee.copy()
        time.sleep(1)
        employee_admin['email'] = 'employee_admin@realty.ru'
        client.post('/employee', json=employee_admin, headers=headers)
        response = client.get('/employee', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert len(response['employees']) == 2
        assert response['employees'][0] == {'date_registration': response['employees'][0]['date_registration'],
                                            'email': employee_admin['email'],
                                            'role': 'employee',
                                            'user_id': response['employees'][0]['user_id'],
                                            "building_id": None}

    def test_get_employees_administrator(self):
        headers = {'jwt': self.jwt['administrator']}
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
                                            'user_id': response['employees'][0]['user_id'],
                                            "building_id": self.building['_id']}

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
        headers['jwt'] = self.jwt['administrator']
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

    def test_get_users_without_filter(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.get(f'/admin/users', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert len(response['users']) == 6

    def test_get_users_by_role(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.get(f'/admin/users?role=employee', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert len(response['users']) == 3

    def test_get_users_by_building(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.get(f'/admin/users?building_id={self.building["_id"]}', headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert len(response['users']) == 4

    def test_get_users(self):
        headers = {'jwt': self.jwt['admin']}
        response = client.get(f'/admin/users?role=user&building_id={self.building["_id"]}',
                              headers=headers)
        assert response.status_code == 200
        response = response.json()
        assert len(response['users']) == 1


if __name__ == '__main__':
    unittest.main()
