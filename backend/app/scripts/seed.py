from datetime import timedelta
from sqlalchemy import select
from app.db import Base,engine,SessionLocal
from app.models import User,TatTarget,AppSetting,Ticket,TicketMessage,SavedReply
from app.core.security import hash_password
from app.core.clock import now

USERS=[("Meera Shah","head@concave.test","Head@123","head"),("Arjun Mehta","agent1@concave.test","Agent@123","agent"),("Kavya Nair","agent2@concave.test","Agent@123","agent"),("Rohan Verma","member1@concave.test","Member@123","member"),("Sneha Iyer","member2@concave.test","Member@123","member"),("Imran Khan","member3@concave.test","Member@123","member"),("Divya Menon","member4@concave.test","Member@123","member")]
def seed(reset=False):
    Base.metadata.create_all(engine); db=SessionLocal()
    if reset:
        for table in reversed(Base.metadata.sorted_tables): db.execute(table.delete())
        db.commit()
    existing={u.email for u in db.scalars(select(User)).all()}
    for name,email,password,role in USERS:
        if email not in existing: db.add(User(name=name,email=email,password_hash=hash_password(password),role=role,created_at=now()))
    db.flush()
    for p,m in [("high",240),("medium",1440),("low",2880)]:
        if not db.get(TatTarget,p): db.add(TatTarget(priority=p,target_minutes=m,updated_at=now()))
    for k,v in [("reopen_window_days",3),("max_reopens",2),("auto_close_days",7)]:
        if not db.get(AppSetting,k): db.add(AppSetting(key=k,value_int=v,updated_at=now()))
    head=db.scalar(select(User).where(User.role=="head"))
    replies=[("Payment acknowledgement","Thanks for contacting us about your payment. We are checking the rewards record.","payment"),("Request more detail","Please share the study name and the reference shown in your payment app.",None),("Eligibility guidance","Eligibility is checked per study and the three-month participation rule applies.","eligibility"),("Profile update","Please confirm the profile field you would like us to update.","profile_change"),("Survey troubleshooting","Please share the survey link and a screenshot of the issue if possible.","survey_issue"),("Resolution note","We have completed the requested check and recorded the outcome above.",None)]
    for title,body,category in replies:
        if not db.scalar(select(SavedReply).where(SavedReply.title==title)): db.add(SavedReply(title=title,body=body,category=category,created_by=head.id,created_at=now(),updated_at=now()))
    db.commit(); print("Seeded users: 7 | TAT targets: 3 | settings: 3"); db.close()
if __name__=="__main__": import sys; seed("--reset" in sys.argv)
