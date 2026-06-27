#!/usr/bin/env bash
# GUI sudo password prompt for ARIA System tab installs (SUDO_ASKPASS).
exec zenity --password --title="ARIA system install (sudo required)" 2>/dev/null \
  || exec kdialog --password "ARIA system install (sudo required)" 2>/dev/null
