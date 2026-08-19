"""A fixture that speaks nonsense instead of MCP, to prove protocol errors are handled."""

from __future__ import annotations

import sys

sys.stdout.write("this is not JSON-RPC\n")
sys.stdout.flush()
for _ in sys.stdin:
    sys.stdout.write("{still not valid mcp}\n")
    sys.stdout.flush()
