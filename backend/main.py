import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from routers.member import router as member_router
from routers.ng_pair import router as ng_pair_router
from routers.pediatric_doctor_schedule import router as pediatric_doctor_schedule_router
from routers.schedule import router as schedule_router
from routers.shift_request import router as shift_request_router

logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("IntegrityError: %s %s — %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=409,
        content={"detail": "関連するデータが存在するため、操作を完了できませんでした。"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s %s — %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "サーバーエラーが発生しました。"},
    )

app.include_router(member_router)
app.include_router(ng_pair_router)
app.include_router(shift_request_router)
app.include_router(pediatric_doctor_schedule_router)
app.include_router(schedule_router)
