import pytest
from unittest.mock import patch
from utils.runtime_config import (
    set_runtime_config,
    get_runtime_config,
    clear_runtime_config,
    is_configured,
)
from utils.settings import settings

def test_runtime_config_lifecycle():
    # Make sure we clean up at the beginning
    clear_runtime_config()
    
    # Mock settings values
    with patch.object(settings, "OPENAI_API_KEY", "env-key"), \
         patch.object(settings, "OPENAI_BASE_URL", "env-url"), \
         patch.object(settings, "OPENAI_MODEL_NAME", "env-model"):
             
        # By default, should return settings values
        cfg = get_runtime_config()
        assert cfg["OPENAI_API_KEY"] == "env-key"
        assert cfg["OPENAI_BASE_URL"] == "env-url"
        assert cfg["OPENAI_MODEL_NAME"] == "env-model"
        assert is_configured() is True
        
        # Override a single value
        set_runtime_config("user-key", "user-url", "user-model")
        cfg2 = get_runtime_config()
        assert cfg2["OPENAI_API_KEY"] == "user-key"
        assert cfg2["OPENAI_BASE_URL"] == "user-url"
        assert cfg2["OPENAI_MODEL_NAME"] == "user-model"
        assert is_configured() is True
        
        # Clear override
        clear_runtime_config()
        cfg3 = get_runtime_config()
        assert cfg3["OPENAI_API_KEY"] == "env-key"
        assert cfg3["OPENAI_BASE_URL"] == "env-url"
        assert cfg3["OPENAI_MODEL_NAME"] == "env-model"

def test_is_configured_empty():
    clear_runtime_config()
    with patch.object(settings, "OPENAI_API_KEY", None), \
         patch.object(settings, "OPENAI_BASE_URL", None), \
         patch.object(settings, "OPENAI_MODEL_NAME", None):
             
        assert is_configured() is False
        
        # Add overrides
        set_runtime_config("custom-key", "custom-url", "custom-model")
        assert is_configured() is True
        
        # Clear again
        clear_runtime_config()
        assert is_configured() is False
