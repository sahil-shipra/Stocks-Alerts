from src.conditions.check_opportunity_conditions import check_opportunity_conditions
from src.conditions.check_dma_conditions import check_dma_conditions
from src.conditions.check_pe_ratio_conditions import check_pe_ratio_conditions
from src.conditions.check_price_conditions import check_price_conditions
from src.conditions.check_drawdown_conditions import check_drawdown_conditions
from src.conditions.check_rsi_conditions import check_rsi_conditions


async def process_alert_condition(alert: any):
    command = alert["condition"]
    match command:
        case "DMA":
            await check_dma_conditions(alert)
        case "PE_RATIO":
            await check_pe_ratio_conditions(alert)
        case "PRICE":
            await check_price_conditions(alert)
        case "DRAWDOWN":
            await check_drawdown_conditions(alert)
        case "OPPORTUNITY":
            await check_opportunity_conditions(alert)
        case "RSI":
            await check_rsi_conditions(alert)
        case "CROSS_JUNCTION":
            pass
        case "NEWS":
            pass
        case _:
            print(f"Unknown command: {command}.")


async def run_alerts(alerts: list, ticker: str, current_stock_data: any):
    for alert in alerts:

        if alert["status"] == "DEACTIVATED":
            print(f"DEACTIVATED:{str(alert["_id"])}")
            pass

        alert["tickerNm"] = ticker
        alert["currentStockData"] = current_stock_data
        alert["userXTickerId"] = alert["ticker"]["_id"]
        await process_alert_condition(alert)
    return ""
