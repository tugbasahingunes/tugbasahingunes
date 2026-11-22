"""Randevu: appointment booking API for a small practice (tutoring, counselling, beauty, clinic).
FastAPI + SQLite. Endpoints for services, free slots, booking, cancellation and an admin view."""
from __future__ import annotations
import datetime as dt, os, secrets, sqlite3
from contextlib import contextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, field_validator

DB = os.getenv("RANDEVU_DB", str(Path(__file__).parent / "randevu.db"))
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-me")
OPEN, CLOSE, LUNCH = dt.time(9), dt.time(18), (dt.time(12, 30), dt.time(13, 30))
app = FastAPI(title="Randevu API", version="1.0")

@contextmanager
def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    try: yield c; c.commit()
    finally: c.close()

def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS services(id INTEGER PRIMARY KEY, name TEXT, minutes INT, price INT);
        CREATE TABLE IF NOT EXISTS bookings(id INTEGER PRIMARY KEY, service_id INT, start TEXT, end TEXT,
            name TEXT, email TEXT, phone TEXT, note TEXT, code TEXT UNIQUE, status TEXT DEFAULT 'confirmed', created TEXT);
        CREATE INDEX IF NOT EXISTS ix_start ON bookings(start);""")
        if not c.execute("SELECT 1 FROM services").fetchone():
            c.executemany("INSERT INTO services(name,minutes,price) VALUES(?,?,?)",
                          [("Tanışma görüşmesi", 20, 0), ("Birebir ders", 60, 900), ("Veri analizi danışmanlığı", 45, 1200)])
init()

class BookingIn(BaseModel):
    service_id: int
    start: dt.datetime
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    note: str | None = Field(default=None, max_length=500)
    @field_validator("start")
    @classmethod
    def future(cls, v):
        if v.replace(tzinfo=None) < dt.datetime.now(): raise ValueError("start must be in the future")
        return v.replace(tzinfo=None, second=0, microsecond=0)

def service(c, sid):
    s = c.execute("SELECT * FROM services WHERE id=?", (sid,)).fetchone()
    if not s: raise HTTPException(404, "service not found")
    return s

def free_slots(c, day: dt.date, minutes: int, step=15):
    if day.weekday() >= 5: return []
    busy = [(dt.datetime.fromisoformat(r["start"]), dt.datetime.fromisoformat(r["end"])) for r in
            c.execute("SELECT start,end FROM bookings WHERE status='confirmed' AND substr(start,1,10)=?", (day.isoformat(),))]
    busy.append((dt.datetime.combine(day, LUNCH[0]), dt.datetime.combine(day, LUNCH[1])))
    t, end, out = dt.datetime.combine(day, OPEN), dt.datetime.combine(day, CLOSE), []
    while t + dt.timedelta(minutes=minutes) <= end:
        e = t + dt.timedelta(minutes=minutes)
        if t > dt.datetime.now() and all(e <= b0 or t >= b1 for b0, b1 in busy): out.append(t)
        t += dt.timedelta(minutes=step)
    return out

@app.get("/api/services")
def services():
    with db() as c: return [dict(r) for r in c.execute("SELECT * FROM services")]

@app.get("/api/slots")
def slots(service_id: int, day: dt.date):
    with db() as c: return [s.isoformat(timespec="minutes") for s in free_slots(c, day, service(c, service_id)["minutes"])]

@app.post("/api/bookings", status_code=201)
def book(b: BookingIn):
    with db() as c:
        s = service(c, b.service_id)
        c.execute("BEGIN IMMEDIATE")                     # serialises concurrent bookings → no double booking
        if b.start not in free_slots(c, b.start.date(), s["minutes"]):
            raise HTTPException(409, "slot no longer available")
        code = secrets.token_urlsafe(6)
        end = b.start + dt.timedelta(minutes=s["minutes"])
        c.execute("INSERT INTO bookings(service_id,start,end,name,email,phone,note,code,created) VALUES(?,?,?,?,?,?,?,?,?)",
                  (b.service_id, b.start.isoformat(), end.isoformat(), b.name, b.email, b.phone, b.note, code, dt.datetime.now().isoformat()))
        return {"code": code, "service": s["name"], "start": b.start.isoformat(timespec="minutes"), "end": end.isoformat(timespec="minutes")}

@app.delete("/api/bookings/{code}")
def cancel(code: str):
    with db() as c:
        r = c.execute("UPDATE bookings SET status='cancelled' WHERE code=? AND status='confirmed'", (code,))
        if not r.rowcount: raise HTTPException(404, "booking not found")
        return {"cancelled": code}

def admin(x_admin_token: str = Header(...)):
    if not secrets.compare_digest(x_admin_token, ADMIN_TOKEN): raise HTTPException(401, "invalid token")

@app.get("/api/admin/bookings", dependencies=[Depends(admin)])
def all_bookings(day: dt.date | None = None):
    q, p = "SELECT b.*, s.name AS service FROM bookings b JOIN services s ON s.id=b.service_id", ()
    if day: q, p = q + " WHERE substr(start,1,10)=?", (day.isoformat(),)
    with db() as c: return [dict(r) for r in c.execute(q + " ORDER BY start", p)]

@app.get("/api/admin/stats", dependencies=[Depends(admin)])
def stats():
    with db() as c:
        r = c.execute("""SELECT COUNT(*) n, SUM(status='cancelled') cancelled,
                         SUM(CASE WHEN status='confirmed' THEN s.price ELSE 0 END) revenue
                         FROM bookings b JOIN services s ON s.id=b.service_id""").fetchone()
        return {"bookings": r["n"], "cancelled": r["cancelled"] or 0, "revenue_try": r["revenue"] or 0}

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
@app.get("/")
def index(): return FileResponse(Path(__file__).parent / "static" / "index.html")
