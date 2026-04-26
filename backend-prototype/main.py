import threading
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scheduler import check_all_alarms

from routers import drug, chat, alarm, disposal_alarm

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본 테스트
@app.get("/")
def root():
    return {"message": "서버 정상 실행 중"}

# 라우터 등록
app.include_router(drug.router, prefix="/api", tags=["Drug"])
app.include_router(chat.router, prefix="/api")
app.include_router(alarm.router, prefix="/api", tags=["Alarm"])
app.include_router(map.router, prefix="/api/map", tags=["Map"])
app.include_router(disposal_alarm.router, prefix="/api", tags=["Disposal"])


#알람
def run_scheduler():
    while True:
        check_all_alarms()
        time.sleep(60)

@app.on_event("startup")
def start_scheduler():
    threading.Thread(target=run_scheduler, daemon=True).start()
