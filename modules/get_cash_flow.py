# modules/get_cash_flow.py
from api.endpoints import FMPEndpoints

class GetCashFlow:
    async def get_data(self, ticker, year=None, date=None):
        endpoints = FMPEndpoints()
        try:
            data = await endpoints.get_cash_flow(ticker, year=year)
            if not data:
                return f"Error: No cash flow data available for {ticker}."
            value = data[0].get("cashFlowFromOperatingActivities", 0)
            return f"{ticker}'s cash from operations for {year or 'the latest year'} is ${value / 1_000_000_000:.2f} billion."
        except Exception as e:
            return f"Error fetching cash flow: {e}"