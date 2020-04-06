import time
import unittest
from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException

from pytest import raises

from db import requests
from models.building import Coordinates, BuildingOut, BuildingIn, BuildingInDB
from models.requests import RequestIn, RequestOut, RequestOutAdmin, RequestOutEmployee
from models.user import UserIn, UserOut, UserInDB
from db.user import get_user, registration, login, get_employees
from db.building import create_building, get_buildings, get_building, edit_building
from utils.auth import get_password_hash
from utils.db import user_collection, request_collection, building_collection


class TestService:

    def setup_class(cls):
        cls.admin = {'email': 'admin@erealty.ru', 'password': 'admin'}
        registration(UserIn(email=cls.admin['email'], password=cls.admin['password']), 'admin')
        cls.administrator = {'_id': None, 'email': 'newadmin@example.com', 'password': 'admin', 'hash_password': None,
                             'role': 'administrator', "date_registration": None, 'building_id': None}
        cls.user = {'_id': None, 'email': 'newuser@example.com', 'password': 'string',
                    'hash_password': None, 'role': 'user', "date_registration": None, 'building_id': None}
        cls.employee = {'_id': None, 'email': 'employee@example.com', 'password': 'password',
                        'hash_password': None, 'role': 'employee', "date_registration": None, 'building_id': None}
        cls.request = {'_id': None, 'title': 'Test Title', 'description': 'Test Description',
                       'date_receipt': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'status': None}

        cls.request_in = RequestIn(title=cls.request['title'], description=cls.request['description'],
                                   date_receipt=cls.request['date_receipt'])

        cls.administrator_in_db = UserInDB(_id=cls.administrator['_id'], email=cls.administrator['email'],
                                          hash_password=cls.administrator['hash_password'],
                                          role=cls.administrator['role'],
                                          date_registration=cls.administrator['date_registration'], building_id=None)
        cls.user_in_db = UserInDB(_id=cls.user['_id'], email=cls.user['email'],
                                  hash_password=cls.user['hash_password'], role=cls.user['role'],
                                  date_registration=cls.user['date_registration'], building_id=None)
        cls.employee_in_db = UserInDB(_id=cls.employee['_id'], email=cls.employee['email'],
                                      hash_password=cls.employee['hash_password'], role=cls.employee['role'],
                                      date_registration=cls.employee['date_registration'], building_id=None)

        cls.incorrect_user_id = '5e7c92cf6e66c5e9a8b9e005'
        cls.incorrect_request_id = '5e7c92cf6e66c5e9a8b9e005'

        registration(UserIn(email='admin@example.com', password='admin'), 'administrator')

        location_building = Coordinates(59.93904113769531, 30.3157901763916)
        cls.building = {'_id': None, 'name': 'Name Building', 'description': 'Description Building', 'square': 100.2,
                        'location': location_building}

    def teardown_class(cls):
        user_collection.delete_many({})
        request_collection.delete_many({})
        building_collection.delete_many({})

    def test_create_building(self):
        result = create_building(BuildingIn(name=self.building['name'], description=self.building['description'],
                                            location=self.building['location'], square=self.building['square']))
        assert type(result) is BuildingOut
        TestService.building['_id'] = result.building_id

    def test_get_buildings(self):
        result = get_buildings()
        assert type(result) is list
        assert len(result) == 1

    def test_get_building(self):
        result = get_building(self.building['_id'])
        assert type(result) is BuildingOut
        assert result.building_id == self.building['_id']

    def test_edit_building_nothing(self):
        result = edit_building(self.building['_id'])
        assert type(result) is BuildingOut
        assert result.name == self.building['name']
        assert result.description == self.building['description']
        assert result.square == self.building['square']

    def test_edit_building_name(self):
        self.building['name'] = 'New Name'
        result = edit_building(self.building['_id'], name=self.building['name'])
        assert type(result) is BuildingOut
        assert result.name == self.building['name']
        assert result.description == self.building['description']
        assert result.square == self.building['square']

    def test_edit_building_description(self):
        self.building['description'] = 'New Description'
        result = edit_building(self.building['_id'], description=self.building['description'])
        assert type(result) is BuildingOut
        assert result.name == self.building['name']
        assert result.description == self.building['description']
        assert result.square == self.building['square']

    def test_edit_building_square(self):
        self.building['square'] = 10
        result = edit_building(self.building['_id'], square=self.building['square'])
        assert type(result) is BuildingOut
        assert result.name == self.building['name']
        assert result.description == self.building['description']
        assert result.square == self.building['square']

    def test_edit_building_full(self):
        self.building['name'] = 'New Name 2'
        self.building['description'] = 'New Description 2'
        self.building['square'] = 201.1
        result = edit_building(self.building['_id'], name=self.building['name'],
                               description=self.building['description'], square=self.building['square'])
        assert type(result) is BuildingOut
        assert result.name == self.building['name']
        assert result.description == self.building['description']
        assert result.square == self.building['square']

    def test_registration_user(self):
        role = 'user'
        TestService.user['building_id'] = self.building['_id']
        result = registration(UserIn(email=self.user['email'], password=self.user['password'],
                                     building_id=self.user['building_id']))
        TestService.user['_id'] = result.user_id
        TestService.user['hash_password'] = get_password_hash(self.user['password'])
        TestService.user['date_registration'] = TestService.user_in_db.date_registration = result.date_registration
        assert type(result) is UserOut
        assert result.role == role

    def test_registration_user_exists(self):
        result = registration(UserIn(email=self.user['email'], password=self.user['password'],
                                     building_id=self.user['building_id']))
        assert type(result) is HTTPException

    def test_registration_administrator(self):
        role = 'administrator'
        result = registration(UserIn(email=self.administrator['email'], password=self.administrator['password'],
                                     building_id=self.administrator['building_id']), role=role)
        TestService.administrator['_id'] = result.user_id
        TestService.administrator['hash_password'] = get_password_hash(self.administrator['password'])
        TestService.administrator['date_registration'] = TestService.administrator_in_db.date_registration = result.date_registration
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
        result = login(UserIn(email=self.user['email'], password=self.user['password'],
                                     building_id=self.user['building_id']))
        assert result['access_token'] is not None

    def test_login_user_doesnt_exists(self):
        with raises(HTTPException):
            user = UserIn(email='not_exists@gmail.com', password='password', building_id=self.user['building_id'])
            assert login(user)

    def test_login_user_incorrect_data(self):
        with raises(HTTPException):
            user = UserIn(email='not_exists@gmail.com', password='password', building_id=self.user['building_id'])
            user.email = 'not_exit@gmail.com'
            assert login(user)

    def test_create_request(self):
        result = requests.create_request(self.request_in, ObjectId(self.user['_id']))
        TestService.request['_id'] = result.request_id
        TestService.request['status'] = result.status
        assert type(result) is RequestOut

    def test_get_requests(self):
        TestService.user_in_db._id = ObjectId(self.user['_id'])
        TestService.user_in_db.building_id = ObjectId(self.building['_id'])
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
                            date_registration=self.user['date_registration'], building_id=self.user['building_id'])
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

    def test_edit_status_request_administrator(self):
        TestService.administrator_in_db.building_id = ObjectId(self.building['_id'])
        result = requests.edit_status_request(self.request['_id'], self.administrator_in_db)
        assert result.status == 'in_progress'

    def test_edit_status_request_administrator_status_in_progress(self):
        result = requests.edit_status_request(self.request['_id'], self.administrator_in_db)
        assert result.status == 'finished'

    def test_edit_status_request_administrator_status_finished(self):
        with raises(HTTPException):
            assert requests.edit_status_request(self.request['_id'], self.administrator_in_db)

    def test_administrator_get_employees_empty(self):
        result = get_employees()
        assert len(result) == 0

    def test_create_employee(self):
        employee_in = UserIn(email='employee1@realty.com', password='password', building_id=self.user['building_id'])
        registration(employee_in, self.employee['role'])
        time.sleep(1)
        employee_in.email = self.employee['email']
        result = registration(employee_in, self.employee['role'])
        TestService.employee['_id'] = result.user_id
        TestService.employee_in_db.building_id = ObjectId(self.building['_id'])
        TestService.employee_in_db._id = ObjectId(result.user_id)
        TestService.employee['hash_password'] = get_password_hash(self.user['password'])
        TestService.employee[
            'date_registration'] = TestService.employee_in_db.date_registration = result.date_registration
        assert type(result) is UserOut
        assert result.role == self.employee['role']

    def test_administrator_get_employees(self):
        result = get_employees()
        assert type(result[0]) is UserOut
        assert result[0].user_id == self.employee['_id']

    def test_assign_employee_to_request_not_active(self):
        with raises(HTTPException):
            assert requests.assign_employee_to_request(self.employee['_id'], self.request['_id'], self.administrator_in_db)

    def test_assign_employee_to_request(self):
        TestService.request['_id'] = requests.create_request(self.request_in, self.user_in_db._id).request_id
        requests.edit_status_request(self.request['_id'], self.user_in_db)
        result = requests.assign_employee_to_request(self.employee['_id'], self.request['_id'], self.administrator_in_db)
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


if __name__ == '__main__':
    unittest.main()
