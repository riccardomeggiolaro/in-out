import asyncio

class PanelMessage:
    def __init__(self, panel_id: int, duration: int = 0x5A):
        self.panel_id = panel_id
        self.duration = duration
        self.data = []

    def build_message(self, msg: str):
        # Convert empty string to space for panel to accept the clear command
        if msg == "":
            msg = " "

        self.data.clear()
        self.data.extend([0xFF, 0xFF, 0xFF, 0xFF])
        self.data.extend([0, 0])  # Placeholder for length
        self.data.extend([0, 0, 0x68, 0x32, 0x10])  # Fixed bytes
        self.data.extend([0x7B, 0])
        self.data.extend([0, 0])  # Placeholder for CC length
        self.data.extend([0, 0, 2, 0, 0, 0, 0, 0, 3])  # More fixed bytes

        message_bytes = []
        for char in msg:
            self.data.extend([0x12, 0x00, ord(char)])
            message_bytes.extend([0x12, 0x00, ord(char)])

        self.data.extend([0, 0, 0])  # Fixed 3 bytes after message

        data_length = len(self.data) - 6
        self.data[5] = (data_length >> 8) & 0xFF
        self.data[4] = data_length & 0xFF

        string_length = (len(msg) + 1) * 3 + 7
        self.data[13] = string_length

        self.data[10] = self.panel_id
        self.data[22] = (self.duration >> 8) & 0xFF
        self.data[23] = self.duration & 0xFF

        checksum = sum(self.data[8:]) & 0xFFFF
        self.data.append(checksum & 0xFF)
        self.data.append((checksum >> 8) & 0xFF)

        return bytes(self.data)
    
async def send_message(ip, port, username, password, timeout, endpoint, message):
    panel = PanelMessage(panel_id=0x10)
    packet = panel.build_message(message)

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout
        )

        writer.write(packet)
        await writer.drain()

        # Se vuoi leggere una risposta, puoi usare: await reader.read(n)
        # response = await reader.read(1024)

        writer.close()
        await writer.wait_closed()

    except asyncio.TimeoutError:
        raise ConnectionError(f"Host {ip}:{port} non raggiungibile (timeout)")
    except ConnectionRefusedError:
        raise ConnectionRefusedError(f"Connection refused by {ip}:{port}")
    except OSError as e:
        raise ConnectionError(f"Errore di rete con {ip}:{port}: {e}")
    except Exception as e:
        raise ConnectionError(f"Errore di rete con {ip}:{port}: {e}")