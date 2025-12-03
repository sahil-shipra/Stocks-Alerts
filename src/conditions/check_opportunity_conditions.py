import numpy as np

from datetime import datetime
from src.apis.get_ticker_closing_price import get_ticker_closing_price


async def check_opportunity_conditions(alert):
    ticker = alert["tickerNm"]
    data = await get_ticker_closing_price(ticker)
    stock_data = [{"date": d["time"], "close": d["value"]} for d in data]
    lastCloseDate = datetime.strptime(stock_data[-1]["date"], "%Y-%m-%d").date()
    todayDate = datetime.today().date()
    alertTriggered = []

    if alert["condition"] == "OPPORTUNITY" and lastCloseDate == todayDate:
        opportunity = alert["opportunity"]

        # Use numpy for faster calculations
        closes = np.array([item["close"] for item in stock_data])

        # Calculate running maximum and current metrics
        running_max = np.maximum.accumulate(closes)
        peak_price = running_max[-1]
        current_price = closes[-1]

        # Calculate missed opportunity in one step
        missed_opportunity = ((peak_price - current_price) / current_price) * 100

        # Simplified condition checking
        sub_condition = alert["subCondition"]
        should_alert = (
            sub_condition == "GOING_UP" and missed_opportunity > opportunity
        ) or (sub_condition == "GOING_DOWN" and missed_opportunity < opportunity)

        if should_alert:
            alertTriggered.append(
                {
                    "subCondition": sub_condition,
                    "condition": alert["condition"],
                    "advanceCondition": "",
                }
            )
