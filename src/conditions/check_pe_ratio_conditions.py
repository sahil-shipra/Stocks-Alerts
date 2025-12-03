from datetime import datetime, timedelta
from src.apis.get_ticker_pe_ratio import get_ticker_pe_ratio


def filter_pe_by_days(pe_list, days):
    threshold_date = datetime.now() - timedelta(days=days)
    return [
        item
        for item in pe_list
        if datetime.strptime(item["time"], "%Y-%m-%d") >= threshold_date
    ]


def pe_in_range(current, low, high):
    return low <= current <= high


def check_trend(pe_list, days, increasing=True):
    filtered = filter_pe_by_days(pe_list, days)
    if len(filtered) < days - 1:
        return False, 0, 0, 0
    first, last = filtered[0]["value"], filtered[-1]["value"]
    change_pct = ((last - first) / first) * 100
    is_trending = all(
        (
            filtered[i]["value"] <= filtered[i + 1]["value"]
            if increasing
            else filtered[i]["value"] >= filtered[i + 1]["value"]
        )
        for i in range(len(filtered) - 1)
    )
    return is_trending, first, last, change_pct


def find_extreme(pe_list, years=None, highest=True):
    if years:
        cutoff = datetime.now() - timedelta(days=years * 365)
        pe_list = [
            item
            for item in pe_list
            if datetime.strptime(item["time"], "%Y-%m-%d") >= cutoff
        ]
    if not pe_list:
        return None
    extreme_obj = (
        max(pe_list, key=lambda x: x["value"])
        if highest
        else min(pe_list, key=lambda x: x["value"])
    )
    return extreme_obj


async def check_pe_ratio_conditions(alert):
    alerts = []

    if alert is None:
        return

    conds = alert["peRatioAdvanceCondition"]
    alertTitleTickerFullName = alert["tickerNm"]
    alertMessageTickerFullName = alert["tickerNm"]

    pe_list = await get_ticker_pe_ratio("GOOGL")
    currentPe = pe_list[-1]["value"]

    # PE Less Than X
    if conds.get("peRatioLessThanX") and currentPe < conds["peRatioLessThanXValue"]:
        alerts.append(
            {
                "advanceCondition": "peRatioLessThanX",
                "condition": alert["condition"],
                "subCondition": "",
                "alertTitle": f"{alertTitleTickerFullName} PE Ratio Going Down",
                "alertMessage": f'{alertMessageTickerFullName} The PE ratio has dropped to {round(currentPe,2)}, below your threshold of {conds["peRatioLessThanXValue"]}',
            }
        )

    # PE Greater Than X
    if (
        conds.get("peRatioGreaterThanX")
        and currentPe > conds["peRatioGreaterThanXValue"]
    ):
        alerts.append(
            {
                "advanceCondition": "peRatioGreaterThanX",
                "condition": alert["condition"],
                "subCondition": "",
                "alertTitle": f"{alertTitleTickerFullName} PE Ratio Going Up",
                "alertMessage": f'{alertMessageTickerFullName} The PE ratio has risen to {round(currentPe,2)}, above your threshold of {conds["peRatioGreaterThanXValue"]}',
            }
        )

    # PE in Specific Range
    if conds.get("peRatioSpecificRange"):
        if pe_in_range(currentPe, conds["lowRange"], conds["highRange"]):
            alerts.append(
                {
                    "advanceCondition": "peRatioSpecificRange",
                    "condition": alert["condition"],
                    "subCondition": "",
                    "alertTitle": f"{alertTitleTickerFullName} PE Ratio in Range",
                    "alertMessage": f'{alertMessageTickerFullName} The PE ratio is now {round(currentPe,2)}, within your range {conds["lowRange"]}-{conds["highRange"]}',
                }
            )

    # Near X-year Low
    if conds.get("peRatioNearXYearLow"):
        low_obj = find_extreme(pe_list, conds["peRatioNearXYearLowYear"], highest=False)
        if low_obj:
            lower, upper = low_obj["value"] * (
                1 - conds["peRatioNearXYearLowValue"] / 100
            ), low_obj["value"] * (1 + conds["peRatioNearXYearLowValue"] / 100)
            if pe_in_range(currentPe, lower, upper):
                alerts.append(
                    {
                        "advanceCondition": "peRatioNearXYearLow",
                        "condition": alert["condition"],
                        "subCondition": "",
                        "alertTitle": f'{alertTitleTickerFullName} PE Ratio is Near {conds["peRatioNearXYearLowYear"]}-Year Low',
                        "alertMessage": f'{alertMessageTickerFullName} The PE ratio is {round(currentPe,2)}, within {conds["peRatioNearXYearLowValue"]}% of the {conds["peRatioNearXYearLowYear"]}-year low of {low_obj["value"]}',
                    }
                )

    # Near X-year High
    if conds.get("peRatioNearXYearHigh"):
        high_obj = find_extreme(
            pe_list, conds["peRatioNearXYearHighYear"], highest=True
        )
        if high_obj:
            lower, upper = high_obj["value"] * (
                1 - conds["peRatioNearXYearHighValue"] / 100
            ), high_obj["value"] * (1 + conds["peRatioNearXYearHighValue"] / 100)
            if pe_in_range(currentPe, lower, upper):
                alerts.append(
                    {
                        "advanceCondition": "peRatioNearXYearHigh",
                        "condition": alert["condition"],
                        "subCondition": "",
                        "alertTitle": f'{alertTitleTickerFullName} PE Ratio is Near {conds["peRatioNearXYearHighYear"]}-Year High',
                        "alertMessage": f'{alertMessageTickerFullName} The PE ratio is {round(currentPe,2)}, within {conds["peRatioNearXYearHighValue"]}% of the {conds["peRatioNearXYearHighYear"]}-year high of {high_obj["value"]}',
                    }
                )

    # Historical Extreme
    if conds.get("peRatioHistoricalExtreme"):
        extreme_obj = find_extreme(pe_list, highest=True)
        if extreme_obj and currentPe >= extreme_obj["value"]:
            alerts.append(
                {
                    "advanceCondition": "peRatioHistoricalExtreme",
                    "condition": alert["condition"],
                    "subCondition": "",
                    "alertTitle": f"{alertTitleTickerFullName} PE ratio is at a historical extreme!",
                    "alertMessage": f"{alertMessageTickerFullName} The PE ratio has reached {round(currentPe,2)}, surpassing previous historical levels.",
                }
            )

    # Trending Up
    if conds.get("peRatioTrendingUp"):
        trending, first, last, change = check_trend(
            pe_list, conds["peRatioTrendingUpValue"], increasing=True
        )
        if trending:
            alerts.append(
                {
                    "advanceCondition": "peRatioTrendingUp",
                    "condition": alert["condition"],
                    "subCondition": "",
                    "alertTitle": f"{alertTitleTickerFullName} PE ratio is Trending Up",
                    "alertMessage": f'{alertMessageTickerFullName} PE ratio increased {round(change,2)}% from {first} to {last} over past {conds["peRatioTrendingUpValue"]} days.',
                }
            )

    # Trending Down
    if conds.get("peRatioTrendingDown"):
        trending, first, last, change = check_trend(
            pe_list, conds["peRatioTrendingDownValue"], increasing=False
        )
        if trending:
            alerts.append(
                {
                    "advanceCondition": "peRatioTrendingDown",
                    "condition": alert["condition"],
                    "subCondition": "",
                    "alertTitle": f"{alertTitleTickerFullName} PE ratio is Trending Down",
                    "alertMessage": f'{alertMessageTickerFullName} PE ratio decreased {round(change,2)}% from {first} to {last} over past {conds["peRatioTrendingDownValue"]} days.',
                }
            )

    return alerts
