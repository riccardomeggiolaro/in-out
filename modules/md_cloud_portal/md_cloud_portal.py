import time
import requests
import libs.lb_log as lb_log
import libs.lb_config as lb_config
from libs.lb_utils import createThread, startThread
from modules.md_cloud_portal.dto import CloudPortalDTO
from modules.md_cloud_portal.state import load_last_synced_id, save_last_synced_id
from modules.md_database.functions.get_in_out_for_cloud_sync import get_in_out_for_cloud_sync

name_module = "md_cloud_portal"

def init():
    global module_cloud_portal
    lb_log.info("init")
    module_cloud_portal = ModuleCloudPortal()
    thread = createThread(module_cloud_portal.start)
    startThread(thread=thread)
    lb_log.info("end")

def start():
    lb_log.info("start")
    lb_log.info("end")

def stop():
    pass

def _read_config() -> CloudPortalDTO:
    raw = lb_config.g_config.get("app_api", {}).get("cloud_portal") or {}
    return CloudPortalDTO(**raw)

class ModuleCloudPortal:
    def __init__(self):
        self.config = _read_config()
        self.last_synced_id = load_last_synced_id()

    def update_config(self, config: CloudPortalDTO):
        self.config = config

    def get_config(self) -> CloudPortalDTO:
        return self.config

    def _headers(self):
        return {"X-API-Key": self.config.api_key}

    def test_connection(self):
        config = self.config
        if not config.base_url or not config.api_key:
            return False, "Configurazione incompleta: base_url e api_key sono obbligatori"
        try:
            response = requests.get(
                f"{config.base_url}/api/ingest/ping",
                headers=self._headers(),
                timeout=5,
                verify=config.verify_ssl,
            )
            if response.status_code == 200:
                return True, response.json()
            return False, f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)

    def _serialize(self, inout):
        access = inout.access
        vehicle = access.vehicle if access else None

        return {
            "external_id": inout.id,
            "status": access.status.name if access and access.status else None,
            "type": access.type.name if access and access.type else None,
            "type_subject": inout.typeSubject.name if inout.typeSubject else None,
            "plate": vehicle.plate if vehicle else None,
            "vehicle_description": vehicle.description if vehicle else None,
            "subject_name": inout.subject.social_reason if inout.subject else None,
            "vector_name": inout.vector.social_reason if inout.vector else None,
            "driver_name": inout.driver.social_reason if inout.driver else None,
            "material": inout.material.description if inout.material else None,
            "weight1": inout.weight1.weight if inout.weight1 else None,
            "weight1_date": inout.weight1.date.isoformat() if inout.weight1 and inout.weight1.date else None,
            "weight1_pid": inout.weight1.pid if inout.weight1 else None,
            "weight2": inout.weight2.weight if inout.weight2 else None,
            "weight2_date": inout.weight2.date.isoformat() if inout.weight2 and inout.weight2.date else None,
            "weight2_pid": inout.weight2.pid if inout.weight2 else None,
            "net_weight": inout.net_weight,
            "document_reference": inout.document_reference,
            "note": inout.note,
            "date_created": access.date_created.isoformat() if access and access.date_created else None,
        }

    def _push_batch(self, payload):
        config = self.config
        response = requests.post(
            f"{config.base_url}/api/ingest/weighings",
            json={"weighings": payload},
            headers=self._headers(),
            timeout=15,
            verify=config.verify_ssl,
        )
        response.raise_for_status()
        return response.json()

    def start(self):
        while lb_config.g_enabled:
            config = self.config

            if not config.enabled or not config.base_url or not config.api_key:
                time.sleep(5)
                continue

            try:
                records = get_in_out_for_cloud_sync(
                    after_id=self.last_synced_id,
                    limit=config.batch_size,
                    only_closed=config.only_closed,
                )

                if not records:
                    time.sleep(config.sync_interval_seconds)
                    continue

                payload = [self._serialize(record) for record in records]
                self._push_batch(payload)

                self.last_synced_id = records[-1].id
                save_last_synced_id(self.last_synced_id)

                lb_log.info(f"cloud_portal: sincronizzate {len(records)} pesate (fino a id {self.last_synced_id})")

                # Se il batch era pieno, potrebbero esserci altri record: riprova subito
                time.sleep(0.2 if len(records) == config.batch_size else config.sync_interval_seconds)

            except Exception as e:
                lb_log.error(f"cloud_portal: errore di sincronizzazione: {e}")
                time.sleep(config.sync_interval_seconds)
