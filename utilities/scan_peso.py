import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_ip(ip, port, comando, timeout):
    """Prova a connettersi e inviare comando"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Connessione
        sock.connect((ip, port))
        print(f"[+] {ip}:{port} - Connesso!")
        
        # Invia comando + CRLF
        comando_bytes = comando.encode('ascii') + b"\r\n"
        sock.sendall(comando_bytes)
        print(f"[>] {ip}:{port} - Inviato: {comando}\\r\\n")
        
        # Ricevi risposta
        sock.settimeout(timeout + 1)
        risposta = sock.recv(1024)
        
        if risposta:
            print(f"[<] {ip}:{port} - RISPOSTA: {risposta}")
            print(f"[<] {ip}:{port} - Decodificato: {risposta.decode('ascii', errors='ignore')}")
            return (ip, risposta)
        else:
            print(f"[-] {ip}:{port} - Nessuna risposta")
            
    except socket.timeout:
        print(f"[-] {ip}:{port} - Timeout")
    except ConnectionRefusedError:
        pass  # Porta chiusa, non stampa nulla
    except Exception as e:
        print(f"[-] {ip}:{port} - Errore: {e}")
    finally:
        try:
            sock.close()
        except:
            pass
    
    return None

def main():
    print("=" * 60)
    print("SCANNER DISPOSITIVI DI PESATURA")
    print("=" * 60)
    
    # Input parametri
    base_ip = input("\nInserisci l'IP base (es. 10.0.5.): ").strip()
    start = int(input("Inserisci IP iniziale (es. 1): ").strip())
    end = int(input("Inserisci IP finale (es. 254): ").strip())
    port = int(input("Inserisci porta (es. 4001): ").strip())
    comando = input("Inserisci comando da inviare (es. SN): ").strip()
    timeout = float(input("Inserisci timeout in secondi (es. 2): ").strip())
    
    print(f"\n[*] Scansione rete {base_ip}{start}-{end} sulla porta {port}")
    print(f"[*] Comando: {comando}\\r\\n")
    print(f"[*] Timeout: {timeout}s")
    print("-" * 60)
    
    risultati = []
    
    # Test parallelo con 20 thread
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        
        for i in range(start, end + 1):
            ip = f"{base_ip}{i}"
            futures.append(executor.submit(test_ip, ip, port, comando, timeout))
        
        # Raccogli risultati
        for future in as_completed(futures):
            result = future.result()
            if result:
                risultati.append(result)
    
    # Stampa riepilogo
    print("\n" + "=" * 60)
    print("[*] RIEPILOGO DISPOSITIVI CHE HANNO RISPOSTO:")
    print("=" * 60)
    
    if risultati:
        for ip, risposta in risultati:
            print(f"\n[!] {ip}:{port}")
            print(f"    Risposta: {risposta.decode('ascii', errors='ignore')}")
    else:
        print(f"[!] Nessun dispositivo ha risposto sulla porta {port}")

if __name__ == "__main__":
    main()