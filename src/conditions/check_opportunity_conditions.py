import asyncio
import numpy as np

from datetime import datetime
from src.alert_cache import get_alert_triggered
from src.alert_trigger import run_alert_trigger
from src.apis.get_ticker_closing_price import get_ticker_closing_price


async def check_opportunity_conditions(alert):
    ticker = alert["tickerNm"]
    sub_condition = alert["subCondition"]
    emailAddress = alert["emailAddress"][0]

    if await get_alert_triggered(ticker, emailAddress, key=sub_condition):
        return

    data = await get_ticker_closing_price(ticker)
    stock_data = [{"date": d["time"], "close": d["value"]} for d in data]
    lastCloseDate = datetime.strptime(stock_data[-1]["date"], "%Y-%m-%d").date()
    todayDate = datetime.today().date()
    alertTriggered = []

    if alert["condition"] == "OPPORTUNITY":  # and lastCloseDate == todayDate:
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

        should_alert = (
            sub_condition == "GOING_UP" and missed_opportunity > opportunity
        ) or (sub_condition == "GOING_DOWN" and missed_opportunity < opportunity)

        if should_alert:
            if sub_condition == "GOING_UP":
                alertMessage = (
                    f"{ticker}'s price has risen significantly.\n"
                    f"Missed opportunity: {missed_opportunity:.2f}%.\n"
                    f"Peak price: {peak_price}, Current price: {current_price}"
                )
            elif sub_condition == "GOING_DOWN":
                alertMessage = (
                    f"{ticker}'s price has dropped significantly.\n"
                    f"Missed opportunity: {missed_opportunity:.2f}%.\n"
                    f"Peak price: {peak_price}, Current price: {current_price}"
                )

            alertTriggered.append(
                {
                    "subCondition": sub_condition,
                    "condition": alert["condition"],
                    "advanceCondition": "",
                    "alertMessage": alertMessage,
                }
            )
            asyncio.create_task(
                run_alert_trigger(alert, alertTriggered, key=sub_condition)
            )
