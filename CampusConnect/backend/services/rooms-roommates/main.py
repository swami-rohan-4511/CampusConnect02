"""
Campus Connect Rooms & Roommates Service
Handles room listings, roommate matching, and accommodation search
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime
import os
import mysql.connector
from mysql.connector import Error
import jwt
import logging
import json
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Campus Connect Rooms & Roommates Service",
    description="Room listings and roommate matching service",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "rooms_db")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

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
class RoomCreate(BaseModel):
    title: str
    description: str = None
    location: str
    rent_amount: float
    deposit_amount: float = None
    room_type: str  # 'single', 'shared', 'apartment'
    gender_preference: str = "any"  # 'male', 'female', 'any'
    branch_restriction: str = None
    amenities: List[str] = []
    contact_info: str

class RoomUpdate(BaseModel):
    title: str = None
    description: str = None
    location: str = None
    rent_amount: float = None
    deposit_amount: float = None
    room_type: str = None
    gender_preference: str = None
    branch_restriction: str = None
    amenities: List[str] = None
    contact_info: str = None
    status: str = None

class RoomResponse(BaseModel):
    id: int
    title: str
    description: str
    location: str
    rent_amount: float
    deposit_amount: float
    room_type: str
    gender_preference: str
    branch_restriction: str
    amenities: list = []
    images: list = []
    owner_id: int
    contact_info: str
    status: str
    created_at: datetime
    updated_at: datetime

class InquiryCreate(BaseModel):
    message: str

class InquiryResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    message: str
    status: str
    created_at: datetime

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

def create_room(room_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO rooms (title, description, location, rent_amount, deposit_amount,
                             room_type, gender_preference, branch_restriction, amenities,
                             owner_id, contact_info)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            room_data["title"],
            room_data.get("description"),
            room_data["location"],
            room_data["rent_amount"],
            room_data.get("deposit_amount"),
            room_data["room_type"],
            room_data.get("gender_preference", "any"),
            room_data.get("branch_restriction"),
            json.dumps(room_data.get("amenities", [])),
            user_id,
            room_data["contact_info"]
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_room_by_id(room_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()
        if room:
            room['amenities'] = json.loads(room['amenities']) if room['amenities'] else []
            room['images'] = json.loads(room['images']) if room['images'] else []
        return room
    finally:
        cursor.close()
        connection.close()

def get_rooms_by_owner(owner_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM rooms WHERE owner_id = %s ORDER BY created_at DESC", (owner_id,))
        rooms = cursor.fetchall()
        for room in rooms:
            room['amenities'] = json.loads(room['amenities']) if room['amenities'] else []
            room['images'] = json.loads(room['images']) if room['images'] else []
        return rooms
    finally:
        cursor.close()
        connection.close()

def get_all_rooms(limit: int = 50, offset: int = 0, filters: dict = None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = "SELECT * FROM rooms WHERE status = 'available'"
        params = []

        if filters:
            if filters.get('location'):
                query += " AND location LIKE %s"
                params.append(f"%{filters['location']}%")

            if filters.get('min_rent'):
                query += " AND rent_amount >= %s"
                params.append(filters['min_rent'])

            if filters.get('max_rent'):
                query += " AND rent_amount <= %s"
                params.append(filters['max_rent'])

            if filters.get('room_type'):
                query += " AND room_type = %s"
                params.append(filters['room_type'])

            if filters.get('gender_preference') and filters['gender_preference'] != 'any':
                query += " AND (gender_preference = %s OR gender_preference = 'any')"
                params.append(filters['gender_preference'])

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rooms = cursor.fetchall()
        for room in rooms:
            room['amenities'] = json.loads(room['amenities']) if room['amenities'] else []
            room['images'] = json.loads(room['images']) if room['images'] else []
        return rooms
    finally:
        cursor.close()
        connection.close()

def update_room(room_id: int, update_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the owner
        cursor.execute("SELECT owner_id FROM rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()
        if not room or room[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this room")

        update_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                if field == 'amenities':
                    update_fields.append("amenities = %s")
                    params.append(json.dumps(value))
                else:
                    update_fields.append(f"{field} = %s")
                    params.append(value)

        if not update_fields:
            return

        params.append(room_id)
        query = f"UPDATE rooms SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def delete_room(room_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the owner
        cursor.execute("SELECT owner_id FROM rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()
        if not room or room[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this room")

        cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def mark_room_occupied(room_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the owner
        cursor.execute("SELECT owner_id FROM rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()
        if not room or room[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this room")

        cursor.execute("""
            UPDATE rooms SET status = 'occupied', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (room_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def create_inquiry(room_id: int, user_id: int, message: str):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO room_inquiries (room_id, user_id, message)
            VALUES (%s, %s, %s)
        """, (room_id, user_id, message))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_inquiries_for_room(room_id: int, owner_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        # Check if user is the owner
        cursor.execute("SELECT owner_id FROM rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()
        if not room or room[0] != owner_id:
            raise HTTPException(status_code=403, detail="Not authorized to view inquiries")

        cursor.execute("""
            SELECT * FROM room_inquiries WHERE room_id = %s ORDER BY created_at DESC
        """, (room_id,))
        inquiries = cursor.fetchall()
        return inquiries
    finally:
        cursor.close()
        connection.close()

def update_inquiry_status(inquiry_id: int, status: str, owner_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user owns the room for this inquiry
        cursor.execute("""
            SELECT r.owner_id FROM room_inquiries i
            JOIN rooms r ON i.room_id = r.id
            WHERE i.id = %s
        """, (inquiry_id,))
        result = cursor.fetchone()
        if not result or result[0] != owner_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this inquiry")

        cursor.execute("""
            UPDATE room_inquiries SET status = %s WHERE id = %s
        """, (status, inquiry_id))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def search_rooms(query: str, limit: int = 50):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM rooms
            WHERE (title LIKE %s OR description LIKE %s OR location LIKE %s)
            AND status = 'available'
            ORDER BY created_at DESC
            LIMIT %s
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))

        rooms = cursor.fetchall()
        for room in rooms:
            room['amenities'] = json.loads(room['amenities']) if room['amenities'] else []
            room['images'] = json.loads(room['images']) if room['images'] else []
        return rooms
    finally:
        cursor.close()
        connection.close()

def get_room_types():
    """Get all available room types"""
    return ["single", "shared", "apartment"]

def get_gender_preferences():
    """Get all available gender preferences"""
    return ["male", "female", "any"]

# API endpoints
@app.post("/", response_model=RoomResponse)
async def create_room_endpoint(
    room: RoomCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new room listing"""
    user_id = get_user_from_token(credentials)
    room_data = room.dict()
    room_id = create_room(room_data, user_id)
    created_room = get_room_by_id(room_id)

    return RoomResponse(**created_room)

@app.get("/", response_model=List[RoomResponse])
async def get_rooms(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    location: str = Query(None),
    min_rent: float = Query(None, ge=0),
    max_rent: float = Query(None, ge=0),
    room_type: str = Query(None),
    gender_preference: str = Query(None)
):
    """Get all rooms with optional filtering"""
    if room_type and room_type not in get_room_types():
        raise HTTPException(status_code=400, detail="Invalid room type")

    if gender_preference and gender_preference not in get_gender_preferences():
        raise HTTPException(status_code=400, detail="Invalid gender preference")

    filters = {}
    if location:
        filters['location'] = location
    if min_rent is not None:
        filters['min_rent'] = min_rent
    if max_rent is not None:
        filters['max_rent'] = max_rent
    if room_type:
        filters['room_type'] = room_type
    if gender_preference:
        filters['gender_preference'] = gender_preference

    rooms = get_all_rooms(limit, offset, filters)
    return [RoomResponse(**room) for room in rooms]

@app.get("/my-rooms", response_model=List[RoomResponse])
async def get_my_rooms(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get rooms posted by current user"""
    user_id = get_user_from_token(credentials)
    rooms = get_rooms_by_owner(user_id)
    return [RoomResponse(**room) for room in rooms]

@app.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: int):
    """Get a specific room by ID"""
    room = get_room_by_id(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return RoomResponse(**room)

@app.put("/{room_id}", response_model=RoomResponse)
async def update_room_endpoint(
    room_id: int,
    room_update: RoomUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a room listing"""
    user_id = get_user_from_token(credentials)
    update_data = {k: v for k, v in room_update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_room(room_id, update_data, user_id)
    updated_room = get_room_by_id(room_id)

    return RoomResponse(**updated_room)

@app.delete("/{room_id}")
async def delete_room_endpoint(
    room_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a room listing"""
    user_id = get_user_from_token(credentials)
    delete_room(room_id, user_id)

    return {"message": "Room deleted successfully"}

@app.post("/{room_id}/mark-occupied")
async def mark_occupied_endpoint(
    room_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Mark a room as occupied"""
    user_id = get_user_from_token(credentials)
    mark_room_occupied(room_id, user_id)

    return {"message": "Room marked as occupied"}

@app.post("/{room_id}/inquire")
async def create_inquiry_endpoint(
    room_id: int,
    inquiry: InquiryCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create an inquiry for a room"""
    user_id = get_user_from_token(credentials)
    inquiry_id = create_inquiry(room_id, user_id, inquiry.message)

    return {"message": "Inquiry sent successfully", "inquiry_id": inquiry_id}

@app.get("/{room_id}/inquiries", response_model=List[InquiryResponse])
async def get_room_inquiries(
    room_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all inquiries for a room (owner only)"""
    user_id = get_user_from_token(credentials)
    inquiries = get_inquiries_for_room(room_id, user_id)
    return [InquiryResponse(**inquiry) for inquiry in inquiries]

@app.put("/inquiries/{inquiry_id}")
async def update_inquiry_status_endpoint(
    inquiry_id: int,
    status: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update inquiry status (owner only)"""
    user_id = get_user_from_token(credentials)
    if status not in ['pending', 'accepted', 'rejected']:
        raise HTTPException(status_code=400, detail="Invalid status")

    update_inquiry_status(inquiry_id, status, user_id)

    return {"message": f"Inquiry status updated to {status}"}

@app.get("/search")
async def search_rooms_endpoint(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100)
):
    """Search rooms by title, description, or location"""
    rooms = search_rooms(q, limit)
    return [RoomResponse(**room) for room in rooms]

@app.get("/types")
async def get_room_types_endpoint():
    """Get all available room types"""
    return {"room_types": get_room_types()}

@app.get("/preferences")
async def get_gender_preferences_endpoint():
    """Get all available gender preferences"""
    return {"gender_preferences": get_gender_preferences()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rooms"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("ROOMS_SERVICE_PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)