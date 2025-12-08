from datetime import datetime
from dotenv import load_dotenv
import os
import requests
from src.alert_cache import store_alert_triggered


def send_alert_notification(alert, alert_triggered_list):
    """
    Send triggered alerts to the notification service.

    Args:
        alert (dict): Alert configuration containing id, userXTickerId, and frequency
        alert_triggered_list (list): List of triggered alert objects
        node_auth_token (str): Authentication token for the API

    Returns:
        bool: True if successful, False otherwise
    """
    if not alert_triggered_list:
        return False

    auth_token = os.getenv("NODE_AUTH_TOKEN")

    if not auth_token:
        return False

    # Clean alert messages
    for trigger in alert_triggered_list:
        if msg := trigger.get("alertMessage"):
            trigger["alertMessage"] = msg.replace("\n", " ")

    # Prepare request payload
    payload = {
        "alertId": str(alert["_id"]), #6903290431fe6a59be5a4894
        "alertList": alert_triggered_list,
        "userXTickerId": str(alert["userXTickerId"]),
        "frequency": alert["frequency"],
        "date": datetime.now().strftime("%m-%d-%Y"),
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}",
    }

    # Send notification
    try:
        print(f"payload:{payload}")
        response = requests.post(
            "https://api-shipra-v3.pilleo.ca/admin/alert/send",
            json=payload,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.Timeout:
        print(f"Alert notification timeout for alertId: {alert['_id']}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Failed to send alert notification for alertId: {alert['_id']} - {e}")
        return False


async def run_alert_trigger(alert, alertTriggered, key):
    if len(alertTriggered) > 0:
        ticker = alert.get("tickerNm") or alert["ticker"]["ticker"]
        emailAddress = alert["emailAddress"][0]
        print(f"{alert}")
        print(f"alertTriggered:{alertTriggered}")
        print(f"🚨 Alert Triggered: {alertTriggered}")
        send_alert_notification(alert, alertTriggered)
        await store_alert_triggered(
            ticker,
            emailAddress,
            key=key,
            alertTriggered=alertTriggered,
        )
    return
