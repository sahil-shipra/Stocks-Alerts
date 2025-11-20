import yfinance as yf
from datetime import datetime, timedelta


def check_within_past_x_week_value(alert, alertTriggered):
    """
    Check if a stock's highest or lowest price within the past X weeks
    meets the specified threshold and trigger alerts based on the alert settings.
    This checks for peak/trough values within the time period rather than just endpoint comparison.
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
        print(f"Checking ticker: {ticker} for peak/trough in past {num_weeks} week(s)")

        today = datetime.now()
        # Calculate date X weeks ago (7 days * num_weeks)
        weeks_ago_date = today - timedelta(weeks=num_weeks)

        # Fetch data from X weeks ago to now
        start_date = (weeks_ago_date - timedelta(days=3)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")

        data = stock.history(start=start_date, end=end_date)
        print(f"Data retrieved: {len(data)} rows")

        if data.empty:
            print(f"[Warning] No data for {ticker}")
            return

        # Filter data to only include past X weeks
        target_date = weeks_ago_date.strftime("%Y-%m-%d")
        period_data = data[data.index >= target_date]

        if period_data.empty:
            print(
                f"[Warning] No data available for past {num_weeks} week(s) for {ticker}"
            )
            return

        # Get highest and lowest values within the period
        highestPrice = period_data["High"].max()
        lowestPrice = period_data["Low"].min()
        highestDate = (
            period_data[period_data["High"] == highestPrice]
            .index[0]
            .strftime("%Y-%m-%d")
        )
        lowestDate = (
            period_data[period_data["Low"] == lowestPrice].index[0].strftime("%Y-%m-%d")
        )

    except Exception as e:
        print(f"[Error] Could not fetch data for {ticker}: {e}")
        return

    value = alert["value"]

    # Determine the time period label
    if num_weeks == 1:
        time_label = "past week"
    else:
        time_label = f"past {num_weeks} weeks"

    print(
        f"Period: {time_label}, Highest: ${highestPrice} ({highestDate}), Lowest: ${lowestPrice} ({lowestDate}), Current: ${currentPrice}"
    )

    # --- Check percentage-based alerts ---
    if alert["valueType"] == "PERCENTAGE":
        if alert["subCondition"] == "GOING_UP":
            # Calculate percentage change from lowest to current
            changeFromLowest = currentPrice - lowestPrice
            percentageChangeFromLowest = (changeFromLowest / lowestPrice) * 100

            if percentageChangeFromLowest >= value:
                alertTitle = f"{alertTitleTickerFullName} Up {abs(round(percentageChangeFromLowest, 2))}% from {time_label.title()} Low"
                alertMessage = (
                    f"{alertMessageTickerFullName} has risen significantly!\n"
                    f"The price has increased {abs(round(percentageChangeFromLowest, 2))}% "
                    f"from the {time_label} low of ${round(lowestPrice, 2)} ({lowestDate}) to ${round(currentPrice, 2)}."
                )
                alertTriggered.append(
                    {
                        "advanceCondition": "withinPastXWeekValue",
                        "subCondition": "GOING_UP",
                        "valueType": "PERCENTAGE",
                        "condition": alert["condition"],
                        "weeks": num_weeks,
                        "referencePrice": lowestPrice,
                        "referenceDate": lowestDate,
                        "alertTitle": alertTitle,
                        "alertMessage": alertMessage,
                    }
                )

        elif alert["subCondition"] == "GOING_DOWN":
            # Calculate percentage change from highest to current
            changeFromHighest = currentPrice - highestPrice
            percentageChangeFromHighest = (changeFromHighest / highestPrice) * 100

            if percentageChangeFromHighest <= -value:
                alertTitle = f"{alertTitleTickerFullName} Down {abs(round(percentageChangeFromHighest, 2))}% from {time_label.title()} High"
                alertMessage = (
                    f"{alertMessageTickerFullName} has dropped significantly!\n"
                    f"The price has decreased {abs(round(percentageChangeFromHighest, 2))}% "
                    f"from the {time_label} high of ${round(highestPrice, 2)} ({highestDate}) to ${round(currentPrice, 2)}."
                )
                alertTriggered.append(
                    {
                        "advanceCondition": "withinPastXWeekValue",
                        "subCondition": "GOING_DOWN",
                        "valueType": "PERCENTAGE",
                        "condition": alert["condition"],
                        "weeks": num_weeks,
                        "referencePrice": highestPrice,
                        "referenceDate": highestDate,
                        "alertTitle": alertTitle,
                        "alertMessage": alertMessage,
                    }
                )

    # --- Check price-based alerts ---
    elif alert["valueType"] == "PRICE":
        if alert["subCondition"] == "GOING_UP":
            # Calculate price change from lowest to current
            changeFromLowest = currentPrice - lowestPrice

            print(f"Change from lowest: ${changeFromLowest}, Threshold: ${value}")

            if changeFromLowest >= value:
                alertTitle = f"{alertTitleTickerFullName} Up ${abs(round(changeFromLowest, 2))} from {time_label.title()} Low"
                alertMessage = (
                    f"{alertMessageTickerFullName} has risen significantly!\n"
                    f"The price has increased ${abs(round(changeFromLowest, 2))} "
                    f"from the {time_label} low of ${round(lowestPrice, 2)} ({lowestDate}) to ${round(currentPrice, 2)}."
                )
                alertTriggered.append(
                    {
                        "advanceCondition": "withinPastXWeekValue",
                        "subCondition": "GOING_UP",
                        "valueType": "PRICE",
                        "condition": alert["condition"],
                        "weeks": num_weeks,
                        "referencePrice": lowestPrice,
                        "referenceDate": lowestDate,
                        "alertTitle": alertTitle,
                        "alertMessage": alertMessage,
                    }
                )

        elif alert["subCondition"] == "GOING_DOWN":
            # Calculate price change from highest to current
            changeFromHighest = currentPrice - highestPrice

            print(f"Change from highest: ${changeFromHighest}, Threshold: ${value}")

            if changeFromHighest <= -value:
                alertTitle = f"{alertTitleTickerFullName} Down ${abs(round(changeFromHighest, 2))} from {time_label.title()} High"
                alertMessage = (
                    f"{alertMessageTickerFullName} has dropped significantly!\n"
                    f"The price has decreased ${abs(round(changeFromHighest, 2))} "
                    f"from the {time_label} high of ${round(highestPrice, 2)} ({highestDate}) to ${round(currentPrice, 2)}."
                )
                alertTriggered.append(
                    {
                        "advanceCondition": "withinPastXWeekValue",
                        "subCondition": "GOING_DOWN",
                        "valueType": "PRICE",
                        "condition": alert["condition"],
                        "weeks": num_weeks,
                        "referencePrice": highestPrice,
                        "referenceDate": highestDate,
                        "alertTitle": alertTitle,
                        "alertMessage": alertMessage,
                    }
                )
