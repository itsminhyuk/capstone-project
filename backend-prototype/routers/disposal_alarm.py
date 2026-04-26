from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import SessionLocal
from database import DisposalAlarm

router = APIRouter()

# 🔥 폐기 기간 정의
DRUG_EXPIRY_RULES = {
    "tablet": 365,
    "syrup": 30,
    "eye_drop": 30,
    "ointment": 180,
    "powder": 90
}

# DB 세션
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🔥 폐기 알람 생성
@router.post("/disposal")
def create_disposal_alarm(
    user_id: int,
    medicine_name: str,
    drug_type: str,
    db: Session = Depends(get_db)
):
    days = DRUG_EXPIRY_RULES.get(drug_type, 30)

    now = datetime.utcnow()
    disposal_date = now + timedelta(days=days)

    alarm = DisposalAlarm(
        user_id=user_id,
        medicine_name=medicine_name,
        drug_type=drug_type,
        disposal_date=disposal_date
    )

    db.add(alarm)
    db.commit()
    db.refresh(alarm)

    return alarm


# 🔥 조회
@router.get("/disposal")
def get_disposal_alarms(user_id: int, db: Session = Depends(get_db)):
    return db.query(DisposalAlarm).filter(
        DisposalAlarm.user_id == user_id
    ).all()
