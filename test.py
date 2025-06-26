import socket

# Indirizzo IP e porta del server
SERVER_IP = '10.0.5.178'
SERVER_PORT = 4001

def main():
    # Creazione del socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # Connessione al server
            s.connect((SERVER_IP, SERVER_PORT))
            print(f"Connesso a {SERVER_IP}:{SERVER_PORT}")

            # Esempio di invio dati
            message = ("REXT" + chr(13)+chr(10)).encode()
            s.sendall(message)
            print(f"Inviato: {message}")

            # Ricezione di una risposta
            response = s.recv(1024)
            print(f"Ricevuto: {response.decode('utf-8')}")

        except Exception as e:
            print(f"Errore durante la connessione: {e}")

if __name__ == '__main__':
    main()
