from src.utils.db import get_database
from src.utils.redis_cache import get_cache, set_cache
from bson import json_util
import requests
import json

db = get_database()


async def get_index_stocks(ticker: str, period: str = "1W"):
    url = "https://api-python-v3.shipra.ca/index-get-performance"

    payload = json.dumps({"ticker": ticker, "period": period})

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching index performance: {e}")
        return None


async def fetch_index_stock_alerts_from_db():
    # Try cache first
    CACHE_KEY_ALERTS = f"alerts:active:index_stocks"
    cached_data = await get_cache(CACHE_KEY_ALERTS)
    if cached_data is not None:
        print("✅ Returning data from Redis cache")
        return json_util.loads(cached_data)

    # If not cached, query MongoDB

    pipeline = [
        # 1. Initial Filter
        {"$match": {"status": "ACTIVE", "alerCreateType": f"INDEX"}},
        # 2. Join with REG_USER_X_TICKER
        {
            "$lookup": {
                "from": "REG_USER_X_TICKER",
                "localField": "userXTickerId",
                "foreignField": "_id",
                "as": "user_ticker_info",
            }
        },
        {"$unwind": {"path": "$user_ticker_info", "preserveNullAndEmptyArrays": False}},
        # 3. Join with REG_TICKER
        {
            "$lookup": {
                "from": "REG_TICKER",
                "localField": "user_ticker_info.tickerId",
                "foreignField": "_id",
                "as": "ticker_info",
            }
        },
        {"$unwind": {"path": "$ticker_info", "preserveNullAndEmptyArrays": False}},
        # ✅ 4. Merge all fields from WP_TICKER_ALERT + joined data
        {
            "$replaceRoot": {
                "newRoot": {"$mergeObjects": ["$$ROOT", {"ticker": "$ticker_info"}]}
            }
        },
        # Optional: clean up temporary fields if you don't want nested structures
        {
            "$project": {
                "ticker_info": 0,  # remove the old ticker_info field
                "user_ticker_info": 0,  # remove joined helper doc if not needed
            }
        },
    ]

    # Execute the aggregation and fetch all results
    items_cursor = db.WP_TICKER_ALERT.aggregate(pipeline)
    items = await items_cursor.to_list(length=None)

    # 3️⃣ Cache the results
    await set_cache(
        CACHE_KEY_ALERTS, json_util.dumps(items), expire_seconds=900
    )  # cache for 5 mins

    return items


async def fetch_watchlist_alerts_from_db():
    CACHE_KEY_ALERTS = "alerts:active:watchlist"

    # Try to get data from cache first
    cached_data = await get_cache(CACHE_KEY_ALERTS)
    if cached_data is not None:
        print("✅ Returning data from Redis cache")
        return json_util.loads(cached_data)

    # Not cached — query MongoDB
    pipeline = [
        # 1. Match active watchlist alerts
        {"$match": {"status": "ACTIVE", "alerCreateType": "WATCHLIST"}},
        # 2. Join with REG_WATCH_X_TICKER
        {
            "$lookup": {
                "from": "REG_WATCH_X_TICKER",
                "localField": "watchlistId",
                "foreignField": "watchlistId",
                "as": "user_watchlist_info",
            }
        },
        {
            "$unwind": {
                "path": "$user_watchlist_info",
                "preserveNullAndEmptyArrays": False,
            }
        },
        # 3. Join with REG_TICKER
        {
            "$lookup": {
                "from": "REG_TICKER",
                "localField": "user_watchlist_info.tickerId",
                "foreignField": "_id",
                "as": "ticker_info",
            }
        },
        {"$unwind": {"path": "$ticker_info", "preserveNullAndEmptyArrays": False}},
        # 4. Merge all fields into a single document
        {
            "$replaceRoot": {
                "newRoot": {"$mergeObjects": ["$$ROOT", {"ticker": "$ticker_info"}]}
            }
        },
        # 5. Optionally remove helper fields
        {
            "$project": {
                "ticker_info": 0,
                "user_watchlist_info": 0,
            }
        },
    ]

    # Execute aggregation
    items_cursor = db.WP_TICKER_ALERT.aggregate(pipeline)
    items = await items_cursor.to_list(length=None)

    # Cache the results for 15 minutes
    await set_cache(
        CACHE_KEY_ALERTS, json_util.dumps(items), expire_seconds=900  # 15 minutes
    )

    return items


async def fetch_stock_alerts_from_db():
    # Try cache first
    CACHE_KEY_ALERTS = f"alerts:active:stocks"
    cached_data = await get_cache(CACHE_KEY_ALERTS)
    if cached_data is not None:
        print("✅ Returning data from Redis cache")
        return json_util.loads(cached_data)

    # If not cached, query MongoDB

    pipeline = [
        # 1. Initial Filter
        {"$match": {"status": "ACTIVE", "alerCreateType": f"STOCKS"}},
        # 2. Join with REG_USER_X_TICKER
        {
            "$lookup": {
                "from": "REG_USER_X_TICKER",
                "localField": "userXTickerId",
                "foreignField": "_id",
                "as": "user_ticker_info",
            }
        },
        {"$unwind": {"path": "$user_ticker_info", "preserveNullAndEmptyArrays": False}},
        # 3. Join with REG_TICKER
        {
            "$lookup": {
                "from": "REG_TICKER",
                "localField": "user_ticker_info.tickerId",
                "foreignField": "_id",
                "as": "ticker_info",
            }
        },
        {"$unwind": {"path": "$ticker_info", "preserveNullAndEmptyArrays": False}},
        # ✅ 4. Merge all fields from WP_TICKER_ALERT + joined data
        {
            "$replaceRoot": {
                "newRoot": {"$mergeObjects": ["$$ROOT", {"ticker": "$ticker_info"}]}
            }
        },
        # Optional: clean up temporary fields if you don't want nested structures
        {
            "$project": {
                "ticker_info": 0,  # remove the old ticker_info field
                "user_ticker_info": 0,  # remove joined helper doc if not needed
            }
        },
    ]

    # Execute the aggregation and fetch all results
    items_cursor = db.WP_TICKER_ALERT.aggregate(pipeline)
    items = await items_cursor.to_list(length=None)

    # 3️⃣ Cache the results
    await set_cache(
        CACHE_KEY_ALERTS, json_util.dumps(items), expire_seconds=900
    )  # cache for 5 mins

    return items
