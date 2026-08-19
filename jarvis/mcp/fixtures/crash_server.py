"""A fixture MCP server that dies during the handshake."""

from __future__ import annotations

import os
import sys

sys.stderr.write("fixture: exiting before initialize\n")
sys.stderr.flush()
os._exit(3)
