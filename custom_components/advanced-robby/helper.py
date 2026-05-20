import base64
import logging
from datetime import datetime, timedelta

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

    # Python weekday: Monday=0 ... Sunday=6, convert to Sunday=0 ... Saturday=6
    current_day = (now.weekday() + 1) % 7

    start_of_week = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=current_day)

    for event in decoded:
        day_offset = event["day"]

        start_hour, start_minute = event["start"]
        end_hour, end_minute = event["end"]

        base_day = start_of_week + timedelta(days=day_offset)

        start_dt = base_day.replace(
            hour=start_hour,
            minute=start_minute,
            second=0,
            microsecond=0
        )

        end_dt = base_day.replace(
            hour=end_hour,
            minute=end_minute,
            second=0,
            microsecond=0
        )

        # Overnight event
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)

        # Move past events forward by whole weeks
        while end_dt < now:
            start_dt += timedelta(days=7)
            end_dt += timedelta(days=7)

        events.append(
            CalendarEvent(
                summary=f"Maaien",
                start=start_dt,
                end=end_dt
            )
        )

    events.sort(key=lambda x: x.start)

    return events
