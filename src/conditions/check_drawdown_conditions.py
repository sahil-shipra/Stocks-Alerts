from src.apis.get_ticker_closing_price import get_ticker_closing_price
import pandas as pd
import copy


async def compute_drawdowns(ticker: str):
    """
    Returns drawdown_list, current drawdown, and latest running max price.
    """
    # ticker = "GOOGL"  # alert.ticker
    data = await get_ticker_closing_price(ticker)
    stock_data = [{"date": d["time"], "close": d["value"]} for d in data]

    df = pd.DataFrame(copy.deepcopy(stock_data))

    df["Date"] = pd.to_datetime(df["date"]).dt.tz_localize("UTC")
    df["Close"] = df["close"]
    df.set_index("Date", inplace=True)

    # Compute running max and drawdown
    df["running_max"] = df["Close"].cummax()
    df["drawdown"] = df["Close"] / df["running_max"] - 1

    current_drawdown = df["drawdown"].iloc[-1]
    current_date = df.index[-1]

    drawdown_periods = []
    drawdown_start = None

    for date, dd in df["drawdown"].items():
        if dd < 0 and drawdown_start is None:
            drawdown_start = date

        elif dd == 0 and drawdown_start is not None:
            drawdown_end = date

            period = extract_drawdown_period(df, drawdown_start, drawdown_end)
            drawdown_periods.append(period)

            drawdown_start = None

    # Handle ongoing drawdown
    if drawdown_start is not None:
        period = extract_drawdown_period(df, drawdown_start, current_date, ongoing=True)
        drawdown_periods.append(period)

    # Convert to DataFrame
    drawdown_df = pd.DataFrame(drawdown_periods)

    # Take only significant drawdowns > 5%
    drawdown_df = drawdown_df[drawdown_df["max_drawdown"] < -5]

    # Convert rows to list of dicts
    drawdown_list = drawdown_df.to_dict(orient="records")

    # Reverse to get most recent first
    drawdown_list.reverse()

    return drawdown_list, current_drawdown, df["running_max"].iloc[-1]


def extract_drawdown_period(df, start, end, ongoing=False):
    """Extract stats of a drawdown period."""
    dd_slice = df.loc[start:end]
    running_max_slice = df["running_max"].loc[start:end]

    peak_price = running_max_slice.iloc[0]
    low_price = dd_slice["Close"].min()
    max_dd_value = dd_slice["drawdown"].min()
    max_dd_date = dd_slice["drawdown"].idxmin()
    max_dd_price = df["Close"].loc[max_dd_date]
    duration = (end - start).days

    opportunity = (
        None if ongoing else round(((peak_price - low_price) / low_price) * 100, 2)
    )

    return {
        "start_date": start.strftime("%d-%b-%y"),
        "end_date": "TBD" if ongoing else end.strftime("%d-%b-%y"),
        "max_drawdown": round(max_dd_value * 100, 2),
        "duration": f"{duration} days",
        "peak_price": round(peak_price, 2),
        "low_price": round(low_price, 2),
        "opportunity": opportunity,
        "max_drawdown_date": max_dd_date.strftime("%d-%b-%y"),
        "max_drawdown_price": round(max_dd_price, 2),
    }


def add_alert(alertTriggered, condition, title, message):
    """Helper to append alerts in a consistent format."""
    alertTriggered.append(
        {
            "advanceCondition": condition,
            "condition": "DRAWDOWN",
            "subCondition": "",
            "alertTitle": title,
            "alertMessage": message,
        }
    )


# MAIN HANDLER
async def check_drawdown_conditions(alert):
    alertTriggered = []

    alertTitleTickerFullName = alert["tickerNm"]
    alertMessageTickerFullName = alert["tickerNm"]
    currentStockData = alert["currentStockData"]
    currentPrice = currentStockData["price"]
    ticker = alert["tickerNm"]
    # if alert["condition"] != "DRAWDOWN" or lastCloseDate != todayDate:
    #     return
    if alert is None:
        return

    drawdownAdvanceCondition = alert["drawdownAdvanceCondition"]

    # Compute Drawdowns
    drawdown_list, currentDrawdown, _ = await compute_drawdowns(ticker)

    # ========== Common computed values ==========
    last_dd = drawdown_list[1] if len(drawdown_list) > 1 else None
    worst_dd = min(drawdown_list, key=lambda x: x["max_drawdown"])
    current_dd_info = drawdown_list[0]

    # ====================================================
    # ALERT 1: Near Last Drawdown
    # ====================================================
    if drawdownAdvanceCondition.get("nearLastDrawdown") and last_dd:
        tolerance = drawdownAdvanceCondition["nearLastDrawdownValue"] / 100
        dd_val = last_dd["max_drawdown"]

        lower = dd_val * (1 - tolerance)
        upper = dd_val * (1 + tolerance)

        if lower <= currentDrawdown * 100 <= upper:
            title = f"{alertTitleTickerFullName} Near Last Drawdown"
            msg = (
                f"{alertMessageTickerFullName} is near its last drawdown. "
                f"Price {(currentPrice)} is within "
                f"{drawdownAdvanceCondition['nearLastDrawdownValue']}% of "
                f"{round(dd_val, 2)}%."
            )
            add_alert(alertTriggered, "nearLastDrawdown", title, msg)

    # ====================================================
    # ALERT 2: Price Surpasses Last Drawdown Price
    # ====================================================
    if drawdownAdvanceCondition.get("priceSurpassLastDrawdown") and last_dd:
        if currentPrice < last_dd["max_drawdown_price"]:
            title = f"{alertTitleTickerFullName} Price Surpass Last Drawdown"
            msg = (
                f"{alertMessageTickerFullName} has fallen below the last "
                f"drawdown price ({(currentPrice)})."
            )
            add_alert(alertTriggered, "priceSurpassLastDrawdown", title, msg)

    # ====================================================
    # ALERT 3: Surpasses Historical Drawdown
    # ====================================================
    if drawdownAdvanceCondition.get("priceSurpassMultipleHistoricalDrawdown"):
        if currentPrice < worst_dd["max_drawdown_price"]:
            title = f"{alertTitleTickerFullName} Surpass Historical Drawdown"
            msg = (
                f"{alertMessageTickerFullName} fell below all historical "
                f"drawdown prices. Current: {(currentPrice)}."
            )
            add_alert(
                alertTriggered, "priceSurpassMultipleHistoricalDrawdown", title, msg
            )

    # ====================================================
    # ALERT 4: Price Approaches Historical Drawdown
    # ====================================================
    if drawdownAdvanceCondition.get("priceApproachHistoricalDrawdown"):
        tolerance = (
            drawdownAdvanceCondition["priceApproachHistoricalDrawdownValue"] / 100
        )
        dd_price = worst_dd["max_drawdown_price"]

        upper = dd_price * (1 + tolerance)

        if dd_price <= currentPrice <= upper:
            title = f"{alertTitleTickerFullName} Approach Historical Drawdown"
            msg = (
                f"{alertMessageTickerFullName} is approaching its historical drawdown "
                f"within {drawdownAdvanceCondition['priceApproachHistoricalDrawdownValue']}%."
            )
            add_alert(alertTriggered, "priceApproachHistoricalDrawdown", title, msg)

    # ====================================================
    # ALERT 5: Recover After Drawdown
    # ====================================================
    if drawdownAdvanceCondition.get("priceRecoverAfterDrawdown"):
        tolerance = drawdownAdvanceCondition["priceRecoverAfterDrawdownValue"] / 100
        dd_price = current_dd_info["max_drawdown_price"]
        upper = dd_price * (1 + tolerance)

        if currentPrice > upper:
            title = f"{alertTitleTickerFullName} Price Recover After Drawdown"
            msg = (
                f"{alertMessageTickerFullName} recovered "
                f"{drawdownAdvanceCondition['priceRecoverAfterDrawdownValue']}%. "
                f"Price is now {(currentPrice)}."
            )
            add_alert(alertTriggered, "priceRecoverAfterDrawdown", title, msg)
