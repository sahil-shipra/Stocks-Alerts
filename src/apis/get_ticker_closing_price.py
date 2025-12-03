import requests
from src.utils.redis_cache import set_cache, get_cache
from datetime import datetime, timedelta
import json


async def get_ticker_closing_price(ticker: str):
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    redis_key = f"closing_price:{ticker}:{today_str}"
    closing_price = await get_cache(redis_key)
    if closing_price:
        data = json.loads(closing_price)
        return data

    url = "https://api-python-v3.shipra.ca/ticker-closing-price"
    payload = {"ticker": ticker}

    response = requests.post(url, json=payload)

    if response.ok:
        # Expire at midnight

        midnight = datetime.combine(now.date(), datetime.min.time()) + timedelta(days=1)
        seconds_until_midnight = int((midnight - now).total_seconds())

        await set_cache(
            redis_key,
            json.dumps(response.json()),
            expire_seconds=seconds_until_midnight,
        )

        data = response.json()
        return data

    raise RuntimeError(f"Request failed [{response.status_code}]: {response.text}")
