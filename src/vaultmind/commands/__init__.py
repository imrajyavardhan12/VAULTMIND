"""Command registration for modular CLI wiring."""

from __future__ import annotations

import typer


def register_commands(app: typer.Typer) -> None:
    """Register all commands on the main Typer app."""
    from vaultmind.commands.brief import brief
    from vaultmind.commands.compile import compile
    from vaultmind.commands.digest import digest
    from vaultmind.commands.find import find
    from vaultmind.commands.flashcard import flashcard
    from vaultmind.commands.init import init
    from vaultmind.commands.reflect import reflect
    from vaultmind.commands.stats import stats

    app.command("init")(init)
    app.command("brief")(brief)
    app.command("compile")(compile)
    app.command("digest")(digest)
    app.command("find")(find)
    app.command("flashcard")(flashcard)
    app.command("reflect")(reflect)
    app.command("stats")(stats)
