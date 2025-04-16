# modules/get_revenue.py
from api.endpoints import FMPEndpoints

class GetRevenue:
    async def get_data(self, ticker, year=None, date=None):
        endpoints = FMPEndpoints()
        try:
            data = await endpoints.get_income_statement(ticker, year=year)
            if not data:
                return f"Error: No revenue data available for {ticker}."
            value = data[0].get("revenue", 0)
            return f"{ticker}'s revenue for {year or 'the latest year'} is ${value / 1_000_000_000:.2f} billion."
        except Exception as e:
            return f"Error fetching revenue: {e}"