# modules/get_dividend_info.py
from api.endpoints import FMPEndpoints

class GetDividendInfo:
    async def get_data(self, ticker, year=None, date=None):
        endpoints = FMPEndpoints()
        try:
            data = await endpoints.get_ratios(ticker, year=year)
            if not data:
                return f"Error: No dividend info available for {ticker}."
            value = data[0].get("payoutRatio", 0) * 100
            return f"{ticker}'s dividend payout ratio for {year or 'the latest year'} is {value:.2f}%."
        except Exception as e:
            return f"Error fetching dividend info: {e}"