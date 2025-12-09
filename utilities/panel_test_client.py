#!/usr/bin/env python3
"""
Panel Test Client - Invia messaggi di test al pannello

Questo script invia messaggi di test al pannello (o al server di test)
usando lo stesso protocollo binario del sistema.

Usage:
    python panel_test_client.py [--host HOST] [--port PORT] [--message MSG]

Example:
    python panel_test_client.py --host 100.100.100.100 --port 5200 --message "ABC"
"""

import asyncio
import argparse
import sys


class PanelMessage:
    """Costruisce messaggi binari per il pannello."""

    def __init__(self, panel_id: int, duration: int = 0x5A):
        self.panel_id = panel_id
        self.duration = duration
        self.data = []

    def build_message(self, msg: str) -> bytes:
        """
        Costruisce un pacchetto binario per il pannello.

        Args:
            msg: Messaggio da visualizzare sul pannello

        Returns:
            bytes: Pacchetto binario pronto per l'invio
        """
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


async def send_message(host: str, port: int, message: str, panel_id: int = 16, duration: int = 90, timeout: float = 5.0):
    """
    Invia un messaggio al pannello.

    Args:
        host: Indirizzo IP del pannello
        port: Porta TCP del pannello
        message: Messaggio da visualizzare
        panel_id: ID del pannello (default: 16)
        duration: Durata visualizzazione in decimi di secondo (default: 90 = 9s)
        timeout: Timeout connessione in secondi (default: 5.0)
    """
    print(f"\n{'='*80}")
    print(f"📤 INVIO MESSAGGIO AL PANNELLO")
    print(f"{'='*80}")
    print(f"🌐 Host: {host}")
    print(f"🔌 Porta: {port}")
    print(f"💬 Messaggio: '{message}'")
    print(f"🆔 Panel ID: {panel_id} (0x{panel_id:02X})")
    print(f"⏱️  Duration: {duration} decimi = {duration/10:.1f} secondi")
    print(f"{'─'*80}")

    # Costruisci il pacchetto
    panel = PanelMessage(panel_id=panel_id, duration=duration)
    packet = panel.build_message(message)

    print(f"📦 Pacchetto generato: {len(packet)} byte")
    print(f"📊 Dati (hex): {packet.hex()}")
    print(f"{'─'*80}")

    try:
        print(f"🔌 Connessione a {host}:{port}...")
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        print(f"✅ Connesso!")

        print(f"📤 Invio pacchetto...")
        writer.write(packet)
        await writer.drain()
        print(f"✅ Pacchetto inviato con successo!")

        writer.close()
        await writer.wait_closed()
        print(f"🔌 Connessione chiusa")

        print(f"{'='*80}")
        print(f"✅ MESSAGGIO INVIATO CON SUCCESSO")
        print(f"{'='*80}\n")

    except asyncio.TimeoutError:
        print(f"❌ Timeout: Host {host}:{port} non raggiungibile")
        print(f"{'='*80}\n")
        sys.exit(1)
    except ConnectionRefusedError:
        print(f"❌ Connessione rifiutata da {host}:{port}")
        print(f"💡 Assicurati che il server/pannello sia attivo")
        print(f"{'='*80}\n")
        sys.exit(1)
    except OSError as e:
        print(f"❌ Errore di rete: {e}")
        print(f"{'='*80}\n")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*80}\n")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Panel Test Client - Invia messaggi di test al pannello'
    )
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Indirizzo IP del pannello (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5200,
        help='Porta TCP del pannello (default: 5200)'
    )
    parser.add_argument(
        '--message',
        default='TEST',
        help='Messaggio da visualizzare (default: TEST)'
    )
    parser.add_argument(
        '--panel-id',
        type=int,
        default=16,
        help='ID del pannello (default: 16)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=90,
        help='Durata in decimi di secondo (default: 90 = 9s)'
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=5.0,
        help='Timeout connessione in secondi (default: 5.0)'
    )

    args = parser.parse_args()

    try:
        asyncio.run(send_message(
            host=args.host,
            port=args.port,
            message=args.message,
            panel_id=args.panel_id,
            duration=args.duration,
            timeout=args.timeout
        ))
    except KeyboardInterrupt:
        print("\n\n❌ Operazione annullata dall'utente\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
