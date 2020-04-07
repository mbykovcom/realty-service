from fastapi import FastAPI

from config import Config

from models.user import UserIn
from routers import requests, auth, employee, admin

app = FastAPI(title="Realty-Service",
              description="This is a training project, with auto docs for the API",
              version="0.1", )

app.include_router(requests.router, prefix='/requests')
app.include_router(auth.router)
app.include_router(employee.router, prefix='/employee')
app.include_router(admin.router, prefix='/admin')

from db.user import registration

admin = UserIn(email=Config.ADMIN_EMAIL, password=Config.ADMIN_PASSWORD)
registration(admin, 'admin')
