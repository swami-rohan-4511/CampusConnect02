"""
Campus Connect Rental Hub Service
Handles gadget rentals with duration tracking and pricing
"""

from fastapi import FastAPI, HTTPException, Depends, Query
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Campus Connect Rental Hub Service",
    description="Gadget rental service with duration and pricing management",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "rental_db")
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
class RentalItemCreate(BaseModel):
    name: str
    description: str = None
    category: str
    daily_rate: float
    security_deposit: float = None
    location: str = None

class RentalItemUpdate(BaseModel):
    name: str = None
    description: str = None
    category: str = None
    daily_rate: float = None
    security_deposit: float = None
    location: str = None
    availability_status: bool = None

class RentalItemResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    daily_rate: float
    security_deposit: float
    images: list = []
    owner_id: int
    location: str
    availability_status: bool
    created_at: datetime
    updated_at: datetime

class RentalCreate(BaseModel):
    item_id: int
    start_date: date
    end_date: date

class RentalResponse(BaseModel):
    id: int
    item_id: int
    renter_id: int
    start_date: date
    end_date: date
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime
    item_name: str = None

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

def create_rental_item(item_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO rental_items (name, description, category, daily_rate,
                                    security_deposit, owner_id, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            item_data["name"],
            item_data.get("description"),
            item_data["category"],
            item_data["daily_rate"],
            item_data.get("security_deposit"),
            user_id,
            item_data.get("location")
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_rental_item_by_id(item_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM rental_items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        if item:
            item['images'] = json.loads(item['images']) if item['images'] else []
        return item
    finally:
        cursor.close()
        connection.close()

def get_rental_items_by_owner(owner_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM rental_items WHERE owner_id = %s ORDER BY created_at DESC", (owner_id,))
        items = cursor.fetchall()
        for item in items:
            item['images'] = json.loads(item['images']) if item['images'] else []
        return items
    finally:
        cursor.close()
        connection.close()

def get_all_rental_items(limit: int = 50, offset: int = 0, category: str = None, available_only: bool = True):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = "SELECT * FROM rental_items WHERE 1=1"
        params = []

        if available_only:
            query += " AND availability_status = %s"
            params.append(True)

        if category:
            query += " AND category = %s"
            params.append(category)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        items = cursor.fetchall()
        for item in items:
            item['images'] = json.loads(item['images']) if item['images'] else []
        return items
    finally:
        cursor.close()
        connection.close()

def update_rental_item(item_id: int, update_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the owner
        cursor.execute("SELECT owner_id FROM rental_items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        if not item or item[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this item")

        update_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                params.append(value)

        if not update_fields:
            return

        params.append(item_id)
        query = f"UPDATE rental_items SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def delete_rental_item(item_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the owner
        cursor.execute("SELECT owner_id FROM rental_items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        if not item or item[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this item")

        cursor.execute("DELETE FROM rental_items WHERE id = %s", (item_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def create_rental(rental_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if item is available
        cursor.execute("SELECT availability_status, daily_rate, name FROM rental_items WHERE id = %s", (rental_data["item_id"],))
        item = cursor.fetchone()
        if not item:
            raise HTTPException(status_code=404, detail="Rental item not found")
        if not item[0]:
            raise HTTPException(status_code=400, detail="Item is not available for rental")

        # Calculate total amount
        start_date = rental_data["start_date"]
        end_date = rental_data["end_date"]
        days = (end_date - start_date).days + 1  # Include both start and end dates
        total_amount = days * item[1]

        cursor.execute("""
            INSERT INTO rentals (item_id, renter_id, start_date, end_date, total_amount)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            rental_data["item_id"],
            user_id,
            start_date,
            end_date,
            total_amount
        ))
        connection.commit()
        rental_id = cursor.lastrowid

        return rental_id, total_amount, item[2]
    finally:
        cursor.close()
        connection.close()

def get_rentals_by_user(user_id: int, as_renter: bool = True):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        if as_renter:
            cursor.execute("""
                SELECT r.*, ri.name as item_name, ri.daily_rate
                FROM rentals r
                JOIN rental_items ri ON r.item_id = ri.id
                WHERE r.renter_id = %s
                ORDER BY r.created_at DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT r.*, ri.name as item_name, ri.daily_rate
                FROM rentals r
                JOIN rental_items ri ON r.item_id = ri.id
                WHERE ri.owner_id = %s
                ORDER BY r.created_at DESC
            """, (user_id,))

        rentals = cursor.fetchall()
        return rentals
    finally:
        cursor.close()
        connection.close()

def update_rental_status(rental_id: int, status: str, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is involved in this rental
        cursor.execute("""
            SELECT r.renter_id, ri.owner_id
            FROM rentals r
            JOIN rental_items ri ON r.item_id = ri.id
            WHERE r.id = %s
        """, (rental_id,))
        rental = cursor.fetchone()
        if not rental or (rental[0] != user_id and rental[1] != user_id):
            raise HTTPException(status_code=403, detail="Not authorized to update this rental")

        cursor.execute("""
            UPDATE rentals SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (status, rental_id))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def search_rental_items(query: str, category: str = None, limit: int = 50):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        sql_query = """
            SELECT * FROM rental_items
            WHERE (name LIKE %s OR description LIKE %s)
            AND availability_status = %s
        """
        params = [f"%{query}%", f"%{query}%", True]

        if category:
            sql_query += " AND category = %s"
            params.append(category)

        sql_query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cursor.execute(sql_query, params)
        items = cursor.fetchall()
        for item in items:
            item['images'] = json.loads(item['images']) if item['images'] else []
        return items
    finally:
        cursor.close()
        connection.close()

def get_categories():
    """Get all available rental categories"""
    return [
        "calculator", "drafter", "tripod", "bike", "laptop", "other"
    ]

# API endpoints
@app.post("/", response_model=RentalItemResponse)
async def create_rental_item_endpoint(
    item: RentalItemCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new rental item"""
    user_id = get_user_from_token(credentials)
    item_data = item.dict()
    item_id = create_rental_item(item_data, user_id)
    created_item = get_rental_item_by_id(item_id)

    return RentalItemResponse(**created_item)

@app.get("/", response_model=List[RentalItemResponse])
async def get_rental_items(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str = Query(None),
    available_only: bool = Query(True)
):
    """Get all rental items with optional filtering"""
    if category and category not in get_categories():
        raise HTTPException(status_code=400, detail="Invalid category")

    items = get_all_rental_items(limit, offset, category, available_only)
    return [RentalItemResponse(**item) for item in items]

@app.get("/my-items", response_model=List[RentalItemResponse])
async def get_my_rental_items(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get rental items posted by current user"""
    user_id = get_user_from_token(credentials)
    items = get_rental_items_by_owner(user_id)
    return [RentalItemResponse(**item) for item in items]

@app.get("/{item_id}", response_model=RentalItemResponse)
async def get_rental_item(item_id: int):
    """Get a specific rental item by ID"""
    item = get_rental_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Rental item not found")

    return RentalItemResponse(**item)

@app.put("/{item_id}", response_model=RentalItemResponse)
async def update_rental_item_endpoint(
    item_id: int,
    item_update: RentalItemUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a rental item"""
    user_id = get_user_from_token(credentials)
    update_data = {k: v for k, v in item_update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_rental_item(item_id, update_data, user_id)
    updated_item = get_rental_item_by_id(item_id)

    return RentalItemResponse(**updated_item)

@app.delete("/{item_id}")
async def delete_rental_item_endpoint(
    item_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a rental item"""
    user_id = get_user_from_token(credentials)
    delete_rental_item(item_id, user_id)

    return {"message": "Rental item deleted successfully"}

@app.post("/rent")
async def create_rental_endpoint(
    rental: RentalCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new rental booking"""
    user_id = get_user_from_token(credentials)

    # Validate dates
    if rental.start_date >= rental.end_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    if rental.start_date < date.today():
        raise HTTPException(status_code=400, detail="Start date cannot be in the past")

    rental_id, total_amount, item_name = create_rental(rental.dict(), user_id)

    return {
        "message": "Rental created successfully",
        "rental_id": rental_id,
        "total_amount": total_amount,
        "item_name": item_name
    }

@app.get("/rentals/my-rentals", response_model=List[RentalResponse])
async def get_my_rentals(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get rentals where current user is the renter"""
    user_id = get_user_from_token(credentials)
    rentals = get_rentals_by_user(user_id, as_renter=True)
    return [RentalResponse(**rental) for rental in rentals]

@app.get("/rentals/my-lendings", response_model=List[RentalResponse])
async def get_my_lendings(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get rentals where current user is the owner"""
    user_id = get_user_from_token(credentials)
    rentals = get_rentals_by_user(user_id, as_renter=False)
    return [RentalResponse(**rental) for rental in rentals]

@app.put("/rentals/{rental_id}/status")
async def update_rental_status_endpoint(
    rental_id: int,
    status: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update rental status"""
    user_id = get_user_from_token(credentials)
    if status not in ['pending', 'active', 'completed', 'cancelled']:
        raise HTTPException(status_code=400, detail="Invalid status")

    update_rental_status(rental_id, status, user_id)

    return {"message": f"Rental status updated to {status}"}

@app.get("/search")
async def search_rental_items_endpoint(
    q: str = Query(..., min_length=1),
    category: str = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Search rental items by name or description"""
    if category and category not in get_categories():
        raise HTTPException(status_code=400, detail="Invalid category")

    items = search_rental_items(q, category, limit)
    return [RentalItemResponse(**item) for item in items]

@app.get("/categories")
async def get_categories_endpoint():
    """Get all available rental categories"""
    return {"categories": get_categories()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rental-hub"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("RENTAL_SERVICE_PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)