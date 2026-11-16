"""
Registrazione automatica sul broker MQTT (certificato client senza configurazione).

1. Al primo contatto la CA del broker viene scaricata da https://host:porta/ca.crt
   senza verificarla (fiducia al primo contatto) e poi usata per verificare il
   servizio stesso e, in seguito, la connessione MQTT.
2. La chiave privata (EC P-256) viene generata qui e non lascia mai l'in-out:
   al broker arriva solo una richiesta CSR con CN = client ID.
3. Il broker firma subito la richiesta e ritorna il certificato.
4. Il rinnovo usa la stessa chiave: il broker riconosce la chiave del certificato
   attuale e rilascia il nuovo senza bisogno di altro.
"""
import http.client
import json
import os
import ssl
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

TIMEOUT = 20
# Il certificato viene rinnovato quando mancano meno di questi giorni alla scadenza
RENEW_BEFORE_DAYS = 60


class EnrollmentError(Exception):
	def __init__(self, message: str, code: str = ""):
		super().__init__(message)
		self.code = code


def _write_atomic(path: str, data: bytes, mode: int = 0o644) -> None:
	directory = os.path.dirname(path)
	os.makedirs(directory, exist_ok=True)
	fd, tmp = tempfile.mkstemp(dir=directory, prefix=".tmp-")
	try:
		with os.fdopen(fd, "wb") as f:
			f.write(data)
		os.chmod(tmp, mode)
		os.replace(tmp, path)
	except BaseException:
		try:
			os.remove(tmp)
		except OSError:
			pass
		raise


def load_certificate(path: str) -> Optional[x509.Certificate]:
	try:
		with open(path, "rb") as f:
			return x509.load_pem_x509_certificate(f.read())
	except (OSError, ValueError):
		return None


def needs_renewal(cert_path: str) -> bool:
	cert = load_certificate(cert_path)
	if cert is None:
		return True
	return cert.not_valid_after_utc < datetime.now(timezone.utc) + timedelta(days=RENEW_BEFORE_DAYS)


def _load_or_create_key(key_path: str):
	try:
		with open(key_path, "rb") as f:
			return serialization.load_pem_private_key(f.read(), password=None)
	except (OSError, ValueError):
		pass
	key = ec.generate_private_key(ec.SECP256R1())
	pem = key.private_bytes(
		serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
	)
	_write_atomic(key_path, pem, 0o600)
	return key


def _public_der(public_key) -> bytes:
	return public_key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)


def _request(host: str, port: int, method: str, path: str, ctx: ssl.SSLContext, body: Optional[dict] = None):
	conn = http.client.HTTPSConnection(host, port, timeout=TIMEOUT, context=ctx)
	try:
		headers = {"Accept": "application/json"}
		data = None
		if body is not None:
			data = json.dumps(body).encode()
			headers["Content-Type"] = "application/json"
		conn.request(method, path, body=data, headers=headers)
		resp = conn.getresponse()
		return resp.status, resp.read()
	except ssl.SSLCertVerificationError as e:
		raise EnrollmentError(
			f"Il certificato del broker non è valido per '{host}' ({e.verify_message}). "
			"L'host deve coincidere con BROKER_HOST del broker; se il broker è stato reinstallato "
			"elimina e reimposta la configurazione per scaricare la nuova CA.",
			"tls",
		)
	except (OSError, http.client.HTTPException) as e:
		raise EnrollmentError(f"Servizio di registrazione {host}:{port} non raggiungibile: {e}", "network")
	finally:
		conn.close()


def _fetch_ca(host: str, port: int) -> x509.Certificate:
	"""Primo contatto: scarica la CA senza verifica (fiducia al primo contatto)."""
	ctx = ssl.create_default_context()
	ctx.check_hostname = False
	ctx.verify_mode = ssl.CERT_NONE
	status, data = _request(host, port, "GET", "/ca.crt", ctx)
	if status != 200:
		raise EnrollmentError(f"Download della CA dal broker fallito (HTTP {status})", "ca")
	try:
		ca = x509.load_pem_x509_certificate(data)
		if not ca.extensions.get_extension_for_class(x509.BasicConstraints).value.ca:
			raise ValueError("non è una CA")
	except (ValueError, x509.ExtensionNotFound) as e:
		raise EnrollmentError(f"La CA ricevuta dal broker non è valida: {e}", "ca")
	return ca


def enroll(host: str, port: int, client_id: str, ca_path: str, cert_path: str, key_path: str, hostname: str = "") -> x509.Certificate:
	"""Ottiene (o rinnova) il certificato client. Ritorna il certificato installato."""
	ca_pem = None
	ca = load_certificate(ca_path)
	if ca is None:
		ca = _fetch_ca(host, port)
		ca_pem = ca.public_bytes(serialization.Encoding.PEM)

	# Da qui in poi il servizio viene verificato con la CA (salvata o appena ricevuta)
	ctx = ssl.create_default_context(cadata=ca.public_bytes(serialization.Encoding.PEM).decode())

	for attempt in range(2):
		key = _load_or_create_key(key_path)
		csr = (
			x509.CertificateSigningRequestBuilder()
			.subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, client_id)]))
			.sign(key, hashes.SHA256())
		)
		body = {
			"client_id": client_id,
			"csr": csr.public_bytes(serialization.Encoding.PEM).decode(),
			"hostname": hostname,
		}
		status, data = _request(host, port, "POST", "/enroll", ctx, body)
		try:
			payload = json.loads(data or b"{}")
		except ValueError:
			payload = {}
		if status == 200:
			break
		code = payload.get("code", "")
		detail = payload.get("detail") or f"HTTP {status}"
		if code == "key_revoked" and attempt == 0:
			# La chiave attuale è stata revocata dal broker: se ne genera una nuova
			os.remove(key_path)
			continue
		raise EnrollmentError(f"Registrazione rifiutata dal broker: {detail}", code)

	try:
		cert = x509.load_pem_x509_certificate(payload["certificate"].encode())
		cert.verify_directly_issued_by(ca)
	except Exception as e:
		raise EnrollmentError(f"Certificato ricevuto dal broker non valido: {e}", "certificate")
	if _public_der(cert.public_key()) != _public_der(key.public_key()):
		raise EnrollmentError("Il certificato ricevuto non corrisponde alla chiave dell'in-out", "certificate")

	if ca_pem is not None:
		_write_atomic(ca_path, ca_pem)
	_write_atomic(cert_path, cert.public_bytes(serialization.Encoding.PEM))
	return cert
