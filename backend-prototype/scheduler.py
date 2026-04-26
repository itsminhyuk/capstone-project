from datetime import datetime
from database import SessionLocal, DisposalAlarm

def check_all_alarms():
    db = SessionLocal()
    now = datetime.utcnow()

    current_time_str = now.strftime("%H:%M")

    # 🔥 1. 복약 알람 체크
    alarms = db.query(Alarm).filter(Alarm.is_active == True).all()

    for alarm in alarms:
        times = alarm.alarm_time.split(",")

        if current_time_str in times:
            print(f"[복약 알림] {alarm.medicine_name} 복용 시간입니다!")

    # 🔥 2. 폐기 알람 체크
    disposal_alarms = db.query(DisposalAlarm).filter(
        DisposalAlarm.is_triggered == False
    ).all()

    for alarm in disposal_alarms:
        if alarm.disposal_date <= now:
            print(f"[폐기 알림] {alarm.medicine_name} 버릴 시간입니다!")
            alarm.is_triggered = True

    db.commit()
    db.close()
