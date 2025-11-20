import json
from src.utils.redis_cache import get_redis
from datetime import datetime, timedelta


async def get_alert_triggered(ticker: str, emailAddress: str):
    redis_client = await get_redis()
    """Read stored alert from Redis for the current day."""

    today_str = datetime.now().strftime("%Y-%m-%d")
    redis_key = f"alert:triggered:{ticker}:{emailAddress}:{today_str}"

    # Retrieve the hash
    alert_data = await redis_client.hgetall(redis_key)
    if not alert_data:
        return None

    # (No decoding — client already returns strings)
    # Parse alertTriggered if JSON
    if "alertTriggered" in alert_data:
        try:
            alert_data["alertTriggered"] = json.loads(alert_data["alertTriggered"])
        except json.JSONDecodeError:
            pass

    return alert_data


async def store_alert_triggered(
    ticker: str, emailAddress: str, key: str, alertTriggered: any
):
    redis_client = await get_redis()
    """Store alert in Redis only for the current day (expires at midnight)."""
    if not alertTriggered:
        return

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    # Expire at midnight
    midnight = datetime.combine(now.date(), datetime.min.time()) + timedelta(days=1)
    seconds_until_midnight = int((midnight - now).total_seconds())

    # Create Redis key (unique per user + date)
    redis_key = f"alert:triggered:{ticker}:{emailAddress}:{today_str}"

    alert_data = {
        "ticker": str(ticker),
        "emailAddress": str(emailAddress),
        "key": str(key),
        "time": now.strftime("%H:%M:%S"),
        "date": today_str,
        "alertTriggered": json.dumps(alertTriggered),
    }

    # Store as hash
    await redis_client.hset(redis_key, mapping=alert_data)
    await redis_client.expire(redis_key, seconds_until_midnight)

    print(
        f"✅ Alert stored for {emailAddress}, expires in {seconds_until_midnight // 60} min."
    )
