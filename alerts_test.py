from src.index_stock_alerts import fetch_index_stock_alerts
from src.alert_engine import run_alerts
from src.alerts import fetch_stock_alerts_from_db, fetch_watchlist_alerts_from_db
import asyncio
from collections import defaultdict
import logging
import yfinance as yf

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


async def check_alert_conditions(ticker, alerts, msg):
    """
    Check if current price data meets any alert conditions
    """
    # Extract price from the message
    # Adjust based on actual yfinance message structure
    current_price = msg.get("price") or msg.get("last") or msg.get("close")

    if current_price is None:
        return

    await run_alerts(alerts, ticker, current_stock_data=msg)


async def monitor_ticker(ticker, alerts):
    """
    Monitor a single ticker via yfinance WebSocket
    """
    logger.info(f"Starting monitor for {ticker} with {len(alerts)} alerts")
    yf_ws = None

    try:
        async with yf.AsyncWebSocket(verbose=True) as ws:
            yf_ws = ws
            await ws.subscribe([ticker])

            async def on_message(msg: dict):
                logger.debug(f"{ticker}")
                # print(f"{ticker,'---------------->',msg}")
                await check_alert_conditions(ticker, alerts, msg)

            # Listen for messages
            await ws.listen(on_message)

    except Exception as e:
        logger.exception(f"Error monitoring {ticker}")
    finally:
        if yf_ws is not None:
            try:
                await yf_ws.close()
            except Exception:
                pass
        logger.info(f"WebSocket for {ticker} closed")


async def main():
    # Fetch all alerts from database
    stocks_alerts = await fetch_stock_alerts_from_db()

    watchlist_alerts = await fetch_watchlist_alerts_from_db()

    # Combine both lists
    all_alerts = stocks_alerts + watchlist_alerts

    # Group alerts by ticker
    grouped_alerts = defaultdict(list)
    for alert in all_alerts:
        ticker = alert["ticker"]["ticker"]
        grouped_alerts[ticker].append(alert)

    # Create async tasks for each ticker

    index_grouped_alerts = await fetch_index_stock_alerts()

    print(f"index_grouped_alerts: - {len(index_grouped_alerts)}")
    print(f"grouped_alerts: - {len(grouped_alerts)}")

    combined_alerts = defaultdict(list, grouped_alerts)

    if index_grouped_alerts:
        for ticker, alerts in index_grouped_alerts.items():
            combined_alerts[ticker].extend(alerts)

    print(f"combined_alerts: - {len(combined_alerts)}")
    tasks = []
    for ticker, alerts in combined_alerts.items():
        task = asyncio.create_task(monitor_ticker(ticker, alerts))
        tasks.append(task)

    # Run all monitoring tasks concurrently
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Shutting down monitors...")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
