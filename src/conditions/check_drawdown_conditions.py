from src.alert_cache import get_alert_triggered
from src.alert_trigger import run_alert_trigger
from src.apis.get_ticker_closing_price import get_ticker_closing_price
import pandas as pd
import numpy as np


async def compute_drawdowns(ticker: str):
    """
    Returns drawdown_list, current drawdown, and latest running max price.
    """
    data = await get_ticker_closing_price(ticker)

    # Direct DataFrame creation without deep copy
    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["time"], utc=True)
    df = df.set_index("Date")[["value"]].rename(columns={"value": "Close"})

    # Vectorized operations
    df["running_max"] = df["Close"].cummax()
    df["drawdown"] = df["Close"] / df["running_max"] - 1

    current_drawdown = df["drawdown"].iloc[-1]
    current_date = df.index[-1]

    # Vectorized drawdown period detection
    drawdown_periods = _extract_drawdown_periods_vectorized(df, current_date)

    # Filter significant drawdowns (> 5%)
    drawdown_list = [d for d in drawdown_periods if d["max_drawdown"] < -5]
    drawdown_list.reverse()

    return drawdown_list, current_drawdown, df["running_max"].iloc[-1]


def _extract_drawdown_periods_vectorized(df, current_date):
    """Extract drawdown periods using vectorized operations."""
    drawdowns = df["drawdown"].values
    dates = df.index

    # Identify drawdown boundaries
    is_drawdown = drawdowns < 0
    boundaries = np.diff(np.concatenate([[False], is_drawdown, [False]]).astype(int))
    starts = np.where(boundaries == 1)[0]
    ends = np.where(boundaries == -1)[0]

    periods = []
    for start_idx, end_idx in zip(starts, ends):
        start_date = dates[start_idx]
        end_date = dates[end_idx] if end_idx < len(dates) else current_date
        ongoing = end_idx >= len(dates)

        period = _extract_drawdown_stats(df, start_date, end_date, ongoing)
        periods.append(period)

    # Handle ongoing drawdown
    if is_drawdown[-1] and (
        len(starts) == 0 or starts[-1] >= ends[-1] if len(ends) > 0 else True
    ):
        start_idx = starts[-1] if len(starts) > 0 else np.where(is_drawdown)[0][0]
        start_date = dates[start_idx]
        period = _extract_drawdown_stats(df, start_date, current_date, ongoing=True)
        periods.append(period)

    return periods


def _extract_drawdown_stats(df, start, end, ongoing=False):
    """Extract stats of a drawdown period."""
    dd_slice = df.loc[start:end]

    peak_price = df["running_max"].loc[start]
    low_price = dd_slice["Close"].min()
    max_dd_value = dd_slice["drawdown"].min()
    max_dd_date = dd_slice["drawdown"].idxmin()
    max_dd_price = dd_slice["Close"].loc[max_dd_date]
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


def _create_alert(condition, title, message):
    """Helper to create alert dict."""
    return {
        "advanceCondition": condition,
        "condition": "DRAWDOWN",
        "subCondition": "",
        "alertTitle": title,
        "alertMessage": message,
    }


async def _check_alert(ticker, email, key, condition_fn, alert_data):
    """Generic alert checker to reduce code duplication."""
    if await get_alert_triggered(ticker, email, key=key):
        return None

    result = condition_fn(alert_data)
    await run_alert_trigger(alert_data["alert"], alert_data["alerts"], key=key)
    return result


async def check_drawdown_conditions(alert):
    """Main handler for drawdown condition checking."""
    if alert is None:
        return

    alertTriggered = []
    ticker = alert["tickerNm"]
    currentPrice = alert["currentStockData"]["price"]
    emailAddress = alert["emailAddress"][0]
    drawdownAdvanceCondition = alert["drawdownAdvanceCondition"]

    # Compute drawdowns once
    drawdown_list, currentDrawdown, _ = await compute_drawdowns(ticker)

    if len(drawdown_list) < 1:
        return

    # Pre-compute common values
    last_dd = drawdown_list[1] if len(drawdown_list) > 1 else None
    worst_dd = min(drawdown_list, key=lambda x: x["max_drawdown"])
    current_dd_info = drawdown_list[0]

    alert_data = {
        "alert": alert,
        "alerts": alertTriggered,
        "ticker": ticker,
        "currentPrice": currentPrice,
        "currentDrawdown": currentDrawdown,
        "tickerNm": alert["tickerNm"],
    }

    # Alert 1: Near Last Drawdown
    if drawdownAdvanceCondition.get("nearLastDrawdown") and last_dd:
        if not await get_alert_triggered(ticker, emailAddress, key="nearLastDrawdown"):
            tolerance = drawdownAdvanceCondition["nearLastDrawdownValue"] / 100
            dd_val = last_dd["max_drawdown"]
            lower, upper = dd_val * (1 - tolerance), dd_val * (1 + tolerance)

            if lower <= currentDrawdown * 100 <= upper:
                alertTriggered.append(
                    _create_alert(
                        "nearLastDrawdown",
                        f"{ticker} Near Last Drawdown",
                        f"{ticker} is near its last drawdown. Price {currentPrice} is within "
                        f"{drawdownAdvanceCondition['nearLastDrawdownValue']}% of {round(dd_val, 2)}%.",
                    )
                )
        await run_alert_trigger(alert, alertTriggered, key="nearLastDrawdown")

    # Alert 2: Price Surpasses Last Drawdown Price
    if drawdownAdvanceCondition.get("priceSurpassLastDrawdown") and last_dd:
        if not await get_alert_triggered(
            ticker, emailAddress, key="priceSurpassLastDrawdown"
        ):
            if currentPrice < last_dd["max_drawdown_price"]:
                alertTriggered.append(
                    _create_alert(
                        "priceSurpassLastDrawdown",
                        f"{ticker} Price Surpass Last Drawdown",
                        f"{ticker} has fallen below the last drawdown price ({currentPrice}).",
                    )
                )
        await run_alert_trigger(alert, alertTriggered, key="priceSurpassLastDrawdown")

    # Alert 3: Surpasses Historical Drawdown
    if drawdownAdvanceCondition.get("priceSurpassMultipleHistoricalDrawdown"):
        if not await get_alert_triggered(
            ticker, emailAddress, key="priceSurpassMultipleHistoricalDrawdown"
        ):
            if currentPrice < worst_dd["max_drawdown_price"]:
                alertTriggered.append(
                    _create_alert(
                        "priceSurpassMultipleHistoricalDrawdown",
                        f"{ticker} Surpass Historical Drawdown",
                        f"{ticker} fell below all historical drawdown prices. Current: {currentPrice}.",
                    )
                )
        await run_alert_trigger(
            alert, alertTriggered, key="priceSurpassMultipleHistoricalDrawdown"
        )

    # Alert 4: Price Approaches Historical Drawdown
    if drawdownAdvanceCondition.get("priceApproachHistoricalDrawdown"):
        if not await get_alert_triggered(
            ticker, emailAddress, key="priceApproachHistoricalDrawdown"
        ):
            tolerance = (
                drawdownAdvanceCondition["priceApproachHistoricalDrawdownValue"] / 100
            )
            dd_price = worst_dd["max_drawdown_price"]
            upper = dd_price * (1 + tolerance)

            if dd_price <= currentPrice <= upper:
                alertTriggered.append(
                    _create_alert(
                        "priceApproachHistoricalDrawdown",
                        f"{ticker} Approach Historical Drawdown",
                        f"{ticker} is approaching its historical drawdown within "
                        f"{drawdownAdvanceCondition['priceApproachHistoricalDrawdownValue']}%.",
                    )
                )
        await run_alert_trigger(
            alert, alertTriggered, key="priceApproachHistoricalDrawdown"
        )

    # Alert 5: Recover After Drawdown
    if drawdownAdvanceCondition.get("priceRecoverAfterDrawdown"):
        if not await get_alert_triggered(
            ticker, emailAddress, key="priceRecoverAfterDrawdown"
        ):
            tolerance = drawdownAdvanceCondition["priceRecoverAfterDrawdownValue"] / 100
            dd_price = current_dd_info["max_drawdown_price"]
            upper = dd_price * (1 + tolerance)

            if currentPrice > upper:
                alertTriggered.append(
                    _create_alert(
                        "priceRecoverAfterDrawdown",
                        f"{ticker} Price Recover After Drawdown",
                        f"{ticker} recovered {drawdownAdvanceCondition['priceRecoverAfterDrawdownValue']}%. "
                        f"Price is now {currentPrice}.",
                    )
                )
        await run_alert_trigger(alert, alertTriggered, key="priceRecoverAfterDrawdown")
