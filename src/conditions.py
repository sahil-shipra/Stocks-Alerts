from src.alert_cache import get_alert_triggered, store_alert_triggered
from src.advance_condition import (
    check_from_today_open_price,
    check_from_yesterday_close_price,
    check_within_current_week,
    check_within_past_x_weeks,
    check_within_past_x_week_value,
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
    match key:
        case "fromTodayOpenPrice":
            if await get_alert_triggered(ticker, emailAddress):
                print(
                    f"✅ This alert has already been triggered: {ticker, emailAddress}"
                )
                return

            check_from_today_open_price(alert=alert, alertTriggered=alertTriggered)
            if len(alertTriggered) > 0:
                print(f"🚨 Alert Triggered: {alertTriggered}")
                await store_alert_triggered(
                    ticker,
                    emailAddress,
                    key=key,
                    alertTriggered=alertTriggered,
                )

        case "fromYesterdayClosePrice":
            check_from_yesterday_close_price(alert=alert, alertTriggered=alertTriggered)
        case "withinCurrentWeek":
            check_within_current_week(alert=alert, alertTriggered=alertTriggered)
        case "withinPastXWeek":
            check_within_past_x_weeks(alert=alert, alertTriggered=alertTriggered)
            # print(f"----> check_advance_condition for {key}")
        case "withinPastXWeekValue":
            check_within_past_x_week_value(alert=alert, alertTriggered=alertTriggered)
            print(f"----> check_advance_condition for {key}")
        case "fromRecentHighestPrice":
            print(f"----> check_advance_condition for {key}")
        case "withinPastXDays":
            print(f"----> check_advance_condition for {key}")
        case "withinPastXDaysValue":
            print(f"----> check_advance_condition for {key}")
        case "nearing52WeekLow":
            print(f"----> check_advance_condition for {key}")
        case "nearing52WeekHigh":
            print(f"----> check_advance_condition for {key}")
        case "nearingAllTimeHigh":
            print(f"----> check_advance_condition for {key}")
        case _:
            print(f"Unknown command: {key}.")


async def check_price_condition(alert: any):
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
