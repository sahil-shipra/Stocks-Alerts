import asyncio
from collections import defaultdict
from src.alerts import fetch_index_stock_alerts_from_db, get_index_stocks


async def fetch_index_stock_alerts():
    # Fetch all alerts from database
    index_alerts = await fetch_index_stock_alerts_from_db()
    print(f"index-stocks-result: {len(index_alerts)}")

    # Group alerts by ticker (extracting only once for performance)
    grouped_alerts = defaultdict(list)
    for alert in index_alerts:
        ticker = alert["ticker"]["ticker"]
        grouped_alerts[ticker].append(alert)

    # Fetch index stocks concurrently for all tickers
    tickers = list(grouped_alerts.keys())
    index_stocks_lists = await asyncio.gather(
        *(
            get_index_stocks(ticker) for ticker in tickers
        )  # add "^GSPC" for test S&P 500 index stocks
    )

    # Build mapping of ticker -> alerts (avoiding nested loops)
    index_grouped_alerts = defaultdict(list)
    for ticker_list, original_ticker in zip(index_stocks_lists, tickers):
        for item in ticker_list:
            item_ticker = item["ticker"]
            index_grouped_alerts[item_ticker].extend(grouped_alerts[original_ticker])

    return index_grouped_alerts
