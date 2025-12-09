from src.alert_trigger import run_alert_trigger
from src.alert_cache import get_alert_triggered
from src.advance_condition import (
    check_from_today_open_price,
    check_from_yesterday_close_price,
    check_within_current_week,
    check_within_past_x_weeks,
    check_within_past_x_week_value,
    check_within_from_recent_highest_price,
)


GOING_UP_DOWN = [
    "fromTodayOpenPrice",
    "fromYesterdayClosePrice",
    "withinCurrentWeek",
    "withinPastXWeek",
    "withinPastXWeekValue",
    "fromRecentHighestPrice",
    "withinPastXDays",
    "withinPastXDaysValue",
    "nearing52WeekLow",
    "nearing52WeekHigh",
    "nearingAllTimeHigh",
]


async def check_advance_condition(key: str, alert: any):
    alertTriggered = []
    ticker = alert.get("tickerNm") or alert["ticker"]["ticker"]
    emailAddress = alert["emailAddress"][0]

    # 🔹 Cases that should NOT run get_alert_triggered() first
    skip_trigger_check = {
        "withinPastXWeek",
        "withinPastXWeekValue",
        "fromRecentHighestPrice",
        "withinPastXDays",
        "withinPastXDaysValue",
        "nearing52WeekLow",
        "nearing52WeekHigh",
        "nearingAllTimeHigh",
    }

    # 🔹 Map keys → handler functions
    handlers = {
        "fromTodayOpenPrice": lambda: check_from_today_open_price(
            alert, alertTriggered
        ),
        "fromYesterdayClosePrice": lambda: check_from_yesterday_close_price(
            alert, alertTriggered
        ),
        "withinCurrentWeek": lambda: check_within_current_week(alert, alertTriggered),
        "withinPastXWeek": lambda: check_within_past_x_weeks(alert, alertTriggered),
        "withinPastXWeekValue": lambda: check_within_past_x_week_value(
            alert, alertTriggered
        ),
        "fromRecentHighestPrice": lambda: check_within_from_recent_highest_price(
            alert=alert, alertTriggered=alertTriggered
        ),
    }

    # 🔹 Keys that only log for now
    log_only = {
        "withinPastXDays",
        "withinPastXDaysValue",
        "nearing52WeekLow",
        "nearing52WeekHigh",
        "nearingAllTimeHigh",
    }

    # ---------- Handle log-only cases ----------
    if key in log_only:
        # print(f"----> check_advance_condition for {key}")
        return

    # ---------- Unknown command ----------
    if key not in handlers:
        print(f"Unknown command: {key}.")
        return

    # ---------- Check if alert has already been triggered ----------
    if key not in skip_trigger_check:
        if await get_alert_triggered(ticker, emailAddress, key):
            print(
                f"✅ This alert has already been triggered: {key, ticker, emailAddress}"
            )
            return

    # ---------- Run the actual condition handler ----------
    handler = handlers[key]
    result = handler()

    # Some handlers are async (e.g., fromRecentHighestPrice)
    if hasattr(result, "__await__"):
        await result

    # ---------- Execute alert trigger ----------
    await run_alert_trigger(alert, alertTriggered, key)


async def check_price_conditions(alert: any):
    advance_condition = alert["priceAdvanceCondition"]

    # Check if subCondition is GOING_UP or GOING_DOWN
    if alert["subCondition"] in ("GOING_UP", "GOING_DOWN"):
        # Collect all keys from GOING_UP_DOWN that are True
        true_conditions = [
            key for key in GOING_UP_DOWN if advance_condition.get(key) is True
        ]

        # Print results
        if true_conditions:
            for key in true_conditions:
                await check_advance_condition(key, alert)
        else:
            print("-----> No True conditions found.")
