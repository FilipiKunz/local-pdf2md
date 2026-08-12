#!/usr/bin/env python3
"""Verify the local MinerU environment without downloading or parsing a PDF."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pdf_to_md import accelerated_backend_available, mineru_executable


def main() -> int:
    mineru = mineru_executable()
    if mineru is None:
        print("MinerU: unavailable")
        print("Run ./install.sh to install the required environment.")
        return 1

    version = subprocess.run(
        [str(mineru), "--version"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if version.returncode != 0:
        print("MinerU: installed but its CLI failed to start")
        print(version.stderr.strip())
        return 1

    executable = Path(mineru)
    python = executable.with_name("python.exe" if executable.suffix == ".exe" else "python")
    probe = subprocess.run(
        [
            str(python),
            "-c",
            "import json, torch; print(json.dumps({"
            "'torch': torch.__version__, "
            "'cuda': torch.cuda.is_available(), "
            "'cuda_device': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None, "
            "'mps': hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()}))",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if probe.returncode != 0:
        print("MinerU: installed")
        print("PyTorch: failed to load")
        print(probe.stderr.strip())
        return 1

    device = json.loads(probe.stdout)
    print(version.stdout.strip())
    print(f"PyTorch: {device['torch']}")
    if device["cuda"]:
        print(f"Acceleration: CUDA ({device['cuda_device']})")
    elif device["mps"]:
        print("Acceleration: Apple MPS")
    else:
        print("Acceleration: none; MinerU will use its CPU pipeline")
    print(
        "Backend: hybrid-engine"
        if accelerated_backend_available(mineru)
        else "Backend: pipeline"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
