# Example usage
import asyncio
from src.conditions.check_pe_ratio_conditions import check_trend
from src.apis.get_ticker_pe_ratio import get_ticker_pe_ratio


async def main():
    try:
        list = await get_ticker_pe_ratio("GOOGL")
        data = check_trend(list, 100, True)
        print(data)
        print(f"Done:-/")
        return data

    except Exception as e:
        print(f"Error fetching index performance: {e}")
        return None


asyncio.run(main())
