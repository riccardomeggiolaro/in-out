"""
WebSocket handler for real-time updates
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set

from fastapi import WebSocket, WebSocketDisconnect
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket) -> bool:
        """Accept new WebSocket connection"""
        if len(self.active_connections) >= settings.WS_MAX_CONNECTIONS:
            await websocket.close(code=1008, reason="Max connections reached")
            return False
        
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_info[websocket] = {
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        return True
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
        self.connection_info.pop(websocket, None)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connections"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_json(self, data: dict):
        """Broadcast JSON data to all connections"""
        message = json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            **data
        })
        await self.broadcast(message)


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint handler"""
    if not await manager.connect(websocket):
        return
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(heartbeat(websocket))
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(websocket, message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cancel heartbeat task
        if 'heartbeat_task' in locals():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect
        manager.disconnect(websocket)


async def handle_websocket_message(websocket: WebSocket, message: dict):
    """Handle incoming WebSocket message"""
    msg_type = message.get("type")
    
    if msg_type == "ping":
        # Respond to ping
        await websocket.send_json({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })
        # Update last ping time
        if websocket in manager.connection_info:
            manager.connection_info[websocket]["last_ping"] = datetime.utcnow()
    
    elif msg_type == "subscribe":
        # Subscribe to specific events
        events = message.get("events", [])
        if websocket in manager.connection_info:
            manager.connection_info[websocket]["subscriptions"] = events
        await websocket.send_json({
            "type": "subscribed",
            "events": events
        })
    
    elif msg_type == "unsubscribe":
        # Unsubscribe from events
        if websocket in manager.connection_info:
            manager.connection_info[websocket].pop("subscriptions", None)
        await websocket.send_json({
            "type": "unsubscribed"
        })
    
    elif msg_type == "get_status":
        # Send current status
        # TODO: Get actual status from sync manager
        await websocket.send_json({
            "type": "status",
            "data": {
                "active_syncs": 0,
                "total_connections": len(manager.active_connections)
            }
        })
    
    else:
        # Unknown message type
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {msg_type}"
        })


async def heartbeat(websocket: WebSocket):
    """Send periodic heartbeat to keep connection alive"""
    try:
        while True:
            await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat()
            })
    except Exception as e:
        logger.debug(f"Heartbeat stopped: {e}")


async def broadcast_sync_event(event_type: str, sync_id: int, data: dict):
    """Broadcast sync event to all connected clients"""
    await manager.broadcast_json({
        "type": "sync_event",
        "event": event_type,
        "sync_id": sync_id,
        "data": data
    })


async def broadcast_file_event(event_type: str, file_path: str, sync_id: int):
    """Broadcast file event to all connected clients"""
    await manager.broadcast_json({
        "type": "file_event",
        "event": event_type,
        "file_path": file_path,
        "sync_id": sync_id
    })


async def broadcast_system_event(event_type: str, data: dict):
    """Broadcast system event to all connected clients"""
    await manager.broadcast_json({
        "type": "system_event",
        "event": event_type,
        "data": data
    })


async def broadcast_metrics(metrics: dict):
    """Broadcast metrics update to all connected clients"""
    await manager.broadcast_json({
        "type": "metrics",
        "data": metrics
    })
