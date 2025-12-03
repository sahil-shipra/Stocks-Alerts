from datetime import datetime
from src.apis.get_ticker_closing_price import get_ticker_closing_price


async def check_dma_conditions(alert):

    ticker = alert["tickerNm"]
    data = await get_ticker_closing_price(ticker)
    stock_data = [{"date": d["time"], "close": d["value"]} for d in data]
    lastCloseDate = datetime.strptime(stock_data[-1]["date"], "%Y-%m-%d").date()
    todayDate = datetime.today().date()

    alertTriggered = []

    alertTitleTickerFullName = alert["tickerNm"]
    alertMessageTickerFullName = alert["tickerNm"]

    if alert["condition"] == "DMA" and lastCloseDate == todayDate:
        dmaWindowList = alert["dmaWindow"]
        dmaAdvanceCondition = alert["dmaAdvanceCondition"]

        # Convert stock dates once and sort ascending
        stock_data_sorted = [
            {**s, "date": datetime.strptime(s["date"], "%Y-%m-%d")} for s in stock_data
        ]
        stock_data_sorted.sort(key=lambda x: x["date"])

        def calculate_dma(data, window):
            dma_values = []
            for i in range(window - 1, len(data)):
                window_data = data[i + 1 - window : i + 1]
                dma = sum(item["close"] for item in window_data) / window
                dma_values.append({"date": data[i]["date"], "dma": dma})
            return dma_values

        for dmaWindow in dmaWindowList:
            dma_result = calculate_dma(stock_data_sorted, dmaWindow)
            if not dma_result:
                continue

            currentDma = dma_result[-1]["dma"]

            # DMA mapping by date for quick lookup
            dma_dict = {entry["date"]: entry["dma"] for entry in dma_result}

            # Last price
            currentPrice = stock_data_sorted[-1]["close"]

            # ----- Alerts -----
            if dmaAdvanceCondition.get("touchedDma") and currentPrice >= currentDma:
                alertTriggered.append(
                    {
                        "advanceCondition": "touchedDma",
                        "condition": alert["condition"],
                        "subCondition": "",
                        "alertTitle": f"{alertTitleTickerFullName} Touched DMA {dmaWindow}",
                        "alertMessage": f"{alertMessageTickerFullName} has touched its {dmaWindow} DMA! Price: {(currentPrice)}",
                    }
                )

            if dmaAdvanceCondition.get("fallXFromDma"):
                threshold = currentDma * (
                    1 - dmaAdvanceCondition["fallXFromDmaValue"] / 100
                )
                if currentPrice < threshold:
                    alertTriggered.append(
                        {
                            "advanceCondition": "fallXFromDma",
                            "condition": alert["condition"],
                            "subCondition": "",
                            "alertTitle": f"{alertTitleTickerFullName} Fall From DMA {dmaWindow}",
                            "alertMessage": f"{alertMessageTickerFullName} price dropped to {(currentPrice)} from DMA {dmaWindow}: {(currentDma)}",
                        }
                    )

            if dmaAdvanceCondition.get("riseXFromDma"):
                threshold = currentDma * (
                    1 + dmaAdvanceCondition["fallXFromDmaValue"] / 100
                )
                if currentPrice > threshold:
                    alertTriggered.append(
                        {
                            "advanceCondition": "riseXFromDma",
                            "condition": alert["condition"],
                            "subCondition": "",
                            "alertTitle": f"{alertTitleTickerFullName} Rise From DMA {dmaWindow}",
                            "alertMessage": f"{alertMessageTickerFullName} price rose to {(currentPrice)} from DMA {dmaWindow}: {(currentDma)}",
                        }
                    )

            if dmaAdvanceCondition.get("nearDma"):
                lower = currentDma * (1 - dmaAdvanceCondition["nearDmaValue"] / 100)
                upper = currentDma * (1 + dmaAdvanceCondition["nearDmaValue"] / 100)
                if lower <= currentPrice <= upper:
                    alertTriggered.append(
                        {
                            "advanceCondition": "nearDma",
                            "condition": alert["condition"],
                            "subCondition": "",
                            "alertTitle": f"{alertTitleTickerFullName} Nears the {dmaWindow} DMA",
                            "alertMessage": f"{alertMessageTickerFullName} nears DMA {dmaWindow}: {(currentPrice)}",
                        }
                    )

            # Sustained above/below DMA
            for sustain_type in ["sustainXDayAboveDma", "sustainXDayBelowDma"]:
                sustain_value_key = f"{sustain_type}Value"
                consecutive = 0

                # Iterate from latest to oldest
                for stock in reversed(stock_data_sorted):
                    dma_val = dma_dict.get(stock["date"], currentDma)
                    if (
                        sustain_type == "sustainXDayAboveDma"
                        and stock["close"] >= dma_val
                    ) or (
                        sustain_type == "sustainXDayBelowDma"
                        and stock["close"] <= dma_val
                    ):
                        consecutive += 1
                    else:
                        break

                if (
                    dmaAdvanceCondition.get(sustain_type)
                    and consecutive >= dmaAdvanceCondition[sustain_value_key]
                ):
                    alertTriggered.append(
                        {
                            "advanceCondition": sustain_type,
                            "condition": alert["condition"],
                            "subCondition": "",
                            "alertTitle": f'{alertTitleTickerFullName} {sustain_type.replace("sustainXDay", "Sustains ")} {dmaWindow} DMA',
                            "alertMessage": f'{alertMessageTickerFullName} has {sustain_type.replace("sustainXDay", "sustained ")} {dmaWindow} DMA for {consecutive} days. Current price: {(currentPrice)}',
                        }
                    )
