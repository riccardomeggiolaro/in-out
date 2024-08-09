import subprocess

def enable_wifi():
    try:
        # Esegui il comando per attivare l'adattatore WiFi
        subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "admin=enabled"], check=True)
        print("WiFi attivato con successo.")
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'attivazione del WiFi: {e}")
    except Exception as e:
        print(f"Si è verificato un errore inaspettato: {e}")

if __name__ == "__main__":
    enable_wifi()