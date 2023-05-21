import os

import requests

from utils import get_stop_pair, get_zone_date_length

SLOW_ZONE_BOT_SLACK_WEBHOOK_URL = os.environ.get("SLOW_ZONE_BOT_SLACK_WEBHOOK_URL")

def attachment(zone, new):
    output = {}

    if new:
        title = "⚠️ New Slow Zone ⚠️"
        output["color"] = "danger"
    else:
        title = "✅ Fixed Slow Zone 🎉"
        output["color"] = "good"

    output["text"] = title
    output["title"] = title
    output["fields"] = fields(zone, new)

    return output

def fields(zone, new):
    output = {}

    output["stop_pair"] = {
        "title": "Stop Pair",
        "value": get_stop_pair(zone)
    }

    if not new:
        output["age"] = {
            "title": "🗓️",
            "value": str(get_zone_date_length(zone)) + " days ",
            "short": True
        }

    output["delay"] = {
        "title": "⏳",
        "value": str(round(zone["delay"], 1)) + "s",
        "short": True
    }
    output["delay_ratio"] = {
        "title": "⬆️",
        "value": str(round(zone["delay"] / zone["baseline"] * 100, 2)) + "%",
        "short": True
    }

    return output

def send_slow_zone_slack(lines, new):
    attachments = []

    for line in lines:
        for zone in line:
            attachments += attachment(zone, new)

    requests.post(
        SLOW_ZONE_BOT_SLACK_WEBHOOK_URL,
        json={
            "attachments": attachments,
        },
    )
