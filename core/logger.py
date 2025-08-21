import json, time
from pathlib import Path

LOG_PATH = Path("runs.jsonl")

def log_json(obj: dict):
    obj = {"ts": time.time(), **obj}
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")