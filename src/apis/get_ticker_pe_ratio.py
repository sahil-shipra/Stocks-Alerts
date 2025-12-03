import requests
from src.utils.redis_cache import set_cache, get_cache
from datetime import datetime, timedelta
import json


async def get_ticker_pe_ratio(ticker: str):
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    redis_key = f"pe_ratio:{ticker}:{today_str}"
    pe_ratio = await get_cache(redis_key)
    if pe_ratio:
        data = json.loads(pe_ratio)
        return data

    url = "https://api-python-v3.shipra.ca/ticker-pe-ratio"
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
