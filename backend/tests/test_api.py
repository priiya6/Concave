from fastapi.testclient import TestClient
from app.main import app
from app.scripts.seed import seed
from app.db import SessionLocal
from app.models import Ticket, TicketEvent, Notification, InternalTicket, SavedReply, User
from app.main import run_auto_close
from app.core.clock import now
from datetime import timedelta, timezone

def auth(c,email,password):
    r=c.post('/api/auth/login',json={'email':email,'password':password}); assert r.status_code==200; return {'Authorization':'Bearer '+r.json()['access_token']}
def test_member_create_and_isolation():
    seed(True); c=TestClient(app); h=auth(c,'member1@concave.test','Member@123')
    r=c.post('/api/tickets',headers=h,json={'category':'payment','subject':'Payment missing','description':'My payment for the completed study is missing.'})
    assert r.status_code==201 and r.json()['priority']=='high'
    other=auth(c,'member2@concave.test','Member@123'); assert c.get('/api/tickets/'+r.json()['ticket_number'],headers=other).status_code==404
def test_reasons_and_permissions():
    seed(True); c=TestClient(app); member=auth(c,'member1@concave.test','Member@123'); r=c.post('/api/tickets',headers=member,json={'category':'other','subject':'A question','description':'I need help with my profile information.'}); no=r.json()['ticket_number']; agent=auth(c,'agent1@concave.test','Agent@123')
    assert c.post(f'/api/tickets/{no}/priority',headers=agent,json={'priority':'high','reason':'','expected_version':1}).status_code==422
    assert c.get('/api/dashboard/summary',headers=member).status_code==403
def test_invalid_token_envelope():
    c=TestClient(app); r=c.get('/api/tickets',headers={'Authorization':'Bearer bad'}); assert r.status_code==401 and r.json()['error']['code']=='unauthorized'

def test_agent_workflow_pause_priority_resolve_confirm():
    seed(True); c=TestClient(app); member=auth(c,'member1@concave.test','Member@123'); agent=auth(c,'agent1@concave.test','Agent@123')
    t=c.post('/api/tickets',headers=member,json={'category':'payment','subject':'UPI payout','description':'The payout from my completed study is missing.'}).json(); no=t['ticket_number']; v=t['version']
    r=c.post(f'/api/tickets/{no}/messages',headers=agent,json={'body':'Please share your UPI reference.','request_info':True,'expected_version':v}); assert r.status_code==200 and r.json()['waiting_for_member']
    v=r.json()['version']; r=c.post(f'/api/tickets/{no}/messages',headers=member,json={'body':'Reference is UPI-123456789.','expected_version':v}); assert r.status_code==200 and not r.json()['waiting_for_member']
    v=r.json()['version']; r=c.post(f'/api/tickets/{no}/priority',headers=agent,json={'priority':'medium','reason':'Payment evidence is now available.','expected_version':v}); assert r.status_code==200 and r.json()['priority']=='medium'
    v=r.json()['version']; r=c.post(f'/api/tickets/{no}/resolve',headers=agent,json={'note':'Verified with rewards team.','expected_version':v}); assert r.status_code==200 and r.json()['status']=='resolved'
    v=r.json()['version']; assert c.post(f'/api/tickets/{no}/confirm',headers=member,json={'expected_version':v}).json()['status']=='closed'

def test_escalation_boundary_notifications_and_event():
    seed(True); c=TestClient(app); member=auth(c,'member1@concave.test','Member@123'); head=auth(c,'head@concave.test','Head@123')
    t=c.post('/api/tickets',headers=member,json={'category':'payment','subject':'Boundary ticket','description':'This ticket is intentionally made overdue for testing.'}).json(); db=SessionLocal(); row=db.get(Ticket,t['id']); row.due_at=now()-timedelta(seconds=1); db.commit(); db.close()
    r=c.post('/api/admin/jobs/run',headers=head); assert r.status_code==200 and r.json()['escalated']==1
    detail=c.get('/api/tickets/'+t['ticket_number'],headers=head).json(); assert detail['status']=='escalated' and detail['escalation_reason']
    assert c.get('/api/notifications',headers=head).json()['unread_count']>=1
    db=SessionLocal(); assert db.query(TicketEvent).filter_by(ticket_id=t['id'],event_type='escalated').count()==1; db.close()

def test_settings_recompute_and_bonus_endpoints():
    seed(True); c=TestClient(app); member=auth(c,'member1@concave.test','Member@123'); head=auth(c,'head@concave.test','Head@123')
    t=c.post('/api/tickets',headers=member,json={'category':'other','subject':'Internal follow-up','description':'Please ask the rewards team to confirm my payment status.'}).json(); no=t['ticket_number']
    r=c.post(f'/api/tickets/{no}/internal-tickets',headers=head,json={'team':'rewards','title':'Verify reward','description':'Check the member payment record with rewards.','expected_version':t['version']}); assert r.status_code==201
    iid=r.json()['id']; assert c.post(f'/api/internal-tickets/{iid}/complete',headers=head,json={'note':'Checked rewards ledger.'}).json()['status']=='done'
    assert c.get('/api/internal-tickets',headers=member).status_code==403
    r=c.post('/api/saved-replies',headers=head,json={'title':'Greeting','body':'Thanks for contacting Concave Insights.'}); assert r.status_code==201
    assert c.get('/api/saved-replies',headers=auth(c,'agent1@concave.test','Agent@123')).json()['items']

def test_auto_close_records_history_and_notifies_member():
    seed(True); c=TestClient(app); member=auth(c,'member1@concave.test','Member@123'); agent=auth(c,'agent1@concave.test','Agent@123')
    t=c.post('/api/tickets',headers=member,json={'category':'other','subject':'Old resolved query','description':'Please close this resolved query after the configured period.'}).json(); no=t['ticket_number']; r=c.post(f'/api/tickets/{no}/resolve',headers=agent,json={'expected_version':t['version']}); assert r.status_code==200
    db=SessionLocal(); row=db.get(Ticket,t['id']); row.resolved_at=now()-timedelta(days=8); db.commit(); assert run_auto_close(db)==1; db.close()
    assert c.get('/api/tickets/'+no,headers=member).json()['status']=='closed'; assert c.get('/api/notifications',headers=member).json()['unread_count']>=1
