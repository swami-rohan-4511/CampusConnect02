from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse as _FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import os
import uuid
import shutil
import json
import logging
import psycopg2
import psycopg2.extras
from jose import jwt
from datetime import datetime, timedelta
import bcrypt as bcryptlib
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Campus Connect API",
    description="Campus Connect unified API",
    version="1.0.0"
)

cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# SPA routing: serve index.html for browser page-load requests on frontend paths.
# Browser navigations send Accept: text/html — API XHR calls do not.
_SPA_PATHS = {
    '/', '/meetups', '/marketplace', '/stolen-found', '/rooms', '/rental',
    '/clubs', '/jobs', '/notes', '/food', '/profile', '/login', '/signup', '/admin',
}

@app.middleware("http")
async def spa_routing_middleware(request: Request, call_next):
    if _frontend_ready:
        path = request.url.path
        accept = request.headers.get('accept', '')
        if 'text/html' in accept and path in _SPA_PATHS:
            return _FileResponse(os.path.join(FRONTEND_BUILD, 'index.html'))
    return await call_next(request)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

def _remove_upload(image_url: str):
    try:
        filename = image_url.split("/uploads/")[-1]
        fp = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(fp):
            os.remove(fp)
    except Exception:
        pass

# Serve built React frontend in production
FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "../../frontend/build")
_frontend_ready = os.path.isdir(FRONTEND_BUILD) and os.path.exists(os.path.join(FRONTEND_BUILD, "index.html"))

security = HTTPBearer(auto_error=False)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    import secrets
    JWT_SECRET_KEY = secrets.token_hex(32)
    logger.warning("JWT_SECRET_KEY not set, using auto-generated key. Set JWT_SECRET_KEY env var for production.")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days — persistent login

DATABASE_URL = os.getenv("DATABASE_URL")

@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def create_token(user_id: int, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None

class MeetupCreate(BaseModel):
    title: str
    description: Optional[str] = None
    host_name: str
    social_handle: Optional[str] = None
    location: str
    event_date: str
    max_participants: Optional[int] = None

class RSVPRequest(BaseModel):
    status: str

@app.get("/")
async def root():
    if _frontend_ready:
        from fastapi.responses import FileResponse as _FR
        return _FR(os.path.join(FRONTEND_BUILD, "index.html"))
    return {"message": "Campus Connect API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/auth/register")
async def register(req: RegisterRequest):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id FROM users WHERE email = %s", (req.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed = bcryptlib.hashpw(req.password.encode("utf-8"), bcryptlib.gensalt()).decode("utf-8")
        cur.execute(
            "INSERT INTO users (email, password_hash, full_name, phone, role) VALUES (%s, %s, %s, %s, 'student') RETURNING id, email, full_name, role",
            (req.email, hashed, req.full_name, req.phone)
        )
        user = dict(cur.fetchone())
        token = create_token(user["id"], user["email"], user["role"])
        return {"access_token": token, "user": user}

@app.post("/auth/login")
async def login(req: LoginRequest):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, email, password_hash, full_name, role, is_active FROM users WHERE email = %s", (req.email,))
        user = cur.fetchone()
        if not user or not bcryptlib.checkpw(req.password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user["is_active"]:
            raise HTTPException(status_code=403, detail="Account disabled")
        token = create_token(user["id"], user["email"], user["role"])
        return {
            "access_token": token,
            "user": {"id": user["id"], "email": user["email"], "full_name": user["full_name"], "role": user["role"]}
        }

@app.get("/auth/verify-token")
async def verify_token(user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, email, full_name, role FROM users WHERE id = %s", (user["user_id"],))
        db_user = cur.fetchone()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(db_user)

@app.get("/profile/activity")
async def get_my_activity(user=Depends(get_current_user)):
    uid = user["user_id"]
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT id, name, type, location, image_url, created_at FROM food_outlets WHERE owner_id = %s ORDER BY created_at DESC", (uid,))
        food_stalls = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT id, title, description, location, event_date, created_at FROM meetups WHERE created_by = %s ORDER BY created_at DESC", (uid,))
        meetups = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT id, title, price, category, status, created_at FROM items WHERE seller_id = %s ORDER BY created_at DESC", (uid,))
        marketplace = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT id, title, room_type, rent_amount, location, status, created_at FROM rooms WHERE owner_id = %s ORDER BY created_at DESC", (uid,))
        rooms = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT id, name, category, daily_rate, availability_status, created_at FROM rental_items WHERE owner_id = %s ORDER BY created_at DESC", (uid,))
        rentals = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT id, name, category, created_at FROM clubs WHERE president_id = %s ORDER BY created_at DESC", (uid,))
        clubs = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT id, title, company_name, job_type, status, created_at FROM jobs WHERE posted_by = %s ORDER BY created_at DESC", (uid,))
        jobs = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT id, title, subject, file_type, download_count, created_at FROM notes WHERE uploaded_by = %s ORDER BY created_at DESC", (uid,))
        notes = [dict(r) for r in cur.fetchall()]

        return {
            "food_stalls": food_stalls,
            "meetups": meetups,
            "marketplace": marketplace,
            "rooms": rooms,
            "rentals": rentals,
            "clubs": clubs,
            "jobs": jobs,
            "notes": notes,
        }

@app.get("/auth/users")
async def get_users(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, email, full_name, role, is_active, created_at FROM users ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]

@app.delete("/auth/users/{user_id}")
async def delete_user(user_id: int, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if user_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        return {"message": "User deleted"}

@app.patch("/auth/users/{user_id}/role")
async def update_user_role(user_id: int, body: dict, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if user_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    new_role = body.get("role")
    if new_role not in ("student", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'student' or 'admin'")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("UPDATE users SET role = %s WHERE id = %s RETURNING id, email, full_name, role", (new_role, user_id))
        updated = cur.fetchone()
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(updated)

@app.get("/meetups")
async def get_meetups():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM meetups ORDER BY event_date DESC")
        return [dict(r) for r in cur.fetchall()]

@app.post("/meetups")
async def create_meetup(meetup: MeetupCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """INSERT INTO meetups (title, description, host_name, social_handle, location, event_date, max_participants, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
            (meetup.title, meetup.description, meetup.host_name, meetup.social_handle,
             meetup.location, meetup.event_date, meetup.max_participants, user["user_id"])
        )
        return dict(cur.fetchone())

@app.post("/meetups/{meetup_id}/rsvp")
async def rsvp_meetup(meetup_id: int, rsvp: RSVPRequest, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO meetup_participants (meetup_id, user_id, rsvp_status) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (meetup_id, user["user_id"], rsvp.status)
        )
        if rsvp.status == "yes":
            cur.execute("UPDATE meetups SET participant_count = participant_count + 1 WHERE id = %s", (meetup_id,))
        return {"message": "RSVP recorded"}

class MarketplaceItemCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    price: float
    category: str
    condition_status: Optional[str] = "used"
    location: Optional[str] = ""
    contact_info: Optional[str] = ""
    is_negotiable: Optional[bool] = True

@app.get("/marketplace")
async def get_marketplace(category: Optional[str] = None, status: Optional[str] = None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT i.*, u.full_name as seller_display_name, u.email as seller_email,
                   u.created_at as seller_joined
            FROM items i
            LEFT JOIN users u ON i.seller_id = u.id
        """
        conditions, params = [], []
        if category and category != 'all':
            conditions.append("i.category = %s"); params.append(category)
        if status and status != 'all':
            conditions.append("i.status = %s"); params.append(status)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY i.created_at DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("images") is None: d["images"] = []
            result.append(d)
        return result

@app.post("/marketplace")
async def create_marketplace_item(item: MarketplaceItemCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id = %s", (user["user_id"],))
        u = cur.fetchone()
        seller_name = u["full_name"] if u else ""
        cur.execute(
            """INSERT INTO items (title, description, price, category, condition_status,
               location, contact_info, is_negotiable, seller_id, seller_name, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'available') RETURNING *""",
            (item.title, item.description, item.price, item.category, item.condition_status,
             item.location, item.contact_info, item.is_negotiable,
             user["user_id"], seller_name)
        )
        row = dict(cur.fetchone())
        if row.get("images") is None: row["images"] = []
        return row

@app.patch("/marketplace/{item_id}/status")
async def update_marketplace_status(item_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT seller_id FROM items WHERE id = %s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["seller_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        new_status = body.get("status", "available")
        cur.execute("UPDATE items SET status = %s WHERE id = %s RETURNING *", (new_status, item_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.post("/marketplace/{item_id}/image")
async def upload_marketplace_image(item_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only image files allowed")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT seller_id, images FROM items WHERE id = %s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["seller_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"market_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        image_url = f"/uploads/{filename}"
        existing = row["images"] if row["images"] else []
        updated_images = existing + [image_url]
        cur.execute("UPDATE items SET images = %s WHERE id = %s RETURNING *",
                    (json.dumps(updated_images), item_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.delete("/marketplace/{item_id}")
async def delete_marketplace_item(item_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT seller_id FROM items WHERE id = %s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["seller_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM items WHERE id = %s", (item_id,))
        return {"message": "Item removed"}

@app.patch("/marketplace/{item_id}")
async def update_marketplace_item(item_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT seller_id FROM items WHERE id = %s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["seller_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        allowed = ["title", "description", "price", "category", "condition_status", "location", "contact_info", "is_negotiable"]
        updates = {k: v for k, v in body.items() if k in allowed}
        if not updates: raise HTTPException(status_code=400, detail="Nothing to update")
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [item_id]
        cur.execute(f"UPDATE items SET {set_clause} WHERE id = %s RETURNING *", values)
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.delete("/marketplace/{item_id}/image")
async def delete_marketplace_image(item_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT seller_id, images FROM items WHERE id = %s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["seller_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        image_url = body.get("image_url", "")
        existing = row["images"] if row["images"] else []
        updated_images = [img for img in existing if img != image_url]
        cur.execute("UPDATE items SET images = %s WHERE id = %s RETURNING *", (json.dumps(updated_images), item_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        _remove_upload(image_url)
        return updated

class ReportCreate(BaseModel):
    item_name: str
    description: Optional[str] = ""
    category: str
    report_type: str
    location: Optional[str] = ""
    contact_info: Optional[str] = ""

@app.get("/stolen-found")
async def get_reports(report_type: Optional[str] = None, category: Optional[str] = None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT r.*, u.full_name as reporter_display_name, u.created_at as reporter_joined
            FROM reports r LEFT JOIN users u ON r.reported_by = u.id
        """
        conditions, params = [], []
        if report_type and report_type != 'all':
            conditions.append("r.report_type = %s"); params.append(report_type)
        if category and category != 'all':
            conditions.append("r.category = %s"); params.append(category)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY r.created_at DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("images") is None: d["images"] = []
            result.append(d)
        return result

@app.post("/stolen-found")
async def create_report(report: ReportCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id = %s", (user["user_id"],))
        u = cur.fetchone()
        reporter_name = u["full_name"] if u else ""
        cur.execute(
            """INSERT INTO reports (item_name, description, category, report_type, location,
               contact_info, reported_by, reporter_name, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'active') RETURNING *""",
            (report.item_name, report.description, report.category, report.report_type,
             report.location, report.contact_info, user["user_id"], reporter_name)
        )
        row = dict(cur.fetchone())
        if row.get("images") is None: row["images"] = []
        return row

@app.post("/stolen-found/{report_id}/image")
async def upload_report_image(report_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only image files allowed")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT reported_by, images FROM reports WHERE id = %s", (report_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Report not found")
        if user.get("role") != "admin" and row["reported_by"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"report_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        image_url = f"/uploads/{filename}"
        existing = row["images"] if row["images"] else []
        updated_images = existing + [image_url]
        cur.execute("UPDATE reports SET images = %s WHERE id = %s RETURNING *",
                    (json.dumps(updated_images), report_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.patch("/stolen-found/{report_id}/status")
async def update_report_status(report_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT reported_by FROM reports WHERE id = %s", (report_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Report not found")
        if user.get("role") != "admin" and row["reported_by"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        new_status = body.get("status", "active")
        cur.execute("UPDATE reports SET status = %s WHERE id = %s RETURNING *", (new_status, report_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.post("/stolen-found/{report_id}/mark-resolved")
async def resolve_report(report_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("UPDATE reports SET status = 'resolved' WHERE id = %s RETURNING *", (report_id,))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.patch("/stolen-found/{report_id}")
async def update_report(report_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT reported_by FROM reports WHERE id = %s", (report_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Report not found")
        if user.get("role") != "admin" and row["reported_by"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        allowed = ["item_name", "description", "category", "report_type", "location", "contact_info"]
        updates = {k: v for k, v in body.items() if k in allowed}
        if not updates: raise HTTPException(status_code=400, detail="Nothing to update")
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [report_id]
        cur.execute(f"UPDATE reports SET {set_clause} WHERE id = %s RETURNING *", values)
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.delete("/stolen-found/{report_id}/image")
async def delete_report_image(report_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT reported_by, images FROM reports WHERE id = %s", (report_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Report not found")
        if user.get("role") != "admin" and row["reported_by"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        image_url = body.get("image_url", "")
        existing = row["images"] if row["images"] else []
        updated_images = [img for img in existing if img != image_url]
        cur.execute("UPDATE reports SET images = %s WHERE id = %s RETURNING *", (json.dumps(updated_images), report_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        _remove_upload(image_url)
        return updated

@app.delete("/stolen-found/{report_id}")
async def delete_report(report_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT reported_by FROM reports WHERE id = %s", (report_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Report not found")
        if user.get("role") != "admin" and row[0] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM reports WHERE id = %s", (report_id,))
        return {"message": "Report deleted"}

class RoomCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    location: str
    rent_amount: float
    deposit_amount: Optional[float] = 0
    room_type: str
    gender_preference: Optional[str] = "any"
    amenities: Optional[list] = []
    contact_info: Optional[str] = ""

@app.get("/rooms")
async def get_rooms(status: Optional[str] = None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if status:
            cur.execute("SELECT * FROM rooms WHERE status = %s ORDER BY created_at DESC", (status,))
        else:
            cur.execute("SELECT * FROM rooms ORDER BY created_at DESC")
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("amenities") is None:
                d["amenities"] = []
            if d.get("images") is None:
                d["images"] = []
            result.append(d)
        return result

@app.post("/rooms")
async def create_room(room: RoomCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """INSERT INTO rooms (title, description, location, rent_amount, deposit_amount,
               room_type, gender_preference, amenities, contact_info, owner_id, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'available') RETURNING *""",
            (room.title, room.description, room.location, room.rent_amount, room.deposit_amount,
             room.room_type, room.gender_preference, json.dumps(room.amenities),
             room.contact_info, user["user_id"])
        )
        row = dict(cur.fetchone())
        if row.get("amenities") is None: row["amenities"] = []
        if row.get("images") is None: row["images"] = []
        return row

@app.patch("/rooms/{room_id}/status")
async def update_room_status(room_id: int, body: dict, user=Depends(get_current_user)):
    new_status = body.get("status")
    if new_status not in ("available", "taken"):
        raise HTTPException(status_code=400, detail="Status must be 'available' or 'taken'")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id FROM rooms WHERE id = %s", (room_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Room not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("UPDATE rooms SET status = %s WHERE id = %s RETURNING *", (new_status, room_id))
        updated = dict(cur.fetchone())
        if updated.get("amenities") is None: updated["amenities"] = []
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.post("/rooms/{room_id}/image")
async def upload_room_image(room_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id, images FROM rooms WHERE id = %s", (room_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Room not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"room_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        image_url = f"/uploads/{filename}"
        existing = row["images"] if row["images"] else []
        updated_images = existing + [image_url]
        cur.execute("UPDATE rooms SET images = %s WHERE id = %s RETURNING *",
                    (json.dumps(updated_images), room_id))
        updated = dict(cur.fetchone())
        if updated.get("amenities") is None: updated["amenities"] = []
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.delete("/rooms/{room_id}")
async def delete_room(room_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id FROM rooms WHERE id = %s", (room_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Room not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
        return {"message": "Room deleted"}

@app.patch("/rooms/{room_id}")
async def update_room(room_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id FROM rooms WHERE id = %s", (room_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Room not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        allowed = ["title", "description", "location", "rent_amount", "deposit_amount", "room_type", "gender_preference", "contact_info"]
        updates = {k: v for k, v in body.items() if k in allowed}
        if "amenities" in body:
            updates["amenities"] = json.dumps(body["amenities"])
        if not updates: raise HTTPException(status_code=400, detail="Nothing to update")
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [room_id]
        cur.execute(f"UPDATE rooms SET {set_clause} WHERE id = %s RETURNING *", values)
        updated = dict(cur.fetchone())
        if updated.get("amenities") is None: updated["amenities"] = []
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.delete("/rooms/{room_id}/image")
async def delete_room_image(room_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id, images FROM rooms WHERE id = %s", (room_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Room not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        image_url = body.get("image_url", "")
        existing = row["images"] if row["images"] else []
        updated_images = [img for img in existing if img != image_url]
        cur.execute("UPDATE rooms SET images = %s WHERE id = %s RETURNING *", (json.dumps(updated_images), room_id))
        updated = dict(cur.fetchone())
        if updated.get("amenities") is None: updated["amenities"] = []
        if updated.get("images") is None: updated["images"] = []
        _remove_upload(image_url)
        return updated

class RentalItemCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    category: str
    daily_rate: float
    weekly_rate: Optional[float] = None
    security_deposit: Optional[float] = 0
    location: Optional[str] = ""
    contact_info: Optional[str] = ""
    min_rental_days: Optional[int] = 1
    condition_status: Optional[str] = "good"

@app.get("/rental")
async def get_rentals(category: Optional[str] = None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT r.*, u.full_name as owner_display_name, u.email as owner_email,
                   u.created_at as owner_joined
            FROM rental_items r
            LEFT JOIN users u ON r.owner_id = u.id
        """
        if category and category != 'all':
            cur.execute(query + " WHERE r.category = %s ORDER BY r.created_at DESC", (category,))
        else:
            cur.execute(query + " ORDER BY r.created_at DESC")
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("images") is None: d["images"] = []
            result.append(d)
        return result

@app.post("/rental")
async def create_rental(item: RentalItemCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id = %s", (user["user_id"],))
        u = cur.fetchone()
        owner_name = u["full_name"] if u else ""
        cur.execute(
            """INSERT INTO rental_items (name, description, category, daily_rate, weekly_rate,
               security_deposit, location, contact_info, min_rental_days, condition_status,
               owner_id, owner_name, availability_status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true) RETURNING *""",
            (item.name, item.description, item.category, item.daily_rate, item.weekly_rate,
             item.security_deposit, item.location, item.contact_info, item.min_rental_days,
             item.condition_status, user["user_id"], owner_name)
        )
        row = dict(cur.fetchone())
        if row.get("images") is None: row["images"] = []
        return row

@app.patch("/rental/{item_id}/availability")
async def toggle_rental_availability(item_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id FROM rental_items WHERE id = %s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        new_status = body.get("availability_status", True)
        cur.execute("UPDATE rental_items SET availability_status = %s WHERE id = %s RETURNING *",
                    (new_status, item_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.post("/rental/{item_id}/image")
async def upload_rental_image(item_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id, images FROM rental_items WHERE id = %s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"rental_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        image_url = f"/uploads/{filename}"
        existing = row["images"] if row["images"] else []
        updated_images = existing + [image_url]
        cur.execute("UPDATE rental_items SET images = %s WHERE id = %s RETURNING *",
                    (json.dumps(updated_images), item_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.delete("/rental/{item_id}")
async def delete_rental(item_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id FROM rental_items WHERE id = %s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM rental_items WHERE id = %s", (item_id,))
        return {"message": "Item deleted"}

@app.patch("/rental/{item_id}")
async def update_rental(item_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id FROM rental_items WHERE id = %s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        allowed = ["name", "description", "category", "daily_rate", "weekly_rate", "security_deposit", "location", "contact_info", "min_rental_days", "condition_status"]
        updates = {k: v for k, v in body.items() if k in allowed}
        if not updates: raise HTTPException(status_code=400, detail="Nothing to update")
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [item_id]
        cur.execute(f"UPDATE rental_items SET {set_clause} WHERE id = %s RETURNING *", values)
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        return updated

@app.delete("/rental/{item_id}/image")
async def delete_rental_image(item_id: int, body: dict, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT owner_id, images FROM rental_items WHERE id = %s", (item_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        if user.get("role") != "admin" and row["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        image_url = body.get("image_url", "")
        existing = row["images"] if row["images"] else []
        updated_images = [img for img in existing if img != image_url]
        cur.execute("UPDATE rental_items SET images = %s WHERE id = %s RETURNING *", (json.dumps(updated_images), item_id))
        updated = dict(cur.fetchone())
        if updated.get("images") is None: updated["images"] = []
        _remove_upload(image_url)
        return updated

# ───────────────────── CLUBS ─────────────────────
class ClubCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    category: str
    faculty_advisor: Optional[str] = ""
    meeting_schedule: Optional[str] = ""
    contact_email: Optional[str] = ""
    is_recruiting: Optional[bool] = False

@app.get("/clubs")
async def get_clubs():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT c.*, u.full_name as president_display_name,
                   (SELECT COUNT(*) FROM club_members cm WHERE cm.club_id = c.id) as actual_member_count
            FROM clubs c LEFT JOIN users u ON c.president_id = u.id
            ORDER BY c.name
        """)
        return [dict(r) for r in cur.fetchall()]

@app.post("/clubs")
async def create_club(club: ClubCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id = %s", (user["user_id"],))
        u = cur.fetchone()
        president_name = u["full_name"] if u else ""
        cur.execute(
            """INSERT INTO clubs (name, description, category, faculty_advisor, meeting_schedule,
               contact_email, is_recruiting, president_id, president_name)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
            (club.name, club.description, club.category, club.faculty_advisor,
             club.meeting_schedule, club.contact_email, club.is_recruiting,
             user["user_id"], president_name)
        )
        return dict(cur.fetchone())

@app.post("/clubs/{club_id}/join")
async def join_club(club_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM club_members WHERE club_id=%s AND user_id=%s", (club_id, user["user_id"]))
        if cur.fetchone():
            cur.execute("DELETE FROM club_members WHERE club_id=%s AND user_id=%s", (club_id, user["user_id"]))
            cur.execute("UPDATE clubs SET member_count = GREATEST(member_count - 1, 0) WHERE id=%s", (club_id,))
            return {"message": "left"}
        cur.execute("INSERT INTO club_members (club_id, user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (club_id, user["user_id"]))
        cur.execute("UPDATE clubs SET member_count = member_count + 1 WHERE id=%s", (club_id,))
        return {"message": "joined"}

@app.delete("/clubs/{club_id}")
async def delete_club(club_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT president_id FROM clubs WHERE id=%s", (club_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Club not found")
        if user.get("role") != "admin" and row[0] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM clubs WHERE id=%s", (club_id,))
        return {"message": "Club deleted"}

# ───────────────────── JOBS ─────────────────────
class JobCreate(BaseModel):
    title: str
    company_name: str
    description: Optional[str] = ""
    requirements: Optional[str] = ""
    job_type: str
    location: Optional[str] = ""
    salary_range: Optional[str] = ""
    application_deadline: Optional[str] = None
    contact_email: Optional[str] = ""
    apply_link: Optional[str] = ""
    experience_level: Optional[str] = "entry"
    skills_required: Optional[str] = ""

@app.get("/jobs")
async def get_jobs(job_type: Optional[str] = None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if job_type and job_type != 'all':
            cur.execute("SELECT j.*, u.full_name as poster_display FROM jobs j LEFT JOIN users u ON j.posted_by=u.id WHERE j.status='active' AND j.job_type=%s ORDER BY j.created_at DESC", (job_type,))
        else:
            cur.execute("SELECT j.*, u.full_name as poster_display FROM jobs j LEFT JOIN users u ON j.posted_by=u.id WHERE j.status='active' ORDER BY j.created_at DESC")
        return [dict(r) for r in cur.fetchall()]

@app.post("/jobs")
async def create_job(job: JobCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id=%s", (user["user_id"],))
        u = cur.fetchone()
        poster_name = u["full_name"] if u else ""
        deadline = job.application_deadline if job.application_deadline else None
        cur.execute(
            """INSERT INTO jobs (title, company_name, description, requirements, job_type, location,
               salary_range, application_deadline, contact_email, apply_link, experience_level,
               skills_required, posted_by, poster_name, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active') RETURNING *""",
            (job.title, job.company_name, job.description, job.requirements, job.job_type,
             job.location, job.salary_range, deadline, job.contact_email, job.apply_link,
             job.experience_level, job.skills_required, user["user_id"], poster_name)
        )
        return dict(cur.fetchone())

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT posted_by FROM jobs WHERE id=%s", (job_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Job not found")
        if user.get("role") != "admin" and row[0] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("UPDATE jobs SET status='closed' WHERE id=%s", (job_id,))
        return {"message": "Job closed"}

# ───────────────────── NOTES ─────────────────────
class NoteCreate(BaseModel):
    title: str
    subject: str
    description: Optional[str] = ""
    file_type: Optional[str] = "pdf"
    semester: Optional[int] = None
    branch: Optional[str] = ""
    tags: Optional[list] = []

@app.get("/notes")
async def get_notes(branch: Optional[str] = None, semester: Optional[int] = None):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        conditions, params = [], []
        if branch and branch != 'all':
            conditions.append("n.branch = %s"); params.append(branch)
        if semester:
            conditions.append("n.semester = %s"); params.append(semester)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        cur.execute(f"SELECT n.*, u.full_name as uploader_display FROM notes n LEFT JOIN users u ON n.uploaded_by=u.id{where} ORDER BY n.upvotes DESC, n.created_at DESC", params)
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("tags") is None: d["tags"] = []
            result.append(d)
        return result

@app.post("/notes")
async def create_note(note: NoteCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id=%s", (user["user_id"],))
        u = cur.fetchone()
        uploader_name = u["full_name"] if u else ""
        cur.execute(
            """INSERT INTO notes (title, subject, description, file_type, semester, branch, tags,
               uploaded_by, uploader_name)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
            (note.title, note.subject, note.description, note.file_type, note.semester,
             note.branch, json.dumps(note.tags), user["user_id"], uploader_name)
        )
        row = dict(cur.fetchone())
        if row.get("tags") is None: row["tags"] = []
        return row

@app.post("/notes/{note_id}/file")
async def upload_note_file(note_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT uploaded_by FROM notes WHERE id=%s", (note_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Note not found")
        if user.get("role") != "admin" and row["uploaded_by"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "pdf"
        filename = f"note_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        file_url = f"/uploads/{filename}"
        cur.execute("UPDATE notes SET file_url=%s, file_type=%s WHERE id=%s RETURNING *", (file_url, ext, note_id))
        row = dict(cur.fetchone())
        if row.get("tags") is None: row["tags"] = []
        return row

@app.post("/notes/{note_id}/upvote")
async def upvote_note(note_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("UPDATE notes SET upvotes = upvotes + 1 WHERE id=%s RETURNING *", (note_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Note not found")
        return dict(row)

@app.post("/notes/{note_id}/view")
async def increment_note_views(note_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE notes SET views = views + 1, download_count = download_count + 1 WHERE id=%s", (note_id,))
        return {"ok": True}

@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT uploaded_by FROM notes WHERE id=%s", (note_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Note not found")
        if user.get("role") != "admin" and row[0] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorised")
        cur.execute("DELETE FROM notes WHERE id=%s", (note_id,))
        return {"message": "Note deleted"}

class FoodOutletCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    location: Optional[str] = None
    contact_info: Optional[str] = None
    operating_hours: Optional[str] = None
    delivery_available: Optional[bool] = False

class MenuItemCreate(BaseModel):
    item_name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    is_vegetarian: Optional[bool] = True
    is_available: Optional[bool] = True

def _is_outlet_owner_or_admin(outlet_id: int, user: dict, cur) -> bool:
    cur.execute("SELECT owner_id FROM food_outlets WHERE id = %s", (outlet_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Outlet not found")
    return user.get("role") == "admin" or row["owner_id"] == user["user_id"]

@app.get("/food")
async def get_food_outlets():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM food_outlets ORDER BY name")
        return [dict(r) for r in cur.fetchall()]

@app.post("/food")
async def create_food_outlet(outlet: FoodOutletCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT full_name FROM users WHERE id = %s", (user["user_id"],))
        u = cur.fetchone()
        owner_name = u["full_name"] if u else user.get("email", "")
        cur.execute(
            """INSERT INTO food_outlets (name, type, description, location, contact_info, operating_hours,
               delivery_available, owner_id, owner_name)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
            (outlet.name, outlet.type, outlet.description, outlet.location,
             outlet.contact_info, outlet.operating_hours, outlet.delivery_available,
             user["user_id"], owner_name)
        )
        return dict(cur.fetchone())

@app.post("/food/{outlet_id}/image")
async def upload_outlet_image(outlet_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if not _is_outlet_owner_or_admin(outlet_id, user, cur):
            raise HTTPException(status_code=403, detail="Not authorised")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"outlet_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        image_url = f"/uploads/{filename}"
        cur.execute("UPDATE food_outlets SET image_url = %s WHERE id = %s RETURNING *", (image_url, outlet_id))
        row = cur.fetchone()
        if not row:
            os.remove(filepath)
            raise HTTPException(status_code=404, detail="Outlet not found")
        return dict(row)

@app.delete("/food/{outlet_id}")
async def delete_food_outlet(outlet_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if not _is_outlet_owner_or_admin(outlet_id, user, cur):
            raise HTTPException(status_code=403, detail="Not authorised to delete this outlet")
        cur.execute("DELETE FROM food_outlets WHERE id = %s", (outlet_id,))
        return {"message": "Outlet deleted"}

@app.get("/food/{outlet_id}/menu")
async def get_menu(outlet_id: int):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM menus WHERE outlet_id = %s AND is_available = true ORDER BY category, item_name",
            (outlet_id,)
        )
        return [dict(r) for r in cur.fetchall()]

@app.post("/food/{outlet_id}/menu")
async def add_menu_item(outlet_id: int, item: MenuItemCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if not _is_outlet_owner_or_admin(outlet_id, user, cur):
            raise HTTPException(status_code=403, detail="Not authorised to manage this outlet")
        cur.execute(
            """INSERT INTO menus (outlet_id, item_name, description, price, category, is_vegetarian, is_available)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *""",
            (outlet_id, item.item_name, item.description, item.price,
             item.category, item.is_vegetarian, item.is_available)
        )
        return dict(cur.fetchone())

@app.post("/food/{outlet_id}/menu/{item_id}/image")
async def upload_menu_item_image(
    outlet_id: int,
    item_id: int,
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(status_code=400, detail="Only image files (jpeg, png, webp, gif) are allowed")
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 5 MB")
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if not _is_outlet_owner_or_admin(outlet_id, user, cur):
            raise HTTPException(status_code=403, detail="Not authorised to manage this outlet")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        image_url = f"/uploads/{filename}"
        cur.execute(
            "UPDATE menus SET image_url = %s WHERE id = %s AND outlet_id = %s RETURNING *",
            (image_url, item_id, outlet_id)
        )
        row = cur.fetchone()
        if not row:
            os.remove(filepath)
            raise HTTPException(status_code=404, detail="Menu item not found")
        return dict(row)

@app.delete("/food/{outlet_id}/menu/{item_id}")
async def delete_menu_item(outlet_id: int, item_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if not _is_outlet_owner_or_admin(outlet_id, user, cur):
            raise HTTPException(status_code=403, detail="Not authorised to manage this outlet")
        cur.execute("DELETE FROM menus WHERE id = %s AND outlet_id = %s", (item_id, outlet_id))
        return {"message": "Menu item deleted"}

# Serve React frontend for all non-API routes (production SPA fallback)
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles as StarletteStatic

if _frontend_ready:
    app.mount("/static", StarletteStatic(directory=os.path.join(FRONTEND_BUILD, "static")), name="frontend-static")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_BUILD, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_BUILD, "index.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", os.getenv("API_GATEWAY_PORT", 8000)))
    uvicorn.run(app, host="0.0.0.0", port=port)
