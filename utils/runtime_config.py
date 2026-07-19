import threading
from utils.settings import settings

_lock = threading.Lock()

# Stores runtime overrides
_runtime_config = {
    "OPENAI_API_KEY": None,
    "OPENAI_BASE_URL": None,
    "OPENAI_MODEL_NAME": None,
}

def set_runtime_config(api_key: str | None, base_url: str | None, model_name: str | None):
    with _lock:
        _runtime_config["OPENAI_API_KEY"] = api_key
        _runtime_config["OPENAI_BASE_URL"] = base_url
        _runtime_config["OPENAI_MODEL_NAME"] = model_name

def clear_runtime_config():
    with _lock:
        _runtime_config["OPENAI_API_KEY"] = None
        _runtime_config["OPENAI_BASE_URL"] = None
        _runtime_config["OPENAI_MODEL_NAME"] = None

def get_runtime_config() -> dict[str, str | None]:
    with _lock:
        return {
            "OPENAI_API_KEY": _runtime_config["OPENAI_API_KEY"] or settings.OPENAI_API_KEY,
            "OPENAI_BASE_URL": _runtime_config["OPENAI_BASE_URL"] or settings.OPENAI_BASE_URL,
            "OPENAI_MODEL_NAME": _runtime_config["OPENAI_MODEL_NAME"] or settings.OPENAI_MODEL_NAME,
        }

def is_configured() -> bool:
    cfg = get_runtime_config()
    return bool(cfg["OPENAI_API_KEY"] and cfg["OPENAI_BASE_URL"] and cfg["OPENAI_MODEL_NAME"])
