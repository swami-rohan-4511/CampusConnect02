"""
Campus Connect Clubs & Communities Service
Handles club management, member interactions, and club events
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
    title="Campus Connect Clubs & Communities Service",
    description="Club management and community interaction service",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "clubs_db")
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
class ClubCreate(BaseModel):
    name: str
    description: str = None
    category: str
    president_id: int
    vice_president_id: int = None
    secretary_id: int = None
    faculty_advisor: str = None
    social_links: dict = {}

class ClubUpdate(BaseModel):
    name: str = None
    description: str = None
    category: str = None
    president_id: int = None
    vice_president_id: int = None
    secretary_id: int = None
    faculty_advisor: str = None
    social_links: dict = None

class ClubResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    president_id: int
    vice_president_id: int
    secretary_id: int
    faculty_advisor: str
    social_links: dict = {}
    logo_url: str = None
    created_at: datetime
    updated_at: datetime
    member_count: int = 0

class ClubMemberResponse(BaseModel):
    id: int
    club_id: int
    user_id: int
    role: str
    joined_at: datetime

class ClubEventCreate(BaseModel):
    title: str
    description: str = None
    event_date: datetime
    location: str = None
    max_participants: int = None

class ClubEventResponse(BaseModel):
    id: int
    club_id: int
    title: str
    description: str
    event_date: datetime
    location: str
    max_participants: int
    created_by: int
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

def create_club(club_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO clubs (name, description, category, president_id,
                             vice_president_id, secretary_id, faculty_advisor, social_links)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            club_data["name"],
            club_data.get("description"),
            club_data["category"],
            club_data["president_id"],
            club_data.get("vice_president_id"),
            club_data.get("secretary_id"),
            club_data.get("faculty_advisor"),
            json.dumps(club_data.get("social_links", {}))
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_club_by_id(club_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.*, COUNT(cm.id) as member_count
            FROM clubs c
            LEFT JOIN club_members cm ON c.id = cm.club_id
            WHERE c.id = %s
            GROUP BY c.id
        """, (club_id,))
        club = cursor.fetchone()
        if club:
            club['social_links'] = json.loads(club['social_links']) if club['social_links'] else {}
        return club
    finally:
        cursor.close()
        connection.close()

def get_all_clubs(limit: int = 50, offset: int = 0, category: str = None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT c.*, COUNT(cm.id) as member_count
            FROM clubs c
            LEFT JOIN club_members cm ON c.id = cm.club_id
        """
        params = []

        if category:
            query += " WHERE c.category = %s"
            params.append(category)
        else:
            query += " WHERE 1=1"

        query += """
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        cursor.execute(query, params)
        clubs = cursor.fetchall()
        for club in clubs:
            club['social_links'] = json.loads(club['social_links']) if club['social_links'] else {}
        return clubs
    finally:
        cursor.close()
        connection.close()

def update_club(club_id: int, update_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the president
        cursor.execute("SELECT president_id FROM clubs WHERE id = %s", (club_id,))
        club = cursor.fetchone()
        if not club or club[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this club")

        update_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                if field == 'social_links':
                    update_fields.append("social_links = %s")
                    params.append(json.dumps(value))
                else:
                    update_fields.append(f"{field} = %s")
                    params.append(value)

        if not update_fields:
            return

        params.append(club_id)
        query = f"UPDATE clubs SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def delete_club(club_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the president
        cursor.execute("SELECT president_id FROM clubs WHERE id = %s", (club_id,))
        club = cursor.fetchone()
        if not club or club[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this club")

        cursor.execute("DELETE FROM clubs WHERE id = %s", (club_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def join_club(club_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is already a member
        cursor.execute("""
            SELECT id FROM club_members WHERE club_id = %s AND user_id = %s
        """, (club_id, user_id))
        existing = cursor.fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Already a member of this club")

        cursor.execute("""
            INSERT INTO club_members (club_id, user_id, role)
            VALUES (%s, %s, 'member')
        """, (club_id, user_id))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def leave_club(club_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the president (president cannot leave)
        cursor.execute("SELECT president_id FROM clubs WHERE id = %s", (club_id,))
        club = cursor.fetchone()
        if club and club[0] == user_id:
            raise HTTPException(status_code=400, detail="President cannot leave the club")

        cursor.execute("""
            DELETE FROM club_members WHERE club_id = %s AND user_id = %s
        """, (club_id, user_id))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def update_member_role(club_id: int, user_id: int, target_user_id: int, new_role: str, president_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the president
        if president_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update member roles")

        if new_role not in ['member', 'core_team', 'president', 'vice_president', 'secretary']:
            raise HTTPException(status_code=400, detail="Invalid role")

        # If changing to president, update the club
        if new_role == 'president':
            cursor.execute("""
                UPDATE clubs SET president_id = %s WHERE id = %s
            """, (target_user_id, club_id))

        cursor.execute("""
            UPDATE club_members SET role = %s WHERE club_id = %s AND user_id = %s
        """, (new_role, club_id, target_user_id))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def get_club_members(club_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM club_members WHERE club_id = %s ORDER BY joined_at ASC
        """, (club_id,))
        members = cursor.fetchall()
        return members
    finally:
        cursor.close()
        connection.close()

def get_user_clubs(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.*, cm.role, cm.joined_at
            FROM clubs c
            JOIN club_members cm ON c.id = cm.club_id
            WHERE cm.user_id = %s
            ORDER BY cm.joined_at DESC
        """, (user_id,))
        clubs = cursor.fetchall()
        for club in clubs:
            club['social_links'] = json.loads(club['social_links']) if club['social_links'] else {}
        return clubs
    finally:
        cursor.close()
        connection.close()

def create_club_event(event_data: dict, club_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is a member of the club
        cursor.execute("""
            SELECT id FROM club_members WHERE club_id = %s AND user_id = %s
        """, (club_id, user_id))
        member = cursor.fetchone()
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this club")

        cursor.execute("""
            INSERT INTO club_events (club_id, title, description, event_date,
                                   location, max_participants, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            club_id,
            event_data["title"],
            event_data.get("description"),
            event_data["event_date"],
            event_data.get("location"),
            event_data.get("max_participants"),
            user_id
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_club_events(club_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM club_events WHERE club_id = %s ORDER BY event_date ASC
        """, (club_id,))
        events = cursor.fetchall()
        return events
    finally:
        cursor.close()
        connection.close()

def search_clubs(query: str, category: str = None, limit: int = 50):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        sql_query = """
            SELECT c.*, COUNT(cm.id) as member_count
            FROM clubs c
            LEFT JOIN club_members cm ON c.id = cm.club_id
            WHERE (c.name LIKE %s OR c.description LIKE %s)
        """
        params = [f"%{query}%", f"%{query}%"]

        if category:
            sql_query += " AND c.category = %s"
            params.append(category)

        sql_query += """
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT %s
        """
        params.append(limit)

        cursor.execute(sql_query, params)
        clubs = cursor.fetchall()
        for club in clubs:
            club['social_links'] = json.loads(club['social_links']) if club['social_links'] else {}
        return clubs
    finally:
        cursor.close()
        connection.close()

def get_categories():
    """Get all available club categories"""
    return [
        "coding", "music", "robotics", "photography", "sports", "cultural", "other"
    ]

# API endpoints
@app.post("/", response_model=ClubResponse)
async def create_club_endpoint(
    club: ClubCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new club"""
    user_id = get_user_from_token(credentials)
    club_data = club.dict()
    club_id = create_club(club_data)
    created_club = get_club_by_id(club_id)

    # Add creator as president and member
    join_club(club_id, user_id)
    update_member_role(club_id, user_id, user_id, 'president', user_id)

    return ClubResponse(**created_club)

@app.get("/", response_model=List[ClubResponse])
async def get_clubs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str = Query(None)
):
    """Get all clubs with optional filtering"""
    if category and category not in get_categories():
        raise HTTPException(status_code=400, detail="Invalid category")

    clubs = get_all_clubs(limit, offset, category)
    return [ClubResponse(**club) for club in clubs]

@app.get("/my-clubs")
async def get_my_clubs(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get clubs where current user is a member"""
    user_id = get_user_from_token(credentials)
    clubs = get_user_clubs(user_id)
    return clubs

@app.get("/{club_id}", response_model=ClubResponse)
async def get_club(club_id: int):
    """Get a specific club by ID"""
    club = get_club_by_id(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    return ClubResponse(**club)

@app.put("/{club_id}", response_model=ClubResponse)
async def update_club_endpoint(
    club_id: int,
    club_update: ClubUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a club"""
    user_id = get_user_from_token(credentials)
    update_data = {k: v for k, v in club_update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_club(club_id, update_data, user_id)
    updated_club = get_club_by_id(club_id)

    return ClubResponse(**updated_club)

@app.delete("/{club_id}")
async def delete_club_endpoint(
    club_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a club"""
    user_id = get_user_from_token(credentials)
    delete_club(club_id, user_id)

    return {"message": "Club deleted successfully"}

@app.post("/{club_id}/join")
async def join_club_endpoint(
    club_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Join a club"""
    user_id = get_user_from_token(credentials)
    join_club(club_id, user_id)

    return {"message": "Successfully joined the club"}

@app.post("/{club_id}/leave")
async def leave_club_endpoint(
    club_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Leave a club"""
    user_id = get_user_from_token(credentials)
    leave_club(club_id, user_id)

    return {"message": "Successfully left the club"}

@app.put("/{club_id}/members/{target_user_id}/role")
async def update_member_role_endpoint(
    club_id: int,
    target_user_id: int,
    role: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a member's role in the club"""
    user_id = get_user_from_token(credentials)

    # Get club president
    club = get_club_by_id(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    update_member_role(club_id, user_id, target_user_id, role, club['president_id'])

    return {"message": f"Member role updated to {role}"}

@app.get("/{club_id}/members", response_model=List[ClubMemberResponse])
async def get_club_members_endpoint(club_id: int):
    """Get all members of a club"""
    # Verify club exists
    club = get_club_by_id(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    members = get_club_members(club_id)
    return [ClubMemberResponse(**member) for member in members]

@app.post("/{club_id}/events", response_model=ClubEventResponse)
async def create_club_event_endpoint(
    club_id: int,
    event: ClubEventCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new club event"""
    user_id = get_user_from_token(credentials)
    event_data = event.dict()
    event_id = create_club_event(event_data, club_id, user_id)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM club_events WHERE id = %s", (event_id,))
        created_event = cursor.fetchone()
        return ClubEventResponse(**created_event)
    finally:
        cursor.close()
        connection.close()

@app.get("/{club_id}/events", response_model=List[ClubEventResponse])
async def get_club_events_endpoint(club_id: int):
    """Get all events for a club"""
    # Verify club exists
    club = get_club_by_id(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    events = get_club_events(club_id)
    return [ClubEventResponse(**event) for event in events]

@app.get("/search")
async def search_clubs_endpoint(
    q: str = Query(..., min_length=1),
    category: str = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Search clubs by name or description"""
    if category and category not in get_categories():
        raise HTTPException(status_code=400, detail="Invalid category")

    clubs = search_clubs(q, category, limit)
    return [ClubResponse(**club) for club in clubs]

@app.get("/categories")
async def get_categories_endpoint():
    """Get all available club categories"""
    return {"categories": get_categories()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "clubs"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("CLUBS_SERVICE_PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)