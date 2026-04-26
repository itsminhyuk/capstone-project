from fastapi import APIRouter
from datetime import datetime, timedelta
from database import load_data, save_data

router = APIRouter()

# 🔥 약 종류별 폐기 기간
DRUG_EXPIRY_RULES = {
    "tablet": 365,
    "syrup": 30,
    "eye_drop": 30,
    "ointment": 180,
    "powder": 90
}

# 🔥 폐기 알람 생성
@router.post("/disposal")
def create_disposal_alarm(drug_name: str, drug_type: str):
    data = load_data()

    days = DRUG_EXPIRY_RULES.get(drug_type, 30)
    now = datetime.now()
    disposal_date = now + timedelta(days=days)

    new_alarm = {
        "id": len(data["disposal_alarms"]) + 1,
        "drug_name": drug_name,
        "drug_type": drug_type,
        "created_at": now.isoformat(),
        "disposal_date": disposal_date.isoformat(),
        "triggered": False
    }

    data["disposal_alarms"].append(new_alarm)
    save_data(data)

    return new_alarm


# 🔥 전체 조회
@router.get("/disposal")
def get_disposal_alarms():
    data = load_data()
    return data["disposal_alarms"]
