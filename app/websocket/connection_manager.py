"""
WebSocket connection manager for real-time batch updates
Manages connected clients and broadcasts events to subscribed users
"""

from typing import Dict, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""

    def __init__(self):
        # Active connections: {websocket: user_id}
        self.active_connections: Dict[WebSocket, int] = {}
        # Batch subscriptions: {batch_id: set of websockets}
        self.batch_subscriptions: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[websocket] = user_id
        logger.info(f"WebSocket connected: user_id={user_id}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        user_id = self.active_connections.get(websocket)
        if websocket in self.active_connections:
            del self.active_connections[websocket]

        # Remove from all batch subscriptions
        for batch_id, subscribers in list(self.batch_subscriptions.items()):
            if websocket in subscribers:
                subscribers.remove(websocket)
            # Clean up empty subscription sets
            if not subscribers:
                del self.batch_subscriptions[batch_id]

        logger.info(f"WebSocket disconnected: user_id={user_id}")

    def subscribe_to_batch(self, websocket: WebSocket, batch_id: int):
        """Subscribe a connection to batch updates"""
        if batch_id not in self.batch_subscriptions:
            self.batch_subscriptions[batch_id] = set()
        self.batch_subscriptions[batch_id].add(websocket)
        logger.info(f"Subscribed to batch {batch_id}")

    def unsubscribe_from_batch(self, websocket: WebSocket, batch_id: int):
        """Unsubscribe a connection from batch updates"""
        if batch_id in self.batch_subscriptions:
            self.batch_subscriptions[batch_id].discard(websocket)
            if not self.batch_subscriptions[batch_id]:
                del self.batch_subscriptions[batch_id]
        logger.info(f"Unsubscribed from batch {batch_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_batch(self, batch_id: int, message: dict, exclude: WebSocket = None):
        """Broadcast a message to all subscribers of a batch"""
        if batch_id not in self.batch_subscriptions:
            return

        dead_connections = []
        for websocket in self.batch_subscriptions[batch_id]:
            if exclude and websocket == exclude:
                continue
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to batch {batch_id}: {e}")
                dead_connections.append(websocket)

        # Clean up dead connections
        for websocket in dead_connections:
            self.disconnect(websocket)

    async def broadcast_transaction_updated(self, batch_id: int, transaction: dict, exclude: WebSocket = None):
        """Broadcast that a transaction was updated"""
        message = {
            "type": "transaction_updated",
            "batch_id": batch_id,
            "transaction": transaction
        }
        await self.broadcast_to_batch(batch_id, message, exclude)

    async def broadcast_batch_progress(self, batch_id: int, progress: dict, exclude: WebSocket = None):
        """Broadcast batch progress update"""
        message = {
            "type": "batch_progress",
            "batch_id": batch_id,
            "progress": progress
        }
        await self.broadcast_to_batch(batch_id, message, exclude)

    async def broadcast_batch_complete(self, batch_id: int):
        """Broadcast that a batch is complete"""
        message = {
            "type": "batch_complete",
            "batch_id": batch_id
        }
        await self.broadcast_to_batch(batch_id, message)


# Global connection manager instance
manager = ConnectionManager()
