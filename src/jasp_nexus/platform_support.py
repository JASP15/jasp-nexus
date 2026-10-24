"""Host diagnostics only: WSL and macOS run CAO; Windows native requires WSL."""
import os
import platform


def describe_host(system: str, release: str = "", wsl_distro: str = "") -> tuple[str, bool]:
    """Return a human-readable host label and whether CAO can run locally on it.

    This is an OS capability check, not a guarantee that CAO is installed.
    """
    if system == "Darwin":
        return "macOS (native)", True
    if system == "Linux":
        if wsl_distro or "microsoft" in release.lower() or "wsl" in release.lower():
            return "Windows + WSL (Linux environment)", True
        return "Linux (native)", True
    if system == "Windows":
        return "Windows (native; CAO requires WSL2)", False
    return f"{system} (not validated)", False


def current_host() -> tuple[str, bool]:
    return describe_host(
        platform.system(),
        platform.release(),
        os.environ.get("WSL_DISTRO_NAME", ""),
    )
