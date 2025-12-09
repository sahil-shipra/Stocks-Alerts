import yfinance as yf
from datetime import datetime, timedelta


def check_within_current_week(alert, alertTriggered):
    """
    Check if a stock's price has gone up or down from the start of the current week (Monday's open)
    and trigger alerts based on the alert settings.
    """

    if alert is None:
        return

    ticker = alert.get("tickerNm") or alert["ticker"]["ticker"]
    currentPrice = alert.get("current_price") or 0
    alertTitleTickerFullName = alert["ticker"]["nm"]
    alertMessageTickerFullName = alert["ticker"]["nm"]

    # Calculate the start of the current week (Monday)
    try:
        stock = yf.Ticker(ticker)
        print(f"Checking ticker: {ticker}")

        today = datetime.now()
        # Get Monday of current week (0 = Monday, 6 = Sunday)
        days_since_monday = today.weekday()
        monday_date = today - timedelta(days=days_since_monday)

        # Fetch data from Monday to now (plus buffer for safety)
        start_date = (monday_date - timedelta(days=3)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")

        data = stock.history(start=start_date, end=end_date)
        print(f"Data retrieved: {len(data)} rows")

        if data.empty:
            print(f"[Warning] No data for {ticker}")
            return

        # Find Monday's open price (first available data point of the week)
        # Filter data to only include data from Monday onwards
        monday_str = monday_date.strftime("%Y-%m-%d")
        week_data = data[data.index >= monday_str]

        if week_data.empty:
            print(f"[Warning] No data available for current week for {ticker}")
            return

        weekStartPrice = week_data.iloc[0]["Open"]
        weekStartDate = week_data.index[0].strftime("%Y-%m-%d")

    except Exception as e:
        print(f"[Error] Could not fetch data for {ticker}: {e}")
        return

    # Calculate price and percentage change from week start
    change = currentPrice - weekStartPrice
    percentageChange = (change / weekStartPrice) * 100
    value = alert["value"]

    print(
        f"Week Start ({weekStartDate}): ${weekStartPrice}, Current: ${currentPrice}, Change: ${change}, Change %: {percentageChange:.2f}%"
    )

    # --- Check percentage-based alerts ---
    if alert["valueType"] == "PERCENTAGE":
        if alert["subCondition"] == "GOING_UP" and percentageChange >= value:
            alertTitle = f"{alertTitleTickerFullName} Going Up This Week"
            alertMessage = (
                f"{alertMessageTickerFullName} is going up this week!\n"
                f"The price has risen {abs(round(percentageChange, 2))}% "
                f"from this week's start of ${round(weekStartPrice, 2)} to ${round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "withinCurrentWeek",
                    "subCondition": "GOING_UP",
                    "valueType": "PERCENTAGE",
                    "condition": alert["condition"],
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )

        elif alert["subCondition"] == "GOING_DOWN" and percentageChange <= -value:
            alertTitle = f"{alertTitleTickerFullName} Going Down This Week"
            alertMessage = (
                f"{alertMessageTickerFullName} is going down this week!\n"
                f"The price has dropped {abs(round(percentageChange, 2))}% "
                f"from this week's start of ${round(weekStartPrice, 2)} to ${round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "withinCurrentWeek",
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
            alertTitle = f"{alertTitleTickerFullName} Going Up This Week"
            alertMessage = (
                f"{alertMessageTickerFullName} is going up this week!\n"
                f"The price has risen ${abs(round(change, 2))} "
                f"from this week's start of ${round(weekStartPrice, 2)} to ${round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "withinCurrentWeek",
                    "subCondition": "GOING_UP",
                    "valueType": "PRICE",
                    "condition": alert["condition"],
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )

        elif alert["subCondition"] == "GOING_DOWN" and change <= -value:
            alertTitle = f"{alertTitleTickerFullName} Going Down This Week"
            alertMessage = (
                f"{alertMessageTickerFullName} is going down this week!\n"
                f"The price has dropped ${abs(round(change, 2))} "
                f"from this week's start of ${round(weekStartPrice, 2)} to ${round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "withinCurrentWeek",
                    "subCondition": "GOING_DOWN",
                    "valueType": "PRICE",
                    "condition": alert["condition"],
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )
