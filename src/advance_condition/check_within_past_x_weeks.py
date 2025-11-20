import yfinance as yf
from datetime import datetime, timedelta


def check_within_past_x_weeks(alert, alertTriggered):
    """
    Check if a stock's price has gone up or down from X weeks ago
    and trigger alerts based on the alert settings.
    """

    if alert is None:
        return

    ticker = alert.get("tickerNm") or alert["ticker"]["ticker"]
    currentPrice = alert.get("addedPriceAt") or 0
    alertTitleTickerFullName = alert["ticker"]["nm"]
    alertMessageTickerFullName = alert["ticker"]["nm"]

    # Get the number of weeks from the alert (default to 1 if not specified)
    num_weeks = alert.get("weeks") or 1

    # Calculate the date X weeks ago
    try:
        stock = yf.Ticker(ticker)
        print(f"Checking ticker: {ticker} for past {num_weeks} week(s)")

        today = datetime.now()
        # Calculate date X weeks ago (7 days * num_weeks)
        weeks_ago_date = today - timedelta(weeks=num_weeks)

        # Fetch data from X weeks ago to now (with buffer for market closures)
        start_date = (weeks_ago_date - timedelta(days=5)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")

        data = stock.history(start=start_date, end=end_date)
        print(f"Data retrieved: {len(data)} rows")

        if data.empty:
            print(f"[Warning] No data for {ticker}")
            return

        # Find the closest available price to X weeks ago
        target_date = weeks_ago_date.strftime("%Y-%m-%d")

        # Filter data up to and including the target date
        past_data = data[data.index <= target_date]

        if past_data.empty:
            print(
                f"[Warning] No data available for {num_weeks} week(s) ago for {ticker}"
            )
            return

        # Get the last available close price on or before the target date
        pastPrice = past_data.iloc[-1]["Close"]
        pastDate = past_data.index[-1].strftime("%Y-%m-%d")

    except Exception as e:
        print(f"[Error] Could not fetch data for {ticker}: {e}")
        return

    # Calculate price and percentage change from X weeks ago
    change = currentPrice - pastPrice
    percentageChange = (change / pastPrice) * 100
    value = alert["value"]

    print(
        f"Price {num_weeks} week(s) ago ({pastDate}): ${pastPrice}, Current: ${currentPrice}, Change: ${change}, Change %: {percentageChange:.2f}%"
    )

    # Determine the time period label
    if num_weeks == 1:
        time_label = "past week"
    else:
        time_label = f"past {num_weeks} weeks"

    # --- Check percentage-based alerts ---
    if alert["valueType"] == "PERCENTAGE":
        if alert["subCondition"] == "GOING_UP" and percentageChange >= value:
            alertTitle = (
                f"{alertTitleTickerFullName} Going Up Over {time_label.title()}"
            )
            alertMessage = (
                f"{alertMessageTickerFullName} is going up over the {time_label}!\n"
                f"The price has risen {abs(round(percentageChange, 2))}% "
                f"from ${round(pastPrice, 2)} ({pastDate}) to ${round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "withinPastXWeeks",
                    "subCondition": "GOING_UP",
                    "valueType": "PERCENTAGE",
                    "condition": alert["condition"],
                    "weeks": num_weeks,
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )

        elif alert["subCondition"] == "GOING_DOWN" and percentageChange <= -value:
            alertTitle = (
                f"{alertTitleTickerFullName} Going Down Over {time_label.title()}"
            )
            alertMessage = (
                f"{alertMessageTickerFullName} is going down over the {time_label}!\n"
                f"The price has dropped {abs(round(percentageChange, 2))}% "
                f"from ${round(pastPrice, 2)} ({pastDate}) to ${round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "withinPastXWeeks",
                    "subCondition": "GOING_DOWN",
                    "valueType": "PERCENTAGE",
                    "condition": alert["condition"],
                    "weeks": num_weeks,
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )

    # --- Check price-based alerts ---
    elif alert["valueType"] == "PRICE":
        print(f"Price change: ${change}, Threshold: ${value}")

        if alert["subCondition"] == "GOING_UP" and change >= value:
            alertTitle = (
                f"{alertTitleTickerFullName} Going Up Over {time_label.title()}"
            )
            alertMessage = (
                f"{alertMessageTickerFullName} is going up over the {time_label}!\n"
                f"The price has risen ${abs(round(change, 2))} "
                f"from ${round(pastPrice, 2)} ({pastDate}) to ${round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "withinPastXWeeks",
                    "subCondition": "GOING_UP",
                    "valueType": "PRICE",
                    "condition": alert["condition"],
                    "weeks": num_weeks,
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )

        elif alert["subCondition"] == "GOING_DOWN" and change <= -value:
            alertTitle = (
                f"{alertTitleTickerFullName} Going Down Over {time_label.title()}"
            )
            alertMessage = (
                f"{alertMessageTickerFullName} is going down over the {time_label}!\n"
                f"The price has dropped ${abs(round(change, 2))} "
                f"from ${round(pastPrice, 2)} ({pastDate}) to ${round(currentPrice, 2)}."
            )
            alertTriggered.append(
                {
                    "advanceCondition": "withinPastXWeeks",
                    "subCondition": "GOING_DOWN",
                    "valueType": "PRICE",
                    "condition": alert["condition"],
                    "weeks": num_weeks,
                    "alertTitle": alertTitle,
                    "alertMessage": alertMessage,
                }
            )
