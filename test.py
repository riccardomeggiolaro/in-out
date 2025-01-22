import serial
import time

# Impostazioni della connessione seriale
baudrate = 19200
serial_port_name = "/dev/ttyUSB0"
timeout = 1  # Timeout di 1 secondo

# Connessione alla porta seriale
ser = serial.Serial(serial_port_name, baudrate, timeout=timeout)

# Verifica se la porta seriale è aperta
if ser.is_open:
    print(f"Connessione aperta alla porta {serial_port_name}")
else:
    print(f"Impossibile aprire la porta {serial_port_name}")
    exit()

# Invia il comando "R" seguito da CRLF
ser.write(b'OUTP10000\r\n')

# Pausa per assicurarsi che il comando venga inviato
time.sleep(1)

# Leggi la risposta dalla porta seriale (opzionale)
response = ser.readline()
print(f"Risposta ricevuta: {response}")

# Chiudi la connessione seriale
ser.close()