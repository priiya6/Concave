from fastapi.testclient import TestClient
from app.main import app
from app.scripts.seed import seed

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
