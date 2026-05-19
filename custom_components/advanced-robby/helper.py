import base64
import logging
from datetime import timedelta

from homeassistant.components.calendar import CalendarEvent
from homeassistant.util import dt as dt_util


_LOGGER = logging.getLogger(__name__)


# =========================================================
# Decode schedule blob
# =========================================================
def decode_schedule(payload: str):
    try:
        raw = base64.b64decode(payload)
    except Exception as e:
        _LOGGER.error("Decode error: %s", e)
        return []

    events = []

    for i in range(0, len(raw), 5):
        chunk = raw[i:i + 5]
        if len(chunk) < 5:
            continue

        day, sh, sm, eh, em = chunk

        if sh == 0x88 or sh == 0x00:
            continue

        events.append({
            "day": day,
            "start": (sh, sm),
            "end": (eh, em),
        })

    return events

# -----------------------------------------------------
# Build weekly events
# -----------------------------------------------------
def build_week(decoded):
    now = dt_util.now()
    events = []

    for e in decoded:
        day = (e["day"] + 6) % 7

        days_ahead = (day - now.weekday()) % 7
        base = now + timedelta(days=days_ahead)

        sh, sm = e["start"]
        eh, em = e["end"]

        start = base.replace(hour=sh, minute=sm, second=0, microsecond=0)
        end = base.replace(hour=eh, minute=em, second=0, microsecond=0)

        events.append(
            CalendarEvent(
                summary=f"Maaien",
                start=start,
                end=end,
            )
        )

    return events
