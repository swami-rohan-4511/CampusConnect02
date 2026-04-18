"""
Campus Connect Notes & Printing Service
Handles document sharing, note uploads, and printing services
"""

from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File
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
import cloudinary
import cloudinary.uploader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Campus Connect Notes & Printing Service",
    description="Document sharing and printing services",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "notes_db")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Cloudinary configuration
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET
    )

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
class NoteCreate(BaseModel):
    title: str
    subject: str
    description: str = None
    tags: List[str] = []

class NoteUpdate(BaseModel):
    title: str = None
    subject: str = None
    description: str = None
    tags: List[str] = None

class NoteResponse(BaseModel):
    id: int
    title: str
    subject: str
    description: str
    file_url: str = None
    file_type: str
    uploaded_by: int
    download_count: int
    tags: list = []
    created_at: datetime
    updated_at: datetime

class PrintingServiceCreate(BaseModel):
    service_name: str
    description: str = None
    contact_info: str
    location: str = None
    pricing: dict = {}
    operating_hours: dict = {}

class PrintingServiceUpdate(BaseModel):
    service_name: str = None
    description: str = None
    contact_info: str = None
    location: str = None
    pricing: dict = None
    operating_hours: dict = None

class PrintingServiceResponse(BaseModel):
    id: int
    service_name: str
    description: str
    contact_info: str
    location: str
    pricing: dict = {}
    operating_hours: dict = {}
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

def upload_file_to_cloudinary(file: UploadFile, folder: str = "campus-connect/notes") -> str:
    """Upload file to Cloudinary and return URL"""
    if not CLOUDINARY_CLOUD_NAME:
        raise HTTPException(status_code=500, detail="File upload not configured")

    try:
        contents = file.file.read()

        # Determine resource type based on file type
        content_type = file.content_type
        resource_type = "raw"  # Default for documents

        if content_type.startswith('image/'):
            resource_type = "image"
        elif content_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            resource_type = "raw"

        result = cloudinary.uploader.upload(
            contents,
            folder=folder,
            resource_type=resource_type
        )
        return result['secure_url']
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

def get_file_type_from_content_type(content_type: str) -> str:
    """Determine file type from content type"""
    if content_type == 'application/pdf':
        return 'pdf'
    elif content_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        return 'docx' if 'document' in content_type else 'doc'
    elif content_type.startswith('image/'):
        return 'image'
    else:
        return 'other'

def create_note(note_data: dict, user_id: int, file_url: str = None, file_type: str = None):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO notes (title, subject, description, file_url, file_type, uploaded_by, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            note_data["title"],
            note_data["subject"],
            note_data.get("description"),
            file_url,
            file_type,
            user_id,
            json.dumps(note_data.get("tags", []))
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_note_by_id(note_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM notes WHERE id = %s", (note_id,))
        note = cursor.fetchone()
        if note:
            note['tags'] = json.loads(note['tags']) if note['tags'] else []
        return note
    finally:
        cursor.close()
        connection.close()

def get_notes_by_user(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM notes WHERE uploaded_by = %s ORDER BY created_at DESC", (user_id,))
        notes = cursor.fetchall()
        for note in notes:
            note['tags'] = json.loads(note['tags']) if note['tags'] else []
        return notes
    finally:
        cursor.close()
        connection.close()

def get_all_notes(limit: int = 50, offset: int = 0, subject: str = None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = "SELECT * FROM notes WHERE 1=1"
        params = []

        if subject:
            query += " AND subject LIKE %s"
            params.append(f"%{subject}%")

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        notes = cursor.fetchall()
        for note in notes:
            note['tags'] = json.loads(note['tags']) if note['tags'] else []
        return notes
    finally:
        cursor.close()
        connection.close()

def update_note(note_id: int, update_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the uploader
        cursor.execute("SELECT uploaded_by FROM notes WHERE id = %s", (note_id,))
        note = cursor.fetchone()
        if not note or note[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this note")

        update_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                if field == 'tags':
                    update_fields.append("tags = %s")
                    params.append(json.dumps(value))
                else:
                    update_fields.append(f"{field} = %s")
                    params.append(value)

        if not update_fields:
            return

        params.append(note_id)
        query = f"UPDATE notes SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def delete_note(note_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the uploader
        cursor.execute("SELECT uploaded_by FROM notes WHERE id = %s", (note_id,))
        note = cursor.fetchone()
        if not note or note[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this note")

        cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def increment_download_count(note_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            UPDATE notes SET download_count = download_count + 1 WHERE id = %s
        """, (note_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def create_printing_service(service_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO printing_services (service_name, description, contact_info, location, pricing, operating_hours)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            service_data["service_name"],
            service_data.get("description"),
            service_data["contact_info"],
            service_data.get("location"),
            json.dumps(service_data.get("pricing", {})),
            json.dumps(service_data.get("operating_hours", {}))
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_printing_service_by_id(service_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM printing_services WHERE id = %s", (service_id,))
        service = cursor.fetchone()
        if service:
            service['pricing'] = json.loads(service['pricing']) if service['pricing'] else {}
            service['operating_hours'] = json.loads(service['operating_hours']) if service['operating_hours'] else {}
        return service
    finally:
        cursor.close()
        connection.close()

def get_all_printing_services(limit: int = 50, offset: int = 0, location: str = None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = "SELECT * FROM printing_services WHERE 1=1"
        params = []

        if location:
            query += " AND location LIKE %s"
            params.append(f"%{location}%")

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        services = cursor.fetchall()
        for service in services:
            service['pricing'] = json.loads(service['pricing']) if service['pricing'] else {}
            service['operating_hours'] = json.loads(service['operating_hours']) if service['operating_hours'] else {}
        return services
    finally:
        cursor.close()
        connection.close()

def update_printing_service(service_id: int, update_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        update_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                if field in ['pricing', 'operating_hours']:
                    update_fields.append(f"{field} = %s")
                    params.append(json.dumps(value))
                else:
                    update_fields.append(f"{field} = %s")
                    params.append(value)

        if not update_fields:
            return

        params.append(service_id)
        query = f"UPDATE printing_services SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def delete_printing_service(service_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM printing_services WHERE id = %s", (service_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def search_notes(query: str, subject: str = None, tags: List[str] = None, limit: int = 50):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        sql_query = """
            SELECT * FROM notes
            WHERE (title LIKE %s OR description LIKE %s OR subject LIKE %s)
        """
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]

        if subject:
            sql_query += " AND subject LIKE %s"
            params.append(f"%{subject}%")

        if tags:
            for tag in tags:
                sql_query += " AND JSON_CONTAINS(tags, %s)"
                params.append(f'"{tag}"')

        sql_query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cursor.execute(sql_query, params)
        notes = cursor.fetchall()
        for note in notes:
            note['tags'] = json.loads(note['tags']) if note['tags'] else []
        return notes
    finally:
        cursor.close()
        connection.close()

def get_popular_subjects(limit: int = 10):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT subject, COUNT(*) as count
            FROM notes
            GROUP BY subject
            ORDER BY count DESC
            LIMIT %s
        """, (limit,))
        subjects = cursor.fetchall()
        return subjects
    finally:
        cursor.close()
        connection.close()

# API endpoints
@app.post("/notes", response_model=NoteResponse)
async def create_note_endpoint(
    note: NoteCreate,
    file: UploadFile = File(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new note/document"""
    user_id = get_user_from_token(credentials)

    file_url = None
    file_type = None

    if file:
        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'image/jpeg',
            'image/png',
            'image/gif'
        ]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        file_url = upload_file_to_cloudinary(file)
        file_type = get_file_type_from_content_type(file.content_type)

    note_data = note.dict()
    note_id = create_note(note_data, user_id, file_url, file_type)
    created_note = get_note_by_id(note_id)

    return NoteResponse(**created_note)

@app.get("/notes", response_model=List[NoteResponse])
async def get_notes(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    subject: str = Query(None)
):
    """Get all notes with optional filtering"""
    notes = get_all_notes(limit, offset, subject)
    return [NoteResponse(**note) for note in notes]

@app.get("/notes/my-notes", response_model=List[NoteResponse])
async def get_my_notes(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get notes uploaded by current user"""
    user_id = get_user_from_token(credentials)
    notes = get_notes_by_user(user_id)
    return [NoteResponse(**note) for note in notes]

@app.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int):
    """Get a specific note by ID"""
    note = get_note_by_id(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return NoteResponse(**note)

@app.put("/notes/{note_id}", response_model=NoteResponse)
async def update_note_endpoint(
    note_id: int,
    note_update: NoteUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a note"""
    user_id = get_user_from_token(credentials)
    update_data = {k: v for k, v in note_update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_note(note_id, update_data, user_id)
    updated_note = get_note_by_id(note_id)

    return NoteResponse(**updated_note)

@app.delete("/notes/{note_id}")
async def delete_note_endpoint(
    note_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a note"""
    user_id = get_user_from_token(credentials)
    delete_note(note_id, user_id)

    return {"message": "Note deleted successfully"}

@app.post("/notes/{note_id}/download")
async def download_note(note_id: int):
    """Increment download count for a note"""
    note = get_note_by_id(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    increment_download_count(note_id)
    return {"message": "Download recorded", "file_url": note['file_url']}

@app.post("/printing-services", response_model=PrintingServiceResponse)
async def create_printing_service_endpoint(service: PrintingServiceCreate):
    """Create a new printing service"""
    service_data = service.dict()
    service_id = create_printing_service(service_data)
    created_service = get_printing_service_by_id(service_id)

    return PrintingServiceResponse(**created_service)

@app.get("/printing-services", response_model=List[PrintingServiceResponse])
async def get_printing_services(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    location: str = Query(None)
):
    """Get all printing services"""
    services = get_all_printing_services(limit, offset, location)
    return [PrintingServiceResponse(**service) for service in services]

@app.get("/printing-services/{service_id}", response_model=PrintingServiceResponse)
async def get_printing_service(service_id: int):
    """Get a specific printing service by ID"""
    service = get_printing_service_by_id(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Printing service not found")

    return PrintingServiceResponse(**service)

@app.put("/printing-services/{service_id}", response_model=PrintingServiceResponse)
async def update_printing_service_endpoint(
    service_id: int,
    service_update: PrintingServiceUpdate
):
    """Update a printing service"""
    update_data = {k: v for k, v in service_update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_printing_service(service_id, update_data)
    updated_service = get_printing_service_by_id(service_id)

    return PrintingServiceResponse(**updated_service)

@app.delete("/printing-services/{service_id}")
async def delete_printing_service_endpoint(service_id: int):
    """Delete a printing service"""
    delete_printing_service(service_id)

    return {"message": "Printing service deleted successfully"}

@app.get("/search")
async def search_notes_endpoint(
    q: str = Query(..., min_length=1),
    subject: str = Query(None),
    tags: List[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Search notes by title, description, subject, or tags"""
    notes = search_notes(q, subject, tags, limit)
    return [NoteResponse(**note) for note in notes]

@app.get("/subjects/popular")
async def get_popular_subjects_endpoint(limit: int = Query(10, ge=1, le=20)):
    """Get most popular subjects"""
    subjects = get_popular_subjects(limit)
    return {"subjects": subjects}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "notes-printing"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("NOTES_SERVICE_PORT", 8009))
    uvicorn.run(app, host="0.0.0.0", port=port)