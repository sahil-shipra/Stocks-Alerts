import pandas as pd
import pandas_ta as ta
from datetime import datetime
from src.apis.get_ticker_closing_price import get_ticker_closing_price


async def check_rsi_conditions(alert):
    ticker = alert["tickerNm"]
    data = await get_ticker_closing_price(ticker)
    stock_data = [{"date": d["time"], "close": d["value"]} for d in data]
    lastCloseDate = datetime.strptime(stock_data[-1]["date"], "%Y-%m-%d").date()
    todayDate = datetime.today().date()
    alertTriggered = []

    if alert["condition"] == "RSI" and lastCloseDate == todayDate:
        df = pd.DataFrame(stock_data)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        # Calculate RSI
        rsi_period = alert["rsiPeriod"]
        df["RSI"] = ta.rsi(df["close"], length=rsi_period)
        current_rsi = df["RSI"].iloc[-1]

        rsi_conditions = alert["rsiAdvanceCondition"]

        # Helper function to append alerts
        def trigger_alert(advance_condition):
            alertTriggered.append(
                {
                    "advanceCondition": advance_condition,
                    "condition": alert["condition"],
                    "subCondition": "",
                }
            )

        # Check RSI less than X
        if (
            rsi_conditions.get("rsiLessThanX")
            and current_rsi < rsi_conditions["rsiLessThanXValue"]
        ):
            trigger_alert("rsiLessThanX")

        # Check RSI greater than X
        if (
            rsi_conditions.get("rsiGreaterThanX")
            and current_rsi > rsi_conditions["rsiGreaterThanXValue"]
        ):
            trigger_alert("rsiGreaterThanX")

        # Check RSI in a specific range
        if rsi_conditions.get("rsiSpecificRange"):
            low, high = rsi_conditions["lowRange"], rsi_conditions["highRange"]
            if low < current_rsi < high:
                trigger_alert("rsiSpecificRange")

        # Historical extreme helper
        def check_historical_extreme(extreme_type, value_key, comparator):
            n_days = rsi_conditions.get(value_key)
            if n_days and len(df) >= n_days:
                historical_rsi = df["RSI"].tail(n_days)
                if comparator(current_rsi, historical_rsi):
                    trigger_alert(extreme_type)

        # Check historical low
        check_historical_extreme(
            "rsiHistoricalLowExtreme",
            "rsiHistoricalLowExtremeValue",
            lambda current, hist: current < hist.min(),
        )

        # Check historical high
        check_historical_extreme(
            "rsiHistoricalHighExtreme",
            "rsiHistoricalHighExtremeValue",
            lambda current, hist: current > hist.max(),
        )
