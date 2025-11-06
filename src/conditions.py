from src.advance_condition.check_from_today_open_price import (
    check_from_today_open_price,
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


async def check_advance_condition(key: str, item: any):
    alertTriggered = []
    match key:
        case "fromTodayOpenPrice":
            print(item["emailAddress"])
            check_from_today_open_price(
                ticker=item["ticker"]["ticker"],
                currentPrice=item.get("addedPriceAt") or 0,
                alert=item,
                alertTriggered=alertTriggered,
                alertTitleTickerFullName=item["ticker"]["nm"],
                alertMessageTickerFullName=item["ticker"]["nm"],
            )
            if len(alertTriggered) > 0:
                print(f"🚨 alertTriggered: {alertTriggered}")

        case "fromYesterdayClosePrice":
            print(f"----> check_advance_condition for {key}")
        case "withinCurrentWeek":
            print(f"----> check_advance_condition for {key}")
        case "withinPastXWeek":
            print(f"----> check_advance_condition for {key}")
        case "withinPastXWeekValue":
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


async def check_price_condition(item: any):
    advance_condition = item["priceAdvanceCondition"]

    # Check if subCondition is GOING_UP or GOING_DOWN
    if item["subCondition"] in ("GOING_UP", "GOING_DOWN"):
        # Collect all keys from GOING_UP_DOWN that are True
        true_conditions = [
            key for key in GOING_UP_DOWN if advance_condition.get(key) is True
        ]

        # Print results
        if true_conditions:
            for key in true_conditions:
                await check_advance_condition(key, item)
        else:
            print("-----> No True conditions found.")
