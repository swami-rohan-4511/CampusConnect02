"""
Campus Connect Stolen & Found Service
Handles reporting lost/found items with notifications
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
import firebase_admin
from firebase_admin import credentials, messaging
import cloudinary
import cloudinary.uploader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Campus Connect Stolen & Found Service",
    description="Lost/found items reporting service",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "stolen_found_db")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Firebase configuration
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY")
FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL")

# Cloudinary configuration
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Initialize Firebase
firebase_initialized = False
if FIREBASE_PROJECT_ID and FIREBASE_PRIVATE_KEY and FIREBASE_CLIENT_EMAIL:
    try:
        firebase_cred = credentials.Certificate({
            "type": "service_account",
            "project_id": FIREBASE_PROJECT_ID,
            "private_key": FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
            "client_email": FIREBASE_CLIENT_EMAIL,
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        firebase_admin.initialize_app(firebase_cred)
        firebase_initialized = True
        logger.info("Firebase initialized successfully")
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")

# Initialize Cloudinary
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
class ReportCreate(BaseModel):
    item_name: str
    description: str = None
    category: str
    report_type: str  # 'lost', 'found'
    location: str = None
    latitude: float = None
    longitude: float = None
    contact_info: str = None

class ReportUpdate(BaseModel):
    item_name: str = None
    description: str = None
    category: str = None
    location: str = None
    latitude: float = None
    longitude: float = None
    contact_info: str = None
    status: str = None

class ReportResponse(BaseModel):
    id: int
    item_name: str
    description: str
    category: str
    report_type: str
    location: str
    latitude: float
    longitude: float
    images: list = []
    reported_by: int
    contact_info: str
    status: str
    created_at: datetime
    updated_at: datetime

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

def upload_image_to_cloudinary(file: UploadFile) -> str:
    """Upload image to Cloudinary and return URL"""
    if not CLOUDINARY_CLOUD_NAME:
        raise HTTPException(status_code=500, detail="Image upload not configured")

    try:
        contents = file.file.read()
        result = cloudinary.uploader.upload(
            contents,
            folder="campus-connect/stolen-found",
            resource_type="image"
        )
        return result['secure_url']
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        raise HTTPException(status_code=500, detail="Image upload failed")

def send_push_notification(title: str, body: str, topic: str = None, token: str = None):
    """Send push notification via Firebase"""
    if not firebase_initialized:
        logger.warning("Firebase not initialized, skipping notification")
        return

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            topic=topic,
            token=token,
        )
        response = messaging.send(message)
        logger.info(f"Notification sent: {response}")
        return response
    except Exception as e:
        logger.error(f"Notification failed: {e}")

def create_report(report_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO reports (item_name, description, category, report_type, location,
                               latitude, longitude, reported_by, contact_info)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            report_data["item_name"],
            report_data.get("description"),
            report_data["category"],
            report_data["report_type"],
            report_data.get("location"),
            report_data.get("latitude"),
            report_data.get("longitude"),
            user_id,
            report_data.get("contact_info")
        ))
        connection.commit()
        report_id = cursor.lastrowid

        # Send notification for new report
        notification_title = f"New {report_data['report_type']} item reported"
        notification_body = f"{report_data['item_name']} - {report_data.get('location', 'Campus')}"
        send_push_notification(notification_title, notification_body, topic="stolen_found")

        return report_id
    finally:
        cursor.close()
        connection.close()

def get_report_by_id(report_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM reports WHERE id = %s", (report_id,))
        report = cursor.fetchone()
        if report:
            report['images'] = json.loads(report['images']) if report['images'] else []
        return report
    finally:
        cursor.close()
        connection.close()

def get_reports_by_user(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM reports WHERE reported_by = %s ORDER BY created_at DESC", (user_id,))
        reports = cursor.fetchall()
        for report in reports:
            report['images'] = json.loads(report['images']) if report['images'] else []
        return reports
    finally:
        cursor.close()
        connection.close()

def get_all_reports(limit: int = 50, offset: int = 0, report_type: str = None, status: str = "active"):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = "SELECT * FROM reports WHERE status = %s"
        params = [status]

        if report_type:
            query += " AND report_type = %s"
            params.append(report_type)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        reports = cursor.fetchall()
        for report in reports:
            report['images'] = json.loads(report['images']) if report['images'] else []
        return reports
    finally:
        cursor.close()
        connection.close()

def update_report(report_id: int, update_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the reporter
        cursor.execute("SELECT reported_by FROM reports WHERE id = %s", (report_id,))
        report = cursor.fetchone()
        if not report or report[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this report")

        update_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                params.append(value)

        if not update_fields:
            return

        params.append(report_id)
        query = f"UPDATE reports SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def delete_report(report_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the reporter
        cursor.execute("SELECT reported_by FROM reports WHERE id = %s", (report_id,))
        report = cursor.fetchone()
        if not report or report[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this report")

        cursor.execute("DELETE FROM reports WHERE id = %s", (report_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def mark_report_resolved(report_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the reporter
        cursor.execute("SELECT reported_by FROM reports WHERE id = %s", (report_id,))
        report = cursor.fetchone()
        if not report or report[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this report")

        cursor.execute("""
            UPDATE reports SET status = 'resolved', updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (report_id,))
        connection.commit()

        # Send notification
        send_push_notification(
            "Item Report Resolved",
            "Your reported item has been marked as resolved",
            topic=f"user_{user_id}"
        )
    finally:
        cursor.close()
        connection.close()

def add_report_image(report_id: int, image_url: str, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the reporter
        cursor.execute("SELECT reported_by, images FROM reports WHERE id = %s", (report_id,))
        report = cursor.fetchone()
        if not report or report[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this report")

        current_images = json.loads(report[1]) if report[1] else []
        current_images.append(image_url)
        images_json = json.dumps(current_images)

        cursor.execute("UPDATE reports SET images = %s WHERE id = %s", (images_json, report_id))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def search_reports(query: str, report_type: str = None, limit: int = 50):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        sql_query = """
            SELECT * FROM reports
            WHERE (item_name LIKE %s OR description LIKE %s OR location LIKE %s)
            AND status = 'active'
        """
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]

        if report_type:
            sql_query += " AND report_type = %s"
            params.append(report_type)

        sql_query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cursor.execute(sql_query, params)
        reports = cursor.fetchall()
        for report in reports:
            report['images'] = json.loads(report['images']) if report['images'] else []
        return reports
    finally:
        cursor.close()
        connection.close()

def get_categories():
    """Get all available categories"""
    return [
        "electronics", "books", "clothing", "accessories", "documents", "other"
    ]

# API endpoints
@app.post("/", response_model=ReportResponse)
async def create_report_endpoint(
    report: ReportCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new lost/found report"""
    user_id = get_user_from_token(credentials)
    report_data = report.dict()
    report_id = create_report(report_data, user_id)
    created_report = get_report_by_id(report_id)

    return ReportResponse(**created_report)

@app.get("/", response_model=List[ReportResponse])
async def get_reports(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    report_type: str = Query(None),
    status: str = Query("active")
):
    """Get all reports with optional filtering"""
    if report_type and report_type not in ['lost', 'found']:
        raise HTTPException(status_code=400, detail="Invalid report type")

    reports = get_all_reports(limit, offset, report_type, status)
    return [ReportResponse(**report) for report in reports]

@app.get("/my-reports", response_model=List[ReportResponse])
async def get_my_reports(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get reports posted by current user"""
    user_id = get_user_from_token(credentials)
    reports = get_reports_by_user(user_id)
    return [ReportResponse(**report) for report in reports]

@app.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int):
    """Get a specific report by ID"""
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportResponse(**report)

@app.put("/{report_id}", response_model=ReportResponse)
async def update_report_endpoint(
    report_id: int,
    report_update: ReportUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a report"""
    user_id = get_user_from_token(credentials)
    update_data = {k: v for k, v in report_update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_report(report_id, update_data, user_id)
    updated_report = get_report_by_id(report_id)

    return ReportResponse(**updated_report)

@app.delete("/{report_id}")
async def delete_report_endpoint(
    report_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a report"""
    user_id = get_user_from_token(credentials)
    delete_report(report_id, user_id)

    return {"message": "Report deleted successfully"}

@app.post("/{report_id}/mark-resolved")
async def mark_resolved_endpoint(
    report_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Mark a report as resolved"""
    user_id = get_user_from_token(credentials)
    mark_report_resolved(report_id, user_id)

    return {"message": "Report marked as resolved"}

@app.post("/{report_id}/upload-image")
async def upload_image_endpoint(
    report_id: int,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload an image for a report"""
    user_id = get_user_from_token(credentials)

    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_url = upload_image_to_cloudinary(file)
    add_report_image(report_id, image_url, user_id)

    return {"message": "Image uploaded successfully", "image_url": image_url}

@app.get("/search")
async def search_reports_endpoint(
    q: str = Query(..., min_length=1),
    report_type: str = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Search reports by item name, description, or location"""
    if report_type and report_type not in ['lost', 'found']:
        raise HTTPException(status_code=400, detail="Invalid report type")

    reports = search_reports(q, report_type, limit)
    return [ReportResponse(**report) for report in reports]

@app.get("/categories")
async def get_categories_endpoint():
    """Get all available categories"""
    return {"categories": get_categories()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "stolen-found"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("STOLEN_FOUND_SERVICE_PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)