from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from ipykernel.kernelspec import install

KERNEL_NAME = "2026coplac"
DISPLAY_NAME = "Python (2026coplac)"


def kernel_dir() -> Path:
    if sys.platform.startswith("win"):
        return Path.home() / "AppData" / "Roaming" / "jupyter" / "kernels" / KERNEL_NAME
    return Path.home() / ".local" / "share" / "jupyter" / "kernels" / KERNEL_NAME


def conda_path_entries(prefix: Path) -> list[str]:
    if sys.platform.startswith("win"):
        return [
            str(prefix),
            str(prefix / "Library" / "mingw-w64" / "bin"),
            str(prefix / "Library" / "usr" / "bin"),
            str(prefix / "Library" / "bin"),
            str(prefix / "Scripts"),
        ]
    return [str(prefix / "bin"), str(prefix / "lib")]


def main() -> None:
    destino = install(user=True, kernel_name=KERNEL_NAME, display_name=DISPLAY_NAME)

    prefix = Path(sys.prefix).resolve()
    # Usar la ruta real que devuelve ipykernel (en Linux y macOS el nombre queda en minúsculas)
    kernel_json = Path(destino) / "kernel.json"
    spec = json.loads(kernel_json.read_text(encoding="utf-8"))

    spec["argv"] = [
        sys.executable,
        "-Xfrozen_modules=off",
        "-m",
        "ipykernel_launcher",
        "-f",
        "{connection_file}",
    ]

    env = spec.setdefault("env", {})
    separator = ";" if sys.platform.startswith("win") else ":"
    env["PATH"] = separator.join(conda_path_entries(prefix))
    env["CONDA_PREFIX"] = str(prefix)
    env["MPLBACKEND"] = "module://matplotlib_inline.backend_inline"
    env["PYTHONIOENCODING"] = "utf-8"

    if not sys.platform.startswith("win"):
        env["LD_LIBRARY_PATH"] = str(prefix / "lib")

    kernel_json.write_text(json.dumps(spec, indent=1), encoding="utf-8")

    print(f"Kernel '{KERNEL_NAME}' installed at {kernel_json}")
    print("Kernel launch mode: direct python with Conda PATH")
    print("Matplotlib backend for this kernel: inline")


if __name__ == "__main__":
    main()
