from fastapi import WebSocket
from typing import Dict, List

class WebSocketManager:
    def __init__(self):
        # Maps user_id (int or email string) to a list of active WebSockets
        self.active_connections: Dict[object, List[WebSocket]] = {}
        # Tracks which connected user_ids are admins (superusers)
        self.admin_ids: set = set()

    async def connect(self, user_id, websocket: WebSocket, is_admin: bool = False):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        if is_admin:
            self.admin_ids.add(user_id)

    def disconnect(self, user_id, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                self.admin_ids.discard(user_id)

    async def send_personal_message(self, message: dict, user_id):
        """Sends data specifically to all active devices of a single user."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Stale connection handling if client abruptly disconnected
                    pass

    async def send_to_admins(self, message: dict):
        """Sends data to every currently connected admin (superuser)."""
        for admin_id in list(self.admin_ids):
            await self.send_personal_message(message, admin_id)

    async def broadcast(self, message: dict):
        """Sends data to absolutely everyone connected."""
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

# Global instance initialization
ws_manager = WebSocketManager()
