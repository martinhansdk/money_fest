"""
WebSocket router for real-time updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.websocket.connection_manager import manager
from app.auth import verify_session
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates

    Client sends:
    - {"type": "subscribe", "batch_id": 123} - Subscribe to batch updates
    - {"type": "unsubscribe", "batch_id": 123} - Unsubscribe from batch
    - {"type": "ping"} - Keep-alive ping

    Server sends:
    - {"type": "transaction_updated", "batch_id": 123, "transaction": {...}}
    - {"type": "batch_progress", "batch_id": 123, "progress": {...}}
    - {"type": "batch_complete", "batch_id": 123}
    - {"type": "pong"} - Response to ping
    """
    # Get session from cookie
    session_id = websocket.cookies.get("session_id")
    if not session_id:
        await websocket.close(code=1008, reason="Not authenticated")
        return

    user_id = verify_session(session_id)
    if not user_id:
        await websocket.close(code=1008, reason="Invalid session")
        return

    # Accept connection
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "subscribe":
                batch_id = data.get("batch_id")
                if batch_id:
                    manager.subscribe_to_batch(websocket, batch_id)
                    await manager.send_personal_message(
                        {"type": "subscribed", "batch_id": batch_id},
                        websocket
                    )

            elif message_type == "unsubscribe":
                batch_id = data.get("batch_id")
                if batch_id:
                    manager.unsubscribe_from_batch(websocket, batch_id)
                    await manager.send_personal_message(
                        {"type": "unsubscribed", "batch_id": batch_id},
                        websocket
                    )

            elif message_type == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
