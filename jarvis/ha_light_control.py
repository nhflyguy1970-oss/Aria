# Source Generated with Decompyle++
# File: ha_light_control.cpython-312.pyc (Python 3.12)

__doc__ = 'Home Assistant light color, brightness, and daylight helpers.'
from __future__ import annotations
import colorsys
import math
import re
from datetime import datetime, timezone
from typing import Any
ASTRONOMICAL_TWILIGHT_ELEV = -18
NAUTICAL_TWILIGHT_ELEV = -12
NIGHT_OFF_ELEV = NAUTICAL_TWILIGHT_ELEV
CIVIL_SUNRISE_ELEV = 0
# WARNING: Decompyle incomplete
