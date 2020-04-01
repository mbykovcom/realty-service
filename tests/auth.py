import unittest
from datetime import timedelta

from fastapi import HTTPException
from pytest import raises

from config import Config
from models.user import UserInDB
from utils.auth import create_access_token, get_current_user


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