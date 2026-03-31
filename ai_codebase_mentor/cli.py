"""CLI entry point for ai-codebase-mentor."""

import sys
import click
from ai_codebase_mentor import __version__


# Registry of supported runtimes to converter classes.
# v1.0: claude only. v1.2 adds opencode, v1.3 adds gemini.
def _get_converters():
    """Lazy import converters to avoid import errors if optional deps missing."""
    from ai_codebase_mentor.converters.claude import ClaudeInstaller
    from ai_codebase_mentor.converters.opencode import OpenCodeInstaller
    from ai_codebase_mentor.converters.gemini import GeminiInstaller
    return {"claude": ClaudeInstaller, "opencode": OpenCodeInstaller, "gemini": GeminiInstaller}


@click.group()
@click.version_option(version=__version__, prog_name="ai-codebase-mentor")
def main():
    """ai-codebase-mentor: install the Codebase Wizard plugin for AI runtimes."""


@main.command()
@click.option("--for", "runtime", required=True,
              help="Target runtime: claude, opencode, all")
@click.option("--project", is_flag=True, default=False,
              help="Install per-project (./plugins/) instead of global (~/.claude/plugins/).")
def install(runtime, project):
    """Install the Codebase Wizard plugin."""
    converters = _get_converters()
    target = "project" if project else "global"
    runtimes = list(converters.keys()) if runtime == "all" else [runtime]
    for rt in runtimes:
        if rt not in converters:
            click.echo(f"Unsupported runtime: {rt}", err=True)
            sys.exit(1)
        installer = converters[rt]()
        try:
            installer.install(installer.plugin_source, target)
            click.echo(f"Installed codebase-wizard for {rt} ({target})")
        except RuntimeError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


@main.command()
@click.option("--for", "runtime", required=True,
              help="Target runtime: claude, opencode, all")
@click.option("--project", is_flag=True, default=False,
              help="Uninstall per-project install instead of global.")
def uninstall(runtime, project):
    """Uninstall the Codebase Wizard plugin."""
    converters = _get_converters()
    target = "project" if project else "global"
    runtimes = list(converters.keys()) if runtime == "all" else [runtime]
    for rt in runtimes:
        if rt not in converters:
            click.echo(f"Unsupported runtime: {rt}", err=True)
            sys.exit(1)
        installer = converters[rt]()
        installer.uninstall(target)
        click.echo(f"Uninstalled codebase-wizard for {rt} ({target})")


@main.command()
def status():
    """Show install status for all supported runtimes."""
    converters = _get_converters()
    for rt, cls in converters.items():
        installer = cls()
        info = installer.status()
        state = "installed" if info["installed"] else "not installed"
        loc = f" at {info['location']}" if info.get("location") else ""
        ver = f" (v{info['version']})" if info.get("version") else ""
        click.echo(f"{rt}: {state}{loc}{ver}")


@main.command()
def version():
    """Print the installed version."""
    click.echo(f"ai-codebase-mentor {__version__}")


if __name__ == "__main__":
    main()
