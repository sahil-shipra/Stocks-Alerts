from src.conditions import check_price_condition


async def process_alert_condition(alert: any):
    command = alert["condition"]
    match command:
        case "DMA":
            print(f"")
        case "PE_RATIO":
            print(f"")
        case "PRICE":
            await check_price_condition(alert)
        case "DRAWDOWN":
            print(f"")
        case "OPPORTUNITY":
            print(f"")
        case "RSI":
            print(f"")
        case "CROSS_JUNCTION":
            print(f"")
        case "NEWS":
            print(f"")
        case _:
            print(f"Unknown command: {command}.")


async def run_alerts(alerts: list, ticker: str):
    for alert in alerts:
        alert["tickerNm"] = ticker
        await process_alert_condition(alert)
    return ""
