## Stock Alert Monitoring Script

This script monitors real-time stock prices for multiple tickers using Yahoo Finance and triggers alert conditions defined in your database. It leverages asynchronous programming (asyncio) to efficiently handle multiple tickers concurrently.

### Features

- Fetches alert configurations from a database.
- Monitors multiple stock tickers in real-time using Yahoo Finance WebSockets (yfinance.AsyncWebSocket).
- Evaluates incoming price data against alert conditions.
- Runs alert actions asynchronously for any triggered alerts.
- Logs activity and errors for monitoring and debugging.

### Modules & Dependencies

- yfinance: For fetching live stock data and subscribing to price updates via WebSocket.
- asyncio: For running concurrent monitoring tasks for multiple tickers.
- logging: For logging monitoring activity and exceptions.
- collections.defaultdict: To group alerts by ticker efficiently.
- Custom modules:
  - src.alerts.fetch_alerts_from_db: Fetches alert configurations from the database.
  - src.alert_engine.run_alerts: Executes the alert actions when conditions are met.
