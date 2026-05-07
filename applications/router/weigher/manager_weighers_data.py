weighers_data = {}

async def broadcastMessageWebSocket(message):
    for instance in weighers_data:
        for weigher in weighers_data[instance]:
            await weighers_data[instance][weigher]["sockets"].manager_realtime.broadcast(message)

def has_active_connections(instance_name: str) -> bool:
    instance = weighers_data.get(instance_name, {})
    for weigher in instance.values():
        sockets = weigher.get("sockets")
        if sockets is None:
            continue
        if (sockets.manager_realtime and len(sockets.manager_realtime.active_connections) > 0):
            return True
        if (sockets.manager_diagnostic and len(sockets.manager_diagnostic.active_connections) > 0):
            return True
    return False