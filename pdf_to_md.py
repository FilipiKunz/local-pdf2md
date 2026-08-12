#!/usr/bin/env python3
"""Run the local MinerU installation and expose only its final Markdown output."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit


PROJECT_DIR = Path(__file__).resolve().parent


def mineru_executable() -> Path | str | None:
    candidates = (
        Path.home() / ".venvs" / "local-pdf2md" / "bin" / "mineru",
        PROJECT_DIR / ".venv" / "bin" / "mineru",
        PROJECT_DIR / ".venv" / "Scripts" / "mineru.exe",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return shutil.which("mineru")


def accelerated_backend_available(mineru: Path | str) -> bool:
    """Return whether MinerU's Python environment can use CUDA or Apple MPS."""
    executable = Path(mineru)
    python = executable.with_name("python.exe" if executable.suffix == ".exe" else "python")
    if not python.is_file():
        python = Path(sys.executable)
    probe = (
        "import torch; "
        "cuda = torch.cuda.is_available(); "
        "mps = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(); "
        "print('yes' if cuda or mps else 'no')"
    )
    try:
        result = subprocess.run(
            [str(python), "-c", probe],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and result.stdout.strip() == "yes"


def choose_markdown(root: Path, input_stem: str) -> Path:
    markdown_files = list(root.rglob("*.md"))
    if not markdown_files:
        raise RuntimeError("MinerU completed but did not produce a Markdown file.")
    exact = [path for path in markdown_files if path.stem == input_stem]
    candidates = exact or markdown_files
    return max(candidates, key=lambda path: path.stat().st_size)


def collect_markdown(source_md: Path, output_md: Path) -> None:
    text = source_md.read_text(encoding="utf-8")
    assets_dir = output_md.parent / f"{output_md.stem}_assets"
    copied: dict[str, str] = {}

    def copy_target(target: str) -> str:
        stripped = target.strip("<>")
        parsed = urlsplit(stripped)
        if parsed.scheme or parsed.netloc or stripped.startswith(("#", "/")):
            return target
        relative = Path(unquote(parsed.path))
        source = (source_md.parent / relative).resolve()
        try:
            source.relative_to(source_md.parent.resolve())
        except ValueError:
            return target
        if not source.is_file():
            return target
        key = relative.as_posix()
        if key not in copied:
            destination = assets_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied[key] = f"{assets_dir.name}/{key}"
        replacement = copied[key]
        if parsed.query:
            replacement += f"?{parsed.query}"
        if parsed.fragment:
            replacement += f"#{parsed.fragment}"
        return f"<{replacement}>" if target.startswith("<") else replacement

    markdown_link = re.compile(r"(?P<open>!?\[[^\]]*\]\()(?P<target><[^>]+>|[^)\s]+)(?P<close>[^)]*\))")
    text = markdown_link.sub(
        lambda match: match.group("open")
        + copy_target(match.group("target"))
        + match.group("close"),
        text,
    )
    html_link = re.compile(r'(?P<open>\b(?:src|href)\s*=\s*["\'])(?P<target>[^"\']+)(?P<close>["\'])', re.I)
    text = html_link.sub(
        lambda match: match.group("open")
        + copy_target(match.group("target"))
        + match.group("close"),
        text,
    )

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a PDF to Markdown locally with MinerU.")
    parser.add_argument("input_pdf", type=Path, help="PDF to convert")
    parser.add_argument("output_md", type=Path, nargs="?", help="optional output Markdown path")
    args = parser.parse_args()

    input_pdf = args.input_pdf.expanduser().resolve()
    if not input_pdf.is_file():
        parser.error(f"PDF does not exist: {input_pdf}")
    if input_pdf.suffix.lower() != ".pdf":
        parser.error(f"Input must be a PDF file: {input_pdf}")

    output_md = (args.output_md or input_pdf.with_suffix(".md")).expanduser().resolve()
    if output_md.suffix.lower() != ".md":
        parser.error(f"Output path must end in .md: {output_md}")
    if output_md == input_pdf:
        parser.error("Input and output paths must be different.")

    mineru = mineru_executable()
    if mineru is None:
        print("Error: MinerU is unavailable. Run ./install.sh as described in README.md.", file=sys.stderr)
        return 2

    backend = "hybrid-engine" if accelerated_backend_available(mineru) else "pipeline"

    try:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".mineru-", dir=output_md.parent) as temp:
            result = subprocess.run(
                [str(mineru), "-p", str(input_pdf), "-o", temp, "-b", backend],
                text=True,
            )
            if result.returncode:
                raise RuntimeError(f"MinerU exited with status {result.returncode}.")
            collect_markdown(choose_markdown(Path(temp), input_pdf.stem), output_md)
    except (OSError, RuntimeError, UnicodeError) as error:
        print(f"Error: conversion failed: {error}", file=sys.stderr)
        return 1

    print(output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
