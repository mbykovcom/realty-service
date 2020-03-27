from fastapi import FastAPI

from routers import requests, auth

app = FastAPI(title="Realty-Service",
              description="This is a training project, with auto docs for the API",
              version="0.1",)

app.include_router(requests.router, prefix='/requests')
app.include_router(auth.router)


