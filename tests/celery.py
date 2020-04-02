import unittest
from datetime import datetime, timedelta

from bson import ObjectId
import celery_app

from db import requests
from models.requests import RequestIn
from models.user import UserIn, UserInDB
from db.user import registration
from utils.auth import get_password_hash
from utils.db import user_collection, request_collection


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
        registration(UserIn(email='admin@example.com', password='admin'), 'admin')


    def teardown_class(cls):
        user_collection.delete_many({})
        request_collection.delete_many({})

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