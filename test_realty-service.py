import unittest
from tests.routers import TestRoutes
from tests.db import TestService
from tests.celery import TestCelery
from tests.auth import TestOAuth

if __name__ == '__main__':
    unittest.main()
