# Example usage
import asyncio
from src.alert_cache import store_alert


async def main():
    alert = {"emailAddress": "user@example.com"}
    await store_alert(
        alert["emailAddress"], key="fromTodayOpenPrice", alertTriggered=True
    )


asyncio.run(main())
