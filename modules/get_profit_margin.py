# modules/get_profit_margin.py
from api.endpoints import FMPEndpoints

class GetProfitMargin:
    async def get_data(self, ticker, year=None, date=None):
        endpoints = FMPEndpoints()
        try:
            data = await endpoints.get_ratios(ticker, year=year)
            if not data:
                return f"Error: No profit margin data available for {ticker}."
            value = data[0].get("netProfitMargin", 0) * 100
            return f"{ticker}'s profit margin for {year or 'the latest year'} is {value:.2f}%."
        except Exception as e:
            return f"Error fetching profit margin: {e}"