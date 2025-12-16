"""Minimal MCP filesystem server scoped to the course sandbox directory."""

from __future__ import annotations

from pathlib import Path
from typing import List

from mcp.server.fastmcp import FastMCP

BASE_DIR = Path(__file__).resolve().parent
SANDBOX_ROOT = (BASE_DIR / "sandbox").resolve()
SANDBOX_ROOT.mkdir(exist_ok=True)

mcp = FastMCP("sandbox_fs")


def _resolve(relative_path: str) -> Path:
    """Resolve the given path safely under SANDBOX_ROOT."""
    candidate = (SANDBOX_ROOT / Path(relative_path)).expanduser().resolve()
    if not str(candidate).startswith(str(SANDBOX_ROOT)):
        raise ValueError("Path must remain inside the sandbox directory.")
    return candidate


@mcp.tool()
async def read_text_file(path: str) -> str:
    """Read UTF-8 text from a sandbox file."""
    file_path = _resolve(path)
    return file_path.read_text(encoding="utf-8")


@mcp.tool()
async def write_text_file(path: str, content: str) -> str:
    """Write UTF-8 text to a sandbox file, creating parents if needed."""
    file_path = _resolve(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {file_path.relative_to(SANDBOX_ROOT)}"


@mcp.tool()
async def list_directory(path: str = ".") -> List[str]:
    """List files/directories under the given sandbox path."""
    target = _resolve(path)
    if not target.exists():
        raise FileNotFoundError(f"{path} does not exist inside the sandbox.")
    if target.is_file():
        return [target.relative_to(SANDBOX_ROOT).as_posix()]
    return sorted(child.relative_to(SANDBOX_ROOT).as_posix() for child in target.iterdir())


if __name__ == "__main__":
    mcp.run()













