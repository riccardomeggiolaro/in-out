import json
import os
import libs.lb_config as lb_config
import libs.lb_log as lb_log

def _state_path():
    return os.path.join(lb_config.g_workpath, "cloud_portal_state.json")

def load_last_synced_id() -> int:
    path = _state_path()
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            return int(json.load(f).get("last_synced_id", 0))
    except Exception as e:
        lb_log.error(f"cloud_portal: error reading state file: {e}")
        return 0

def save_last_synced_id(last_synced_id: int):
    path = _state_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"last_synced_id": last_synced_id}, f)
    except Exception as e:
        lb_log.error(f"cloud_portal: error writing state file: {e}")
