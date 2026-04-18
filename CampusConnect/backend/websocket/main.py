"""
Campus Connect WebSocket Service
Real-time messaging and chat functionality
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set
import os

import redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Campus Connect WebSocket Service",
    description="Real-time messaging service for chat functionality",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Environment variables
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# WebSocket connections management
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, Set[str]] = {}
        self.redis_client = redis.from_url(REDIS_URL) if REDIS_URL else None

    async def connect(self, websocket: WebSocket, user_id: int, connection_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket

        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)

        logger.info(f"User {user_id} connected with connection {connection_id}")

    def disconnect(self, connection_id: str, user_id: int):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        logger.info(f"User {user_id} disconnected connection {connection_id}")

    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to all connections of a specific user"""
        if user_id in self.user_connections:
            dead_connections = []
            for connection_id in self.user_connections[user_id]:
                if connection_id in self.active_connections:
                    try:
                        await self.active_connections[connection_id].send_json(message)
                    except Exception as e:
                        logger.error(f"Failed to send message to {connection_id}: {e}")
                        dead_connections.append(connection_id)

            # Clean up dead connections
            for conn_id in dead_connections:
                self.disconnect(conn_id, user_id)

    async def broadcast_to_users(self, message: dict, user_ids: List[int]):
        """Send message to multiple users"""
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)

    async def store_message(self, chat_id: str, message: dict):
        """Store message in Redis for persistence"""
        if self.redis_client:
            try:
                message_key = f"chat:{chat_id}:messages"
                message_json = json.dumps({
                    **message,
                    "timestamp": datetime.utcnow().isoformat()
                })
                self.redis_client.lpush(message_key, message_json)
                # Keep only last 100 messages
                self.redis_client.ltrim(message_key, 0, 99)
            except Exception as e:
                logger.error(f"Failed to store message: {e}")

    async def get_recent_messages(self, chat_id: str, limit: int = 50) -> List[dict]:
        """Get recent messages from Redis"""
        if self.redis_client:
            try:
                message_key = f"chat:{chat_id}:messages"
                messages = self.redis_client.lrange(message_key, 0, limit - 1)
                return [json.loads(msg.decode('utf-8')) for msg in messages]
            except Exception as e:
                logger.error(f"Failed to get messages: {e}")
        return []

# Global connection manager
manager = ConnectionManager()

# Helper functions
def verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """Verify JWT token and return user information"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id, "email": email}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_user_from_token(credentials: HTTPAuthorizationCredentials) -> int:
    """Extract user ID from JWT token"""
    user_info = verify_token(credentials)
    return user_info["user_id"]

def generate_chat_id(user1_id: int, user2_id: int) -> str:
    """Generate a unique chat ID for two users"""
    return f"chat_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"

def generate_group_chat_id(item_id: int) -> str:
    """Generate a chat ID for item-related discussions"""
    return f"item_{item_id}"

# WebSocket endpoints
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """Main WebSocket endpoint for real-time messaging"""
    connection_id = f"{user_id}_{id(websocket)}"

    try:
        await manager.connect(websocket, user_id, connection_id)

        # Send welcome message
        await websocket.send_json({
            "type": "welcome",
            "message": f"Connected as user {user_id}",
            "timestamp": datetime.utcnow().isoformat()
        })

        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()

                message_type = data.get("type")
                message_data = data.get("data", {})

                if message_type == "chat_message":
                    await handle_chat_message(user_id, message_data)

                elif message_type == "join_chat":
                    await handle_join_chat(user_id, message_data)

                elif message_type == "leave_chat":
                    await handle_leave_chat(user_id, message_data)

                elif message_type == "typing_start":
                    await handle_typing_indicator(user_id, message_data, "start")

                elif message_type == "typing_stop":
                    await handle_typing_indicator(user_id, message_data, "stop")

                elif message_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing message from user {user_id}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Failed to process message",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        manager.disconnect(connection_id, user_id)

async def handle_chat_message(user_id: int, data: dict):
    """Handle incoming chat messages"""
    try:
        recipient_id = data.get("recipient_id")
        chat_id = data.get("chat_id")
        message_text = data.get("message")
        message_type = data.get("message_type", "text")

        if not all([recipient_id, chat_id, message_text]):
            return

        # Create message object
        message = {
            "type": "chat_message",
            "sender_id": user_id,
            "recipient_id": recipient_id,
            "chat_id": chat_id,
            "message": message_text,
            "message_type": message_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store message
        await manager.store_message(chat_id, message)

        # Send to recipient
        await manager.send_personal_message(message, recipient_id)

        # Send confirmation to sender
        await manager.send_personal_message({
            **message,
            "type": "message_sent",
            "status": "delivered"
        }, user_id)

    except Exception as e:
        logger.error(f"Error handling chat message: {e}")

async def handle_join_chat(user_id: int, data: dict):
    """Handle user joining a chat"""
    try:
        chat_id = data.get("chat_id")
        if not chat_id:
            return

        # Send recent messages
        recent_messages = await manager.get_recent_messages(chat_id, 20)

        await manager.send_personal_message({
            "type": "chat_history",
            "chat_id": chat_id,
            "messages": recent_messages,
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)

    except Exception as e:
        logger.error(f"Error handling join chat: {e}")

async def handle_leave_chat(user_id: int, data: dict):
    """Handle user leaving a chat"""
    try:
        chat_id = data.get("chat_id")
        if not chat_id:
            return

        # Notify other participants (if group chat)
        # For now, just acknowledge the leave
        await manager.send_personal_message({
            "type": "chat_left",
            "chat_id": chat_id,
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)

    except Exception as e:
        logger.error(f"Error handling leave chat: {e}")

async def handle_typing_indicator(user_id: int, data: dict, action: str):
    """Handle typing indicators"""
    try:
        chat_id = data.get("chat_id")
        if not chat_id:
            return

        # In a real implementation, you'd determine the other participants
        # For now, we'll broadcast to all connected users (not ideal for production)
        typing_message = {
            "type": f"typing_{action}",
            "user_id": user_id,
            "chat_id": chat_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        # This is a simplified version - in production you'd track chat participants
        for uid in manager.user_connections.keys():
            if uid != user_id:
                await manager.send_personal_message(typing_message, uid)

    except Exception as e:
        logger.error(f"Error handling typing indicator: {e}")

# REST API endpoints for chat management
@app.get("/chats/{user_id}")
async def get_user_chats(user_id: int):
    """Get all chats for a user"""
    # In a real implementation, you'd query the database for user's chats
    # For now, return a placeholder
    return {
        "chats": [],
        "message": "Chat list endpoint - implement database queries"
    }

@app.get("/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: str, limit: int = 50):
    """Get messages for a specific chat"""
    messages = await manager.get_recent_messages(chat_id, limit)
    return {"messages": messages}

@app.post("/chats/{chat_id}/messages")
async def send_message_rest(
    chat_id: str,
    message: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Send a message via REST API"""
    user_id = get_user_from_token(credentials)

    message_data = {
        "recipient_id": message.get("recipient_id"),
        "chat_id": chat_id,
        "message": message.get("message"),
        "message_type": message.get("message_type", "text")
    }

    await handle_chat_message(user_id, message_data)

    return {"status": "message_sent"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "websocket",
        "active_connections": len(manager.active_connections),
        "connected_users": len(manager.user_connections)
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("WEBSOCKET_PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)