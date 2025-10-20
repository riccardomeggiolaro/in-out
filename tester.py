import socket
import time
from datetime import datetime

HOST = '10.0.5.177'
PORT = 4001
BUFFER_SIZE = 1024

def main():
    print(f"Connessione a {HOST}:{PORT}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    print("Connesso!\n")
    
    last_time = None
    buffer = b""
    
    try:
        while True:
            chunk = sock.recv(BUFFER_SIZE)
            if not chunk:
                break
            
            buffer += chunk
            
            while b"\r\n" in buffer:
                pos = buffer.find(b"\r\n")
                message = buffer[:pos + 2]
                buffer = buffer[pos + 2:]
                
                current_time = time.time()
                now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                decoded = message.decode('utf-8', errors='ignore').replace('\r\n', '[CRLF]')
                
                if last_time:
                    interval = current_time - last_time
                    print(f"[{now}] {interval:.3f}s | {decoded}")
                else:
                    print(f"[{now}] PRIMO | {decoded}")
                
                last_time = current_time
                
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()

if __name__ == "__main__":
    main()