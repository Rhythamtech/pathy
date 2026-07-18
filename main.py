# Backward-compat shim — all CLI logic lives in cli.py
from cli import app  # noqa: F401

if __name__ == "__main__":
    app()