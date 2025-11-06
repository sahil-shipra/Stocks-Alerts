from typing import Union
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import yfinance as yf
import asyncio
import logging
from src.alert_engine import run_alerts
from src.alerts import fetch_stock_alerts_from_db
from src.utils.db import get_database
import time
from datetime import datetime
from bson.json_util import dumps

app = FastAPI()
db = get_database()


# Regular HTTP route
@app.get("/")
def read_root():
    ticker = yf.Ticker("LSEG.L")
    info = ticker.info
    return {
        "symbol": "LSEG.L",
        "company_name": info.get("longName"),
        "current_price": info.get("currentPrice"),
    }


@app.get("/alerts")
async def read_alerts():
    # Record start time
    start_time = time.time()
    start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    print(f"[START] Execution started at: {start_datetime}")

    try:

        items = await fetch_stock_alerts_from_db()
        await run_alerts(items)

        return {
            "count": len(items),
        }
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Calculate execution time
        end_time = time.time()
        end_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        execution_time = end_time - start_time

        print(f"[END] Execution ended at: {end_datetime}")
        print(f"[DURATION] Total execution time: {execution_time:.3f} seconds")


# --- NEW SECTION: WebSocket streaming endpoint ---

logger = logging.getLogger(__name__)


@app.websocket("/ws/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await websocket.accept()
    logger.info(f"Client connected for symbol: {symbol}")

    yf_ws = None  # Define early for safe reference in finally
    try:
        async with yf.AsyncWebSocket() as ws:
            yf_ws = ws
            await ws.subscribe([symbol])

            # Flag to control message sending
            disconnected = asyncio.Event()

            async def on_message(msg: dict):
                if disconnected.is_set():
                    return  # Don't try sending after disconnect
                try:
                    await websocket.send_json(msg)
                except Exception as send_err:
                    logger.warning(f"Client disconnected or send failed: {send_err}")
                    disconnected.set()
                    await websocket.close()
                    # Stop yf listener immediately
                    await ws.close()

            listen_task = asyncio.create_task(ws.listen(on_message))

            # Wait until the client disconnects or an exception occurs
            done, pending = await asyncio.wait(
                [listen_task], return_when=asyncio.FIRST_EXCEPTION
            )

            for task in pending:
                task.cancel()

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from symbol: {symbol}")
    except Exception as e:
        logger.exception(f"Error in websocket for {symbol}: {e}")
    finally:
        # Explicitly close Yahoo WebSocket if still open
        if yf_ws is not None:
            try:
                await yf_ws.close()
            except Exception:
                pass
        await websocket.close()
        logger.info(f"WebSocket for {symbol} closed cleanly.")
