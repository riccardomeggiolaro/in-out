from pymodbus.client import ModbusTcpClient, ModbusSerialClient
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoReconnectModbusClient:
    def __init__(self, client, reconnect_delay=5):
        """
        client: ModbusTcpClient o ModbusSerialClient
        reconnect_delay: secondi tra tentativi di riconnessione
        """
        self.client = client
        self.reconnect_delay = reconnect_delay
        self.connected = False
    
    def connect(self):
        """Tenta la connessione all'infinito"""
        while not self.connected:
            try:
                logger.info("Tentativo di connessione...")
                self.connected = self.client.connect()
                if self.connected:
                    logger.info("Connesso!")
                else:
                    logger.warning(f"Connessione fallita, riprovo tra {self.reconnect_delay}s")
                    time.sleep(self.reconnect_delay)
            except Exception as e:
                logger.error(f"Errore connessione: {e}, riprovo tra {self.reconnect_delay}s")
                time.sleep(self.reconnect_delay)
    
    def _execute_with_retry(self, func, *args, **kwargs):
        """Esegue una funzione con riconnessione automatica"""
        while True:
            try:
                if not self.connected:
                    self.connect()
                
                result = func(*args, **kwargs)
                
                if result.isError():
                    logger.warning("Errore Modbus, riconnetto...")
                    self.connected = False
                    self.client.close()
                    time.sleep(self.reconnect_delay)
                    continue
                
                return result
                
            except Exception as e:
                logger.error(f"Eccezione: {e}, riconnetto...")
                self.connected = False
                try:
                    self.client.close()
                except:
                    pass
                time.sleep(self.reconnect_delay)
    
    # Metodi di lettura - USA 'unit' INVECE DI 'slave'
    def read_holding_registers(self, address, count, unit=1):
        result = self._execute_with_retry(
            self.client.read_holding_registers, 
            address, count, unit=unit
        )
        return result.registers
    
    def read_input_registers(self, address, count, unit=1):
        result = self._execute_with_retry(
            self.client.read_input_registers,
            address, count, unit=unit
        )
        return result.registers
    
    def read_coils(self, address, count, unit=1):
        result = self._execute_with_retry(
            self.client.read_coils,
            address, count, unit=unit
        )
        return result.bits
    
    def read_discrete_inputs(self, address, count, unit=1):
        result = self._execute_with_retry(
            self.client.read_discrete_inputs,
            address, count, unit=unit
        )
        return result.bits
    
    # Metodi di scrittura - USA 'unit' INVECE DI 'slave'
    def write_register(self, address, value, unit=1):
        result = self._execute_with_retry(
            self.client.write_register,
            address, value, unit=unit
        )
        return True
    
    def write_registers(self, address, values, unit=1):
        result = self._execute_with_retry(
            self.client.write_registers,
            address, values, unit=unit
        )
        return True
    
    def write_coil(self, address, value, unit=1):
        result = self._execute_with_retry(
            self.client.write_coil,
            address, value, unit=unit
        )
        return True
    
    def write_coils(self, address, values, unit=1):
        result = self._execute_with_retry(
            self.client.write_coils,
            address, values, unit=unit
        )
        return True
    
    def close(self):
        """Chiude la connessione"""
        try:
            self.client.close()
            self.connected = False
        except:
            pass


# ESEMPIO USO
if __name__ == "__main__":
    # TCP
    tcp_client = ModbusTcpClient('10.0.5.178', port=4001, timeout=3)
    modbus = AutoReconnectModbusClient(tcp_client, reconnect_delay=5)
    
    # Oppure SERIALE
    # serial_client = ModbusSerialClient(
    #     port='/dev/ttyUSB0',
    #     baudrate=9600,
    #     timeout=3
    # )
    # modbus = AutoReconnectModbusClient(serial_client, reconnect_delay=5)
    
    # Connessione iniziale
    modbus.connect()
    
    # Uso normale
    while True:
        try:
            # Lettura - nota: usa 'unit' non 'slave'
            data = modbus.read_holding_registers(0, 10, unit=1)
            print(f"Dati letti: {data}")
            
            # Scrittura
            modbus.write_register(0, 123, unit=1)
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("Chiusura...")
            modbus.close()
            break