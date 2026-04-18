"""
Campus Connect Marketplace Service
Handles buying/selling items with categories and search functionality
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
import cloudinary.api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Campus Connect Marketplace Service",
    description="Buy/sell items marketplace service",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "marketplace_db")
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
class ItemCreate(BaseModel):
    title: str
    description: str = None
    price: float
    category: str
    condition_status: str = "used"
    contact_info: str = None

class ItemUpdate(BaseModel):
    title: str = None
    description: str = None
    price: float = None
    category: str = None
    condition_status: str = None
    contact_info: str = None
    status: str = None

class ItemResponse(BaseModel):
    id: int
    title: str
    description: str
    price: float
    category: str
    condition_status: str
    images: list = []
    seller_id: int
    buyer_id: int = None
    status: str
    contact_info: str
    created_at: datetime
    updated_at: datetime

class ContactInfoCreate(BaseModel):
    contact_type: str  # 'phone', 'email', 'social'
    contact_value: str

class ContactInfoResponse(BaseModel):
    id: int
    item_id: int
    contact_type: str
    contact_value: str

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
        # Read file content
        contents = file.file.read()

        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            contents,
            folder="campus-connect/marketplace",
            resource_type="image"
        )

        return result['secure_url']
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        raise HTTPException(status_code=500, detail="Image upload failed")

def create_item(item_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO items (title, description, price, category, condition_status,
                             seller_id, contact_info)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            item_data["title"],
            item_data.get("description"),
            item_data["price"],
            item_data["category"],
            item_data.get("condition_status", "used"),
            user_id,
            item_data.get("contact_info")
        ))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

def get_item_by_id(item_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        if item:
            # Parse images JSON
            item['images'] = json.loads(item['images']) if item['images'] else []
        return item
    finally:
        cursor.close()
        connection.close()

def get_items_by_seller(seller_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM items WHERE seller_id = %s ORDER BY created_at DESC", (seller_id,))
        items = cursor.fetchall()
        for item in items:
            item['images'] = json.loads(item['images']) if item['images'] else []
        return items
    finally:
        cursor.close()
        connection.close()

def get_all_items(limit: int = 50, offset: int = 0, category: str = None, status: str = "available"):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = "SELECT * FROM items WHERE status = %s"
        params = [status]

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

def update_item(item_id: int, update_data: dict, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the seller
        cursor.execute("SELECT seller_id FROM items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        if not item or item[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this item")

        # Build update query
        update_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                params.append(value)

        if not update_fields:
            return

        params.append(item_id)
        query = f"UPDATE items SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        cursor.execute(query, params)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def delete_item(item_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the seller
        cursor.execute("SELECT seller_id FROM items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        if not item or item[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this item")

        cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def mark_item_sold(item_id: int, buyer_id: int, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the seller
        cursor.execute("SELECT seller_id FROM items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        if not item or item[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this item")

        cursor.execute("""
            UPDATE items SET status = 'sold', buyer_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (buyer_id, item_id))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def add_item_image(item_id: int, image_url: str, user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Check if user is the seller
        cursor.execute("SELECT seller_id, images FROM items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        if not item or item[0] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this item")

        # Update images array
        current_images = json.loads(item[1]) if item[1] else []
        current_images.append(image_url)
        images_json = json.dumps(current_images)

        cursor.execute("UPDATE items SET images = %s WHERE id = %s", (images_json, item_id))
        connection.commit()
    finally:
        cursor.close()
        connection.close()

def search_items(query: str, category: str = None, limit: int = 50):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        sql_query = """
            SELECT * FROM items
            WHERE (title LIKE %s OR description LIKE %s)
            AND status = 'available'
        """
        params = [f"%{query}%", f"%{query}%"]

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
    """Get all available categories"""
    return [
        "electronics", "books", "stationery", "fashion", "essentials", "other"
    ]

# API endpoints
@app.post("/", response_model=ItemResponse)
async def create_item_endpoint(
    item: ItemCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new item for sale"""
    user_id = get_user_from_token(credentials)
    item_data = item.dict()
    item_id = create_item(item_data, user_id)
    created_item = get_item_by_id(item_id)

    return ItemResponse(**created_item)

@app.get("/", response_model=List[ItemResponse])
async def get_items(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str = Query(None),
    status: str = Query("available")
):
    """Get all items with optional filtering"""
    if category and category not in get_categories():
        raise HTTPException(status_code=400, detail="Invalid category")

    items = get_all_items(limit, offset, category, status)
    return [ItemResponse(**item) for item in items]

@app.get("/my-items", response_model=List[ItemResponse])
async def get_my_items(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get items posted by current user"""
    user_id = get_user_from_token(credentials)
    items = get_items_by_seller(user_id)
    return [ItemResponse(**item) for item in items]

@app.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """Get a specific item by ID"""
    item = get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return ItemResponse(**item)

@app.put("/{item_id}", response_model=ItemResponse)
async def update_item_endpoint(
    item_id: int,
    item_update: ItemUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update an item"""
    user_id = get_user_from_token(credentials)
    update_data = {k: v for k, v in item_update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_item(item_id, update_data, user_id)
    updated_item = get_item_by_id(item_id)

    return ItemResponse(**updated_item)

@app.delete("/{item_id}")
async def delete_item_endpoint(
    item_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete an item"""
    user_id = get_user_from_token(credentials)
    delete_item(item_id, user_id)

    return {"message": "Item deleted successfully"}

@app.post("/{item_id}/mark-sold")
async def mark_sold_endpoint(
    item_id: int,
    buyer_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Mark an item as sold"""
    user_id = get_user_from_token(credentials)
    mark_item_sold(item_id, buyer_id, user_id)

    return {"message": "Item marked as sold"}

@app.post("/{item_id}/upload-image")
async def upload_image_endpoint(
    item_id: int,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload an image for an item"""
    user_id = get_user_from_token(credentials)

    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Upload to Cloudinary
    image_url = upload_image_to_cloudinary(file)

    # Add to item
    add_item_image(item_id, image_url, user_id)

    return {"message": "Image uploaded successfully", "image_url": image_url}

@app.get("/search")
async def search_items_endpoint(
    q: str = Query(..., min_length=1),
    category: str = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Search items by title or description"""
    if category and category not in get_categories():
        raise HTTPException(status_code=400, detail="Invalid category")

    items = search_items(q, category, limit)
    return [ItemResponse(**item) for item in items]

@app.get("/categories")
async def get_categories_endpoint():
    """Get all available categories"""
    return {"categories": get_categories()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "marketplace"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MARKETPLACE_SERVICE_PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)