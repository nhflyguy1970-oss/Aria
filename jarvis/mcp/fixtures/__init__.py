"""Local fixture MCP providers.

Real MCP servers speaking the real protocol over stdio, so tests exercise the
actual client path rather than a mock of it — and without depending on any
external service, network or credential.
"""

from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent
DEMO_SERVER = FIXTURE_DIR / "demo_server.py"
CRASH_SERVER = FIXTURE_DIR / "crash_server.py"
MALFORMED_SERVER = FIXTURE_DIR / "malformed_server.py"

__all__ = ["CRASH_SERVER", "DEMO_SERVER", "FIXTURE_DIR", "MALFORMED_SERVER"]
