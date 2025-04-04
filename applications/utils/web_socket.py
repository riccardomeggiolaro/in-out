from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        # Safely remove the websocket if it exists in the list
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    def disconnect_all(self):
        # Create a copy of the list to avoid modification during iteration
        connections_to_remove = self.active_connections.copy()
        for connection in connections_to_remove:
            self.disconnect(connection)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            # Check if the websocket is still in the active connections
            # before trying to disconnect it
            import libs.lb_log as lb_log
            lb_log.error(e)
            lb_log.error(type(message))
            lb_log.error(message)
            if websocket in self.active_connections:
                self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        # Create a copy to avoid modification during iteration
        connections = self.active_connections.copy()
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # Check if the connection is still active before disconnecting
                if connection in self.active_connections:
                    self.disconnect(connection)