import os, datetime as dt, tempfile
os.environ["RANDEVU_DB"] = tempfile.mktemp(suffix=".db"); os.environ["ADMIN_TOKEN"] = "t"
from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app)
def next_weekday():
    d = dt.date.today() + dt.timedelta(days=1)
    while d.weekday() >= 5: d += dt.timedelta(days=1)
    return d
D = next_weekday()
def book(start, sid=2, email="a@b.com"):
    return c.post("/api/bookings", json={"service_id": sid, "start": start, "name": "Ayşe Y", "email": email})

def test_services(): assert len(c.get("/api/services").json()) == 3
def test_slots_skip_lunch():
    s = c.get(f"/api/slots?service_id=2&day={D}").json()
    assert f"{D}T09:00" in s and f"{D}T12:00" not in s and f"{D}T12:30" not in s and f"{D}T17:00" in s and f"{D}T17:15" not in s
def test_book_and_no_double_booking():
    r = book(f"{D}T10:00"); assert r.status_code == 201
    assert book(f"{D}T10:30").status_code == 409            # overlaps 10:00–11:00
    assert f"{D}T10:30" not in c.get(f"/api/slots?service_id=2&day={D}").json()
    code = r.json()["code"]; assert c.delete(f"/api/bookings/{code}").status_code == 200
    assert book(f"{D}T10:30").status_code == 201            # freed after cancellation
def test_weekend_closed():
    sat = D + dt.timedelta(days=(5 - D.weekday()) % 7)
    assert c.get(f"/api/slots?service_id=1&day={sat}").json() == []
def test_validation():
    assert book(f"{D}T15:00", email="not-an-email").status_code == 422
    assert book("2020-01-01T10:00").status_code == 422
    assert book(f"{D}T15:00", sid=99).status_code == 404
def test_admin_requires_token():
    assert c.get("/api/admin/bookings").status_code == 422
    assert c.get("/api/admin/bookings", headers={"x-admin-token": "wrong"}).status_code == 401
    s = c.get("/api/admin/stats", headers={"x-admin-token": "t"}).json(); assert s["bookings"] >= 2 and s["revenue_try"] >= 900
def test_frontend_served(): assert "Randevu al" in c.get("/").text
