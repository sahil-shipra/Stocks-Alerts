from src.utils.db import get_database
from src.utils.redis_cache import get_cache, set_cache
from bson import json_util
import json

db = get_database()
CACHE_KEY_ALERTS = "alerts:active:stocks"


async def fetch_alerts_from_db():
    # Try cache first
    cached_data = await get_cache(CACHE_KEY_ALERTS)
    if cached_data is not None:
        print("✅ Returning data from Redis cache")
        return json_util.loads(cached_data)

    # If not cached, query MongoDB

    pipeline = [
        # 1. Initial Filter
        {"$match": {"status": "ACTIVE", "alerCreateType": "STOCKS"}},
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
