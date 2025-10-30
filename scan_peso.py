#!/usr/bin/env python3
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_ip(ip, port=4001, timeout=2):
    """Prova a connettersi e inviare comando SN"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Connessione
        sock.connect((ip, port))
        print(f"[+] {ip}:{port} - Connesso!")
        
        # Invia comando SN + CRLF
        comando = b"SN\r\n"
        sock.sendall(comando)
        print(f"[>] {ip}:{port} - Inviato: SN\\r\\n")
        
        # Ricevi risposta
        sock.settimeout(3)
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
    # Range di IP da testare
    base_ip = "10.0.5."
    start = 1
    end = 254
    port = 4001
    
    print(f"[*] Scansione rete {base_ip}0/24 sulla porta {port}")
    print(f"[*] Comando: SN\\r\\n")
    print("-" * 60)
    
    risultati = []
    
    # Test parallelo con 20 thread
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        
        for i in range(start, end + 1):
            ip = f"{base_ip}{i}"
            futures.append(executor.submit(test_ip, ip, port))
        
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
            print(f"\n[!] {ip}:4001")
            print(f"    Risposta: {risposta.decode('ascii', errors='ignore')}")
    else:
        print("[!] Nessun dispositivo ha risposto sulla porta 4001")

if __name__ == "__main__":
    main()