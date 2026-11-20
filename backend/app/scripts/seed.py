from datetime import timedelta
from sqlalchemy import select
from app.db import Base,engine,SessionLocal
from app.models import User,TatTarget,AppSetting,Ticket,TicketMessage,TicketEvent,Notification,InternalTicket,SavedReply
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
    if not db.scalar(select(Ticket.id)):
        agents={u.email:u for u in db.scalars(select(User).where(User.role.in_(["agent","head"]))).all()}; members={u.email:u for u in db.scalars(select(User).where(User.role=="member")).all()}; head=agents["head@concave.test"]; at=now(); targets={"high":240*60,"medium":1440*60,"low":2880*60}
        demos=[
            ("member1@concave.test","agent1@concave.test","payment","Payment missing from completed study","My completed study payment has not arrived yet.","high","open",0,False),
            ("member1@concave.test","agent1@concave.test","profile_change","Update my bank account","I need to update the bank account used for rewards.","low","in_progress",0,False),
            ("member2@concave.test","agent1@concave.test","survey_issue","Survey link is not opening","The survey link shows an error after I sign in.","medium","in_progress",3600,True),
            ("member3@concave.test","agent2@concave.test","payment","UPI reference not recognised","The UPI reference is not showing against my completed participation.","high","escalated",0,False),
            ("member4@concave.test","agent1@concave.test","eligibility","Eligibility clarification","Please explain why I am not eligible for this study.","medium","resolved",900,False),
            ("member1@concave.test",None,"other","General support question","I have a question about my member account and study access.","low","closed",1200,False),
            ("member2@concave.test","agent2@concave.test","profile_change","Profile name correction","My profile name needs to be corrected before the next study.","low","reopened",300,False),
            ("member3@concave.test","agent1@concave.test","survey_issue","Survey completed but status pending","The completed survey still appears as pending in my account.","medium","resolved",1800,False),
            ("member4@concave.test","agent2@concave.test","payment","Payment confirmation request","Please confirm the payment review outcome for my completed study.","high","resolved",2100,False),
            ("member4@concave.test",None,"other","Cool-off period question","Please confirm the three-month participation cool-off rule.","low","open",0,False),
        ]
        created=[]
        for member_email,agent_email,category,subject,description,priority,status,banked,waiting in demos:
            created_at=at-timedelta(days=2 if status in {"resolved","closed"} else 0,hours=6 if status=="escalated" else 1)
            resolved_at=at-timedelta(days=6 if subject.startswith("Payment confirmation") else 1) if status in {"resolved","closed"} else None
            closed_at=resolved_at if status=="closed" else None; elapsed=banked or (1800 if status in {"resolved","closed"} else 0); running=None if status in {"resolved","closed"} or waiting else created_at
            due=None if status in {"resolved","closed"} or waiting else (at-timedelta(hours=1) if status=="escalated" else created_at+timedelta(seconds=targets[priority]))
            ticket=Ticket(member_id=members[member_email].id,assignee_id=agents[agent_email].id if agent_email else None,category=category,subject=subject,description=description,priority=priority,status=status,waiting_for_member=waiting,waiting_since=at-timedelta(hours=1) if waiting else None,tat_elapsed_seconds=elapsed,tat_running_since=running,due_at=due,escalated_at=at-timedelta(hours=1) if status=="escalated" else None,escalation_reason=f"TAT of {priority} target exceeded: active time elapsed beyond target (member-waiting time excluded)" if status=="escalated" else None,resolved_at=resolved_at,closed_at=closed_at,resolution_seconds=elapsed if resolved_at else None,reopen_count=1 if status=="reopened" else 0,version=1,created_at=created_at,updated_at=at)
            db.add(ticket); db.flush(); db.add(TicketEvent(ticket_id=ticket.id,actor_id=members[member_email].id,event_type="created",old_value=None,new_value="open",created_at=created_at)); created.append(ticket)
            db.add(TicketMessage(ticket_id=ticket.id,author_id=members[member_email].id,body=description,created_at=created_at))
            if status in {"in_progress","resolved","closed","reopened","escalated"} and agent_email: db.add(TicketMessage(ticket_id=ticket.id,author_id=agents[agent_email].id,body="We are reviewing this support query and will update you shortly.",created_at=created_at+timedelta(minutes=15)))
        db.flush(); internal_parent=created[1]; db.add(InternalTicket(ticket_id=internal_parent.id,team="finance",title="Verify bank update",description="Confirm the requested bank details with the finance team.",status="done",created_by=head.id,created_at=at-timedelta(hours=2),completed_by=head.id,completed_at=at-timedelta(hours=1),completion_note="Finance verification completed.")); db.add(InternalTicket(ticket_id=internal_parent.id,team="operations",title="Confirm profile workflow",description="Check the profile update workflow before closing the member query.",status="open",created_by=head.id,created_at=at-timedelta(minutes=30)))
        escalated=created[3]; db.add(Notification(user_id=head.id,ticket_id=escalated.id,type="escalation",message=f"{escalated.id:04d} has breached its high target",created_at=at)); db.add(Notification(user_id=agents["agent2@concave.test"].id,ticket_id=escalated.id,type="escalation",message=f"TKT-{escalated.id:04d} has breached its high target",created_at=at)); db.add(Notification(user_id=members["member1@concave.test"].id,ticket_id=created[4].id,type="resolution",message=f"TKT-{created[4].id:04d} is ready for confirmation",created_at=at))
    db.commit(); print("Seeded users: 7 | TAT targets: 3 | settings: 3"); db.close()
if __name__=="__main__": import sys; seed("--reset" in sys.argv)
