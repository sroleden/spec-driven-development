from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.routes import api, pages
from app.services.errors import Conflict, NotFound, ServiceError, ValidationFailed

STATUS_FOR_ERROR = {NotFound: 404, Conflict: 409, ValidationFailed: 422}


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Dark Spark Tickets", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(api.router)
app.include_router(pages.router)


@app.exception_handler(ServiceError)
async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
    status = STATUS_FOR_ERROR.get(type(exc), 400)
    return JSONResponse(status_code=status, content={"detail": exc.detail})
