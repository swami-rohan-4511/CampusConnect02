"""
Campus Connect Food Service
Handles food outlets, menus, reviews, and delivery services
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
    title="Campus Connect Food Service",
    description="Food outlets, menus, and delivery services",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "food_db")
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
class FoodOutletCreate(BaseModel):
    name: str
    type: str  # 'cafe', 'mess', 'food_court', 'delivery'
    description: str = None
    location: str
    contact_info: str
    delivery_available: bool = False
    operating_hours: dict = {}

class FoodOutletUpdate(BaseModel):
    name: str = None
    type: str = None
    description: str = None
    location: str = None
    contact_info: str = None
    delivery_available: bool = None
    operating_hours: dict = None

class FoodOutletResponse(BaseModel):
    id: int
    name: str
    type: str
    description: str
    location: str
    contact_info: str
    delivery_available: bool
    operating_hours: dict = {}
    created_at: datetime
    average_rating: float = 0.0
    review_count: int = 0

class MenuItemCreate(BaseModel):
    item_name: str
    description: str = None
    price: float
    category: str = None
    is_vegetarian: bool = True
    image_url: str = None

class MenuItemUpdate(BaseModel):
    item_name: str = None
    description: str = None
    price: float = None
    category: str = None
    is_vegetarian: bool = None
    image_url: str = None
    is_available: bool = None

class MenuItemResponse(BaseModel):
    id: int
    outlet_id: int
    item_name: str
    description: str
    price: float
    category: str
    is_vegetarian: bool
    image_url: str
    is_available: bool
    created_at: datetime

class ReviewCreate(BaseModel):
    rating: int  # 1-5
    comment: str = None

class ReviewResponse(BaseModel):
    id: int
    outlet_id: int
    user_id: int
    rating: int
    comment: str
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

def create_food_outlet(outlet_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO food_outlets (name, type, description, location, contact_info,
                                    delivery_available, operating_hours)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            outlet_data["name"],
            outlet_data["type"],
            outlet_data.get("description"),
            outlet_data["location"],
            outlet_data["contact_info"],
            outlet_data.get("delivery_available", False),
            json.dumps(outlet_data.get("operating_hours", {}))
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_food_outlet_by_id(outlet_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT fo.*,
                   COALESCE(AVG(r.rating), 0) as average_rating,
                   COUNT(r.id) as review_count
            FROM food_outlets fo
            LEFT JOIN reviews r ON fo.id = r.outlet_id
            WHERE fo.id = %s
            GROUP BY fo.id
        """, (outlet_id,))
        outlet = cursor.fetchone()
        if outlet:
            outlet['operating_hours'] = json.loads(outlet['operating_hours']) if outlet['operating_hours'] else {}
        return outlet
    finally:
        cursor.close()
        connection.close()

def get_all_food_outlets(limit: int = 50, offset: int = 0, outlet_type: str = None, delivery_only: bool = False):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT fo.*,
                   COALESCE(AVG(r.rating), 0) as average_rating,
                   COUNT(r.id) as review_count
            FROM food_outlets fo
            LEFT JOIN reviews r ON fo.id = r.outlet_id
            WHERE 1=1
        """
        params = []

        if outlet_type:
            query += " AND fo.type = %s"
            params.append(outlet_type)

        if delivery_only:
            query += " AND fo.delivery_available = %s"
            params.append(True)

        query += """
            GROUP BY fo.id
            ORDER BY fo.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        cursor.execute(query, params)
        outlets = cursor.fetchall()
        for outlet in outlets:
            outlet['operating_hours'] = json.loads(outlet['operating_hours']) if outlet['operating_hours'] else {}
        return outlets
    finally:
        cursor.close()
        connection.close()

def update_food_outlet(outlet_id: int, update_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        update_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                if field == 'operating_hours':
                    update_fields.append("operating_hours = %s")
                    params.append(json.dumps(value))
                else:
                    update_fields.append(f"{field} = %s")
                    params.append(value)

        if not update_fields:
            return

        params.append(outlet_id)
        query = f"UPDATE food_outlets SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def delete_food_outlet(outlet_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM food_outlets WHERE id = %s", (outlet_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def create_menu_item(outlet_id: int, item_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO menus (outlet_id, item_name, description, price, category,
                             is_vegetarian, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            outlet_id,
            item_data["item_name"],
            item_data.get("description"),
            item_data["price"],
            item_data.get("category"),
            item_data.get("is_vegetarian", True),
            item_data.get("image_url")
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_menu_items_by_outlet(outlet_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM menus WHERE outlet_id = %s AND is_available = %s
            ORDER BY category, item_name
        """, (outlet_id, True))
        items = cursor.fetchall()
        return items
    finally:
        cursor.close()
        connection.close()

def update_menu_item(item_id: int, update_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        update_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                params.append(value)

        if not update_fields:
            return

        params.append(item_id)
        query = f"UPDATE menus SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def delete_menu_item(item_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM menus WHERE id = %s", (item_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def create_review(outlet_id: int, user_id: int, review_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user already reviewed this outlet
        cursor.execute("""
            SELECT id FROM reviews WHERE outlet_id = %s AND user_id = %s
        """, (outlet_id, user_id))
        existing = cursor.fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="You have already reviewed this outlet")

        cursor.execute("""
            INSERT INTO reviews (outlet_id, user_id, rating, comment)
            VALUES (%s, %s, %s, %s)
        """, (
            outlet_id,
            user_id,
            review_data["rating"],
            review_data.get("comment")
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_reviews_by_outlet(outlet_id: int, limit: int = 50):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM reviews WHERE outlet_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (outlet_id, limit))
        reviews = cursor.fetchall()
        return reviews
    finally:
        cursor.close()
        connection.close()

def update_review(review_id: int, user_id: int, update_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user owns this review
        cursor.execute("SELECT user_id FROM reviews WHERE id = %s", (review_id,))
        review = cursor.fetchone()
        if not review or review[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this review")

        update_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                params.append(value)

        if not update_fields:
            return

        params.append(review_id)
        query = f"UPDATE reviews SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def delete_review(review_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user owns this review
        cursor.execute("SELECT user_id FROM reviews WHERE id = %s", (review_id,))
        review = cursor.fetchone()
        if not review or review[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this review")

        cursor.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def search_food_outlets(query: str, outlet_type: str = None, limit: int = 50):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        sql_query = """
            SELECT fo.*,
                   COALESCE(AVG(r.rating), 0) as average_rating,
                   COUNT(r.id) as review_count
            FROM food_outlets fo
            LEFT JOIN reviews r ON fo.id = r.outlet_id
            WHERE (fo.name LIKE %s OR fo.description LIKE %s OR fo.location LIKE %s)
        """
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]

        if outlet_type:
            sql_query += " AND fo.type = %s"
            params.append(outlet_type)

        sql_query += """
            GROUP BY fo.id
            ORDER BY fo.created_at DESC
            LIMIT %s
        """
        params.append(limit)

        cursor.execute(sql_query, params)
        outlets = cursor.fetchall()
        for outlet in outlets:
            outlet['operating_hours'] = json.loads(outlet['operating_hours']) if outlet['operating_hours'] else {}
        return outlets
    finally:
        cursor.close()
        connection.close()

def get_outlet_types():
    """Get all available outlet types"""
    return ["cafe", "mess", "food_court", "delivery"]

# API endpoints
@app.post("/outlets", response_model=FoodOutletResponse)
async def create_food_outlet_endpoint(outlet: FoodOutletCreate):
    """Create a new food outlet"""
    outlet_data = outlet.dict()
    outlet_id = create_food_outlet(outlet_data)
    created_outlet = get_food_outlet_by_id(outlet_id)

    return FoodOutletResponse(**created_outlet)

@app.get("/outlets", response_model=List[FoodOutletResponse])
async def get_food_outlets(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    type: str = Query(None, alias="outlet_type"),
    delivery_only: bool = Query(False)
):
    """Get all food outlets with optional filtering"""
    if type and type not in get_outlet_types():
        raise HTTPException(status_code=400, detail="Invalid outlet type")

    outlets = get_all_food_outlets(limit, offset, type, delivery_only)
    return [FoodOutletResponse(**outlet) for outlet in outlets]

@app.get("/outlets/{outlet_id}", response_model=FoodOutletResponse)
async def get_food_outlet(outlet_id: int):
    """Get a specific food outlet by ID"""
    outlet = get_food_outlet_by_id(outlet_id)
    if not outlet:
        raise HTTPException(status_code=404, detail="Food outlet not found")

    return FoodOutletResponse(**outlet)

@app.put("/outlets/{outlet_id}", response_model=FoodOutletResponse)
async def update_food_outlet_endpoint(
    outlet_id: int,
    outlet_update: FoodOutletUpdate
):
    """Update a food outlet"""
    update_data = {k: v for k, v in outlet_update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_food_outlet(outlet_id, update_data)
    updated_outlet = get_food_outlet_by_id(outlet_id)

    return FoodOutletResponse(**updated_outlet)

@app.delete("/outlets/{outlet_id}")
async def delete_food_outlet_endpoint(outlet_id: int):
    """Delete a food outlet"""
    delete_food_outlet(outlet_id)

    return {"message": "Food outlet deleted successfully"}

@app.post("/outlets/{outlet_id}/menu", response_model=MenuItemResponse)
async def create_menu_item_endpoint(
    outlet_id: int,
    item: MenuItemCreate
):
    """Add a menu item to a food outlet"""
    # Verify outlet exists
    outlet = get_food_outlet_by_id(outlet_id)
    if not outlet:
        raise HTTPException(status_code=404, detail="Food outlet not found")

    item_data = item.dict()
    item_id = create_menu_item(outlet_id, item_data)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM menus WHERE id = %s", (item_id,))
        created_item = cursor.fetchone()
        return MenuItemResponse(**created_item)
    finally:
        cursor.close()
        connection.close()

@app.get("/outlets/{outlet_id}/menu", response_model=List[MenuItemResponse])
async def get_menu_endpoint(outlet_id: int):
    """Get menu items for a food outlet"""
    # Verify outlet exists
    outlet = get_food_outlet_by_id(outlet_id)
    if not outlet:
        raise HTTPException(status_code=404, detail="Food outlet not found")

    items = get_menu_items_by_outlet(outlet_id)
    return [MenuItemResponse(**item) for item in items]

@app.put("/menu/{item_id}", response_model=MenuItemResponse)
async def update_menu_item_endpoint(
    item_id: int,
    item_update: MenuItemUpdate
):
    """Update a menu item"""
    update_data = {k: v for k, v in item_update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_menu_item(item_id, update_data)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM menus WHERE id = %s", (item_id,))
        updated_item = cursor.fetchone()
        return MenuItemResponse(**updated_item)
    finally:
        cursor.close()
        connection.close()

@app.delete("/menu/{item_id}")
async def delete_menu_item_endpoint(item_id: int):
    """Delete a menu item"""
    delete_menu_item(item_id)

    return {"message": "Menu item deleted successfully"}

@app.post("/outlets/{outlet_id}/reviews", response_model=ReviewResponse)
async def create_review_endpoint(
    outlet_id: int,
    review: ReviewCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a review for a food outlet"""
    user_id = get_user_from_token(credentials)

    # Verify outlet exists
    outlet = get_food_outlet_by_id(outlet_id)
    if not outlet:
        raise HTTPException(status_code=404, detail="Food outlet not found")

    # Validate rating
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    review_data = review.dict()
    review_id = create_review(outlet_id, user_id, review_data)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM reviews WHERE id = %s", (review_id,))
        created_review = cursor.fetchone()
        return ReviewResponse(**created_review)
    finally:
        cursor.close()
        connection.close()

@app.get("/outlets/{outlet_id}/reviews", response_model=List[ReviewResponse])
async def get_reviews_endpoint(
    outlet_id: int,
    limit: int = Query(50, ge=1, le=100)
):
    """Get reviews for a food outlet"""
    # Verify outlet exists
    outlet = get_food_outlet_by_id(outlet_id)
    if not outlet:
        raise HTTPException(status_code=404, detail="Food outlet not found")

    reviews = get_reviews_by_outlet(outlet_id, limit)
    return [ReviewResponse(**review) for review in reviews]

@app.put("/reviews/{review_id}", response_model=ReviewResponse)
async def update_review_endpoint(
    review_id: int,
    review_update: ReviewCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a review"""
    user_id = get_user_from_token(credentials)

    # Validate rating
    if review_update.rating < 1 or review_update.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    update_data = {k: v for k, v in review_update.dict().items() if v is not None}
    update_review(review_id, user_id, update_data)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM reviews WHERE id = %s", (review_id,))
        updated_review = cursor.fetchone()
        return ReviewResponse(**updated_review)
    finally:
        cursor.close()
        connection.close()

@app.delete("/reviews/{review_id}")
async def delete_review_endpoint(
    review_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a review"""
    user_id = get_user_from_token(credentials)
    delete_review(review_id, user_id)

    return {"message": "Review deleted successfully"}

@app.get("/search")
async def search_food_outlets_endpoint(
    q: str = Query(..., min_length=1),
    type: str = Query(None, alias="outlet_type"),
    limit: int = Query(50, ge=1, le=100)
):
    """Search food outlets by name, description, or location"""
    if type and type not in get_outlet_types():
        raise HTTPException(status_code=400, detail="Invalid outlet type")

    outlets = search_food_outlets(q, type, limit)
    return [FoodOutletResponse(**outlet) for outlet in outlets]

@app.get("/types")
async def get_outlet_types_endpoint():
    """Get all available outlet types"""
    return {"outlet_types": get_outlet_types()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "food"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("FOOD_SERVICE_PORT", 8010))
    uvicorn.run(app, host="0.0.0.0", port=port)