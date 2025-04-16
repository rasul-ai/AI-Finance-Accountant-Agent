# modules/get_balance_sheet.py
from api.endpoints import FMPEndpoints

class GetBalanceSheet:
    async def get_data(self, ticker, year=None, date=None):
        endpoints = FMPEndpoints()
        try:
            data = await endpoints.get_balance_sheet(ticker, year=year)
            if not data:
                return f"Error: No balance sheet data available for {ticker}."
            assets = data[0].get("totalAssets", 0)
            liabilities = data[0].get("totalLiabilities", 0)
            return f"{ticker}'s assets for {year or 'the latest year'} are ${assets / 1_000_000_000:.2f} billion, and liabilities are ${liabilities / 1_000_000_000:.2f} billion."
        except Exception as e:
            return f"Error fetching balance sheet: {e}"