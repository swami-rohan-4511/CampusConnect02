"""
Campus Connect Jobs & Internships Service
Handles job postings, applications, and career opportunities
"""

from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, date
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
    title="Campus Connect Jobs & Internships Service",
    description="Job postings and internship management service",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "jobs_db")
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
class JobCreate(BaseModel):
    title: str
    company_name: str
    description: str = None
    requirements: str = None
    job_type: str  # 'internship', 'full_time', 'part_time', 'contract'
    location: str = None
    salary_range: str = None
    application_deadline: date = None
    contact_email: str

class JobUpdate(BaseModel):
    title: str = None
    company_name: str = None
    description: str = None
    requirements: str = None
    job_type: str = None
    location: str = None
    salary_range: str = None
    application_deadline: date = None
    contact_email: str = None
    status: str = None

class JobResponse(BaseModel):
    id: int
    title: str
    company_name: str
    description: str
    requirements: str
    job_type: str
    location: str
    salary_range: str
    application_deadline: date
    contact_email: str
    posted_by: int
    status: str
    created_at: datetime
    updated_at: datetime
    application_count: int = 0

class JobApplicationCreate(BaseModel):
    cover_letter: str = None

class JobApplicationResponse(BaseModel):
    id: int
    job_id: int
    applicant_id: int
    resume_url: str = None
    cover_letter: str
    status: str
    applied_at: datetime

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

def upload_resume_to_cloudinary(file: UploadFile) -> str:
    """Upload resume to Cloudinary and return URL"""
    if not CLOUDINARY_CLOUD_NAME:
        raise HTTPException(status_code=500, detail="File upload not configured")

    try:
        contents = file.file.read()
        result = cloudinary.uploader.upload(
            contents,
            folder="campus-connect/jobs/resumes",
            resource_type="raw"
        )
        return result['secure_url']
    except Exception as e:
        logger.error(f"Resume upload error: {e}")
        raise HTTPException(status_code=500, detail="Resume upload failed")

def create_job(job_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO jobs (title, company_name, description, requirements, job_type,
                            location, salary_range, application_deadline, contact_email, posted_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            job_data["title"],
            job_data["company_name"],
            job_data.get("description"),
            job_data.get("requirements"),
            job_data["job_type"],
            job_data.get("location"),
            job_data.get("salary_range"),
            job_data.get("application_deadline"),
            job_data["contact_email"],
            user_id
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_job_by_id(job_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT j.*, COUNT(ja.id) as application_count
            FROM jobs j
            LEFT JOIN job_applications ja ON j.id = ja.job_id
            WHERE j.id = %s
            GROUP BY j.id
        """, (job_id,))
        job = cursor.fetchone()
        return job
    finally:
        cursor.close()
        connection.close()

def get_all_jobs(limit: int = 50, offset: int = 0, job_type: str = None, status: str = "active"):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT j.*, COUNT(ja.id) as application_count
            FROM jobs j
            LEFT JOIN job_applications ja ON j.id = ja.job_id
            WHERE j.status = %s
        """
        params = [status]

        if job_type:
            query += " AND j.job_type = %s"
            params.append(job_type)

        query += """
            GROUP BY j.id
            ORDER BY j.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        cursor.execute(query, params)
        jobs = cursor.fetchall()
        return jobs
    finally:
        cursor.close()
        connection.close()

def get_jobs_by_poster(poster_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT j.*, COUNT(ja.id) as application_count
            FROM jobs j
            LEFT JOIN job_applications ja ON j.id = ja.job_id
            WHERE j.posted_by = %s
            GROUP BY j.id
            ORDER BY j.created_at DESC
        """, (poster_id,))
        jobs = cursor.fetchall()
        return jobs
    finally:
        cursor.close()
        connection.close()

def update_job(job_id: int, update_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the poster
        cursor.execute("SELECT posted_by FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        if not job or job[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this job")

        update_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                params.append(value)

        if not update_fields:
            return

        params.append(job_id)
        query = f"UPDATE jobs SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def delete_job(job_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the poster
        cursor.execute("SELECT posted_by FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        if not job or job[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this job")

        cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def apply_for_job(job_id: int, user_id: int, application_data: dict, resume_url: str = None):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if job exists and is active
        cursor.execute("SELECT status FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job[0] != 'active':
            raise HTTPException(status_code=400, detail="Job is not accepting applications")

        # Check if user already applied
        cursor.execute("""
            SELECT id FROM job_applications WHERE job_id = %s AND applicant_id = %s
        """, (job_id, user_id))
        existing = cursor.fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Already applied for this job")

        cursor.execute("""
            INSERT INTO job_applications (job_id, applicant_id, resume_url, cover_letter)
            VALUES (%s, %s, %s, %s)
        """, (
            job_id,
            user_id,
            resume_url,
            application_data.get("cover_letter")
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_job_applications(job_id: int, poster_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        # Check if user is the poster
        cursor.execute("SELECT posted_by FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        if not job or job[0] != poster_id:
            raise HTTPException(status_code=403, detail="Not authorized to view applications")

        cursor.execute("""
            SELECT * FROM job_applications WHERE job_id = %s ORDER BY applied_at DESC
        """, (job_id,))
        applications = cursor.fetchall()
        return applications
    finally:
        cursor.close()
        connection.close()

def get_user_applications(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT ja.*, j.title, j.company_name, j.job_type
            FROM job_applications ja
            JOIN jobs j ON ja.job_id = j.id
            WHERE ja.applicant_id = %s
            ORDER BY ja.applied_at DESC
        """, (user_id,))
        applications = cursor.fetchall()
        return applications
    finally:
        cursor.close()
        connection.close()

def update_application_status(application_id: int, status: str, poster_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the poster of the job
        cursor.execute("""
            SELECT j.posted_by FROM job_applications ja
            JOIN jobs j ON ja.job_id = j.id
            WHERE ja.id = %s
        """, (application_id,))
        result = cursor.fetchone()
        if not result or result[0] != poster_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this application")

        if status not in ['pending', 'reviewed', 'accepted', 'rejected']:
            raise HTTPException(status_code=400, detail="Invalid status")

        cursor.execute("""
            UPDATE job_applications SET status = %s WHERE id = %s
        """, (status, application_id))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def search_jobs(query: str, job_type: str = None, location: str = None, limit: int = 50):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        sql_query = """
            SELECT j.*, COUNT(ja.id) as application_count
            FROM jobs j
            LEFT JOIN job_applications ja ON j.id = ja.job_id
            WHERE (j.title LIKE %s OR j.company_name LIKE %s OR j.description LIKE %s)
            AND j.status = 'active'
        """
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]

        if job_type:
            sql_query += " AND j.job_type = %s"
            params.append(job_type)

        if location:
            sql_query += " AND j.location LIKE %s"
            params.append(f"%{location}%")

        sql_query += """
            GROUP BY j.id
            ORDER BY j.created_at DESC
            LIMIT %s
        """
        params.append(limit)

        cursor.execute(sql_query, params)
        jobs = cursor.fetchall()
        return jobs
    finally:
        cursor.close()
        connection.close()

def get_job_types():
    """Get all available job types"""
    return ["internship", "full_time", "part_time", "contract"]

# API endpoints
@app.post("/", response_model=JobResponse)
async def create_job_endpoint(
    job: JobCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new job posting"""
    user_id = get_user_from_token(credentials)
    job_data = job.dict()
    job_id = create_job(job_data, user_id)
    created_job = get_job_by_id(job_id)

    return JobResponse(**created_job)

@app.get("/", response_model=List[JobResponse])
async def get_jobs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    job_type: str = Query(None),
    status: str = Query("active")
):
    """Get all jobs with optional filtering"""
    if job_type and job_type not in get_job_types():
        raise HTTPException(status_code=400, detail="Invalid job type")

    jobs = get_all_jobs(limit, offset, job_type, status)
    return [JobResponse(**job) for job in jobs]

@app.get("/my-jobs", response_model=List[JobResponse])
async def get_my_jobs(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get jobs posted by current user"""
    user_id = get_user_from_token(credentials)
    jobs = get_jobs_by_poster(user_id)
    return [JobResponse(**job) for job in jobs]

@app.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int):
    """Get a specific job by ID"""
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(**job)

@app.put("/{job_id}", response_model=JobResponse)
async def update_job_endpoint(
    job_id: int,
    job_update: JobUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a job posting"""
    user_id = get_user_from_token(credentials)
    update_data = {k: v for k, v in job_update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_job(job_id, update_data, user_id)
    updated_job = get_job_by_id(job_id)

    return JobResponse(**updated_job)

@app.delete("/{job_id}")
async def delete_job_endpoint(
    job_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a job posting"""
    user_id = get_user_from_token(credentials)
    delete_job(job_id, user_id)

    return {"message": "Job deleted successfully"}

@app.post("/{job_id}/apply")
async def apply_for_job_endpoint(
    job_id: int,
    application: JobApplicationCreate,
    resume: UploadFile = File(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Apply for a job"""
    user_id = get_user_from_token(credentials)

    resume_url = None
    if resume:
        if not resume.content_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            raise HTTPException(status_code=400, detail="Resume must be a PDF or Word document")
        resume_url = upload_resume_to_cloudinary(resume)

    application_id = apply_for_job(job_id, user_id, application.dict(), resume_url)

    return {
        "message": "Application submitted successfully",
        "application_id": application_id,
        "resume_url": resume_url
    }

@app.get("/{job_id}/applications", response_model=List[JobApplicationResponse])
async def get_job_applications_endpoint(
    job_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all applications for a job (poster only)"""
    user_id = get_user_from_token(credentials)
    applications = get_job_applications(job_id, user_id)
    return [JobApplicationResponse(**app) for app in applications]

@app.get("/applications/my-applications")
async def get_my_applications(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user's job applications"""
    user_id = get_user_from_token(credentials)
    applications = get_user_applications(user_id)
    return applications

@app.put("/applications/{application_id}/status")
async def update_application_status_endpoint(
    application_id: int,
    status: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update application status (poster only)"""
    user_id = get_user_from_token(credentials)
    update_application_status(application_id, status, user_id)

    return {"message": f"Application status updated to {status}"}

@app.get("/search")
async def search_jobs_endpoint(
    q: str = Query(..., min_length=1),
    job_type: str = Query(None),
    location: str = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Search jobs by title, company, or description"""
    if job_type and job_type not in get_job_types():
        raise HTTPException(status_code=400, detail="Invalid job type")

    jobs = search_jobs(q, job_type, location, limit)
    return [JobResponse(**job) for job in jobs]

@app.get("/types")
async def get_job_types_endpoint():
    """Get all available job types"""
    return {"job_types": get_job_types()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "jobs"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("JOBS_SERVICE_PORT", 8008))
    uvicorn.run(app, host="0.0.0.0", port=port)