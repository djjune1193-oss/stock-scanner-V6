from pathlib import Path
import json
from datetime import datetime

STATUS_FILE = Path(__file__).resolve().parent / "scan_status.json"

def set_scan_running(is_running: bool):
    STATUS_FILE.write_text(json.dumps({
        "running": is_running,
        "updated": datetime.utcnow().isoformat()
    }))

def get_scan_status():
    if not STATUS_FILE.exists():
        return {"running": False}
    return json.loads(STATUS_FILE.read_text())
