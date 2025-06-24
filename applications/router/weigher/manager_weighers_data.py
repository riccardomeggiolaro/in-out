weighers_data = {}

async def broadcastMessageWebSocket(message):
    for instance in weighers_data:
        for weigher in weighers_data[instance]:
            await weighers_data[instance][weigher]["sockets"].manager_realtime.broadcast(message)