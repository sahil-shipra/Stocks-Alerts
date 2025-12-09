import asyncio
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from src.alert_cache import get_alert_triggered
from src.alert_trigger import run_alert_trigger
from src.apis.get_ticker_closing_price import get_ticker_closing_price


async def check_rsi_conditions(alert):
    ticker = alert["tickerNm"]
    data = await get_ticker_closing_price(ticker)
    stock_data = [{"date": d["time"], "close": d["value"]} for d in data]
    lastCloseDate = datetime.strptime(stock_data[-1]["date"], "%Y-%m-%d").date()
    todayDate = datetime.today().date()
    alertTriggered = []
    alertTitleTickerFullName = alert["ticker"]["nm"]
    alertMessageTickerFullName = alert["ticker"]["nm"]

    if alert["condition"] == "RSI":  # and lastCloseDate == todayDate:
        df = pd.DataFrame(stock_data)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        # Calculate RSI
        rsi_period = alert["rsiPeriod"]
        df["RSI"] = ta.rsi(df["close"], length=rsi_period)
        current_rsi = df["RSI"].iloc[-1]

        rsi_conditions = alert["rsiAdvanceCondition"]
        emailAddress = alert["emailAddress"][0]

        # Helper function to append alerts
        def trigger_alert(advance_condition, alertMessage):
            alertTriggered.append(
                {
                    "advanceCondition": advance_condition,
                    "condition": alert["condition"],
                    "subCondition": "",
                    "alertTitle": f"RSI Alert for {alertTitleTickerFullName}",
                    "alertMessage": alertMessage,
                }
            )
            asyncio.create_task(
                run_alert_trigger(alert, alertTriggered, key=advance_condition)
            )

        # Check RSI less than X
        if (
            rsi_conditions.get("rsiLessThanX")
            and current_rsi < rsi_conditions["rsiLessThanXValue"]
            and not await get_alert_triggered(ticker, emailAddress, key="rsiLessThanX")
        ):
            threshold = rsi_conditions["rsiLessThanXValue"]
            alertMessage = (
                f"{alertMessageTickerFullName} RSI is less than {threshold} for the RSI period of {rsi_period}!\n"
                f"RSI changed from {threshold} to {current_rsi}."
            )
            trigger_alert("rsiLessThanX", alertMessage)

        # Check RSI greater than X
        if (
            rsi_conditions.get("rsiGreaterThanX")
            and current_rsi > rsi_conditions["rsiGreaterThanXValue"]
            and not await get_alert_triggered(
                ticker, emailAddress, key="rsiGreaterThanX"
            )
        ):
            threshold = rsi_conditions["rsiGreaterThanXValue"]
            alertMessage = (
                f"{alertMessageTickerFullName} RSI is greater than {threshold} for the RSI period of {rsi_period}!\n"
                f"RSI changed from {threshold} to {current_rsi}."
            )
            trigger_alert("rsiGreaterThanX", alertMessage)

        # Check RSI in a specific range
        if rsi_conditions.get("rsiSpecificRange") and not await get_alert_triggered(
            ticker, emailAddress, key="rsiSpecificRange"
        ):
            low, high = rsi_conditions["lowRange"], rsi_conditions["highRange"]
            if low < current_rsi < high:
                alertMessage = (
                    f"{alertMessageTickerFullName}'s RSI is within the range {low}–{high} "
                    f"for the RSI period of {rsi_period}.\n"
                    f"Current RSI: {current_rsi}."
                )
                trigger_alert("rsiSpecificRange", alertMessage)

        # Historical extreme helper
        def check_historical_extreme(extreme_type, value_key, comparator, alertMessage):
            n_days = rsi_conditions.get(value_key)
            if n_days and len(df) >= n_days:
                historical_rsi = df["RSI"].tail(n_days)
                if comparator(current_rsi, historical_rsi):
                    trigger_alert(extreme_type, alertMessage)

        # Check historical low
        check_historical_extreme(
            "rsiHistoricalLowExtreme",
            "rsiHistoricalLowExtremeValue",
            lambda current, hist: current < hist.min(),
            alertMessage=(
                f"{alertMessageTickerFullName}'s RSI has dropped below its historical low value "
                f"for the RSI period of {rsi_period}.\n"
                f"Current RSI: {current_rsi}."
            ),
        )

        # Check historical high
        check_historical_extreme(
            "rsiHistoricalHighExtreme",
            "rsiHistoricalHighExtremeValue",
            lambda current, hist: current > hist.max(),
            alertMessage=(
                f"{alertMessageTickerFullName}'s RSI has exceeded its historical high value "
                f"for the RSI period of {rsi_period}.\n"
                f"Current RSI: {current_rsi}."
            ),
        )
