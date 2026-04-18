"""
Campus Connect Auth Service
Handles user authentication, registration, and JWT token management
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
import mysql.connector
from mysql.connector import Error
import redis
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Campus Connect Auth Service",
    description="Authentication service for Campus Connect",
    version="1.0.0"
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "auth_db")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

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

# Redis connection
def get_redis_client():
    try:
        return redis.from_url(REDIS_URL)
    except Exception as e:
        logger.error(f"Redis connection error: {e}")
        return None

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    phone: str = None
    password: str
    full_name: str
    role: str = "student"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    phone: str = None
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class UserProfile(BaseModel):
    branch: str = None
    year_of_study: int = None
    hostel_name: str = None
    room_number: str = None
    profile_picture_url: str = None
    bio: str = None
    interests: list = []

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_user_by_email(email: str):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        return user
    finally:
        cursor.close()
        connection.close()

def get_user_by_id(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        return user
    finally:
        cursor.close()
        connection.close()

def create_user(user_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        hashed_password = get_password_hash(user_data["password"])
        cursor.execute("""
            INSERT INTO users (email, phone, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_data["email"],
            user_data.get("phone"),
            hashed_password,
            user_data["full_name"],
            user_data.get("role", "student")
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_user_profile(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
        profile = cursor.fetchone()
        return profile
    finally:
        cursor.close()
        connection.close()

def create_or_update_user_profile(user_id: int, profile_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if profile exists
        cursor.execute("SELECT id FROM user_profiles WHERE user_id = %s", (user_id,))
        existing = cursor.fetchone()

        if existing:
            # Update existing profile
            cursor.execute("""
                UPDATE user_profiles
                SET branch = %s, year_of_study = %s, hostel_name = %s,
                    room_number = %s, profile_picture_url = %s, bio = %s, interests = %s
                WHERE user_id = %s
            """, (
                profile_data.get("branch"),
                profile_data.get("year_of_study"),
                profile_data.get("hostel_name"),
                profile_data.get("room_number"),
                profile_data.get("profile_picture_url"),
                profile_data.get("bio"),
                json.dumps(profile_data.get("interests", [])),
                user_id
            ))
        else:
            # Create new profile
            cursor.execute("""
                INSERT INTO user_profiles (user_id, branch, year_of_study, hostel_name,
                                         room_number, profile_picture_url, bio, interests)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                profile_data.get("branch"),
                profile_data.get("year_of_study"),
                profile_data.get("hostel_name"),
                profile_data.get("room_number"),
                profile_data.get("profile_picture_url"),
                profile_data.get("bio"),
                json.dumps(profile_data.get("interests", []))
            ))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# API endpoints
@app.post("/register", response_model=TokenResponse)
async def register(user: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user_data = user.dict()
    user_id = create_user(user_data)

    # Get created user
    new_user = get_user_by_id(user_id)

    # Create access token
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": new_user["id"], "email": new_user["email"], "role": new_user["role"]},
        expires_delta=access_token_expires
    )

    # Prepare user response
    user_response = UserResponse(
        id=new_user["id"],
        email=new_user["email"],
        phone=new_user["phone"],
        full_name=new_user["full_name"],
        role=new_user["role"],
        is_active=new_user["is_active"],
        created_at=new_user["created_at"]
    )

    return TokenResponse(access_token=access_token, user=user_response)

@app.post("/login", response_model=TokenResponse)
async def login(user_credentials: UserLogin):
    """Authenticate user and return JWT token"""
    user = get_user_by_email(user_credentials.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="Account is deactivated")

    # Create access token
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user["id"], "email": user["email"], "role": user["role"]},
        expires_delta=access_token_expires
    )

    # Prepare user response
    user_response = UserResponse(
        id=user["id"],
        email=user["email"],
        phone=user["phone"],
        full_name=user["full_name"],
        role=user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"]
    )

    return TokenResponse(access_token=access_token, user=user_response)

@app.get("/verify-token")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user information"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if user_id is None or email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = get_user_by_id(user_id)
        if not user or not user["is_active"]:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        return {
            "user_id": user_id,
            "email": email,
            "role": role,
            "full_name": user["full_name"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/profile")
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user profile"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")

        user = get_user_by_id(user_id)
        profile = get_user_profile(user_id)

        return {
            "user": user,
            "profile": profile
        }
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.put("/profile")
async def update_profile(profile_data: UserProfile, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Update user profile"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")

        create_or_update_user_profile(user_id, profile_data.dict())

        return {"message": "Profile updated successfully"}
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/users")
async def get_all_users(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all users (admin only)"""
    user_id = get_user_from_token(credentials)

    # Check if user is admin
    user = get_user_by_id(user_id)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, email, phone, full_name, role, is_active, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        return users
    finally:
        cursor.close()
        connection.close()

@app.delete("/users/{target_user_id}")
async def delete_user(target_user_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Delete a user (admin only)"""
    user_id = get_user_from_token(credentials)

    # Check if user is admin
    user = get_user_by_id(user_id)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Prevent admin from deleting themselves
    if user_id == target_user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = %s", (target_user_id,))
        connection.commit()
        return {"message": "User deleted successfully"}
    finally:
        cursor.close()
        connection.close()

@app.put("/users/{target_user_id}/role")
async def update_user_role(target_user_id: int, role: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Update user role (admin only)"""
    user_id = get_user_from_token(credentials)

    # Check if user is admin
    user = get_user_by_id(user_id)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    if role not in ["student", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE users SET role = %s WHERE id = %s", (role, target_user_id))
        connection.commit()
        return {"message": f"User role updated to {role}"}
    finally:
        cursor.close()
        connection.close()

@app.get("/stats")
async def get_user_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user statistics (admin only)"""
    user_id = get_user_from_token(credentials)

    # Check if user is admin
    user = get_user_by_id(user_id)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        # Get total users
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cursor.fetchone()["total_users"]

        # Get users by role
        cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
        role_stats = cursor.fetchall()

        # Get active users
        cursor.execute("SELECT COUNT(*) as active_users FROM users WHERE is_active = TRUE")
        active_users = cursor.fetchone()["active_users"]

        return {
            "total_users": total_users,
            "active_users": active_users,
            "role_distribution": {stat["role"]: stat["count"] for stat in role_stats}
        }
    finally:
        cursor.close()
        connection.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AUTH_SERVICE_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)