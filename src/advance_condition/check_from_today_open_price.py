import yfinance as yf
from datetime import datetime, timedelta


def check_from_today_open_price(alert, alertTriggered):
    """
    Check if a stock's price has gone up or down from today's open
    and trigger alerts based on the alert settings.

    Args:
        alert: Dictionary containing alert configuration with keys:
               - ticker/tickerNm: Stock ticker symbol
               - addedPriceAt: Current price
               - value: Threshold value
               - valueType: 'PERCENTAGE' or 'PRICE'
               - subCondition: 'GOING_UP' or 'GOING_DOWN'
               - condition: Alert condition type
        alertTriggered: List to append triggered alerts to
    """
    if alert is None:
        return

    # Extract alert data
    ticker = alert.get("tickerNm") or alert["ticker"]["ticker"]
    current_price = alert.get("current_price") or 0
    ticker_full_name = alert["ticker"]["nm"]
    threshold = alert["value"]
    value_type = alert["valueType"]
    sub_condition = alert["subCondition"]

    if current_price == 0:
        return
    # Fetch today's open price
    try:
        stock = yf.Ticker(ticker)
        current_date_plus_two = (datetime.now() + timedelta(days=2)).strftime(
            "%Y-%m-%d"
        )
        data = stock.history(
            start=datetime.now().strftime("%Y-%m-%d"), end=current_date_plus_two
        )

        if data.empty:
            print(f"[Warning] No data for {ticker}")
            return

        today_open = data.iloc[0]["Open"]

    except Exception as e:
        print(f"[Error] Could not fetch data for {ticker}: {e}")
        return

    # Calculate changes
    change = current_price - today_open
    pct_change = (change / today_open) * 100

    # Determine metric and check if alert should trigger
    is_going_up = sub_condition == "GOING_UP"
    use_percentage = value_type == "PERCENTAGE"

    metric = pct_change if use_percentage else change
    triggered = (metric > threshold) if is_going_up else (metric < -threshold)

    if not triggered:
        return

    # Build alert message
    direction = "Up" if is_going_up else "Down"
    action = "going up" if is_going_up else "going down"
    verb = "risen" if is_going_up else "dropped"

    if use_percentage:
        change_text = f"{abs(round(pct_change, 2))}%"
    else:
        change_text = f"{abs(round(change, 2))}"

    alert_title = f"{ticker_full_name} Going {direction}"
    alert_message = (
        f"{ticker_full_name} is {action}!\n"
        f"The price has {verb} {change_text} "
        f"from today's open of {round(today_open, 2)} to {round(current_price, 2)}."
    )

    # Append triggered alert
    alertTriggered.append(
        {
            "advanceCondition": "fromTodayOpenPrice",
            "subCondition": sub_condition,
            "valueType": value_type,
            "condition": alert["condition"],
            "alertTitle": alert_title,
            "alertMessage": alert_message,
        }
    )
