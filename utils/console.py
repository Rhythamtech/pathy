from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.status import Status


console = Console()
OUTPUT_DIR = Path("output")


def heading(text: str) -> None:
    console.print(Panel.fit(text, style="bold cyan"))


def status(text: str) -> Status:
    return console.status(text, spinner="dots")


def render_markdown(text: str) -> None:
    console.print(Markdown(text))


def save_markdown(filename: str, content: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path