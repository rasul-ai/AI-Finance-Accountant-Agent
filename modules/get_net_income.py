# modules/get_net_income.py
from api.endpoints import FMPEndpoints

class GetNetIncome:
    async def get_data(self, ticker, year=None, date=None):
        endpoints = FMPEndpoints()
        try:
            data = await endpoints.get_income_statement(ticker, year=year)
            if not data:
                return f"Error: No net income data available for {ticker}."
            value = data[0].get("netIncome", 0)
            return f"{ticker}'s net income for {year or 'the latest year'} is ${value / 1_000_000_000:.2f} billion."
        except Exception as e:
            return f"Error fetching net income: {e}"