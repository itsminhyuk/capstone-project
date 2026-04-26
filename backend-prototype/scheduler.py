from datetime import datetime
from database import SessionLocal, DisposalAlarm

def check_disposal_alarm():
    db = SessionLocal()
    now = datetime.utcnow()

    alarms = db.query(DisposalAlarm).filter(
        DisposalAlarm.is_triggered == False
    ).all()

    for alarm in alarms:
        if alarm.disposal_date <= now:
            print(f"[폐기 알림] {alarm.medicine_name} 버릴 시간입니다!")
            alarm.is_triggered = True

    db.commit()
    db.close()
