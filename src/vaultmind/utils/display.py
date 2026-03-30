"""Rich terminal output helpers."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
error_console = Console(stderr=True)


def print_success(title: str, message: str) -> None:
    console.print(Panel(message, title=f"✅ {title}", border_style="green"))


def print_error(message: str) -> None:
    error_console.print(Panel(message, title="❌ Error", border_style="red"))


def print_warning(message: str) -> None:
    console.print(Panel(message, title="⚠️  Warning", border_style="yellow"))


def print_info(message: str) -> None:
    console.print(f"[dim]{message}[/dim]")


def get_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )
