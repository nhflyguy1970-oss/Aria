"""CLI shim — delegates to AI Platform or Aria standalone."""

from jarvis.workstation import main

if __name__ == "__main__":
    import sys

    sys.exit(main())
