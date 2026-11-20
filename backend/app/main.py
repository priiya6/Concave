from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
import asyncio, logging
from fastapi import FastAPI, Depends, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select, or_, and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .db import Base, engine, get_db, SessionLocal
from .models import User, TatTarget, AppSetting, Ticket, TicketMessage, TicketEvent, Notification, InternalTicket, SavedReply
from .schemas import *
from .core.security import *
from .core.clock import now
from .core.config import settings

log=logging.getLogger(__name__)

CATEGORIES={"payment":"high","eligibility":"medium","survey_issue":"medium","profile_change":"low","other":"low"}
OPEN={"open","in_progress","reopened","escalated"}
TARGET_DEFAULT={"high":240,"medium":1440,"low":2880}

def err(code,message,status): raise HTTPException(status_code=status, detail={"code":code,"message":message})
def utc(v): return v.replace(tzinfo=timezone.utc) if v and v.tzinfo is None else v
def format_dt(v): return utc(v).astimezone(timezone.utc).isoformat().replace("+00:00","Z") if v else None
def number(t): return f"TKT-{t.id:04d}"
def get_ticket(db,no):
    raw=str(no); key=raw[4:] if raw.upper().startswith("TKT-") else raw
    if not key.isdigit(): err("not_found","Ticket not found",404)
    t=db.get(Ticket,int(key))
    if not t: err("not_found","Ticket not found",404)
    return t
def require_user(authorization: str|None=Header(default=None), db:Session=Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "): err("unauthorized","Authentication required",401)
    data=decode_token(authorization.split(" ",1)[1]); user=db.get(User,int(data["uid"]))
    if not user or not user.is_active: err("unauthorized","Authentication required",401)
    return user
def roles(*allowed):
    def dep(user=Depends(require_user)):
        if user.role not in allowed: err("forbidden","You do not have permission for this action",403)
        return user
    return dep
def event(db,t,actor,event_type,old=None,new=None,reason=None): db.add(TicketEvent(ticket_id=t.id,actor_id=actor.id if actor else None,event_type=event_type,old_value=old,new_value=new,reason=reason,created_at=now()))
def target(db,priority): return db.get(TatTarget,priority).target_minutes*60
def elapsed(t,at): return t.tat_elapsed_seconds + (int((at-utc(t.tat_running_since)).total_seconds()) if t.tat_running_since else 0)
def tat(db,t,at):
    running=t.status in OPEN and not t.waiting_for_member and t.tat_running_since is not None
    e=elapsed(t,at); due=utc(t.due_at)
    state="overdue" if t.status=="escalated" or (running and due and due<=at) else "running" if running else "paused" if t.waiting_for_member else "stopped"
    remaining=max(0,int((due-at).total_seconds())) if due and running else 0
    return {"state":state,"target_seconds":target(db,t.priority),"elapsed_seconds":e,"remaining_seconds":remaining,"due_at":format_dt(due),"as_of":format_dt(at)}
def serialize_user(u): return {"id":u.id,"name":u.name,"email":u.email,"role":u.role}
def serialize_ticket(db,t,staff=False):
    at=now(); msgs=db.scalars(select(TicketMessage).where(TicketMessage.ticket_id==t.id).order_by(TicketMessage.created_at)).all()
    member=db.get(User,t.member_id); assignee=db.get(User,t.assignee_id) if t.assignee_id else None
    d={"id":t.id,"ticket_number":number(t),"member":{"id":member.id,"name":member.name,"email":member.email},"assignee":serialize_user(assignee) if assignee else None,"category":t.category,"subject":t.subject,"description":t.description,"priority":t.priority,"status":t.status,"waiting_for_member":t.waiting_for_member,"tat":tat(db,t,at),"due_at":format_dt(t.due_at),"created_at":format_dt(t.created_at),"updated_at":format_dt(t.updated_at),"resolved_at":format_dt(t.resolved_at),"closed_at":format_dt(t.closed_at),"reopen_count":t.reopen_count,"version":t.version,"messages":[{"id":m.id,"body":m.body,"requests_info":m.requests_info,"author":serialize_user(db.get(User,m.author_id)),"created_at":format_dt(m.created_at)} for m in msgs]}
    internals=db.scalars(select(InternalTicket).where(InternalTicket.ticket_id==t.id).order_by(InternalTicket.created_at)).all()
    d["internal_tickets"]=[{"id":x.id,"internal_number":f"INT-{x.id:04d}","team":x.team,"title":x.title if staff else None,"description":x.description if staff else None,"status":x.status,"completion_note":x.completion_note if staff else None,"created_at":format_dt(x.created_at),"completed_at":format_dt(x.completed_at)} for x in internals]
    if staff:
        d["escalation_reason"]=t.escalation_reason; d["events"]=[{"id":e.id,"event_type":e.event_type,"old_value":e.old_value,"new_value":e.new_value,"reason":e.reason,"actor":serialize_user(db.get(User,e.actor_id)) if e.actor_id else None,"created_at":format_dt(e.created_at)} for e in db.scalars(select(TicketEvent).where(TicketEvent.ticket_id==t.id).order_by(TicketEvent.created_at)).all()]
    return d
def check_version(t,expected):
    if t.version!=expected: err("version_conflict","This ticket was updated by someone else. Refresh and try again.",409)
def touch(t,at): t.version+=1; t.updated_at=at

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    task=None
    if settings.enable_background_jobs:
        async def loop():
            while True:
                try:
                    await asyncio.to_thread(run_jobs)
                except Exception:
                    log.exception("background job failed")
                await asyncio.sleep(settings.escalation_interval_seconds)
        task=asyncio.create_task(loop())
    try: yield
    finally:
        if task: task.cancel()
app=FastAPI(title="Concave Insights Support API",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.exception_handler(RequestValidationError)
async def validation(_,exc): return JSONResponse(content={"error":{"code":"validation_error","message":"Request validation failed","details":exc.errors()}},status_code=422)
@app.exception_handler(HTTPException)
async def http_error(_,exc):
    detail=exc.detail if isinstance(exc.detail,dict) else {"code":"http_error","message":str(exc.detail)}
    return JSONResponse(content={"error":detail},status_code=exc.status_code)
@app.exception_handler(IntegrityError)
async def integrity(_,exc):
    log.warning("database integrity error: %s",exc); return JSONResponse(content={"error":{"code":"conflict","message":"That change conflicts with existing data."}},status_code=409)
@app.exception_handler(Exception)
async def unexpected(_,exc):
    log.exception("unhandled application error",exc_info=exc); return JSONResponse(content={"error":{"code":"server_error","message":"An unexpected server error occurred."}},status_code=500)

@app.get("/api/health")
def health(): return {"ok":True}
@app.post("/api/auth/login")
def login(data:Login,db:Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==data.email.strip().lower()))
    if not u or not verify_password(data.password,u.password_hash): err("unauthorized","Invalid email or password",401)
    return {"access_token":create_token(u.id,u.role),"token_type":"bearer","user":serialize_user(u)}
@app.get("/api/auth/me")
def me(u=Depends(require_user)): return serialize_user(u)
@app.get("/api/users/staff")
def staff(db=Depends(get_db),u=Depends(roles("agent","head"))): return {"items":[serialize_user(x) for x in db.scalars(select(User).where(User.role.in_(["agent","head"]),User.is_active==True)).all()]}

@app.post("/api/tickets",status_code=201)
def create_ticket(data:TicketCreate,db:Session=Depends(get_db),u=Depends(roles("member"))):
    cat=data.category.strip();
    if cat not in CATEGORIES: err("validation_error","Unknown category",422)
    subject=data.subject.strip(); description=data.description.strip()
    if len(subject)<3 or len(description)<10: err("validation_error","Subject and description cannot be blank",422)
    tnow=now(); p=CATEGORIES[cat]; t=Ticket(member_id=u.id,category=cat,subject=subject,description=description,priority=p,status="open",tat_running_since=tnow,due_at=tnow+timedelta(seconds=target(db,p)),created_at=tnow,updated_at=tnow)
    db.add(t); db.flush(); event(db,t,u,"created",new="open"); db.commit(); return serialize_ticket(db,t)
@app.get("/api/tickets")
def list_tickets(status:str|None=None,category:str|None=None,priority:str|None=None,overdue:bool=False,q:str|None=None,assignee:str|None=None,page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),sort:str="created_at",db:Session=Depends(get_db),u=Depends(require_user)):
    stmt=select(Ticket)
    if u.role=="member": stmt=stmt.where(Ticket.member_id==u.id)
    if status: stmt=stmt.where(Ticket.status==status)
    if category: stmt=stmt.where(Ticket.category==category)
    if priority: stmt=stmt.where(Ticket.priority==priority)
    if overdue: stmt=stmt.where(or_(Ticket.status=="escalated",and_(Ticket.status.in_(OPEN),Ticket.waiting_for_member==False,Ticket.due_at<=now())))
    if assignee=="me": stmt=stmt.where(Ticket.assignee_id==u.id)
    elif assignee=="unassigned": stmt=stmt.where(Ticket.assignee_id==None)
    elif assignee:
        try: stmt=stmt.where(Ticket.assignee_id==int(assignee))
        except ValueError: err("validation_error","Invalid assignee filter",422)
    if q:
        raw_q=q.strip(); ticket_q=raw_q[4:] if raw_q.upper().startswith("TKT-") else raw_q; safe_q=raw_q.replace('%','\\%').replace('_','\\_'); text=f"%{safe_q}%"; member_clause=or_(func.lower(User.name).like(text.lower(),escape="\\"),func.lower(User.email).like(text.lower(),escape="\\")); id_clause=Ticket.id==int(ticket_q) if ticket_q.isdigit() else func.cast(Ticket.id,String).like(text,escape="\\"); stmt=stmt.join(User,User.id==Ticket.member_id).where(or_(member_clause,id_clause))
    total=db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows=db.scalars(stmt.order_by(Ticket.created_at.desc()).offset((page-1)*page_size).limit(page_size)).all()
    return {"items":[serialize_ticket(db,t,u.role!="member") for t in rows],"total":total,"page":page,"page_size":page_size}
@app.get("/api/tickets/{no}")
def detail(no:str,db=Depends(get_db),u=Depends(require_user)):
    t=get_ticket(db,no)
    if u.role=="member" and t.member_id!=u.id: err("not_found","Ticket not found",404)
    can=False; reason=None
    if t.status!="resolved": reason="not_resolved"
    elif t.reopen_count>=get_setting(db,"max_reopens"): reason="max_reopens_reached"
    elif not t.resolved_at or now()-utc(t.resolved_at)>timedelta(days=get_setting(db,"reopen_window_days")): reason="window_expired"
    else: can=True
    out=serialize_ticket(db,t,u.role!="member"); out.update({"can_reopen":can,"reopen_blocked_reason":reason}); return out
def get_setting(db,key): return db.get(AppSetting,key).value_int

@app.post("/api/tickets/{no}/messages")
def message(no:str,data:MessageCreate,db=Depends(get_db),u=Depends(require_user)):
    t=get_ticket(db,no)
    if u.role=="member" and t.member_id!=u.id: err("not_found","Ticket not found",404)
    if t.status in {"resolved","closed"}: err("invalid_transition","This ticket cannot receive messages",409)
    if not data.body.strip(): err("validation_error","Message cannot be blank",422)
    check_version(t,data.expected_version); at=now(); old=t.status
    if u.role!="member" and t.status in {"open","reopened"}: t.status="in_progress"; event(db,t,u,"status_changed",old, t.status)
    if u.role=="member" and t.waiting_for_member:
        t.waiting_for_member=False; t.waiting_since=None; t.tat_running_since=at; t.due_at=at+timedelta(seconds=max(0,target(db,t.priority)-t.tat_elapsed_seconds)); event(db,t,u,"waiting_resumed")
    if u.role!="member" and data.request_info:
        t.tat_elapsed_seconds=elapsed(t,at); t.tat_running_since=None; t.due_at=None; t.waiting_for_member=True; t.waiting_since=at; event(db,t,u,"waiting_started")
    db.add(TicketMessage(ticket_id=t.id,author_id=u.id,body=data.body.strip(),requests_info=data.request_info,created_at=at)); touch(t,at); db.commit(); return serialize_ticket(db,t,u.role!="member")
def mutate_staff(no,db,u,expected,fn):
    t=get_ticket(db,no); check_version(t,expected); fn(t); touch(t,now()); db.commit(); return serialize_ticket(db,t,True)
@app.post("/api/tickets/{no}/assign")
def assign(no:str,data:Assign,db=Depends(get_db),u=Depends(roles("agent","head"))):
    def f(t):
        if data.assignee_id and (not db.get(User,data.assignee_id) or db.get(User,data.assignee_id).role not in {"agent","head"}): err("validation_error","Invalid assignee",422)
        old=t.assignee_id; t.assignee_id=data.assignee_id
        if t.status in {"open","reopened"}:
            t.status="in_progress"; event(db,t,u,"status_changed",old=None,new="in_progress")
        event(db,t,u,"assigned",str(old),str(data.assignee_id))
    return mutate_staff(no,db,u,data.expected_version,f)
@app.post("/api/tickets/{no}/priority")
def priority(no:str,data:Priority,db=Depends(get_db),u=Depends(roles("agent","head"))):
    if data.priority not in TARGET_DEFAULT: err("validation_error","Unknown priority",422)
    def f(t):
        at=now(); oldp=t.priority; e=elapsed(t,at); t.priority=data.priority
        if t.tat_running_since and not t.waiting_for_member: t.due_at=at+timedelta(seconds=max(0,target(db,data.priority)-e))
        event(db,t,u,"priority_changed",oldp,data.priority,data.reason)
    return mutate_staff(no,db,u,data.expected_version,f)
@app.post("/api/tickets/{no}/resolve")
def resolve(no:str,data:Resolve,db=Depends(get_db),u=Depends(roles("agent","head"))):
    def f(t):
        if t.status not in {"open","in_progress","reopened","escalated"}: err("invalid_transition","Ticket cannot be resolved",409)
        at=now(); t.tat_elapsed_seconds=elapsed(t,at); t.tat_running_since=None; t.due_at=None; t.waiting_for_member=False; t.waiting_since=None; t.status="resolved"; t.resolved_at=at; t.resolution_seconds=t.tat_elapsed_seconds; event(db,t,u,"status_changed",None,"resolved")
        if data.note: db.add(TicketMessage(ticket_id=t.id,author_id=u.id,body=data.note,created_at=at))
    return mutate_staff(no,db,u,data.expected_version,f)
@app.post("/api/tickets/{no}/confirm")
def confirm(no:str,data:Action,db=Depends(get_db),u=Depends(roles("member"))):
    def f(t):
        if t.member_id!=u.id: err("not_found","Ticket not found",404)
        if t.status!="resolved": err("invalid_transition","Only resolved tickets can be closed",409)
        t.status="closed"; t.closed_at=now(); event(db,t,u,"status_changed","resolved","closed")
    return mutate_staff(no,db,u,data.expected_version,f)
@app.post("/api/tickets/{no}/reopen")
def reopen(no:str,data:Reopen,db=Depends(get_db),u=Depends(roles("member"))):
    def f(t):
        if t.member_id!=u.id: err("not_found","Ticket not found",404)
        if t.status!="resolved": err("reopen_not_allowed","Only resolved tickets can be reopened",409)
        if t.reopen_count>=get_setting(db,"max_reopens") or not t.resolved_at or now()-utc(t.resolved_at)>timedelta(days=get_setting(db,"reopen_window_days")): err("reopen_not_allowed","This ticket is outside the reopen policy",409)
        at=now(); t.status="reopened"; t.reopen_count+=1; t.tat_elapsed_seconds=0; t.tat_running_since=at; t.due_at=at+timedelta(seconds=target(db,t.priority)); t.resolved_at=None; t.resolution_seconds=None; event(db,t,u,"reopened",reason=data.reason); db.add(TicketMessage(ticket_id=t.id,author_id=u.id,body=data.reason,created_at=at))
    return mutate_staff(no,db,u,data.expected_version,f)

@app.get("/api/notifications")
def notifications(unread:bool=False,db=Depends(get_db),u=Depends(require_user)):
    stmt=select(Notification).where(Notification.user_id==u.id); 
    if unread: stmt=stmt.where(Notification.is_read==False)
    items=db.scalars(stmt.order_by(Notification.created_at.desc())).all(); return {"items":[{"id":n.id,"ticket_id":n.ticket_id,"type":n.type,"message":n.message,"is_read":n.is_read,"created_at":format_dt(n.created_at)} for n in items],"unread_count":db.scalar(select(func.count()).where(Notification.user_id==u.id,Notification.is_read==False))}
@app.post("/api/notifications/{nid}/read")
def read(nid:int,db=Depends(get_db),u=Depends(require_user)):
    n=db.get(Notification,nid)
    if not n or n.user_id!=u.id: err("not_found","Notification not found",404)
    n.is_read=True; db.commit(); return {"ok":True}

@app.get("/api/dashboard/member")
def member_dashboard(db=Depends(get_db),u=Depends(roles("member"))):
    rows=db.scalars(select(Ticket).where(Ticket.member_id==u.id)).all(); return {"counts":{s:sum(t.status==s for t in rows) for s in ["open","in_progress","resolved","closed","reopened","escalated"]},"awaiting_confirmation":[serialize_ticket(db,t) for t in rows if t.status=="resolved"]}
@app.get("/api/dashboard/summary")
def summary(db=Depends(get_db),u=Depends(roles("head"))):
    rows=db.scalars(select(Ticket)).all(); active=[t for t in rows if t.status in OPEN]; at=now(); overdue=[t for t in active if t.status=="escalated" or (t.due_at and utc(t.due_at)<=at and not t.waiting_for_member)]; resolved=[t for t in rows if t.resolved_at and t.status in {"resolved","closed"} and utc(t.resolved_at).date()==at.date()]; vals=[t.resolution_seconds for t in rows if t.resolution_seconds is not None]; cats=[{"category":c,"total":sum(t.category==c for t in rows),"active":sum(t.category==c and t in active for t in rows)} for c in CATEGORIES]; wall=[(utc(t.resolved_at)-utc(t.created_at)).total_seconds() for t in rows if t.resolved_at]; return {"open":len(active),"overdue":len(overdue),"escalated":sum(t.status=="escalated" for t in rows),"resolved_today":len(resolved),"avg_resolution_seconds":sum(vals)/len(vals) if vals else 0,"avg_wall_clock_resolution_seconds":sum(wall)/len(wall) if wall else 0,"unassigned":sum(t.assignee_id is None and t in active for t in rows),"by_category":cats}

@app.get("/api/admin/settings")
def settings_get(db=Depends(get_db),u=Depends(roles("agent","head"))):
    return {"tat_minutes":{p:db.get(TatTarget,p).target_minutes for p in ["high","medium","low"]},**{k:get_setting(db,k) for k in ["reopen_window_days","max_reopens","auto_close_days"]}}
@app.put("/api/admin/settings")
def settings_put(data:SettingsUpdate,db=Depends(get_db),u=Depends(roles("head"))):
    if set(data.tat_minutes)!={"high","medium","low"} or any(v<1 for v in data.tat_minutes.values()): err("validation_error","tat_minutes must contain positive high, medium, and low values",422)
    at=now()
    for p,v in data.tat_minutes.items(): db.get(TatTarget,p).target_minutes=v; db.get(TatTarget,p).updated_at=at; db.get(TatTarget,p).updated_by=u.id
    for k in ["reopen_window_days","max_reopens","auto_close_days"]: s=db.get(AppSetting,k); s.value_int=getattr(data,k); s.updated_at=at; s.updated_by=u.id
    for t in db.scalars(select(Ticket).where(Ticket.status.in_(OPEN),Ticket.waiting_for_member==False)).all(): t.due_at=at+timedelta(seconds=max(0,target(db,t.priority)-elapsed(t,at))); t.version+=1; t.updated_at=at
    db.commit(); return settings_get(db,u)
def run_escalation(db):
    at=now(); count=0; heads=db.scalars(select(User).where(User.role=="head",User.is_active==True)).all()
    for t in db.scalars(select(Ticket).where(Ticket.status.in_(["open","in_progress","reopened"]),Ticket.waiting_for_member==False,Ticket.due_at<=at)).all():
        t.status="escalated"; t.escalated_at=at; t.escalation_reason=f"TAT of {t.priority} exceeded: active time elapsed (member-waiting time excluded)"; t.version+=1; t.updated_at=at; event(db,t,None,"escalated",reason=t.escalation_reason)
        recipients=heads+([db.get(User,t.assignee_id)] if t.assignee_id else [])
        for recipient in recipients: db.add(Notification(user_id=recipient.id,ticket_id=t.id,type="escalation",message=f"{number(t)} has breached its {t.priority} target",created_at=at))
        count+=1
    db.commit(); return count
def run_auto_close(db):
    at=now(); days=get_setting(db,"auto_close_days"); count=0
    for t in db.scalars(select(Ticket).where(Ticket.status=="resolved",Ticket.resolved_at!=None)).all():
        if utc(t.resolved_at)+timedelta(days=days)<=at:
            t.status="closed"; t.closed_at=at; t.version+=1; t.updated_at=at; event(db,t,None,"auto_closed","resolved","closed"); db.add(Notification(user_id=t.member_id,ticket_id=t.id,type="auto_closed",message=f"{number(t)} was closed automatically",created_at=at)); count+=1
    db.commit(); return count
def run_jobs():
    db=SessionLocal()
    try: return {"escalated":run_escalation(db),"auto_closed":run_auto_close(db)}
    finally: db.close()
@app.post("/api/admin/jobs/run")
def jobs(db=Depends(get_db),u=Depends(roles("head"))): return {"escalated":run_escalation(db),"auto_closed":run_auto_close(db)}

@app.post("/api/tickets/{no}/internal-tickets",status_code=201)
def internal_create(no:str,data:InternalCreate,db=Depends(get_db),u=Depends(roles("agent","head"))):
    t=get_ticket(db,no); check_version(t,data.expected_version)
    if data.team not in {"rewards","finance","technical","operations"}: err("validation_error","Unknown internal team",422)
    at=now(); item=InternalTicket(ticket_id=t.id,team=data.team,title=data.title.strip(),description=data.description.strip(),created_by=u.id,created_at=at); db.add(item); event(db,t,u,"internal_ticket_created",new=data.team); touch(t,at); db.commit(); return {"id":item.id,"internal_number":f"INT-{item.id:04d}","team":item.team,"title":item.title,"description":item.description,"status":item.status,"created_at":format_dt(item.created_at)}
@app.get("/api/internal-tickets")
def internal_list(db=Depends(get_db),u=Depends(roles("agent","head"))):
    rows=db.scalars(select(InternalTicket).order_by(InternalTicket.created_at.desc())).all(); return {"items":[{"id":x.id,"internal_number":f"INT-{x.id:04d}","ticket_number":f"TKT-{x.ticket_id:04d}","team":x.team,"title":x.title,"description":x.description,"status":x.status,"completion_note":x.completion_note} for x in rows]}
@app.post("/api/internal-tickets/{internal_id}/complete")
def internal_complete(internal_id:int,data:InternalComplete,db=Depends(get_db),u=Depends(roles("agent","head"))):
    item=db.get(InternalTicket,internal_id)
    if not item: err("not_found","Internal ticket not found",404)
    if item.status=="done": err("conflict","Internal ticket is already complete",409)
    at=now(); item.status="done"; item.completed_by=u.id; item.completed_at=at; item.completion_note=data.note; t=db.get(Ticket,item.ticket_id); event(db,t,u,"internal_ticket_done",new=item.team,reason=data.note); db.add(Notification(user_id=t.member_id,ticket_id=t.id,type="internal_done",message=f"Internal check completed for {number(t)}",created_at=at)); db.commit(); return {"ok":True,"status":"done"}
@app.get("/api/saved-replies")
def saved_list(category:str|None=None,db=Depends(get_db),u=Depends(roles("agent","head"))):
    stmt=select(SavedReply).where(SavedReply.is_active==True)
    if category: stmt=stmt.where((SavedReply.category==category)|(SavedReply.category==None))
    rows=db.scalars(stmt.order_by(SavedReply.title)).all(); return {"items":[{"id":x.id,"title":x.title,"body":x.body,"category":x.category} for x in rows]}
@app.post("/api/saved-replies",status_code=201)
def saved_create(data:SavedReplyCreate,db=Depends(get_db),u=Depends(roles("head"))):
    if data.category and data.category not in CATEGORIES: err("validation_error","Unknown category",422)
    at=now(); item=SavedReply(title=data.title.strip(),body=data.body.strip(),category=data.category,created_by=u.id,created_at=at,updated_at=at); db.add(item); db.commit(); return {"id":item.id,"title":item.title,"body":item.body,"category":item.category}
@app.delete("/api/saved-replies/{reply_id}")
def saved_delete(reply_id:int,db=Depends(get_db),u=Depends(roles("head"))):
    item=db.get(SavedReply,reply_id)
    if not item: err("not_found","Saved reply not found",404)
    item.is_active=False; item.updated_at=now(); db.commit(); return {"ok":True}
