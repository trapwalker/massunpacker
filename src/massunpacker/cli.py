"""Command-line interface for massunpacker."""

import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn

from .collision import CollisionMethod
from .extractor import Extractor, ExtractionResult
from .i18n import _, setup_i18n
from .utils import ensure_directory, get_sorted_zip_files

app = typer.Typer(help="Mass unpack utility for zip archives")
console = Console()
err_console = Console(stderr=True)


def setup_logging(verbose: bool = False) -> None:
    """
    Setup logging with rich handler.

    Args:
        verbose: Enable debug logging
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Setup root logger with RichHandler for colored output
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[
            RichHandler(
                console=console,
                show_time=False,
                show_path=False,
                markup=True,
                rich_tracebacks=True,
            )
        ],
    )

    # Separate handler for errors to stderr
    error_handler = RichHandler(
        console=err_console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )
    error_handler.setLevel(logging.WARNING)
    logging.getLogger().addHandler(error_handler)


def print_summary(result: ExtractionResult) -> None:
    """
    Print extraction summary to stdout.

    Args:
        result: Extraction result
    """
    compression_ratio = (
        (1 - result.size_compressed / result.size_uncompressed) * 100
        if result.size_uncompressed > 0
        else 0
    )

    console.print(
        f"[bold]{result.archive_path.name}[/bold]: "
        f"{result.files_extracted} extracted, "
        f"{result.files_skipped} skipped, "
        f"{result.files_renamed} renamed | "
        f"{result.size_compressed // 1024} KB → {result.size_uncompressed // 1024} KB "
        f"({compression_ratio:.1f}% compression)"
    )

    # Print collisions to stderr
    if result.collisions:
        for original, new_name in result.collisions:
            err_console.print(
                f"[yellow]Collision[/yellow] in {result.archive_path.name}: {original} → {new_name}",
                style="yellow",
            )

    # Print errors to stderr
    if result.errors:
        for error in result.errors:
            err_console.print(f"[red]Error[/red] in {result.archive_path.name}: {error}", style="red")


@app.command()
def main(
    patterns: list[str] = typer.Argument(..., help="Glob pattern(s) or zip file(s) (e.g., 'data/*.zip' or file1.zip file2.zip)"),
    extract_to: Optional[Path] = typer.Option(
        None, "--extract-to", "-o", help="Output directory (default: current directory)"
    ),
    count: Optional[int] = typer.Option(None, "--count", "-n", help="Limit number of archives to process"),
    mv_ok: Optional[Path] = typer.Option(
        None, "--mv-ok", help="Move successful archives here (default: ./OK)"
    ),
    mv_er: Optional[Path] = typer.Option(
        None, "--mv-er", help="Move failed archives here (default: ./ERR)"
    ),
    collision_method: CollisionMethod = typer.Option(
        CollisionMethod.HASH_FAST,
        "--collision",
        "-c",
        help="Method for collision detection: size, hash-sha256, hash-fast",
    ),
    no_progress: bool = typer.Option(False, "--no-progress", help="Disable progress bar"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """
    Extract multiple zip archives to a single directory with collision handling.

    Examples:
        massunpacker "data/*.zip" --extract-to=output
        massunpacker *.zip --count=10
        massunpacker file1.zip file2.zip file3.zip
    """
    setup_i18n()
    setup_logging(verbose)

    # Set defaults for output directories
    if extract_to is None:
        extract_to = Path.cwd()
    if mv_ok is None:
        mv_ok = Path.cwd() / "OK"
    if mv_er is None:
        mv_er = Path.cwd() / "ERR"

    try:
        # Ensure directories exist
        ensure_directory(extract_to, "extraction directory")
        ensure_directory(mv_ok, "OK directory")
        ensure_directory(mv_er, "ERR directory")

        # Get list of archives
        archives = get_sorted_zip_files(patterns, limit=count)

        if not archives:
            err_console.print(f"[red]No zip files found matching patterns: {', '.join(patterns)}[/red]")
            raise typer.Exit(code=1)

        console.print(f"Found {len(archives)} archive(s) to process")

        # Create extractor
        extractor = Extractor(output_dir=extract_to, collision_method=collision_method)

        # Process archives
        total_extracted = 0
        total_skipped = 0
        total_renamed = 0
        total_errors = 0

        if no_progress or not sys.stdout.isatty():
            # Simple output without progress bar
            for i, archive in enumerate(archives, 1):
                console.print(f"[{i}/{len(archives)}] Processing {archive.name}...")
                result = extractor.extract_archive(archive)
                print_summary(result)

                total_extracted += result.files_extracted
                total_skipped += result.files_skipped
                total_renamed += result.files_renamed
                total_errors += len(result.errors)

                # Move archive
                if result.success and not result.errors:
                    archive.rename(mv_ok / archive.name)
                else:
                    archive.rename(mv_er / archive.name)
        else:
            # With progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Extracting archives...", total=len(archives))

                for archive in archives:
                    progress.update(task, description=f"Processing {archive.name}")
                    result = extractor.extract_archive(archive)
                    print_summary(result)

                    total_extracted += result.files_extracted
                    total_skipped += result.files_skipped
                    total_renamed += result.files_renamed
                    total_errors += len(result.errors)

                    # Move archive
                    if result.success and not result.errors:
                        archive.rename(mv_ok / archive.name)
                    else:
                        archive.rename(mv_er / archive.name)

                    progress.advance(task)

        # Print final summary
        console.print("\n[bold green]Processing complete![/bold green]")
        console.print(
            f"Total: {total_extracted} extracted, {total_skipped} skipped, "
            f"{total_renamed} renamed, {total_errors} errors"
        )

    except KeyboardInterrupt:
        err_console.print("\n[red]Operation interrupted by user (Ctrl-C)[/red]")
        raise typer.Exit(code=130)
    except Exception as e:
        err_console.print(f"[red]Fatal error: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
