"""
Campus Connect Meetups Service
Handles event creation, management, and RSVP functionality
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from datetime import datetime
import os
import mysql.connector
from mysql.connector import Error
import jwt
import logging
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Campus Connect Meetups Service",
    description="Meetups and events management service",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "meetups_db")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            database=MYSQL_DATABASE,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        return connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# Pydantic models
class MeetupCreate(BaseModel):
    title: str
    description: str = None
    host_name: str
    social_handle: str = None
    location: str
    latitude: float = None
    longitude: float = None
    event_date: datetime
    max_participants: int = None

    @validator('event_date')
    def validate_event_date(cls, v):
        if v <= datetime.now():
            raise ValueError('Event date must be in the future')
        return v

class MeetupUpdate(BaseModel):
    title: str = None
    description: str = None
    host_name: str = None
    social_handle: str = None
    location: str = None
    latitude: float = None
    longitude: float = None
    event_date: datetime = None
    max_participants: int = None

class MeetupResponse(BaseModel):
    id: int
    title: str
    description: str
    host_name: str
    social_handle: str
    location: str
    latitude: float
    longitude: float
    event_date: datetime
    max_participants: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    participant_count: int = 0

class RSVPRequest(BaseModel):
    status: str  # 'yes', 'no', 'maybe'

class ParticipantResponse(BaseModel):
    id: int
    meetup_id: int
    user_id: int
    rsvp_status: str
    joined_at: datetime

# Helper functions
def verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """Verify JWT token and return user information"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_user_from_token(credentials: HTTPAuthorizationCredentials) -> int:
    """Extract user ID from JWT token"""
    user_info = verify_token(credentials)
    return user_info["user_id"]

def create_meetup(meetup_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO meetups (title, description, host_name, social_handle, location,
                               latitude, longitude, event_date, max_participants, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            meetup_data["title"],
            meetup_data.get("description"),
            meetup_data["host_name"],
            meetup_data.get("social_handle"),
            meetup_data["location"],
            meetup_data.get("latitude"),
            meetup_data.get("longitude"),
            meetup_data["event_date"],
            meetup_data.get("max_participants"),
            user_id
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_meetup_by_id(meetup_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT m.*, COUNT(p.id) as participant_count
            FROM meetups m
            LEFT JOIN meetup_participants p ON m.id = p.meetup_id
            WHERE m.id = %s
            GROUP BY m.id
        """, (meetup_id,))
        meetup = cursor.fetchone()
        return meetup
    finally:
        cursor.close()
        connection.close()

def get_all_meetups(limit: int = 50, offset: int = 0, upcoming_only: bool = True):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT m.*, COUNT(p.id) as participant_count
            FROM meetups m
            LEFT JOIN meetup_participants p ON m.id = p.meetup_id
        """
        params = []

        if upcoming_only:
            query += " WHERE m.event_date > NOW()"
        else:
            query += " WHERE 1=1"

        query += """
            GROUP BY m.id
            ORDER BY m.event_date ASC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        cursor.execute(query, params)
        meetups = cursor.fetchall()
        return meetups
    finally:
        cursor.close()
        connection.close()

def update_meetup(meetup_id: int, update_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the creator
        cursor.execute("SELECT created_by FROM meetups WHERE id = %s", (meetup_id,))
        meetup = cursor.fetchone()
        if not meetup or meetup[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this meetup")

        # Build update query
        update_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                params.append(value)

        if not update_fields:
            return

        params.append(meetup_id)
        query = f"UPDATE meetups SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def delete_meetup(meetup_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the creator
        cursor.execute("SELECT created_by FROM meetups WHERE id = %s", (meetup_id,))
        meetup = cursor.fetchone()
        if not meetup or meetup[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this meetup")

        cursor.execute("DELETE FROM meetups WHERE id = %s", (meetup_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def rsvp_meetup(meetup_id: int, user_id: int, status: str):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if meetup exists and is not full
        cursor.execute("""
            SELECT max_participants, (
                SELECT COUNT(*) FROM meetup_participants WHERE meetup_id = %s AND rsvp_status = 'yes'
            ) as current_participants
            FROM meetups WHERE id = %s
        """, (meetup_id, meetup_id))
        meetup = cursor.fetchone()

        if not meetup:
            raise HTTPException(status_code=404, detail="Meetup not found")

        max_participants, current_participants = meetup

        if status == 'yes' and max_participants and current_participants >= max_participants:
            raise HTTPException(status_code=400, detail="Meetup is full")

        # Check if user already RSVPed
        cursor.execute("""
            SELECT id FROM meetup_participants WHERE meetup_id = %s AND user_id = %s
        """, (meetup_id, user_id))
        existing = cursor.fetchone()

        if existing:
            # Update existing RSVP
            cursor.execute("""
                UPDATE meetup_participants SET rsvp_status = %s WHERE meetup_id = %s AND user_id = %s
            """, (status, meetup_id, user_id))
        else:
            # Create new RSVP
            cursor.execute("""
                INSERT INTO meetup_participants (meetup_id, user_id, rsvp_status)
                VALUES (%s, %s, %s)
            """, (meetup_id, user_id, status))

        connection.commit()
    finally:
        cursor.close()
        connection.close()

def get_meetup_participants(meetup_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM meetup_participants WHERE meetup_id = %s ORDER BY joined_at DESC
        """, (meetup_id,))
        participants = cursor.fetchall()
        return participants
    finally:
        cursor.close()
        connection.close()

def get_user_rsvp_status(meetup_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT rsvp_status FROM meetup_participants WHERE meetup_id = %s AND user_id = %s
        """, (meetup_id, user_id))
        result = cursor.fetchone()
        return result['rsvp_status'] if result else None
    finally:
        cursor.close()
        connection.close()

# API endpoints
@app.post("/", response_model=MeetupResponse)
async def create_meetup_endpoint(
    meetup: MeetupCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new meetup"""
    user_id = get_user_from_token(credentials)
    meetup_data = meetup.dict()
    meetup_id = create_meetup(meetup_data, user_id)
    created_meetup = get_meetup_by_id(meetup_id)

    return MeetupResponse(**created_meetup)

@app.get("/", response_model=List[MeetupResponse])
async def get_meetups(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    upcoming_only: bool = Query(True)
):
    """Get all meetups"""
    meetups = get_all_meetups(limit, offset, upcoming_only)
    return [MeetupResponse(**meetup) for meetup in meetups]

@app.get("/{meetup_id}", response_model=MeetupResponse)
async def get_meetup(meetup_id: int):
    """Get a specific meetup by ID"""
    meetup = get_meetup_by_id(meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")

    return MeetupResponse(**meetup)

@app.put("/{meetup_id}", response_model=MeetupResponse)
async def update_meetup_endpoint(
    meetup_id: int,
    meetup_update: MeetupUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a meetup"""
    user_id = get_user_from_token(credentials)
    update_data = {k: v for k, v in meetup_update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_meetup(meetup_id, update_data, user_id)
    updated_meetup = get_meetup_by_id(meetup_id)

    return MeetupResponse(**updated_meetup)

@app.delete("/{meetup_id}")
async def delete_meetup_endpoint(
    meetup_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a meetup"""
    user_id = get_user_from_token(credentials)
    delete_meetup(meetup_id, user_id)

    return {"message": "Meetup deleted successfully"}

@app.post("/{meetup_id}/rsvp")
async def rsvp_meetup_endpoint(
    meetup_id: int,
    rsvp: RSVPRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """RSVP to a meetup"""
    user_id = get_user_from_token(credentials)

    if rsvp.status not in ['yes', 'no', 'maybe']:
        raise HTTPException(status_code=400, detail="Invalid RSVP status")

    rsvp_meetup(meetup_id, user_id, rsvp.status)

    return {"message": f"RSVP status updated to {rsvp.status}"}

@app.get("/{meetup_id}/participants", response_model=List[ParticipantResponse])
async def get_participants(meetup_id: int):
    """Get all participants for a meetup"""
    # Verify meetup exists
    meetup = get_meetup_by_id(meetup_id)
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")

    participants = get_meetup_participants(meetup_id)
    return [ParticipantResponse(**participant) for participant in participants]

@app.get("/{meetup_id}/my-rsvp")
async def get_my_rsvp(
    meetup_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current user's RSVP status for a meetup"""
    user_id = get_user_from_token(credentials)
    status = get_user_rsvp_status(meetup_id, user_id)

    return {"rsvp_status": status}

@app.get("/search")
async def search_meetups(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50)
):
    """Search meetups by title or description"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT m.*, COUNT(p.id) as participant_count
            FROM meetups m
            LEFT JOIN meetup_participants p ON m.id = p.meetup_id
            WHERE (m.title LIKE %s OR m.description LIKE %s OR m.location LIKE %s)
            AND m.event_date > NOW()
            GROUP BY m.id
            ORDER BY m.event_date ASC
            LIMIT %s
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))

        meetups = cursor.fetchall()
        return [MeetupResponse(**meetup) for meetup in meetups]
    finally:
        cursor.close()
        connection.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "meetups"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MEETUPS_SERVICE_PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)