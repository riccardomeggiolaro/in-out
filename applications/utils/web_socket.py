import asyncio
import json
import libs.lb_log as lb_log
from fastapi import WebSocket, WebSocketDisconnect

# Event loop del server (uvicorn) a cui appartengono i websocket.
# Viene memorizzato alla prima connect(), che gira sempre dentro il loop del server.
_server_loop: asyncio.AbstractEventLoop = None

# Tempo massimo per l'invio di un messaggio a un singolo client:
# un client lento o "mezzo morto" non deve mai bloccare chi trasmette.
SEND_TIMEOUT = 3


def _current_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        global _server_loop
        await websocket.accept()
        _server_loop = asyncio.get_running_loop()
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
            await asyncio.wait_for(websocket.send_text(message), timeout=SEND_TIMEOUT)
        except Exception as e:
            if websocket in self.active_connections:
                self.disconnect(websocket)

    async def _send_one(self, connection: WebSocket, text: str):
        try:
            await asyncio.wait_for(connection.send_text(text), timeout=SEND_TIMEOUT)
        except Exception as e:
            # Invio fallito o scaduto: il client viene scollegato
            # (il browser della dashboard si riconnette da solo)
            if connection in self.active_connections:
                self.disconnect(connection)
            try:
                await asyncio.wait_for(connection.close(), timeout=1)
            except Exception:
                pass

    async def _send_to_all(self, text: str):
        # Gira SEMPRE nel loop del server, l'unico a cui appartengono i websocket.
        # Invio in parallelo: un client lento non ritarda gli altri.
        connections = self.active_connections.copy()
        if connections:
            await asyncio.gather(*(self._send_one(c, text) for c in connections))

    async def broadcast(self, message: str):
        if not self.active_connections:
            return
        # Serializza subito, così il messaggio non cambia se l'oggetto viene modificato dopo
        try:
            # Stessa codifica di WebSocket.send_json usata in precedenza
            text = json.dumps(message, separators=(",", ":"), ensure_ascii=False)
        except Exception as e:
            lb_log.warning(f"Broadcast websocket: messaggio non serializzabile: {e}")
            return
        loop = _current_loop()
        if _server_loop is not None and loop is not _server_loop and _server_loop.is_running():
            # Chiamato da un thread (es. thread della pesa tramite asyncio.run):
            # i websocket appartengono al loop del server, quindi l'invio viene
            # passato a quel loop senza attenderne la fine, così il thread
            # chiamante non può mai restare bloccato su un client.
            asyncio.run_coroutine_threadsafe(self._send_to_all(text), _server_loop)
            return
        await self._send_to_all(text)
