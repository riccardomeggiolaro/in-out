from applications.router.anagrafic.manager_anagrafics import manager_anagrafics

class Message:
    def __init__(self, action, name):
        self.action = action
        self.data = name

class WebSocket:
    async def broadcastAddAnagrafic(self, anagrafic, data: any):
        message = Message("add", data).__dict__
        await manager_anagrafics[anagrafic].broadcast(message)
        
    async def broadcastUpdateAnagrafic(self, anagrafic: str, data: any):
        message = Message("update", data).__dict__
        await manager_anagrafics[anagrafic].broadcast(message)
        
    async def broadcastDeleteAnagrafic(self, anagrafic: str, data: any):
        message = Message("delete", data).__dict__
        await manager_anagrafics[anagrafic].broadcast(message)
        
    async def broadcastCallAnagrafic(self, anagrafic: str, data: any):
        message = Message("call", data).__dict__
        await manager_anagrafics[anagrafic].broadcast(message)
        
    async def broadcastMessageAnagrafic(self, anagrafic: str, data: any):
        message = Message("message", data).__dict__
        await manager_anagrafics[anagrafic].broadcast(message)