from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.member import router as member_router
from routers.ng_pair import router as ng_pair_router
from routers.pediatric_doctor_schedule import router as pediatric_doctor_schedule_router
from routers.schedule import router as schedule_router
from routers.shift_request import router as shift_request_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(member_router)
app.include_router(ng_pair_router)
app.include_router(shift_request_router)
app.include_router(pediatric_doctor_schedule_router)
app.include_router(schedule_router)
