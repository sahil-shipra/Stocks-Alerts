from src.alert_engine import run_alerts
from src.alerts import fetch_alerts_from_db
import asyncio
from collections import defaultdict
import yfinance as yf
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
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

    await run_alerts(alerts)


async def monitor_ticker(ticker, alerts):
    """
    Monitor a single ticker via yfinance WebSocket
    """
    logger.info(f"Starting monitor for {ticker} with {len(alerts)} alerts")
    yf_ws = None

    try:
        async with yf.AsyncWebSocket() as ws:
            yf_ws = ws
            await ws.subscribe([ticker])

            async def on_message(msg: dict):
                logger.debug(f"{ticker}: {msg}")
                await check_alert_conditions(ticker, alerts, msg)

            # Listen for messages
            await ws.listen(on_message)

    except Exception as e:
        logger.exception(f"Error monitoring {ticker}: {e}")
    finally:
        if yf_ws is not None:
            try:
                await yf_ws.close()
            except Exception:
                pass
        logger.info(f"WebSocket for {ticker} closed")


async def main():
    # Fetch all alerts from database
    result = await fetch_alerts_from_db()

    # Group alerts by ticker
    grouped_alerts = defaultdict(list)
    for alert in result:
        ticker = alert["ticker"]["ticker"]
        grouped_alerts[ticker].append(alert)

    logger.info(
        f"Monitoring {len(grouped_alerts)} tickers: {list(grouped_alerts.keys())}"
    )

    # Create async tasks for each ticker
    tasks = []
    for ticker, alerts in grouped_alerts.items():
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
