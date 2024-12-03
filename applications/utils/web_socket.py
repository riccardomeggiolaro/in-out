from fastapi import WebSocket, WebSocketDisconnect

# create connectio manager of weight real time
class ConnectionManager:
	def __init__(self):
		self.active_connections: list[WebSocket] = []

	async def connect(self, websocket: WebSocket):
		await websocket.accept()
		self.active_connections.append(websocket)

	def disconnect(self, websocket: WebSocket):
		self.active_connections.remove(websocket)

	def disconnect_all(self):
		for connection in self.active_connections:
			self.disconnect(connection)

	async def send_personal_message(self, message: str, websocket: WebSocket):
		try:
			await websocket.send_text(message)
		except Exception:
			self.disconnect(websocket)

	async def broadcast(self, message: str):
		for connection in self.active_connections:
			try:
				await connection.send_json(message)
			except Exception:
				#print("client down")
				self.disconnect(connection)