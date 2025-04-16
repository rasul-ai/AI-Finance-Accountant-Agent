# modules/get_financial_ratios.py
from api.endpoints import FMPEndpoints

class GetFinancialRatios:
    async def get_data(self, ticker, year=None, date=None):
        endpoints = FMPEndpoints()
        try:
            data = await endpoints.get_ratios(ticker, year=year)
            if not data:
                return f"Error: No financial ratios data available for {ticker}."
            current_ratio = data[0].get("currentRatio", 0)
            return f"{ticker}'s current ratio for {year or 'the latest year'} is {current_ratio:.2f}."
        except Exception as e:
            return f"Error fetching financial ratios: {e}"