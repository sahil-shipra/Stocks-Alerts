import yfinance as yf
from datetime import datetime, timedelta


def check_from_today_open_price(
    ticker,
    currentPrice,
    alert,
    alertTriggered,
    alertTitleTickerFullName,
    alertMessageTickerFullName,
):
    """
    Check if a stock's price has gone up or down from today's open
    and trigger alerts based on the alert settings.
    """

    # Fetch today's data safely
    try:
        stock = yf.Ticker(ticker)
        print(f"{stock}")
        current_date_plus_two = (datetime.now() + timedelta(days=2)).strftime(
            "%Y-%m-%d"
        )
        data = stock.history(
            start=datetime.now().strftime("%Y-%m-%d"), end=current_date_plus_two
        )
        print(f"{data}")
        if data.empty:
            print(f"[Warning] No data for {ticker}")
            return

        todayOpenPrice = data.iloc[0]["Open"]
    except Exception as e:
        print(f"[Error] Could not fetch data for {ticker}: {e}")
        return

    # Calculate price and percentage change
    change = currentPrice - todayOpenPrice
    percentageChange = (change / todayOpenPrice) * 100
    value = alert["value"]

    # --- Check percentage-based alerts ---
    if alert["valueType"] == "PERCENTAGE":
        if alert["subCondition"] == "GOING_UP" and percentageChange > value:
            alertTitle = f"{alertTitleTickerFullName} Going Up"
            alertMessage = (
                f"{alertMessageTickerFullName} is going up!\n"
                f"The price has risen {round(percentageChange, 2)}% "
                f"from today's open of {round(todayOpenPrice, 2)} to {round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "fromTodayOpenPrice",
                    "subCondition": "GOING_UP",
                    "valueType": "PERCENTAGE",
                    "condition": alert["condition"],
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )

        elif alert["subCondition"] == "GOING_DOWN" and percentageChange < -value:
            alertTitle = f"{alertTitleTickerFullName} Going Down"
            alertMessage = (
                f"{alertMessageTickerFullName} is going down!\n"
                f"The price has dropped {round(percentageChange, 2)}% "
                f"from today's open of {round(todayOpenPrice, 2)} to {round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "fromTodayOpenPrice",
                    "subCondition": "GOING_DOWN",
                    "valueType": "PERCENTAGE",
                    "condition": alert["condition"],
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )

    # --- Check price-based alerts ---
    elif alert["valueType"] == "PRICE":
        print(f"change: {change}")
        print(f"value: {value}")
        if alert["subCondition"] == "GOING_UP" and change > value:
            alertTitle = f"{alertTitleTickerFullName} Going Up"
            alertMessage = (
                f"{alertMessageTickerFullName} is going up!\n"
                f"The price has risen {round(change, 2)} "
                f"from today’s open of {round(todayOpenPrice, 2)} to {round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "fromTodayOpenPrice",
                    "subCondition": "GOING_UP",
                    "valueType": "PRICE",
                    "condition": alert["condition"],
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )

        elif alert["subCondition"] == "GOING_DOWN" and change < -value:
            alertTitle = f"{alertTitleTickerFullName} Going Down"
            alertMessage = (
                f"{alertMessageTickerFullName} is going down!\n"
                f"The price has dropped {round(change, 2)} "
                f"from today's open of {round(todayOpenPrice, 2)} to {round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "fromTodayOpenPrice",
                    "subCondition": "GOING_DOWN",
                    "valueType": "PRICE",
                    "condition": alert["condition"],
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )
