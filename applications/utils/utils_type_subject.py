"""
Memoria dell'ultimo tipo soggetto (CUSTOMER/SUPPLIER) utilizzato.

- Per ogni pesa: l'ultimo tipo scelto sulla pesa diventa il predefinito per le
  pesate successive su quella pesa (dopo una pesata, deselezione, riavvio...).
- Per i form (prenotazioni, transiti, preferiti, accessi): l'ultimo tipo usato
  creando un accesso dall'interfaccia diventa il predefinito del form.

Viene salvato in config.json sotto app_api.last_type_subject, così sopravvive
ai riavvii. Se non c'è ancora un valore memorizzato si usa il tipo predefinito
della configurazione (app_api.default_type_subject).

Struttura:
	"last_type_subject": {
		"forms": "SUPPLIER",
		"weighers": {"<instance_name>": {"<weigher_name>": "CUSTOMER"}}
	}
"""
import libs.lb_config as lb_config

VALID_TYPE_SUBJECTS = ("CUSTOMER", "SUPPLIER")


def _normalize(type_subject):
	if type_subject is None:
		return None
	value = type_subject.name if hasattr(type_subject, "name") else str(type_subject)
	return value if value in VALID_TYPE_SUBJECTS else None


def _store() -> dict:
	app_api = lb_config.g_config["app_api"]
	store = app_api.get("last_type_subject")
	if not isinstance(store, dict):
		store = {}
		app_api["last_type_subject"] = store
	if not isinstance(store.get("weighers"), dict):
		store["weighers"] = {}
	return store


def get_configured_default_type_subject() -> str:
	return _normalize(lb_config.g_config["app_api"].get("default_type_subject")) or "CUSTOMER"


def get_weigher_type_subject(instance_name: str, weigher_name: str) -> str:
	"""Ultimo tipo soggetto usato sulla pesa, altrimenti il predefinito di configurazione."""
	last = _store()["weighers"].get(instance_name, {}).get(weigher_name)
	return _normalize(last) or get_configured_default_type_subject()


def get_form_type_subject() -> str:
	"""Ultimo tipo soggetto usato nei form, altrimenti il predefinito di configurazione."""
	return _normalize(_store().get("forms")) or get_configured_default_type_subject()


def remember_weigher_type_subject(instance_name: str, weigher_name: str, type_subject) -> None:
	value = _normalize(type_subject)
	if not value or not instance_name or not weigher_name:
		return
	weighers = _store()["weighers"]
	if weighers.get(instance_name, {}).get(weigher_name) == value:
		return
	weighers.setdefault(instance_name, {})[weigher_name] = value
	lb_config.saveconfig()


def remember_form_type_subject(type_subject) -> None:
	value = _normalize(type_subject)
	if not value:
		return
	store = _store()
	if store.get("forms") == value:
		return
	store["forms"] = value
	lb_config.saveconfig()
