import yfinance as yf
from datetime import datetime, timedelta


def check_from_yesterday_close_price(alert, alertTriggered):
    """
    Check if a stock's price has gone up or down from yesterday's close
    and trigger alerts based on the alert settings.
    """

    if alert is None:
        return

    ticker = alert.get("tickerNm") or alert["ticker"]["ticker"]
    currentPrice = alert.get("current_price") or 0
    alertTitleTickerFullName = alert["ticker"]["nm"]
    alertMessageTickerFullName = alert["ticker"]["nm"]

    if currentPrice == 0:
        return

    # Fetch historical data to get yesterday's close
    try:
        stock = yf.Ticker(ticker)
        
        # Get data for the last 5 days to ensure we have yesterday's close
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

        data = stock.history(start=start_date, end=end_date)

        if data.empty or len(data) < 2:
            print(f"[Warning] Insufficient data for {ticker}")
            return

        # Get yesterday's close (second to last row, or last row if today's data isn't available)
        yesterdayClosePrice = (
            data.iloc[-2]["Close"] if len(data) >= 2 else data.iloc[-1]["Close"]
        )

    except Exception as e:
        print(f"[Error] Could not fetch data for {ticker}: {e}")
        return

    # Calculate price and percentage change from yesterday's close
    change = currentPrice - yesterdayClosePrice
    percentageChange = (change / yesterdayClosePrice) * 100
    value = alert["value"]

     # --- Check percentage-based alerts ---
    if alert["valueType"] == "PERCENTAGE":
        if alert["subCondition"] == "GOING_UP" and percentageChange >= value:
            alertTitle = f"{alertTitleTickerFullName} Going Up"
            alertMessage = (
                f"{alertMessageTickerFullName} is going up!\n"
                f"The price has risen {abs(round(percentageChange, 2))}% "
                f"from yesterday's close of ${round(yesterdayClosePrice, 2)} to ${round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "fromYesterdayClosePrice",
                    "subCondition": "GOING_UP",
                    "valueType": "PERCENTAGE",
                    "condition": alert["condition"],
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )

        elif alert["subCondition"] == "GOING_DOWN" and percentageChange <= -value:
            alertTitle = f"{alertTitleTickerFullName} Going Down"
            alertMessage = (
                f"{alertMessageTickerFullName} is going down!\n"
                f"The price has dropped {abs(round(percentageChange, 2))}% "
                f"from yesterday's close of ${round(yesterdayClosePrice, 2)} to ${round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "fromYesterdayClosePrice",
                    "subCondition": "GOING_DOWN",
                    "valueType": "PERCENTAGE",
                    "condition": alert["condition"],
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )

    # --- Check price-based alerts ---
    elif alert["valueType"] == "PRICE":
        print(f"Price change: ${change}, Threshold: ${value}")

        if alert["subCondition"] == "GOING_UP" and change >= value:
            alertTitle = f"{alertTitleTickerFullName} Going Up"
            alertMessage = (
                f"{alertMessageTickerFullName} is going up!\n"
                f"The price has risen ${abs(round(change, 2))} "
                f"from yesterday's close of ${round(yesterdayClosePrice, 2)} to ${round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "fromYesterdayClosePrice",
                    "subCondition": "GOING_UP",
                    "valueType": "PRICE",
                    "condition": alert["condition"],
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )

        elif alert["subCondition"] == "GOING_DOWN" and change <= -value:
            alertTitle = f"{alertTitleTickerFullName} Going Down"
            alertMessage = (
                f"{alertMessageTickerFullName} is going down!\n"
                f"The price has dropped ${abs(round(change, 2))} "
                f"from yesterday's close of ${round(yesterdayClosePrice, 2)} to ${round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "fromYesterdayClosePrice",
                    "subCondition": "GOING_DOWN",
                    "valueType": "PRICE",
                    "condition": alert["condition"],
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )
