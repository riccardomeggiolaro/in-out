#!/usr/bin/env python3
"""
Panel Test Server - Simula un pannello con protocollo binario TCP custom

Questo server riceve pacchetti dal sistema panel/siren e decodifica il protocollo
binario per mostrare i messaggi ricevuti.

Usage:
    python panel_test_server.py [--host HOST] [--port PORT]

Example:
    python panel_test_server.py --host 0.0.0.0 --port 5200
"""

import asyncio
import sys
import argparse
from datetime import datetime


class PanelTestServer:
    """Server di test che simula un pannello con protocollo binario."""

    def __init__(self, host='0.0.0.0', port=5200):
        self.host = host
        self.port = port
        self.message_count = 0

    def decode_packet(self, data: bytes) -> dict:
        """
        Decodifica un pacchetto binario del pannello.

        Struttura pacchetto:
        - Byte 0-3:   Header [0xFF, 0xFF, 0xFF, 0xFF]
        - Byte 4-5:   Lunghezza pacchetto (little-endian)
        - Byte 6-9:   Fixed bytes
        - Byte 10:    Panel ID
        - Byte 11-21: Fixed bytes e placeholder
        - Byte 22-23: Duration (big-endian)
        - Byte 24+:   Messaggio codificato (3 byte per carattere: 0x12, 0x00, ASCII)
        - Last 2:     Checksum
        """
        result = {
            'valid': False,
            'panel_id': None,
            'duration': None,
            'message': '',
            'raw_length': len(data),
            'error': None
        }

        try:
            # Verifica lunghezza minima
            if len(data) < 30:
                result['error'] = f"Pacchetto troppo corto: {len(data)} byte"
                return result

            # Verifica header
            header = data[0:4]
            if header != bytes([0xFF, 0xFF, 0xFF, 0xFF]):
                result['error'] = f"Header non valido: {header.hex()}"
                return result

            # Leggi lunghezza pacchetto
            packet_length = data[4] | (data[5] << 8)
            result['packet_length'] = packet_length

            # Leggi Panel ID (byte 10)
            result['panel_id'] = data[10]

            # Leggi Duration (byte 22-23, big-endian)
            duration_raw = (data[22] << 8) | data[23]
            result['duration'] = duration_raw
            result['duration_seconds'] = duration_raw / 10.0

            # Decodifica messaggio
            # Il messaggio inizia dopo i fixed bytes, cerca pattern 0x12 0x00
            message_chars = []
            i = 24  # Inizia dopo i fixed bytes

            while i < len(data) - 5:  # -5 per checksum e terminatore
                # Pattern messaggio: 0x12 0x00 ASCII
                if i + 2 < len(data) and data[i] == 0x12 and data[i+1] == 0x00:
                    char_code = data[i+2]
                    if 32 <= char_code <= 126:  # ASCII stampabile
                        message_chars.append(chr(char_code))
                    i += 3
                else:
                    break

            result['message'] = ''.join(message_chars)

            # Verifica checksum
            checksum_calculated = sum(data[8:-2]) & 0xFFFF
            checksum_received = data[-2] | (data[-1] << 8)
            result['checksum_valid'] = checksum_calculated == checksum_received
            result['checksum_calculated'] = checksum_calculated
            result['checksum_received'] = checksum_received

            result['valid'] = True

        except Exception as e:
            result['error'] = str(e)

        return result

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Gestisce una connessione client."""
        addr = writer.get_extra_info('peername')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        print(f"\n{'='*80}")
        print(f"[{timestamp}] 🔌 Nuova connessione da {addr[0]}:{addr[1]}")
        print(f"{'='*80}")

        try:
            # Leggi i dati
            data = await asyncio.wait_for(reader.read(4096), timeout=5.0)

            if not data:
                print("⚠️  Nessun dato ricevuto")
                return

            print(f"\n📦 Ricevuti {len(data)} byte")
            print(f"📊 Dati raw (hex): {data.hex()}")

            # Decodifica il pacchetto
            decoded = self.decode_packet(data)

            print(f"\n{'─'*80}")
            print("📋 DECODIFICA PACCHETTO:")
            print(f"{'─'*80}")

            if decoded['valid']:
                self.message_count += 1

                print(f"✅ Pacchetto valido")
                print(f"🆔 Panel ID: {decoded['panel_id']} (0x{decoded['panel_id']:02X})")
                print(f"⏱️  Duration: {decoded['duration']} decimi = {decoded['duration_seconds']:.1f} secondi")
                print(f"💬 Messaggio: '{decoded['message']}'")
                print(f"📏 Lunghezza messaggio: {len(decoded['message'])} caratteri")
                print(f"🔢 Checksum: {'✅ OK' if decoded['checksum_valid'] else '❌ ERRORE'}")
                print(f"   - Calcolato: 0x{decoded['checksum_calculated']:04X}")
                print(f"   - Ricevuto:  0x{decoded['checksum_received']:04X}")

                # Mostra box con messaggio
                print(f"\n{'┌' + '─'*40 + '┐'}")
                print(f"│ 📺 DISPLAY PANNELLO:")
                print(f"│ {' '*40}")
                msg_display = decoded['message'].center(40)
                print(f"│ {msg_display}")
                print(f"│ {' '*40}")
                print(f"│ (visualizzato per {decoded['duration_seconds']:.1f}s)")
                print(f"{'└' + '─'*40 + '┘'}")

                print(f"\n📈 Messaggi ricevuti: {self.message_count}")

            else:
                print(f"❌ Pacchetto NON valido")
                if decoded['error']:
                    print(f"🐛 Errore: {decoded['error']}")

                if decoded['panel_id'] is not None:
                    print(f"🆔 Panel ID: {decoded['panel_id']}")
                if decoded['duration'] is not None:
                    print(f"⏱️  Duration: {decoded['duration']} ({decoded.get('duration_seconds', 0):.1f}s)")
                if decoded['message']:
                    print(f"💬 Messaggio parziale: '{decoded['message']}'")

        except asyncio.TimeoutError:
            print("⏱️  Timeout: nessun dato ricevuto entro 5 secondi")
        except Exception as e:
            print(f"❌ Errore nella gestione del client: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print(f"\n{'─'*80}")
            print(f"🔌 Chiusura connessione da {addr[0]}:{addr[1]}")
            print(f"{'='*80}\n")
            writer.close()
            await writer.wait_closed()

    async def start(self):
        """Avvia il server."""
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )

        addr = server.sockets[0].getsockname()
        print(f"\n{'='*80}")
        print(f"🚀 Panel Test Server AVVIATO")
        print(f"{'='*80}")
        print(f"📍 Host: {self.host}")
        print(f"🔌 Porta: {self.port}")
        print(f"🌐 Indirizzo: {addr[0]}:{addr[1]}")
        print(f"{'='*80}")
        print(f"\n⏳ In attesa di connessioni...")
        print(f"💡 Configura il pannello con IP: {addr[0]} e Porta: {self.port}")
        print(f"💡 Premi Ctrl+C per terminare\n")

        async with server:
            await server.serve_forever()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Panel Test Server - Simula un pannello con protocollo binario TCP'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host su cui ascoltare (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5200,
        help='Porta su cui ascoltare (default: 5200)'
    )

    args = parser.parse_args()

    server = PanelTestServer(host=args.host, port=args.port)

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n\n{'='*80}")
        print("🛑 Server arrestato dall'utente")
        print(f"📊 Totale messaggi ricevuti: {server.message_count}")
        print(f"{'='*80}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Errore fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
